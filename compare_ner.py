"""So sánh regex, NlpHUST ELECTRA và OpenMed PII trong việc che tên người, địa chỉ.

Colab: tải masked.csv, clean_dataset.py, danh_sach_dia_danh_truong.csv, compare_ner.py lên /content, bật GPU rồi chạy
    !pip install -q transformers sentencepiece protobuf
    !python compare_ner.py

Không cần dữ liệu gốc: tên thật đã được che, script điền lại bằng tên giả nên biết chắc đáp án.
Kết quả: ner_compare_results/summary.csv và review_real_rows.csv (để người đánh dấu).
"""
import random
import re
import unicodedata
from pathlib import Path

import pandas as pd

from clean_dataset import PLACEHOLDER, mask

HERE = Path(__file__).parent
RESULTS = HERE / "ner_compare_results"
SEED, N_NAME_ROWS, N_REAL_ROWS, N_ADDRESSES = 42, 1000, 2000, 200
BATCH_SIZE, MAX_CHARS = 32, 300  # bỏ câu dài để không vượt giới hạn 512 token của mô hình

MODELS = {"nlphust": "NlpHUST/ner-vietnamese-electra-base",
          "openmed": "OpenMed/OpenMed-PII-Vietnamese-BigMed-Large-278M-v1"}
NAME_GROUPS = {"PERSON", "FIRSTNAME", "MIDDLENAME", "LASTNAME"}
ADDRESS_GROUPS = {"STREET", "BUILDINGNUMBER", "SECONDARYADDRESS"}

SURNAMES = "Nguyễn Trần Lê Phạm Hoàng Huỳnh Phan Vũ Võ Đặng Bùi Đỗ Hồ Ngô Dương Lý".split()
MIDDLES = "Văn Thị Hữu Đức Minh Ngọc Thanh Quang Tuấn Hải Thu Xuân".split()
GIVENS = """Trang Nam Hà Linh Anh Huy Đạt Dũng Hùng Lan Mai Hương Thảo Nhung Tùng Sơn Long Phong Hiếu Khánh Quân Yến
Ngân Hoa Hạnh Tâm Bình An Minh Tuấn""".split()

VARIANTS = {
    "full": lambda full, given: full,
    "full_lower": lambda full, given: full.lower(),
    "full_no_accent": lambda full, given: strip_accents(full),
    "full_no_accent_lower": lambda full, given: strip_accents(full).lower(),
    "given": lambda full, given: given,
    "given_lower": lambda full, given: given.lower(),
    "given_no_accent_lower": lambda full, given: strip_accents(given).lower(),
}

# Các từ vừa là tên vừa là từ thường: che ở đây là che nhầm.
TRAPS = """trang web đăng ký lag quá
trang này load chậm thật
phòng tập chia khu nam nữ riêng
sinh viên nam đăng ký ở đây
mai mình thi môn toán
sáng mai có lịch học không
hoa trước cổng trường nở đẹp ghê
thi xong thấy tâm trạng tệ hẳn
đề này bình thường mà
cuối cùng cũng an tâm rồi
chúc mọi người bình an nhé
sơn tường ký túc xá bong hết rồi
long lanh ghê
phong trào năm nay vui phết
hùng hổ thế bạn
hiếu kỳ quá
nhà xe hết chỗ rồi
tùng cây trước sân cao thật
lan can tầng 3 sắp gãy
đạt môn này là mừng rồi
mình đạt loại khá
dũng cảm lên nào
thanh toán học phí ở đâu vậy
quân sự năm nay học ở đâu
minh chứng rèn luyện nộp cho ai
hải sản căng tin dở lắm
tuấn tú dữ
ngọc trai đẹp thế
thu học phí sớm vậy
yến tiệc tất niên khi nào
ngân hàng nào đóng học phí được
hạnh kiểm có ảnh hưởng học bổng không
hương vị đồ ăn căng tin chán
hà cớ gì lại thế
khánh thành nhà mới chưa
Trang web trường sập rồi
Mai thi rồi mà chưa học gì
Thu học phí sớm thế
Thanh toán online lỗi
Đạt môn rồi vui quá""".split("\n")


def strip_accents(text):
    text = text.replace("đ", "d").replace("Đ", "D")
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


def fill_names(text, names):
    """Thay lần lượt từng [NAME] bằng tên giả, trả về văn bản và vị trí của các tên."""
    parts = text.split("[NAME]")
    assert len(parts) == len(names) + 1
    out, spans = parts[0], []
    for name, part in zip(names, parts[1:]):
        spans.append((len(out), len(out) + len(name)))
        out += name + part
    return out, spans


def spans_from_mask(original, masked):
    """Từ văn bản đã che, suy ra các đoạn của bản gốc bị thay bằng token."""
    parts, spans = PLACEHOLDER.split(masked), []
    assert original.startswith(parts[0]), (original, masked)
    position = len(parts[0])
    for index, part in enumerate(parts[1:], 2):
        end = original.rfind(part) if index == len(parts) else original.find(part, position)
        assert end >= position, (original, masked)
        spans.append((position, end))
        position = end + len(part)
    return spans


def coverage(text, gold, predicted):
    """Trả về (che hết, che được một phần) của một tên, bỏ qua khoảng trắng."""
    chars = {i for i in range(*gold) if not text[i].isspace()}
    hit = {i for start, end in predicted for i in range(start, end)} & chars
    return hit == chars, bool(hit)


def self_check():
    assert strip_accents("Đặng Thị Hà") == "Dang Thi Ha"
    assert fill_names("[NAME] và [NAME] ạ", ["An", "Bình"]) == ("An và Bình ạ", [(0, 2), (6, 10)])
    assert spans_from_mask("Thầy Nguyễn An chấm", "Thầy [NAME] chấm") == [(5, 14)]
    assert spans_from_mask("gọi Nam ơi và Hà ơi", "gọi [NAME] ơi và [NAME] ơi") == [(4, 7), (14, 16)]
    assert coverage("Trần An", (0, 7), [(0, 4)]) == (False, True)
    assert coverage("Trần An", (0, 7), [(0, 4), (5, 7)]) == (True, True)
    assert coverage("Trần An", (0, 7), []) == (False, False)


def load_rows():
    path = next(p for p in [HERE / "masked.csv", HERE / "cleaned" / "masked.csv"] if p.exists())
    df = pd.read_csv(path, dtype=str, keep_default_na=False, usecols=["text_public", "is_low_info"])
    return df[df.text_public.str.len().le(MAX_CHARS)].drop_duplicates("text_public")


def build_name_cases(df, rng):
    """Mỗi câu được điền cùng một bộ tên giả ở mọi dạng viết để các dạng so được với nhau."""
    tokens = df.text_public.str.findall(PLACEHOLDER)
    only_name = tokens.map(lambda found: len(found) > 0 and set(found) == {"[NAME]"})
    enough_words = df.text_public.str.replace(PLACEHOLDER, "", regex=True).str.split().str.len().ge(3)
    chosen = df[only_name & enough_words].sample(n=N_NAME_ROWS, random_state=SEED)
    cases = []
    for text in chosen.text_public:
        count = text.count("[NAME]")
        people = [(rng.choice(SURNAMES), rng.choice(MIDDLES), rng.choice(GIVENS)) for _ in range(count)]
        for variant, render in VARIANTS.items():
            names = [render(" ".join(p), p[2]) for p in people]
            filled, spans = fill_names(text, names)
            where = "start" if text.startswith("[NAME]") else "mid"
            cases += [{"variant": variant, "position": where, "text": filled, "gold": span} for span in spans]
    return cases


def build_address_cases(rng):
    streets = "Trần Phú|Nguyễn Trãi|Lê Lợi|Kim Giang|Quang Trung|Phùng Khoang|Chiến Thắng|Tô Hiệu".split("|")
    templates = ["Cho thuê phòng trọ tại {} giá rẻ", "Nhà mình ở {} nhé", "Qua {} lấy đồ giúp mình", "Địa chỉ: {}, Hà Đông"]
    cases = []
    for _ in range(N_ADDRESSES):
        address = f"số {rng.randint(1, 200)} ngõ {rng.randint(1, 99)} {rng.choice(streets)}"
        text = rng.choice(templates).format(address)
        cases.append({"text": text, "gold": (text.index(address), text.index(address) + len(address))})
    return cases


def run_ner(texts):
    """Chạy trực tiếp trên máy hoặc Colab, không gửi văn bản tới API nào."""
    import torch
    from transformers import pipeline

    device = 0 if torch.cuda.is_available() else -1
    results = {}
    for name, model_id in MODELS.items():
        print("Đang chạy", model_id, "GPU" if device == 0 else "CPU")
        ner = pipeline("token-classification", model=model_id, aggregation_strategy="first", device=device)
        results[name] = dict(zip(texts, ner(texts, batch_size=BATCH_SIZE)))
    return results


def by_group(entities, groups):
    return [(e["start"], e["end"]) for e in entities if e["entity_group"] in groups]


def evaluate(cases, traps, real, addresses, ner):
    regex = {t: spans_from_mask(t, mask(t)[0]) for t in {c["text"] for c in cases} | set(traps) | set(real) | {a["text"] for a in addresses}}
    name = lambda model, t: by_group(ner[model][t], NAME_GROUPS)
    systems = {
        "regex": lambda t: regex[t],
        "nlphust": lambda t: name("nlphust", t),
        "openmed": lambda t: name("openmed", t),
        "regex+nlphust": lambda t: regex[t] + name("nlphust", t),
        "regex+openmed": lambda t: regex[t] + name("openmed", t),
        "regex+nlphust+openmed": lambda t: regex[t] + name("nlphust", t) + name("openmed", t),
    }
    rows = []
    for system, predict in systems.items():
        scores = {}
        for case in cases:
            full, partial = coverage(case["text"], case["gold"], predict(case["text"]))
            scores.setdefault(case["variant"], []).append(full)
            scores.setdefault(f'{case["variant"]}|{case["position"]}', []).append(full)
            scores.setdefault("any_part_masked", []).append(partial)
        row = {"system": system, **{k: sum(v) / len(v) for k, v in scores.items()}}
        row["trap_false_mask_rate"] = sum(bool(predict(t)) for t in traps) / len(traps)
        row["real_rows_extra_mask_rate"] = sum(bool(predict(t)) for t in real) / len(real)
        rows.append(row)
    address_rows = {}
    for system, predict in {"regex": lambda t: regex[t], "openmed": lambda t: by_group(ner["openmed"][t], ADDRESS_GROUPS)}.items():
        result = [coverage(a["text"], a["gold"], predict(a["text"])) for a in addresses]
        address_rows[system] = {"address_full": sum(r[0] for r in result) / len(result), "address_any": sum(r[1] for r in result) / len(result)}
    return pd.DataFrame(rows).set_index("system"), pd.DataFrame(address_rows).T


def main():
    self_check()
    RESULTS.mkdir(exist_ok=True)
    rng = random.Random(SEED)
    df = load_rows()
    cases = build_name_cases(df, rng)
    addresses = build_address_cases(rng)
    no_token = ~df.text_public.str.contains(PLACEHOLDER) & (df.is_low_info == "False")
    real = df[no_token].sample(n=N_REAL_ROWS, random_state=SEED).text_public.tolist()

    texts = sorted({c["text"] for c in cases} | set(TRAPS) | set(real) | {a["text"] for a in addresses})
    ner = run_ner(texts)
    names, address = evaluate(cases, TRAPS, real, addresses, ner)
    names.round(4).to_csv(RESULTS / "summary.csv", encoding="utf-8-sig")
    address.round(4).to_csv(RESULTS / "summary_address.csv", encoding="utf-8-sig")

    # Câu thật không có token mà mô hình vẫn thấy tên: người đọc để biết là bắt thêm đúng hay che nhầm.
    review = []
    for text in real:
        found = {m: "; ".join(text[s:e] for s, e in by_group(ner[m][text], NAME_GROUPS)) for m in MODELS}
        if any(found.values()):
            review.append({"text": text, **found, "is_real_name": ""})
    pd.DataFrame(review).to_csv(RESULTS / "review_real_rows.csv", index=False, encoding="utf-8-sig")

    pd.set_option("display.width", 250, "display.max_columns", None)
    print("\nTỷ lệ che HẾT tên theo từng dạng viết:\n", names[list(VARIANTS)].round(3))
    print("\nChe nhầm và mức che thêm:\n", names[["any_part_masked", "trap_false_mask_rate", "real_rows_extra_mask_rate"]].round(3))
    print("\nĐịa chỉ:\n", address.round(3))
    print("\nĐã lưu vào", RESULTS, "| số câu thật cần đọc:", len(review))


if __name__ == "__main__":
    main()

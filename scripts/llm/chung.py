"""Phần dùng chung cho gán nhãn bằng LLM: bộ nhãn, lược đồ JSON, prompt, kiểm tra nhãn, đọc gold và masked.csv."""
import hashlib
import importlib.util
import re
import unicodedata
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent
ROOT = HERE.parent.parent
MASKED = ROOT / "data" / "cleaned" / "masked.csv"
GOLD = {1: ROOT / "data" / "gan_nhan" / "vong1" / "gold_vong1.csv", 2: ROOT / "data" / "gan_nhan" / "vong2" / "gold_vong2.csv"}
KET_QUA = ROOT / "data" / "llm" / "ket_qua"
PROMPT_FILE = HERE / "prompt_ban5.md"

TOXICITY = ["clean", "profane", "attack", "unk"]
TOPIC = ["academics", "facilities", "administration", "student_life", "unk"]
STANCE = ["support", "oppose", "suggest", "none", "unk"]
EMOTION = ["joy", "sadness", "anger", "fear", "surprise", "neutral", "unk"]
EMOTION_2 = ["joy", "sadness", "anger", "fear", "surprise"]
HUONG = {"toxicity": TOXICITY, "topic": TOPIC, "stance": STANCE, "emotion_1": EMOTION}

# Lược đồ cho structured outputs của cả Claude (output_config.format) và OpenAI (response_format, strict).
SCHEMA = {
    "type": "object",
    "properties": {
        "toxicity": {"type": "string", "enum": TOXICITY},
        "topic": {"type": "string", "enum": TOPIC},
        "stance": {"type": "string", "enum": STANCE},
        "emotion_1": {"type": "string", "enum": EMOTION},
        "emotion_2": {"type": "array", "items": {"type": "string", "enum": EMOTION_2}},
        "hard": {"type": "boolean"},
        "ly_do": {"type": "string"},
    },
    "required": ["toxicity", "topic", "stance", "emotion_1", "emotion_2", "hard", "ly_do"],
    "additionalProperties": False,
}


# Chế độ tách hướng: mỗi câu gọi 4 lần, mỗi lần một hướng. `ly_do` đứng đầu để mô hình nêu dấu hiệu trước khi chọn nhãn
# (structured outputs sinh các trường theo đúng thứ tự trong lược đồ).
HUONG_TACH = ["toxicity", "topic", "stance", "emotion"]


def _schema(fields):
    props = {"ly_do": {"type": "string"}} | fields | {"hard": {"type": "boolean"}}
    return {"type": "object", "properties": props, "required": list(props), "additionalProperties": False}


SCHEMA_TACH = {
    "toxicity": _schema({"bang_chung": {"type": "string"}, "toxicity": {"type": "string", "enum": TOXICITY}}),
    "topic": _schema({"topic": {"type": "string", "enum": TOPIC}}),
    "stance": _schema({"stance": {"type": "string", "enum": STANCE}}),
    "emotion": _schema({"emotion_1": {"type": "string", "enum": EMOTION},
                        "emotion_2": {"type": "array", "items": {"type": "string", "enum": EMOTION_2}}}),
}


def _strip(raw):
    return re.sub(r"<!--.*?-->\s*", "", raw, flags=re.S).strip()


def load_prompt_tach(folder):
    """Bộ prompt tách hướng: thư mục có chung.md (ghi PROMPT_VERSION) và toxicity.md, topic.md, stance.md, emotion.md.
    Trả về ({hướng: system prompt = chung + hướng}, phiên bản, sha256 12 ký tự của cả bộ)."""
    folder = Path(folder)
    raw = (folder / "chung.md").read_text(encoding="utf-8")
    version = re.search(r"PROMPT_VERSION:\s*(\S+)", raw).group(1)
    head = _strip(raw)
    prompts = {h: head + "\n\n" + _strip((folder / f"{h}.md").read_text(encoding="utf-8")) for h in HUONG_TACH}
    sha = hashlib.sha256("\n\n=====\n\n".join(prompts[h] for h in HUONG_TACH).encode("utf-8")).hexdigest()[:12]
    return prompts, version, sha


def load_prompt(path=PROMPT_FILE):
    """Trả về (system prompt, phiên bản, sha256 12 ký tự). Bỏ các khối chú thích <!-- -->."""
    raw = Path(path).read_text(encoding="utf-8")
    version = re.search(r"PROMPT_VERSION:\s*(\S+)", raw).group(1)
    text = re.sub(r"<!--.*?-->\s*", "", raw, flags=re.S).strip()
    return text, version, hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def clean_dataset_module():
    spec = importlib.util.spec_from_file_location("clean_dataset", ROOT / "scripts" / "clean_dataset.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_cd = None


def con_thong_tin_ca_nhan(*texts):
    """Tên các mẫu thông tin cá nhân còn khớp trong các đoạn văn bản (rỗng nghĩa là gửi được).
    Kiểm tra từng đoạn riêng: nối các cột lại sẽ tạo mẫu giả ở chỗ nối."""
    global _cd
    if _cd is None:
        _cd = clean_dataset_module()
    patterns = {"URL": _cd.URL, "EMAIL": _cd.EMAIL, "PHONE": _cd.PHONE, "STUDENT_ID": _cd.STUDENT_ID,
                "STUDENT_ID_PART": _cd.STUDENT_ID_PART, "LONG_NUMBER": _cd.LONG_NUMBER}
    found = set()
    for text in texts:
        found |= {name for name, pattern in patterns.items() if pattern.search(text)}
        if _cd.mask_supplement(text)[0] != text or _cd.merge_name_fragments(text) != text:
            found.add("NAME")
    return sorted(found)


# Kiểm tra bằng chứng toxicity (từ ban5-en-tach-p3): mô hình hay tự bịa từ tục hoặc lời xúc phạm không có trong câu.
# profane chỉ giữ khi câu có một từ trong TU_TUC (hoặc biến thể lặp chữ); attack chỉ giữ khi `bang_chung` có thật trong câu.
# Danh sách cố ý rộng: nó chỉ chặn nhãn profane khi câu không có từ nào, không dùng để tự gán profane.
TU_TUC = [
    "vl", "vcl", "vkl", "vcc", "vc", "vler", "vloz", "vlz", "vleu", "vãi", "vải l", "vai l", "vãi l", "vờ lờ", "vê lờ",
    "đm", "dm", "đmm", "dmm", "đcm", "dcm", "đkm", "dkm", "đcmm", "đmcs", "dmcs", "đkmm", "đờ mờ", "đậu má", "đù má", "đụ má", "du ma",
    "đù", "đụ", "địt", "dit", "djt", "đjt", "đếch", "đéo", "đ3o", "deo", "déo", "đel", "dell", "đek", "đệch", "đách",
    "cc", "cl", "clm", "clgt", "cmm", "cmn", "cđm", "cdm", "cđg", "cặc", "cak", "lồn", "loz", "lol", "lz", "l", "buồi", "dái",
    "đĩ", "điếm", "cứt", "chó", "đcu", "dcu", "dcd", "đcd", "dkmm", "ccc", "mẹ mày", "mẹ m", "cha mày",
    "fuck", "fck", "fk", "shit", "wtf", "vđ",
]
_CHU = r"0-9a-zà-ỹđ"


def _mau_tu(tu):
    """Mỗi chữ cho phép lặp (vl → vlll, đéo → đéooo), cách nhau bởi khoảng trắng hoặc dấu chấm, đứng riêng một từ."""
    parts = [r"[\s.\-_*]*".join(re.escape(c) + "+" for c in w) for w in tu.split()]
    return r"\s+".join(parts)


TU_TUC_RE = re.compile(rf"(?<![{_CHU}])(?:{'|'.join(_mau_tu(t) for t in sorted(TU_TUC, key=len, reverse=True))})(?![{_CHU}])",
                       re.I)


def _chuan(s):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", str(s))).strip().lower()


def co_tu_tuc(text):
    return bool(TU_TUC_RE.search(_chuan(text)))


def bang_chung_co_that(quote, text):
    """`quote` (bỏ dấu ngoặc, dấu câu hai đầu) có nằm nguyên văn trong `text` không. Mô hình có khi trích nhiều đoạn
    nối bằng dấu phẩy, chấm phẩy, "...", "|" ("loz, th ngu"): khi đó mọi đoạn đều phải có trong câu."""
    def sach(s):
        return _chuan(s).strip(" \"'“”‘’.,!?…:;()[]")
    q, t = sach(quote), _chuan(text)
    if not q:
        return False
    if q in t:
        return True
    parts = [sach(p) for p in re.split(r"\s*(?:,|;|\||\.\.\.|…|\s/\s)\s*", q)]
    parts = [p for p in parts if p]
    return len(parts) > 1 and all(p in t for p in parts)


def kiem_tra_bang_chung(toxicity, bang_chung, text):
    """None nếu nhãn toxicity có bằng chứng (hoặc không cần), ngược lại là lý do (tiếng Việt, để ghi log)."""
    if toxicity == "attack" and not bang_chung_co_that(bang_chung, text):
        return f"attack nhưng bằng chứng {bang_chung!r} không có trong câu"
    if toxicity == "profane" and not co_tu_tuc(text):
        return "profane nhưng câu không có từ tục nào trong danh sách"
    return None


def kiem_tra(d):
    """Chuẩn hóa và kiểm tra một kết quả. Trả về (nhãn đã chuẩn hóa, [vi phạm], [đã tự sửa])."""
    vi_pham, da_sua = [], []
    for key, labels in HUONG.items():
        if d.get(key) not in labels:
            vi_pham.append(f"{key}={d.get(key)!r} không hợp lệ")
    e2 = []
    for e in d.get("emotion_2") or []:
        if e in EMOTION_2 and e != d.get("emotion_1") and e not in e2:
            e2.append(e)
        else:
            da_sua.append(f"bỏ {e!r} khỏi emotion_2")
    if d.get("emotion_1") in ("neutral", "unk") and e2:
        da_sua.append(f"bỏ emotion_2 {e2} vì emotion_1 = {d.get('emotion_1')}")
        e2 = []
    if d.get("topic") == "unk" and d.get("stance") not in ("none", "unk"):
        vi_pham.append(f"topic = unk nhưng stance = {d.get('stance')}")
    out = {k: d.get(k) for k in HUONG}
    out |= {"emotion_2": "; ".join(e2), "hard": bool(d.get("hard")), "ly_do": str(d.get("ly_do", ""))[:800]}
    return out, vi_pham, da_sua


def load_masked(columns=("comment_uid", "post_uid", "post_text", "parent_text", "text_public", "split")):
    return pd.read_csv(MASKED, dtype=str, keep_default_na=False, usecols=list(columns))


def load_gold(rounds):
    frames = []
    for r in rounds:
        g = pd.read_csv(GOLD[r], dtype=str, keep_default_na=False)
        g["vong"] = str(r)
        frames.append(g)
    return pd.concat(frames, ignore_index=True)

"""Làm sạch và che thông tin cá nhân cho dữ liệu bình luận NLP_N12.

Colab (bật GPU): tải file này, danh_sach_dia_danh_truong.csv và file xlsx gốc lên /content rồi chạy
    !pip install -q transformers sentencepiece protobuf openpyxl
    !python clean_dataset.py [file_xlsx_goc]
Che theo 2 lớp: regex trước, sau đó NER chạy ngay trên máy đang chạy script, không gửi tới API nào.
Kết quả nằm trong cleaned/: masked.csv để gán nhãn, private/ giữ kín (bảng ID, mẫu soát tay).
File gốc chỉ được đọc, không bị sửa. Ngôn ngữ (emoji, từ tục, teencode, chữ kéo dài) giữ nguyên.
"""
import csv
import json
import random
import re
import secrets
import sys
import unicodedata
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent
DEFAULT_INPUT = HERE / "tonghopcmt_n12_backup_truoc_khi_them_toxic.xlsx"
OUT = HERE / "cleaned"
PRIVATE = OUT / "private"
SEED = 42

UP = "A-ZĐÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴ"
LOW = "a-zđàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵ"
CAP = f"[{UP}][{LOW}]+"
# Tên gõ kiểu "TTuấnn", "VAnh", "QuỳnhAnh": tối đa 2 chữ hoa đầu và có thể dính thêm một từ viết hoa.
CAP2 = f"[{UP}]{{1,2}}[{LOW}]+(?:[{UP}][{LOW}]+)?"
TITLES = "thầy cô anh chị em bạn bác chú ông bà cậu dì".split()
TITLE_RE = "|".join(TITLES)
# Chữ viết hoa ở đầu câu hay dính vào tên ("Hoàng Năm ngoái", "tiếng Anh Cũng"): tách ra, không che.
SENTENCE_WORDS = set("""Năm Cũng Không Có Các Mong Hay Với Muốn Đổi Thực Ngày Mình Tôi Cho Xin Cảm Ơn Được Và Là Nhưng
Thì Nên Vậy Còn Chắc Rồi Nếu Khi Sao Ai Gì Đã Đang Sẽ Vẫn Cứ Hôm Nay Ví Dụ Lúc Trước Sau Giờ Mấy Bao Nhiêu Đi Làm""".split())
# Tên viết thường chỉ che khi đứng sau danh xưng; đã bỏ những tên trùng từ thường gặp (bảo, đạt, hùng, mai, an...).
GIVEN_NAMES = set("""bích bình chiến cường dung dũng duy dương đức giang hà hải hạnh hiền hiếu hiệp hoài hoàng hồng huệ hưng
hương hường huy huyền khang khánh khải khôi kiên lam lan lâm liên linh loan lộc long luân ly mạnh minh my nam nga ngân ngọc
nguyên nhàn nhật nhi nhung oanh phong phú phúc phương quân quang quế quốc quý quyên quỳnh sơn thái thanh thành thảo thịnh
thơ thư thuận thủy thúy tiến trang trí trinh trung tú tuấn tùng tường uy uyên vân việt vinh vũ vy vỹ yến đào hậu""".split())
NOT_NAME_NEXT = """công viên phố thường tĩnh luận toàn tâm sự tiền phí nhận mắt lanh nhong nữ sinh bộ cảnh độ hành toán thật ra
họa chứng bạch quả sau này kia người cách trào tín lực phấn thịnh kiều điểm phục động chương tuệ nhớ óc án pháp tiện hướng
thức phúc kiểm hệ quan tục kết lạc nhất trì nhẫn quyết thắng đấu dịch lược trụ khí tính hàng sách quỹ lượng túng hòa nạp
viện giãn ký mục tạo tắc văn liệu niệm nghi lợi đội tế gia hội phòng bản tích lập thảo""".split()

# Cụm viết hoa có một trong các từ này là tổ chức, môn học, sản phẩm chứ không phải tên người.
NOT_NAME_TOKENS = set("""
Học Viện Nghệ Bưu Viễn Đội Niên Hiến Máu Thuật Lập Trình Truyền Kỹ Mềm Tiếng Media Sổ Khoa Ban Phòng Câu Lạc Bộ
Đại Giáo Môn Điểm Ngày Tháng Quận Phường Đường Phố Hội Chương Marketing
Google Microsoft Facebook Zalo Messenger Youtube Tiktok Data Machine Learning Science Studio Visual Java Python Web
Code Club University English Toeic Ielts Group Page Team Teams Meet Word Excel Online Game Test Guitar
Training TikTok YouTube LinkedIn GitHub PowerPoint Daisuki Daiyo Bài Phần Coffee
""".split())
# Các từ trong cụm này có thể là tên riêng nếu đứng một mình, nên phải khớp cả cụm.
NOT_NAME_PHRASES = ["Sinh Viên", "Thông Báo", "Tài Chính", "Hành Chính", "Kinh Tế", "Kế Toán", "Thông Tin", "Công Nghệ",
                    "Trung Thu"]
# Cụm mở đầu bằng họ phổ biến luôn là tên, kể cả khi dính liền tên tổ chức do tag nhiều người.
SURNAMES = set("Nguyễn Nguyen Trần Tran Lê Le Phạm Pham Hoàng Hoang Huỳnh Phan Vũ Vu Võ Vo Đặng Dang Bùi Bui Đỗ Do Ngô Ngo Đinh Dinh Trịnh Lương Khương Đào".split())
PLACES = {"Hà Nội", "Hà Đông", "Việt Nam", "Hồ Chí Minh", "Trần Phú", "Văn Quán", "Ao Sen", "Nguyễn Văn Trỗi",
          "Nguyễn Trãi", "Thanh Xuân", "Cầu Giấy", "Mộ Lao", "Đà Nẵng", "Hải Phòng", "Nam Định", "Bắc Ninh",
          "Thái Nguyên", "Thái Bình", "Quốc Oai", "Cao Nguyên"}
# Cấp tỉnh, thành và quận Hà Nội không đủ để nhận ra một người, lại có ích cho nội dung nên giữ.
PLACES |= set("""An Giang|Bà Rịa|Vũng Tàu|Bạc Liêu|Bắc Giang|Bắc Kạn|Bến Tre|Bình Dương|Bình Định|Bình Phước|Bình Thuận|Cà Mau
Cao Bằng|Cần Thơ|Đắk Lắk|Đắk Nông|Điện Biên|Đồng Nai|Đồng Tháp|Gia Lai|Hà Giang|Hà Nam|Hà Tĩnh|Hải Dương|Hậu Giang|Hòa Bình
Hoà Bình|Hưng Yên|Khánh Hòa|Khánh Hoà|Kiên Giang|Kon Tum|Lai Châu|Lạng Sơn|Lào Cai|Lâm Đồng|Long An|Nghệ An|Ninh Bình
Ninh Thuận|Phú Thọ|Phú Yên|Quảng Bình|Quảng Nam|Quảng Ngãi|Quảng Ninh|Quảng Trị|Sóc Trăng|Sơn La|Tây Ninh|Thanh Hóa|Thanh Hoá
Thừa Thiên Huế|Tiền Giang|Trà Vinh|Tuyên Quang|Vĩnh Long|Vĩnh Phúc|Yên Bái|Sài Gòn|Hoàn Kiếm|Đống Đa|Ba Đình|Hai Bà Trưng
Long Biên|Tây Hồ|Bắc Từ Liêm|Nam Từ Liêm|Từ Liêm|Thanh Trì|Gia Lâm|Đông Anh|Sóc Sơn|Hoàng Mai
Phùng Khoang|Triều Khúc|Yên Nghĩa|Kiến Hưng|Phú La|Văn Phú|Đại Mỗ|Mỗ Lao|Khương Đình|Kim Giang|Định Công|Linh Đàm
Mỹ Đình|Ngã Tư Sở|Láng Hạ|Hà Lội""".replace("\n", "|").split("|"))
# Nhiều huyện, trường trùng tên người ("Thanh Hà", "Duy Tân") nên chỉ giữ khi đứng sau từ chỉ nơi chốn.
with open(HERE / "danh_sach_dia_danh_truong.csv", encoding="utf-8-sig", newline="") as _file:
    _gazetteer = list(csv.DictReader(_file))
PLACES |= {row["ten"] for row in _gazetteer if row["dang"] == "ngan_ro_nghia"}
KEEP_WITH_CUE = {row["ten"] for row in _gazetteer}
ADMIN_AREAS = {row["ten"] for row in _gazetteer if row["loai"] in ("tinh_thanh", "quan_huyen")} | {"Việt Nam"}
PLACE_CUE = re.compile(r"(?i)(?:^|[\s(])(?:ở|tại|về|đến|tới|từ|học|quê(?: mình| tôi| em| tao)?|huyện|quận|tỉnh|thành phố|tp|thị xã|tx|khu vực|khu|trường|đại học|đh|học viện|cao đẳng|cđ|sinh viên|sv)[\s.:]*$")
# Sau danh xưng hoặc trước "ơi", các từ này không phải tên ("cô Văn", "Trời ơi").
NOT_NAME_SINGLE = set("""Toán Hóa Hoá Sử Sự Địa Tin Văn Anh Ơi Trời Ôi Mẹ Bố Ba Má Ad Admin Add Mọi Người Trường Mn Mng Cj Bn Ac Acj
Ace Ae Eo Tr Cháu Con Sợ Web Dự Đại Đội Pit Ní Ib Ibb Mik Mk Mjk Mnf Ko Kh Ny Vl Qt Ngta Dsa Bro Bump Claude Grok
Hust Ptit Udu Ok Oke Tao Mày Mình Rep Cmm Cmnr Cmn Vcl Vkl Đm Dm Đmm Dmm Đcm Dcm Clm Cc Cl""".split()) | SENTENCE_WORDS
# NER hay gắn nhầm chữ cái đơn ("t", "m" = tao, mày) và mã viết hoa ngắn (D26, TL) là tên người.
NER_NOT_NAME = re.compile(r"\w|[A-ZĐ0-9]{1,4}")
NOT_NAME_SINGLE |= {t.capitalize() for t in TITLES}

KEEP_MENTIONS = r"mọi người|nêu bật|everyone|highlight"
URL = re.compile(r"(?i)(?:https?://|www\.)\S*[^\s.,!?)]|\b[\w-]+(?:\.[\w-]+)*\.(?:com|vn|net|org|edu|io|me|ly|gl|co|info|xyz|link|app)\b(?:/\S*[^\s.,!?)])?")
EMAIL = re.compile(r"[\w.+-]+\s?@\s?[\w-]+(?:\.[\w-]+)+")
# Tên ẩn danh do Facebook tạo ("Người tham gia ẩn danh 756", "BluePanda1589"): không phải danh tính thật, che cho thống nhất.
PSEUDONYM = re.compile(r"Người tham gia ẩn danh(?:\s+\d+)?|Anonymous participant(?:\s+\d+)?|\b[A-Z][a-z]+[A-Z][a-z]+\d{2,5}\b")
MENTION = re.compile(rf"(?<!@)@(?![@\s])(?!(?i:{KEEP_MENTIONS}))(?:{CAP}(?:\s+{CAP}){{0,4}}|\S+)")
STUDENT_ID = re.compile(r"(?i)\b[bdn]\d{2}[a-z]{4}\d{2,3}\b")
PHONE = re.compile(r"(?<![\d.,])(?:\+?84[\s.-]?|0)(?:[35789](?:[\s.-]?\d){8}|2(?:[\s.-]?\d){9})(?!\d)")
LONG_NUMBER = re.compile(r"(?<![\d.,])\d{9,}(?![\d.,])")
NAME_SEQ = re.compile(rf"\b{CAP2}(?:\s+{CAP2})+\b")
TITLE_NAME = re.compile(rf"\b({TITLE_RE}|th|c|a|e)\s+({CAP2})\b")  # th, c, a, e là thầy, chị, anh, em viết tắt
SURNAME_ALT = "|".join(sorted(SURNAMES, key=len, reverse=True))
GIVEN_ALT = "|".join(sorted(GIVEN_NAMES | {"anh"}, key=len, reverse=True))
# Lấy cả từ tên thứ hai nếu có ("thầy tuấn anh", "cô giang lê").
LOWER_NAME = re.compile(rf"\b((?i:thầy|cô|anh|chị|th|c|a))\s+((?:{'|'.join(sorted(GIVEN_NAMES, key=len, reverse=True))})"
                        rf"(?:\s+(?:{GIVEN_ALT}|{SURNAME_ALT.lower()}))?)\b(?!\s+(?:{'|'.join(NOT_NAME_NEXT)})\b)")
INITIAL_NAME = re.compile(rf"\b[{UP}]\.\s?({CAP2})\b")  # "Q. Sáng"
NAME_FRAGMENTS = [(re.compile(rf"\[NAME\](?:\s+(?:{SURNAME_ALT})\b)+"), "[NAME]"),   # "[NAME] Đỗ"
                  (re.compile(rf"\b(?:(?:{SURNAME_ALT})\s+)+\[NAME\]"), "[NAME]"),
                  (re.compile(r"^Anh\s+\[NAME\]"), "[NAME]"),                      # "Anh" là một phần của tên được tag
                  # "[NAME] nhi hư": phần tên gõ thường dính sau tên đã che.
                  (re.compile(rf"\[NAME\]\s+(?:{'|'.join(sorted(GIVEN_NAMES, key=len, reverse=True))})\b"
                              rf"(?!\s+(?:{'|'.join(NOT_NAME_NEXT)})\b)"), "[NAME]")]
VOCATIVE = re.compile(rf"\b({CAP})(?=\s+ơi\b)")
NUM = r"\d+[a-zA-Z]?(?:/\d+)*"
ALLEY = r"(?i:ngõ|ngách|hẻm|kiệt|ngo|ngach|hem)"
HOUSE = rf"(?i:số)\s*(?i:nhà\s*)?{NUM}"
# Chỉ che địa chỉ có số (số nhà, ngõ, ngách). Mã tòa nhà như A2, B5 và tên đường đứng một mình được giữ.
ADDRESS = re.compile(rf"\b(?:{HOUSE}\s*,?\s*)?{ALLEY}\s*{NUM}(?:\s*,?\s*{ALLEY}\s*{NUM})*"
                     rf"|\b{HOUSE}\s*,?\s*(?:(?i:đường|phố)\s+)?(?P<area>{CAP}(?:\s+{CAP}){{0,3}})")
STREET_CUE = re.compile(r"(?i)(?:^|\s)(?:đường|phố)\s*$")
UPPER_NAME = re.compile(rf"\b(?:NGUYỄN|NGUYEN|TRẦN|TRAN|LÊ|PHẠM|PHAM|HOÀNG|HOANG|HUỲNH|PHAN|VŨ|VÕ|ĐẶNG|BÙI|ĐỖ|NGÔ|DƯƠNG|ĐINH)(?:\s+[{UP}]+){{1,3}}\b")

EMOJI = re.compile(r"[\U00010000-\U0010FFFF☀-➿]")
PLACEHOLDER = re.compile(r"\[(?:URL|EMAIL|USER|STUDENT_ID|PHONE|NUMBER|NAME|ADDRESS)\]")
AD = re.compile(r"(?i)inbox|\bib\b|zalo|tuyển dụng|cho thuê|phòng trọ|\bbán\s|\bpass\s|\bship\b|giá\s\d")

# Mô hình -> nhãn của mô hình cần che -> token. Sửa ở đây nếu compare_ner.py cho thấy cách kết hợp khác tốt hơn.
# Đã bỏ OpenMed: lần chạy 2026-11-11 nó che nhầm "1", "b", "A2", "ptit" thành địa chỉ, nay địa chỉ dùng luật ADDRESS.
NER_MODELS = {"NlpHUST/ner-vietnamese-electra-base": {"PERSON": "[NAME]"}}
NER_BATCH_SIZE, CHUNK_CHARS, CHUNK_OVERLAP = 32, 600, 50  # bài đăng dài phải cắt nhỏ vì mô hình giới hạn 512 token


def normalize(text):
    text = unicodedata.normalize("NFC", str(text))
    text = re.sub(r"^'(?=[@=+-])", "", text)  # dấu ' do bước xuất Excel thêm vào
    return re.sub(r"\s+", " ", text).strip()


def replace_name_seq(match):
    tokens = match.group().split()
    joined = " ".join(tokens)
    is_org = NOT_NAME_TOKENS & set(tokens) or any(phrase in joined for phrase in NOT_NAME_PHRASES)
    if joined in PLACES:
        return match.group()
    if is_org and tokens[0] not in SURNAMES:
        # "Lam Anh Trung Thu về trường": tag tên đứng trước cụm tổ chức, sự kiện thì vẫn che phần tên.
        org_at = next(i for i in range(len(tokens)) if tokens[i] in NOT_NAME_TOKENS
                      or any(" ".join(tokens[i:]).startswith(p) for p in NOT_NAME_PHRASES))
        return match.group() if org_at < 2 else " ".join(["[NAME]"] + tokens[org_at:])
    prefix = match.string[:match.start()]
    if (joined in KEEP_WITH_CUE and PLACE_CUE.search(prefix)) or STREET_CUE.search(prefix):
        return match.group()  # tên đường đặt theo danh nhân, không phải tên người dùng
    lead, trail = [], []
    while tokens and tokens[0] in SENTENCE_WORDS:
        lead.append(tokens.pop(0))
    while tokens and tokens[-1] in SENTENCE_WORDS:
        trail.insert(0, tokens.pop())
    if not tokens or (len(tokens) == 1 and tokens[0] in NOT_NAME_SINGLE):
        return match.group()
    title = len(tokens) > 1 and tokens[0].lower() in TITLES
    if title and len(tokens) == 2 and tokens[1] in NOT_NAME_SINGLE:
        return match.group()
    if title and tokens[0] == "Anh" and not lead and match.start() == 0:
        title = False  # "Anh Thư Nguyễn" ở đầu câu thường là tag tên, chữ "Anh" thuộc về tên
    # shortcut: cụm dài không rõ loại cũng bị che, ưu tiên không lộ tên hơn là giữ tiêu đề viết hoa.
    return " ".join(lead + [f"{tokens[0]} [NAME]" if title else "[NAME]"] + trail)


def merge_name_fragments(text):
    for pattern, repl in NAME_FRAGMENTS:
        text = pattern.sub(repl, text)
    return text


def replace_initial_name(match):
    rest = match.string[match.start(1):]
    if match.group(1) in NOT_NAME_SINGLE | NOT_NAME_TOKENS:  # "A. Bài 1" là đáp án, không phải tên
        return match.group()
    return match.group() if any(rest.startswith(p) for p in PLACES | ADMIN_AREAS) else "[NAME]"


def mask(text):
    """Trả về (văn bản đã che, các loại đã che). Email chạy trước URL vì đuôi gmail.com cũng khớp mẫu URL."""
    found = set()

    def sub(pattern, repl, value, kind):
        new = pattern.sub(repl, value)
        if new != value:
            found.add(kind)
        return new

    text = sub(EMAIL, "[EMAIL]", text, "EMAIL")
    text = sub(URL, "[URL]", text, "URL")
    text = sub(PSEUDONYM, "[USER]", text, "USER")
    text = sub(MENTION, "[USER]", text, "USER")
    text = sub(STUDENT_ID, "[STUDENT_ID]", text, "STUDENT_ID")
    text = sub(PHONE, "[PHONE]", text, "PHONE")
    text = sub(LONG_NUMBER, "[NUMBER]", text, "NUMBER")
    # "đội số 3 Hà Nội" là thứ hạng, không phải số nhà: bỏ qua khi sau số là tên tỉnh, quận.
    text = sub(ADDRESS, lambda m: m.group() if m.group("area") in ADMIN_AREAS else "[ADDRESS]", text, "ADDRESS")
    text = sub(UPPER_NAME, "[NAME]", text, "NAME")
    text = sub(NAME_SEQ, replace_name_seq, text, "NAME")
    text = sub(INITIAL_NAME, replace_initial_name, text, "NAME")
    text = sub(TITLE_NAME, lambda m: m.group() if m.group(2) in NOT_NAME_SINGLE else f"{m.group(1)} [NAME]", text, "NAME")
    text = sub(LOWER_NAME, lambda m: f"{m.group(1)} [NAME]", text, "NAME")
    text = sub(VOCATIVE, lambda m: m.group() if m.group(1) in NOT_NAME_SINGLE else "[NAME]", text, "NAME")
    return merge_name_fragments(text), ";".join(sorted(found))


def split_chunks(text):
    """Cắt văn bản dài ở khoảng trắng, các đoạn gối nhau để không làm đứt một tên ở ranh giới."""
    start = 0
    while start < len(text):
        end = min(start + CHUNK_CHARS, len(text))
        if end < len(text):
            space = text.rfind(" ", start + CHUNK_CHARS // 2, end)
            end = space if space > 0 else end
        yield start, text[start:end]
        if end == len(text):
            break
        start = max(end - CHUNK_OVERLAP, start + 1)


def apply_entities(text, spans):
    """Thay các đoạn NER tìm được bằng token, không đụng vào token regex đã che."""
    taken = [m.span() for m in PLACEHOLDER.finditer(text)]
    kept = []
    for start, end, token in sorted(spans):
        # Cắt khoảng trắng, emoji, dấu câu dính ở hai đầu để không xóa mất emoji bên cạnh tên.
        while start < end and not text[start].isalnum():
            start += 1
        while start < end and not text[end - 1].isalnum():
            end -= 1
        value = text[start:end]
        # NER hiểu ngữ cảnh nên nếu nó bảo "Hải Dương" là tên người thì vẫn che, chỉ không che địa danh thành địa chỉ.
        if start == end or ((value in PLACES or value in KEEP_WITH_CUE) and token == "[ADDRESS]"):
            continue
        if token == "[NAME]" and (value.capitalize() in NOT_NAME_SINGLE or NER_NOT_NAME.fullmatch(value)):
            continue
        if any(s < end and start < e for s, e in taken):
            continue
        if kept and start < kept[-1][1]:
            kept[-1] = (kept[-1][0], max(end, kept[-1][1]), kept[-1][2])
        else:
            kept.append((start, end, token))
    for start, end, token in reversed(kept):
        text = text[:start] + token + text[end:]
    return merge_name_fragments(text), {token.strip("[]") for _, _, token in kept}


def detect_entities(chunks):
    """Trả về {đoạn văn bản: [(đầu, cuối, token)]} cho mọi mô hình trong NER_MODELS."""
    import torch
    from transformers import AutoTokenizer, pipeline

    device = 0 if torch.cuda.is_available() else -1
    found = {chunk: [] for chunk in chunks}
    for model_id, groups in NER_MODELS.items():
        print("Đang chạy", model_id, "trên", "GPU" if device == 0 else "CPU", flush=True)
        tokenizer = AutoTokenizer.from_pretrained(model_id, model_max_length=512)
        ner = pipeline("token-classification", model=model_id, tokenizer=tokenizer,
                       aggregation_strategy="first", device=device)
        for chunk, entities in zip(chunks, ner(chunks, batch_size=NER_BATCH_SIZE)):
            found[chunk] += [(e["start"], e["end"], groups[e["entity_group"]]) for e in entities if e["entity_group"] in groups]
    return found


def mask_with_ner(texts):
    """Trả về {văn bản đã qua regex: (văn bản đã che thêm, các loại NER đã che)}."""
    pieces = {text: list(split_chunks(text)) for text in texts}
    entities = detect_entities(sorted({chunk for parts in pieces.values() for _, chunk in parts}))
    result = {}
    for text, parts in pieces.items():
        spans = [(offset + start, offset + end, token) for offset, chunk in parts for start, end, token in entities[chunk]]
        result[text] = apply_entities(text, spans)
    return result


def self_check():
    assert list(split_chunks("")) == [] and list(split_chunks("abc")) == [(0, "abc")]
    long_text = "tu " * 400
    parts = list(split_chunks(long_text))
    assert all(len(c) <= CHUNK_CHARS for _, c in parts) and parts[-1][0] + len(parts[-1][1]) == len(long_text)
    assert all(long_text[o:o + len(c)] == c for o, c in parts)
    assert apply_entities("gặp trang ở số 5 Lê Lợi", [(4, 9, "[NAME]"), (12, 23, "[ADDRESS]")]) == ("gặp [NAME] ở [ADDRESS]", {"NAME", "ADDRESS"})
    assert apply_entities("Lan 😢 ơi", [(0, 5, "[NAME]")]) == ("[NAME] 😢 ơi", {"NAME"})
    for word in ["T", "m", "Ib", "D26", "Mik"]:
        assert apply_entities(f"{word} ngu vl", [(0, len(word), "[NAME]")])[0] == f"{word} ngu vl", word
    assert apply_entities("An ơi", [(0, 2, "[NAME]")])[0] == "[NAME] ơi"
    assert mask("nhà mình số 12 ngõ 5 Trần Phú nhé")[0] == "nhà mình [ADDRESS] Trần Phú nhé"
    assert mask("qua số 96 Trần Phú lấy đồ")[0] == "qua [ADDRESS] lấy đồ"
    assert mask("ngách 3/14 đường Chiến Thắng")[0] == "[ADDRESS] đường Chiến Thắng"
    assert mask("đội số 3 Hà Nội")[0] == "đội số 3 Hà Nội"
    assert mask("học ở tòa A2 tầng 3")[0] == "học ở tòa A2 tầng 3"
    assert mask("trường top số 1 Việt Nam")[0] == "trường top số 1 Việt Nam"
    assert apply_entities("[NAME] nhé", [(0, 6, "[NAME]")]) == ("[NAME] nhé", set())
    assert apply_entities("anh ơi", [(0, 3, "[NAME]")]) == ("anh ơi", set())
    # Các lỗi tìm được khi soát tay 500 câu ngày 2026-11-12.
    soat_tay = {
        "Người tham gia ẩn danh 756 đúng rồi": "[USER] đúng rồi",
        "BluePanda1589 với": "[USER] với",
        "Anh Thư Nguyễn cho em hỏi": "[NAME] cho em hỏi",
        "Lsđ th Ninh, c VAnh dạy hay": "Lsđ th [NAME], c [NAME] dạy hay",
        "TTuấnn AAnhh thầy oii": "[NAME] thầy oii",
        "Lan Anh Q. Sáng tớ k rõ": "[NAME] [NAME] tớ k rõ",
        "học thầy sơn khó lắm": "học thầy [NAME] khó lắm",
        "anh nam anh lên tiếng đi": "anh [NAME] lên tiếng đi",  # "nam anh" cũng có thể là tên Nam Anh
        "Ô a Vỹ ne": "Ô a [NAME] ne",
        "bạn nam nữ đều được": "bạn nam nữ đều được",
        "chị thanh toán chưa": "chị thanh toán chưa",
        "anh hùng bàn phím": "anh hùng bàn phím",
        "Hoàng Năm ngoái anh thi": "[NAME] Năm ngoái anh thi",
        "học phần tiếng Anh Cũng không miễn": "học phần tiếng Anh Cũng không miễn",
        "Cảm Ơn Bạn nhé": "Cảm Ơn Bạn nhé",
        "Ở Phùng Khoang có quán ngon": "Ở Phùng Khoang có quán ngon",
        "Trung Thu về trường hội trại": "Trung Thu về trường hội trại",
        "nhà ở Q. Thanh Xuân": "nhà ở Q. Thanh Xuân",
        "Nguyễn Văn An Đỗ gu của em": "[NAME] gu của em",
        "Lam Anh Trung Thu về trường": "[NAME] Trung Thu về trường",
        "Linh Chi nhi hư": "[NAME] hư",
        "lên Hà Lội học": "lên Hà Lội học",
        "học thầy tuấn anh thì ổn": "học thầy [NAME] thì ổn",
        "A. Bài 1 đúng": "A. Bài 1 đúng",
    }
    for raw, want in soat_tay.items():
        assert mask(raw)[0] == want, (raw, mask(raw)[0])
    assert apply_entities("Cmm nói thế", [(0, 3, "[NAME]")])[0] == "Cmm nói thế"
    assert apply_entities("Đỗ Lan đẹp", [(3, 6, "[NAME]")])[0] == "[NAME] đẹp"
    assert apply_entities("Anh Thư ơi", [(4, 7, "[NAME]")])[0] == "[NAME] ơi"
    assert mask("Thanh Hóa là quê tôi")[0] == "Thanh Hóa là quê tôi"
    assert mask("quê mình Thanh Hà đó")[0] == "quê mình Thanh Hà đó"
    assert mask("Thanh Hà đi chưa")[0] == "[NAME] đi chưa"
    assert mask("sinh viên Đại học Bách Khoa")[0] == "sinh viên Đại học Bách Khoa"
    assert mask("em học Duy Tân")[0] == "em học Duy Tân"
    assert apply_entities("Thanh Hóa là quê tôi", [(0, 9, "[ADDRESS]")])[0] == "Thanh Hóa là quê tôi"
    assert apply_entities("Hải Dương đi chưa", [(0, 9, "[NAME]")])[0] == "[NAME] đi chưa"
    assert apply_entities("a Trang b", [(2, 5, "[NAME]"), (4, 7, "[NAME]")]) == ("a [NAME] b", {"NAME"})
    cases = {
        "Liên hệ 0912.345.678 nhé": "Liên hệ [PHONE] nhé",
        "mail abc.d@gmail.com ạ": "mail [EMAIL] ạ",
        "xem https://fb.com/x?a=1, hay": "xem [URL], hay",
        "B21DCCN123 nộp bài": "[STUDENT_ID] nộp bài",
        "@Nguyễn Văn An vào xem": "[USER] vào xem",
        "@mọi người ơi": "@mọi người ơi",
        "Thầy Nguyễn Văn An chấm gắt": "Thầy [NAME] chấm gắt",
        "thầy Nam dạy hay": "thầy [NAME] dạy hay",
        "Minh Đức ơi đi học": "[NAME] ơi đi học",
        "Trời ơi đỉnh vl 😂": "Trời ơi đỉnh vl 😂",
        "Học ở Hà Nội": "Học ở Hà Nội",
        "Nguyễn Trang Nguyễn Hà Trang Trần Văn An xem nè": "[NAME] xem nè",
        "Minh Tài đi chưa": "[NAME] đi chưa",
        "Đội Thanh Niên Vận Động Học Viện tuyển": "Đội Thanh Niên Vận Động Học Viện tuyển",
        "Mn ơi cho hỏi": "Mn ơi cho hỏi",
        "cô Văn cho điểm": "cô Văn cho điểm",
        "giảng đường đông lắmmm :)))": "giảng đường đông lắmmm :)))",
    }
    for raw, want in cases.items():
        assert mask(normalize(raw))[0] == want, (raw, mask(normalize(raw))[0])
    assert normalize("'@mọi người") == "@mọi người" and normalize("'abc") == "'abc"


def load_id_map(post_ids):
    """Giữ ID ổn định giữa các lần chạy, ID mới là ngẫu nhiên nên không suy ngược được."""
    path = PRIVATE / "id_map.csv"
    known = pd.read_csv(path, dtype=str) if path.exists() else pd.DataFrame(columns=["post_id", "post_uid"])
    mapping = dict(zip(known.post_id, known.post_uid))
    for pid in post_ids:
        mapping.setdefault(pid, "p" + secrets.token_hex(6))
    assert len(set(mapping.values())) == len(mapping)
    pd.DataFrame(mapping.items(), columns=["post_id", "post_uid"]).to_csv(path, index=False)
    return mapping


def split_by_post(df):
    sizes = df.groupby("post_uid").size()
    posts = sorted(sizes.index)
    random.Random(SEED).shuffle(posts)
    total, seen, assign = len(df), 0, {}
    for post in posts:
        ratio = seen / total
        assign[post] = "train" if ratio < 0.70 else "val" if ratio < 0.85 else "test"
        seen += sizes[post]
    return df.post_uid.map(assign)


def main():
    self_check()
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_INPUT
    PRIVATE.mkdir(parents=True, exist_ok=True)
    (OUT / ".gitignore").write_text("*\n", encoding="utf-8")  # dữ liệu không được lên repo

    raw = pd.read_excel(source, dtype={"post_id": str, "comment_id": str})
    report = {"rows_input": len(raw), "posts_input": raw.post_id.nunique()}
    id_map = load_id_map(raw.post_id.unique())

    df = pd.DataFrame({"post_uid": raw.post_id.map(id_map), "comment_type": raw.comment_type, "data_status": raw.data_status})
    df["comment_uid"] = df.post_uid + "_" + raw.comment_id
    df["parent_uid"] = df.post_uid + "_" + raw.parent_comment_id.astype("Int64").astype("string")
    assert df.comment_uid.is_unique

    # Che trên giá trị duy nhất để nhanh hơn, và cùng một câu luôn cho cùng một kết quả.
    columns = {"post_text": "post_message", "parent_text": "parent_message", "text_public": "message_original"}
    original_comment = raw.message_original.fillna("").map(normalize)
    normalized = {new: raw[old].fillna("").map(normalize) for new, old in columns.items()}
    regex_masked = {value: mask(value) for value in pd.unique(pd.concat(normalized.values()))}
    ner_masked = mask_with_ner(sorted({text for text, _ in regex_masked.values() if text}))
    final = {"": ("", "")}
    for value, (text, kinds) in regex_masked.items():
        if text:
            new_text, ner_kinds = ner_masked[text]
            final[value] = (new_text, ";".join(sorted(set(filter(None, kinds.split(";"))) | ner_kinds)))
    for new, series in normalized.items():
        df[new] = series.map(lambda v: final[v][0])
    df["pii_types"] = normalized["text_public"].map(lambda v: final[v][1])

    empty = df.text_public == ""
    duplicate = ~empty & df.duplicated(["post_uid", "parent_text", "text_public"])
    report |= {"removed_empty": int(empty.sum()), "removed_same_context_duplicates": int(duplicate.sum())}
    df[duplicate | empty][["comment_uid"]].to_csv(PRIVATE / "removed_rows.csv", index=False)
    keep = ~(empty | duplicate)
    df, original_comment = df[keep].reset_index(drop=True), original_comment[keep].reset_index(drop=True)

    # Chỉ gắn cờ, quyết định loại hay giữ sau khi đã soát mẫu.
    bare = df.text_public.str.replace(r"[^\w\s]", "", regex=True).str.casefold().str.strip()
    frequent_short = bare.map(bare.value_counts()).ge(20) & bare.str.split().str.len().le(2)
    only_placeholder = df.text_public.str.replace(PLACEHOLDER, "", regex=True).str.strip() == ""
    df["is_low_info"] = (frequent_short & ~df.text_public.str.contains(EMOJI)) | only_placeholder
    df["is_spam_candidate"] = df.text_public.str.contains(AD)
    df["post_is_ad_candidate"] = df.post_text.str.contains(AD)
    df["parent_missing"] = (df.comment_type == "reply") & (df.parent_text == "")
    df["post_missing"] = df.post_text == ""

    df["split"] = split_by_post(df)
    assert df.groupby("post_uid").split.nunique().max() == 1
    splits_per_text = df.groupby("text_public").split.transform("nunique")
    df["cross_split_duplicate"] = (splits_per_text > 1) & ~df.is_low_info

    # Không còn mẫu định danh dạng cấu trúc trong các cột sẽ gán nhãn hoặc công bố.
    for column in columns:
        for name, pattern in {"URL": URL, "EMAIL": EMAIL, "PHONE": PHONE, "STUDENT_ID": STUDENT_ID}.items():
            assert not df[column].str.contains(pattern).any(), (column, name)
    # Che thông tin không được làm mất emoji của bình luận.
    lost_emoji = (original_comment.str.count(EMOJI) != df.text_public.str.count(EMOJI)).sum()
    report["rows_where_emoji_count_changed"] = int(lost_emoji)

    order = ["post_uid", "comment_uid", "parent_uid", "comment_type", "post_text", "parent_text", "text_public", "split",
             "data_status", "pii_types", "is_low_info", "is_spam_candidate", "post_is_ad_candidate", "parent_missing",
             "post_missing", "cross_split_duplicate"]
    df[order].to_csv(OUT / "masked.csv", index=False, encoding="utf-8-sig")

    # Mẫu soát tay: một nửa ngẫu nhiên để đo bỏ sót, một nửa đã che để đo che nhầm.
    changed = df[df.pii_types != ""].sample(n=min(250, (df.pii_types != "").sum()), random_state=SEED)
    plain = df[df.pii_types == ""].sample(n=250, random_state=SEED)
    audit = pd.concat([plain, changed])
    audit = pd.DataFrame({"comment_uid": audit.comment_uid, "original": original_comment[audit.index],
                          "masked": audit.text_public, "pii_left": "", "over_masked": ""})
    audit.to_csv(PRIVATE / "audit_sample.csv", index=False, encoding="utf-8-sig")

    report |= {
        "rows_output": len(df),
        "posts_output": int(df.post_uid.nunique()),
        "pii_rows_comment": {kind: int(df.pii_types.str.contains(kind).sum()) for kind in ["URL", "EMAIL", "USER", "STUDENT_ID", "PHONE", "NUMBER", "NAME", "ADDRESS"]},
        "flags": {c: int(df[c].sum()) for c in ["is_low_info", "is_spam_candidate", "post_is_ad_candidate", "parent_missing", "post_missing", "cross_split_duplicate"]},
        "split_rows": df.split.value_counts().to_dict(),
    }
    (OUT / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

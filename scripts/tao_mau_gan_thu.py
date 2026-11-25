"""Tạo file Excel gán thử cho từng người trong nhóm.

Chạy (từ thư mục gốc repo): python scripts/tao_mau_gan_thu.py [số vòng]   (mặc định vòng 1)
Đầu vào: data/cleaned/masked.csv.
Kết quả: data/gan_nhan/vong<N>/gan_thu_vong<N>_<Tên>.xlsx cho từng người và tong_hop_vong<N>.csv (ghi nguồn mẫu).
Câu đã dùng ở các vòng trước không bị lấy lại.
"""
import random
import sys
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

DATA = Path(__file__).resolve().parents[1] / "data"
MASKED = DATA / "cleaned" / "masked.csv"
OUT_ROOT = DATA / "gan_nhan"
NGUOI_GAN = {"Hao": "Hảo", "Sinh": "Sinh", "Trieu": "Triệu", "Long": "Long"}
N_CAU, N_NGAU_NHIEN = 240, 120  # còn lại chia đều cho các nhóm nhãn hiếm của vòng
MAX_MOI_BAI = 2
SEED = 42

# Nhãn tiếng Anh theo Quy_chuan_gan_nhan_4_huong_NLP_N12.docx (bản nháp 2).
NHAN = {
    "toxicity": ["clean", "profane", "attack", "unk"],
    "topic": ["academics", "facilities", "administration", "student_life", "unk"],
    "stance": ["support", "oppose", "suggest", "none", "unk"],
    "emotion": ["joy", "sadness", "anger", "fear", "surprise", "neutral", "unk"],
}
# Dấu hiệu chỉ dùng để chọn câu có khả năng mang nhãn hiếm, không phải nhãn.
# Mỗi vòng nhắm vào các nhãn còn hiếm trong gold các vòng trước; giữ nguyên vòng cũ để chạy lại ra đúng mẫu.
DAU_HIEU_THEO_VONG = {
    1: {
        "hiem_tu_tuc": r"(?i)\b(?:vl|vcl|vkl|vãi|đm|dm|đmm|đcm|dcm|cmm|cc|clm|đéo|địt|lồn|loz|ngu|óc chó|cút|súc vật|mất dạy|khốn nạn)\b",
        "hiem_de_xuat": r"(?i)\b(?:mong (?:trường|học viện|nhà trường|thầy|cô|ban|khoa)|nên (?:mở|cho|có|thêm|làm|bỏ|tổ chức|lắp|sửa|xem xét)|đề nghị|kiến nghị|đề xuất|hy vọng (?:trường|học viện|nhà trường)|giá mà)\b",
        "hiem_cam_xuc": r"(?i)😭|😡|😢|🥲|😤|😱|\b(?:lo quá|sợ|hoang mang|sốc|ức chế|bực|buồn|chán|vui quá|tự hào|áp lực)\b",
    },
    # Gold vòng 1 sau rà soát: facilities 6, anger 11, surprise 12, support 23, attack 25 trên 240 câu.
    2: {
        "hiem_cong_kich": r"(?i)\b(?:ngu|óc chó|đần|ngáo|khùng|bịp|cút|câm mồm|súc vật|mất dạy|vô học|khốn nạn|rác rưởi|não tôm|ăn hại|vô dụng)\b|🤡",
        "hiem_co_so_vat_chat": r"(?i)\b(?:phòng học|điều hòa|điều hoà|wifi|wi-fi|mạng trường|thư viện|căng tin|canteen|nhà xe|bãi xe|gửi xe|ktx|ký túc|kí túc|máy chiếu|thang máy|nhà vệ sinh|wc|toilet|phòng máy|sân bóng|giảng đường|bàn ghế|ổ điện)\b",
        "hiem_tuc_gian_ngac_nhien": r"(?i)😡|😤|🤬|😱|😳|😲|\b(?:ức chế|bực|tức (?:thật|ghê|quá|điên|mình)|nghe tức|điên tiết|cay cú|phẫn nộ|vô lý|sốc|thật hả|bất ngờ|không tin nổi|hả trời)\b",
        "hiem_ung_ho": r"(?i)\b(?:cảm ơn (?:trường|thầy|cô|học viện|nhà trường)|tuyệt vời|tự hào|yêu trường|dạy hay|dạy dễ hiểu|nhiệt tình|xứng đáng|tâm lý quá)\b",
    },
}
COT = [("stt", 6), ("post_text", 45), ("parent_text", 35), ("text_public", 55), ("toxicity", 12), ("topic", 15),
       ("stance", 11), ("emotion_1", 12), ("emotion_2", 20), ("hard", 6), ("note", 25), ("comment_uid", 20)]


def chon_mau(df, rng, used, vong):
    dau_hieu = DAU_HIEU_THEO_VONG.get(vong, DAU_HIEU_THEO_VONG[max(DAU_HIEU_THEO_VONG)])
    n_moi_nhom = (N_CAU - N_NGAU_NHIEN) // len(dau_hieu)
    pool = df[(df.split == "train") & (df.is_low_info == "False") & (df.is_spam_candidate == "False")
              & ~df.comment_uid.isin(used) & df.text_public.str.len().between(5, 400)]
    chosen, per_post = [], {}

    def take(rows, n, nguon):
        for _, row in rows.sample(frac=1, random_state=rng.randint(0, 10**6)).iterrows():
            if len([c for c in chosen if c[1] == nguon]) >= n:
                break
            if row.comment_uid in {c[0] for c in chosen} or per_post.get(row.post_uid, 0) >= MAX_MOI_BAI:
                continue
            per_post[row.post_uid] = per_post.get(row.post_uid, 0) + 1
            chosen.append((row.comment_uid, nguon))

    take(pool, N_NGAU_NHIEN, "ngau_nhien")
    for nguon, pattern in dau_hieu.items():
        take(pool[pool.text_public.str.contains(pattern, regex=True)], n_moi_nhom, nguon)
    picked = pd.DataFrame(chosen, columns=["comment_uid", "nguon_mau"])
    out = picked.merge(df, on="comment_uid")
    out = out.sample(frac=1, random_state=SEED).reset_index(drop=True)  # trộn để người gán không đoán được nguồn
    out.insert(0, "stt", range(1, len(out) + 1))
    return out


def ghi_excel(mau, path, ten):
    wb = Workbook()
    ws = wb.active
    ws.title = "gan_nhan"
    lists = wb.create_sheet("danh_sach_nhan")
    for col, (key, values) in enumerate(NHAN.items(), 1):
        lists.cell(1, col, key)
        for row, value in enumerate(values, 2):
            lists.cell(row, col, value)
    lists.sheet_state = "hidden"

    for col, (name, width) in enumerate(COT, 1):
        cell = ws.cell(1, col, name)
        cell.font = Font(bold=True)
        cell.fill = PatternFill("solid", fgColor="DDEBF7" if col in range(5, 12) else "E7E6E6")
        ws.column_dimensions[cell.column_letter].width = width
    for r, row in enumerate(mau.itertuples(index=False), 2):
        for col, (name, _) in enumerate(COT, 1):
            value = getattr(row, name) if name in mau.columns else ""
            ws.cell(r, col, value).alignment = Alignment(wrap_text=True, vertical="top")
    last = len(mau) + 1

    def dropdown(col_letters, list_col, n):
        dv = DataValidation(type="list", formula1=f"=danh_sach_nhan!${list_col}$2:${list_col}${n + 1}", allow_blank=True,
                            showErrorMessage=True, error="Chọn nhãn trong danh sách")
        ws.add_data_validation(dv)
        for letter in col_letters:
            dv.add(f"{letter}2:{letter}{last}")

    dropdown(["E"], "A", len(NHAN["toxicity"]))
    dropdown(["F"], "B", len(NHAN["topic"]))
    dropdown(["G"], "C", len(NHAN["stance"]))
    dropdown(["H"], "D", len(NHAN["emotion"]))  # emotion_2 gõ tay nhiều nhãn nên không giới hạn bằng danh sách
    kho = DataValidation(type="list", formula1='"x"', allow_blank=True)
    ws.add_data_validation(kho)
    kho.add(f"J2:J{last}")
    ws.freeze_panes = "E2"
    ws.auto_filter.ref = f"A1:L{last}"

    guide = wb.create_sheet("huong_dan", 0)
    lines = [f"Người gán: {ten}", "",
             "Gán ĐỘC LẬP: không bàn với người khác, không xem file của người khác.",
             "Chỉ gán cho cột text_public. post_text và parent_text chỉ để hiểu ngữ cảnh.",
             "Theo quy chuẩn trong file Quy_chuan_gan_nhan_4_huong_NLP_N12.docx, đọc kỹ mục 7 (quy tắc rút ra từ vòng 1). Nhắc lại:",
             "  stance phải hướng tới một chủ đề của trường; topic = unk thì stance chỉ được là none hoặc unk.",
             "  Đồng tình hay phản bác người đối thoại, chửi bạn, đùa trong hội thoại: stance = none (trừ khi bình luận cha nói về chủ đề của trường).",
             "  suggest: lời khuyên hoặc góp ý chỉ cụ thể việc cần làm, nơi cần đến. Chỉ trả lời được hay không, khi nào, bao nhiêu: none.",
             "  Nhờ vả, rủ rê, xin cho bản thân, quảng cáo, chiêu mộ CLB, câu hỏi: none.",
             "  Góp ý mỉa mai hoặc mong muốn chung chung không có hành động: oppose.",
             "  topic = unk chỉ khi câu không nói về việc gì (chỉ cảm thán, tag tên, emoji).",
             "toxicity, topic, stance, emotion_1: chọn từ danh sách thả xuống (nhãn tiếng Anh).",
             "  toxicity: clean, profane, attack, unk",
             "  topic: academics, facilities, administration, student_life, unk",
             "  stance: support, oppose, suggest, none, unk",
             "  emotion: joy, sadness, anger, fear, surprise, neutral, unk",
             "emotion_1: cảm xúc chính. emotion_2: các cảm xúc còn lại xếp giảm dần theo độ rõ, cách nhau bằng dấu ; (ví dụ: fear; sadness).",
             "Chỉ 1 cảm xúc, hoặc neutral, hoặc unk: để trống emotion_2.",
             "unk chỉ dùng khi đã xem cả ngữ cảnh mà vẫn không chọn được nhãn. Không dùng unk thay cho none hay neutral.",
             "Chọn được nhãn nhưng không chắc thì điền x ở cột hard, ghi lý do ở note (ví dụ: dùng ngữ cảnh).",
             "Không sửa, xóa hay sắp xếp lại các cột stt, text_public, comment_uid.",
             "Gán xong lưu lại đúng tên file và gửi cho người tổng hợp."]
    for r, text in enumerate(lines, 1):
        guide.cell(r, 1, text).font = Font(bold=(r == 1))
    guide.column_dimensions["A"].width = 100
    wb.active = 1
    wb.save(path)


def main():
    vong = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    out_dir = OUT_ROOT / f"vong{vong}"
    out_dir.mkdir(parents=True, exist_ok=True)
    (OUT_ROOT / ".gitignore").write_text("*\n", encoding="utf-8")  # dữ liệu chưa công bố, không đưa lên repo
    used = set()
    for old in OUT_ROOT.glob("vong*/tong_hop_vong*.csv"):
        if old.parent != out_dir:
            used |= set(pd.read_csv(old, dtype=str).comment_uid)

    df = pd.read_csv(MASKED, dtype=str, keep_default_na=False)
    mau = chon_mau(df, random.Random(SEED + vong), used, vong)
    assert len(mau) == N_CAU, f"chỉ lấy được {len(mau)} câu"
    assert mau.comment_uid.is_unique and not mau.comment_uid.isin(used).any()
    assert (mau.split == "train").all() and mau.groupby("post_uid").size().max() <= MAX_MOI_BAI

    mau[["stt", "comment_uid", "post_uid", "nguon_mau"]].to_csv(out_dir / f"tong_hop_vong{vong}.csv", index=False, encoding="utf-8-sig")
    for code, ten in NGUOI_GAN.items():
        ghi_excel(mau, out_dir / f"gan_thu_vong{vong}_{code}.xlsx", ten)
    print(f"Vòng {vong}: {len(mau)} câu, {mau.post_uid.nunique()} bài đăng")
    print(mau.nguon_mau.value_counts().to_string())
    print("Đã tạo trong", out_dir)


if __name__ == "__main__":
    main()

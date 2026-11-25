"""Gộp các file gán thử của nhiều người, đánh dấu câu lệch nhãn và tính độ đồng thuận.

Chạy: python scripts/tong_hop_gan_thu.py <file_ra.xlsx> <file_gan_1.xlsx> <file_gan_2.xlsx> [...]
Tên người lấy từ tên file (gan_thu_vong1_<Tên>.xlsx).

Quy tắc gộp (theo quy chuẩn bản nháp 2, mục 7):
- toxicity, topic, stance: mọi người cùng nhãn thì chốt luôn; có từ 3 người thì nhãn quá nửa được đề xuất;
  còn lại để trống cột chốt và tô màu để nhóm phân xử (như OLID, ViHSD: bất đồng thì người thứ 3 hoặc nhóm quyết định).
- emotion: giữ cảm xúc có ít nhất 2 người cùng chọn (như GoEmotions); với 2 người tức là cả hai cùng chọn.
"""
import difflib
import itertools
import re
import sys
from collections import Counter
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

NHAN = {
    "toxicity": ["clean", "profane", "attack", "unk"],
    "topic": ["academics", "facilities", "administration", "student_life", "unk"],
    "stance": ["support", "oppose", "suggest", "none", "unk"],
    "emotion": ["joy", "sadness", "anger", "fear", "surprise", "neutral", "unk"],
}
DON_NHAN = ["toxicity", "topic", "stance"]
EXCLUSIVE = {"neutral", "unk"}
# File tạo trước bản nháp 2 có tên cột tiếng Việt.
COT_CU = {"doc_hai": "toxicity", "chu_de": "topic", "lap_truong": "stance", "cam_xuc_1": "emotion_1",
          "cam_xuc_2": "emotion_2", "kho": "hard", "ghi_chu": "note"}
VANG, DO, CAM = PatternFill("solid", fgColor="FFF2CC"), PatternFill("solid", fgColor="F8CBAD"), PatternFill("solid", fgColor="FCE4D6")


def chuan_hoa(value, axis, sua, nguoi, stt):
    """Đưa nhãn về đúng danh sách; sửa lỗi gõ gần đúng ("suprise") và ghi lại để báo cáo."""
    raw = str(value).strip()
    v = raw.lower().replace(" ", "_")
    if v in NHAN[axis] or v == "":
        return v
    gan = difflib.get_close_matches(v, NHAN[axis], n=1, cutoff=0.75)
    sua.append({"nguoi": nguoi, "stt": stt, "huong": axis, "gia_tri_goc": raw, "sua_thanh": gan[0] if gan else "(không sửa được)"})
    return gan[0] if gan else v


def doc_file(path, sua):
    nguoi = re.sub(r"^gan_thu_vong\d+_", "", Path(path).stem)
    df = pd.read_excel(path, sheet_name="gan_nhan", dtype=str).fillna("").rename(columns=COT_CU)
    for axis in DON_NHAN:
        df[axis] = [chuan_hoa(v, axis, sua, nguoi, s) for v, s in zip(df[axis], df.stt)]
    emotions = []
    for e1, e2, s in zip(df.emotion_1, df.emotion_2, df.stt):
        parts = [chuan_hoa(x, "emotion", sua, nguoi, s) for x in [e1, *re.split(r"[;,]", e2)] if x.strip()]
        emotions.append(list(dict.fromkeys(parts)))  # giữ thứ tự ưu tiên, bỏ trùng
    df["emotion"] = emotions
    return nguoi, df


def cohen_kappa(a, b):
    labels = sorted(set(a) | set(b))
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[l] * cb[l] for l in labels) / (n * n)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def fleiss_kappa(rows):
    """rows: danh sách nhãn của từng câu (mỗi câu cùng số người gán)."""
    k = len(rows[0])
    cats = sorted({x for r in rows for x in r})
    p_i = [(sum(c * c for c in Counter(r).values()) - k) / (k * (k - 1)) for r in rows]
    p_j = [sum(r.count(c) for r in rows) / (len(rows) * k) for c in cats]
    pe = sum(p * p for p in p_j)
    return 1.0 if pe == 1 else (sum(p_i) / len(rows) - pe) / (1 - pe)


def gop_cam_xuc(lists):
    votes, first = Counter(), Counter()
    for labels in lists:
        votes.update(labels)
        if labels:
            first[labels[0]] += 1
    nguong = 2 if len(lists) >= 2 else 1
    kept = sorted([l for l, v in votes.items() if v >= nguong], key=lambda l: (-votes[l], -first[l], NHAN["emotion"].index(l) if l in NHAN["emotion"] else 99))
    if any(l in EXCLUSIVE for l in kept) and len(kept) > 1:
        return []  # neutral hoặc unk đi cùng nhãn khác là mâu thuẫn, để nhóm phân xử
    return kept


def self_check():
    assert abs(cohen_kappa(list("aabb"), list("aabb")) - 1) < 1e-9
    assert abs(cohen_kappa(list("aaab"), list("abab")) - 0.5) < 1e-9
    assert abs(fleiss_kappa([["a", "a"], ["b", "b"]]) - 1) < 1e-9
    assert gop_cam_xuc([["fear", "sadness"], ["sadness"]]) == ["sadness"]
    assert gop_cam_xuc([["joy"], ["neutral"]]) == []
    assert gop_cam_xuc([["surprise", "joy"], ["surprise", "joy"]]) == ["surprise", "joy"]
    sua = []
    assert chuan_hoa("suprise", "emotion", sua, "x", "1") == "surprise" and sua
    assert chuan_hoa("adminstration", "topic", [], "x", "1") == "administration"


def main():
    self_check()
    out, files = Path(sys.argv[1]), sys.argv[2:]
    assert len(files) >= 2, "Cần ít nhất 2 file gán"
    sua = []
    people = [doc_file(f, sua) for f in files]
    names = [n for n, _ in people]
    base = people[0][1]
    for name, df in people[1:]:
        assert (df.comment_uid.values == base.comment_uid.values).all(), f"Thứ tự câu của {name} khác file đầu tiên"

    rows, stats = [], []
    for i in range(len(base)):
        # Đặt ngữ cảnh trước bình luận theo thứ tự đọc: bài đăng, bình luận cha, rồi bình luận được gán.
        row = {"stt": base.stt[i], "ngu_canh_bai_dang": base.post_text[i],
               "ngu_canh_comment_cha": base.parent_text[i] or "(không có, đây là bình luận gốc)",
               "text_public": base.text_public[i]}
        lech = 0
        for axis in DON_NHAN:
            vals = [df[axis][i] for _, df in people]
            top, cnt = Counter(vals).most_common(1)[0]
            ok = len(set(vals)) == 1
            row.update({f"{axis}_{n}": v for n, v in zip(names, vals)})
            row[f"{axis}_lech"] = "" if ok else "LỆCH"
            row[f"{axis}_chot"] = top if ok or cnt > len(vals) / 2 else ""
            lech += not ok
        emos = [df.emotion[i] for _, df in people]
        kept = gop_cam_xuc(emos)
        same = len({tuple(sorted(e)) for e in emos}) == 1
        row.update({f"emotion_{n}": "; ".join(e) for n, e in zip(names, emos)})
        row["emotion_lech"] = "" if same else ("LỆCH MỘT PHẦN" if kept else "LỆCH")
        row["emotion_1_chot"] = kept[0] if kept else ""
        row["emotion_2_chot"] = "; ".join(kept[1:])
        lech += not same
        row["so_huong_lech"] = lech
        row["hard"] = ", ".join(n for n, (_, df) in zip(names, people) if str(df.hard[i]).strip())
        row["note"] = " | ".join(f"{n}: {df.note[i]}" for n, (_, df) in zip(names, people) if str(df.note[i]).strip())
        row["ghi_chu_hop"] = ""
        row["comment_uid"] = base.comment_uid[i]
        rows.append(row)
    merged = pd.DataFrame(rows)

    # Thống kê đồng thuận từng hướng.
    for axis in DON_NHAN + ["emotion_1"]:
        cols = [[df[axis][i] if axis != "emotion_1" else (df.emotion[i][0] if df.emotion[i] else "") for i in range(len(base))] for _, df in people]
        pairs = {f"κ {a}-{b}": round(cohen_kappa(cols[x], cols[y]), 3) for (x, a), (y, b) in itertools.combinations(enumerate(names), 2)}
        entry = {"huong": axis, "so_cau": len(base), "dong_y_tuyet_doi": f"{sum(len(set(v)) == 1 for v in zip(*cols)) / len(base):.1%}", **pairs}
        if len(names) >= 3:
            entry["Fleiss κ"] = round(fleiss_kappa([list(v) for v in zip(*cols)]), 3)
        for n, c in zip(names, cols):
            entry[f"unk {n}"] = c.count("unk")
        stats.append(entry)
    same_set = sum(len({tuple(sorted(df.emotion[i])) for _, df in people}) == 1 for i in range(len(base)))
    stats.append({"huong": "emotion (cả tập nhãn)", "so_cau": len(base), "dong_y_tuyet_doi": f"{same_set / len(base):.1%}"})
    for label in NHAN["emotion"]:
        cols = [["co" if label in df.emotion[i] else "khong" for i in range(len(base))] for _, df in people]
        pairs = {f"κ {a}-{b}": round(cohen_kappa(cols[x], cols[y]), 3) for (x, a), (y, b) in itertools.combinations(enumerate(names), 2)}
        stats.append({"huong": f"emotion: {label}", "so_cau": len(base),
                      **{f"so_cau_chon {n}": c.count("co") for n, c in zip(names, cols)}, **pairs})
    dist = []
    for axis in DON_NHAN + ["emotion"]:
        for label in NHAN[axis]:
            entry = {"huong": axis, "nhan": label}
            for n, (_, df) in zip(names, people):
                entry[n] = sum(label in e for e in df.emotion) if axis == "emotion" else int((df[axis] == label).sum())
            dist.append(entry)

    write(out, merged, names, pd.DataFrame(stats), pd.DataFrame(dist), pd.DataFrame(sua))
    print(f"{len(merged)} câu, {int((merged.so_huong_lech > 0).sum())} câu có lệch nhãn")
    print(pd.DataFrame(stats).head(5).to_string(index=False))
    print("Đã sửa", len(sua), "lỗi gõ nhãn. Lưu:", out)


def write(out, merged, names, stats, dist, sua):
    wb = Workbook()
    ws = wb.active
    ws.title = "tong_hop"
    cols = list(merged.columns)
    widths = {"text_public": 50, "ngu_canh_bai_dang": 45, "ngu_canh_comment_cha": 35, "note": 30, "ghi_chu_hop": 30, "comment_uid": 18}
    for c, name in enumerate(cols, 1):
        cell = ws.cell(1, c, name)
        cell.font = Font(bold=True)
        cell.alignment = Alignment(wrap_text=True, vertical="center")
        ws.column_dimensions[get_column_letter(c)].width = widths.get(name, 13)
    idx = {name: c for c, name in enumerate(cols, 1)}
    for r, row in enumerate(merged.itertuples(index=False), 2):
        values = row._asdict()
        for c, name in enumerate(cols, 1):
            ws.cell(r, c, values[name]).alignment = Alignment(wrap_text=True, vertical="top")
        if values["so_huong_lech"]:
            for c in range(1, len(cols) + 1):
                ws.cell(r, c).fill = VANG
        for axis in DON_NHAN + ["emotion"]:
            flag = values[f"{axis}_lech"]
            if flag:
                fill = CAM if flag == "LỆCH MỘT PHẦN" else DO
                for n in names:
                    ws.cell(r, idx[f"{axis}_{n}"]).fill = fill
                ws.cell(r, idx[f"{axis}_lech"]).fill = fill
    ws.freeze_panes = "E2"  # giữ ngữ cảnh và bình luận cố định khi cuộn sang các cột nhãn
    ws.auto_filter.ref = f"A1:{get_column_letter(len(cols))}{len(merged) + 1}"

    guide = wb.create_sheet("cach_doc", 0)
    lines = ["Cách đọc file tổng hợp",
             "Cột B, C là ngữ cảnh (bài đăng, bình luận cha), cột D là bình luận được gán. Bốn cột đầu luôn hiện khi cuộn ngang.",
             "Hàng tô vàng: có ít nhất một hướng lệch nhãn. Ô tô đỏ: hai người gán khác nhau. Ô tô cam: cảm xúc lệch một phần.",
             "Cột *_chot: nhãn đã chốt. Trống nghĩa là cần nhóm thảo luận rồi điền.",
             "toxicity, topic, stance: chốt khi mọi người cùng nhãn (có từ 3 người thì lấy nhãn quá nửa).",
             "emotion: giữ cảm xúc có ít nhất 2 người cùng chọn (như GoEmotions). LỆCH MỘT PHẦN: đã có nhãn chung, chỉ khác phần còn lại.",
             "neutral hoặc unk đi cùng nhãn khác bị coi là mâu thuẫn, để trống cho nhóm phân xử.",
             "Ghi lý do chốt vào cột ghi_chu_hop để sửa quy chuẩn sau buổi họp.",
             "Sheet thong_ke: độ đồng thuận. Sheet phan_bo_nhan: số lần mỗi người chọn từng nhãn. Sheet sua_loi_go: nhãn gõ sai đã được sửa."]
    for r, text in enumerate(lines, 1):
        guide.cell(r, 1, text).font = Font(bold=(r == 1))
    guide.column_dimensions["A"].width = 120
    for title, frame in [("thong_ke", stats), ("phan_bo_nhan", dist), ("sua_loi_go", sua)]:
        sheet = wb.create_sheet(title)
        if frame.empty:
            sheet.cell(1, 1, "Không có")
            continue
        for c, name in enumerate(frame.columns, 1):
            sheet.cell(1, c, name).font = Font(bold=True)
            sheet.column_dimensions[get_column_letter(c)].width = 22 if c == 1 else 14
        for r, row in enumerate(frame.itertuples(index=False), 2):
            for c, value in enumerate(row, 1):
                sheet.cell(r, c, None if pd.isna(value) else value)
    wb.active = 1
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)


if __name__ == "__main__":
    main()

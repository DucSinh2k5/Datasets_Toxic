"""Đóng gói những gì cần để gán bằng mô hình mở trên Kaggle (hoặc Colab), không đưa cả masked.csv lên.

Chạy từ thư mục gốc repo:
    python scripts/llm/dong_goi_kaggle.py                 # gói gold (khóa prompt): data/llm/goi_kaggle/goi_kaggle.zip
    python scripts/llm/dong_goi_kaggle.py --nguoi Hao     # gói các đợt của một người (theo data/llm/dot/phan_cong.csv)
    python scripts/llm/dong_goi_kaggle.py --nguoi tat_ca  # mỗi người một gói
Gói đợt (data/llm/goi_kaggle/goi_<người>.zip) có code, bộ prompt đã khóa, data/llm/dot/<các đợt của người đó>.csv,
phan_cong.csv và masked.csv CHỈ gồm các dòng của các đợt đó; không có gold. Gói dừng nếu còn câu khớp mẫu thông tin cá nhân.
Gói gold: data/llm/goi_kaggle/goi_kaggle.zip, giữ nguyên cấu trúc thư mục của repo để script chạy không cần sửa:
    scripts/clean_dataset.py, scripts/danh_sach_dia_danh_truong.csv   (để kiểm tra thông tin cá nhân trước khi gửi)
    scripts/llm/chung.py, gan_nhan_llm.py, danh_gia_llm.py, prompt_ban5.md, prompt_ban5_en.md, prompt_ban5_en_tach/*.md
    data/cleaned/masked.csv            CHỈ các dòng của gold (đủ cột, văn bản đã che)
    data/gan_nhan/vong1/gold_vong1.csv, data/gan_nhan/vong2/gold_vong2.csv   (để chấm; mô hình không thấy nhãn)
Không bao giờ đóng gói data/cleaned/private/. Gói dừng lại nếu còn câu khớp mẫu thông tin cá nhân hoặc có câu tập test.
"""
import argparse
import io
import sys
import zipfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import chung  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")
ROOT = chung.ROOT
OUT = ROOT / "data" / "llm" / "goi_kaggle" / "goi_kaggle.zip"
CODE = ["scripts/clean_dataset.py", "scripts/danh_sach_dia_danh_truong.csv", "scripts/llm/chung.py",
        "scripts/llm/gan_nhan_llm.py", "scripts/llm/danh_gia_llm.py", "scripts/llm/prompt_ban5.md",
        "scripts/llm/prompt_ban5_en.md"] + sorted(p.relative_to(chung.ROOT).as_posix()
                                                    for p in (chung.HERE / "prompt_ban5_en_tach").glob("*.md"))
GOLD = {r: p.relative_to(ROOT).as_posix() for r, p in chung.GOLD.items()}


CODE_DOT = ["scripts/clean_dataset.py", "scripts/danh_sach_dia_danh_truong.csv", "scripts/llm/chung.py",
            "scripts/llm/gan_nhan_llm.py", "scripts/llm/prompt_ban5.md"] + sorted(p.relative_to(chung.ROOT).as_posix()
                                                    for p in (chung.HERE / "prompt_ban5_en_tach").glob("*.md"))
DOT = ROOT / "data" / "llm" / "dot"


def goi_nguoi(ten, masked, pc):
    mine = pc[pc.nguoi == ten]
    if mine.empty:
        raise SystemExit(f"Không có đợt nào của {ten!r} trong phan_cong.csv (có: {', '.join(pc.nguoi.unique())})")
    dots = {d: pd.read_csv(DOT / f"{d}.csv", dtype=str) for d in mine["dot"]}
    uids = set().union(*(set(d.comment_uid) for d in dots.values()))
    sub = masked[masked.comment_uid.isin(uids)]
    if len(sub) != len(uids):
        raise SystemExit(f"{ten}: các đợt có {len(uids)} câu nhưng masked.csv khớp {len(sub)} dòng: masked.csv đã đổi sau khi chia đợt?")
    gold = set(chung.load_gold([1, 2]).comment_uid)
    if uids & gold:
        raise SystemExit(f"{ten}: có {len(uids & gold)} câu gold trong đợt: dừng")
    blocked = [u for u, *t in sub[["comment_uid", "post_text", "parent_text", "text_public"]].itertuples(index=False)
               if chung.con_thong_tin_ca_nhan(*t)]
    if blocked:
        raise SystemExit(f"{ten}: {len(blocked)} câu còn khớp mẫu thông tin cá nhân, không đóng gói: {blocked[:5]}")
    out = OUT.parent / f"goi_{ten}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for rel in CODE_DOT:
            z.write(ROOT / rel, rel)
        z.write(DOT / "phan_cong.csv", "data/llm/dot/phan_cong.csv")
        for d in dots:
            z.write(DOT / f"{d}.csv", f"data/llm/dot/{d}.csv")
        buf = io.StringIO()
        sub.to_csv(buf, index=False)
        z.writestr("data/cleaned/masked.csv", buf.getvalue().encode("utf-8-sig"))
        z.writestr("DOC_TRUOC.txt", (f"Gói gán nhãn NLP_N12 của {ten}: các đợt {', '.join(dots)}. data/cleaned/masked.csv ở đây CHỈ "
                                     f"có {len(sub)} dòng của các đợt này (đã che), không phải toàn bộ dữ liệu. Không chia sẻ ra "
                                     "ngoài nhóm; để dataset Kaggle ở chế độ Private và xóa khi nhóm đã nhận đủ kết quả.\n").encode("utf-8"))
    names = zipfile.ZipFile(out).namelist()
    assert not any("private" in n or "gan_nhan/" in n for n in names), names
    print(f"Đã ghi {out.relative_to(ROOT)} ({out.stat().st_size / 2**20:.1f} MB): {ten}, {len(dots)} đợt "
          f"({', '.join(dots)}), {len(sub):,} dòng masked, 0 câu bị chặn, {int((sub.split == 'test').sum()):,} câu tập test")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--nguoi", help="tên người trong data/llm/dot/phan_cong.csv, hoặc tat_ca; bỏ trống thì đóng gói gold")
    args = ap.parse_args()
    if args.nguoi:
        pc = pd.read_csv(DOT / "phan_cong.csv", dtype=str)
        masked = pd.read_csv(chung.MASKED, dtype=str, keep_default_na=False)
        OUT.parent.mkdir(parents=True, exist_ok=True)
        for ten in (pc.nguoi.unique() if args.nguoi == "tat_ca" else [args.nguoi]):
            goi_nguoi(ten, masked, pc)
        return
    gold = chung.load_gold([1, 2])
    uids = set(gold.comment_uid)
    masked = pd.read_csv(chung.MASKED, dtype=str, keep_default_na=False)
    sub = masked[masked.comment_uid.isin(uids)]
    if len(sub) != len(uids) or len(uids) != len(gold):
        raise SystemExit(f"Gold có {len(gold)} dòng, {len(uids)} comment_uid khác nhau, masked.csv khớp {len(sub)} dòng: kiểm tra lại")
    if (sub.split == "test").any():
        raise SystemExit("Có câu thuộc split test trong gold: dừng")
    blocked = [u for u, *t in sub[["comment_uid", "post_text", "parent_text", "text_public"]].itertuples(index=False)
               if chung.con_thong_tin_ca_nhan(*t)]
    if blocked:
        raise SystemExit(f"{len(blocked)} câu còn khớp mẫu thông tin cá nhân, không đóng gói: {blocked[:5]}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for rel in CODE:
            z.write(ROOT / rel, rel)
        for rel in GOLD.values():
            z.write(ROOT / rel, rel)
        buf = io.StringIO()
        sub.to_csv(buf, index=False)
        z.writestr("data/cleaned/masked.csv", buf.getvalue().encode("utf-8-sig"))
        z.writestr("DOC_TRUOC.txt", "Gói gán thử gold NLP_N12. data/cleaned/masked.csv ở đây CHỈ có "
                   f"{len(sub)} dòng của gold vòng 1 và 2 (đã che), không phải toàn bộ dữ liệu. Không chia sẻ ra ngoài nhóm; "
                   "để dataset Kaggle ở chế độ Private và xóa khi xong.\n".encode("utf-8"))
    names = zipfile.ZipFile(OUT).namelist()
    assert not any("private" in n for n in names), names
    print(f"Đã ghi {OUT.relative_to(ROOT)} ({OUT.stat().st_size / 1024:.0f} KB): {len(sub)} dòng masked, "
          f"{len(gold)} dòng gold, 0 câu bị chặn vì thông tin cá nhân, 0 câu tập test")
    for n in names:
        print("  ", n)


if __name__ == "__main__":
    main()

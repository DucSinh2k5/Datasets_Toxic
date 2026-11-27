"""Chia các dòng cần gán của masked.csv thành các đợt để gán bằng cấu hình LLM đã khóa, và phân công cho từng người chạy.

Chạy từ thư mục gốc repo:
    python scripts/llm/chia_dot.py                # chạy thử: in bảng phân công, không ghi file
    python scripts/llm/chia_dot.py --ghi          # ghi data/llm/dot/
Mặc định 14 đợt (train 10, val 2, test 2), mỗi đợt khoảng 9.500–10.300 câu (khoảng 6 giờ trên Kaggle 2 × T4), 4 người
chạy (Hảo, Sinh, Triệu, Long) theo vòng: người 1 nhận đợt 1, 5, 9, 13; người 2 nhận đợt 2, 6, 10, 14; người 3 nhận 3, 7, 11;
người 4 nhận 4, 8, 12.
- Bỏ 480 câu gold (giữ nhãn người).
- Bỏ các câu còn khớp mẫu thông tin cá nhân (không gửi đi), ghi vào bi_chan.csv để che rồi gán bù sau.
- Mỗi bài đăng nằm trọn trong một đợt; mỗi đợt chỉ có một split. Trong đợt, câu xếp theo bài đăng để máy chủ vLLM dùng lại
  được phần đầu request (prefix caching).
- Chia xếp bài lớn trước vào đợt đang ít câu nhất, nên kết quả cố định với cùng masked.csv.
Ghi ra data/llm/dot/: dot_01.csv ... (cột comment_uid, post_uid, split), phan_cong.csv, bi_chan.csv.
Đã có phan_cong.csv thì dừng (đang gán dở mà chia lại sẽ lệch đợt); muốn chia lại thì xóa thư mục data/llm/dot/ trước.
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import chung  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
DOT = chung.ROOT / "data" / "llm" / "dot"
GIAY_MOI_CAU = 2.21  # Qwen3-14B-AWQ, ban5-en-tach-p3, 2 × T4, 16 luồng (đo trên gold 27/11/2026)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    ap.add_argument("--so-dot", nargs=3, type=int, default=[10, 2, 2], metavar=("TRAIN", "VAL", "TEST"))
    ap.add_argument("--nguoi", nargs="+", default=["Hao", "Sinh", "Trieu", "Long"], help="người chạy, chia đợt theo vòng")
    ap.add_argument("--ghi", action="store_true", help="ghi file (mặc định chỉ in)")
    args = ap.parse_args()
    if args.ghi and (DOT / "phan_cong.csv").exists():
        raise SystemExit(f"Đã có {DOT / 'phan_cong.csv'}: đang dùng bộ đợt này. Muốn chia lại thì xóa thư mục {DOT} trước.")

    m = chung.load_masked(("comment_uid", "post_uid", "post_text", "parent_text", "text_public", "split"))
    gold = set(chung.load_gold([1, 2]).comment_uid)
    m = m[~m.comment_uid.isin(gold)].copy()
    m["thu_tu"] = range(len(m))
    chan = [(u, ", ".join(p)) for u, *t in m[["comment_uid", "post_text", "parent_text", "text_public"]].itertuples(index=False)
            if (p := chung.con_thong_tin_ca_nhan(*t))]
    bi_chan = pd.DataFrame(chan, columns=["comment_uid", "mau_con_lai"])
    m = m[~m.comment_uid.isin(set(bi_chan.comment_uid))]
    print(f"{len(m) + len(bi_chan) + len(gold):,} dòng masked.csv: bỏ {len(gold)} câu gold, {len(bi_chan)} câu còn mẫu thông tin "
          f"cá nhân; cần gán {len(m):,} câu")

    dots = []
    for split, n in zip(["train", "val", "test"], args.so_dot):
        sub = m[m.split == split]
        sizes = sub.groupby("post_uid").size().sort_values(ascending=False, kind="stable")
        bins = [[] for _ in range(n)]
        load = [0] * n
        for post, k in sizes.items():  # bài lớn trước, bỏ vào đợt đang ít câu nhất
            j = min(range(n), key=lambda x: (load[x], x))
            bins[j].append(post)
            load[j] += k
        for posts in bins:
            d = sub[sub.post_uid.isin(set(posts))].sort_values(["post_uid", "thu_tu"])
            dots.append((split, d[["comment_uid", "post_uid", "split"]]))

    rows = []
    for i, (split, d) in enumerate(dots, 1):
        rows.append({"dot": f"dot_{i:02d}", "split": split, "so_cau": len(d), "so_bai_dang": d.post_uid.nunique(),
                     "nguoi": args.nguoi[(i - 1) % len(args.nguoi)], "uoc_gio": round(len(d) * GIAY_MOI_CAU / 3600, 1)})
    pc = pd.DataFrame(rows)
    assert pc.so_cau.sum() == len(m) and len(set().union(*(set(d.comment_uid) for _, d in dots))) == len(m)
    print(pc.to_string(index=False))
    print("\nMỗi người:")
    print(pc.groupby("nguoi", sort=False).agg(so_dot=("dot", "count"), dot=("dot", ", ".join), so_cau=("so_cau", "sum"),
                                               uoc_gio=("uoc_gio", "sum")).to_string())
    print("Kaggle cho 30 giờ GPU mỗi tuần mỗi tài khoản; mỗi phiên tối đa 12 giờ.")
    if not args.ghi:
        print("\nChạy thử, chưa ghi file. Thêm --ghi để ghi data/llm/dot/.")
        return
    DOT.mkdir(parents=True, exist_ok=True)
    for (split, d), r in zip(dots, rows):
        d.to_csv(DOT / f"{r['dot']}.csv", index=False)
    pc.to_csv(DOT / "phan_cong.csv", index=False)
    bi_chan.to_csv(DOT / "bi_chan.csv", index=False)
    print(f"\nĐã ghi {len(dots)} file đợt, phan_cong.csv, bi_chan.csv ({len(bi_chan)} câu) vào {DOT}")


if __name__ == "__main__":
    main()

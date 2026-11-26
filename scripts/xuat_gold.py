"""Xuất gold của một vòng gán thử từ file chốt (sheet tong_hop của tong_hop_gan_thu.py).

Chạy (từ thư mục gốc repo):
    python scripts/xuat_gold.py <vòng> <file_chốt.xlsx> [nguoi_chot]
Ví dụ:
    python scripts/xuat_gold.py 2 data/gan_nhan/vong2/tong_hop_vong2_Hao_Long.xlsx Trieu

Kết quả: data/gan_nhan/vong<N>/gold_vong<N>.csv, cùng cấu trúc với gold_vong1.csv.
Nếu file gold đã có thì sao lưu thành gold_vong<N>_ban_cu.csv trước khi ghi.

Cột *_cach_chot:
- dong_y: mọi người gán cùng nhãn và nhãn được giữ;
- phan_xu: người gán lệch nhau, người chốt chọn nhãn;
- ra_soat_claude: nhãn đổi theo rà soát của Claude (ô có trong sheet da_ap_dung của file chốt).
"""
import re
import shutil
import sys
from pathlib import Path

import pandas as pd

NHAN = {
    "toxicity": ["clean", "profane", "attack", "unk"],
    "topic": ["academics", "facilities", "administration", "student_life", "unk"],
    "stance": ["support", "oppose", "suggest", "none", "unk"],
    "emotion": ["joy", "sadness", "anger", "fear", "surprise", "neutral", "unk"],
}
DATA = Path(__file__).resolve().parents[1] / "data" / "gan_nhan"


def tach(s):
    return [x.strip() for x in re.split(r"[;,]", str(s)) if x.strip()]


def main():
    vong, chot = int(sys.argv[1]), Path(sys.argv[2])
    nguoi_chot = sys.argv[3] if len(sys.argv) > 3 else ""
    out_dir = DATA / f"vong{vong}"
    t = pd.read_excel(chot, sheet_name="tong_hop", dtype=str).fillna("")
    t = t[t.comment_uid.str.strip() != ""]  # bỏ dòng trống do Excel định dạng thừa
    sheets = pd.ExcelFile(chot).sheet_names
    da_ap_dung = pd.read_excel(chot, sheet_name="da_ap_dung", dtype=str) if "da_ap_dung" in sheets else pd.DataFrame(columns=["comment_uid", "huong"])
    claude = set(zip(da_ap_dung.comment_uid, da_ap_dung.huong))
    nguoi = [c[len("toxicity_"):] for c in t.columns if c.startswith("toxicity_") and c not in ("toxicity_lech", "toxicity_chot")]
    nguon = pd.read_csv(out_dir / f"tong_hop_vong{vong}.csv", dtype=str)[["comment_uid", "post_uid", "nguon_mau"]]

    loi, rows = [], []
    for _, r in t.iterrows():
        g = {"comment_uid": r.comment_uid, "text_public": r.text_public}
        trong = []
        for h in ["toxicity", "topic", "stance"]:
            v = r[f"{h}_chot"].strip()
            if not v:
                trong.append(h)
            elif v not in NHAN[h]:
                loi.append(f"stt {r.get('stt', '?')}: {h} = {v!r}")
            g[h] = v
        e = tach(r.emotion_1_chot) + tach(r.emotion_2_chot)
        if not e:
            trong.append("emotion_1")
        for x in e:
            if x not in NHAN["emotion"]:
                loi.append(f"stt {r.get('stt', '?')}: emotion = {x!r}")
        if len(e) > 1 and set(e) & {"neutral", "unk"}:
            loi.append(f"stt {r.get('stt', '?')}: neutral/unk đi cùng cảm xúc khác {e}")
        g["emotion_1"] = e[0] if e else ""
        g["emotion_2"] = "; ".join(dict.fromkeys(e[1:]))
        for h, cot in [("toxicity", "toxicity"), ("topic", "topic"), ("stance", "stance"), ("emotion_1", "emotion")]:
            if (r.comment_uid, h) in claude:
                cach = "ra_soat_claude"
            else:
                gan = [tach(r[f"emotion_{n}"])[:1] for n in nguoi] if h == "emotion_1" else [[r[f"{h}_{n}"].strip()] for n in nguoi]
                cach = "dong_y" if all(x == [g[h]] for x in gan) else "phan_xu"
            g[f"{cot}_cach_chot"] = cach
        g["con_trong"] = ";".join(trong)
        rows.append(g)
    gold = pd.DataFrame(rows).merge(nguon, on="comment_uid", how="left")
    gold["vong"], gold["nguoi_gan"] = str(vong), ";".join(nguoi)
    gold = gold[["comment_uid", "text_public", "toxicity", "topic", "stance", "emotion_1", "emotion_2",
                 "toxicity_cach_chot", "topic_cach_chot", "stance_cach_chot", "emotion_cach_chot",
                 "post_uid", "nguon_mau", "vong", "nguoi_gan", "con_trong"]]

    vi_pham = gold[(gold.topic == "unk") & ~gold.stance.isin(["none", "unk"])]
    thieu_nguon = list(gold.comment_uid[gold.post_uid.isna()])
    if loi or not vi_pham.empty or thieu_nguon:
        print("Không xuất vì còn lỗi:", *loi, f"vi phạm ràng buộc: {list(vi_pham.comment_uid)}",
              f"không có trong tong_hop_vong{vong}.csv: {thieu_nguon[:10]}", sep="\n  ")
        sys.exit(1)

    out = out_dir / f"gold_vong{vong}.csv"
    if out.exists():
        shutil.copy2(out, out_dir / f"gold_vong{vong}_ban_cu.csv")
    gold.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"Đã ghi {out}: {len(gold)} câu, ô trống {int((gold.con_trong != '').sum())}, người chốt {nguoi_chot or '(không ghi)'}")
    for c in ["toxicity", "topic", "stance", "emotion_1"]:
        print(f"  {c}: {gold[c].value_counts().to_dict()}")
    for c in [c for c in gold.columns if c.endswith("_cach_chot")]:
        print(f"  {c}: {gold[c].value_counts().to_dict()}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()

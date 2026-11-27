"""Theo dõi tiến độ các đợt gán, ghép kết quả thành một file nhãn cho toàn bộ dataset, tạo đợt bù cho câu thiếu hoặc lỗi.

Chạy từ thư mục gốc repo, sau khi giải nén các ket_qua_dot_XX.zip vào thư mục gốc repo (file vào data/llm/ket_qua/):
    python scripts/llm/ghep_ket_qua.py              # bảng tiến độ từng đợt và từng người
    python scripts/llm/ghep_ket_qua.py --dot-bu --nguoi-bu Trieu   # ghi data/llm/dot/dot_bu.csv (câu thiếu hoặc lỗi) và
                                                    # thêm dòng dot_bu vào phan_cong.csv; rồi đóng gói lại cho người đó
    python scripts/llm/ghep_ket_qua.py --ghi        # ghi data/llm/nhan_toan_bo.csv (dừng nếu còn câu chưa có nhãn,
                                                    # thêm --cho-thieu để vẫn ghi, câu thiếu có nguon_nhan = chua_gan)
Chỉ nhận kết quả đúng cấu hình đã khóa (prompt KHOA_SHA, mô hình KHOA_MODEL); kết quả khác cấu hình bị bỏ và báo ra.
480 câu gold lấy nhãn người (nguon_nhan = gold_vong1 / gold_vong2). Mỗi dòng ghi nguồn gốc nhãn: đợt, mô hình, phiên bản và
mã băm prompt, các lần hỏi lại hay hạ nhãn (da_sua), bằng chứng toxicity, lý do của mô hình.
"""
import argparse
import glob
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import chung  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
DOT = chung.ROOT / "data" / "llm" / "dot"
KHOA_VERSION, KHOA_SHA, KHOA_MODEL = "ban5-en-tach-p3", "e4cc4216433b", "qwen3-14b"
MAU_KQ = f"vllm_{KHOA_MODEL}_mac-dinh_{KHOA_VERSION}_dot_*.jsonl"
NHAN = ["toxicity", "topic", "stance", "emotion_1", "emotion_2"]
COT_LLM = ["hard", "bang_chung", "da_sua", "vi_pham", "ly_do"]


def doc_ket_qua():
    """{comment_uid: bản ghi}, ưu tiên bản ghi không lỗi mới nhất; và số dòng bị bỏ vì khác cấu hình."""
    best, sai = {}, 0
    files = sorted(glob.glob(str(chung.KET_QUA / MAU_KQ)))
    for f in files:
        dot = Path(f).stem.split("_mac-dinh_")[1].split("_", 1)[1]
        for line in open(f, encoding="utf-8"):
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("prompt_sha") != KHOA_SHA or (r.get("model_tra_loi") and r["model_tra_loi"] != KHOA_MODEL):
                sai += 1
                continue
            r["dot"] = dot
            cu = best.get(r["comment_uid"])
            if cu is None or r["loi"] == "" or cu["loi"] != "":
                best[r["comment_uid"]] = r
    return best, sai, files


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    ap.add_argument("--ghi", action="store_true")
    ap.add_argument("--cho-thieu", action="store_true", help="với --ghi: vẫn ghi khi còn câu chưa có nhãn")
    ap.add_argument("--dot-bu", action="store_true")
    ap.add_argument("--nguoi-bu", default="Trieu", help="người chạy đợt bù (ghi vào phan_cong.csv)")
    args = ap.parse_args()

    pc = pd.read_csv(DOT / "phan_cong.csv", dtype=str)
    best, sai, files = doc_ket_qua()
    print(f"{len(files)} file kết quả trong {chung.KET_QUA}; {sai} dòng bị bỏ vì khác cấu hình đã khóa")
    rows, thieu = [], []
    for d in pc[pc["dot"] != "dot_bu"].itertuples():
        uids = pd.read_csv(DOT / f"{d.dot}.csv", dtype=str).comment_uid
        ok = sum(1 for u in uids if u in best and best[u]["loi"] == "")
        loi = sum(1 for u in uids if u in best and best[u]["loi"] != "")
        thieu += [u for u in uids if u not in best or best[u]["loi"] != ""]
        tt = "xong" if ok == len(uids) else ("chưa chạy" if ok + loi == 0 else "dở")
        rows.append({"dot": d.dot, "split": d.split, "nguoi": d.nguoi, "so_cau": len(uids), "co_nhan": ok, "loi": loi,
                     "chua_co": len(uids) - ok - loi, "trang_thai": tt})
    if (DOT / "dot_bu.csv").exists():
        bu = pd.read_csv(DOT / "dot_bu.csv", dtype=str).comment_uid
        ok = sum(1 for u in bu if u in best and best[u]["loi"] == "")
        nguoi_bu = ", ".join(pc[pc["dot"] == "dot_bu"].nguoi) or "?"
        rows.append({"dot": "dot_bu", "split": "trộn", "nguoi": nguoi_bu, "so_cau": len(bu), "co_nhan": ok, "loi": len(bu) - ok,
                     "chua_co": 0, "trang_thai": "xong" if ok == len(bu) else "dở"})
        thieu = [u for u in thieu if not (u in best and best[u]["loi"] == "")]
    tien_do = pd.DataFrame(rows)
    print(tien_do.to_string(index=False))
    print("\nTheo người:")
    print(tien_do[tien_do["dot"] != "dot_bu"].groupby("nguoi", sort=False)
          .agg(so_dot=("dot", "count"), xong=("trang_thai", lambda s: int((s == "xong").sum())), so_cau=("so_cau", "sum"),
               co_nhan=("co_nhan", "sum")).to_string())
    bi_chan = pd.read_csv(DOT / "bi_chan.csv", dtype=str) if (DOT / "bi_chan.csv").exists() else pd.DataFrame(columns=["comment_uid"])
    print(f"\nCâu thiếu hoặc lỗi: {len(thieu):,}; câu không gửi vì còn mẫu thông tin cá nhân (bi_chan.csv): {len(bi_chan)}")

    if args.dot_bu:
        if not thieu:
            print("Không có câu nào cần chạy bù.")
        else:
            m = chung.load_masked(("comment_uid", "post_uid", "split"))
            bu = m[m.comment_uid.isin(set(thieu))][["comment_uid", "post_uid", "split"]].sort_values("post_uid", kind="stable")
            bu.to_csv(DOT / "dot_bu.csv", index=False)
            pc = pd.concat([pc[pc["dot"] != "dot_bu"], pd.DataFrame([{
                "dot": "dot_bu", "split": "trộn", "so_cau": len(bu), "so_bai_dang": bu.post_uid.nunique(), "nguoi": args.nguoi_bu,
                "uoc_gio": round(len(bu) * 2.21 / 3600, 1)}])], ignore_index=True)
            pc.to_csv(DOT / "phan_cong.csv", index=False)
            print(f"Đã ghi {DOT / 'dot_bu.csv'} ({len(bu)} câu, {int((bu.split == 'test').sum())} câu test) và dòng dot_bu "
                  f"(người chạy {args.nguoi_bu}) trong phan_cong.csv. Tiếp: python scripts/llm/dong_goi_kaggle.py --nguoi "
                  f"{args.nguoi_bu}, tải gói mới lên dataset Kaggle của người đó (New Version), chạy notebook với DOT = \"dot_bu\".")

    if args.ghi:
        if thieu and not args.cho_thieu:
            raise SystemExit(f"Còn {len(thieu):,} câu chưa có nhãn: chạy bù trước, hoặc thêm --cho-thieu")
        m = chung.load_masked(("comment_uid", "post_uid", "split"))
        gold = chung.load_gold([1, 2]).set_index("comment_uid")
        out = []
        for u, post, split in m[["comment_uid", "post_uid", "split"]].itertuples(index=False):
            rec = {"comment_uid": u, "post_uid": post, "split": split}
            if u in gold.index:
                rec |= {h: gold.at[u, h] for h in NHAN} | {"nguon_nhan": f"gold_vong{gold.at[u, 'vong']}"}
            elif u in best and best[u]["loi"] == "":
                r = best[u]
                rec |= {h: r[h] for h in NHAN} | {"nguon_nhan": "llm", "dot": r["dot"], "model": r["model_tra_loi"],
                                                    "prompt_version": r["prompt_version"], "prompt_sha": r["prompt_sha"]}
                rec |= {k: r.get(k, "") for k in COT_LLM}
            else:
                rec |= {"nguon_nhan": "chua_gan_bi_chan" if u in set(bi_chan.comment_uid) else "chua_gan"}
            out.append(rec)
        df = pd.DataFrame(out)
        vp = df[(df.topic == "unk") & ~df.stance.isin(["none", "unk"]) & df.stance.notna()]
        path = chung.ROOT / "data" / "llm" / "nhan_toan_bo.csv"
        df.to_csv(path, index=False)
        print(f"\nĐã ghi {path}: {len(df):,} dòng; nguồn nhãn {df.nguon_nhan.value_counts().to_dict()}; "
              f"{len(vp)} dòng vi phạm ràng buộc topic = unk")
        co = df[df.toxicity.notna()]
        for h in ["toxicity", "topic", "stance", "emotion_1"]:
            print(f"\n{h} (tỷ lệ theo split):")
            print(pd.crosstab(co[h], co.split, normalize="columns").round(3).to_string())


if __name__ == "__main__":
    main()

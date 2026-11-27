"""Chấm kết quả gán nhãn bằng LLM so với gold: Cohen κ, macro-F1, F1 từng nhãn, κ giữa các LLM.

Chạy từ thư mục gốc repo:
  python scripts/llm/danh_gia_llm.py --gold 2 --kq data/llm/ket_qua/claude_..._gold2.jsonl data/llm/ket_qua/openai_..._gold2.jsonl
  python scripts/llm/danh_gia_llm.py --gold 1 --kq data/llm/ket_qua/*_gold1.jsonl --ra data/llm/danh_gia_gold1.xlsx
Báo riêng phần ô gold có cách chốt dong_y (hai người cùng gán, không qua Claude) để thấy thiên lệch về Claude.
Sheet cau_lech (câu LLM khác gold, kèm lý do của LLM) chỉ có câu gold vòng 2: vòng 1 dùng để kiểm tra, không dùng để
chỉnh prompt (TIEN_TRINH_DATASET.md, giai đoạn 4).
Chấm nhiều vòng thì báo thêm κ riêng từng vòng (*_kappa_vong1, *_kappa_vong2).
--bo-trung-prompt <file hoặc thư mục prompt>: báo thêm κ khi bỏ các câu gold có văn bản trùng một ví dụ trích trong prompt
(*_kappa_bo_trung), vì mô hình đã thấy các câu đó; cột trong_prompt ở sheet cau_lech đánh dấu các câu này.
"""
import argparse
import itertools
import json
import re
import sys
from pathlib import Path

import pandas as pd
from sklearn.metrics import cohen_kappa_score, f1_score, precision_recall_fscore_support

sys.path.insert(0, str(Path(__file__).parent))
import chung  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")
MUC_TIEU = {"toxicity": 0.67, "topic": 0.67, "stance": 0.5, "emotion_1": 0.5}
CACH_CHOT = {"toxicity": "toxicity_cach_chot", "topic": "topic_cach_chot", "stance": "stance_cach_chot", "emotion_1": "emotion_cach_chot"}


def load_result(path):
    last = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            last[r["comment_uid"]] = r  # dòng sau (chạy lại) ghi đè dòng trước
    df = pd.DataFrame(last.values())
    meta = df.iloc[0]
    name = f"{meta.nha_cung_cap}:{meta.model_yeu_cau}:{meta.effort or '-'}:{meta.prompt_version}"
    return name, df


def norm(s):
    return re.sub(r"\s+", " ", str(s)).strip().lower()


def cau_trong_prompt(path, gold):
    """comment_uid của các câu gold có văn bản trùng (hoặc chứa) một đoạn trích trong ngoặc kép của prompt."""
    path = Path(path)
    text = "\n".join(chung.load_prompt_tach(path)[0].values()) if path.is_dir() else chung.load_prompt(path)[0]
    quotes = [norm(q) for q in set(re.findall(r'"([^"]{6,})"', text))]
    return {u for u, t in zip(gold.index, gold.text_public)
            if any(q == norm(t) or (len(q) > 12 and q in norm(t)) for q in quotes)}


def emotion_set(e1, e2):
    return {e1} | {x.strip() for x in str(e2 or "").split(";") if x.strip()}


def fleiss_kappa(table):
    """table: DataFrame câu × người gán, giá trị là nhãn."""
    labels = sorted(set(table.values.ravel()))
    n = table.shape[1]
    counts = pd.DataFrame({l: (table == l).sum(axis=1) for l in labels})
    p_i = ((counts ** 2).sum(axis=1) - n) / (n * (n - 1))
    p_j = counts.sum() / counts.values.sum()
    pe = (p_j ** 2).sum()
    return (p_i.mean() - pe) / (1 - pe) if pe < 1 else float("nan")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--gold", type=int, nargs="+", choices=[1, 2], required=True)
    ap.add_argument("--kq", nargs="+", required=True, help="các file .jsonl của gan_nhan_llm.py")
    ap.add_argument("--ra", help="file Excel báo cáo (mặc định data/llm/danh_gia_gold<vòng>.xlsx)")
    ap.add_argument("--bo-trung-prompt", help="file hoặc thư mục prompt: báo thêm κ khi bỏ câu gold trùng ví dụ trong prompt")
    args = ap.parse_args()

    gold = chung.load_gold(args.gold).set_index("comment_uid")
    trung = cau_trong_prompt(args.bo_trung_prompt, gold) if args.bo_trung_prompt else set()
    if args.bo_trung_prompt:
        print(f"Câu gold trùng ví dụ trong prompt: {len(trung)} "
              f"({', '.join(f'vòng {v}: {n}' for v, n in gold.loc[sorted(trung), 'vong'].value_counts().sort_index().items())})")
    masked = chung.load_masked(("comment_uid", "post_text", "parent_text")).set_index("comment_uid")
    results = dict(load_result(p) for p in args.kq)
    tong, theo_nhan, nham_lan, lech = [], [], {}, []
    preds = {}
    for name, df in results.items():
        df = df.set_index("comment_uid")
        ok = df[df.loi == ""]
        common = gold.index.intersection(ok.index)
        g, p = gold.loc[common], ok.loc[common]
        preds[name] = p
        base = {"llm": name, "so_cau_gold": len(gold), "co_ket_qua": len(common), "loi_hoac_thieu": len(gold) - len(common),
                "vi_pham": int((p.vi_pham != "").sum()), "hard": int(p.hard.astype(bool).sum()),
                "model_tra_loi": ", ".join(sorted(set(p.model_tra_loi.dropna()))),
                "chi_phi_usd": round(df.chi_phi_usd.fillna(0).sum(), 4)}
        for h, labels in chung.HUONG.items():
            y, yhat = g[h], p[h]
            dong_y = g[CACH_CHOT[h]] == "dong_y"
            k = cohen_kappa_score(y, yhat)
            base |= {f"{h}_kappa": round(k, 3), f"{h}_macro_f1": round(f1_score(y, yhat, average="macro", labels=labels, zero_division=0), 3),
                     f"{h}_dat_muc_tieu": "đạt" if k >= MUC_TIEU[h] else "chưa",
                     f"{h}_kappa_dong_y": round(cohen_kappa_score(y[dong_y], yhat[dong_y]), 3) if dong_y.sum() > 1 else None,
                     f"{h}_so_o_dong_y": int(dong_y.sum())}
            if len(args.gold) > 1:
                for r in map(str, args.gold):
                    m = g.vong == r
                    base[f"{h}_kappa_vong{r}"] = round(cohen_kappa_score(y[m], yhat[m]), 3)
                    if trung:
                        m &= ~g.index.isin(trung)
                        base[f"{h}_kappa_vong{r}_bo_trung"] = round(cohen_kappa_score(y[m], yhat[m]), 3)
            if trung:
                m = ~g.index.isin(trung)
                base[f"{h}_kappa_bo_trung"] = round(cohen_kappa_score(y[m], yhat[m]), 3)
                base["so_cau_bo_trung"] = int(m.sum())
            prec, rec, f1, sup = precision_recall_fscore_support(y, yhat, labels=labels, zero_division=0)
            for l, a, b, c, s in zip(labels, prec, rec, f1, sup):
                theo_nhan.append({"llm": name, "huong": h, "nhan": l, "so_cau_gold": int(s), "so_cau_llm": int((yhat == l).sum()),
                                  "precision": round(a, 3), "recall": round(b, 3), "f1": round(c, 3)})
            nham_lan[(name, h)] = pd.crosstab(y.rename("gold"), yhat.rename("llm")).reindex(index=labels, columns=labels, fill_value=0)
        # Emotion đa nhãn: κ và F1 cho từng cảm xúc có mặt hay không
        gs = [emotion_set(a, b) for a, b in zip(g.emotion_1, g.emotion_2)]
        ps = [emotion_set(a, b) for a, b in zip(p.emotion_1, p.emotion_2)]
        base["emotion_jaccard_tb"] = round(sum(len(a & b) / len(a | b) for a, b in zip(gs, ps)) / max(len(gs), 1), 3)
        for e in chung.EMOTION[:-1]:
            ye, pe = [e in s for s in gs], [e in s for s in ps]
            kappa = cohen_kappa_score(ye, pe) if len(set(ye) | set(pe)) > 1 else float("nan")
            theo_nhan.append({"llm": name, "huong": "emotion_da_nhan", "nhan": e, "so_cau_gold": sum(ye), "so_cau_llm": sum(pe),
                              "kappa": round(kappa, 3), "f1": round(f1_score(ye, pe, zero_division=0), 3)})
        tong.append(base)
        for uid in common:
            if gold.at[uid, "vong"] != "2":
                continue
            diff = [h for h in chung.HUONG if g.at[uid, h] != p.at[uid, h]]
            if emotion_set(g.at[uid, "emotion_1"], g.at[uid, "emotion_2"]) != emotion_set(p.at[uid, "emotion_1"], p.at[uid, "emotion_2"]):
                diff.append("emotion_2") if "emotion_1" not in diff else None
            if diff:
                lech.append({"llm": name, "comment_uid": uid, "huong_lech": ", ".join(diff),
                             "post_text": masked.at[uid, "post_text"][:300], "parent_text": masked.at[uid, "parent_text"][:300],
                             "text_public": g.at[uid, "text_public"],
                             **{f"gold_{h}": g.at[uid, h] for h in ["toxicity", "topic", "stance", "emotion_1", "emotion_2"]},
                             **{f"llm_{h}": p.at[uid, h] for h in ["toxicity", "topic", "stance", "emotion_1", "emotion_2"]},
                             "cach_chot_gold": "; ".join(f"{h}:{g.at[uid, CACH_CHOT[h]]}" for h in diff if h in CACH_CHOT),
                             "hard": p.at[uid, "hard"], "trong_prompt": uid in trung, "ly_do_llm": p.at[uid, "ly_do"]})

    giua = []
    names = list(preds)
    for a, b in itertools.combinations(names, 2):
        common = preds[a].index.intersection(preds[b].index)
        giua.append({"cap": f"{a} | {b}", "so_cau": len(common),
                     **{f"{h}_kappa": round(cohen_kappa_score(preds[a].loc[common, h], preds[b].loc[common, h]), 3) for h in chung.HUONG}})
    if len(names) >= 3:
        common = set.intersection(*(set(preds[n].index) for n in names))
        common = sorted(common)
        giua.append({"cap": "Fleiss κ (tất cả LLM)", "so_cau": len(common),
                     **{f"{h}_kappa": round(fleiss_kappa(pd.DataFrame({n: preds[n].loc[common, h] for n in names})), 3) for h in chung.HUONG}})

    out = Path(args.ra) if args.ra else chung.ROOT / "data" / "llm" / f"danh_gia_gold{''.join(map(str, args.gold))}.xlsx"
    out.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(out) as w:
        pd.DataFrame({"ghi_chu": [
            f"Gold vòng {', '.join(map(str, args.gold))}: {len(gold)} câu. Mục tiêu κ: toxicity, topic ≥ 0,67; stance, emotion ≥ 0,5.",
            "Cột *_kappa_dong_y chỉ tính trên ô gold mà hai người cùng gán (cách chốt dong_y), không qua Claude chốt.",
            "Sheet cau_lech chỉ có câu gold vòng 2. Gold vòng 1 chỉ dùng để kiểm tra, không chỉnh prompt theo các câu đó.",
            "Cột *_kappa_vong<r>: κ riêng từng vòng. Cột *_bo_trung: bỏ các câu gold trùng ví dụ trong prompt "
            f"({len(trung)} câu; cột trong_prompt ở sheet cau_lech)." if trung else "Không bỏ câu trùng ví dụ trong prompt (--bo-trung-prompt).",
        ]}).to_excel(w, sheet_name="cach_doc", index=False)
        pd.DataFrame(tong).T.to_excel(w, sheet_name="tong_hop", header=False)
        pd.DataFrame(theo_nhan).to_excel(w, sheet_name="theo_nhan", index=False)
        if giua:
            pd.DataFrame(giua).to_excel(w, sheet_name="giua_cac_llm", index=False)
        row = 0
        for (name, h), tab in nham_lan.items():
            pd.DataFrame([[f"{name} · {h} (hàng: gold, cột: LLM)"]]).to_excel(w, sheet_name="nham_lan", startrow=row, index=False, header=False)
            tab.to_excel(w, sheet_name="nham_lan", startrow=row + 1)
            row += len(tab) + 4
        pd.DataFrame(lech).to_excel(w, sheet_name="cau_lech", index=False)
    for b in tong:
        print(f"\n{b['llm']}: {b['co_ket_qua']}/{b['so_cau_gold']} câu, chi phí ${b['chi_phi_usd']}")
        for h in chung.HUONG:
            print(f"  {h:10s} κ = {b[f'{h}_kappa']:.3f} ({b[f'{h}_dat_muc_tieu']}, mục tiêu {MUC_TIEU[h]})  macro-F1 = {b[f'{h}_macro_f1']:.3f}"
                  f"  κ trên ô dong_y = {b[f'{h}_kappa_dong_y']} ({b[f'{h}_so_o_dong_y']} ô)")
            extra = [f"vòng {r} {b[f'{h}_kappa_vong{r}']}" + (f" (bỏ trùng {b[f'{h}_kappa_vong{r}_bo_trung']})" if trung else "")
                     for r in args.gold if f"{h}_kappa_vong{r}" in b]
            if trung:
                extra.append(f"tất cả bỏ trùng {b[f'{h}_kappa_bo_trung']}")
            if extra:
                print(f"  {'':10s} " + "; ".join(extra))
        print(f"  emotion đa nhãn: Jaccard trung bình {b['emotion_jaccard_tb']}")
    for r in giua:
        print(f"\n{r['cap']} ({r['so_cau']} câu): " + ", ".join(f"{h} {r[f'{h}_kappa']}" for h in chung.HUONG))
    print("\nBáo cáo:", out)


if __name__ == "__main__":
    main()

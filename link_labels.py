"""Nối nhãn từ final_dataset_relaxed_fixed.csv sang master_da_loc.xlsx, ghi ra file mới.

Mức khớp (label_source): exact > comment > no_tag > no_tag_multi; conflict = nhãn mâu thuẫn, để trống.
"""
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "master_da_loc_labeled.xlsx"
FINAL = ROOT / "title_comment_label.csv"
BINARY = ROOT / "title_comment_label_binary.csv"


def norm(s):
    s = unicodedata.normalize("NFC", "" if pd.isna(s) else str(s))
    s = re.sub("[​-‏⁠﻿\xa0]", " ", s)
    return re.sub(r"\s+", " ", s).strip().lower()


def key(s):
    """Bỏ tag <person>/<user>, dấu câu, emoji: file nhãn đã xóa tag khỏi nhiều bình luận."""
    return re.sub(r"[\W_]+", "", re.sub(r"<\w+>", "", norm(s)))


def title_ok(fr_title, master_titles):
    return any(fr_title in t or t[:30] in fr_title for t in master_titles if t)


def candidates(row, by_key, title_keys):
    """Dòng master có cùng bình luận (bỏ tag) và tiêu đề tương thích."""
    rows = by_key.get(row.ck, [])
    if not row.ck:
        return []
    if row.tk:
        return [i for i in rows if title_ok(row.tk[:30], title_keys[i])]
    # Không có tiêu đề để đối chiếu: chỉ nhận bình luận đủ dài và duy nhất
    return rows if len(rows) == 1 and len(row.ck) >= 15 else []


def main():
    fr = pd.read_csv(ROOT / "final_dataset_relaxed_fixed.csv")
    ml = pd.read_excel(ROOT / "master_da_loc.xlsx", dtype={"post_id": str})
    pq = pd.read_parquet(ROOT / "master_combined.parquet", columns=["input_text", "cleaned_comment"])
    # input_text chỉ có trong parquet; hai file phải cùng thứ tự dòng mới dùng chung được
    assert (ml.cleaned_comment.astype(str) == pq.cleaned_comment.astype(str)).all()

    parts = fr.input_text.astype(str).str.split("</s>", n=1, expand=True)
    fr["t"], fr["c"], fr["n"] = parts[0].map(norm), parts[1].map(norm), fr.input_text.map(norm)
    fr["tk"], fr["ck"] = fr.t.map(key), fr.c.map(key)

    input_title = pq.input_text.str.split("</s>", n=1).str[0]
    title_keys = [(key(a), key(b)) for a, b in zip(ml.cleaned_title, input_title)]
    full = pq.input_text.map(norm).tolist()
    comment = ml.cleaned_comment.map(norm).tolist()
    by_full, by_comment, by_key = defaultdict(list), defaultdict(list), defaultdict(list)
    for i in range(len(ml)):
        by_full[full[i]].append(i)
        by_comment[comment[i]].append(i)
        by_key[key(comment[i])].append(i)

    # Tự kiểm tra: mức no_tag phải tìm lại đúng dòng trên các cặp đã khớp tuyệt đối
    exact = fr[fr.n.isin(by_full)]
    found = [by_full[r.n][0] in candidates(r, by_key, title_keys) for r in exact.itertuples()]
    print(f"Tự kiểm tra no_tag: tìm lại đúng {sum(found)}/{len(found)} = {sum(found)/len(found):.4f}")
    assert sum(found) / len(found) > 0.98

    TIERS = ["exact", "comment", "no_tag", "no_tag_multi"]
    votes = defaultdict(lambda: defaultdict(set))
    unmatched = []
    for r in fr.itertuples():
        if r.n in by_full:
            hits = {"exact": by_full[r.n]}
        else:
            comment_hits = [i for i in by_comment.get(r.c, []) if r.c and (not r.tk or title_ok(r.tk[:30], title_keys[i]))]
            if comment_hits:
                hits = {"comment": comment_hits}
            else:
                cands = candidates(r, by_key, title_keys)
                hits = {"no_tag" if len(cands) == 1 else "no_tag_multi": cands} if cands else {}
        if not hits:
            unmatched.append(r.Index)
        for tier, idx in hits.items():
            for i in idx:
                votes[i][tier].add(r.label)

    labels, sources = [None] * len(ml), [None] * len(ml)
    for i, by_tier in votes.items():
        best = next(t for t in TIERS if t in by_tier)  # mức khớp tốt nhất thắng
        if len(by_tier[best]) == 1:
            labels[i], sources[i] = next(iter(by_tier[best])), best
        else:
            sources[i] = "conflict"

    out = ml.copy()
    out["label"] = pd.Series(labels, dtype="Int64")
    out["label_source"] = sources
    rest = fr.loc[unmatched, ["input_text", "label"]]

    with pd.ExcelWriter(OUT, engine="openpyxl") as w:
        out.to_excel(w, sheet_name="labeled", index=False)
        rest.to_excel(w, sheet_name="khong_noi_duoc", index=False)
        for ws in w.book.worksheets:  # giữ "=))" là văn bản, nếu không Excel coi là công thức
            for row in ws.iter_rows(min_row=2):
                for c in row:
                    if isinstance(c.value, str) and c.value.startswith("="):
                        c.data_type = "s"

    back = pd.read_excel(OUT, sheet_name="labeled", dtype={"post_id": str})
    assert len(back) == len(ml)
    assert back.cleaned_comment.astype(str).equals(ml.cleaned_comment.astype(str))
    assert back.post_id.astype(str).equals(ml.post_id.astype(str))
    assert back.label.notna().sum() == out.label.notna().sum()

    # File 3 cột: dòng đã nối lấy văn bản từ parquet; dòng không nối được lấy từ chính file final
    joined = out[out.label.notna()].rename(columns={"cleaned_title": "title", "cleaned_comment": "comment"})
    seen = set(joined.comment.map(key))
    extra = fr.loc[unmatched].rename(columns={"t": "title", "c": "comment"})
    extra = extra[extra.comment.fillna("").ne("") & ~extra.ck.isin(seen)]
    extra = extra[extra.groupby(["title", "comment"]).label.transform("nunique") == 1]
    extra = extra.drop_duplicates(["title", "comment"])
    final = pd.concat([joined[["title", "comment", "label"]], extra[["title", "comment", "label"]]], ignore_index=True)
    final["title"] = final.title.fillna("")
    final["label"] = final.label.astype(int)
    assert final.comment.notna().all() and set(final.label) <= {0, 1, 2}
    final.to_csv(FINAL, index=False, encoding="utf-8-sig")
    final.assign(label=final.label.clip(upper=1)).to_csv(BINARY, index=False, encoding="utf-8-sig")  # 1, 2 = toxic
    print("File 3 cột:", len(final), "| từ parquet:", len(joined), "| chỉ có trong final:", len(extra))
    print("Nhãn file 3 cột:", final.label.value_counts().to_dict())

    print("Dòng master:", len(ml), "| có nhãn:", out.label.notna().sum())
    print("Theo mức khớp:", out.label_source.value_counts(dropna=False).to_dict())
    print("Theo nhãn:", out.label.value_counts(dropna=False).to_dict())
    print("Dòng nhãn không nối được:", len(rest), rest.label.value_counts().to_dict())
    print("Đã ghi:", OUT)


if __name__ == "__main__":
    main()

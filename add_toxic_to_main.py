"""Thay các dòng cuối của tonghopcmt_n12.xlsx bằng mẫu toxic ngoài (post_id có tiền tố EXT_)."""
import os
import shutil
import sys
from pathlib import Path

import openpyxl
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
MAIN = HERE / "tonghopcmt_n12.xlsx"
BACKUP = HERE / "tonghopcmt_n12_backup_truoc_khi_them_toxic.xlsx"
SOURCE = HERE.parent / "title_comment_label_binary.csv"
N = 3123


def read_main(path):
    return pd.read_excel(path, dtype=object)


def main():
    before = read_main(MAIN)
    # Chạy lại sẽ xóa thêm dữ liệu thật, nên dừng nếu đã thay rồi
    assert not before.post_id.astype(str).str.startswith("EXT_").any(), "File đã được thay trước đó"

    toxic = pd.read_csv(SOURCE, keep_default_na=False).query("label == 1").reset_index(drop=True)
    assert len(toxic) == N, len(toxic)

    tail = before.tail(N)
    head = before.iloc[:-N]
    print("Bị thay: dòng Excel", len(head) + 2, "đến", len(before) + 1, "| bài đăng:", tail.post_id.nunique(),
          "| bài mất hết bình luận:", len(set(tail.post_id) - set(head.post_id)),
          "| loại:", tail.comment_type.value_counts().to_dict())
    print("Toxic trùng văn bản với phần giữ lại:",
          toxic.comment.isin(set(head.message_clean.astype(str).str.lower())).sum())

    if not BACKUP.exists():
        shutil.copy2(MAIN, BACKUP)
    assert BACKUP.stat().st_size == MAIN.stat().st_size

    # Cùng tiêu đề thì cùng post_id để chia tập theo bài; tiêu đề trống thì mỗi dòng một bài
    title_ids = {t: i + 1 for i, t in enumerate(dict.fromkeys(toxic.title[toxic.title != ""]))}
    values = []
    for i, r in toxic.iterrows():
        pid = f"EXT_{title_ids[r.title]:04d}" if r.title else f"EXT_NT{i + 1:04d}"
        values.append({
            "post_id": pid, "comment_id": str(i + 1), "post_message": r.title or None,
            "parent_comment_id": None, "parent_message": None,
            "message_original": r.comment, "message_clean": r.comment,
            "comment_type": None, "data_status": "valid", "label": 1,
            "clean_status": "ready", "noise_removed": None,
        })

    wb = openpyxl.load_workbook(MAIN)
    ws = wb["NLP_N12"]
    assert ws.max_row == len(before) + 1, ws.max_row
    cols = {c.value: c.column for c in ws[1]}
    assert set(cols) == set(values[0]), cols
    for offset, row in enumerate(values):
        for name, value in row.items():
            cell = ws.cell(row=ws.max_row - N + 1 + offset, column=cols[name])
            cell.value = value
            if isinstance(value, str):
                cell.data_type = "s"  # giữ "=))" là văn bản, không thành công thức

    tmp = MAIN.with_name(MAIN.stem + "_tmp.xlsx")
    wb.save(tmp)
    after = read_main(tmp)
    # Kiểm tra trước khi thay file thật: phần giữ lại không đổi, phần mới đúng ánh xạ
    assert after.shape == before.shape
    assert after.iloc[:-N].fillna("__NA__").astype(str).equals(head.fillna("__NA__").astype(str))
    new = after.tail(N).reset_index(drop=True)
    assert new.message_clean.astype(str).equals(toxic.comment.astype(str))
    assert new.message_original.astype(str).equals(toxic.comment.astype(str))
    assert new.post_message.fillna("").astype(str).equals(toxic.title.astype(str))
    assert (new.label == 1).all() and after.label.notna().sum() == N
    assert not after.duplicated(["post_id", "comment_id"]).any()
    os.replace(tmp, MAIN)

    print("Đã thay", N, "dòng. Tổng:", len(after), "| bài EXT:", new.post_id.nunique(),
          "| không có tiêu đề:", (toxic.title == "").sum())
    print("Sao lưu:", BACKUP)


if __name__ == "__main__":
    main()

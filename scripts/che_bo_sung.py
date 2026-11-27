"""Che bổ sung thông tin cá nhân cho data/cleaned/masked.csv đã có và mọi file gán nhãn sinh ra từ nó.

Dùng SUPPLEMENT_RULES trong scripts/clean_dataset.py (lần làm sạch sau sẽ tự chạy các luật này) và một danh sách che
thủ công (chuỗi cũ -> chuỗi mới) đặt trong data/, không đặt trong repo vì chứa tên thật.

Chạy từ thư mục gốc repo:
    python scripts/che_bo_sung.py          # chạy thử: chỉ đếm, không ghi gì
    python scripts/che_bo_sung.py --ghi    # sao lưu masked.csv rồi ghi masked.csv và các file trong data/gan_nhan/
masked.csv luôn được dựng lại từ masked_truoc_che_bo_sung.csv (bản gốc trước lần che bổ sung đầu tiên), nên sửa luật
hay danh sách che tay rồi chạy lại là ra kết quả tái lập được; chỗ đợt trước che nhầm được trả lại (luật khoi_phuc).
Kết quả nằm trong data/cleaned/private/che_bo_sung/ (hoặc data/cleaned/che_bo_sung/ nếu chưa chuyển; đợt sau thêm hậu tố _dot2, _dot3..., không ghi đè đợt trước):
    masked_truoc_che_bo_sung.csv   bản gốc, còn tên thật: xác nhận xong thì chuyển vào data/cleaned/private/
    masked_truoc_dot*.csv          masked.csv trước mỗi đợt từ đợt 2
    xac_nhan_che_bo_sung*.xlsx     từng chỗ đổi trong masked.csv so với đợt trước, để một người xác nhận
    log_file_gan_nhan*.csv, sao_luu_file_gan_nhan*/   các ô đã sửa trong file gán nhãn và bản sao các file đó
Chạy lại khi không đổi luật thì không đổi gì.
"""
import argparse
import difflib
import importlib.util
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")
HERE = Path(__file__).parent
ROOT = HERE.parent
_spec = importlib.util.spec_from_file_location("clean_dataset", HERE / "clean_dataset.py")
cd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cd)

MASKED = ROOT / "data" / "cleaned" / "masked.csv"
# Xác nhận xong thì chuyển cả thư mục che_bo_sung/ (còn tên thật) vào data/cleaned/private/; script tìm ở đó trước.
_PRIVATE = ROOT / "data" / "cleaned" / "private" / "che_bo_sung"
OUT = _PRIVATE if _PRIVATE.exists() else ROOT / "data" / "cleaned" / "che_bo_sung"
MANUAL = OUT / "thu_cong.csv"
BACKUP = OUT / "masked_truoc_che_bo_sung.csv"
LABEL_DIR = ROOT / "data" / "gan_nhan"
TEXT_COLUMNS = ["post_text", "parent_text", "text_public"]
KIND = {"ma_sv_thieu_tien_to": "STUDENT_ID"}  # các luật còn lại đều che tên

manual = pd.read_csv(MANUAL, dtype=str, keep_default_na=False) if MANUAL.exists() else pd.DataFrame(columns=["chuoi_cu", "chuoi_moi"])
MANUAL_PAIRS = list(zip(manual.chuoi_cu, manual.chuoi_moi))


def fix(text):
    """Trả về (văn bản đã che bổ sung, các luật đã khớp)."""
    rules = []
    for old, new in MANUAL_PAIRS:
        if old in text:
            text = text.replace(old, new)
            rules.append("thu_cong")
    text, hits = cd.mask_supplement(text)
    rules += [name for name, _ in hits]
    merged = cd.merge_name_fragments(text)
    if merged != text:
        rules.append("ten_sau_NAME")
    return merged, rules


def window(old, new, pad=60):
    """Đoạn quanh chỗ khác nhau đầu tiên và cuối cùng, để người xác nhận đọc nhanh."""
    ops = [op for op in difflib.SequenceMatcher(None, old, new, autojunk=False).get_opcodes() if op[0] != "equal"]
    a1, a2, b1, b2 = ops[0][1], ops[-1][2], ops[0][3], ops[-1][4]
    return (("…" if a1 > pad else "") + old[max(0, a1 - pad):a2 + pad] + ("…" if a2 + pad < len(old) else ""),
            ("…" if b1 > pad else "") + new[max(0, b1 - pad):b2 + pad] + ("…" if b2 + pad < len(new) else ""))


def check(old, new):
    assert cd.EMOJI.findall(old) == cd.EMOJI.findall(new), ("mất emoji", old)
    assert fix(new)[0] == new, ("chạy lại vẫn đổi", new)


# Đợt che: đợt 1 ghi xac_nhan_che_bo_sung.xlsx, đợt sau ghi _dot2, _dot3... để không ghi đè file đã xác nhận.
ROUND = 1 + len(list(OUT.glob("xac_nhan_che_bo_sung*.xlsx")))


def next_free(name):
    """<thư mục che bổ sung>/<name> của đợt hiện tại (thêm _dot<N> từ đợt 2); không bao giờ ghi đè."""
    path = OUT / (name if ROUND == 1 else f"{Path(name).stem}_dot{ROUND}{Path(name).suffix}")
    assert not path.exists(), f"{path} đã có: đợt này đã ghi rồi, kiểm tra lại trước khi chạy tiếp"
    return path


def process_masked(write):
    """Dựng lại masked.csv từ bản gốc trước khi che bổ sung (BACKUP) bằng luật và danh sách che tay hiện tại, rồi so
    với masked.csv đang có. Nhờ vậy kết quả luôn tái lập được từ BACKUP, kể cả khi một luật bị thu hẹp (chỗ che nhầm
    ở đợt trước được khôi phục, ghi luật khoi_phuc)."""
    cur = pd.read_csv(MASKED, dtype=str, keep_default_na=False)
    base = pd.read_csv(BACKUP, dtype=str, keep_default_na=False) if BACKUP.exists() else cur.copy()
    assert len(base) == len(cur) and (base.comment_uid.values == cur.comment_uid.values).all()
    fixed = {}  # văn bản gốc -> (mới, luật)
    for column in TEXT_COLUMNS:
        for value in pd.unique(base[column]):
            if value and value not in fixed:
                new, rules = fix(value)
                if new != value:
                    check(value, new)
                    fixed[value] = (new, rules)
    out = base.copy()
    for column in TEXT_COLUMNS:
        out[column] = base[column].map(lambda v: fixed[v][0] if v in fixed else v)
    changed = base.text_public.isin(fixed.keys())
    out.loc[changed, "pii_types"] = [
        ";".join(sorted(set(filter(None, kinds.split(";"))) | {KIND.get(r, "NAME") for r in fixed[text][1]}))
        for kinds, text in zip(base.pii_types[changed], base.text_public[changed])]
    other = [c for c in cur.columns if c not in TEXT_COLUMNS + ["pii_types"]]
    assert cur[other].equals(out[other]), "các cột không phải văn bản bị đổi"
    diffs = {}  # (văn bản trong masked.csv hiện tại, văn bản mới) -> luật, cột, số dòng
    for column in TEXT_COLUMNS:
        differ = cur[column] != out[column]
        for b, c, n in zip(base[column][differ], cur[column][differ], out[column][differ]):
            d = diffs.setdefault((c, n), {"rules": set(fixed[b][1]) if b in fixed else {"khoi_phuc"}, "cols": set(), "n": 0})
            d["cols"].add(column)
            d["n"] += 1
    rows = {c: int((cur[c] != out[c]).sum()) for c in TEXT_COLUMNS}
    print(f"masked.csv: {len(fixed)} đoạn khác bản gốc; so với masked.csv hiện tại: {len(diffs)} đoạn đổi, số dòng theo cột {rows}")
    print("  số đoạn đổi theo luật:", dict(Counter(r for d in diffs.values() for r in d["rules"]).most_common()))
    if write and diffs:
        if not BACKUP.exists():
            shutil.copy2(MASKED, BACKUP)
            print("  sao lưu bản gốc:", BACKUP.relative_to(ROOT))
        else:
            previous = next_free("masked_truoc.csv")
            shutil.copy2(MASKED, previous)
            print("  sao lưu masked.csv trước đợt này:", previous.relative_to(ROOT))
        out.to_csv(MASKED, index=False, encoding="utf-8-sig")
        print("  đã ghi", MASKED.relative_to(ROOT))
    return diffs


def write_review(diffs):
    wb = Workbook()
    ws = wb.active
    ws.title = "cach_dung"
    for line in [
        "Danh sách các chỗ che bổ sung trong data/cleaned/masked.csv (scripts/che_bo_sung.py). Mỗi dòng là một đoạn văn bản khác nhau.",
        "File của đợt sau (_dot2, _dot3...) chỉ liệt kê chỗ đổi so với masked.csv sau đợt trước; file đợt trước đã xác nhận được giữ nguyên.",
        "Cột truoc còn tên thật: KHÔNG chia sẻ file này ra ngoài nhóm. Xác nhận xong thì chuyển file này và các bản sao lưu vào data/cleaned/private/.",
        "Người xác nhận đọc cột truoc và sau, chọn ở cột xac_nhan: dung (che đúng), che_nham (chữ bị che không phải tên, mã) hoặc con_sot (vẫn còn tên chưa che).",
        "Dòng che_nham hoặc con_sot: ghi lại ở ghi_chu rồi báo để sửa luật trong scripts/clean_dataset.py hoặc danh sách thu_cong.csv, sau đó chạy lại.",
        "Luật: thu_cong = danh sách che tay; ten_thuong_sau_thay_co = tên viết thường sau thầy/cô; ten_hoa_chu_dau_sau_thay_co = tên viết hoa chữ đầu sau thầy/cô;",
        "ten_thuong_truoc_oi = tên viết thường trước ơi; ten_hoa_sau_THAY_CO, ten_sau_NAME = tên viết hoa hoặc phần tên còn sót cạnh [NAME];",
        "ho_ten_*, ho_thi_* = họ tên đầy đủ viết thường; ma_sv_thieu_tien_to = mã sinh viên; khoi_phuc = trả lại chữ đợt trước che nhầm.",
    ]:
        ws.append([line])
    ws.column_dimensions["A"].width = 160
    ws = wb.create_sheet("da_che")
    ws.append(["stt", "luat", "cot", "so_dong", "truoc", "sau", "xac_nhan", "ghi_chu"])
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="305496")
    items = sorted(diffs.items(), key=lambda kv: (",".join(sorted(kv[1]["rules"])), kv[0][0]))
    for i, ((old, new), d) in enumerate(items, 1):
        a, b = window(old, new)
        ws.append([i, ",".join(sorted(d["rules"])), ",".join(sorted(d["cols"])), d["n"], a, b, "", ""])
    for col, w in zip("ABCDEFGH", [6, 26, 22, 8, 70, 70, 12, 30]):
        ws.column_dimensions[col].width = w
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    dv = DataValidation(type="list", formula1='"dung,che_nham,con_sot"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f"G2:G{len(items) + 1}")
    path = next_free("xac_nhan_che_bo_sung.xlsx")
    wb.save(path)
    print("  đã ghi", path.relative_to(ROOT), f"({len(items)} dòng)")


def restore_map():
    """Ô trong file gán nhãn mà đợt trước đã che nhưng luật hiện tại không che nữa (che nhầm): (file, sheet, ô) ->
    (giá trị hiện tại, giá trị khôi phục). Chỉ lấy ô có văn bản ngắn (log ghi đủ cả câu, không có dấu …)."""
    def round_of(path):
        tail = path.stem.rsplit("_dot", 1)
        return int(tail[1]) if len(tail) == 2 and tail[1].isdigit() else 1
    first, last = {}, {}  # ô -> văn bản trước lần sửa đầu tiên / sau lần sửa gần nhất
    for log in sorted(OUT.glob("log_file_gan_nhan*.csv"), key=round_of):
        for r in pd.read_csv(log, dtype=str, keep_default_na=False).itertuples():
            key = (r.file, r.sheet, r.o)
            first.setdefault(key, r.truoc)
            last[key] = r.sau
    restore = {}
    for key, original in first.items():
        if "…" not in original and "…" not in last[key]:
            target = fix(original)[0]
            if target != last[key]:
                restore[key] = (last[key], target)
    return restore


def process_label_files(write):
    log = []
    restore = restore_map()
    backup_dir = None
    for path in sorted(LABEL_DIR.rglob("*")):
        if path.name.startswith("~$") or path.suffix not in (".csv", ".xlsx"):
            continue
        rel = str(path.relative_to(ROOT))

        def change(sheet, where, value):
            key = (rel, sheet, where)
            if key in restore and restore[key][0] == value:
                return restore[key][1], ["khoi_phuc"]
            return fix(value)

        n = 0
        if path.suffix == ".csv":
            bom = path.read_bytes().startswith(b"\xef\xbb\xbf")
            df = pd.read_csv(path, dtype=str, keep_default_na=False)
            for column in df.columns:
                for i, value in df[column].items():
                    if value:
                        new, rules = change("", f"{column}[{i}]", value)
                        if new != value:
                            a, b = window(value, new)
                            log.append([rel, "", f"{column}[{i}]", ",".join(sorted(set(rules))), a, b])
                            df.at[i, column] = new
                            n += 1
        else:
            wb = load_workbook(path)
            for ws in wb.worksheets:
                for row in ws.iter_rows():
                    for cell in row:
                        if isinstance(cell.value, str) and cell.value:
                            new, rules = change(ws.title, cell.coordinate, cell.value)
                            if new != cell.value:
                                a, b = window(cell.value, new)
                                log.append([rel, ws.title, cell.coordinate, ",".join(sorted(set(rules))), a, b])
                                if write:
                                    cell.value = new
                                n += 1
        if n and write:
            if backup_dir is None:
                backup_dir = next_free("sao_luu_file_gan_nhan")
            target = backup_dir / path.relative_to(LABEL_DIR)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
            if path.suffix == ".csv":
                df.to_csv(path, index=False, encoding="utf-8-sig" if bom else "utf-8")
            else:
                wb.save(path)
        if n:
            print(f"  {rel}: {n} ô")
    if write and log:
        log_path = next_free("log_file_gan_nhan.csv")
        pd.DataFrame(log, columns=["file", "sheet", "o", "luat", "truoc", "sau"]).to_csv(log_path, index=False, encoding="utf-8-sig")
        print("  log:", log_path.relative_to(ROOT), "; sao lưu file gốc:", backup_dir.relative_to(ROOT))
    print(f"File gán nhãn: {len(log)} ô {'đã sửa' if write else 'sẽ sửa'}")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--ghi", action="store_true", help="sao lưu rồi ghi; không có cờ này thì chỉ chạy thử")
    args = parser.parse_args()
    cd.self_check()
    OUT.mkdir(parents=True, exist_ok=True)
    print("Danh sách che tay:", len(MANUAL_PAIRS), "chuỗi" if MANUAL.exists() else "(không có file thu_cong.csv)")
    diffs = process_masked(args.ghi)
    if args.ghi and diffs:
        write_review(diffs)
    process_label_files(args.ghi)
    if not args.ghi:
        print("Chạy thử xong, chưa ghi gì. Thêm --ghi để ghi.")


if __name__ == "__main__":
    main()

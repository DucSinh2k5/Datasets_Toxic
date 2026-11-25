#!/usr/bin/env python3
"""Tiền xử lý dữ liệu cào NLP_N12, không gán nhãn Toxic.

pip install pandas openpyxl regex
python preprocess_nlp_n12_compatible.py --input tonghopcmtcaoduoc_n12.xlsx --output tonghopcmt_n12_clean.xlsx

Giữ nguyên cột gốc, dấu tiếng Việt, dấu câu, teencode và emoji có cảm xúc.
Lọc trùng CHÍNH XÁC theo (post_clean, parent_clean, message_clean).
"""
import argparse
import html
import re
import unicodedata
from pathlib import Path

import pandas as pd
import regex

# Chỉ nhận dạng các tag XML/HTML có hình dạng rõ ràng; không xóa biểu thức so sánh bình thường.
TAG_RE = re.compile(r"<!--.*?-->|<!\[CDATA\[|\]\]>|<\?[^>]*\?>|<!DOCTYPE[^>]*>|</?[A-Za-z][A-Za-z0-9:_-]*(?:\s+[^<>]*?)?\s*/?>", re.I | re.S)
URL_RE = re.compile(r"(?i)(?<![\w@])(?:https?://|ftp://|www\.)[^\s<>\"']+|(?<![\w@])(?:[a-z0-9-]+\.)+(?:com|vn|org|net|edu|gov|io|me|info|co|app|dev)(?:/[^\s<>\"']*)?")
CTRL_RE = regex.compile(r"[\p{Cc}\p{Cf}]", regex.VERSION1)
# Giữ chữ (kể cả tiếng Việt), số, dấu kết hợp, dấu câu, dấu cách, ký hiệu emoji.
NOISE_RE = regex.compile(r"[^\p{L}\p{N}\p{M}\p{P}\p{Zs}\p{So}\p{Sk}]", regex.VERSION1)
SPACE_RE = re.compile(r"\s+")
# Danh sách giữ mang tính heuristic, KHÔNG có nghĩa mọi emoji này là Toxic.
EMOTION_EMOJI = set(regex.findall(r'\X', '😀😁😂🤣😃😄😅😆😉😊😋😎😍🥰😘🙂🙃🥲🥹😌😏😒🙄😔😕🙁😣😖😫😩🥺😢😭😤😠😡🤬🤯😳😱😨😰😥😓🤗🤔🤨🧐😑😐😶😬🤥🤢🤮🥴😵🤐😮😯😲😧😦😟😞😝😜🤪😛😇🤡👿😈💀💩👎👍👏🙏🤝👊✊🤛🤜🖕💔🔥💯'))
EMOTION_EMOJI.update({'❤️', '❤', '♥', '♥️', '☠', '☠️', '☺', '☺️', '😵‍💫', '🫥', '🫶', '🫤', '🥹', '🥲', '🥰', '😭', '🤣', '😂'})


def clean_text(value, emoji_mode='selective'):
    if value is None or (not isinstance(value, str) and pd.isna(value)):
        return ''
    s = unicodedata.normalize('NFC', str(value))
    s = html.unescape(s)
    s = TAG_RE.sub(' ', s)
    # URL có thể nuốt dấu câu cuối câu; giữ lại ?/!/. nếu là dấu kết thúc bên ngoài URL.
    def remove_url(m):
        tail = m.group(0)
        trailing = ''
        while tail and tail[-1] in '!,;:':
            trailing = tail[-1] + trailing
            tail = tail[:-1]
        # Dấu chấm cuối câu giữ lại; dấu chấm trong domain không bị ảnh hưởng.
        if tail.endswith('.'):
            trailing = '.' + trailing
        return ' ' + trailing + ' '
    s = URL_RE.sub(remove_url, s)
    if emoji_mode != 'all':
        parts = []
        for token in regex.findall(r'\X', s):
            is_emoji = bool(regex.search(r'\p{Extended_Pictographic}', token))
            if is_emoji and (emoji_mode == 'none' or token not in EMOTION_EMOJI):
                parts.append(' ')
            else:
                parts.append(token)
        s = ''.join(parts)
    s = CTRL_RE.sub(' ', s)
    s = NOISE_RE.sub(' ', s)
    return SPACE_RE.sub(' ', s).strip()


def main():
    parser = argparse.ArgumentParser(description='NLP_N12: clean + deduplicate crawled comments')
    parser.add_argument('--input', required=True, help='Đường dẫn .xlsx/.xlsm/.csv gốc')
    parser.add_argument('--output', required=True, help='Đường dẫn .xlsx/.csv kết quả')
    parser.add_argument('--comment-col', default='message_original')
    parser.add_argument('--post-col', default='post_message')
    parser.add_argument('--parent-col', default='parent_message')
    parser.add_argument('--sheet', default='0', help='Sheet name hoặc chỉ số từ 0')
    parser.add_argument('--emoji-mode', choices=['selective', 'all', 'none'], default='selective')
    args = parser.parse_args()
    src, dst = Path(args.input), Path(args.output)
    if not src.is_file():
        parser.error(f'Không tìm thấy file: {src}')
    if src.suffix.lower() in ('.xlsx', '.xlsm'):
        sheet = int(args.sheet) if args.sheet.isdigit() else args.sheet
        df = pd.read_excel(src, sheet_name=sheet, dtype=object, engine='openpyxl')
    elif src.suffix.lower() == '.csv':
        df = pd.read_csv(src, dtype=object, encoding='utf-8-sig', low_memory=False)
    else:
        parser.error('Chỉ hỗ trợ đầu vào .xlsx, .xlsm hoặc .csv')
    for name in (args.comment_col, args.post_col, args.parent_col):
        if name not in df.columns:
            parser.error(f'Thiếu cột {name!r}. Các cột hiện có: {list(df.columns)}')
    original_count = len(df)
    # File gốc có message_clean; tái tạo từ message_original, không làm sạch chồng.
    # Các cột gốc khác, bao gồm ID và dữ liệu trạng thái, được giữ nguyên.
    for src_col, out_col in ((args.comment_col, 'message_clean'),
                             (args.post_col, 'post_clean'),
                             (args.parent_col, 'parent_clean')):
        df[out_col] = df[src_col].map(lambda x: clean_text(x, args.emoji_mode))
    empty = df['message_clean'].eq('')
    removed_empty = int(empty.sum())
    df = df.loc[~empty].copy()
    duplicate = df.duplicated(subset=['post_clean', 'parent_clean', 'message_clean'], keep='first')
    removed_duplicate = int(duplicate.sum())
    df = df.loc[~duplicate].reset_index(drop=True)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.suffix.lower() == '.xlsx':
        df.to_excel(dst, index=False, engine='openpyxl')
    elif dst.suffix.lower() == '.csv':
        df.to_csv(dst, index=False, encoding='utf-8-sig')
    else:
        parser.error('Đầu ra phải là .xlsx hoặc .csv')
    print(f'Đầu vào: {original_count:,} | Rỗng sau làm sạch: {removed_empty:,} | Trùng bộ ba: {removed_duplicate:,} | Đầu ra: {len(df):,}')
    print(f'Đã lưu: {dst}')


if __name__ == '__main__':
    main()

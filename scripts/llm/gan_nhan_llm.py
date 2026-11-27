"""Gán nhãn 4 hướng bằng LLM (Claude hoặc OpenAI) theo prompt scripts/llm/prompt_ban5.md.

Chạy từ thư mục gốc repo. Chỉ gửi văn bản đã che lấy từ data/cleaned/masked.csv. Câu nào còn khớp mẫu thông tin cá
nhân (mã sinh viên, số điện thoại, tên viết thường...) thì bỏ qua và ghi lý do, không gửi đi.

Ví dụ:
  # Chạy thử, KHÔNG gọi API: kiểm tra đầu vào, ghi một request mẫu, ước số token và chi phí
  python scripts/llm/gan_nhan_llm.py --gold 2 --thu
  # Gold vòng 2 (dùng để chỉnh prompt), gọi từng câu
  python scripts/llm/gan_nhan_llm.py --gold 2 --nha-cung-cap claude --model claude-opus-5-5 --effort medium
  # Gold vòng 1 (chỉ để kiểm tra, không chỉnh prompt theo kết quả này)
  python scripts/llm/gan_nhan_llm.py --gold 1 --nha-cung-cap openai --model <tên mô hình OpenAI> --gia 0.4,1.6,0.1
  # Batch API của Claude: rẻ 50%, xong trong tối đa 24 giờ; lần chạy sau lấy kết quả
  python scripts/llm/gan_nhan_llm.py --ds data/llm/ds_cau.csv --che-do batch
  python scripts/llm/gan_nhan_llm.py --ds data/llm/ds_cau.csv --che-do batch --lay-batch
  # Mô hình mở qua máy chủ vLLM (Kaggle/Colab, xem scripts/llm/kaggle_qwen3_tach_huong.ipynb), chọn prompt bằng --prompt
  python scripts/llm/gan_nhan_llm.py --gold 1 2 --nha-cung-cap vllm --model qwen2.5-7b-instruct --nhiet-do 0 --luong 16 --prompt scripts/llm/prompt_ban5_en.md
  # Tách hướng (4 prompt tiếng Anh, mỗi câu gọi 4 lần), Qwen3 tắt chế độ suy nghĩ (scripts/llm/kaggle_qwen3_tach_huong.ipynb)
  python scripts/llm/gan_nhan_llm.py --gold 2 --nha-cung-cap vllm --model qwen3-14b --nhiet-do 0 --luong 16 --khong-suy-nghi --prompt scripts/llm/prompt_ban5_en_tach
  # Gán toàn bộ theo đợt bằng cấu hình đã khóa (scripts/llm/kaggle_gan_dot.ipynb; chia đợt bằng chia_dot.py)
  python scripts/llm/gan_nhan_llm.py --ds data/llm/dot/dot_01.csv --nha-cung-cap vllm --model qwen3-14b --nhiet-do 0 --luong 16 --khong-suy-nghi --prompt scripts/llm/prompt_ban5_en_tach --dung-sau-phut 600
  # API khác tương thích OpenAI (Groq, Mistral...): --nha-cung-cap openai --base-url <địa chỉ> --bien-khoa <TÊN_BIẾN_KHÓA>
Kết quả: data/llm/ket_qua/<nhà cung cấp>_<mô hình>_<effort>_<prompt>_<nguồn>.jsonl, mỗi dòng một câu, ghi ngay sau
khi có kết quả. Chạy lại cùng lệnh thì bỏ qua câu đã có kết quả hợp lệ, nên dừng giữa chừng không mất gì.
File .tong_ket.json cạnh đó ghi mô hình, effort, phiên bản và mã băm prompt, số token, chi phí (để khóa và khai báo).

Cần: pip install anthropic (Claude) hoặc pip install openai (OpenAI). Khóa API đặt trong biến môi trường
ANTHROPIC_API_KEY / OPENAI_API_KEY, không ghi vào file nào trong repo. Dùng gói API không lấy dữ liệu để huấn luyện.
"""
import argparse
import json
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import chung  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# Giá USD cho 1 triệu token (bảng giá Anthropic lưu ngày 2026-10-06; kiểm tra lại trước khi chạy thật).
# cache_write: ghi cache 5 phút = 1,25 lần giá input. Batch API: giảm 50% mọi loại token.
GIA = {
    "claude-opus-5-5": {"input": 4.00, "output": 20.00, "cache_read": 0.20},
    "claude-sonnet-5-5": {"input": 2.00, "output": 10.00, "cache_read": 0.20},
    "claude-haiku-5-5": {"input": 0.10, "output": 0.50, "cache_read": 0.01},  # cache_read là ước tính 10% giá input
}
# Mô hình nhận tham số fallbacks: "default" (tự chạy lại trên mô hình khác khi bị bộ lọc an toàn từ chối).
FALLBACK_MODELS = {"claude-opus-5-5", "claude-opus-5", "claude-fable-5-1", "claude-sonnet-5-5"}
MAX_TOKENS = 4096  # gồm cả token suy nghĩ (luôn bật trên Claude thế hệ 5)
CUSTOM_ID = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")
# Prompt mặc định; main() nạp lại theo --prompt trước khi dùng.
PROMPT_FILE = chung.PROMPT_FILE
SYSTEM, PROMPT_VERSION, PROMPT_SHA = chung.load_prompt()
TACH = None  # {hướng: system prompt} khi --prompt là thư mục prompt tách hướng
VLLM_URL = "http://localhost:8000/v1"


def user_message(row, cap):
    def cut(text):
        return text if len(text) <= cap else text[:cap].rstrip() + " […đã cắt]"
    post = cut(row.post_text) if row.post_text else "(không có)"
    parent = cut(row.parent_text) if row.parent_text else "(không có, đây là bình luận gốc)"
    return f"<bai_dang>{post}</bai_dang>\n<binh_luan_cha>{parent}</binh_luan_cha>\n<binh_luan>{row.text_public}</binh_luan>"


NHAC_LAI = "\n\nLưu ý: lần trả lời trước vi phạm quy tắc ({}). Xem lại mục 6 rồi gán lại."
NHAC_LAI_EN = "\n\nNote: your previous answer broke a rule ({}). Re-read section 6 and label again."


def nhac_lai():
    return NHAC_LAI_EN if "-en" in PROMPT_VERSION else NHAC_LAI


def cost(model, usage, price, batch):
    p = price or GIA.get(model)
    if not p:
        return None
    write = p.get("cache_write", p["input"] * 1.25)
    usd = (usage["input_tokens"] * p["input"] + usage["output_tokens"] * p["output"]
           + usage["cache_creation_input_tokens"] * write + usage["cache_read_input_tokens"] * p["cache_read"]) / 1e6
    return round(usd * (0.5 if batch else 1), 6)


# ---------------------------------------------------------------- nhà cung cấp
def claude_params(model, effort, text):
    # Không gửi temperature: các mô hình Claude thế hệ 5 trả lỗi 400 nếu có tham số này.
    # Không gửi thinking: mặc định là adaptive; độ sâu điều khiển bằng effort.
    # System prompt giống hệt nhau ở mọi câu nên được cache; phần riêng của câu nằm sau, trong messages.
    return {
        "model": model,
        "max_tokens": MAX_TOKENS,
        "system": [{"type": "text", "text": SYSTEM, "cache_control": {"type": "ephemeral"}}],
        "messages": [{"role": "user", "content": text}],
        "output_config": {"effort": effort, "format": {"type": "json_schema", "schema": chung.SCHEMA}},
    }


class Claude:
    def __init__(self, model, effort, fallback):
        import anthropic
        self.anthropic = anthropic
        self.client = anthropic.Anthropic(max_retries=4)
        self.model, self.effort = model, effort
        self.fallback = fallback and model in FALLBACK_MODELS

    def params(self, text):
        return claude_params(self.model, self.effort, text)

    def read(self, resp):
        usage = {k: getattr(resp.usage, k, 0) or 0 for k in
                 ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")}
        if resp.stop_reason == "refusal":
            category = getattr(resp.stop_details, "category", None) if resp.stop_details else None
            return None, usage, resp.model, f"refusal ({category})"
        if resp.stop_reason == "max_tokens":
            return None, usage, resp.model, "max_tokens"
        text = next((b.text for b in resp.content if b.type == "text"), "")
        return json.loads(text), usage, resp.model, None

    def call(self, text):
        try:
            if self.fallback:
                resp = self.client.beta.messages.create(**self.params(text), betas=["server-side-fallback-2026-07-01"],
                                                        fallbacks="default")
            else:
                resp = self.client.messages.create(**self.params(text))
        except self.anthropic.BadRequestError as e:
            raise SystemExit(f"Request sai ({e.status_code}): {e.message}. Dừng để sửa, không gửi tiếp.")
        except self.anthropic.AuthenticationError:
            raise SystemExit("Khóa API không hợp lệ hoặc chưa đặt ANTHROPIC_API_KEY.")
        except (self.anthropic.RateLimitError, self.anthropic.APIConnectionError, self.anthropic.InternalServerError) as e:
            return None, None, None, f"tạm lỗi: {type(e).__name__}"  # SDK đã tự thử lại 4 lần
        return self.read(resp)


class OpenAIChat:
    """OpenAI, hoặc máy chủ tương thích OpenAI khi có base_url (vLLM chạy trên Kaggle/Colab, sau này Groq, Mistral...)."""

    def __init__(self, model, nhiet_do, reasoning_effort, base_url=None, api_key=None, max_tokens=None, key_name="OPENAI_API_KEY",
                 khong_suy_nghi=False):
        import openai
        self.openai = openai
        kwargs = {"max_retries": 4}
        if base_url:
            kwargs["base_url"] = base_url
        if api_key:
            kwargs["api_key"] = api_key
        self.client = openai.OpenAI(**kwargs)
        self.model, self.nhiet_do, self.reasoning_effort, self.max_tokens = model, nhiet_do, reasoning_effort, max_tokens
        self.key_name, self.khong_suy_nghi = key_name, khong_suy_nghi

    def params(self, text, system=None, schema=None):
        p = {
            "model": self.model,
            "messages": [{"role": "system", "content": system or SYSTEM}, {"role": "user", "content": text}],
            "response_format": {"type": "json_schema",
                                "json_schema": {"name": "nhan", "strict": True, "schema": schema or chung.SCHEMA}},
        }
        if self.nhiet_do is not None:  # mô hình suy luận của OpenAI không nhận temperature
            p["temperature"] = self.nhiet_do
        if self.reasoning_effort:
            p["reasoning_effort"] = self.reasoning_effort
        if self.max_tokens:
            p["max_tokens"] = self.max_tokens
        if self.khong_suy_nghi:  # Qwen3 trên vLLM: tắt chế độ suy nghĩ qua chat template
            p["extra_body"] = {"chat_template_kwargs": {"enable_thinking": False}}
        return p

    def call(self, text, system=None, schema=None, max_tokens=None):
        p = self.params(text, system, schema)
        if max_tokens:  # hỏi lại với giới hạn cao hơn khi lần trước bị cắt (max_tokens)
            p["max_tokens"] = max_tokens
        try:
            r = self.client.chat.completions.create(**p)
        except self.openai.BadRequestError as e:
            raise SystemExit(f"Request sai: {e}. Dừng để sửa, không gửi tiếp.")
        except self.openai.AuthenticationError:
            raise SystemExit(f"Khóa API không hợp lệ hoặc chưa đặt {self.key_name}.")
        except (self.openai.RateLimitError, self.openai.APIConnectionError, self.openai.InternalServerError) as e:
            return None, None, None, f"tạm lỗi: {type(e).__name__}"
        u = r.usage
        cached = getattr(getattr(u, "prompt_tokens_details", None), "cached_tokens", 0) or 0
        usage = {"input_tokens": u.prompt_tokens - cached, "output_tokens": u.completion_tokens,
                 "cache_creation_input_tokens": 0, "cache_read_input_tokens": cached}
        msg = r.choices[0].message
        if getattr(msg, "refusal", None):
            return None, usage, r.model, "refusal"
        if r.choices[0].finish_reason == "length":
            return None, usage, r.model, "max_tokens"
        try:
            return json.loads(msg.content), usage, r.model, None
        except (json.JSONDecodeError, TypeError):
            return None, usage, r.model, "JSON hỏng: " + str(msg.content)[:80]


class GiaLap:
    """Chỉ để thử đường chạy của script (ghi file, chạy tiếp, kiểm tra nhãn), không gọi mạng."""
    model = "gia-lap"

    def call(self, text, system=None, schema=None, max_tokens=None):
        if schema and "emotion_1" in schema["properties"] and "MAXTOK" in text and not max_tokens:
            return None, None, "gia-lap", "max_tokens"   # giả lập câu bị cắt, phải hỏi lại với giới hạn cao hơn
        out = {"toxicity": "clean", "topic": "unk", "stance": "suggest", "emotion_1": "neutral", "emotion_2": [], "hard": False,
               "ly_do": "giả lập"}
        if schema:  # tách hướng: chỉ trả các trường của hướng được hỏi
            out = {k: v for k, v in out.items() if k in schema["properties"]}
            if "stance" in out and "judged unk" in text:  # giả lập việc hỏi lại stance khi vi phạm ràng buộc
                out["stance"] = "none"
            if "bang_chung" in schema["properties"]:  # giả lập bằng chứng bịa: câu có "ngu" thì lần đầu trích sai
                out["bang_chung"] = ""
                if " ngu" in text:
                    out |= {"toxicity": "attack", "bang_chung": "ngu" if "Check:" in text else "đồ bịa"}
                elif "đẹp" in text:  # profane không có từ tục: hỏi lại vẫn sai, script phải đổi thành clean
                    out |= {"toxicity": "profane", "bang_chung": "đẹp"}
        return out, {"input_tokens": len(text) // 3, "output_tokens": 40, "cache_creation_input_tokens": 0,
                     "cache_read_input_tokens": len(system or SYSTEM) // 3}, "gia-lap", None


# ---------------------------------------------------------------- đầu vào, đầu ra
def load_rows(args):
    masked = chung.load_masked()
    if args.gold:
        uids = chung.load_gold(args.gold)[["comment_uid", "vong"]]
        source = "gold" + "".join(str(r) for r in args.gold)
    else:
        uids = pd.read_csv(args.ds, dtype=str, usecols=["comment_uid"])
        uids["vong"] = ""
        source = Path(args.ds).stem
    rows = uids.merge(masked, on="comment_uid", how="left")
    missing = rows.text_public.isna().sum()
    if missing:
        raise SystemExit(f"{missing} comment_uid không có trong masked.csv")
    if not args.co_tap_test and (rows.split == "test").any():
        raise SystemExit(f"Đầu vào có {(rows.split == 'test').sum()} câu thuộc split test. Tập test chỉ gán khi đã khóa prompt: "
                         "thêm --co-tap-test nếu đúng là đang gán tập test.")
    if args.gioi_han:
        rows = rows.head(args.gioi_han)
    return rows.reset_index(drop=True), source


def out_path(args, source):
    if args.ra:
        return Path(args.ra)
    model = args.model.replace("/", "-")
    effort = args.effort if args.nha_cung_cap == "claude" else (args.reasoning_effort or "mac-dinh")
    return chung.KET_QUA / f"{args.nha_cung_cap}_{model}_{effort}_{PROMPT_VERSION}_{source}.jsonl"


def done_ids(path):
    if not path.exists():
        return set()
    ids = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                r = json.loads(line)
            except json.JSONDecodeError:  # dòng cuối dở dang khi phiên bị ngắt: bỏ, câu đó sẽ gán lại
                continue
            if not r.get("loi"):
                ids.add(r["comment_uid"])
    return ids


def record(row, args, model_served, labels, usage, err, vi_pham, da_sua, batch=False):
    rec = {"comment_uid": row.comment_uid, "vong": row.vong, "nha_cung_cap": args.nha_cung_cap, "model_yeu_cau": args.model,
           "model_tra_loi": model_served, "effort": args.effort if args.nha_cung_cap == "claude" else args.reasoning_effort,
           "prompt_version": PROMPT_VERSION, "prompt_sha": PROMPT_SHA, "che_do": "batch" if batch else "truc_tiep",
           "thoi_gian": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    rec |= labels or {k: None for k in ["toxicity", "topic", "stance", "emotion_1", "emotion_2", "hard", "ly_do"]}
    rec |= {"vi_pham": "; ".join(vi_pham), "da_sua": "; ".join(da_sua), "loi": err or "", "usage": usage,
            "chi_phi_usd": cost(args.model, usage, args.gia_dict, batch) if usage else None}
    return rec


def summarize(path, meta):
    recs = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    last = {}
    for r in recs:  # dòng sau ghi đè dòng trước của cùng câu (chạy lại câu lỗi)
        last[r["comment_uid"]] = r
    tok = {k: sum((r["usage"] or {}).get(k, 0) for r in recs) for k in
           ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")}
    s = meta | {
        "so_cau": len(last), "thanh_cong": sum(1 for r in last.values() if not r["loi"]),
        "loi": sum(1 for r in last.values() if r["loi"]), "vi_pham": sum(1 for r in last.values() if r["vi_pham"]),
        "hard": sum(1 for r in last.values() if r.get("hard")),
        "model_tra_loi": sorted({r["model_tra_loi"] for r in last.values() if r["model_tra_loi"]}),
        "token_tong_moi_lan_goi": tok, "chi_phi_usd": round(sum(r["chi_phi_usd"] or 0 for r in recs), 4),
    }
    path.with_suffix(".tong_ket.json").write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(s, ensure_ascii=False, indent=2))


# ---------------------------------------------------------------- các chế độ chạy
NHAC_STANCE = ("\n\nNote: in a separate step the topic of this comment was judged unk (it is not about anything). "
               "Stance must therefore be none or unk.")
NHAC_ATTACK = ("\n\nCheck: you answered attack with `bang_chung` = {q!r}, but this text does not appear in <binh_luan>. "
               "`bang_chung` must be copied exactly, character by character, from <binh_luan> (not from the post or the parent "
               "comment). If <binh_luan> itself contains no word or phrase that insults, belittles, mocks or threatens a person "
               "or group, the comment is not attack. Answer again.")
NHAC_PROFANE = ("\n\nCheck: you answered profane, but <binh_luan> contains none of the known profane words or their variants "
                "(vl, vcl, vãi, đm, dm, đéo, deo, cc, cl, loz, đcm, vkl, ...). Abbreviations, slang and words you do not "
                "recognize are not profanity. Answer again.")


def nhac_bang_chung(toxicity, quote):
    return NHAC_ATTACK.format(q=quote) if toxicity == "attack" else NHAC_PROFANE


def one_tach(row, args, backend):
    """Tách hướng: gọi 4 lần (mỗi lần một hướng, prompt và lược đồ riêng), ghép kết quả rồi kiểm tra như thường.
    Kiểm tra bằng chứng toxicity (khi lược đồ có `bang_chung`, từ p3): attack mà `bang_chung` không có trong câu, hoặc
    profane mà câu không có từ tục nào trong chung.TU_TUC, thì hỏi lại toxicity một lần; vẫn không có bằng chứng thì
    attack thành profane (nếu câu có từ tục) hoặc clean, profane thành clean, ghi ở da_sua.
    Nếu ghép lại vi phạm ràng buộc topic = unk thì hỏi lại stance một lần, có báo topic đã gán."""
    text = user_message(row, args.cat_bai_dang)
    usage_all, served, out, reasons, hard = None, None, {}, {}, False
    sua_tox = []

    def ask(h, extra=""):
        nonlocal usage_all, served, hard
        o, usage, served_h, err = backend.call(text + extra, system=TACH[h], schema=chung.SCHEMA_TACH[h])
        if usage:
            usage_all = usage if usage_all is None else {k: usage_all[k] + usage[k] for k in usage}
        if err == "max_tokens" and args.max_tokens:
            # Ở nhiệt độ 0 chạy lại y hệt sẽ bị cắt y hệt: hỏi lại một lần với giới hạn gấp đôi.
            o, usage, served_h, err = backend.call(text + extra, system=TACH[h], schema=chung.SCHEMA_TACH[h],
                                                   max_tokens=2 * args.max_tokens)
            if usage:
                usage_all = {k: usage_all[k] + usage[k] for k in usage} if usage_all else usage
            sua_tox.append(f"hỏi lại {h} với max_tokens {2 * args.max_tokens} vì bị cắt")
        if err:
            return f"{h}: {err}"
        served = served_h or served
        out.update({k: v for k, v in o.items() if k not in ("ly_do", "hard")})
        reasons[h] = str(o.get("ly_do", "")).strip()
        hard = hard or bool(o.get("hard"))
        return None

    for h in chung.HUONG_TACH:
        err = ask(h)
        if err:
            return record(row, args, served, None, usage_all, err, [], [])

    if "bang_chung" in chung.SCHEMA_TACH["toxicity"]["properties"]:
        ly = chung.kiem_tra_bang_chung(out.get("toxicity"), out.get("bang_chung", ""), row.text_public)
        if ly:
            err = ask("toxicity", nhac_bang_chung(out.get("toxicity"), out.get("bang_chung", "")))
            if err:
                return record(row, args, served, None, usage_all, err, [], [])
            sua_tox.append(f"hỏi lại toxicity vì {ly}")
            ly2 = chung.kiem_tra_bang_chung(out.get("toxicity"), out.get("bang_chung", ""), row.text_public)
            if ly2:
                moi = "profane" if out["toxicity"] == "attack" and chung.co_tu_tuc(row.text_public) else "clean"
                sua_tox.append(f"toxicity {out['toxicity']} → {moi} vì lần hỏi lại vẫn {ly2}")
                out["toxicity"] = moi

    def merged():
        return out | {"hard": hard, "ly_do": " | ".join(f"{h}: {reasons[h]}" for h in chung.HUONG_TACH)}

    labels, vi_pham, da_sua = chung.kiem_tra(merged())
    if any("topic = unk" in v for v in vi_pham):
        err = ask("stance", NHAC_STANCE)
        if err:
            return record(row, args, served, None, usage_all, err, [], [])
        labels, vi_pham, da_sua = chung.kiem_tra(merged())
        da_sua = da_sua + ["hỏi lại stance vì topic = unk"]
    labels["bang_chung"] = str(out.get("bang_chung", ""))[:200]
    return record(row, args, served, labels, usage_all, None, vi_pham, sua_tox + da_sua)


def run_direct(args, rows, path, backend):
    skip = done_ids(path)
    todo = [r for r in rows.itertuples() if r.comment_uid not in skip]
    print(f"{len(rows)} câu, đã có {len(rows) - len(todo)}, cần gán {len(todo)} → {path}")
    lock = threading.Lock()
    path.parent.mkdir(parents=True, exist_ok=True)
    han = time.time() + args.dung_sau_phut * 60 if args.dung_sau_phut else None

    def one(row):
        if han and time.time() > han:  # hết giờ: không gán thêm câu mới, chạy lại cùng lệnh để gán tiếp
            return None
        pii = chung.con_thong_tin_ca_nhan(row.post_text, row.parent_text, row.text_public)
        if pii:
            return record(row, args, None, None, None, f"không gửi: còn mẫu thông tin cá nhân {pii}", [], [])
        if TACH:
            return one_tach(row, args, backend)
        text = user_message(row, args.cat_bai_dang)
        usage_all = None
        for attempt in range(2):  # lần 2 chỉ khi vi phạm quy tắc, kèm lời nhắc
            out, usage, served, err = backend.call(text)
            if usage:
                usage_all = usage if usage_all is None else {k: usage_all[k] + usage[k] for k in usage}
            if err:
                return record(row, args, served, None, usage_all, err, [], [])
            labels, vi_pham, da_sua = chung.kiem_tra(out)
            if not vi_pham or attempt == 1:
                return record(row, args, served, labels, usage_all, None, vi_pham, da_sua)
            text = user_message(row, args.cat_bai_dang) + nhac_lai().format("; ".join(vi_pham))

    bo_qua = 0
    step = 20 if len(todo) <= 2000 else 500
    if path.exists() and path.stat().st_size and not path.read_bytes().endswith(b"\n"):
        with path.open("a", encoding="utf-8") as f:  # dòng cuối dở dang (phiên bị ngắt): xuống dòng để không dính dòng mới
            f.write("\n")
    with ThreadPoolExecutor(max_workers=args.luong) as pool, path.open("a", encoding="utf-8") as f:
        futures = [pool.submit(one, r) for r in todo]
        for i, fut in enumerate(as_completed(futures), 1):
            rec = fut.result()
            if rec is None:
                bo_qua += 1
                continue
            with lock:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                f.flush()
            if i % step == 0 or i == len(todo):
                print(f"  {i}/{len(todo)} ({datetime.now():%H:%M})", flush=True)
    if bo_qua:
        print(f"Dừng vì quá {args.dung_sau_phut} phút: còn {bo_qua} câu chưa gán. Chạy lại cùng lệnh (cùng file kết quả) để gán tiếp.")


def run_batch_submit(args, rows, path, backend):
    from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
    from anthropic.types.messages.batch_create_params import Request
    state = path.with_suffix(".batch.json")
    if state.exists():
        raise SystemExit(f"Đã có {state}: lấy kết quả bằng --lay-batch trước khi gửi batch mới.")
    skip = done_ids(path)
    reqs, blocked = [], []
    for row in rows.itertuples():
        if row.comment_uid in skip:
            continue
        if chung.con_thong_tin_ca_nhan(row.post_text, row.parent_text, row.text_public):
            blocked.append(row.comment_uid)
            continue
        assert CUSTOM_ID.match(row.comment_uid), row.comment_uid
        # Batch API không nhận tham số fallbacks; câu bị từ chối sẽ chạy lại ở chế độ trực tiếp.
        reqs.append(Request(custom_id=row.comment_uid,
                            params=MessageCreateParamsNonStreaming(**backend.params(user_message(row, args.cat_bai_dang)))))
    ids = []
    for start in range(0, len(reqs), args.co_batch):
        batch = backend.client.messages.batches.create(requests=reqs[start:start + args.co_batch])
        ids.append(batch.id)
        print("Đã gửi batch", batch.id, len(reqs[start:start + args.co_batch]), "câu")
    state.write_text(json.dumps({"batch_ids": ids, "khong_gui": blocked}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(blocked)} câu không gửi vì còn mẫu thông tin cá nhân. Lấy kết quả: thêm --lay-batch vào lệnh này.")


def run_batch_collect(args, rows, path, backend):
    state = path.with_suffix(".batch.json")
    info = json.loads(state.read_text(encoding="utf-8"))
    by_id = {r.comment_uid: r for r in rows.itertuples()}
    for bid in info["batch_ids"]:
        if backend.client.messages.batches.retrieve(bid).processing_status != "ended":
            raise SystemExit(f"Batch {bid} chưa xong, thử lại sau.")
    n = 0
    with path.open("a", encoding="utf-8") as f:
        for bid in info["batch_ids"]:
            for res in backend.client.messages.batches.results(bid):  # kết quả không theo thứ tự: khớp theo custom_id
                row = by_id[res.custom_id]
                if res.result.type == "succeeded":
                    out, usage, served, err = backend.read(res.result.message)
                    if err:
                        rec = record(row, args, served, None, usage, err, [], [], batch=True)
                    else:
                        labels, vi_pham, da_sua = chung.kiem_tra(out)
                        rec = record(row, args, served, labels, usage, None, vi_pham, da_sua, batch=True)
                else:
                    rec = record(row, args, None, None, None, f"batch: {res.result.type}", [], [], batch=True)
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                n += 1
        for uid in info["khong_gui"]:
            f.write(json.dumps(record(by_id[uid], args, None, None, None, "không gửi: còn mẫu thông tin cá nhân", [], [], batch=True),
                               ensure_ascii=False) + "\n")
    state.rename(state.with_suffix(f".da_lay_{datetime.now():%Y%m%d%H%M}.json"))
    print(f"Đã ghi {n} kết quả. Câu lỗi hoặc bị từ chối: chạy lại cùng lệnh ở chế độ trực tiếp, script chỉ gán các câu đó.")


def dry_run(args, rows, path):
    """Không gọi API: kiểm tra đầu vào, ghi request mẫu, ước token và chi phí."""
    blocked = [r.comment_uid for r in rows.itertuples()
               if chung.con_thong_tin_ca_nhan(r.post_text, r.parent_text, r.text_public)]
    msgs = [user_message(r, args.cat_bai_dang) for r in rows.itertuples()]
    cut = sum(1 for m in msgs if "[…đã cắt]" in m)
    chars_sys, chars_user = len(SYSTEM), sum(len(m) for m in msgs)
    tpc = args.ky_tu_moi_token
    sys_tok, user_tok = chars_sys / tpc, chars_user / tpc
    out_tok = args.uoc_token_ra
    n = len(rows)
    print(f"Prompt {PROMPT_VERSION} (sha {PROMPT_SHA}): {chars_sys} ký tự ≈ {sys_tok:,.0f} token")
    if TACH:
        print("  tách hướng, mỗi câu gọi 4 lần: " + ", ".join(f"{h} {len(TACH[h])} ký tự" for h in chung.HUONG_TACH))
    print(f"{n} câu; {len(blocked)} câu sẽ không gửi vì còn mẫu thông tin cá nhân; {cut} câu có bài đăng hoặc bình luận cha bị cắt ở {args.cat_bai_dang} ký tự")
    print(f"Phần riêng của mỗi câu: trung bình {chars_user / max(n, 1):,.0f} ký tự ≈ {user_tok / max(n, 1):,.0f} token")
    print(f"Ước lượng thô (≈{tpc} ký tự/token, ±50%; đếm đúng bằng count_tokens khi có khóa API), mỗi câu ≈ {out_tok} token ra (JSON + suy nghĩ):")
    for model, p in GIA.items():
        usage = {"input_tokens": user_tok, "output_tokens": out_tok * n, "cache_creation_input_tokens": sys_tok,
                 "cache_read_input_tokens": sys_tok * max(n - 1, 0)}
        print(f"  {model:18s} trực tiếp ≈ ${cost(model, usage, None, False):8.2f}   batch ≈ ${cost(model, usage, None, True):8.2f}")
    path.parent.mkdir(parents=True, exist_ok=True)
    sample = path.with_suffix(".request_mau.json")
    if TACH:
        mau = {h: {"system": f"<{len(TACH[h])} ký tự: chung.md + {h}.md>", "user": msgs[0],
                   "response_format": {"type": "json_schema", "json_schema": {"name": "nhan", "strict": True,
                                                                             "schema": chung.SCHEMA_TACH[h]}}}
               for h in chung.HUONG_TACH}
    else:
        mau = {"claude": {**claude_params(args.model, args.effort, msgs[0]), "system": f"<{chars_sys} ký tự từ {PROMPT_FILE.name}>"},
               "openai_response_format": {"type": "json_schema", "json_schema": {"name": "nhan", "strict": True, "schema": chung.SCHEMA}}}
    sample.write_text(json.dumps(mau, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Request mẫu (câu đầu tiên):", sample)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--gold", type=int, nargs="+", choices=[1, 2], help="gán các câu của gold vòng 1 và/hoặc 2")
    src.add_argument("--ds", help="file CSV có cột comment_uid")
    ap.add_argument("--nha-cung-cap", choices=["claude", "openai", "vllm", "gia_lap"], default="claude",
                    help="vllm: máy chủ vLLM tương thích OpenAI chạy mô hình mở (Kaggle/Colab), không cần khóa")
    ap.add_argument("--model", default="claude-opus-5-5")
    ap.add_argument("--prompt", default=str(chung.PROMPT_FILE),
                    help="file prompt (mặc định scripts/llm/prompt_ban5.md), hoặc thư mục prompt tách hướng "
                         "(scripts/llm/prompt_ban5_en_tach: mỗi câu gọi 4 lần, mỗi lần một hướng)")
    ap.add_argument("--khong-suy-nghi", action="store_true",
                    help="vllm/openai: tắt chế độ suy nghĩ của Qwen3 (chat_template_kwargs enable_thinking=false)")
    ap.add_argument("--base-url", help=f"openai/vllm: địa chỉ máy chủ tương thích OpenAI (vllm mặc định {VLLM_URL})")
    ap.add_argument("--bien-khoa", help="openai: tên biến môi trường chứa khóa (mặc định OPENAI_API_KEY)")
    ap.add_argument("--max-tokens", type=int, help="openai/vllm: giới hạn token trả lời (vllm mặc định 768)")
    ap.add_argument("--effort", default="medium", choices=["low", "medium", "high", "xhigh", "max"], help="Claude: độ sâu suy nghĩ")
    ap.add_argument("--khong-fallback", action="store_true", help="Claude: tắt fallbacks khi bị bộ lọc an toàn từ chối")
    ap.add_argument("--nhiet-do", type=float, help="OpenAI: temperature, chỉ đặt với mô hình nhận tham số này")
    ap.add_argument("--reasoning-effort", help="OpenAI: reasoning_effort cho mô hình suy luận")
    ap.add_argument("--gia", help="giá USD/1 triệu token 'input,output,cache_read' cho mô hình không có trong bảng GIA")
    ap.add_argument("--che-do", choices=["truc_tiep", "batch"], default="truc_tiep")
    ap.add_argument("--lay-batch", action="store_true", help="lấy kết quả batch đã gửi")
    ap.add_argument("--co-batch", type=int, default=10000, help="số câu mỗi batch")
    ap.add_argument("--luong", type=int, default=4, help="số request song song ở chế độ trực tiếp")
    ap.add_argument("--cat-bai-dang", type=int, default=1500, help="cắt bài đăng và bình luận cha dài hơn số ký tự này")
    ap.add_argument("--gioi-han", type=int, help="chỉ gán N câu đầu (thử)")
    ap.add_argument("--dung-sau-phut", type=float,
                    help="trực tiếp: sau N phút thì không gán thêm câu mới (để kịp đóng gói trước giới hạn phiên Kaggle)")
    ap.add_argument("--co-tap-test", action="store_true", help="cho phép đầu vào có câu của split test")
    ap.add_argument("--ra", help="đường dẫn file kết quả .jsonl")
    ap.add_argument("--thu", action="store_true", help="chạy thử, không gọi API")
    ap.add_argument("--ky-tu-moi-token", type=float, default=2.5, help="chạy thử: số ký tự tiếng Việt trung bình mỗi token")
    ap.add_argument("--uoc-token-ra", type=int, default=400, help="chạy thử: token ra mỗi câu (JSON khoảng 80 + suy nghĩ)")
    args = ap.parse_args()
    global PROMPT_FILE, SYSTEM, PROMPT_VERSION, PROMPT_SHA, TACH
    PROMPT_FILE = Path(args.prompt)
    if PROMPT_FILE.is_dir():  # bộ prompt tách hướng: mỗi câu gọi 4 lần
        TACH, PROMPT_VERSION, PROMPT_SHA = chung.load_prompt_tach(PROMPT_FILE)
        SYSTEM = "\n\n".join(TACH[h] for h in chung.HUONG_TACH)  # chỉ để đếm kích thước khi chạy thử
        if args.nha_cung_cap == "claude" or args.che_do == "batch":
            raise SystemExit("Prompt tách hướng hiện chỉ dùng với openai, vllm, gia_lap ở chế độ trực tiếp")
    else:
        SYSTEM, PROMPT_VERSION, PROMPT_SHA = chung.load_prompt(PROMPT_FILE)
    if args.nha_cung_cap == "vllm":
        args.base_url = args.base_url or VLLM_URL
        args.max_tokens = args.max_tokens or 768
        if args.model.startswith("claude-"):
            raise SystemExit("Với --nha-cung-cap vllm, ghi tên mô hình đã phục vụ bằng --model (ví dụ qwen2.5-7b-instruct)")
    args.gia_dict = None
    if args.gia:
        i, o, c = (float(x) for x in args.gia.split(","))
        args.gia_dict = {"input": i, "output": o, "cache_read": c, "cache_write": i}
    if args.nha_cung_cap == "claude" and not args.model.startswith("claude-"):
        raise SystemExit("--model của Claude phải bắt đầu bằng claude-")
    if args.nha_cung_cap == "openai" and args.model.startswith("claude-"):
        raise SystemExit("Với --nha-cung-cap openai, ghi rõ tên mô hình OpenAI bằng --model")
    if args.che_do == "batch" and args.nha_cung_cap != "claude":
        raise SystemExit("Chế độ batch hiện chỉ viết cho Claude")

    rows, source = load_rows(args)
    path = out_path(args, source)
    if args.thu:
        dry_run(args, rows, path)
        return
    key_name = args.bien_khoa or "OPENAI_API_KEY"
    backend = {"claude": lambda: Claude(args.model, args.effort, not args.khong_fallback),
               "openai": lambda: OpenAIChat(args.model, args.nhiet_do, args.reasoning_effort, args.base_url,
                                            os.environ.get(key_name) if args.bien_khoa else None, args.max_tokens, key_name,
                                            args.khong_suy_nghi),
               "vllm": lambda: OpenAIChat(args.model, args.nhiet_do, args.reasoning_effort, args.base_url, "EMPTY",
                                          args.max_tokens, khong_suy_nghi=args.khong_suy_nghi),
               "gia_lap": GiaLap}[args.nha_cung_cap]()
    t0 = time.time()
    if args.che_do == "batch":
        (run_batch_collect if args.lay_batch else run_batch_submit)(args, rows, path, backend)
        if not args.lay_batch:
            return
    else:
        run_direct(args, rows, path, backend)
    summarize(path, {"nha_cung_cap": args.nha_cung_cap, "model_yeu_cau": args.model, "effort": args.effort,
                     "reasoning_effort": args.reasoning_effort, "nhiet_do": args.nhiet_do,
                     "fallback": args.nha_cung_cap == "claude" and not args.khong_fallback and args.model in FALLBACK_MODELS,
                     "prompt_version": PROMPT_VERSION, "prompt_sha": PROMPT_SHA, "prompt_file": PROMPT_FILE.name,
                     "base_url": args.base_url, "max_tokens": args.max_tokens, "tach_huong": TACH is not None,
                     "khong_suy_nghi": args.khong_suy_nghi, "cat_bai_dang": args.cat_bai_dang,
                     "nguon": source, "che_do": args.che_do, "so_cau_dau_vao": len(rows),
                     "giay": round(time.time() - t0)})


if __name__ == "__main__":
    main()

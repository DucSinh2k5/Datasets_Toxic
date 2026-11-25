"""
Module xử lý ngôn ngữ tự nhiên và Vector hóa (nlp.py)
Dùng trực tiếp 100% các hàm có sẵn của các thư viện (không dùng class rườm rà):
- py_vncorenlp: py_vncorenlp.VnCoreNLP(annotators=['wseg']) -> word_segment()
- fasttext: fasttext.train_unsupervised(), fasttext.load_model(), model.get_word_vector()
- pandas & numpy: map, mean, zeros, hstack
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import fasttext
import numpy as np
import pandas as pd
from loguru import logger
from tqdm import tqdm


# =====================================================================
# 1. TÁCH TỪ TIẾNG VIỆT (DÙNG TRỰC TIẾP PY_VNCORENLP)
# =====================================================================

def get_safe_vncorenlp_dir(resource_dir: Path = Path("resources/vncorenlp")) -> str:
    """Java VNCoreNLP bị lỗi nếu đường dẫn có dấu cách. Hàm này đảm bảo thư mục không có dấu cách."""
    res_str = str(resource_dir.resolve())
    if " " not in res_str:
        return res_str

    scratch_base = Path(r"C:\Users\DELL\.gemini\antigravity\brain\42c13f5e-4d86-49b6-a16c-5e29d4ca63b7\scratch")
    if not scratch_base.is_dir():
        scratch_base = Path(tempfile.gettempdir())

    safe_target = scratch_base / "vncorenlp"
    safe_target.mkdir(parents=True, exist_ok=True)
    models_dir = safe_target / "models" / "wordsegmenter"
    models_dir.mkdir(parents=True, exist_ok=True)

    jar_src = resource_dir / "VnCoreNLP-1.2.jar"
    vocab_src = resource_dir / "models" / "wordsegmenter" / "vi-vocab"
    rdr_src = resource_dir / "models" / "wordsegmenter" / "wordsegmenter.rdr"

    if jar_src.is_file() and not (safe_target / "VnCoreNLP-1.2.jar").is_file():
        shutil.copy2(jar_src, safe_target / "VnCoreNLP-1.2.jar")
    if vocab_src.is_file() and not (models_dir / "vi-vocab").is_file():
        shutil.copy2(vocab_src, models_dir / "vi-vocab")
    if rdr_src.is_file() and not (models_dir / "wordsegmenter.rdr").is_file():
        shutil.copy2(rdr_src, models_dir / "wordsegmenter.rdr")

    return str(safe_target)


def init_vncorenlp(resource_dir: str = "resources/vncorenlp") -> Any:
    """Khởi tạo bộ tách từ VNCoreNLP dùng trực tiếp thư viện py_vncorenlp."""
    safe_dir = get_safe_vncorenlp_dir(Path(resource_dir))
    logger.info(f"Khởi tạo VNCoreNLP từ thư mục: {safe_dir}")

    orig_cwd = os.getcwd()
    try:
        import py_vncorenlp
        return py_vncorenlp.VnCoreNLP(annotators=["wseg"], save_dir=safe_dir)
    finally:
        os.chdir(orig_cwd)


def segment_text(text: Optional[str], rdrsegmenter: Any) -> str:
    """Tách từ cho 1 câu dùng trực tiếp rdrsegmenter.word_segment()."""
    if not text or not isinstance(text, str):
        return ""
    text = text.strip()
    if not text or text in {"NO_PARENT", "PARENT_MISSING", "POST_MISSING"}:
        return text

    try:
        sentences = rdrsegmenter.word_segment(text)
        if isinstance(sentences, list):
            return " ".join(sentences).strip()
        return str(sentences).strip()
    except Exception:
        return text


def segment_column(series: pd.Series, rdrsegmenter: Any, desc: str = "Tách từ") -> pd.Series:
    """Tách từ cho 1 cột DataFrame (dùng map và cache để tăng tốc)."""
    unique_texts = series.fillna("").unique()
    cache = {t: segment_text(t, rdrsegmenter) for t in tqdm(unique_texts, desc=desc)}
    return series.fillna("").map(cache)


def segment_dataframe(df: pd.DataFrame, rdrsegmenter: Any) -> pd.DataFrame:
    """Tách từ cho toàn bộ các cột văn bản trong DataFrame."""
    df_out = df.copy()

    logger.info("Đang tách từ cho cột: message_clean -> message_segmented")
    df_out["message_segmented"] = segment_column(df_out["message_clean"], rdrsegmenter, desc="Bình luận")

    if "post_clean" in df_out.columns:
        logger.info("Đang tách từ cho cột: post_clean -> post_segmented")
        df_out["post_segmented"] = segment_column(df_out["post_clean"], rdrsegmenter, desc="Bài đăng")

    if "parent_clean" in df_out.columns:
        logger.info("Đang tách từ cho cột: parent_clean -> parent_segmented")
        df_out["parent_segmented"] = segment_column(df_out["parent_clean"], rdrsegmenter, desc="Bình luận cha")

    return df_out


# =====================================================================
# 2. VECTOR HÓA BẰNG FASTTEXT (DÙNG TRỰC TIẾP FASTTEXT)
# =====================================================================

def train_fasttext_model(
    corpus_texts: List[str],
    model_save_path: str = "artifacts/embeddings/fasttext_model.bin",
    dim: int = 100,
    epoch: int = 25,
    lr: float = 0.05,
    minn: int = 2,
    maxn: int = 5
) -> Any:
    """Huấn luyện mô hình FastText dùng trực tiếp hàm fasttext.train_unsupervised."""
    out_path = Path(model_save_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, suffix=".txt") as tmp:
        tmp_path = tmp.name
        for line in corpus_texts:
            t = str(line).strip()
            if t and t not in {"NO_PARENT", "PARENT_MISSING", "POST_MISSING"}:
                tmp.write(t + "\n")

    try:
        logger.info(f"Bắt đầu train FastText dim={dim}, epoch={epoch}...")
        model = fasttext.train_unsupervised(
            input=tmp_path,
            model="skipgram",
            dim=dim,
            epoch=epoch,
            lr=lr,
            minn=minn,
            maxn=maxn,
        )
        model.save_model(str(out_path))
        logger.info(f"Đã lưu mô hình FastText vào: {out_path}")
        return model
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def load_fasttext_model(model_path: str = "artifacts/embeddings/fasttext_model.bin") -> Any:
    """Nạp mô hình FastText dùng trực tiếp fasttext.load_model."""
    p = Path(model_path)
    if not p.is_file():
        raise FileNotFoundError(f"Không tìm thấy mô hình FastText tại: {p}")
    logger.info(f"Đã nạp mô hình FastText từ: {p}")
    return fasttext.load_model(str(p))


def get_sentence_vector(
    model: Any,
    text: Optional[str],
    dim: int = 100,
    pooling: str = "mean_max"
) -> np.ndarray:
    """
    Tính vector câu từ vector các từ của FastText:
    - "mean": Trung bình cộng đơn thuần (dim chiều).
    - "mean_max": Kết hợp trung bình cộng và giá trị cực đại [Mean ; Max] (2*dim chiều).
      Giữ lại xung lực mạnh nhất của các từ khóa độc hại, tránh bị loãng nghĩa.
    """
    out_dim = dim * 2 if pooling == "mean_max" else dim
    if not text or not isinstance(text, str):
        return np.zeros(out_dim, dtype=np.float32)

    tokens = text.strip().split()
    if not tokens or text in {"NO_PARENT", "PARENT_MISSING", "POST_MISSING"}:
        return np.zeros(out_dim, dtype=np.float32)

    word_vectors = [model.get_word_vector(w) for w in tokens]
    if pooling == "mean_max":
        mean_v = np.mean(word_vectors, axis=0)
        max_v = np.max(word_vectors, axis=0)
        return np.hstack([mean_v, max_v]).astype(np.float32)

    return np.mean(word_vectors, axis=0).astype(np.float32)


def extract_features(
    model: Any,
    df: pd.DataFrame,
    mode: str = "comment_only",
    dim: int = 100,
    pooling: str = "mean_max",
    label_col: str = "label"
) -> Tuple[np.ndarray, np.ndarray]:
    """Trích xuất ma trận đặc trưng X và vector nhãn y từ DataFrame."""
    msg_vecs = np.array(
        [get_sentence_vector(model, t, dim, pooling=pooling) for t in df["message_segmented"]],
        dtype=np.float32
    )

    if mode == "comment_only":
        X = msg_vecs
    else:
        post_vecs = np.array(
            [get_sentence_vector(model, t, dim, pooling=pooling) for t in df.get("post_segmented", [])],
            dtype=np.float32
        )
        parent_vecs = np.array(
            [get_sentence_vector(model, t, dim, pooling=pooling) for t in df.get("parent_segmented", [])],
            dtype=np.float32
        )
        X = np.hstack([post_vecs, parent_vecs, msg_vecs])

    actual_label_col = label_col if label_col in df.columns else "label"
    y = df[actual_label_col].values.astype(int)
    return X, y

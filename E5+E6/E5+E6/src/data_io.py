"""
Module quản lý dữ liệu toàn diện (data_io.py)
Dùng trực tiếp 100% các hàm có sẵn của các thư viện chuẩn (không dùng class rườm rà):
- pandas: pd.read_excel, df.to_excel (đọc và lưu file Excel)
- numpy: np.savez_compressed, np.load (lưu và nạp mảng vector nén .npz)
- joblib: joblib.dump, joblib.load (lưu và nạp mô hình .pkl)
- json: json.dump, json.load (lưu và nạp tệp chỉ số .json)
- yaml: yaml.safe_load (đọc cấu hình YAML)
- unicodedata: unicodedata.normalize (chuẩn hóa tiếng Việt NFC)
"""

import json
import unicodedata
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import joblib
import numpy as np
import pandas as pd
import yaml
from loguru import logger


# =====================================================================
# 1. CẤU HÌNH HỆ THỐNG
# =====================================================================

class SystemConfig:
    """Class chứa cấu hình từ file YAML để gọi theo dạng config.paths, config.columns."""

    def __init__(self, cfg: Dict[str, Any]):
        self._cfg = cfg
        self.paths = cfg.get("paths", {})
        self.columns = cfg.get("columns", {})
        self.prediction_input_mode = cfg.get("prediction_input_mode", "comment_only")
        self.fasttext_cfg = cfg.get("fasttext", {})
        self.e5_cfg = cfg.get("e5_gaussian_nb", {})
        self.e6_cfg = cfg.get("e6_linear_svm", {})

    def __getitem__(self, item: str) -> Any:
        return self._cfg[item]

    def get(self, key: str, default: Any = None) -> Any:
        return self._cfg.get(key, default)


def load_config(config_path: str = "config/system_config.yaml") -> SystemConfig:
    """Đọc file cấu hình YAML dùng trực tiếp yaml.safe_load có sẵn."""
    path = Path(config_path)
    if not path.is_file():
        raise FileNotFoundError(f"Không tìm thấy file cấu hình tại: {config_path}")

    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    return SystemConfig(cfg)


# =====================================================================
# 2. CÁC HÀM XỬ LÝ VĂN BẢN VÀ ĐỌC/GHI TỆP (DÙNG TRỰC TIẾP THƯ VIỆN)
# =====================================================================

def clean_text_field(val: any) -> str:
    """Làm sạch ký tự: Chuẩn hóa Unicode NFC có sẵn của Python, xóa khoảng trắng thừa."""
    if pd.isna(val) or val is None:
        return ""
    text = str(val).strip()
    if text.lower() in {"nan", "none", "null", "."}:
        return ""
    text = unicodedata.normalize("NFC", text)
    text = " ".join(text.split())
    return text


def read_excel(file_path: str) -> pd.DataFrame:
    """Đọc file Excel dùng trực tiếp hàm pd.read_excel của Pandas."""
    p = Path(file_path)
    if not p.is_file():
        raise FileNotFoundError(f"Không tìm thấy file Excel: {file_path}")
    logger.info(f"Đọc Excel: {file_path}")
    return pd.read_excel(p, engine="openpyxl")


def save_excel(df: pd.DataFrame, file_path: str) -> str:
    """Lưu DataFrame ra file Excel dùng trực tiếp hàm df.to_excel của Pandas."""
    p = Path(file_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Lưu Excel ({len(df)} dòng): {file_path}")
    df.to_excel(p, index=False, engine="openpyxl")
    return str(p)


def save_vectors(file_path: str, features: np.ndarray, labels: np.ndarray, mode: str = "comment_only") -> str:
    """Lưu ma trận đặc trưng và nhãn dùng trực tiếp np.savez_compressed của NumPy."""
    p = Path(file_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(p, features=features, labels=labels, mode=mode)
    logger.info(f"Đã lưu vector nén {features.shape} vào: {file_path}")
    return str(p)


def load_vectors(file_path: str) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    """Nạp ma trận đặc trưng và nhãn dùng trực tiếp np.load của NumPy."""
    p = Path(file_path)
    if not p.is_file():
        raise FileNotFoundError(f"Không tìm thấy file vector: {file_path}")
    data = np.load(p, allow_pickle=True)
    features = data["features"]
    labels = data["labels"]
    mode = str(data["mode"]) if "mode" in data else "comment_only"
    logger.info(f"Đã nạp vector {features.shape} từ: {file_path}")
    return features, labels, {"mode": mode}


def save_model(file_path: str, model_payload: Any) -> str:
    """Lưu mô hình học máy dùng trực tiếp joblib.dump của Joblib."""
    p = Path(file_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model_payload, p)
    logger.info(f"Đã lưu mô hình vào: {file_path}")
    return str(p)


def load_model(file_path: str) -> Any:
    """Nạp mô hình học máy dùng trực tiếp joblib.load của Joblib."""
    p = Path(file_path)
    if not p.is_file():
        raise FileNotFoundError(f"Không tìm thấy file mô hình: {file_path}")
    logger.info(f"Đã nạp mô hình từ: {file_path}")
    return joblib.load(p)


def save_json(file_path: str, data: Dict[str, Any]) -> str:
    """Lưu từ điển chỉ số ra file JSON dùng trực tiếp json.dump của Python."""
    p = Path(file_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"Đã lưu JSON vào: {file_path}")
    return str(p)


def load_json(file_path: str) -> Dict[str, Any]:
    """Nạp tệp JSON dùng trực tiếp json.load của Python."""
    p = Path(file_path)
    if not p.is_file():
        raise FileNotFoundError(f"Không tìm thấy file JSON: {file_path}")
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

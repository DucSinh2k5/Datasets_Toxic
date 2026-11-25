"""
Module mô hình học máy (models.py)
Dùng trực tiếp 100% các mô hình có sẵn của scikit-learn (hoàn toàn không dùng class):
1. GaussianNB (Gaussian Naive Bayes - Mô hình E5)
2. LinearSVC (Linear Support Vector Machine - Mô hình E6)
"""

from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import numpy as np
import pandas as pd
from loguru import logger
from sklearn.naive_bayes import GaussianNB
from sklearn.svm import LinearSVC
from sklearn.metrics import f1_score

from src.data_io import SystemConfig, save_model
from src.evaluation import evaluate_and_export


# =====================================================================
# 1. MÔ HÌNH E5: FASTTEXT + GAUSSIAN NAIVE BAYES (sklearn.naive_bayes.GaussianNB)
# =====================================================================

def train_e5_gaussian_nb(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    config: Optional[SystemConfig] = None
) -> Tuple[GaussianNB, float, Dict[str, Any]]:
    """
    Huấn luyện mô hình GaussianNB có sẵn của scikit-learn.
    Dò tìm tham số var_smoothing và ngưỡng tau tốt nhất trên tập Val để tối ưu Toxic F1.
    """
    var_smoothing_list = [1e-9, 1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 1e-2, 1e-1]
    threshold_list = np.linspace(0.05, 0.95, 91)

    logger.info("[E5 GaussianNB] Đang dùng mô hình GaussianNB của sklearn để tìm tham số tối ưu...")

    best_f1 = -1.0
    best_vs = 1e-9
    best_th = 0.5
    best_model = None

    for vs in var_smoothing_list:
        # Gọi trực tiếp GaussianNB có sẵn của sklearn
        clf = GaussianNB(var_smoothing=vs)
        clf.fit(X_train, y_train)

        # Dự đoán xác suất lớp Toxic (nhãn 1) trên tập Val
        val_probs = clf.predict_proba(X_val)[:, 1]

        # Quét ngưỡng tau để tìm F1 lớp Toxic cao nhất
        for th in threshold_list:
            val_preds = (val_probs >= th).astype(int)
            score = f1_score(y_val, val_preds, pos_label=1, zero_division=0)
            if score > best_f1:
                best_f1 = score
                best_vs = vs
                best_th = float(th)
                best_model = clf

    logger.info(
        f"[E5 GaussianNB] Hoàn tất! var_smoothing={best_vs}, "
        f"ngưỡng tau={best_th:.2f}, Toxic F1 trên Val={best_f1:.4f}"
    )

    tune_info = {
        "best_var_smoothing": best_vs,
        "best_threshold": best_th,
        "best_val_toxic_f1": round(best_f1, 4),
    }

    if config is not None:
        save_path = config.paths["artifacts"]["e5_model"]
        save_model(save_path, {
            "model": best_model,
            "var_smoothing": best_vs,
            "threshold": best_th,
            "val_f1": best_f1,
        })

    return best_model, best_th, tune_info


def predict_e5(model: GaussianNB, threshold: float, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Dự đoán nhãn (0/1) và xác suất bằng mô hình E5 GaussianNB."""
    probs = model.predict_proba(X)[:, 1]
    preds = (probs >= threshold).astype(int)
    return preds, probs


# =====================================================================
# 2. MÔ HÌNH E6: FASTTEXT + LINEAR SVM (sklearn.svm.LinearSVC)
# =====================================================================

def train_e6_linear_svm(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    config: Optional[SystemConfig] = None
) -> Tuple[LinearSVC, float, Dict[str, Any]]:
    """
    Huấn luyện mô hình LinearSVC có sẵn của scikit-learn.
    Dò tìm hệ số phạt C, class_weight và ngưỡng tau tốt nhất trên tập Val để tối ưu Toxic F1.
    """
    c_list = [0.01, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0]
    class_weight_list = [None, "balanced", {0: 1.0, 1: 1.2}, {0: 1.0, 1: 1.5}, {0: 1.0, 1: 1.8}, {0: 1.0, 1: 2.0}]

    logger.info("[E6 Linear SVM] Đang dùng mô hình LinearSVC của sklearn để tìm tham số tối ưu...")

    best_f1 = -1.0
    best_c = 1.0
    best_cw = None
    best_th = 0.0
    best_model = None

    for c in c_list:
        for cw in class_weight_list:
            # Gọi trực tiếp LinearSVC có sẵn của sklearn
            clf = LinearSVC(C=c, class_weight=cw, max_iter=3000, random_state=42, dual=False)
            clf.fit(X_train, y_train)

            # Lấy điểm khoảng cách decision function trên tập Val
            val_scores = clf.decision_function(X_val)
            p5, p95 = np.percentile(val_scores, [5, 95])
            candidate_thresholds = np.linspace(p5, p95, 51)

            # Quét ngưỡng tau để tìm F1 lớp Toxic cao nhất
            for th in candidate_thresholds:
                val_preds = (val_scores >= th).astype(int)
                score = f1_score(y_val, val_preds, pos_label=1, zero_division=0)
                if score > best_f1:
                    best_f1 = score
                    best_c = c
                    best_cw = cw
                    best_th = float(th)
                    best_model = clf

    logger.info(
        f"[E6 Linear SVM] Hoàn tất! C={best_c}, class_weight={best_cw}, "
        f"ngưỡng tau={best_th:.4f}, Toxic F1 trên Val={best_f1:.4f}"
    )

    tune_info = {
        "best_C": best_c,
        "best_class_weight": best_cw,
        "best_threshold": round(best_th, 4),
        "best_val_toxic_f1": round(best_f1, 4),
    }

    if config is not None:
        save_path = config.paths["artifacts"]["e6_model"]
        save_model(save_path, {
            "model": best_model,
            "C": best_c,
            "class_weight": best_cw,
            "threshold": best_th,
            "val_f1": best_f1,
        })

    return best_model, best_th, tune_info


def predict_e6(model: LinearSVC, threshold: float, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Dự đoán nhãn (0/1) và điểm số khoảng cách bằng mô hình E6 Linear SVM."""
    scores = model.decision_function(X)
    preds = (scores >= threshold).astype(int)
    return preds, scores


# =====================================================================
# 3. HÀM ĐÁNH GIÁ VÀ XUẤT KẾT QUẢ CHO MÔ HÌNH
# =====================================================================

def evaluate_model_split(
    model_name: str,
    split_name: str,
    preds: np.ndarray,
    scores: np.ndarray,
    y_true: np.ndarray,
    df_source: pd.DataFrame,
    config: Optional[SystemConfig] = None
) -> Tuple[Dict[str, Any], pd.DataFrame]:
    """Hàm đánh giá các chỉ số và xuất file Excel dự đoán chi tiết."""
    return evaluate_and_export(
        model_name=model_name,
        split=split_name,
        df_source=df_source,
        y_true=y_true,
        y_pred=preds,
        y_scores=scores,
        config=config
    )

"""
Module đánh giá, so sánh và trực quan hóa (evaluation.py)
Dùng trực tiếp 100% các hàm có sẵn của các thư viện (hoàn toàn không dùng class):
- sklearn.metrics: confusion_matrix, f1_score, recall_score, precision_score, accuracy_score, precision_recall_curve, auc
- numpy: np.select (phân loại lỗi vector hóa), np.array
- pandas: pd.ExcelWriter, to_excel
- matplotlib & seaborn: sns.heatmap, sns.barplot, plt.subplots
"""

from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from loguru import logger
from sklearn.metrics import (
    accuracy_score,
    auc,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
)

from src.data_io import SystemConfig, save_json

plt.rcParams["font.sans-serif"] = "DejaVu Sans"
plt.rcParams["font.size"] = 11


# =====================================================================
# 1. HÀM TÍNH CHỈ SỐ ĐÁNH GIÁ (DÙNG TRỰC TIẾP SKLEARN.METRICS & NUMPY)
# =====================================================================

def compute_error_type(y_true: int, y_pred: int) -> str:
    """Phân loại kết quả dự đoán đơn lẻ thành TP, TN, FP, FN."""
    if y_true == 1 and y_pred == 1:
        return "TP"
    elif y_true == 0 and y_pred == 0:
        return "TN"
    elif y_true == 0 and y_pred == 1:
        return "FP"
    elif y_true == 1 and y_pred == 0:
        return "FN"
    return "UNKNOWN"


def compute_error_types(y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
    """Phân loại toàn bộ mảng dự đoán thành TP, TN, FP, FN bằng hàm có sẵn np.select của NumPy."""
    conds = [
        (y_true == 1) & (y_pred == 1),
        (y_true == 0) & (y_pred == 0),
        (y_true == 0) & (y_pred == 1),
        (y_true == 1) & (y_pred == 0)
    ]
    choices = ["TP", "TN", "FP", "FN"]
    return np.select(conds, choices, default="UNKNOWN")


def compute_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_scores: Optional[np.ndarray] = None
) -> Dict[str, Any]:
    """Tính toàn bộ các chỉ số dùng trực tiếp các hàm có sẵn của sklearn.metrics."""
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()

    toxic_f1 = float(f1_score(y_true, y_pred, pos_label=1, zero_division=0))
    toxic_recall = float(recall_score(y_true, y_pred, pos_label=1, zero_division=0))
    toxic_precision = float(precision_score(y_true, y_pred, pos_label=1, zero_division=0))
    macro_f1 = float(f1_score(y_true, y_pred, average="macro", zero_division=0))
    accuracy = float(accuracy_score(y_true, y_pred))

    pr_auc = None
    if y_scores is not None:
        try:
            precisions, recalls, _ = precision_recall_curve(y_true, y_scores, pos_label=1)
            pr_auc = float(auc(recalls, precisions))
        except Exception:
            pass

    return {
        "toxic_f1": round(toxic_f1, 4),
        "toxic_recall": round(toxic_recall, 4),
        "toxic_precision": round(toxic_precision, 4),
        "macro_f1": round(macro_f1, 4),
        "accuracy": round(accuracy, 4),
        "pr_auc": round(pr_auc, 4) if pr_auc is not None else None,
        "confusion_matrix": {
            "TP": int(tp),
            "TN": int(tn),
            "FP": int(fp),
            "FN": int(fn),
        },
        "total_samples": int(len(y_true)),
        "toxic_samples": int(np.sum(y_true == 1)),
        "non_toxic_samples": int(np.sum(y_true == 0)),
    }


def generate_prediction_dataframe(
    df_original: pd.DataFrame,
    y_pred: np.ndarray,
    y_scores: Optional[np.ndarray] = None,
    label_col: str = "label"
) -> pd.DataFrame:
    """Ghép các cột dự đoán (pred_label, pred_score, error_type) vào DataFrame gốc."""
    df_pred = df_original.copy()
    df_pred["pred_label"] = y_pred
    df_pred["pred_score"] = np.round(y_scores, 4) if y_scores is not None else y_pred

    actual_col = label_col if label_col in df_pred.columns else "label"
    if actual_col in df_pred.columns:
        y_true = df_pred[actual_col].values
        df_pred["error_type"] = compute_error_types(y_true, y_pred)
    return df_pred


def evaluate_and_export(
    model_name: str,
    split: str,
    df_source: pd.DataFrame,
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_scores: Optional[np.ndarray] = None,
    config: Optional[SystemConfig] = None
) -> Tuple[Dict[str, Any], pd.DataFrame]:
    """Tính toàn bộ chỉ số, lưu file metrics JSON và file Excel dự đoán."""
    metrics = compute_metrics(y_true, y_pred, y_scores)
    logger.info(
        f"[{model_name.upper()} - {split.upper()}] "
        f"Toxic F1={metrics['toxic_f1']:.4f}, Recall={metrics['toxic_recall']:.4f}, "
        f"Precision={metrics['toxic_precision']:.4f}, Macro-F1={metrics['macro_f1']:.4f}"
    )

    label_col = config.columns.get("label_column", "label") if config else "label"
    df_pred = generate_prediction_dataframe(df_source, y_pred, y_scores, label_col=label_col)

    if config is not None:
        metrics_key = f"{model_name}_{split}_metrics"
        metrics_path = config.paths["results"][metrics_key]
        save_json(metrics_path, metrics)

        if split == "test":
            pred_key = f"{model_name}_predictions"
            pred_path = Path(config.paths["results"][pred_key])
            pred_path.parent.mkdir(parents=True, exist_ok=True)
            df_pred.to_excel(pred_path, index=False, engine="openpyxl")
            logger.info(f"Đã xuất bảng dự đoán chi tiết: {pred_path}")

    return metrics, df_pred


# =====================================================================
# 2. HÀM SO SÁNH ĐỐI CHIẾU E5 VÀ E6 (XUẤT EXCEL 3 SHEET)
# =====================================================================

def generate_comparison_report(
    e5_val_metrics: Dict[str, Any],
    e5_test_metrics: Dict[str, Any],
    e6_val_metrics: Dict[str, Any],
    e6_test_metrics: Dict[str, Any],
    df_e5_pred: pd.DataFrame,
    df_e6_pred: pd.DataFrame,
    output_path: str = "results/comparison/e5_vs_e6_comparison_report.xlsx"
) -> str:
    """Xuất file Excel gồm 3 sheet bằng pd.ExcelWriter có sẵn của Pandas."""
    report_path = Path(output_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Đang tạo báo cáo đối chiếu E5 vs E6 tại: {report_path}")

    summary_rows = [
        {
            "Mô hình": "E5 (fastText + GaussianNB)",
            "Tập dữ liệu": "Validation",
            "Toxic F1": e5_val_metrics["toxic_f1"],
            "Toxic Recall": e5_val_metrics["toxic_recall"],
            "Toxic Precision": e5_val_metrics["toxic_precision"],
            "Macro F1": e5_val_metrics["macro_f1"],
            "Accuracy": e5_val_metrics["accuracy"],
            "PR-AUC": e5_val_metrics.get("pr_auc"),
            "TP": e5_val_metrics["confusion_matrix"]["TP"],
            "TN": e5_val_metrics["confusion_matrix"]["TN"],
            "FP": e5_val_metrics["confusion_matrix"]["FP"],
            "FN": e5_val_metrics["confusion_matrix"]["FN"],
        },
        {
            "Mô hình": "E5 (fastText + GaussianNB)",
            "Tập dữ liệu": "Test (Khóa)",
            "Toxic F1": e5_test_metrics["toxic_f1"],
            "Toxic Recall": e5_test_metrics["toxic_recall"],
            "Toxic Precision": e5_test_metrics["toxic_precision"],
            "Macro F1": e5_test_metrics["macro_f1"],
            "Accuracy": e5_test_metrics["accuracy"],
            "PR-AUC": e5_test_metrics.get("pr_auc"),
            "TP": e5_test_metrics["confusion_matrix"]["TP"],
            "TN": e5_test_metrics["confusion_matrix"]["TN"],
            "FP": e5_test_metrics["confusion_matrix"]["FP"],
            "FN": e5_test_metrics["confusion_matrix"]["FN"],
        },
        {
            "Mô hình": "E6 (fastText + Linear SVM)",
            "Tập dữ liệu": "Validation",
            "Toxic F1": e6_val_metrics["toxic_f1"],
            "Toxic Recall": e6_val_metrics["toxic_recall"],
            "Toxic Precision": e6_val_metrics["toxic_precision"],
            "Macro F1": e6_val_metrics["macro_f1"],
            "Accuracy": e6_val_metrics["accuracy"],
            "PR-AUC": e6_val_metrics.get("pr_auc"),
            "TP": e6_val_metrics["confusion_matrix"]["TP"],
            "TN": e6_val_metrics["confusion_matrix"]["TN"],
            "FP": e6_val_metrics["confusion_matrix"]["FP"],
            "FN": e6_val_metrics["confusion_matrix"]["FN"],
        },
        {
            "Mô hình": "E6 (fastText + Linear SVM)",
            "Tập dữ liệu": "Test (Khóa)",
            "Toxic F1": e6_test_metrics["toxic_f1"],
            "Toxic Recall": e6_test_metrics["toxic_recall"],
            "Toxic Precision": e6_test_metrics["toxic_precision"],
            "Macro F1": e6_test_metrics["macro_f1"],
            "Accuracy": e6_test_metrics["accuracy"],
            "PR-AUC": e6_test_metrics.get("pr_auc"),
            "TP": e6_test_metrics["confusion_matrix"]["TP"],
            "TN": e6_test_metrics["confusion_matrix"]["TN"],
            "FP": e6_test_metrics["confusion_matrix"]["FP"],
            "FN": e6_test_metrics["confusion_matrix"]["FN"],
        },
    ]
    df_summary = pd.DataFrame(summary_rows)

    analysis_data = []
    for model_name, df_p in [("E5 (GaussianNB)", df_e5_pred), ("E6 (Linear SVM)", df_e6_pred)]:
        total_samples = len(df_p)
        errors = df_p[df_p["error_type"].isin(["FP", "FN"])]

        analysis_data.append({
            "Model": model_name,
            "Subgroup": "Toàn bộ tập Test",
            "Tổng số mẫu": total_samples,
            "Số mẫu sai": len(errors),
            "Error Rate (%)": round(len(errors) / total_samples * 100, 2),
        })

        if "comment_type" in df_p.columns:
            for c_type in ["top_level", "reply"]:
                sub = df_p[df_p["comment_type"] == c_type]
                if len(sub) > 0:
                    sub_err = sub[sub["error_type"].isin(["FP", "FN"])]
                    analysis_data.append({
                        "Model": model_name,
                        "Subgroup": f"comment_type = '{c_type}'",
                        "Tổng số mẫu": len(sub),
                        "Số mẫu sai": len(sub_err),
                        "Error Rate (%)": round(len(sub_err) / len(sub) * 100, 2),
                    })

        if "parent_clean" in df_p.columns:
            has_p = df_p[df_p["parent_clean"].fillna("").str.strip() != ""]
            no_p = df_p[df_p["parent_clean"].fillna("").str.strip() == ""]
            if len(has_p) > 0:
                err_has = has_p[has_p["error_type"].isin(["FP", "FN"])]
                analysis_data.append({
                    "Model": model_name,
                    "Subgroup": "Có ngữ cảnh bình luận cha (parent_clean != '')",
                    "Tổng số mẫu": len(has_p),
                    "Số mẫu sai": len(err_has),
                    "Error Rate (%)": round(len(err_has) / len(has_p) * 100, 2),
                })
            if len(no_p) > 0:
                err_no = no_p[no_p["error_type"].isin(["FP", "FN"])]
                analysis_data.append({
                    "Model": model_name,
                    "Subgroup": "Không có bình luận cha (parent_clean == '')",
                    "Tổng số mẫu": len(no_p),
                    "Số mẫu sai": len(err_no),
                    "Error Rate (%)": round(len(err_no) / len(no_p) * 100, 2),
                })

    df_context = pd.DataFrame(analysis_data)

    df_disagree = df_e5_pred.copy()
    df_disagree["e5_pred"] = df_e5_pred["pred_label"]
    df_disagree["e6_pred"] = df_e6_pred["pred_label"]
    df_disagree["e5_error"] = df_e5_pred["error_type"]
    df_disagree["e6_error"] = df_e6_pred["error_type"]

    df_samples = df_disagree[(df_disagree["e5_error"] != "TP") & (df_disagree["e5_error"] != "TN") |
                             (df_disagree["e6_error"] != "TP") & (df_disagree["e6_error"] != "TN")].copy()

    with pd.ExcelWriter(report_path, engine="openpyxl") as writer:
        df_summary.to_excel(writer, sheet_name="Metrics_Summary", index=False)
        df_context.to_excel(writer, sheet_name="Context_Error_Analysis", index=False)
        df_samples.to_excel(writer, sheet_name="Error_Samples_E5_vs_E6", index=False)

    logger.info(f"Đã xuất báo cáo đối chiếu 3 sheet ra: {report_path}")
    return str(report_path)


# =====================================================================
# 3. CÁC HÀM TRỰC QUAN HÓA BIỂU ĐỒ (DÙNG TRỰC TIẾP SEABORN & MATPLOTLIB)
# =====================================================================

def plot_metrics_comparison(
    e5_metrics: Dict[str, Any],
    e6_metrics: Dict[str, Any],
    split: str = "Test",
    output_dir: str = "results/comparison/figures",
    save_name: str = "metrics_comparison.png"
) -> str:
    """Vẽ biểu đồ cột nhóm so sánh các chỉ số giữa E5 và E6."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    keys = ["toxic_f1", "toxic_recall", "toxic_precision", "macro_f1", "accuracy", "pr_auc"]
    labels = ["Toxic F1", "Toxic Recall", "Toxic Precision", "Macro-F1", "Accuracy", "PR-AUC"]

    e5_vals = [e5_metrics.get(k, 0) or 0 for k in keys]
    e6_vals = [e6_metrics.get(k, 0) or 0 for k in keys]

    x = np.arange(len(labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=300)
    r1 = ax.bar(x - width / 2, e5_vals, width, label="E5 (fastText + GaussianNB)", color="#4A90E2")
    r2 = ax.bar(x + width / 2, e6_vals, width, label="E6 (fastText + Linear SVM)", color="#E94E77")

    ax.set_ylabel("Điểm số", fontsize=12, fontweight="bold")
    ax.set_title(f"So sánh các chỉ số hiệu năng trên tập {split.upper()}", fontsize=13, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10, fontweight="bold")
    ax.set_ylim(0, 1.05)
    ax.legend(loc="lower right")

    for rects in [r1, r2]:
        for rect in rects:
            h = rect.get_height()
            ax.annotate(f"{h:.4f}", xy=(rect.get_x() + rect.get_width() / 2, h),
                        xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=8.5, fontweight="bold")

    plt.tight_layout()
    out_path = out_dir / save_name
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return str(out_path)


def plot_confusion_matrices(
    e5_cm: Dict[str, int],
    e6_cm: Dict[str, int],
    output_dir: str = "results/comparison/figures",
    save_name: str = "confusion_matrices.png"
) -> str:
    """
    Vẽ heatmap ma trận nhầm lẫn cho E5 và E6 bằng sns.heatmap.
    Chuẩn hóa phần trăm theo từng lớp thực tế (Row-normalized):
    - Hàng 1 (Toxic thực tế): chia cho chính tổng (TP + FN)
    - Hàng 2 (Non-toxic thực tế): chia cho chính tổng (FP + TN)
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5), dpi=300)
    models = [
        ("E5: fastText + GaussianNB", e5_cm, axes[0], "Blues"),
        ("E6: fastText + Linear SVM", e6_cm, axes[1], "Purples"),
    ]

    for title, cm, ax, cmap in models:
        tp, tn, fp, fn = cm["TP"], cm["TN"], cm["FP"], cm["FN"]
        tot_toxic = tp + fn
        tot_non = fp + tn

        cm_arr = np.array([[tp, fn], [fp, tn]])

        pct_tp = (tp / tot_toxic * 100) if tot_toxic > 0 else 0
        pct_fn = (fn / tot_toxic * 100) if tot_toxic > 0 else 0
        pct_fp = (fp / tot_non * 100) if tot_non > 0 else 0
        pct_tn = (tn / tot_non * 100) if tot_non > 0 else 0

        annot = [
            [f"TP (Đúng)\n{tp}\n({pct_tp:.1f}%)", f"FN (Bỏ sót)\n{fn}\n({pct_fn:.1f}%)"],
            [f"FP (Nhầm)\n{fp}\n({pct_fp:.1f}%)", f"TN (Đúng)\n{tn}\n({pct_tn:.1f}%)"]
        ]

        sns.heatmap(
            cm_arr, annot=np.array(annot), fmt="", cmap=cmap, cbar=False, ax=ax,
            annot_kws={"fontsize": 11, "fontweight": "bold"},
            xticklabels=["Dự đoán Toxic (1)", "Dự đoán Non-toxic (0)"],
            yticklabels=["Thực tế Toxic (1)", "Thực tế Non-toxic (0)"]
        )
        ax.set_title(title, fontsize=12, fontweight="bold")

    fig.suptitle("Ma trận nhầm lẫn — Chuẩn hóa phần trăm theo từng lớp thực tế", fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()
    out_path = out_dir / save_name
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return str(out_path)


def plot_precision_recall_curves(
    y_test: np.ndarray,
    e5_scores: np.ndarray,
    e6_scores: np.ndarray,
    output_dir: str = "results/comparison/figures",
    save_name: str = "precision_recall_curves.png"
) -> str:
    """Vẽ đường cong Precision-Recall đánh đổi giữa độ chuẩn xác và độ bao phủ."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(7.5, 5.5), dpi=300)

    p5, r5, _ = precision_recall_curve(y_test, e5_scores, pos_label=1)
    auc5 = auc(r5, p5)
    ax.plot(r5, p5, label=f"E5 (GaussianNB) — PR-AUC: {auc5:.4f}", color="#4A90E2", lw=2.5)

    p6, r6, _ = precision_recall_curve(y_test, e6_scores, pos_label=1)
    auc6 = auc(r6, p6)
    ax.plot(r6, p6, label=f"E6 (Linear SVM) — PR-AUC: {auc6:.4f}", color="#E94E77", lw=2.5)

    baseline = np.sum(y_test == 1) / len(y_test)
    ax.axhline(baseline, color="gray", linestyle="--", label=f"Tỷ lệ Toxic ngẫu nhiên: {baseline:.4f}")

    ax.set_xlabel("Recall (Độ nhạy)", fontsize=11, fontweight="bold")
    ax.set_ylabel("Precision (Độ chuẩn xác)", fontsize=11, fontweight="bold")
    ax.set_title("Đường cong Precision-Recall trên tập Test", fontsize=13, fontweight="bold")
    ax.set_xlim([0.0, 1.02])
    ax.set_ylim([0.0, 1.05])
    ax.legend(loc="upper right")

    plt.tight_layout()
    out_path = out_dir / save_name
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return str(out_path)


def plot_context_error_analysis(
    df_context_summary: pd.DataFrame,
    output_dir: str = "results/comparison/figures",
    save_name: str = "context_error_analysis.png"
) -> str:
    """Vẽ biểu đồ cột so sánh tỷ lệ lỗi dự đoán sai giữa các nhóm ngữ cảnh bằng sns.barplot."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(9, 5.5), dpi=300)

    sns.barplot(
        data=df_context_summary,
        x="Subgroup",
        y="Error Rate (%)",
        hue="Model",
        palette={"E5 (GaussianNB)": "#4A90E2", "E6 (Linear SVM)": "#E94E77"},
        ax=ax
    )

    ax.set_ylabel("Tỷ lệ dự đoán sai (%)", fontsize=11, fontweight="bold")
    ax.set_xlabel("")
    ax.set_title("So sánh tỷ lệ sai sót theo nhóm ngữ cảnh (Context Error Analysis)", fontsize=13, fontweight="bold")
    ax.tick_params(axis="x", rotation=15)
    ax.legend(loc="upper right")

    for p in ax.patches:
        h = p.get_height()
        if h > 0:
            ax.annotate(f"{h:.1f}%", xy=(p.get_x() + p.get_width() / 2, h),
                        xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=8.5, fontweight="bold")

    plt.tight_layout()
    out_path = out_dir / save_name
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return str(out_path)


def generate_full_dashboard(
    e5_metrics: Dict[str, Any],
    e6_metrics: Dict[str, Any],
    y_test: np.ndarray,
    e5_scores: np.ndarray,
    e6_scores: np.ndarray,
    output_dir: str = "results/comparison/figures",
    save_name: str = "e5_vs_e6_summary_dashboard.png"
) -> str:
    """Ghép 4 đồ thị thành 1 Dashboard lớn phục vụ báo cáo."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(2, 2, figsize=(15, 11), dpi=300)

    # Panel A: Biểu đồ cột chỉ số
    ax1 = axes[0, 0]
    keys = ["toxic_f1", "toxic_recall", "toxic_precision", "macro_f1", "accuracy"]
    labels = ["Toxic F1", "Toxic Recall", "Toxic Precision", "Macro-F1", "Accuracy"]
    e5_vals = [e5_metrics.get(k, 0) for k in keys]
    e6_vals = [e6_metrics.get(k, 0) for k in keys]
    x = np.arange(len(labels))
    w = 0.35
    ax1.bar(x - w / 2, e5_vals, w, label="E5 (GaussianNB)", color="#4A90E2")
    ax1.bar(x + w / 2, e6_vals, w, label="E6 (Linear SVM)", color="#E94E77")
    ax1.set_title("A. So sánh các chỉ số hiệu năng trên tập Test", fontsize=11, fontweight="bold")
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, fontsize=9, fontweight="bold")
    ax1.set_ylim(0, 1.05)
    ax1.legend(loc="lower right", fontsize=9)

    # Panel B: Heatmap E5
    ax2 = axes[0, 1]
    e5_cm = e5_metrics["confusion_matrix"]
    tp5, tn5, fp5, fn5 = e5_cm["TP"], e5_cm["TN"], e5_cm["FP"], e5_cm["FN"]
    tot_toxic5 = tp5 + fn5
    tot_non5 = fp5 + tn5
    annot5 = [
        [f"TP: {tp5}\n({tp5/tot_toxic5*100:.1f}%)", f"FN: {fn5}\n({fn5/tot_toxic5*100:.1f}%)"],
        [f"FP: {fp5}\n({fp5/tot_non5*100:.1f}%)", f"TN: {tn5}\n({tn5/tot_non5*100:.1f}%)"]
    ]
    sns.heatmap(np.array([[tp5, fn5], [fp5, tn5]]), annot=np.array(annot5), fmt="", cmap="Blues", cbar=False, ax=ax2,
                xticklabels=["Pred Toxic (1)", "Pred Non-toxic (0)"], yticklabels=["Actual Toxic (1)", "Actual Non-toxic (0)"])
    ax2.set_title("B. Ma trận nhầm lẫn E5 (GaussianNB) - Chuẩn hóa theo lớp", fontsize=11, fontweight="bold")

    # Panel C: Heatmap E6
    ax3 = axes[1, 0]
    e6_cm = e6_metrics["confusion_matrix"]
    tp6, tn6, fp6, fn6 = e6_cm["TP"], e6_cm["TN"], e6_cm["FP"], e6_cm["FN"]
    tot_toxic6 = tp6 + fn6
    tot_non6 = fp6 + tn6
    annot6 = [
        [f"TP: {tp6}\n({tp6/tot_toxic6*100:.1f}%)", f"FN: {fn6}\n({fn6/tot_toxic6*100:.1f}%)"],
        [f"FP: {fp6}\n({fp6/tot_non6*100:.1f}%)", f"TN: {tn6}\n({tn6/tot_non6*100:.1f}%)"]
    ]
    sns.heatmap(np.array([[tp6, fn6], [fp6, tn6]]), annot=np.array(annot6), fmt="", cmap="Purples", cbar=False, ax=ax3,
                xticklabels=["Pred Toxic (1)", "Pred Non-toxic (0)"], yticklabels=["Actual Toxic (1)", "Actual Non-toxic (0)"])
    ax3.set_title("C. Ma trận nhầm lẫn E6 (Linear SVM) - Chuẩn hóa theo lớp", fontsize=11, fontweight="bold")

    # Panel D: PR Curves
    ax4 = axes[1, 1]
    p5, r5, _ = precision_recall_curve(y_test, e5_scores, pos_label=1)
    auc5 = auc(r5, p5)
    ax4.plot(r5, p5, label=f"E5 (GaussianNB) - PR-AUC: {auc5:.4f}", color="#4A90E2", lw=2)

    p6, r6, _ = precision_recall_curve(y_test, e6_scores, pos_label=1)
    auc6 = auc(r6, p6)
    ax4.plot(r6, p6, label=f"E6 (Linear SVM) - PR-AUC: {auc6:.4f}", color="#E94E77", lw=2)

    ax4.set_xlabel("Recall", fontsize=10, fontweight="bold")
    ax4.set_ylabel("Precision", fontsize=10, fontweight="bold")
    ax4.set_title("D. Đường cong Precision-Recall", fontsize=11, fontweight="bold")
    ax4.legend(loc="upper right", fontsize=9)

    fig.suptitle("DASHBOARD ĐỐI CHIẾU HIỆU NĂNG MÔ HÌNH E5 VÀ E6", fontsize=15, fontweight="bold", y=0.99)
    plt.tight_layout()
    out_path = out_dir / save_name
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return str(out_path)

"""
Bước 4: Tạo biểu đồ ảnh so sánh trực quan cho mô hình E5 và E6
Dùng trực tiếp 100% các hàm có sẵn:
- Đọc json bằng load_json (json.load)
- Đọc excel bằng read_excel (pd.read_excel)
- Vẽ 5 biểu đồ bằng các hàm plot_* (seaborn, matplotlib)
"""

from loguru import logger
import pandas as pd
from src.data_io import load_config, read_excel, load_json
from src.evaluation import (
    plot_metrics_comparison,
    plot_confusion_matrices,
    plot_precision_recall_curves,
    plot_context_error_analysis,
    generate_full_dashboard,
)


def main():
    logger.info("=" * 70)
    logger.info("TẠO BIỂU ĐỒ SO SÁNH TRỰC QUAN (ẢNH) CHO E5 VÀ E6")
    logger.info("=" * 70)

    config = load_config("config/system_config.yaml")

    # 1. Nạp metrics JSON trực tiếp bằng hàm load_json (json.load)
    e5_test_metrics = load_json(config.paths["results"]["e5_test_metrics"])
    e6_test_metrics = load_json(config.paths["results"]["e6_test_metrics"])

    # 2. Nạp file dự đoán trực tiếp bằng hàm read_excel (pd.read_excel)
    df_e5_pred = read_excel(config.paths["results"]["e5_predictions"])
    df_e6_pred = read_excel(config.paths["results"]["e6_predictions"])

    label_col = config.columns["label_column"]
    y_test = df_e5_pred[label_col].values.astype(int)

    e5_scores = df_e5_pred["pred_score"].values
    e6_scores = df_e6_pred["pred_score"].values

    report_path = config.paths["results"]["comparison_report"]
    df_context = pd.read_excel(report_path, sheet_name="Context_Error_Analysis")

    # 3. Vẽ và lưu ảnh bằng các hàm vẽ trực tiếp (không class)
    out_dir = "results/comparison/figures"

    p1 = plot_metrics_comparison(e5_test_metrics, e6_test_metrics, split="Test", output_dir=out_dir)
    p2 = plot_confusion_matrices(
        e5_test_metrics["confusion_matrix"],
        e6_test_metrics["confusion_matrix"],
        output_dir=out_dir
    )
    p3 = plot_precision_recall_curves(y_test, e5_scores, e6_scores, output_dir=out_dir)
    p4 = plot_context_error_analysis(df_context, output_dir=out_dir)
    p5 = generate_full_dashboard(
        e5_metrics=e5_test_metrics,
        e6_metrics=e6_test_metrics,
        y_test=y_test,
        e5_scores=e5_scores,
        e6_scores=e6_scores,
        output_dir=out_dir
    )

    print("\n" + "=" * 70)
    print("           HOÀN TẤT TẠO TOÀN BỘ CÁC BIỂU ĐỒ ẢNH SO SÁNH!")
    print("=" * 70)
    print(f"1. Biểu đồ chỉ số:             {p1}")
    print(f"2. Ma trận nhầm lẫn heatmap:   {p2}")
    print(f"3. Đường cong Precision-Recall: {p3}")
    print(f"4. Phân tích lỗi ngữ cảnh:     {p4}")
    print(f"5. Dashboard tổng hợp 4 ô:     {p5}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()

"""
Bước 2: Huấn luyện và Đánh giá mô hình E5 (fastText + GaussianNB)
Dùng trực tiếp các hàm có sẵn của thư viện (100% không class):
- Nạp vector trực tiếp bằng load_vectors (np.load)
- Đọc Excel trực tiếp bằng read_excel (pd.read_excel)
- Huấn luyện GaussianNB có sẵn của sklearn bằng train_e5_gaussian_nb
- Đánh giá chỉ số và xuất file Excel bằng evaluate_model_split
"""

from loguru import logger
from src.data_io import load_config, read_excel, load_vectors
from src.models import train_e5_gaussian_nb, predict_e5, evaluate_model_split


def main():
    logger.info("=" * 70)
    logger.info("HUẤN LUYỆN VÀ ĐÁNH GIÁ MÔ HÌNH E5 (fastText + GaussianNB)")
    logger.info("=" * 70)

    # 1. Nạp cấu hình
    config = load_config("config/system_config.yaml")

    # 2. Nạp vector trực tiếp bằng hàm load_vectors (dùng np.load của numpy)
    X_train, y_train, _ = load_vectors(config.paths["artifacts"]["train_vectors"])
    X_val, y_val, _ = load_vectors(config.paths["artifacts"]["val_vectors"])
    X_test, y_test, _ = load_vectors(config.paths["artifacts"]["test_vectors"])

    # 3. Đọc dữ liệu Excel trực tiếp bằng hàm read_excel (dùng pd.read_excel của pandas)
    df_val_seg = read_excel(config.paths["segmented_data"]["val"])
    df_test_seg = read_excel(config.paths["segmented_data"]["test"])

    # 4. Huấn luyện mô hình GaussianNB có sẵn của sklearn
    model, threshold, tune_info = train_e5_gaussian_nb(
        X_train, y_train, X_val, y_val, config
    )

    # 5. Dự đoán và đánh giá trên tập Val
    val_preds, val_probs = predict_e5(model, threshold, X_val)
    val_metrics, _ = evaluate_model_split(
        "e5", "val", val_preds, val_probs, y_val, df_val_seg, config
    )

    # 6. Dự đoán và đánh giá trên tập Test
    test_preds, test_probs = predict_e5(model, threshold, X_test)
    test_metrics, _ = evaluate_model_split(
        "e5", "test", test_preds, test_probs, y_test, df_test_seg, config
    )

    # 7. In bảng kết quả
    print("\n" + "=" * 70)
    print("           KẾT QUẢ MÔ HÌNH E5: fastText + GaussianNB")
    print("=" * 70)
    print(f"Tham số tối ưu trên Val:  var_smoothing={tune_info['best_var_smoothing']}, threshold={tune_info['best_threshold']}")
    print("-" * 70)
    print(f"{'Chỉ số đánh giá':<25} | {'Tập Val':<15} | {'Tập Test':<15}")
    print("-" * 70)
    print(f"{'Toxic F1 (Chính)':<25} | {val_metrics['toxic_f1']:<15.4f} | {test_metrics['toxic_f1']:<15.4f}")
    print(f"{'Toxic Recall':<25} | {val_metrics['toxic_recall']:<15.4f} | {test_metrics['toxic_recall']:<15.4f}")
    print(f"{'Toxic Precision':<25} | {val_metrics['toxic_precision']:<15.4f} | {test_metrics['toxic_precision']:<15.4f}")
    print(f"{'Macro-F1':<25} | {val_metrics['macro_f1']:<15.4f} | {test_metrics['macro_f1']:<15.4f}")
    print(f"{'Accuracy':<25} | {val_metrics['accuracy']:<15.4f} | {test_metrics['accuracy']:<15.4f}")
    print(f"{'PR-AUC':<25} | {str(val_metrics.get('pr_auc')):<15} | {str(test_metrics.get('pr_auc')):<15}")
    cm = test_metrics["confusion_matrix"]
    print(f"{'Confusion Matrix (Test)':<25} | TP={cm['TP']}, TN={cm['TN']}, FP={cm['FP']}, FN={cm['FN']}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()

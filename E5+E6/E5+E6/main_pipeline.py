"""
Pipeline trung tâm: Tự động chạy liên hoàn toàn bộ 7 giai đoạn
Dùng trực tiếp 100% các hàm có sẵn (hoàn toàn không dùng class):
1. Nạp cấu hình (load_config)
2. Đọc dữ liệu thô (read_excel)
3. Tách từ VNCoreNLP (segment_dataframe)
4. Vector hóa FastText (train_fasttext_model, extract_features)
5. Train & Test E5 (train_e5_gaussian_nb)
6. Train & Test E6 (train_e6_linear_svm)
7. So sánh & Xuất biểu đồ (generate_comparison_report, plot_*)
"""

import argparse
from pathlib import Path
from loguru import logger
import pandas as pd

from src.data_io import (
    load_config,
    read_excel,
    save_excel,
    load_vectors,
    save_vectors,
)
from src.nlp import (
    init_vncorenlp,
    segment_dataframe,
    train_fasttext_model,
    load_fasttext_model,
    extract_features,
)
from src.models import (
    train_e5_gaussian_nb,
    predict_e5,
    train_e6_linear_svm,
    predict_e6,
    evaluate_model_split,
)
from src.evaluation import (
    generate_comparison_report,
    plot_metrics_comparison,
    plot_confusion_matrices,
    plot_precision_recall_curves,
    plot_context_error_analysis,
    generate_full_dashboard,
)


def run_pipeline(
    config_path: str = "config/system_config.yaml",
    prediction_mode: str = None,
    target_model: str = "all",
    force_segment: bool = False,
    force_vectorize: bool = False,
):
    logger.info("=" * 80)
    logger.info(f"BẮT ĐẦU PIPELINE PHÂN LOẠI NGÔN NGỮ CÔNG KÍCH [MỤC TIÊU: {target_model.upper()}]")
    logger.info("=" * 80)

    # Giai đoạn 1: Nạp cấu hình
    config = load_config(config_path)
    if prediction_mode:
        config.prediction_input_mode = prediction_mode

    # Giai đoạn 2: Đọc dữ liệu thô
    df_train_raw = read_excel(config.paths["raw_data"]["train"])
    df_val_raw = read_excel(config.paths["raw_data"]["val"])
    df_test_raw = read_excel(config.paths["raw_data"]["test"])

    # Giai đoạn 3: Tách từ VNCoreNLP
    train_seg_p = Path(config.paths["segmented_data"]["train"])
    val_seg_p = Path(config.paths["segmented_data"]["val"])
    test_seg_p = Path(config.paths["segmented_data"]["test"])

    if train_seg_p.is_file() and val_seg_p.is_file() and test_seg_p.is_file() and not force_segment:
        logger.info("Đã có sẵn file dữ liệu tách từ, tiến hành nạp lại...")
        df_train_seg = read_excel(str(train_seg_p))
        df_val_seg = read_excel(str(val_seg_p))
        df_test_seg = read_excel(str(test_seg_p))
    else:
        logger.info("Chạy tách từ VNCoreNLP trên các cột làm sạch...")
        rdr = init_vncorenlp()
        df_train_seg = segment_dataframe(df_train_raw, rdr)
        save_excel(df_train_seg, str(train_seg_p))

        df_val_seg = segment_dataframe(df_val_raw, rdr)
        save_excel(df_val_seg, str(val_seg_p))

        df_test_seg = segment_dataframe(df_test_raw, rdr)
        save_excel(df_test_seg, str(test_seg_p))

    # Giai đoạn 4: Vector hóa FastText
    train_vec_p = Path(config.paths["artifacts"]["train_vectors"])
    val_vec_p = Path(config.paths["artifacts"]["val_vectors"])
    test_vec_p = Path(config.paths["artifacts"]["test_vectors"])

    mode = config.prediction_input_mode
    dim = config.fasttext_cfg.get("dim", 100)
    label_col = config.columns.get("label_column", "label")

    if train_vec_p.is_file() and val_vec_p.is_file() and test_vec_p.is_file() and not force_vectorize:
        X_train, y_train, _ = load_vectors(str(train_vec_p))
        X_val, y_val, _ = load_vectors(str(val_vec_p))
        X_test, y_test, _ = load_vectors(str(test_vec_p))
    else:
        corpus = []
        for col in ["message_segmented", "post_segmented", "parent_segmented"]:
            if col in df_train_seg.columns:
                corpus.extend(df_train_seg[col].dropna().astype(str).tolist())

        ft_model = train_fasttext_model(
            corpus_texts=corpus,
            model_save_path=config.paths["artifacts"]["fasttext_model"],
            dim=dim,
            epoch=config.fasttext_cfg.get("epoch", 25),
            lr=config.fasttext_cfg.get("lr", 0.05),
            minn=config.fasttext_cfg.get("minn", 2),
            maxn=config.fasttext_cfg.get("maxn", 5),
        )

        pooling = config.fasttext_cfg.get("pooling", "mean_max")
        X_train, y_train = extract_features(ft_model, df_train_seg, mode=mode, dim=dim, pooling=pooling, label_col=label_col)
        save_vectors(str(train_vec_p), X_train, y_train, mode=mode)

        X_val, y_val = extract_features(ft_model, df_val_seg, mode=mode, dim=dim, pooling=pooling, label_col=label_col)
        save_vectors(str(val_vec_p), X_val, y_val, mode=mode)

        X_test, y_test = extract_features(ft_model, df_test_seg, mode=mode, dim=dim, pooling=pooling, label_col=label_col)
        save_vectors(str(test_vec_p), X_test, y_test, mode=mode)

    e5_val_m, e5_test_m, df_e5_pred = None, None, None
    e6_val_m, e6_test_m, df_e6_pred = None, None, None

    # Giai đoạn 5: Huấn luyện E5 (GaussianNB)
    if target_model in ["all", "e5"]:
        logger.info("Chạy cấu hình E5 (fastText + GaussianNB)...")
        e5_model, e5_th, _ = train_e5_gaussian_nb(X_train, y_train, X_val, y_val, config)

        val_preds, val_probs = predict_e5(e5_model, e5_th, X_val)
        e5_val_m, _ = evaluate_model_split("e5", "val", val_preds, val_probs, y_val, df_val_seg, config)

        test_preds, test_probs = predict_e5(e5_model, e5_th, X_test)
        e5_test_m, df_e5_pred = evaluate_model_split("e5", "test", test_preds, test_probs, y_test, df_test_seg, config)

    # Giai đoạn 6: Huấn luyện E6 (Linear SVM)
    if target_model in ["all", "e6"]:
        logger.info("Chạy cấu hình E6 (fastText + Linear SVM)...")
        e6_model, e6_th, _ = train_e6_linear_svm(X_train, y_train, X_val, y_val, config)

        val_preds, val_scores = predict_e6(e6_model, e6_th, X_val)
        e6_val_m, _ = evaluate_model_split("e6", "val", val_preds, val_scores, y_val, df_val_seg, config)

        test_preds, test_scores = predict_e6(e6_model, e6_th, X_test)
        e6_test_m, df_e6_pred = evaluate_model_split("e6", "test", test_preds, test_scores, y_test, df_test_seg, config)

    # Giai đoạn 7: So sánh & Vẽ biểu đồ
    if target_model == "all":
        logger.info("Tạo báo cáo so sánh đối chiếu và biểu đồ ảnh...")
        report_path = config.paths["results"]["comparison_report"]
        report_file = generate_comparison_report(
            e5_val_m, e5_test_m, e6_val_m, e6_test_m, df_e5_pred, df_e6_pred, output_path=report_path
        )

        out_figures = "results/comparison/figures"
        y_test_arr = df_e5_pred[label_col].values.astype(int)
        e5_scores = df_e5_pred["pred_score"].values
        e6_scores = df_e6_pred["pred_score"].values
        df_ctx = pd.read_excel(report_file, sheet_name="Context_Error_Analysis")

        plot_metrics_comparison(e5_test_m, e6_test_m, split="Test", output_dir=out_figures)
        plot_confusion_matrices(e5_test_m["confusion_matrix"], e6_test_m["confusion_matrix"], output_dir=out_figures)
        plot_precision_recall_curves(y_test_arr, e5_scores, e6_scores, output_dir=out_figures)
        plot_context_error_analysis(df_ctx, output_dir=out_figures)
        generate_full_dashboard(e5_test_m, e6_test_m, y_test_arr, e5_scores, e6_scores, output_dir=out_figures)

        print("\n" + "=" * 80)
        print("                      TỔNG KẾT KẾT QUẢ: E5 vs E6")
        print("=" * 80)
        print(f"{'Chỉ số':<25} | {'E5 (GaussianNB) Test':<25} | {'E6 (Linear SVM) Test':<25}")
        print("-" * 80)
        print(f"{'Toxic F1 (Chính)':<25} | {e5_test_m['toxic_f1']:<25.4f} | {e6_test_m['toxic_f1']:<25.4f}")
        print(f"{'Toxic Recall':<25} | {e5_test_m['toxic_recall']:<25.4f} | {e6_test_m['toxic_recall']:<25.4f}")
        print(f"{'Toxic Precision':<25} | {e5_test_m['toxic_precision']:<25.4f} | {e6_test_m['toxic_precision']:<25.4f}")
        print(f"{'Macro-F1':<25} | {e5_test_m['macro_f1']:<25.4f} | {e6_test_m['macro_f1']:<25.4f}")
        print(f"{'Accuracy':<25} | {e5_test_m['accuracy']:<25.4f} | {e6_test_m['accuracy']:<25.4f}")
        print(f"{'PR-AUC':<25} | {str(e5_test_m.get('pr_auc')):<25} | {str(e6_test_m.get('pr_auc')):<25}")
        print("=" * 80 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chạy pipeline phân loại ngôn ngữ công kích (E5 & E6)")
    parser.add_argument("--config", default="config/system_config.yaml")
    parser.add_argument("--mode", default=None)
    parser.add_argument("--model", default="all", choices=["all", "e5", "e6"])
    parser.add_argument("--force-segment", action="store_true")
    parser.add_argument("--force-vectorize", action="store_true")
    args = parser.parse_args()

    run_pipeline(
        config_path=args.config,
        prediction_mode=args.mode,
        target_model=args.model,
        force_segment=args.force_segment,
        force_vectorize=args.force_vectorize
    )

"""
Package mã nguồn hệ thống phân loại ngôn ngữ công kích NLP_N12 (E5 & E6)
100% là các hàm thuần túy (def) dùng trực tiếp các thư viện chuẩn (không class thừa):
- data_io: read_excel, save_excel, load_vectors, save_vectors, load_model, save_model, load_json, save_json
- nlp: init_vncorenlp, segment_dataframe, train_fasttext_model, load_fasttext_model, extract_features
- models: train_e5_gaussian_nb, predict_e5, train_e6_linear_svm, predict_e6, evaluate_model_split
- evaluation: compute_metrics, generate_comparison_report, plot_confusion_matrices,...
"""

from .data_io import (
    SystemConfig,
    load_config,
    clean_text_field,
    read_excel,
    save_excel,
    save_vectors,
    load_vectors,
    save_model,
    load_model,
    save_json,
    load_json,
)
from .nlp import (
    init_vncorenlp,
    segment_text,
    segment_column,
    segment_dataframe,
    train_fasttext_model,
    load_fasttext_model,
    get_sentence_vector,
    extract_features,
)
from .models import (
    train_e5_gaussian_nb,
    predict_e5,
    train_e6_linear_svm,
    predict_e6,
    evaluate_model_split,
)
from .evaluation import (
    compute_error_type,
    compute_error_types,
    compute_metrics,
    generate_prediction_dataframe,
    evaluate_and_export,
    generate_comparison_report,
    plot_metrics_comparison,
    plot_confusion_matrices,
    plot_precision_recall_curves,
    plot_context_error_analysis,
    generate_full_dashboard,
)

__all__ = [
    # data_io
    "SystemConfig",
    "load_config",
    "clean_text_field",
    "read_excel",
    "save_excel",
    "save_vectors",
    "load_vectors",
    "save_model",
    "load_model",
    "save_json",
    "load_json",
    # nlp
    "init_vncorenlp",
    "segment_text",
    "segment_column",
    "segment_dataframe",
    "train_fasttext_model",
    "load_fasttext_model",
    "get_sentence_vector",
    "extract_features",
    # models
    "train_e5_gaussian_nb",
    "predict_e5",
    "train_e6_linear_svm",
    "predict_e6",
    "evaluate_model_split",
    # evaluation
    "compute_error_type",
    "compute_error_types",
    "compute_metrics",
    "generate_prediction_dataframe",
    "evaluate_and_export",
    "generate_comparison_report",
    "plot_metrics_comparison",
    "plot_confusion_matrices",
    "plot_precision_recall_curves",
    "plot_context_error_analysis",
    "generate_full_dashboard",
]

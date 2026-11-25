"""
Bước 1: Tách từ tiếng Việt (VNCoreNLP) và Mã hóa vector (FastText)
Dùng trực tiếp các hàm có sẵn của thư viện (không class):
1. Đọc dữ liệu gốc bằng read_excel (pd.read_excel)
2. Tách từ bằng init_vncorenlp + segment_dataframe (py_vncorenlp)
3. Học FastText bằng train_fasttext_model (fasttext.train_unsupervised)
4. Lưu vector bằng save_vectors (np.savez_compressed)
"""

from loguru import logger
import numpy as np

from src.data_io import load_config, read_excel, save_excel, save_vectors
from src.nlp import init_vncorenlp, segment_dataframe, train_fasttext_model, extract_features


def main():
    logger.info("=" * 80)
    logger.info("BƯỚC 1: TÁCH TỪ (VNCORENLP) VÀ MÃ HÓA VECTOR (FASTTEXT)")
    logger.info("=" * 80)

    # 1. Đọc cấu hình
    config = load_config("config/system_config.yaml")

    # 2. Đọc dữ liệu gốc trực tiếp bằng hàm read_excel (pd.read_excel của pandas)
    df_train_raw = read_excel(config.paths["raw_data"]["train"])
    df_val_raw = read_excel(config.paths["raw_data"]["val"])
    df_test_raw = read_excel(config.paths["raw_data"]["test"])
    logger.info(f"Dữ liệu gốc: Train {df_train_raw.shape}, Val {df_val_raw.shape}, Test {df_test_raw.shape}")

    # 3. Tách từ tiếng Việt trực tiếp bằng py_vncorenlp
    logger.info("Bắt đầu tách từ bằng VNCoreNLP...")
    rdr = init_vncorenlp()

    df_train_seg = segment_dataframe(df_train_raw, rdr)
    save_excel(df_train_seg, config.paths["segmented_data"]["train"])

    df_val_seg = segment_dataframe(df_val_raw, rdr)
    save_excel(df_val_seg, config.paths["segmented_data"]["val"])

    df_test_seg = segment_dataframe(df_test_raw, rdr)
    save_excel(df_test_seg, config.paths["segmented_data"]["test"])

    # 4. Học mô hình FastText trực tiếp bằng hàm train_fasttext_model
    logger.info("Bắt đầu học từ vựng và trích xuất vector FastText...")
    corpus = []
    for col in ["message_segmented", "post_segmented", "parent_segmented"]:
        if col in df_train_seg.columns:
            corpus.extend(df_train_seg[col].dropna().astype(str).tolist())

    ft_model = train_fasttext_model(
        corpus_texts=corpus,
        model_save_path=config.paths["artifacts"]["fasttext_model"],
        dim=config.fasttext_cfg.get("dim", 100),
        epoch=config.fasttext_cfg.get("epoch", 25),
        lr=config.fasttext_cfg.get("lr", 0.05),
        minn=config.fasttext_cfg.get("minn", 2),
        maxn=config.fasttext_cfg.get("maxn", 5),
    )

    # 5. Trích xuất ma trận đặc trưng X và nhãn y, lưu bằng np.savez_compressed
    label_col = config.columns.get("label_column", "label")
    mode = config.prediction_input_mode
    dim = config.fasttext_cfg.get("dim", 100)
    pooling = config.fasttext_cfg.get("pooling", "mean_max")

    X_train, y_train = extract_features(ft_model, df_train_seg, mode=mode, dim=dim, pooling=pooling, label_col=label_col)
    save_vectors(config.paths["artifacts"]["train_vectors"], X_train, y_train, mode=mode)

    X_val, y_val = extract_features(ft_model, df_val_seg, mode=mode, dim=dim, pooling=pooling, label_col=label_col)
    save_vectors(config.paths["artifacts"]["val_vectors"], X_val, y_val, mode=mode)

    X_test, y_test = extract_features(ft_model, df_test_seg, mode=mode, dim=dim, pooling=pooling, label_col=label_col)
    save_vectors(config.paths["artifacts"]["test_vectors"], X_test, y_test, mode=mode)

    print("\n" + "=" * 80)
    print("        HOÀN TẤT GIAI ĐOẠN TÁCH TỪ VÀ MÃ HÓA VECTOR FASTTEXT!")
    print("=" * 80)
    print(f"X_train: {X_train.shape}, nhãn y_train: {y_train.shape} (Toxic: {np.sum(y_train==1)})")
    print(f"X_val:   {X_val.shape}, nhãn y_val:   {y_val.shape} (Toxic: {np.sum(y_val==1)})")
    print(f"X_test:  {X_test.shape}, nhãn y_test:  {y_test.shape} (Toxic: {np.sum(y_test==1)})")
    print("Hệ thống đã sẵn sàng cho bước tiếp theo: Huấn luyện và Đánh giá E5 và E6!\n")


if __name__ == "__main__":
    main()

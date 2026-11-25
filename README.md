# NLP_N12: dataset bình luận sinh viên PTIT gán nhãn 4 hướng

Nhóm NLP_N12 (Hảo, Sinh, Triệu, Long). Từ khoảng 140 nghìn bình luận Facebook của sinh viên PTIT (136.609 dòng sau làm sạch), nhóm xây bộ dữ liệu gán nhãn theo 4 hướng: **toxicity** (clean, profane, attack), **topic**, **stance** và **emotion**, để công bố trên Hugging Face.

**Bắt đầu từ đây:** đọc [`TIEN_TRINH_DATASET.md`](TIEN_TRINH_DATASET.md). File này ghi tiến trình, checklist từng giai đoạn và nhật ký. Hiện dự án đang ở giai đoạn gán thử: vòng 1 đã chốt gold, vòng 2 đã tạo file nhưng chưa ai gán.

## Cấu trúc

```
.
├── README.md
├── TIEN_TRINH_DATASET.md     tiến trình, checklist, nhật ký
├── docs/                     quy chuẩn gán nhãn, thiết kế nhãn, quy tắc làm sạch (.docx)
├── scripts/                  code làm sạch và gán thử
│   └── ra_soat/              script đợt rà gold vòng 1, docx2txt.py
├── data/                     dữ liệu nhận riêng, KHÔNG commit
│   ├── cleaned/              masked.csv, report.json
│   └── gan_nhan/             vong1/, vong2/, ...
├── huggingface/              dataset card nháp để công bố trên Hugging Face
└── .claude/skills/nlp-n12-dataset/   skill bàn giao cho Claude Code
```

| Đường dẫn | Nội dung |
|---|---|
| `docs/Quy_chuan_gan_nhan_4_huong_NLP_N12.docx` | Quy chuẩn gán nhãn 4 hướng (bản nháp 3) |
| `docs/Thiet_ke_du_lieu_da_huong_NLP_N12.docx` | Thiết kế 4 hướng, so sánh với UIT-VSFC, UIT-VSMEC, ViHSD |
| `docs/Quy_tac_lam_sach_du_lieu_NLP_N12.docx` | Quy trình làm sạch và che thông tin cá nhân |
| `docs/Ke_hoach_tiep_theo_NLP_N12.docx` | Kế hoạch bước tiếp theo cho cả nhóm, các điểm còn vướng, bảng tra quy tắc gán (25/11/2026) |
| `scripts/clean_dataset.py`, `scripts/danh_sach_dia_danh_truong.csv` | Làm sạch, che thông tin cá nhân. Chạy trên Colab, cần file thô (không có trong repo) |
| `scripts/tao_mau_gan_thu.py [vòng]` | Tạo file gán thử cho 4 người từ `data/cleaned/masked.csv`, không lấy lại câu các vòng trước |
| `scripts/tong_hop_gan_thu.py <out.xlsx> <file>...` | Tổng hợp file đã gán, tính Cohen κ và Fleiss κ |
| `scripts/ra_soat/` | Script đợt rà gold vòng 1 (chỉ để tái lập); `docx2txt.py` đọc docx khi không có pandoc |
| `data/cleaned/report.json` | Thống kê lần làm sạch chính thức (lần 3), file duy nhất trong `data/` được commit |
| `huggingface/README.md` | Dataset card nháp: metadata, mô tả nhãn, chia tập, quy trình, đạo đức; mục chưa có số liệu ghi `TODO` |

## Dữ liệu (nhận riêng, không có trên GitHub)

Dữ liệu chưa qua rà soát pháp lý và đạo đức, nên chỉ chia sẻ trong nhóm qua kênh riêng. Nhận được thì đặt vào `data/` như sau:

| Đường dẫn | Nội dung |
|---|---|
| `data/cleaned/masked.csv` | Dataset đã che thông tin cá nhân, 136.609 dòng, có cột `split` (train/val/test theo bài đăng) |
| `data/gan_nhan/vong1/` | File gán vòng 1, `gold_vong1.csv`, các file `_da_chot.xlsx` |
| `data/gan_nhan/vong2/` | 4 file gán vòng 2 và `tong_hop_vong2.csv`; gán xong đặt vào `data/gan_nhan/vong2/da_gan/` |

**Không bao giờ commit dữ liệu vào repo này.** `.gitignore` chặn cả `data/` (trừ `report.json`) và mọi file `.xlsx`, `.parquet`, `.zip`. Không gửi dữ liệu chưa che cho LLM hay dịch vụ ngoài.

## Chạy

Chạy mọi lệnh từ thư mục gốc repo.

- Python 3.10+, cài `pip install pandas openpyxl`.
- Tạo file gán vòng N: `python scripts/tao_mau_gan_thu.py N`
- Tổng hợp vòng 2 khi cả 4 người gán xong:
  ```
  python scripts/tong_hop_gan_thu.py data/gan_nhan/vong2/tong_hop_vong2_4nguoi.xlsx data/gan_nhan/vong2/da_gan/gan_thu_vong2_Hao.xlsx data/gan_nhan/vong2/da_gan/gan_thu_vong2_Sinh.xlsx data/gan_nhan/vong2/da_gan/gan_thu_vong2_Trieu.xlsx data/gan_nhan/vong2/da_gan/gan_thu_vong2_Long.xlsx
  ```
- Làm sạch (`scripts/clean_dataset.py`) chạy trên Colab có GPU: xem mục "Cách chạy trên Colab" trong `TIEN_TRINH_DATASET.md`.
- Trên Windows, in tiếng Việt từ Python cần đặt `PYTHONIOENCODING=utf-8`.

## Làm tiếp bằng Claude Code

Mở thư mục gốc của repo trong Claude Code, sau đó gõ `/nlp-n12-dataset` hoặc hỏi "làm gì tiếp". Skill sẽ đọc `TIEN_TRINH_DATASET.md`, kiểm tra trạng thái file rồi tiếp tục theo lộ trình.

## Giai đoạn cũ đã bỏ khỏi repo

Trước dataset 4 hướng, nhóm làm bài toán Toxic nhị phân (E1–E8 trên 9.962 câu, quy chuẩn v2.2). Ngày 2026-11-25, phần đó cùng các công cụ phụ đã bỏ khỏi repo để repo chỉ phục vụ dataset 4 hướng: `notebooks/`, `E5+E6/`, `results_chuan/`, `facebook_post_comment_scraper/`, `Bao_cao_tien_do_NLP_N12.docx`, kế hoạch và quy chuẩn nhị phân (`.txt`), `add_toxic_to_main.py`, `link_labels.py`, `tienxuly_data_n12.py`, `compare_ner.py`. Cần lại thì lấy từ commit `7fa0312`:

```
git checkout 7fa0312 -- notebooks/
```

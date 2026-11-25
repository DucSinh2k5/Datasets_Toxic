# NLP_N12: dataset bình luận sinh viên PTIT gán nhãn 4 hướng

Nhóm NLP_N12 (Hảo, Sinh, Triệu, Long). Từ khoảng 140 nghìn bình luận Facebook của sinh viên PTIT, nhóm xây bộ dữ liệu gán nhãn theo 4 hướng: **toxicity** (clean, profane, attack), **topic**, **stance** và **emotion**.

**Bắt đầu từ đây:** đọc [`TIEN_TRINH_DATASET.md`](TIEN_TRINH_DATASET.md). File này ghi tiến trình, checklist từng giai đoạn và nhật ký. Hiện dự án đang ở giai đoạn gán thử: vòng 1 đã chốt gold, vòng 2 đã tạo file nhưng chưa ai gán.

## Repo này có gì

Repo chỉ chứa **code và tài liệu**. Repo không chứa dữ liệu bình luận, kể cả bản đã che thông tin.

| Đường dẫn | Nội dung |
|---|---|
| `TIEN_TRINH_DATASET.md` | Tiến trình, việc cần làm tiếp |
| `Quy_chuan_gan_nhan_4_huong_NLP_N12.docx` | Quy chuẩn gán nhãn 4 hướng (bản nháp 3) |
| `Thiet_ke_du_lieu_da_huong_NLP_N12.docx` | Thiết kế 4 hướng, so sánh với UIT-VSFC, UIT-VSMEC, ViHSD |
| `Quy_tac_lam_sach_du_lieu_NLP_N12.docx`, `clean_dataset.py`, `compare_ner.py`, `danh_sach_dia_danh_truong.csv` | Quy trình làm sạch và che thông tin cá nhân |
| `cleaned/report.json` | Thống kê lần làm sạch chính thức (lần 3) |
| `tao_mau_gan_thu.py [vòng]` | Tạo file gán thử cho 4 người, không lấy lại câu các vòng trước |
| `tong_hop_gan_thu.py <out.xlsx> <file>...` | Tổng hợp file đã gán, tính Cohen κ và Fleiss κ |
| `scripts_ra_soat/` | Script đợt rà gold vòng 1; `docx2txt.py` để đọc docx khi không có pandoc |
| `.claude/skills/nlp-n12-dataset/SKILL.md` | Skill bàn giao cho Claude Code: bối cảnh, quy tắc, lộ trình |
| `facebook_post_comment_scraper/` | Công cụ cào bình luận (không kèm cookie, không kèm dữ liệu) |
| `notebooks/`, `E5+E6/`, `results_chuan/` | Giai đoạn cũ: bài toán Toxic nhị phân E1–E8. Notebook đã xóa output; `results_chuan/` chỉ giữ số liệu |
| `Bao_cao_tien_do_NLP_N12.docx`, `KẾ HOẠCH...txt`, `Quy chuẩn gán nhãn NLP.txt` | Báo cáo và kế hoạch của giai đoạn cũ, để tham khảo |

## Dữ liệu (nhận riêng, không có trên GitHub)

Dữ liệu chưa qua rà soát pháp lý và đạo đức, nên chỉ chia sẻ trong nhóm qua kênh riêng. Nhận được thì đặt vào đúng chỗ sau (các đường dẫn này đã nằm trong `.gitignore`):

| Đường dẫn | Nội dung |
|---|---|
| `cleaned/masked.csv` | Dataset đã che thông tin cá nhân, 136.609 dòng, có cột `split` (train/val/test theo bài đăng) |
| `gan_nhan/vong1/` | File gán vòng 1, `gold_vong1.csv`, các file `_da_chot.xlsx` |
| `gan_nhan/vong2/` | 4 file gán vòng 2 và `tong_hop_vong2.csv` |

**Không bao giờ commit dữ liệu vào repo này.** Không gửi dữ liệu chưa che cho LLM hay dịch vụ ngoài.

## Làm tiếp bằng Claude Code

Mở thư mục gốc của repo trong Claude Code, sau đó gõ `/nlp-n12-dataset` hoặc hỏi "làm gì tiếp". Skill sẽ đọc `TIEN_TRINH_DATASET.md`, kiểm tra trạng thái file rồi tiếp tục theo lộ trình.

## Chạy

- Python 3.10+. Gói cần cho các script gán thử: `pandas`, `openpyxl`.
- Làm sạch (`clean_dataset.py`) chạy trên Colab có GPU: xem mục "Cách chạy trên Colab" trong `TIEN_TRINH_DATASET.md`. Script cần file thô, mà file thô không có ở đây.
- Scraper đọc `FB_COOKIE`, `FB_DTSG`, `PROXY` từ biến môi trường hoặc file `.env` (không commit).
- Trên Windows, in tiếng Việt từ Python cần đặt `PYTHONIOENCODING=utf-8`.

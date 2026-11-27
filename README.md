# NLP_N12: dataset bình luận sinh viên PTIT gán nhãn 4 hướng

Nhóm NLP_N12 (Hảo, Sinh, Triệu, Long). Từ khoảng 140 nghìn bình luận Facebook của sinh viên PTIT (136.609 dòng sau làm sạch), nhóm xây bộ dữ liệu gán nhãn theo 4 hướng: **toxicity** (clean, profane, attack), **topic**, **stance** và **emotion**, để công bố trên Hugging Face.

**Bắt đầu từ đây:** đọc [`TIEN_TRINH_DATASET.md`](TIEN_TRINH_DATASET.md). File này ghi tiến trình, checklist từng giai đoạn và nhật ký. Ngày 27/11/2026, nhóm dừng gán nhãn tay sau 2 vòng gán thử. Quy chuẩn đã chốt ở bản 5; hai bộ gold (480 câu) đều theo bản 5; masked.csv đã che bổ sung (đợt 1 đã xác nhận, đợt 2 chờ xác nhận). Prompt và script gán bằng LLM (`scripts/llm/`) đã viết và chạy thử không gọi API. Bước tiếp theo là chọn cách gọi LLM (so sánh các gói miễn phí trong `docs/Cach_gan_nhan_LLM_mien_phi_NLP_N12.docx`), chạy trên gold để khóa prompt, rồi gán toàn bộ (Claude phân xử câu bất đồng). Lộ trình đến khi công bố nằm ở `docs/Ke_hoach_tong_the_NLP_N12.docx`; việc cần làm ngay nằm ở `docs/Ke_hoach_tiep_theo_NLP_N12.docx`.

## Cấu trúc

```
.
├── README.md                 giới thiệu repo (cùng nội dung với CLAUDE.md)
├── CLAUDE.md                 hướng dẫn cho Claude Code
├── TIEN_TRINH_DATASET.md     tiến trình, checklist, nhật ký
├── docs/                     quy chuẩn gán nhãn, thiết kế nhãn, quy tắc làm sạch, kế hoạch (.docx)
├── scripts/                  code làm sạch, che bổ sung, đọc docx
│   └── llm/                  prompt, gán nhãn bằng LLM, chấm so với gold
├── data/                     dữ liệu nhận riêng, KHÔNG commit
│   ├── cleaned/              masked.csv, report.json
│   └── gan_nhan/             vong1/, vong2/, ...
├── huggingface/              dataset card nháp để công bố trên Hugging Face
└── .claude/skills/nlp-n12-dataset/   skill bàn giao cho Claude Code
```

| Đường dẫn | Nội dung |
|---|---|
| `docs/Ke_hoach_tong_the_NLP_N12.docx` | Kế hoạch tổng thể: 8 giai đoạn từ dữ liệu thô đến công bố trên Hugging Face, việc cần làm, tiêu chí xong, cổng kiểm soát (27/11/2026) |
| `docs/Ke_hoach_tiep_theo_NLP_N12.docx` | Kế hoạch bước tiếp theo sau khi dừng gán tay: kết quả chốt vòng 2, bước 1–9 (gán bằng LLM), điểm còn vướng, lịch gợi ý (27/11/2026) |
| `docs/Cach_gan_nhan_LLM_mien_phi_NLP_N12.docx` | Các cách gọi LLM miễn phí để gán nhãn (giới hạn, chính sách dữ liệu, so sánh, khuyến nghị), chờ nhóm chọn (27/11/2026) |
| `docs/Quy_chuan_gan_nhan_4_huong_NLP_N12_ban5.docx` | **Quy chuẩn gán nhãn 4 hướng, bản 5 (bản chốt, 27/11/2026)**: gộp mọi quy tắc thành một bộ thống nhất; dùng để viết prompt LLM |
| `docs/Thiet_ke_du_lieu_da_huong_NLP_N12.docx` | Thiết kế 4 hướng, so sánh với UIT-VSFC, UIT-VSMEC, ViHSD |
| `docs/Quy_tac_lam_sach_du_lieu_NLP_N12.docx` | Quy trình làm sạch và che thông tin cá nhân |
| `scripts/clean_dataset.py`, `scripts/danh_sach_dia_danh_truong.csv` | Làm sạch, che thông tin cá nhân. Chạy trên Colab, cần file thô (không có trong repo) |
| `scripts/che_bo_sung.py [--ghi]` | Che bổ sung `masked.csv` và mọi file trong `data/gan_nhan/` bằng `SUPPLEMENT_RULES` của `clean_dataset.py` và danh sách che tay `data/cleaned/private/che_bo_sung/thu_cong.csv`; luôn dựng lại từ bản gốc trước khi che bổ sung, ghi file xác nhận theo đợt (`_dot2`...); không có `--ghi` thì chỉ chạy thử |
| `scripts/llm/prompt_ban5.md` | System prompt gán nhãn bằng LLM, viết từ bản 5; phiên bản ở dòng đầu (`ban5-p1`) |
| `scripts/llm/gan_nhan_llm.py` | Gán bằng Claude, OpenAI hoặc máy chủ tương thích OpenAI (vLLM, `--base-url`) (structured outputs, cache, batch), ghi từng câu, chạy tiếp được; `--thu` để chạy thử không gọi API |
| `scripts/llm/danh_gia_llm.py --gold <vòng> --kq <file.jsonl>... [--bo-trung-prompt <prompt>]` | Chấm kết quả LLM so với gold: κ, macro-F1, F1 từng nhãn, κ giữa các LLM, κ riêng từng vòng, κ khi bỏ câu gold trùng ví dụ trong prompt |
| `scripts/llm/prompt_ban5_en.md` | Bản tiếng Anh của prompt (`ban5-en-p1`), ví dụ giữ tiếng Việt; chọn bằng `--prompt` |
| `scripts/llm/prompt_ban5_en_tach/` | Bộ prompt tiếng Anh tách theo hướng (`ban5-en-tach-p3`; toxicity có trường `bang_chung`, script kiểm tra bằng chứng có trong câu và từ tục trong `chung.TU_TUC`): `chung.md` + một file mỗi hướng; truyền thư mục vào `--prompt` thì mỗi câu gọi 4 lần |
| `scripts/llm/kaggle_khoa_prompt.ipynb` | Notebook Kaggle khóa prompt: chọn mô hình bằng `MO_HINH` (`14b` mặc định: Qwen3-14B-AWQ; `30b-a3b`: Qwen3-30B-A3B-GPTQ-Int4), tắt suy nghĩ, bộ prompt tách hướng hiện tại (`ban5-en-tach-p3`), gán và chấm cả hai bộ gold (480 câu), đo tốc độ |
| `scripts/llm/dong_goi_kaggle.py [--nguoi <tên>|tat_ca]` | Gói Kaggle: không tham số thì gói 480 dòng gold đã che kèm code (`data/llm/goi_kaggle/goi_kaggle.zip`, để khóa prompt); `--nguoi` thì gói các đợt của người đó (`goi_<tên>.zip`: code, prompt đã khóa, file đợt, chỉ các dòng masked của các đợt đó). Dừng nếu còn câu khớp mẫu thông tin cá nhân |
| `scripts/llm/chia_dot.py [--ghi]` | Chia 136.129 câu cần gán (trừ gold) thành 14 đợt theo bài đăng (train 10, val 2, test 2; khoảng 9.500–10.300 câu, khoảng 6 giờ mỗi đợt), phân công cho 4 người; ghi `data/llm/dot/` (`dot_XX.csv`, `phan_cong.csv`, `bi_chan.csv`) |
| `scripts/llm/kaggle_gan_dot.ipynb` | Notebook Kaggle gán một đợt bằng cấu hình đã khóa (Qwen3-14B-AWQ, vLLM 0.34.0, `ban5-en-tach-p3`, kiểm tra sha), tự dừng sau 10 giờ, chạy tiếp được từ Output của phiên trước, xuất `ket_qua_<đợt>.zip` |
| `scripts/llm/ghep_ket_qua.py [--dot-bu] [--ghi]` | Tiến độ từng đợt và từng người; tạo đợt bù cho câu thiếu hoặc lỗi; ghép thành `data/llm/nhan_toan_bo.csv` (gold giữ nhãn người, mỗi dòng ghi nguồn gốc nhãn); chỉ nhận kết quả đúng cấu hình đã khóa |
| `scripts/docx2txt.py` | Đọc docx khi không có pandoc |
| `data/cleaned/report.json` | Thống kê lần làm sạch chính thức (lần 3), file duy nhất trong `data/` được commit |
| `huggingface/README.md` | Dataset card nháp: metadata, mô tả nhãn, chia tập, quy trình, đạo đức; mục chưa có số liệu ghi `TODO` |

## Dữ liệu (nhận riêng, không có trên GitHub)

Dữ liệu chưa qua rà soát pháp lý và đạo đức, nên chỉ chia sẻ trong nhóm qua kênh riêng. Nhận được thì đặt vào `data/` như sau:

| Đường dẫn | Nội dung |
|---|---|
| `data/cleaned/masked.csv` | Dataset đã che thông tin cá nhân, 136.609 dòng, có cột `split` (train/val/test theo bài đăng) |
| `data/cleaned/private/che_bo_sung/` | Danh sách che tay `thu_cong.csv`, bản gốc trước khi che bổ sung (script dựng lại từ đây), file xác nhận đợt 1 và 2 (đã xác nhận), log (có tên thật, không chia sẻ) |
| `data/gan_nhan/vong1/` | `gold_vong1.csv` (240 câu, theo bản 5); `ra_soat_gold_vong1_ban5.xlsx` (các ô Claude sửa khi rà theo bản 5); bài của Hảo, Triệu trong `da_gan/`; file 4 người soát chung trong `da_chot/`; lý do đợt rà 24/11 trong các file `_da_chot.xlsx` |
| `data/gan_nhan/vong2/` | `gold_vong2.csv` (240 câu, theo bản 5); file chốt `tong_hop_vong2_Hao_Long.xlsx` (sheet `da_ap_dung` ghi các ô Claude sửa, kèm nhãn cũ); bài của Hảo, Long trong `da_gan/`; đề xuất rà soát `ra_soat_chot_vong2_Hao_Long.xlsx`. Nguồn mẫu từng câu nằm ở cột `nguon_mau` của gold |

**Không bao giờ commit dữ liệu vào repo này.** `.gitignore` chặn cả `data/` (trừ `report.json`) và mọi file `.xlsx`, `.parquet`, `.zip`. Không gửi dữ liệu chưa che cho LLM hay dịch vụ ngoài.

## Chạy

Chạy mọi lệnh từ thư mục gốc repo.

- Python 3.10+, cài `pip install pandas openpyxl`.
- Gold hai vòng đã chốt. Muốn sửa nhãn gold thì sao lưu trước, sửa thẳng trong csv và ghi `ra_soat_claude` hoặc nguồn khác ở cột `*_cach_chot`.
- Gán bằng LLM: `pip install anthropic openai`, đặt `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` trong biến môi trường, rồi xem lệnh ở đầu `scripts/llm/gan_nhan_llm.py` hoặc mục "Gán bằng LLM" trong `TIEN_TRINH_DATASET.md`. Chỉnh prompt chỉ dựa trên gold vòng 2; gold vòng 1 để kiểm tra; không dùng tập test.
- Đã xóa ngày 27/11/2026 (không gán tay thêm, gold đã xuất xong): `scripts/tao_mau_gan_thu.py`, `scripts/tong_hop_gan_thu.py`, `scripts/xuat_gold.py`; lấy lại bằng `git checkout 46c38cd -- scripts/<tên file>`.
- Làm sạch (`scripts/clean_dataset.py`) chạy trên Colab có GPU: xem mục "Cách chạy trên Colab" trong `TIEN_TRINH_DATASET.md`.
- Trên Windows, in tiếng Việt từ Python cần đặt `PYTHONIOENCODING=utf-8`.

## Làm tiếp bằng Claude Code

Mở thư mục gốc của repo trong Claude Code, sau đó gõ `/nlp-n12-dataset` hoặc hỏi "làm gì tiếp". Skill sẽ đọc `TIEN_TRINH_DATASET.md`, kiểm tra trạng thái file rồi tiếp tục theo lộ trình.

## File đã bỏ khỏi repo

Trước dataset 4 hướng, nhóm làm bài toán Toxic nhị phân (E1–E8 trên 9.962 câu, quy chuẩn v2.2). Ngày 2026-11-25, phần đó cùng các công cụ phụ đã bỏ khỏi repo để repo chỉ phục vụ dataset 4 hướng: `notebooks/`, `E5+E6/`, `results_chuan/`, `facebook_post_comment_scraper/`, `Bao_cao_tien_do_NLP_N12.docx`, kế hoạch và quy chuẩn nhị phân (`.txt`), `add_toxic_to_main.py`, `link_labels.py`, `tienxuly_data_n12.py`, `compare_ner.py`. Cần lại thì lấy từ commit `7fa0312`:

```
git checkout 7fa0312 -- notebooks/
```

Ngày 2026-11-27 bỏ thêm quy chuẩn bản nháp 3 và bản nháp 4 (`docs/Quy_chuan_gan_nhan_4_huong_NLP_N12_ban4.docx`, lấy lại từ commit `46c38cd`), notebook Qwen2.5 `scripts/llm/kaggle_qwen_gold.ipynb` (chưa commit, đã thay bằng `kaggle_qwen3_tach_huong.ipynb`, rồi bằng `kaggle_khoa_prompt.ipynb`), thư mục `scripts/ra_soat/` (chuyển `docx2txt.py` lên `scripts/`), cùng bản nháp 3 (`docs/Quy_chuan_gan_nhan_4_huong_NLP_N12.docx`; vòng 1 và bài vòng 2 của Hảo, Long gán theo bản này) và hai script rà gold vòng 1 (`scripts/ra_soat/chot_vong1.py`, `scripts/ra_soat/ra_soat_suggest.py`). Lấy lại từ commit `2b39403`:

```
git checkout 2b39403 -- docs/Quy_chuan_gan_nhan_4_huong_NLP_N12.docx
```

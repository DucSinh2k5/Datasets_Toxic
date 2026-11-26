---
name: nlp-n12-dataset
description: Tiếp tục dự án NLP_N12 (BTL1) - xây bộ dữ liệu bình luận sinh viên PTIT gán nhãn 4 hướng (toxicity, topic, stance, emotion). Dùng khi người dùng hỏi về tiến trình, gán nhãn các vòng, tính κ, chốt gold, quy chuẩn gán nhãn, gán bằng LLM, hoặc "làm gì tiếp" trong repo dataset NLP_N12.
---

# Bàn giao dự án NLP_N12: dataset 4 hướng

Bàn giao ngày 2026-11-25, sắp xếp lại cấu trúc repo cùng ngày. **Nguồn sự thật là `TIEN_TRINH_DATASET.md`** ở thư mục gốc repo: đọc file đó trước, và cập nhật nó (đầu file, mục "Đang ở đâu", checklist, nhật ký) sau mỗi bước hoàn thành. File skill này tóm tắt bối cảnh, quy tắc làm việc và lộ trình; nếu hai file lệch nhau thì tin TIEN_TRINH và kiểm tra lại dữ liệu.

## 1. Bối cảnh

- Nhóm 4 người: **Hảo, Sinh, Triệu, Long**. Skill viết từ phiên làm việc của **Sinh** (git user `DucSinh2k5`); người dùng có thể là bất kỳ thành viên nào, xem git user hoặc hỏi khi cần biết ai đang làm (gán thử phải độc lập). Trao đổi bằng tiếng Việt.
- Dữ liệu: 141.276 bình luận cào từ 16 group Facebook sinh viên PTIT, 22.144 bài đăng. Sau làm sạch và che thông tin: **136.609 dòng** trong `data/cleaned/masked.csv`, chia train/val/test theo bài đăng 70/15/15, seed 42 (95.667 / 20.458 / 20.484).
- Mục tiêu: gán nhãn 4 hướng, viết paper và công bố dataset trên Hugging Face (gated) nếu qua được rà soát pháp lý, đạo đức.
- Lịch sử: giai đoạn trước nhóm làm bài toán Toxic nhị phân (E1–E8 trên 9.962 câu, quy chuẩn v2.2 "Keyword-Priority"). Kết quả đó **không phải** của dataset mới. Quy chuẩn cũ coi mọi từ tục là Toxic nên tra 56 từ khóa đã đạt F1 0,827; vì vậy hướng mới tách profane khỏi attack.

### Phạm vi, những thứ KHÔNG thuộc dự án
- `shared_dataset.csv`, `data_splits_shared/`, `results_shared/`: của **nhóm khác** (nhãn do ollama qwen3 gán). Không trộn vào phân tích của N12.
- Thư mục cha `NPL-NMF` (backend, frontend, docs, tóm tắt văn bản NMF): **dự án khác**, không liên quan.
- `tonghopcmt_n12.xlsx`: 3.123 dòng cuối là toxic ngoài PTIT. Đầu vào làm sạch phải là `tonghopcmt_n12_backup_truoc_khi_them_toxic.xlsx`.
- Phần giai đoạn Toxic nhị phân (`notebooks/` E1–E8, `E5+E6/`, `results_chuan/`, báo cáo, kế hoạch, quy chuẩn nhị phân), scraper, `compare_ner.py` và các script cũ đã xóa khỏi repo ngày 2026-11-25. Cần thì lấy lại: `git checkout 7fa0312 -- <đường dẫn>`.

## 2. Quy tắc làm việc (bắt buộc)

- **Riêng tư:** chỉ dùng bản đã che (`text_public`, `data/cleaned/masked.csv`) khi gửi cho LLM hay dịch vụ ngoài. Không đọc ra, không gửi, không chia sẻ `data/cleaned/private/`, `data/cleaned_lan2/`, `data/cleaned_ban_cu/` và các file `.xlsx` thô. Gửi qua API thì dùng gói không lấy dữ liệu để huấn luyện.
- **Không sửa gold mà không sao lưu.** Mọi thay đổi nhãn ghi nguồn gốc ở cột `*_cach_chot` (ví dụ `dong_y`, `phan_xu`, `ra_soat_claude`).
- **Gán thử phải độc lập**: mỗi người gán riêng rồi mới họp. Không dùng nhãn của người khác hay gold khi gán.
- **Không dùng tập Test để sửa prompt, quy chuẩn hay mô hình.** Mẫu gán thử chỉ lấy từ train.
- Đề xuất trước, sửa sau: khi rà nhãn, ghi đề xuất và lý do ra file Excel cho nhóm duyệt; chỉ ghi thẳng vào gold khi người dùng bảo. Nếu Claude là người chốt, ghi rõ để paper khai báo.
- Không commit hay đẩy dữ liệu: mọi dữ liệu nằm trong `data/`; `.gitignore` gốc chặn cả `data/` (trừ `data/cleaned/report.json`) và mọi `.xlsx`, `.parquet`, `.zip`. Xem `git status` trước khi commit.
- Chạy lệnh từ thư mục gốc repo. Script gán thử cần `pandas`, `openpyxl`; có máy chưa cài `openpyxl` (`pip install openpyxl`).
- Đọc docx: máy không có pandoc và python-docx. Dùng `python scripts/ra_soat/docx2txt.py <file.docx>`; script ghi `<tên>.docx.txt` vào thư mục đang đứng, nên chạy từ thư mục tạm.
- Windows: in tiếng Việt từ Python cần `PYTHONIOENCODING=utf-8`.

## 3. Bộ nhãn và các quy tắc đã chốt

Tài liệu: `docs/Quy_chuan_gan_nhan_4_huong_NLP_N12_ban5.docx` (**bản 5, bản chốt, 27/11/2026**). Bản này gộp mọi quy tắc vào mục 3–6, ghi các trường hợp đã chốt ở 5.1–5.14 (stance) và 6.1–6.8 (emotion), có lịch sử phiên bản ở mục 9. Dùng bản này để viết prompt LLM. Bản nháp 4 `_ban4.docx` chỉ giữ để đối chiếu. Bản nháp 3 đã xóa, lấy lại bằng `git checkout 2b39403 -- docs/Quy_chuan_gan_nhan_4_huong_NLP_N12.docx`. Lộ trình: `docs/Ke_hoach_tong_the_NLP_N12.docx`; việc cần làm ngay: `docs/Ke_hoach_tiep_theo_NLP_N12.docx`.

| Hướng | Nhãn |
|---|---|
| toxicity | clean, profane, attack, unk |
| topic | academics, facilities, administration, student_life, unk |
| stance | support, oppose, suggest, none, unk |
| emotion | joy, sadness, anger, fear, surprise, neutral, unk; đa nhãn: `emotion_1` chính, `emotion_2` các cảm xúc còn lại cách nhau bằng `;` |

Quy tắc quan trọng (bản 5):

- **Chung:** không suy đoán ý ngầm; chỉ gán theo dấu hiệu trong câu và ngữ cảnh.
- **toxicity:**
  - Xúc phạm, mỉa mai, chế giễu nhắm vào người là attack, kể cả khi trêu bạn bè kèm emoji cười. Phép thử: bỏ emoji đi mà câu vẫn hạ thấp ai đó.
  - Từ tục chỉ để nhấn mạnh, hoặc chửi sự vật, tổ chức, là profane.
  - Câu chỉ có tag hoặc emoji là clean.
  - unk chỉ dùng cho từ đa nghĩa như "cc" mà không rõ nghĩa.
- **topic:**
  - Câu phản hồi nội dung đang bàn (kể cả cảm ơn người trả lời, "+1", "xin vía") lấy topic theo bình luận cha hoặc bài đăng.
  - unk chỉ dùng cho câu chỉ có tag, emoji, tiếng cười, spam, hoặc không hiểu được.
  - Tuyển sinh, xét tuyển, điểm chuẩn, học phí, học bổng, đăng ký học phần là administration.
  - Mọi câu về ký túc xá là facilities.
  - Tài liệu, đề thi, chất lượng đào tạo là academics.
  - CLB, Đoàn, đời sống, tình cảm với trường nói chung là student_life.
- **stance:**
  - Đối tượng là một việc của trường hoặc vấn đề đang bàn, không phải người đối thoại. Ba câu tự hỏi (mục 5).
  - Các trường hợp là none: khen, cảm ơn, chê người đối thoại (kể cả thầy cô trả lời trong nhóm); quảng cáo, chiêu mộ CLB (kể cả thành viên giới thiệu CLB của mình); câu trả lời có/không, khi nào, bao nhiêu; nhờ vả, rủ rê; đùa dưới dạng góp ý mà không chê; than về bản thân; chỉ bộc lộ cảm xúc; chê một cá nhân không đại diện cho trường; "+1" đáp lại một lời khuyên.
  - suggest khi câu chỉ việc cần làm hoặc nơi cần đến.
  - Ràng buộc: topic = unk thì stance chỉ là none hoặc unk.
- **emotion:**
  - Mặc định neutral. Chỉ gán cảm xúc khi có dấu hiệu: emoji, dấu cười, từ cảm thán, từ chỉ cảm xúc của chính người viết, chữ kéo dài thể hiện cảm xúc, lời chửi nặng.
  - Lời khen chê thuần túy ("dạy hay", "tuyệt vời luôn") là neutral.
  - Câu mỉa mai thì gán cảm xúc thật.
- **Gộp cảm xúc** khi có từ 4 người hoặc 4 mô hình: `emotion_1` cần 3/4 phiếu, `emotion_2` cần 2/4.

## 4. Đã làm xong

- **Làm sạch** (Colab lần 3, 2026-11-12): regex kết hợp NER NlpHUST, che `[NAME]`, `[USER]`, `[ADDRESS]`, `[URL]`, `[PHONE]`, `[STUDENT_ID]`...; không lọc emoji, từ tục, teencode. Tỷ lệ sót tên ước khoảng 2,7% (đo ở lần 1).
- **Vòng 1** (240 câu, `data/gan_nhan/vong1/`): Hảo và Triệu gán độc lập (2026-11-19), κ toxicity 0,647, topic 0,541, stance 0,357, emotion_1 0,364. **Cả 4 người soát chung** trên file `da_chot/tong_hop_vong1_Hao_Trieu_da_chot.xlsx` (2026-11-20). Vì vậy vòng 1 chỉ có κ cặp Hảo–Triệu; κ nhiều người phải lấy từ vòng 2. Không cần ai gán lại vòng 1.
- **Rà gold vòng 1** (2026-11-24, Claude chốt theo yêu cầu): 95 câu suggest và 44 câu topic = unk có stance, kèm 3 ô trống. Kết quả và lý do từng câu trong `data/gan_nhan/vong1/ra_soat_suggest_vong1_da_chot.xlsx` và `xem_lai_stance_vong1_da_chot.xlsx`. Gold đã cập nhật tại `data/gan_nhan/vong1/gold_vong1.csv`, bản cũ là `gold_vong1_truoc_ra_soat.csv`. Stance đổi 90 câu (suggest 95 → 32), topic đổi 22 câu, 0 câu vi phạm ràng buộc, không còn ô trống. Hai script của đợt rà (`scripts/ra_soat/chot_vong1.py`, `ra_soat_suggest.py`) và hai file đề xuất gốc đã xóa ngày 2026-11-27 theo yêu cầu của Triệu; script còn trong commit `2b39403`, nội dung file đề xuất gốc đã có đủ trong bản `_da_chot`.
- Phân bố gold vòng 1 sau rà: toxicity clean 190 / attack 25 / profane 24 / unk 1; topic academics 81 / unk 58 / student_life 56 / administration 39 / facilities 6; stance none 137 / oppose 33 / suggest 32 / support 23 / unk 15; emotion_1 neutral 139 / joy 29 / sadness 23 / fear 17 / surprise 12 / anger 11 / unk 9.
- **Vòng 2 đã tạo file** (2026-11-24): `python scripts/tao_mau_gan_thu.py 2` → `data/gan_nhan/vong2/gan_thu_vong2_{Hao,Sinh,Trieu,Long}.xlsx` và `tong_hop_vong2.csv` (nguồn mẫu từng câu). 240 câu train, 229 bài đăng, không trùng vòng 1; 120 ngẫu nhiên + 4 × 30 câu ưu tiên nhãn hiếm (công kích, cơ sở vật chất, tức giận/ngạc nhiên, ủng hộ). Script có `DAU_HIEU_THEO_VONG`; đã kiểm tra chạy lại vòng 1 ra đúng mẫu cũ. Sheet `huong_dan` của file vòng 2 đã nhắc các quy tắc mục 7 và 4 quy tắc mới. Đọc lướt thấy nhóm ủng hộ và tức giận/ngạc nhiên lẫn nhiều câu không mang nhãn đó ("xứng đáng độc thân", "tức là"), nên khi báo cáo kết quả theo `nguon_mau` đừng coi 30 câu mỗi nhóm là 30 câu nhãn hiếm; khi làm vòng 3 nên siết lại regex.
- **Vòng 2 xong, gold theo bản 5.**
  - Hảo và Long gán theo bản 3 (nộp 2026-11-26). Cohen κ: toxicity 0,669; topic 0,437; stance 0,215; emotion_1 0,157.
  - Triệu chốt nhãn (2026-11-27), rồi quyết định **không gán tay thêm** và ủy quyền cho Claude.
  - Claude sao lưu file chốt (`data/gan_nhan/vong2/da_chot/..._truoc_ra_soat.xlsx`) rồi sửa 153 ô trên 123 câu theo bản 5. Ô đổi tô xanh, lý do ở `ghi_chu_hop`, danh sách ở sheet `da_ap_dung`.
  - `scripts/xuat_gold.py` xuất `data/gan_nhan/vong2/gold_vong2.csv` (240 câu; 123 câu có nhãn `ra_soat_claude`). Phân bố stance: none 194, support 18, suggest 15, oppose 10, unk 3.
  - Không làm vòng 3; Sinh không gán vòng 2.
- **Còn lộ thông tin cá nhân:** mã sinh viên trong bình luận cha của câu 1 vòng 2; câu 58, 73, 215, 218 vòng 2 nghi còn tên người; 4 câu sót tên Triệu ghi ở vòng 1.
- **Sắp xếp lại repo** (2026-11-25): `docs/`, `scripts/`, `data/` (đổi tên từ `Datasets_N12_ban_giao/`), `huggingface/`. Đã kiểm tra `scripts/tao_mau_gan_thu.py` ở chỗ mới sinh lại đúng mẫu vòng 1 và vòng 2. Phần giai đoạn cũ đã xóa (xem mục 1).

## 5. Lộ trình tiếp theo

Nhóm không gán tay nữa: LLM gán, Claude phân xử, người trong nhóm duyệt kết quả và lo pháp lý. Chi tiết và lịch nằm ở `docs/Ke_hoach_tiep_theo_NLP_N12.docx`.

1. **Rà gold vòng 1 theo bản 5** (gold vòng 1 chốt theo bản 3).
   - Sao lưu, ghi đề xuất và lý do ra Excel, rồi áp dụng.
   - Đánh dấu `ra_soat_claude` ở cột cách chốt.
   - Chuẩn hóa `emotion_2` sang dấu `;`.
2. **Che nốt thông tin cá nhân** ở `masked.csv` và mọi file sinh ra từ nó.
   - Sao lưu và ghi log; quét các dạng lặp lại; thêm luật vào `clean_dataset.py`.
   - Nhờ một người xác nhận.
3. **Prompt và script gán bằng LLM.**
   - Prompt viết từ bản 5; ví dụ lấy từ gold, không lấy từ tập test.
   - Đầu ra JSON có 5 cột nhãn và cờ `hard`; script kiểm tra nhãn hợp lệ và ràng buộc.
   - Chạy theo batch, chạy tiếp được khi lỗi; ghi log, token, chi phí; nhiệt độ 0. Chỉ gửi dữ liệu đã che.
4. **Chạy thử trên 480 câu gold.**
   - Chỉnh prompt trên vòng 2, kiểm tra trên vòng 1.
   - Dùng 2–3 LLM, ít nhất một LLM khác hãng, vì gold có nhiều nhãn do Claude chốt.
   - Báo κ theo từng hướng, báo riêng phần nhãn `dong_y`.
   - Mục tiêu: toxicity, topic ≥ 0,67; stance, emotion ≥ 0,5. Đạt thì khóa prompt.
5. **Nhóm chọn LLM, ngân sách và phạm vi** (toàn bộ 136.609 câu hay 20–30 nghìn câu), dựa trên số token đo được ở bước 4.
6. **Gán toàn bộ và tập test.**
   - Lấy đa số giữa các LLM; Claude phân xử câu bất đồng; ghi `label_source`.
   - Tập test 1.500–2.000 câu: phân xử mọi câu bất đồng.
   - Khuyến nghị một người duyệt khoảng 200 câu test; nếu không thì ghi là hạn chế.
7. **Kiểm tra tự động.**
   - Ràng buộc và tổ hợp nhãn đáng ngờ.
   - Một mô hình khác gán lại khoảng 5% để kiểm tra mù.
   - Bỏ khỏi train các câu trùng với test (`cross_split_duplicate`, 9.014 dòng).
   - Quét lại thông tin cá nhân; thống kê phân bố nhãn.
8. **Baseline** (tùy chọn): BoW, TF-IDF, fastText, PhoBERT, XLM-R; báo Macro-F1.
9. **Đóng gói và công bố** khi phần pháp lý đã xong.
   - Script xuất parquet vào `huggingface/data/`.
   - Điền dataset card: mô tả nhãn theo bản 5, cách gán bằng LLM, κ, hạn chế.
   - Repo gated, duyệt thủ công; đẩy lên bằng `huggingface_hub`.

Làm song song, không chặn việc gán:
- **Pháp lý, đạo đức (chặn công bố):** hỏi giảng viên về phê duyệt đạo đức; xác định group công khai hay kín (file dữ liệu không có cột group, phải tra danh sách lúc cào); điều khoản Meta (scraper dùng cookie); Luật 91/2025/QH15 (Điều 14, 19) với người có chuyên môn; loại group kín khỏi bản công bố nếu chưa có căn cứ. Không đưa ra kết luận pháp lý thay người có chuyên môn.
- **Làm sạch còn dở:** sửa 4 câu sót tên Triệu báo ở vòng 1 và các câu trong sheet `thong_tin_ca_nhan` của file rà soát vòng 2. Che trong `masked.csv` và mọi file sinh từ nó (sao lưu trước, ghi log); lỗi lặp lại thì thêm luật vào `clean_dataset.py`; đọc khoảng 50 dòng `post_text` và 50 dòng `parent_text`; quyết định giữ hay bỏ các dòng cờ spam / ít thông tin; cập nhật mục kết quả trong `docs/Quy_tac_lam_sach_du_lieu_NLP_N12.docx` theo lần chạy 3.
- Giai đoạn 1 còn mở: đối chiếu định nghĩa OFFENSIVE, HATE của ViHSD và nhãn UIT-VSMEC với bài báo gốc.

## 6. Bản đồ file chính

| File | Vai trò |
|---|---|
| `TIEN_TRINH_DATASET.md` | Tiến trình chi tiết, checklist, nhật ký. Cập nhật sau mỗi bước |
| `docs/` | Tài liệu `.docx`: quy chuẩn, thiết kế, quy tắc làm sạch, kế hoạch tổng thể (`Ke_hoach_tong_the_NLP_N12.docx`, 27/11, không chứa kết quả) và kế hoạch tiếp theo (`Ke_hoach_tiep_theo_NLP_N12.docx`, 27/11, hướng gán bằng LLM, 14 điểm còn vướng) |
| `scripts/` | Toàn bộ code; chạy từ thư mục gốc repo |
| `data/` | Dữ liệu nhận riêng (`cleaned/`, `gan_nhan/`), không commit |
| `huggingface/README.md` | Dataset card nháp để công bố trên Hugging Face |
| `docs/Quy_chuan_gan_nhan_4_huong_NLP_N12_ban5.docx` | Quy chuẩn gán nhãn, bản 5 (bản chốt). Bản 4 giữ để đối chiếu; bản 3 đã xóa, còn trong commit `2b39403` |
| `scripts/xuat_gold.py <vòng> <file_chốt> [người chốt]` | Xuất gold từ file chốt, kiểm tra, ghi cách chốt |
| `data/gan_nhan/vong2/gold_vong2.csv` | Gold vòng 2 theo bản 5 (240 câu) |
| `docs/Thiet_ke_du_lieu_da_huong_NLP_N12.docx` | Thiết kế 4 hướng, so sánh UIT-VSFC, UIT-VSMEC, ViHSD |
| `docs/Quy_tac_lam_sach_du_lieu_NLP_N12.docx`, `scripts/clean_dataset.py` | Quy trình và script làm sạch |
| `data/cleaned/masked.csv` | Dataset đã che, 16 cột: `post_uid`, `comment_uid`, `parent_uid`, `comment_type`, `post_text`, `parent_text`, `text_public`, `split`, `data_status`, `pii_types`, `is_low_info`, `is_spam_candidate`, `post_is_ad_candidate`, `parent_missing`, `post_missing`, `cross_split_duplicate` |
| `scripts/tao_mau_gan_thu.py [vòng]` | Tạo file gán thử, không lấy lại câu các vòng trước |
| `scripts/tong_hop_gan_thu.py <out.xlsx> <file>...` | Tổng hợp, κ, Fleiss κ |
| `data/gan_nhan/vong1/gold_vong1.csv` | Gold vòng 1 sau rà (240 câu) |
| `data/gan_nhan/vong1/*_da_chot.xlsx` | Nhãn và lý do đợt rà gold vòng 1 |
| `data/gan_nhan/vong2/` | `tong_hop_vong2.csv` (nguồn mẫu), bài của Hảo, Long trong `da_gan/`, file chốt `tong_hop_vong2_Hao_Long.xlsx` (Triệu chốt 27/11), `da_chot/` để sao lưu |
| `data/gan_nhan/vong2/ra_soat_chot_vong2_Hao_Long.xlsx` | Đề xuất rà file chốt vòng 2 (Claude, 27/11): sheet `de_xuat` (130 ô, mức A–D, cột `nhom_quyet` để Triệu duyệt), `can_nhom_quyet` (9 câu hỏi), `thong_tin_ca_nhan`, `thong_ke` |
| `scripts/ra_soat/docx2txt.py` | Đọc docx khi không có pandoc (script rà gold vòng 1 đã xóa ngày 27/11) |

## 7. Cách trả lời người dùng

- Khi được hỏi "làm gì tiếp": đọc TIEN_TRINH, kiểm tra trạng thái thật của file (ví dụ thư mục `da_gan/` đã có file chưa, cột nhãn đã điền chưa) rồi mới trả lời. Lệnh kiểm tra nhanh một vòng (chạy từ thư mục gốc repo; đổi `vong2` thành vòng đang gán):
  ```
  PYTHONIOENCODING=utf-8 python -c "import pandas as pd, glob; [print(f, pd.read_excel(f, sheet_name='gan_nhan')[['toxicity','topic','stance','emotion_1']].notna().sum().to_dict()) for f in sorted(glob.glob('data/gan_nhan/vong2/**/gan_thu_vong2_*.xlsx', recursive=True))]"
  ```
- Người dùng có thể giao Claude tự chốt nhãn thay nhóm (đã làm ở vòng 1). Khi đó vẫn ghi lý do từng câu, ghi `ra_soat_claude` ở `*_cach_chot`, sao lưu gold, và nhắc rằng cần một người duyệt lại để paper khai báo đúng.
- Trình bày theo kiểu ngắn gọn, có bảng số liệu trước/sau khi sửa nhãn; người dùng thích nhận file Excel để tự soát (gửi file bằng SendUserFile nếu có).
- Nêu rõ cái gì đã kiểm chứng, cái gì là ước tính. Không khẳng định số liệu chưa đo lại.
- Sau mỗi việc hoàn thành, cập nhật TIEN_TRINH_DATASET.md (checklist + nhật ký có ngày).

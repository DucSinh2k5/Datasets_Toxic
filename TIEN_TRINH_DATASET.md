# Tiến trình: dataset 4 hướng và paper (NLP_N12)

Cập nhật lần cuối: 2026-11-27

**Mục tiêu:** từ khoảng 140 nghìn bình luận Facebook của sinh viên PTIT, tạo bộ dữ liệu gán nhãn theo 4 hướng (độc hại, chủ đề, lập trường và góp ý, cảm xúc), viết paper và công bố dataset nếu đủ điều kiện pháp lý, đạo đức.

## Đang ở đâu

**Giai đoạn 4 (gán bằng LLM): prompt đã khóa ngày 2026-11-27, chuẩn bị gán toàn bộ theo đợt.** Nhóm không gán tay thêm; quy chuẩn chốt ở bản 5; hai bộ gold (480 câu) theo bản 5; `masked.csv` đã che bổ sung hai đợt (Triệu xác nhận). Sau 5 lần chạy trên Kaggle (Qwen2.5-7B, Qwen3-14B p1, Qwen3-30B-A3B p2, Qwen3-14B p2, Qwen3-14B p3), Triệu đồng ý khóa: **Qwen3-14B-AWQ + bộ prompt tách hướng `ban5-en-tach-p3`** (chi tiết ở checklist giai đoạn 4). κ so với gold vòng 1 (tập kiểm tra, bỏ câu trùng prompt): toxicity 0,660, topic 0,710, stance 0,494, emotion_1 0,530; vòng 2: 0,600 / 0,720 / 0,488 / 0,574. Toxicity và stance còn dưới mục tiêu ban đầu (0,67 và 0,5) nhưng đã ngang hoặc hơn κ giữa hai người (toxicity 0,65–0,67, topic 0,44–0,54, stance 0,22–0,36, emotion 0,16–0,36). Ý tưởng cột Note cho câu khó đã bỏ.

**Cấu trúc repo (từ 2026-11-25):** tài liệu trong `docs/`, code trong `scripts/`, dữ liệu trong `data/` (không commit), dataset card nháp trong `huggingface/`. Chạy lệnh từ thư mục gốc repo. Phần Nhật ký trước ngày này ghi đường dẫn cũ, khi chưa có các tiền tố `docs/`, `scripts/`, `data/`.

**Việc tiếp theo ngay** (lộ trình đến khi công bố: `docs/Ke_hoach_tong_the_NLP_N12.docx`; file kế hoạch tiếp theo viết trước khi chọn Kaggle nên một phần đã cũ):
1. ~~Chốt cách chia đợt~~ (xong 27/11: 14 đợt, 4 người chạy song song; bảng phân công ở checklist giai đoạn 4)
2. ~~Claude viết script chia đợt, gói, notebook, ghép~~ (xong 27/11). **Việc ngay: gửi `goi_<tên>.zip` và `scripts/llm/kaggle_gan_dot.ipynb` cho từng người, mỗi người chạy đợt của mình**
3. Gán toàn bộ (khoảng 84 giờ GPU); 480 câu gold giữ nhãn người
4. Giai đoạn 5: người gán tay một tập con của test (khoảng 1.500–2.000 câu), kiểm tra mù một mẫu nhãn LLM, bỏ câu train trùng test
5. Giai đoạn 6–8: baseline, rà soát pháp lý và đạo đức (chặn công bố), paper và dataset card

Song song (chỉ người trong nhóm làm được, chặn công bố): hỏi giảng viên về đạo đức, danh sách 16 group, điều khoản Meta, Luật 91/2025/QH15. Commit các thay đổi đang chờ (`scripts/clean_dataset.py`, `scripts/che_bo_sung.py`, `scripts/llm/`, tài liệu).

## Tổng quan

| Giai đoạn | Trạng thái |
|---|---|
| 1. Thiết kế nhãn | **Xong**: quy chuẩn bản 5 (bản chốt, 2026-11-27) |
| 2. Làm sạch và che thông tin | **Xong** (bản lần 3, che bổ sung hai đợt ngày 2026-11-27, đã xác nhận), còn vài mục kiểm tra phụ |
| 3. Gán thử và đo đồng thuận | **Dừng** sau 2 vòng (nhóm không gán tay thêm); hai bộ gold (480 câu) đều theo bản 5 |
| 4. Gán nhãn toàn bộ | **Đang làm**: prompt `ban5-p1` và script đã có, chờ khóa API để chạy thử trên gold và khóa prompt |
| 5. Kiểm tra chất lượng nhãn | Chưa làm |
| 6. Mô hình baseline | Tùy chọn, chưa làm cho 4 hướng |
| 7. Rà soát pháp lý, đạo đức | Chưa làm, **chặn việc công bố** |
| 8. Viết paper và công bố | Chưa làm (đã có dataset card nháp `huggingface/README.md`) |

## Giai đoạn 1: Thiết kế nhãn

Tài liệu: `docs/Thiet_ke_du_lieu_da_huong_NLP_N12.docx`

- [x] Chọn 4 hướng, có lý do chọn và bảng Nhãn / Gộp từ / Tại sao / Ví dụ
- [x] So sánh với UIT-VSFC, UIT-VSMEC, ViHSD
- [x] Chốt hướng độc hại 3 nhãn: Không độc hại, Thô tục, Công kích (nhóm chốt 2026-11-12)
- [ ] Đối chiếu định nghĩa OFFENSIVE, HATE của ViHSD và nhãn UIT-VSMEC với bài báo gốc
- [x] Viết bản nháp 1 quy chuẩn gán nhãn 4 hướng dựa trên các chuẩn đã công bố (OLID, UIT-VSFC, SemEval-2016 Task 6, SemEval-2019 Task 9, GoEmotions, SemEval-2018 Task 1, UIT-VSMEC): `docs/Quy_chuan_gan_nhan_4_huong_NLP_N12.docx` (2026-11-12). File này giữ bản nháp 1 đến 3; đã xóa ngày 2026-11-27, còn trong commit `2b39403`
- [x] Bản nháp 2 (2026-11-14): nhãn tiếng Anh, thêm `unk` cho mọi hướng, cảm xúc đa nhãn ghi theo `emotion_1` và `emotion_2`. Đã tạo lại 4 file Excel vòng 1 theo nhãn mới (cùng 240 câu, chưa ai gán)
- [ ] Nhóm duyệt quy chuẩn, rồi sửa sau mỗi vòng gán thử

Nhãn tiếng Anh theo yêu cầu của giảng viên (quy chuẩn bản nháp 2, 2026-11-14). Mỗi hướng có thêm `unk` khi không chọn được nhãn nào; chủ đề dùng `unk` thay cho Khác.

| Hướng | Nhãn |
|---|---|
| toxicity | clean (Không độc hại), profane (Thô tục), attack (Công kích), unk |
| topic | academics (Đào tạo), facilities (Cơ sở vật chất), administration (Hành chính, chính sách và tài chính), student_life (Hoạt động và đời sống sinh viên), unk |
| stance | support (Ủng hộ), oppose (Phản đối), suggest (Đề xuất), none (Không ý kiến), unk |
| emotion | joy (Vui vẻ), sadness (Buồn bã), anger (Tức giận), fear (Lo lắng), surprise (Ngạc nhiên), neutral (Không cảm xúc), unk. Đa nhãn không giới hạn: `emotion_1` là cảm xúc chính, `emotion_2` là các cảm xúc còn lại xếp giảm dần theo độ rõ, cách nhau bằng `;` |

## Giai đoạn 2: Làm sạch và che thông tin

Tài liệu: `docs/Quy_tac_lam_sach_du_lieu_NLP_N12.docx`. Script: `scripts/clean_dataset.py`.

**Đầu vào phải là** `tonghopcmt_n12_backup_truoc_khi_them_toxic.xlsx`. Không dùng `tonghopcmt_n12.xlsx`, vì 3.123 dòng cuối của file đó là dữ liệu toxic từ nguồn ngoài PTIT.

- [x] Khảo sát file thô và `message_clean` cũ
- [x] Nghiên cứu quy trình (deep research)
- [x] Viết script: đổi ID, NFC, che thông tin ở 3 cột, khử trùng, gắn cờ, chia theo bài đăng, tự kiểm tra
- [x] Chạy trên toàn bộ file (bản chỉ có regex, ngày 2026-11-08)
- [x] Đối chiếu 136.913 dòng với bản gốc: văn bản chỉ khác ở chỗ che, không lọc emoji, dấu câu, teencode
- [x] Viết `compare_ner.py` so sánh regex với 2 mô hình NER (NlpHUST ELECTRA, OpenMed PII). Tùy chọn, chạy khi muốn đổi cách kết hợp mô hình. Đã bỏ khỏi repo ngày 2026-11-25, lấy lại từ commit `7fa0312` nếu cần
- [x] Ghép NER vào `scripts/clean_dataset.py`
- [x] Chạy Colab lần 1 (2026-11-11): NER chạy được nhưng có 3 lỗi. OpenMed che nhầm "1", "b", "A2", "ptit" thành địa chỉ, NlpHUST che nhầm "T", "M", "Ib", "Mik" thành tên, và 174 dòng mất emoji
- [x] Sửa 3 lỗi: bỏ OpenMed, thay bằng luật che địa chỉ có số; chặn chữ cái đơn, mã viết hoa ngắn và từ viết tắt thường gặp; cắt emoji, dấu câu ở hai đầu đoạn NER
- [x] Tạo `scripts/danh_sach_dia_danh_truong.csv` (tỉnh, huyện, trường đại học) để không che nhầm địa danh, tên trường
- [x] Chạy Colab lần 2 (2026-11-11) với bản đã sửa, kết quả đặt vào `data/cleaned/`, bản regex cũ chuyển thành `data/cleaned_ban_cu/`
- [x] Đối chiếu lần 2 với file gốc: 0 dòng lệch, emoji chỉ đổi ở 7 dòng (5 dòng do link), không còn che nhầm "T", "M", "Ib", địa chỉ còn 282 đoạn và đều có "ngõ" hoặc "số"
- [x] Viết lại `docs/Quy_tac_lam_sach_du_lieu_NLP_N12.docx` thành tài liệu quy trình và kết quả làm sạch (theo Colab lần 2)
- [x] Soát tay lần 1 trên kết quả Colab lần 2 (2026-11-12), tổng hợp trong `data/cleaned_lan2/private/audit_tong_hop.csv`:
  - Mẫu hiện tại, nhóm chưa che (250 câu): sót tên thật 6 (2,4%), 29 câu chỉ là tên ẩn danh do Facebook tạo (không tính)
  - Mẫu hiện tại, nhóm đã che (250 câu, đã xác nhận đọc hết): sót tên thật 8 (3,2%), che nhầm 3 (1,2%), 3 câu tên ẩn danh Facebook
  - Ước tính toàn bộ dataset còn khoảng 2,7% câu sót tên (khoảng tin cậy 95% của từng nhóm: 1,1–5,1% và 1,6–6,2%)
  - Bổ sung: 250 câu nhóm đã che lấy nhầm từ mẫu bản cũ (`cleaned_ban_cu`), 247 câu có kết quả che giống bản hiện tại: sót 9, che nhầm 5
  - Lỗi chính: tên viết thường sau thầy/cô ("thầy sơn"), viết tắt "th Ninh", "c VAnh", chữ "Anh" của tên bị giữ như danh xưng, tên ẩn danh Facebook chưa thống nhất; NER che nhầm "Cmm", "rep", "Cũng"
- [x] Sửa script theo các lỗi trên (2026-11-12): che tên ẩn danh Facebook thành `[USER]`; bắt "a/c/e/th + Tên", tên viết thường sau thầy/cô/anh/chị (danh sách tên riêng, bỏ tên trùng từ thường), "TTuấnn", "VAnh", "Q. Sáng"; gộp phần tên còn sót ("Anh [NAME]", "[NAME] Đỗ", "[NAME] nhi"); không che Cmm, rep, Cũng, Năm, Trung Thu, Phùng Khoang, Hà Lội. Thử với NER giả: 136.738 dòng, emoji đổi 5 dòng
- [x] Chạy Colab lần 3 (2026-11-12) với script mới. Kết quả đặt vào `data/cleaned/`, bản lần 2 chuyển thành `data/cleaned_lan2/` (kèm file soát lần 1)
- [x] Kiểm tra tự động lần 3: 0 dòng lệch so với bản gốc, emoji đổi 7 dòng (5 dòng do link). Trong 23 câu sót và 7 câu che nhầm đã soát ở lần 1, lần 3 sửa được 17 câu sót và 6 câu che nhầm. Còn sót: tên một từ ở đầu câu ("Quang năm nay", "Đức ai bảo"), "VŨ", "pHát"; NER vẫn che "daisuki daiyo"
- [x] Soát 500 câu mẫu lần 3 (`data/cleaned/private/audit_sample.csv`): nhóm xác nhận đã soát và đồng ý với kết quả, không cần sửa thêm (2026-11-12). Chưa có file ghi kết quả soát lần này, nên khi báo cáo tỷ lệ sót cần dùng số đo của lần 1
- [x] Che bổ sung (2026-11-27, Claude, `python scripts/che_bo_sung.py --ghi`), không chạy lại NER. Thêm 7 luật vào `scripts/clean_dataset.py` (`SUPPLEMENT_RULES`, có ca kiểm tra trong `self_check`): mã sinh viên thiếu tiền tố năm ("mã SV DCxx123"); tên giảng viên viết thường sau thầy/thày/cô, kể cả tên trùng từ thường, có danh sách chữ đứng sau để không che nhầm ("cô tâm huyết", "cô liên hệ", "thầy cô biên soạn", "thầy trường mình"); họ tên đầy đủ viết thường sau thầy/cô và dạng "họ thị tên"; tên viết thường trước "ơi" (trừ "tổ quốc ơi", "các b nam ơi"); tên viết hoa sau "THẦY", "CÔ" và sau `[NAME]` (trừ "[NAME] LIÊN HỆ"). Thêm danh sách 18 chuỗi che tay `data/cleaned/che_bo_sung/thu_cong.csv` (không để trong repo vì chứa tên thật) cho các câu đã biết ở gold hai vòng mà luật không bắt được. Trước khi thêm, đã chạy thử trên toàn bộ masked.csv và đọc từng chỗ khớp
  - Kết quả: 259 đoạn văn bản khác nhau, tức 365 dòng `post_text`, 149 dòng `parent_text`, 230 dòng `text_public` (`pii_types` thêm loại ở 107 dòng). Theo luật: tên sau thầy/cô 214 đoạn, che tay 18, tên trước "ơi" 14, tên hoa sau THẦY/CÔ 10, phần tên cạnh [NAME] 6, họ tên 2, mã sinh viên 1. Đã che mọi trường hợp đã biết: mã sinh viên ở câu 1 vòng 2; câu 58, 73, 215, 218 vòng 2; câu 1, 6, 65, 150, 161, 190, 198, 203 vòng 1. Câu 12 vòng 1 ("Cậu bé lùn", Triệu ghi chưa lọc hết tên) không phải tên người nên giữ
  - Kiểm tra: số dòng, thứ tự và mọi cột không phải văn bản giữ nguyên; emoji không đổi; chạy lại script không còn gì để che. Đã sửa cùng cách 108 ô trong 16 file của `data/gan_nhan/` (gold, file gán, file chốt, file rà), nhãn không đổi; danh sách ô ở `data/cleaned/che_bo_sung/log_file_gan_nhan.csv`
  - Sao lưu: `data/cleaned/che_bo_sung/masked_truoc_che_bo_sung.csv` (bản gốc, còn tên thật). Triệu đã xác nhận `xac_nhan_che_bo_sung.xlsx` (27/11): 247 dòng đúng, 9 `con_sot`, 2 `che_nham`, 1 để trống (coi là đúng)
- [x] Che bổ sung đợt 2 (2026-11-27, Claude) theo kết quả xác nhận đợt 1:
  - `con_sot`: tên giảng viên viết hoa chữ đầu sau thầy/cô (luật đợt 1 chỉ bắt chữ thường) và vài tên chưa có trong danh sách. Thêm luật `ten_hoa_chu_dau_sau_thay_co` (bỏ tên môn học: "cô Văn", "thầy Anh"...), thêm 12 tên vào `TEACHER_ONLY`, 3 chữ vào `TEACHER_NOT_NEXT`, 27 chuỗi che tay (tên trùng từ thường như "thế", "công", "chung", "cầm"; chữ viết tắt lặp nhiều lần). Quét toàn bộ masked.csv thấy cùng loại lỗi ở nhiều câu khác nên đợt 2 đổi 219 đoạn văn bản (286 dòng `post_text`, 168 `parent_text`, 184 `text_public`; `pii_types` thêm loại ở 100 dòng); đã đọc từng chữ bị che, không thấy che nhầm
  - `che_nham` dòng 14: "HUY <mã>" là cú pháp tin nhắn hủy gói cước, không phải tên. Sửa luật `NAME_UPPER` và trả lại nguyên văn trong masked.csv và 5 ô file gán nhãn (gồm `gold_vong2.csv`). `che_nham` dòng 63: Triệu chọn giữ che và che thêm tên ở đầu câu
  - `scripts/che_bo_sung.py` đổi cách chạy: luôn dựng lại masked.csv từ `masked_truoc_che_bo_sung.csv` bằng luật và danh sách che tay hiện tại (tái lập được, khôi phục được chỗ che nhầm), so với masked.csv đang có, ghi file của đợt mới với hậu tố `_dot2` (không ghi đè file đã xác nhận), sao lưu masked.csv (`masked_truoc_dot2.csv`) và các file gán nhãn (`sao_luu_file_gan_nhan_dot2/`) trước khi ghi. Chạy lại không còn gì đổi
  - Triệu xác nhận đúng toàn bộ 219 dòng qua chat (27/11; Claude ghi `dung` vào cột `xac_nhan` kèm ghi chú vì file lưu còn trống). Đã chuyển cả thư mục vào `data/cleaned/private/che_bo_sung/`, xóa bản sao lưu tạm của đợt 2 (`masked_truoc_dot2.csv`, `sao_luu_file_gan_nhan_dot2/`); script đọc thư mục ở chỗ mới
  - Giới hạn còn lại: chữ viết tắt tên giảng viên (2–3 chữ in hoa sau thầy/cô) và tên đứng một mình vẫn có thể sót
  - Giới hạn: luật chỉ bắt tên sau thầy/thày/cô hoặc trước "ơi"; tên viết thường đứng một mình, tên không dấu vẫn có thể sót (ước tính 2,7% câu còn sót tên đo ở lần 1 chưa đo lại). Một số tên ít gặp sau thầy/cô trùng động từ nên được che tay thay vì thêm vào luật
- [ ] Cập nhật mục kết quả trong `docs/Quy_tac_lam_sach_du_lieu_NLP_N12.docx` sau lần chạy 3
- [ ] Đọc thêm khoảng 50 dòng `post_text` và 50 dòng `parent_text`, vì mẫu 500 câu chỉ lấy từ cột bình luận
- [ ] Đọc mẫu từng nhóm cờ, quyết định loại hay giữ

Quy tắc đã chốt:
- Không lọc emoji, dấu câu thừa, chữ kéo dài, từ tục, teencode. Chỉ chuẩn hóa NFC, gộp khoảng trắng, bỏ dấu `'` do Excel, che thông tin cá nhân, xóa dòng trùng cùng ngữ cảnh.
- Giữ tên tỉnh, thành, quận huyện, tên trường, mã tòa nhà (A2, B5) và tên đường đứng sau "đường", "phố". Chỉ che địa chỉ có số ("số 12 ngõ 5", "ngách 3/14", "số 96 Trần Phú") bằng `[ADDRESS]`.
- Huyện, trường trùng tên người ("Thanh Hà", "Duy Tân") chỉ giữ khi đứng sau từ chỉ nơi chốn.
- Che tên 2 lớp: regex, rồi NlpHUST (`PERSON`). Không dùng OpenMed. Đổi cấu hình tại `NER_MODELS`.
- NER không được che chữ cái đơn ("t", "m" là tao, mày), mã viết hoa ngắn (D26, TL) và các từ như Ib, Mik, Mk, Ko.

Kết quả Colab lần 3 ngày 2026-11-12, bản chính thức (chi tiết trong `data/cleaned/report.json`):

| Mục | Số lượng |
|---|---|
| Đầu vào | 141.276 dòng, 22.144 bài đăng |
| Xóa vì trùng cùng ngữ cảnh | 4.667 |
| Đầu ra (`data/cleaned/masked.csv`) | 136.609 |
| Train / Val / Test (theo bài đăng) | 95.667 / 20.458 / 20.484 |
| Bình luận có che: tên | 53.070 |
| Tên ẩn danh Facebook và tag (`[USER]`) | 12.311 |
| Địa chỉ | 221 |
| URL / số điện thoại / mã SV, mã lớp | 2.712 / 875 / 96 |
| Email / dãy số dài | 30 / 20 |
| Cờ spam / ít thông tin | 7.231 / 6.512 |
| Cờ trùng giữa các tập | 9.014 |
| Dòng đổi số emoji | 7 |

Giới hạn đã biết:
- Điểm công bố của NlpHUST không đo trên bình luận mạng, nên tên viết thường, tên một từ và tên không dấu vẫn có thể sót. Tỷ lệ sót thật phải đo bằng 500 câu soát tay.
- NER vẫn che vài thứ không phải người dùng như tên trang (DoiMauBuuchinh), thương hiệu (Zenlish), ca sĩ (Jack), tên đường "Chiến Thắng" khi không có chữ "đường". Che thừa, không làm lộ thông tin.
- Luật địa chỉ có thể che nhầm vài cụm như "SỐ 1 Một" (khoảng vài chục trên 342 lần che).
- Danh sách địa danh là dữ liệu trước đợt sáp nhập 2025, chưa có cấp xã, phường. Danh sách trường chưa đối chiếu với danh sách của Bộ Giáo dục.
- Chưa bắt số điện thoại viết né (emoji số, chữ số full-width, viết bằng chữ).
- Có 5 dòng đổi số emoji sau khi che, có lẽ do emoji nằm trong link hoặc tag.

### Cách chạy trên Colab

1. Tạo notebook, bật GPU (T4), dùng tài khoản của nhóm.
2. Tải lên 3 file, đặt cùng chỗ trong `/content`: `scripts/clean_dataset.py`, `scripts/danh_sach_dia_danh_truong.csv`, `tonghopcmt_n12_backup_truoc_khi_them_toxic.xlsx`. Nếu đã có `data/cleaned/private/id_map.csv` thì tải lên cả file này vào `/content/cleaned/private/`, để `post_uid` và split giữ nguyên, gold các vòng vẫn khớp.
3. Chạy `!pip install -q transformers sentencepiece protobuf openpyxl`.
4. Chạy `!python clean_dataset.py`, giữ tab mở vì script không lưu giữa chừng.
5. Kiểm tra: dòng log ghi GPU, `rows_output` khoảng 136.600 đến 136.900, `NAME` lớn hơn khoảng 50.000, `ADDRESS` khoảng 200, `rows_where_emoji_count_changed` chỉ vài dòng.
6. Chạy `!zip -r cleaned.zip cleaned`, rồi tải `cleaned.zip` về.
7. **Xóa runtime** (Runtime → Disconnect and delete runtime), vì file gốc có thông tin cá nhân thật.
8. Đổi `data/cleaned` cũ thành `data/cleaned_ban_cu`, giải nén `cleaned.zip` vào `data/`.
9. Sao lưu mẫu thành `audit_sample_reviewed.csv` trước khi soát, vì chạy lại script sẽ ghi đè.

Hai file kết quả: `data/cleaned/masked.csv` (dataset đã lọc) và `data/cleaned/private/audit_sample.csv` (500 mẫu).

## Giai đoạn 3: Gán thử và đo đồng thuận

Cách làm: cả 4 người (Hảo, Sinh, Triệu, Long) gán độc lập cùng một tập mỗi vòng, 2–3 vòng, sau mỗi vòng họp xem câu bất đồng và sửa quy chuẩn. Script tạo file: `scripts/tao_mau_gan_thu.py [số vòng]`, file nằm trong `data/gan_nhan/vong<N>/`.

- [x] Tạo file vòng 1 (2026-11-12): 240 câu từ tập train, 234 bài đăng; 120 câu ngẫu nhiên và 120 câu ưu tiên nhãn hiếm (40 có từ tục, 40 có dấu hiệu đề xuất, 40 có dấu hiệu cảm xúc mạnh), đã trộn lẫn. Bỏ câu có cờ spam, ít thông tin. Nguồn mẫu của từng câu ghi trong `data/gan_nhan/vong1/tong_hop_vong1.csv`
- [x] Hảo và Triệu gán xong vòng 1 (2026-11-19). File gốc lưu trong `data/gan_nhan/vong1/da_gan/`. Tổng hợp bằng `scripts/tong_hop_gan_thu.py` ra `data/gan_nhan/vong1/tong_hop_vong1_Hao_Trieu.xlsx`
  - Cohen κ Hảo-Triệu: toxicity 0,647; topic 0,541; stance 0,357; emotion_1 0,364. Đồng ý tuyệt đối: 87,9% / 65,8% / 50,8% / 60,4%; cả tập cảm xúc 54,2%
  - 189/240 câu lệch ít nhất 1 hướng. Lệch có hệ thống: Hảo hay chọn none / neutral / unk, Triệu hay chọn có lập trường, có cảm xúc (stance none–oppose 48 câu, emotion neutral–joy 29 câu, topic unk–student_life 43 câu, toxicity clean–attack 19 câu)
  - Triệu ghi 4 câu còn sót tên chưa che, cần kiểm tra lại phần làm sạch
- [x] Cả 4 người (Hảo, Sinh, Triệu, Long) cùng soát và chốt vòng 1 trên một file (2026-11-20). File chốt lưu tại `data/gan_nhan/vong1/da_chot/tong_hop_vong1_Hao_Trieu_da_chot.xlsx`; gold vòng 1 xuất ra `data/gan_nhan/vong1/gold_vong1.csv` (240 câu, cột `*_cach_chot` ghi đồng ý hay phân xử). Vòng 1 chỉ có κ giữa Hảo và Triệu vì chỉ hai người gán độc lập; κ nhiều người phải lấy từ vòng 2. Không cần Sinh và Long gán lại vòng 1 vì đã xem gold
- [x] Quy chuẩn bản nháp 3 (2026-11-20): thêm mục 7 ghi các quy tắc rút ra từ vòng 1, kèm ví dụ
- [x] Nhóm chốt định nghĩa stance (2026-11-20): **lập trường hướng tới chủ đề của trường** (SemEval-2016), không dùng cho việc đồng tình hay phản bác người đối thoại. Đã ghi vào quy chuẩn bản 3, mục 7.3
- [x] Rà lại gold vòng 1 theo quy chuẩn bản 3 (2026-11-24). Claude chốt theo yêu cầu của nhóm, có ghi lý do từng câu:
  - 95 câu suggest: `data/gan_nhan/vong1/ra_soat_suggest_vong1_da_chot.xlsx`. Giữ 32 câu suggest, đổi 55 sang none, 7 sang oppose, 1 sang support. Lỗi chính: chỉ cung cấp thông tin, quảng cáo hoặc chiêu mộ CLB, rủ rê hoặc xin cho bản thân, đùa dưới dạng góp ý
  - 44 câu topic = unk nhưng có stance, kèm 3 ô trống (topic dòng 83, emotion dòng 140 và 142): `data/gan_nhan/vong1/xem_lai_stance_vong1_da_chot.xlsx`. 12 câu trùng với file 95 câu, nhãn hai file khớp nhau
  - Gold cập nhật tại `gold_vong1.csv`, bản trước khi rà là `gold_vong1_truoc_ra_soat.csv`. Ô nào đổi thì cột `*_cach_chot` ghi `ra_soat_claude`
  - Kết quả: stance đổi 90 câu, topic đổi 22 câu (21 câu từ unk sang chủ đề cụ thể), điền 2 ô emotion. Không còn ô trống, 0 câu vi phạm ràng buộc topic = unk thì stance chỉ là none/unk
  - Script chốt: `scripts/ra_soat/ra_soat_suggest.py` và `scripts/ra_soat/chot_vong1.py`. Nhãn và lý do đã ghi đầy đủ trong 2 file `_da_chot.xlsx`. Ngày 2026-11-27 đã xóa 2 script này (còn trong commit `2b39403`) và 2 file đề xuất gốc `ra_soat_suggest_vong1.xlsx`, `xem_lai_stance_vong1.xlsx` (đã kiểm tra: bản `_da_chot` chứa đủ mọi ô của bản gốc, các ô khác nhau đều là ô trống ở bản gốc)
  - **Lưu ý cho paper:** 114 nhãn gold vòng 1, ở 100/240 câu (stance 90, topic 22, emotion 2), do LLM (Claude) chốt, chưa có người duyệt lại. Nên có ít nhất một người đọc lướt 2 file `_da_chot`, và ghi rõ trong paper. Nếu dùng gold để chấm các LLM gán nhãn, kết quả có thể thiên về mô hình giống Claude; cân nhắc chỉ dùng gold từ vòng 2 để đánh giá LLM

Phân bố gold vòng 1 sau khi rà (240 câu):

| Hướng | Phân bố |
|---|---|
| toxicity | clean 190, attack 25, profane 24, unk 1 |
| topic | academics 81, unk 58, student_life 56, administration 39, facilities 6 |
| stance | none 137, oppose 33, suggest 32, support 23, unk 15 |
| emotion_1 | neutral 139, joy 29, sadness 23, fear 17, surprise 12, anger 11, unk 9 |

- [x] Quy chuẩn bản 4 (2026-11-26): `docs/Quy_chuan_gan_nhan_4_huong_NLP_N12_ban4.docx`, bản 3 giữ nguyên để đối chiếu. Mục 7.6 ghi 4 quy tắc từ đợt rà soát dưới đây; mục 8 ghi 5 quy tắc nhóm chốt sau vòng 2 (8.1 topic theo ngữ cảnh, unk chỉ khi câu không nói về việc gì; 8.2 phân định academics/administration/student_life; 8.3 stance chặt, phải có dấu hiệu trong câu; 8.4 emotion mặc định neutral, chỉ 7 nhãn; 8.5 ranh giới attack/clean). Đã sửa theo các quy tắc này ở mục 4, 5, 6 và bảng quy trình (nay là mục 9). Còn chờ: ví dụ ranh giới toxicity từ vòng 2; ngưỡng gộp cảm xúc 2/4 hay 3/4. Các quy tắc từ đợt rà soát:
  - suggest khi câu chỉ cụ thể việc cần làm hoặc nơi cần đến ("ra tòa A1 điểm danh lại"); none khi chỉ trả lời được hay không, khi nào, bao nhiêu ("sau 2/9 xin vẫn được")
  - Quảng cáo, chiêu mộ CLB, tin tuyển dụng: none
  - Đùa dưới dạng góp ý mà không chê gì ("đề nghị có CLB trai làng"): none; đùa hoặc mỉa mai có chê: oppose. Sửa câu chữ mục 5 cho rõ
  - Đồng tình hay phản bác bình luận cha về chủ đề của trường: gán topic theo bình luận cha (đã áp dụng, ví dụ câu 19, 85, 173, 198)
- [x] Tạo file vòng 2 (2026-11-24): `scripts/tao_mau_gan_thu.py 2` tạo 4 file `data/gan_nhan/vong2/gan_thu_vong2_<Tên>.xlsx` và `tong_hop_vong2.csv`. 240 câu từ train, 229 bài đăng, không trùng vòng 1; 120 câu ngẫu nhiên và 4 nhóm × 30 câu ưu tiên nhãn còn hiếm sau vòng 1 (công kích, cơ sở vật chất, tức giận/ngạc nhiên, ủng hộ). Sheet hướng dẫn có nhắc các quy tắc mục 7 và quy tắc suggest mới
  - Script đổi sang cấu hình dấu hiệu theo từng vòng (`DAU_HIEU_THEO_VONG`); đã kiểm tra chạy lại vòng 1 ra đúng 240 câu cũ
  - Đọc lướt: nhóm ủng hộ và tức giận/ngạc nhiên lẫn nhiều câu không mang nhãn đó ("xứng đáng độc thân", "tức là"), nên số câu nhãn hiếm thực tế sẽ dưới 30 mỗi nhóm
- [x] Hảo và Long gán vòng 2 độc lập theo bản 3 (nộp 2026-11-26, file trong `data/gan_nhan/vong2/da_gan/`). Sinh chưa gán. Triệu đã xem nhãn khi chốt nên không gán vòng 2 nữa. Đề xuất không gán thêm vòng 2 và đo κ 4 người ở vòng 3; nhóm chốt ở buổi họp. Mẫu vòng 2 của Sinh, Triệu không còn trong `vong2/`; cần thì tạo lại bằng `python scripts/tao_mau_gan_thu.py 2` **trước** khi tạo vòng 3
- [x] Tổng hợp 2 người ra `data/gan_nhan/vong2/tong_hop_vong2_Hao_Long.xlsx`, Cohen κ Hảo–Long (xem nhật ký 2026-11-26)
- [x] Triệu chốt nhãn vòng 2 trên file tổng hợp (2026-11-27): đủ 240 câu ở cả 4 hướng; `ghi_chu_hop` chỉ ghi 1 dòng (mã sinh viên chưa che ở câu 1); cột `stt` đã bị xóa nhưng thứ tự dòng không đổi
- [x] Claude rà file chốt theo bản 4 (2026-11-27), đề xuất ở `data/gan_nhan/vong2/ra_soat_chot_vong2_Hao_Long.xlsx`: 130 ô trên 112 câu (A 33, B 47, C 40, D 10; stance 70, topic 28, emotion 27, toxicity 5), 9 câu hỏi cần nhóm quyết, 5 câu còn lộ hoặc nghi lộ thông tin cá nhân. File chốt chưa bị sửa
- [x] Nhóm quyết định không gán tay thêm (2026-11-27). Triệu ủy quyền cho Claude sửa file chốt theo đề xuất và chốt 9 câu hỏi quy chuẩn theo gợi ý của Claude. Không làm vòng 3; Sinh không gán vòng 2
- [x] Claude sửa file chốt vòng 2 (2026-11-27): sao lưu ở `data/gan_nhan/vong2/da_chot/tong_hop_vong2_Hao_Long_truoc_ra_soat.xlsx`; áp dụng 130 đề xuất (câu 153 đổi sang none theo quyết định 5.5) và 23 ô sửa thêm cho khớp bản 5, tổng 153 ô trên 123 câu (stance 71, emotion 47, topic 30, toxicity 5). Ô đổi tô xanh, lý do ở `ghi_chu_hop` (mọi câu lệch đều có ghi chú), danh sách ở sheet `da_ap_dung`; thêm lại cột `stt`
- [x] Viết `scripts/xuat_gold.py`, xuất `data/gan_nhan/vong2/gold_vong2.csv`: 240 câu, 0 ô trống, 0 vi phạm ràng buộc. Cách chốt: 123/240 câu có ít nhất một nhãn `ra_soat_claude`
- [x] Quy chuẩn bản 5 (bản chốt) `docs/Quy_chuan_gan_nhan_4_huong_NLP_N12_ban5.docx`: gộp bản 4 và 9 quyết định thành một bộ quy tắc thống nhất (mục 3–6), có lịch sử phiên bản (mục 9)
- [x] Rà gold vòng 1 theo bản 5 (2026-11-27, Claude theo yêu cầu của Triệu). Claude đọc cả 240 câu kèm bài đăng, bình luận cha và nhãn của Hảo, Triệu. Sao lưu `data/gan_nhan/vong1/gold_vong1_truoc_ban5.csv`; danh sách từng ô đã đổi, mức (A sai rõ, B nên sửa, C ranh giới), căn cứ bản 5 và lý do ở `data/gan_nhan/vong1/ra_soat_gold_vong1_ban5.xlsx` (sheet `da_ap_dung`, có cột `nguoi_duyet` để duyệt; `thong_ke` có phân bố trước và sau)
  - Đổi 171 ô trên 131 câu, ô đổi ghi `ra_soat_claude` ở cột cách chốt. Lỗi chính giống vòng 2: topic unk ở câu phản hồi trong chuỗi có chủ đề (58 câu unk còn 9); học bổng, học phí, tuyển sinh, chuẩn đầu ra gán academics hoặc student_life; stance support hoặc oppose cho câu trả lời thông tin, khen chê người đối thoại, kể chuyện bản thân; emotion không có dấu hiệu mà vẫn có cảm xúc, có dấu cười mà neutral (theo cách gán của gold vòng 2)
  - Chủ đề giữ nhất quán với 22 bài đăng có ở cả hai vòng. `emotion_2` dùng dấu `;` như vòng 2. 0 ô trống, 0 vi phạm ràng buộc
  - Phân bố sau khi rà: toxicity clean 199, profane 26, attack 15; topic academics 82, student_life 77, administration 60, facilities 12, unk 9; stance none 179, suggest 33, oppose 21, support 6, unk 1; emotion_1 neutral 149, joy 31, sadness 23, fear 15, surprise 10, anger 9, unk 3
  - **Lưu ý cho paper:** 184/240 câu gold vòng 1 có ít nhất một nhãn do Claude chốt (vòng 2: 123/240). Cách chốt theo ô: toxicity dong_y 211, phan_xu 18, ra_soat_claude 11; topic 99 / 47 / 94; stance 79 / 28 / 133; emotion 123 / 75 / 42. support chỉ còn 6 câu ở vòng 1, nên κ của nhãn này trên gold sẽ dao động nhiều

## Giai đoạn 4: Gán nhãn toàn bộ

Chỉ gửi bản đã che cho LLM và người gán.

### Gán bằng LLM (scripts/llm/)

- `scripts/llm/prompt_ban5.md`: system prompt viết từ bản 5 (định nghĩa, quy tắc quyết định, các trường hợp đã chốt, ví dụ trong quy chuẩn; không có câu nào của tập test). Phiên bản ghi ở dòng đầu (`ban5-p1`); sửa prompt thì tăng phiên bản. Mã băm prompt ghi vào mọi kết quả
- `scripts/llm/gan_nhan_llm.py`: gửi từng câu (bài đăng, bình luận cha, bình luận; bài đăng và bình luận cha cắt ở 1.500 ký tự, có ghi dấu) cho Claude hoặc OpenAI, nhận JSON theo lược đồ (structured outputs, nhãn là enum), kiểm tra nhãn và ràng buộc, vi phạm thì hỏi lại một lần có kèm lời nhắc. Ghi từng câu ngay khi có kết quả vào `data/llm/ket_qua/*.jsonl`, chạy lại thì chỉ gán câu còn thiếu hoặc lỗi; file `.tong_ket.json` ghi mô hình, effort, phiên bản prompt, token, chi phí. Không gửi câu còn khớp mẫu thông tin cá nhân (kiểm tra từng cột bằng luật của `clean_dataset.py`; toàn bộ masked.csv hiện 0 câu bị chặn). Từ chối chạy nếu đầu vào có câu split test, trừ khi thêm `--co-tap-test`. Chế độ batch của Claude (rẻ 50%) cho lần gán lớn
- `scripts/llm/danh_gia_llm.py`: Cohen κ, macro-F1, F1 từng nhãn, ma trận nhầm lẫn của từng LLM so với gold; κ tính riêng trên ô gold `dong_y` (không qua Claude chốt); κ cảm xúc đa nhãn từng cảm xúc; κ giữa các LLM và Fleiss κ khi có từ 3 LLM. Sheet `cau_lech` chỉ có câu vòng 2
- Đã kiểm tra không gọi API (2026-11-27): chạy thử (`--thu`) trên 480 câu gold và toàn bộ dữ liệu, đường chạy giả lập (`--nha-cung-cap gia_lap`, ghi file, chạy tiếp), script chấm trên kết quả giả. **Chưa gọi LLM thật** vì chưa có khóa API
- Khác với kế hoạch: Claude thế hệ 5 không nhận `temperature` (trả lỗi 400) và luôn suy nghĩ; tái lập bằng cách ghi mô hình, `effort`, phiên bản và mã băm prompt. Với Claude Opus 5.5, Opus 5, Sonnet 5.5, script bật `fallbacks: "default"` ở chế độ trực tiếp: nếu bộ lọc an toàn từ chối, API chạy lại câu đó trên mô hình khác và kết quả ghi `model_tra_loi` thực tế (tắt bằng `--khong-fallback`). Chế độ batch không có fallbacks; câu bị từ chối chạy lại ở chế độ trực tiếp. Phần OpenAI viết theo Chat Completions với `response_format` json_schema strict; cần kiểm tra lại với tài liệu OpenAI và tên mô hình lúc chạy, giá truyền bằng `--gia`
- Ước chi phí (ước lượng thô, ±50%, 2,5 ký tự/token, 400 token ra mỗi câu gồm cả suy nghĩ; giá Anthropic lưu 2026-10-06): 480 câu gold ≈ 4,6 USD với claude-opus-5-5, 2,6 USD với claude-sonnet-5-5, 0,13 USD với claude-haiku-5-5. Toàn bộ 136.609 câu, gọi trực tiếp / batch: opus-5-5 ≈ 1.312 / 656 USD; sonnet-5-5 ≈ 732 / 366 USD; haiku-5-5 ≈ 37 / 18 USD. Phần lớn chi phí là token ra (chủ yếu là suy nghĩ), nên số thật phải đo ở lần chạy gold; effort `low` có thể rẻ hơn nhiều

Lệnh (chạy từ gốc repo, sau `pip install anthropic openai`):
```
python scripts/llm/gan_nhan_llm.py --gold 2 --thu                                   # kiểm tra, không gọi API
python scripts/llm/gan_nhan_llm.py --gold 2 --model claude-opus-5-5 --effort medium   # chỉnh prompt trên vòng 2
python scripts/llm/gan_nhan_llm.py --gold 2 --nha-cung-cap openai --model <mô hình> --gia <in,out,cache>
python scripts/llm/danh_gia_llm.py --gold 2 --kq data/llm/ket_qua/*_gold2.jsonl
python scripts/llm/gan_nhan_llm.py --gold 1 ...                                      # kiểm tra một lần trên vòng 1 khi đã khóa
python scripts/llm/dong_goi_kaggle.py                                               # gói cho Kaggle (mô hình mở qua vLLM)
python scripts/llm/gan_nhan_llm.py --gold 1 2 --nha-cung-cap vllm --model qwen2.5-7b-instruct --nhiet-do 0 --luong 16 --prompt scripts/llm/prompt_ban5_en.md
```

- [x] Viết prompt từ bản 5 và script gán, chấm (2026-11-27), đã chạy thử không gọi API
- [x] So sánh các cách gọi LLM miễn phí (2026-11-27): `docs/Cach_gan_nhan_LLM_mien_phi_NLP_N12.docx`. Mỗi câu tốn khoảng 6.000 token (prompt hệ thống khoảng 5.500). Đủ cho gold: Claude qua gói Pro/Max (`claude -p`, tắt "Help improve Claude"), Mistral Experiment (phải tắt huấn luyện), Groq (khoảng 30 câu/ngày theo giới hạn 200.000 token/ngày), GitHub Models (50–150 request/ngày), Qwen3 trên Kaggle/Colab. Loại: Gemini API miễn phí (dữ liệu dùng cải thiện sản phẩm), Cerebras (không còn gói miễn phí). Không gói miễn phí nào đủ cho toàn bộ dữ liệu với nhiều mô hình; phương án trả phí rẻ nhất là Claude Haiku 5.5 qua Batch API (≈ 18 USD). Khuyến nghị: Claude qua gói + Mistral + Qwen3 trên Kaggle. **Chờ nhóm chọn**; script hiện mới gọi được Claude API và OpenAI
- [x] Chuẩn bị gán thử bằng mô hình mở trên Kaggle (2026-11-27, Triệu chọn Qwen2.5-7B-Instruct, Kaggle GPU T4 x2, chạy cả prompt tiếng Việt và tiếng Anh). `gan_nhan_llm.py` thêm `--nha-cung-cap vllm` (máy chủ vLLM tương thích OpenAI, không cần khóa, `--max-tokens` mặc định 512), `--prompt` (chọn file prompt), `--base-url` và `--bien-khoa` (dùng sau cho Groq, Mistral...). Thêm `scripts/llm/prompt_ban5_en.md` (`ban5-en-p1`, dịch sát `ban5-p1`, ví dụ giữ tiếng Việt), `scripts/llm/dong_goi_kaggle.py` (gói `data/llm/goi_kaggle/goi_kaggle.zip`, 159 KB: code, 480 dòng masked của gold, 2 file gold; tự dừng nếu còn thông tin cá nhân hay câu test) và `scripts/llm/kaggle_qwen_gold.ipynb` (cài vLLM, chạy Qwen fp16 trên 2 GPU hoặc AWQ trên 1 GPU, chạy thử 5 câu, gán 480 câu với cả hai prompt, chấm, so token, đóng gói kết quả, xóa dữ liệu). Đã kiểm tra trên máy: chạy thử cả hai prompt, giả lập ra hai file khác tên, script chấm đọc hai file, gói giải nén chạy độc lập, nhánh vllm khi chưa có máy chủ ghi `tạm lỗi` rồi dừng. Phần vLLM chưa chạy thật (máy không có GPU đủ). **Chờ Triệu chạy trên Kaggle**, tải `ket_qua_qwen.zip` về giải nén vào `data/llm/`
  - **Kết quả lần chạy đầu (2026-11-27, Triệu chạy trên Kaggle; vLLM 0.34.0, fp16, 2 × T4, nhiệt độ 0)**, file trong `data/llm/` (`ket_qua/vllm_qwen2.5-7b-instruct_*`, `danh_gia_qwen_gold12.xlsx`, `vllm.log`). Chạy trọn vẹn: 0 lỗi, 0 vi phạm, khoảng 300 giây cho 480 câu mỗi prompt (≈ 1,6 câu/giây; ước 24 giờ GPU cho toàn bộ 136.609 câu mỗi lần chạy). Token vào trung bình mỗi câu: tiếng Việt 4.600, tiếng Anh 4.200 (bộ tách từ của Qwen xử lý tiếng Việt tốt, bản Anh chỉ ít hơn 9%; thời gian gần như bằng nhau). κ so với gold (480 câu): tiếng Việt toxicity 0,376 / topic 0,583 / stance 0,306 / emotion_1 0,388; tiếng Anh 0,475 / 0,556 / 0,313 / 0,409. **Chưa hướng nào đạt mục tiêu.** κ giữa hai prompt 0,62–0,80 (mô hình nhạy với cách viết). Lỗi lặp lại ở vòng 2: emotion gán thừa joy (38 câu neutral thành joy) và sadness (18), không bao giờ gán fear; stance gán thừa support (21–26 câu none: cảm ơn người đối thoại, "xin vía", quảng cáo), bản Việt gán thừa suggest (27); toxicity bỏ sót khoảng nửa số câu attack (trêu kèm emoji cười) và gần như không nhận ra profane (recall 16–26%); bản Anh đẩy academics, administration sang student_life (39 câu). Qwen sai cả một số câu chính là ví dụ trong prompt. Bản Anh viết `ly_do` bằng tiếng Trung ở 172/480 câu. **Rò rỉ:** 24 câu gold (20 vòng 2, 4 vòng 1) trùng nguyên văn ví dụ trong prompt (ví dụ của quy chuẩn bản 5 lấy từ buổi chốt vòng 2); bỏ các câu này thì κ của Qwen gần như không đổi, nhưng khi chấm mô hình mạnh hơn phải báo κ trên phần không trùng
  - Cách chạy: (1) `python scripts/llm/dong_goi_kaggle.py`; (2) Kaggle › New Dataset (Private) tải `goi_kaggle.zip`; Import Notebook `scripts/llm/kaggle_qwen_gold.ipynb`; Settings: GPU T4 x2, Internet On, Add Input dataset; Run All; (3) tải `/kaggle/working/ket_qua_qwen.zip`
- [x] Chuẩn bị lần chạy 2 trên Kaggle (2026-11-27, theo yêu cầu của Triệu): Qwen3-14B-AWQ, tắt chế độ suy nghĩ, chỉ prompt tiếng Anh, chỉ gold vòng 2. Bộ prompt tách hướng `scripts/llm/prompt_ban5_en_tach/` (`ban5-en-tach-p1`: `chung.md` + `toxicity.md`, `topic.md`, `stance.md`, `emotion.md`; quy tắc giữ nguyên như `ban5-en-p1`, chưa chỉnh theo kết quả; `ly_do` tiếng Anh viết trước nhãn). `gan_nhan_llm.py`: `--prompt <thư mục>` bật chế độ tách hướng (mỗi câu gọi 4 lần với lược đồ riêng, ghép kết quả, hỏi lại stance một lần nếu vi phạm ràng buộc topic = unk), `--khong-suy-nghi` (gửi `chat_template_kwargs.enable_thinking=false`). Notebook `scripts/llm/kaggle_qwen3_tach_huong.ipynb` chạy hai cách: A (một prompt `ban5-en-p1`) và B (tách hướng), để tách tác động của mô hình và của việc tách prompt. Đã kiểm tra trên máy bằng giả lập (4 lần gọi + hỏi lại stance, chấm được) và in thử request. **Chờ Triệu chạy**: đóng gói lại (`dong_goi_kaggle.py`, gói 170 KB có thêm thư mục prompt), tải bản mới lên dataset Kaggle, tải `ket_qua_qwen3.zip` về giải nén vào gốc repo
  - **Kết quả lần chạy 2 (2026-11-27, Triệu chạy trên Kaggle; vLLM 0.34.0, Qwen3-14B-AWQ, 2 × T4, tắt suy nghĩ, nhiệt độ 0, gold vòng 2)**, file trong `data/llm/` (`ket_qua/vllm_qwen3-14b_*_gold2.*`, `danh_gia_qwen3_gold2.xlsx`, `vllm_qwen3.log`). κ toxicity / topic / stance / emotion_1: A (một prompt `ban5-en-p1`) 0,577 / 0,560 / 0,519 / 0,383; B (tách hướng `ban5-en-tach-p1`) 0,499 / 0,546 / 0,539 / 0,594. So với Qwen2.5-7B tiếng Anh trên vòng 2: 0,471 / 0,529 / 0,353 / 0,416. Bỏ 20 câu trùng ví dụ trong prompt, B còn 0,459 / 0,546 / 0,508 / 0,583. **B đạt mục tiêu ở stance và emotion**; toxicity, topic chưa đạt 0,67 ở cả hai cách. Để so sánh, κ giữa hai người gán (theo bản 3): Hảo–Triệu vòng 1 0,647 / 0,541 / 0,357 / 0,364; Hảo–Long vòng 2 0,669 / 0,437 / 0,215 / 0,157. Lỗi của B: toxicity gán attack cho 25 câu clean (lý do viện dẫn từ không có trong câu, đoán nghĩa từ lóng, coi mọi 🤡 là chế giễu); topic gán unk cho 44 câu student_life/academics (không lấy chủ đề theo bình luận cha hay bài đăng, trái quy tắc 2). A gán emotion thiếu (21 joy thành neutral) nên emotion thấp. B: 1 câu lỗi `max_tokens` ở emotion, 8 câu hỏi lại stance, 0 lý do bằng chữ Hán. Thời gian: A 327 giây, B 488 giây cho 240 câu (ước toàn bộ 136.609 câu: A khoảng 52 giờ, B khoảng 77 giờ GPU)
- [x] Chuẩn bị lần chạy khóa prompt (2026-11-27, Triệu chọn Qwen3-30B-A3B): notebook `scripts/llm/kaggle_khoa_prompt.ipynb` gán cả hai bộ gold (480 câu) bằng `Qwen/Qwen3-30B-A3B-GPTQ-Int4` (thử thêm `--enable-expert-parallel`, dự phòng Qwen3-14B-AWQ nếu 30B-A3B không chạy được trên T4; chưa kiểm chứng trên T4), tắt suy nghĩ, nhiệt độ 0, prompt `ban5-en-tach-p2`; chấm κ riêng từng vòng và khi bỏ câu gold trùng ví dụ trong prompt (`danh_gia_llm.py --bo-trung-prompt`: 20 câu vòng 2, 5 câu vòng 1); in tốc độ và ước tính giờ cho 10.000 câu. Tiêu chí khóa: vòng 2 bỏ câu trùng đạt mục tiêu; vòng 1 không thấp hơn vòng 2 quá khoảng 0,1; 0 lỗi; 10.000 câu dưới khoảng 9 giờ. Mốc lần trước (Qwen3-14B, p1, vòng 2, bỏ câu trùng): 0,459 / 0,546 / 0,508 / 0,583. **Chờ Triệu chạy**: `dong_goi_kaggle.py` (gói 172 KB), New Version dataset Kaggle, Save & Run All, tải `ket_qua_khoa_prompt.zip` giải nén vào gốc repo
- [x] **Khóa prompt (2026-11-27, Triệu đồng ý).** Cấu hình dùng để gán toàn bộ, không sửa nữa:
  - Mô hình `Qwen/Qwen3-14B-AWQ` trên Kaggle 2 × T4, vLLM 0.34.0, `--dtype half --quantization awq --tensor-parallel-size 2 --max-model-len 16384 --enable-prefix-caching --seed 0`
  - Prompt `scripts/llm/prompt_ban5_en_tach/` bản `ban5-en-tach-p3`, sha `e4cc4216433b`; mỗi câu gọi 4 lần (mỗi hướng một lần), `ly_do` trước nhãn, toxicity có `bang_chung` và kiểm tra bằng chứng trong code (`chung.kiem_tra_bang_chung`, bản đã sửa trích nhiều đoạn)
  - `--nha-cung-cap vllm --khong-suy-nghi --nhiet-do 0 --luong 16`, `max_tokens` 768, cắt bài đăng và bình luận cha ở 1.500 ký tự
  - Kết quả trên gold: xem mục "Đang ở đâu" và nhật ký 27/11; tốc độ 2,21 giây mỗi câu
- [x] ~~Gán bằng nhiều LLM, lấy biểu quyết đa số; người xác nhận câu bất đồng~~: bỏ, Triệu chọn phương án 1 (một mô hình); cột Note cho câu khó cũng đã bỏ
- [x] Chuẩn bị gán toàn bộ (2026-11-27, Triệu chọn 14 đợt, 4 người chạy):
  - `gan_nhan_llm.py`: lỗi `max_tokens` thì hỏi lại hướng đó một lần với giới hạn gấp đôi (ghi `da_sua`); `--dung-sau-phut` dừng nhận câu mới để kịp đóng gói trước giới hạn 12 giờ; đọc tiếp được file kết quả có dòng cuối dở dang
  - `chia_dot.py --ghi` đã chạy: 136.129 câu (bỏ 480 gold, 0 câu bị chặn vì thông tin cá nhân), 14 đợt theo bài đăng, mỗi bài trọn trong một đợt, mỗi đợt một split, trong đợt xếp theo bài đăng
  - Phân công (`data/llm/dot/phan_cong.csv`; ước tính 2,21 giây mỗi câu, chưa tính khoảng 20–25 phút khởi động mỗi phiên):

    | Người | Đợt | Số câu | Giờ GPU |
    |---|---|---|---|
    | Hảo | dot_01, dot_05, dot_09 (train), dot_13 (test) | 38.798 | 23,7 |
    | Sinh | dot_02, dot_06, dot_10 (train), dot_14 (test) | 38.798 | 23,7 |
    | Triệu | dot_03, dot_07 (train), dot_11 (val) | 29.267 | 17,9 |
    | Long | dot_04, dot_08 (train), dot_12 (val) | 29.266 | 17,9 |

  - Gói từng người: `python scripts/llm/dong_goi_kaggle.py --nguoi tat_ca` → `data/llm/goi_kaggle/goi_<tên>.zip` (1,5–2 MB). Notebook `scripts/llm/kaggle_gan_dot.ipynb`. Đã mô phỏng trên máy (gia_lap): gán, dừng hết giờ, chạy tiếp từ Output phiên trước, ghép
- [ ] Gửi gói và notebook cho từng người qua kênh riêng; mỗi người tạo dataset Kaggle Private, chạy từng đợt, gửi `ket_qua_<đợt>.zip` cho Triệu
- [ ] Triệu giải nén vào gốc repo, theo dõi bằng `python scripts/llm/ghep_ket_qua.py`; câu thiếu hoặc lỗi: `--dot-bu`; đủ thì `--ghi` ra `data/llm/nhan_toan_bo.csv`
- [ ] Ghi nguồn gốc nhãn theo từng dòng (LLM nào, người nào)

## Giai đoạn 5: Kiểm tra chất lượng nhãn

- [ ] Người gán tay tập Test
- [ ] Kiểm tra mù khoảng 5% các câu LLM đồng thuận
- [ ] Rà các tổ hợp nhãn hiếm (ví dụ Công kích + Ủng hộ, Ủng hộ + Buồn bã)
- [ ] Bỏ khỏi train các câu trùng với test

## Giai đoạn 6: Mô hình baseline

Mục tiêu hiện tại là tạo dataset nên giai đoạn này là tùy chọn, nhưng paper dataset thường có kết quả mô hình tham chiếu. Nên quyết định khi chọn nơi nộp.

Kết quả E1–E8 là của bộ 9.962 câu chỉ có nhãn Toxic (quy chuẩn v2.2), **không phải của dataset mới**. Notebook và kết quả E1–E8 đã bỏ khỏi repo ngày 2026-11-25; muốn dùng làm mẫu thì lấy lại từ commit `7fa0312` (`notebooks/`, `E5+E6/`, `results_chuan/`).

- [ ] Chạy lại BoW, TF-IDF, fastText, PhoBERT, XLM-R cho từng hướng trên tập chia theo bài đăng
- [ ] Thêm mô hình có ngữ cảnh bài đăng và bình luận cha (E9, E10)
- [ ] Báo cáo Macro-F1 và F1 từng nhãn, ma trận nhầm lẫn
- [ ] Đối chiếu kết quả với UIT-VSFC, UIT-VSMEC, ViHSD

## Giai đoạn 7: Rà soát pháp lý, đạo đức

Phần nghiên cứu về mục này chưa được kiểm chứng đầy đủ, không phải tư vấn pháp lý. Làm sạch không giải quyết được các vấn đề này.

- [ ] Xác định từng group là công khai hay kín (file hiện không có cột group, phải tra từ danh sách lúc cào). Repo không còn scraper; file `group_links.txt` cũ trong commit `7fa0312` chỉ có 2 link, không đủ 16 group, nên cần hỏi người đã cào
- [ ] Hỏi giảng viên, trường về phê duyệt đạo đức
- [ ] Xem điều khoản Meta (mục cấm thu thập tự động) so với cách đã cào (scraper có dùng cookie)
- [ ] Kiểm tra Luật 91/2025/QH15 (Điều 14, 19) với người có chuyên môn
- [ ] Loại dữ liệu group kín khỏi bản công bố nếu chưa có căn cứ
- [ ] Thử tìm lại một mẫu bình luận trên Facebook để đánh giá tái nhận dạng

## Giai đoạn 8: Viết paper và công bố

- [ ] Chọn hội nghị, kiểm tra yêu cầu (ACL/ARR có Responsible NLP checklist)
- [ ] Viết paper: giới thiệu, nghiên cứu liên quan, thu thập, làm sạch và ẩn danh, quy chuẩn gán nhãn, độ đồng thuận, thống kê dữ liệu, baseline, đạo đức, hạn chế
- [ ] Viết datasheet hoặc dataset card, có giấy phép và điều khoản sử dụng. Bản nháp: `huggingface/README.md` (2026-11-25), đã có metadata, mô tả nhãn, chia tập, quy trình; các mục còn thiếu đánh dấu `TODO`
- [ ] Công bố gated, duyệt thủ công (mặc định của Hugging Face là tự động duyệt), có kênh nhận yêu cầu gỡ dữ liệu

## Bản đồ file

| File | Vai trò | Chia sẻ? |
|---|---|---|
| `tonghopcmt_n12_backup_truoc_khi_them_toxic.xlsx` | Dữ liệu thô đầu vào | **Không** |
| `scripts/clean_dataset.py` | Script làm sạch, có regex và NER | Có |
| `scripts/danh_sach_dia_danh_truong.csv` | Tỉnh, huyện, trường đại học để không che nhầm, script bắt buộc phải có | Có |
| `data/cleaned/masked.csv` | Bản đã che để gán nhãn | Chỉ trong nhóm, chờ soát tay |
| `data/cleaned/report.json` | Thống kê lần chạy | Có |
| `data/cleaned/private/` | Bảng ID, dòng đã xóa, mẫu soát tay có văn bản gốc | **Không** |
| `data/cleaned_lan2/`, `data/cleaned_ban_cu/` | Kết quả lần 2 (kèm file soát tay lần 1) và bản chỉ có regex, giữ để đối chiếu | **Không** |
| `docs/Thiet_ke_du_lieu_da_huong_NLP_N12.docx` | Thiết kế 4 hướng nhãn | Có |
| `docs/Quy_tac_lam_sach_du_lieu_NLP_N12.docx` | Quy tắc làm sạch | Có |
| `docs/Quy_chuan_gan_nhan_4_huong_NLP_N12_ban5.docx` | Quy chuẩn gán nhãn 4 hướng, **bản 5, bản chốt** (27/11/2026), dùng để viết prompt LLM | Có |
| `data/gan_nhan/vong2/gold_vong2.csv` | Gold vòng 2 theo bản 5 (240 câu) | Chỉ trong nhóm |
| `data/gan_nhan/vong1/gold_vong1.csv` | Gold vòng 1 theo bản 5 (240 câu, rà lại ngày 27/11) | Chỉ trong nhóm |
| `data/gan_nhan/vong1/ra_soat_gold_vong1_ban5.xlsx` | Từng ô Claude đổi khi rà gold vòng 1 theo bản 5, lý do, cột duyệt | Chỉ trong nhóm |
| `scripts/che_bo_sung.py` | Che bổ sung masked.csv và các file gán nhãn bằng luật mới của `clean_dataset.py` và danh sách che tay | Có |
| `data/cleaned/private/che_bo_sung/` | Danh sách che tay, bản gốc trước khi che bổ sung (script dựng lại từ đây), file xác nhận đợt 1 và 2, log (có tên thật) | **Không** |
| `scripts/llm/` | Prompt (`prompt_ban5.md`, bản tiếng Anh `prompt_ban5_en.md`), gán bằng LLM (`gan_nhan_llm.py`: Claude, OpenAI, máy chủ vLLM), chấm so với gold (`danh_gia_llm.py`), phần chung (`chung.py`), gói Kaggle (`dong_goi_kaggle.py`) và notebook `kaggle_qwen_gold.ipynb` | Có |
| `data/llm/` | Kết quả gán bằng LLM (`ket_qua/*.jsonl`), báo cáo chấm | Chỉ trong nhóm |
| `data/gan_nhan/vong1/da_chot/` | File 4 người soát chung vòng 1 | Chỉ trong nhóm |
| `data/gan_nhan/vong1/*_da_chot.xlsx` | Nhãn và lý do chốt đợt rà gold vòng 1 (95 câu suggest, 44 câu stance) | Chỉ trong nhóm |
| `data/gan_nhan/vong2/` | Bài của Hảo và Long trong `da_gan/`, file chốt `tong_hop_vong2_Hao_Long.xlsx` (Triệu chốt 27/11; sheet `da_ap_dung` ghi nhãn cũ của các ô Claude sửa). Nguồn mẫu từng câu ở cột `nguon_mau` của gold | Chỉ trong nhóm |
| `data/gan_nhan/vong2/ra_soat_chot_vong2_Hao_Long.xlsx` | Đề xuất rà soát file chốt vòng 2 của Claude (27/11): sheet `de_xuat` (130 ô, có cột `nhom_quyet` để duyệt), `can_nhom_quyet` (9 câu hỏi), `thong_tin_ca_nhan`, `thong_ke` | Chỉ trong nhóm |
| `scripts/docx2txt.py` | Đọc docx khi không có pandoc (chuyển từ `scripts/ra_soat/` ngày 27/11; hai script rà gold vòng 1 trong thư mục đó còn trong commit `2b39403`) | Có |
| `huggingface/README.md` | Dataset card nháp để công bố trên Hugging Face | Có |
| `docs/Ke_hoach_tong_the_NLP_N12.docx` | Kế hoạch tổng thể: 8 giai đoạn đến khi công bố, việc cần làm, tiêu chí xong, cổng kiểm soát, vai trò, rủi ro (27/11/2026). Không chứa kết quả | Có |
| `docs/Ke_hoach_tiep_theo_NLP_N12.docx` | Kế hoạch bước tiếp theo sau khi dừng gán tay: kết quả chốt vòng 2, bước 1–9 (gán bằng LLM), 14 điểm còn vướng, lịch gợi ý (27/11/2026) | Có |
| `docs/Cach_gan_nhan_LLM_mien_phi_NLP_N12.docx` | Các cách gọi LLM miễn phí để gán nhãn: giới hạn, chính sách dữ liệu, khối lượng token, so sánh, lộ trình đề xuất, 4 câu cần nhóm quyết (27/11/2026) | Có |
| `README.md`, `CLAUDE.md` | Giới thiệu repo (cùng nội dung): `README.md` cho GitHub, `CLAUDE.md` cho Claude Code | Có |
| `.claude/skills/nlp-n12-dataset/SKILL.md` | Skill bàn giao cho phiên Claude khác: bối cảnh, quy tắc, lộ trình | Có |

Cần lưu ý: repo git chỉ theo dõi code và tài liệu. `.gitignore` chặn cả `data/` (trừ `data/cleaned/report.json`) và mọi file `.xlsx`, `.parquet`, `.zip` ở bất kỳ đâu. Xem `git status` trước khi commit để chắc không có file dữ liệu.

## Nhật ký

- **2026-11-08:** Chốt bản nháp 4 hướng nhãn, thêm so sánh 3 bộ dữ liệu. Nghiên cứu quy trình làm sạch, viết và chạy `clean_dataset.py`, viết tài liệu quy tắc làm sạch.
- **2026-11-09:** Tạo file tiến trình này.
- **2026-11-10:** Quyết định không lọc emoji, dấu câu, chỉ tập trung che thông tin cá nhân. Thêm NER vào `clean_dataset.py` (NlpHUST che tên, OpenMed che địa chỉ), viết `compare_ner.py`, tạo danh sách tỉnh, huyện, trường. Chuyển việc chạy sang Colab.
- **2026-11-11:** Chạy Colab lần 1, phát hiện 3 lỗi do NER (che nhầm địa chỉ, che nhầm chữ cái đơn, mất emoji). Bỏ OpenMed, thêm luật địa chỉ, sửa script. Chạy Colab lần 2, kết quả đạt yêu cầu kiểm tra tự động, chuyển sang soát tay 500 câu.
- **2026-11-12:** Soát tay lần 1 (500 câu của lần 2), sửa script theo lỗi tìm được, chạy Colab lần 3 làm bản chính thức. Nhóm chốt độc hại 3 nhãn. Chuyển sang viết quy chuẩn gán nhãn. Viết quy chuẩn bản nháp 1, tạo file gán thử vòng 1.
- **2026-11-14:** Quy chuẩn bản nháp 2 (nhãn tiếng Anh, thêm `unk`, cảm xúc đa nhãn). Tạo lại 4 file vòng 1 theo nhãn mới.
- **2026-11-19:** Hảo và Triệu gán xong vòng 1. Tổng hợp và tính κ (toxicity 0,647; topic 0,541; stance 0,357; emotion 0,364).
- **2026-11-20:** Cả 4 người soát chung và chốt gold vòng 1. Chốt định nghĩa stance hướng tới chủ đề của trường. Viết quy chuẩn bản nháp 3 (mục 7).
- **2026-11-23:** Phát hiện gold vòng 1 có 95/240 câu suggest (40%), cao bất thường do gold chốt trước quy tắc mục 7.3. Claude rà và đề xuất nhãn cho 95 câu.
- **2026-11-24:** Claude chốt 95 câu suggest và 44 câu stance theo yêu cầu của nhóm, cập nhật gold vòng 1 (stance đổi 90 câu, topic đổi 22 câu, có sao lưu bản cũ). Sửa `tao_mau_gan_thu.py` để mỗi vòng có bộ dấu hiệu riêng, tạo file vòng 2 ưu tiên các nhãn còn hiếm.
- **2026-11-25:** Sắp xếp lại repo cho mục tiêu dataset 4 hướng trên Hugging Face. Tài liệu chuyển vào `docs/`, code vào `scripts/` (`scripts_ra_soat/` thành `scripts/ra_soat/`). Thư mục bàn giao `Datasets_N12_ban_giao/` đổi tên thành `data/`, checksum 23 file không đổi. Sửa đường dẫn trong `scripts/tao_mau_gan_thu.py`; đã kiểm tra script sinh lại đúng 240 câu vòng 1 và 240 câu vòng 2 như file hiện có (ghi ra thư mục tạm, không ghi đè `data/`). Xóa phần của giai đoạn Toxic nhị phân và công cụ phụ: `E5+E6/`, `notebooks/`, `results_chuan/`, `facebook_post_comment_scraper/`, `Bao_cao_tien_do_NLP_N12.docx`, `KẾ HOẠCH THỰC HIỆN ĐỀ TÀI NLP_N12.txt`, `Quy chuẩn gán nhãn NLP.txt`, `add_toxic_to_main.py`, `link_labels.py`, `tienxuly_data_n12.py`, `compare_ner.py` (tất cả còn trong commit `7fa0312`). `.gitignore` chặn cả `data/`. Tạo dataset card nháp `huggingface/README.md`.
- **2026-11-25:** Soạn `docs/Ke_hoach_tiep_theo_NLP_N12.docx` cho cả nhóm. Tài liệu gồm các bước 0–6 kèm người làm và tiêu chí xong, việc song song, 26 điểm còn vướng, lịch gợi ý và bảng tra quy tắc gán. Trạng thái kiểm tra cùng ngày: 4 file vòng 2 đều 0/240 câu, chưa có `da_gan/`; quy chuẩn trong `docs/` vẫn là bản nháp 3; gold vòng 1 có 100/240 câu chứa nhãn `ra_soat_claude` (stance 90, topic 22, emotion 2). Ghi nhận thêm: `tong_hop_gan_thu.py` chưa tách theo `nguon_mau`, chưa kiểm tra ràng buộc từng người, chưa có script xuất `gold_vong2.csv`; ngưỡng gộp cảm xúc hiện là 2 người, với 4 người cần chốt giữ 2/4 hay nâng lên 3/4.
- **2026-11-26:** Hảo và Long nộp file vòng 2 (`data/gan_nhan/vong2/da_gan/`), Sinh và Triệu chưa nộp. Tổng hợp 2 người ra `data/gan_nhan/vong2/tong_hop_vong2_Hao_Long.xlsx` để chốt nhãn: 227/240 câu lệch ít nhất 1 hướng. Cohen κ Hảo–Long: toxicity 0,669; topic 0,437; stance 0,215; emotion_1 0,157. Đồng ý tuyệt đối: 91,7% / 59,2% / 45,8% / 20,4%. Số κ emotion thấp vì Hảo ghi `none` (170 câu) và `nonr` (4 câu) ở emotion_1. Nhóm chọn giữ nguyên, không tự đổi thành neutral; nếu coi là neutral thì κ emotion_1 khoảng 0,365. File Hảo còn 6 ô topic trống (stt 1–6) và 2 ô ghi `s` (stt 86, 87). Lệch rõ ở stance: Long chọn none 175 câu, Hảo chỉ 83 câu.
- **2026-11-26:** Nhóm chốt bộ khuyến nghị thống nhất quy chuẩn (1A–5A). Viết quy chuẩn bản nháp 4 thành `docs/Quy_chuan_gan_nhan_4_huong_NLP_N12_ban4.docx`: thêm mục 7.6 (4 quy tắc từ đợt rà gold vòng 1) và mục 8 (5 quy tắc sau vòng 2). Sửa định nghĩa topic unk (bỏ ví dụ "Haha đúng quá"), support và quy tắc quyết định stance (bỏ "suy ra được"), câu đùa dạng góp ý, quy tắc chọn cảm xúc. Mục Quy trình thành mục 9, Nguồn tham khảo thành mục 10. File đạt kiểm tra XSD; đã xuất PDF bằng Word và xem các trang có thay đổi. Lưu ý: bài vòng 2 của Hảo và Long gán theo bản 3; Sinh và Triệu nếu chưa gán thì gán theo bản 4, và khi báo κ cần ghi rõ bản nào.
- **2026-11-27:** Triệu chốt nhãn vòng 2 trên `data/gan_nhan/vong2/tong_hop_vong2_Hao_Long.xlsx`. Kiểm tra tự động: đủ 240 câu ở cả 4 hướng; 1 ô sai định dạng (câu 63 ghi `" administration"`); 4 câu vi phạm ràng buộc topic = unk mà stance khác none/unk (câu 49, 54, 64, 110); `ghi_chu_hop` chỉ có 1 dòng; cột `stt` bị xóa nhưng thứ tự dòng vẫn khớp `comment_uid`. Phân bố chốt: toxicity clean 211, attack 22, profane 5, unk 2; topic student_life 109, academics 62, administration 31, unk 19, facilities 19; stance none 131, oppose 37, support 35, suggest 33, unk 4; emotion_1 neutral 116, joy 70, surprise 20, anger 18, sadness 10, fear 4, unk 2. So với 2 người gán: stance chốt theo Hảo 45 câu, theo Long 72 câu, khác cả hai 13 câu; emotion_1 khác cả hai 35 câu. Claude đọc cả 240 câu và đối chiếu với bản 4, ghi đề xuất ra `data/gan_nhan/vong2/ra_soat_chot_vong2_Hao_Long.xlsx`: 130 ô trên 112 câu (A 33, B 47, C 40, D 10). Lỗi chính: stance còn suy đoán như bản 3 (khen, chê người đối thoại vẫn gán support hoặc oppose; đùa dạng góp ý, quảng cáo, chiêu mộ CLB vẫn gán suggest); topic chưa theo 8.1, 8.2 (học bổng, đăng ký học phần, chất lượng đào tạo gán student_life; tuyển sinh không thống nhất); emotion chưa theo 8.4 (có `=))` mà neutral, không có dấu hiệu mà joy). Nếu nhận hết A và B, stance còn none 180, support 22, suggest 18, oppose 17, unk 3. Có 9 câu hỏi quy chuẩn cần nhóm quyết (sheet `can_nhom_quyet`). Thông tin cá nhân: mã sinh viên chưa che trong bình luận cha của câu 1; tên giảng viên viết thường ở câu 58; câu 73, 215, 218 nghi còn tên người.
- **2026-11-27:** Viết `docs/Ke_hoach_tong_the_NLP_N12.docx` (kế hoạch tổng thể 8 giai đoạn, không chứa kết quả) và cập nhật `docs/Ke_hoach_tiep_theo_NLP_N12.docx` theo trạng thái ngày 27/11 (bước 1–7, 30 điểm còn vướng, lịch đến 11/12). Cả hai đạt kiểm tra XSD, đã xuất PDF bằng Word để xem bố cục. Xóa theo yêu cầu của Triệu: `docs/Quy_chuan_gan_nhan_4_huong_NLP_N12.docx` (bản nháp 3), `scripts/ra_soat/chot_vong1.py`, `scripts/ra_soat/ra_soat_suggest.py` (cả ba còn trong commit `2b39403`), `data/gan_nhan/vong1/ra_soat_suggest_vong1.xlsx`, `data/gan_nhan/vong1/xem_lai_stance_vong1.xlsx` (đã kiểm tra bản `_da_chot` chứa đủ nội dung), và các thư mục `__pycache__/`. Khôi phục `README.md` với cùng nội dung `CLAUDE.md`; thêm `.vscode/` vào `.gitignore`. Sửa các chỗ còn trỏ tới bản 3 trong `scripts/tao_mau_gan_thu.py` (sheet hướng dẫn trỏ tới bản 4, mục 7 và 8) và ghi chú của `huggingface/README.md`. Chưa commit.
- **2026-11-27:** Triệu quyết định không gán nhãn tay thêm và ủy quyền cho Claude sửa file chốt vòng 2, chốt quy chuẩn. Claude sao lưu rồi sửa `tong_hop_vong2_Hao_Long.xlsx` (153 ô trên 123 câu, xem checklist giai đoạn 3). Lúc thêm lại cột `stt`, script ghi nhầm số vào các dòng trống 242–1000 (sheet có định dạng thừa tới dòng 1000); đã xóa các dòng đó, dữ liệu 240 câu không đổi. Viết `scripts/xuat_gold.py` và xuất `gold_vong2.csv`. Phân bố gold vòng 2: toxicity clean 212, attack 23, profane 5; topic student_life 98, academics 70, administration 45, facilities 18, unk 9; stance none 194, support 18, suggest 15, oppose 10, unk 3; emotion_1 neutral 143, joy 48, surprise 20, anger 17, sadness 9, fear 2, unk 1. Gold vòng 2 ghi `emotion_2` cách nhau bằng `;`, còn gold vòng 1 đang dùng dấu phẩy, cần chuẩn hóa khi rà vòng 1. Viết quy chuẩn bản 5 (bản chốt) gộp mọi quy tắc và 9 quyết định: khen, cảm ơn người đối thoại là none; chiêu mộ CLB là none; tuyển sinh là administration; mọi câu về ký túc xá là facilities; "+1" đáp lại lời khuyên là none; chê người không phải người đối thoại là none; lời đánh giá không phải dấu hiệu cảm xúc; ngưỡng gộp cảm xúc 3/4 cho emotion_1; ví dụ ranh giới attack/clean. Cập nhật kế hoạch tổng thể (tập test, phân xử, cổng kiểm soát khi không gán tay; thêm rủi ro nhãn thiên về Claude) và viết lại kế hoạch tiếp theo theo hướng gán bằng LLM. Cả ba docx đạt kiểm tra XSD, đã xuất PDF bằng Word để xem. Sửa lỗi đánh số danh sách trong các docx (mỗi danh sách một định nghĩa đánh số riêng). Chưa commit.
- **2026-11-27:** Làm 3 bước tiếp theo theo yêu cầu của Triệu. (1) Claude rà gold vòng 1 theo bản 5: đọc 240 câu, đổi 171 ô trên 131 câu, có sao lưu và file lý do (xem checklist giai đoạn 3). (2) Che bổ sung thông tin cá nhân: thêm 7 luật vào `scripts/clean_dataset.py`, viết `scripts/che_bo_sung.py`, che 259 đoạn văn bản trong masked.csv và 108 ô trong file gán nhãn, sao lưu và chờ một người xác nhận (xem checklist giai đoạn 2). (3) Viết prompt `scripts/llm/prompt_ban5.md` (`ban5-p1`), `scripts/llm/gan_nhan_llm.py` (Claude và OpenAI, structured outputs, cache system prompt, batch, ghi token và chi phí, chặn câu còn thông tin cá nhân và câu thuộc tập test) và `scripts/llm/danh_gia_llm.py`; chạy thử không gọi API. Máy chưa có khóa API nào nên chưa chạy LLM trên gold và chưa khóa prompt; Triệu chọn viết sẵn, chạy khi nhóm có khóa. Chưa commit.
- **2026-11-27:** Triệu xác nhận file che bổ sung đợt 1 (247 đúng, 9 còn sót, 2 che nhầm, 1 trống). Claude che bổ sung đợt 2: thêm luật tên viết hoa chữ đầu sau thầy/cô, thêm tên vào luật, 27 chuỗi che tay, sửa luật gộp tên để không che cú pháp tin nhắn "HUY <mã>" (trả lại nguyên văn ở masked.csv và 5 ô file gán nhãn, gồm gold vòng 2). Đổi `scripts/che_bo_sung.py` sang dựng lại từ bản gốc, ghi file theo đợt, sao lưu trước khi ghi. 219 đoạn đổi, chờ xác nhận `xac_nhan_che_bo_sung_dot2.xlsx`. Tra giới hạn và chính sách dữ liệu của các gói LLM miễn phí (Groq, Mistral, GitHub Models, OpenRouter, Gemini, Cerebras, Claude qua gói cá nhân, mô hình mở trên Kaggle/Colab) và viết `docs/Cach_gan_nhan_LLM_mien_phi_NLP_N12.docx` (6 trang, đạt kiểm tra XSD, đã xuất PDF xem bố cục). Chưa sửa script gán để gọi các nhà cung cấp mới, chờ nhóm chọn. Chưa commit.
- **2026-11-27:** Triệu xác nhận đúng toàn bộ đợt che 2 (219 dòng); chuyển `data/cleaned/che_bo_sung/` vào `data/cleaned/private/che_bo_sung/`. Dọn file theo lựa chọn của Triệu: xóa bản sao lưu tạm đợt che 2 (`masked_truoc_dot2.csv`, `sao_luu_file_gan_nhan_dot2/`), `data/llm/` (chỉ có request mẫu của lần chạy thử), bản sao lưu gold cũ (`gold_vong1_truoc_ban5.csv`, `gold_vong1_truoc_ra_soat.csv`, `vong2/da_chot/tong_hop_vong2_Hao_Long_truoc_ra_soat.xlsx`; nhãn cũ của các ô đổi đã ghi trong `ra_soat_gold_vong1_ban5.xlsx` và sheet `da_ap_dung`), nguồn mẫu và tổng hợp κ cũ (`tong_hop_vong1.csv`, `tong_hop_vong2.csv`, `tong_hop_vong1_Hao_Trieu.xlsx`; gold có cột `nguon_mau`, κ tính lại được từ `da_gan/`), các thư mục `__pycache__/`, và 3 script gán tay `scripts/tao_mau_gan_thu.py`, `scripts/tong_hop_gan_thu.py`, `scripts/xuat_gold.py` (lấy lại: `git checkout 46c38cd -- scripts/<tên file>`). Giữ quy chuẩn bản 4 và các file đề xuất rà soát. Kiểm tra lại: `che_bo_sung.py` chạy từ thư mục mới không đổi gì; chạy thử gán LLM trên 480 câu gold không câu nào bị chặn. Chưa commit.
- **2026-11-27:** Triệu chọn gán thử 480 câu gold bằng Qwen2.5-7B-Instruct trên Kaggle (T4 x2), chạy cả prompt tiếng Việt và tiếng Anh. Thêm nhánh vLLM và `--prompt` vào `gan_nhan_llm.py`, prompt tiếng Anh `ban5-en-p1`, script đóng gói `dong_goi_kaggle.py` và notebook `kaggle_qwen_gold.ipynb` (xem checklist giai đoạn 4). Cài gói `openai` trên máy để thử nhánh vllm. Chưa chạy trên Kaggle. Chưa commit.
- **2026-11-27:** Triệu chạy `kaggle_qwen_gold.ipynb` trên Kaggle (Qwen2.5-7B-Instruct, 2 prompt × 480 câu, khoảng 5 phút mỗi prompt, 0 lỗi). κ chưa đạt ở cả 4 hướng (cao nhất topic 0,58; stance khoảng 0,31); chi tiết ở checklist giai đoạn 4. Kết quả Triệu giải nén vào `scripts/llm/ket_qua_qwen/` (thư mục được git theo dõi, file .jsonl/.json/.log không bị chặn); Claude chuyển sang `data/llm/` và xóa thư mục trong `scripts/`. Phát hiện 24 câu gold trùng ví dụ trong prompt. Chưa commit.
- **2026-11-27:** Viết bộ prompt tiếng Anh tách theo hướng (`prompt_ban5_en_tach/`, `ban5-en-tach-p1`), thêm chế độ tách hướng và cờ `--khong-suy-nghi` vào `gan_nhan_llm.py`, notebook `kaggle_qwen3_tach_huong.ipynb` (Qwen3-14B-AWQ, gold vòng 2, so một prompt với tách hướng). Đóng gói lại `goi_kaggle.zip`. Chưa chạy trên Kaggle. Chưa commit.
- **2026-11-27:** Dọn file theo yêu cầu của Triệu: xóa `data/llm/goi_kaggle/` (đã tải lên Kaggle; tạo lại bằng `dong_goi_kaggle.py`), `data/llm/vllm.log` và 2 file `*.request_mau.json` của lần chạy Qwen2.5 (phiên bản vLLM 0.34.0 đã ghi ở checklist giai đoạn 4), notebook `scripts/llm/kaggle_qwen_gold.ipynb` (chưa commit nên không lấy lại được; `kaggle_qwen3_tach_huong.ipynb` thay thế, đổi `MODEL` để chạy mô hình khác); chuyển `scripts/ra_soat/docx2txt.py` thành `scripts/docx2txt.py` và bỏ thư mục `scripts/ra_soat/`. Triệu đã tự xóa `docs/Quy_chuan_gan_nhan_4_huong_NLP_N12_ban4.docx` (lấy lại: `git checkout 46c38cd -- docs/Quy_chuan_gan_nhan_4_huong_NLP_N12_ban4.docx`). Chưa commit.
- **2026-11-27:** Triệu chạy `kaggle_qwen3_tach_huong.ipynb` (Qwen3-14B-AWQ, gold vòng 2): tách hướng đạt mục tiêu ở stance (0,539) và emotion (0,594); toxicity (0,499) và topic (0,546) chưa đạt, lỗi chính là đoán xúc phạm và không lấy chủ đề theo ngữ cảnh. Claude giải nén `ket_qua_qwen3.zip` vào `data/llm/`, xóa file zip ở gốc repo và các `request_mau.json`. Chưa commit.
- **2026-11-27:** Triệu chọn phương án 1 (một mô hình Qwen3 trên Kaggle, gán theo đợt 10.000 dòng; ý tưởng cột note cho câu khó sau đó đã bỏ). Sửa bộ prompt tách hướng lên `ban5-en-tach-p2` (sha ce59e4e87701), chỉ sửa theo lỗi trên gold vòng 2: toxicity phải trích được từ xúc phạm hoặc từ tục có trong câu, không đoán nghĩa từ lóng, 🤡 chỉ tính khi nhắm vào người, chê hành động không có từ xúc phạm là clean; topic xác định theo ngữ cảnh trước (bài đăng, bình luận cha), unk chỉ khi câu không có chữ nào ngoài tag, emoji, tiếng cười. Ví dụ mới tự đặt, đã kiểm tra không trùng gold. stance, emotion giữ nguyên. Giới hạn token mặc định của vllm tăng từ 512 lên 768. Chưa chạy p2 trên Kaggle. Chưa commit.
- **2026-11-27:** Bỏ ý tưởng cột Note cho câu khó (theo Triệu). Triệu chọn Qwen3-30B-A3B. Viết `kaggle_khoa_prompt.ipynb` (thay `kaggle_qwen3_tach_huong.ipynb`, đã xóa) để khóa prompt `ban5-en-tach-p2` trên cả hai bộ gold; `danh_gia_llm.py` thêm κ từng vòng và `--bo-trung-prompt`. Đã đóng gói lại `goi_kaggle.zip`, chạy giả lập trên máy được. Chưa commit.
- **2026-11-27:** Triệu chạy `kaggle_khoa_prompt.ipynb`: `Qwen/Qwen3-30B-A3B-GPTQ-Int4` khởi động được trên 2 × T4 ngay cấu hình 1 (vLLM 0.34.0, 362 giây), prompt `ban5-en-tach-p2`, gold vòng 1 và 2 (480 câu), 1 câu lỗi (stance max_tokens), 663 giây (1,38 giây mỗi câu, nhanh hơn Qwen3-14B khoảng 1/3; 10.000 câu ≈ 3,8 giờ). File trong `data/llm/` (`ket_qua/vllm_qwen3-30b-a3b_*`, `danh_gia_khoa_prompt_qwen3-30b-a3b.xlsx`, `vllm_khoa_prompt_qwen3-30b-a3b.log`). κ vòng 2 bỏ câu trùng prompt / vòng 1: toxicity 0,415 / 0,594; topic 0,733 / 0,716 (đạt, topic = unk từ 60 câu xuống 13 nhờ p2); stance 0,348 / 0,495; emotion_1 0,478 / 0,450. Chưa khóa prompt. So với Qwen3-14B p1 trên cùng 239 câu vòng 2, 30B-A3B kém hơn ở stance (0,381 so với 0,539: gán oppose cho câu chê người, suggest cho câu rủ rê, quảng cáo), emotion (0,485 so với 0,594: 40 câu neutral thành joy) và toxicity (0,431 so với 0,499: tự bịa bằng chứng, 18/41 câu sai có đoạn trích không có trong câu); stance và emotion không đổi prompt nên phần giảm là do mô hình. Đề xuất: chạy Qwen3-14B với p2 trên cả hai bộ gold để tách tác động mô hình và prompt, và thêm kiểm tra bằng chứng toxicity trong code.
- **2026-11-27:** Theo yêu cầu của Triệu, sửa `kaggle_khoa_prompt.ipynb` để chọn mô hình bằng biến `MO_HINH` (mặc định `"14b"`: Qwen3-14B-AWQ; `"30b-a3b"`), bỏ tự chuyển sang mô hình dự phòng, tên báo cáo, log và zip có tên mô hình (`danh_gia_khoa_prompt_<mô hình>.xlsx`, `ket_qua_khoa_prompt_<mô hình>.zip`); đổi tên file của lần 30B-A3B cho khớp. Lần chạy tiếp: Qwen3-14B với p2 trên cả hai bộ gold, so với 14B p1 (tác động prompt) và 30B-A3B p2 (tác động mô hình). Dataset Kaggle không cần tải lại. **Chờ Triệu chạy.**
- **2026-11-27:** Triệu chạy `kaggle_khoa_prompt.ipynb` với `MO_HINH = "14b"` (Qwen3-14B-AWQ, p2, 480 câu): 1 câu lỗi, 993 giây (2,07 giây mỗi câu; 10.000 câu ≈ 5,75 giờ; toàn bộ ≈ 79 giờ GPU). File trong `data/llm/` (`ket_qua/vllm_qwen3-14b_*_p2_gold12.*`, `danh_gia_khoa_prompt_qwen3-14b.xlsx`, `vllm_khoa_prompt_qwen3-14b.log`). κ bỏ câu trùng prompt, trên cùng 219 câu vòng 2 (14B p1 / 14B p2 / 30B-A3B p2): toxicity 0,459 / 0,480 / 0,414; topic 0,546 / 0,714 / 0,733; stance 0,508 / 0,488 / 0,341; emotion_1 0,583 / 0,574 / 0,475. Vòng 1 (234 câu, 14B p2 / 30B p2): 0,646 / 0,594; 0,725 / 0,716; 0,513 / 0,495; 0,527 / 0,450. Kết luận: p2 làm topic tăng khoảng 0,17 (unk từ 60 xuống 9 câu), toxicity tăng ít (attack thừa từ 44 xuống 31 câu nhưng profane thừa từ 4 lên 11: mô hình đoán từ viết tắt lạ là từ tục); stance, emotion dao động ±0,02 (prompt không đổi). Mô hình: 14B hơn 30B-A3B ở 3/4 hướng cả hai vòng, nên chọn Qwen3-14B. Vòng 1 không thấp hơn vòng 2, chưa thấy dấu hiệu prompt khớp riêng vòng 2. Chưa khóa: toxicity vòng 2 0,480, stance 0,488 (sát 0,5). Để so sánh, κ giữa hai người: vòng 1 Hảo–Triệu 0,647 / 0,541 / 0,357 / 0,364; vòng 2 Hảo–Long 0,669 / 0,437 / 0,215 / 0,157.
- **2026-11-27:** Theo yêu cầu của Triệu, viết `ban5-en-tach-p3` (sha e4cc4216433b), chỉ sửa toxicity theo lỗi của Qwen3-14B p2 trên gold vòng 2: lược đồ toxicity thêm trường `bang_chung` (chép nguyên văn từ <binh_luan>); `gan_nhan_llm.py` kiểm tra bằng chứng (attack mà `bang_chung` không có trong câu, profane mà câu không có từ nào trong danh sách `chung.TU_TUC`) thì hỏi lại một lần, vẫn thiếu thì hạ nhãn (attack thành profane nếu câu có từ tục, còn lại thành clean), ghi ở `da_sua`, lưu `bang_chung` vào kết quả; thêm ví dụ tự đặt về từ không phải lời xúc phạm (cách xưng hô, cảm thán, từ lóng chỉ hành động, "bịp" về tin đồn, viết tắt lạ), đã kiểm tra không trùng gold. Danh sách từ tục kiểm trên gold vòng 2: giữ cả 5 câu gold profane, chặn cả 7 câu profane thừa của 14B p2. stance chưa sửa (vòng 1 đã đạt 0,513). Notebook `kaggle_khoa_prompt.ipynb` chuyển sang p3, mặc định 14b, in số câu hỏi lại và hạ nhãn. Đã đóng gói lại `goi_kaggle.zip` (175 KB), chạy giả lập trên máy được. **Chờ Triệu tải gói mới (New Version) và chạy.** Chưa commit.
- **2026-11-27:** Triệu chạy `kaggle_khoa_prompt.ipynb` với Qwen3-14B và p3 (sha e4cc4216433b): 1 câu lỗi (emotion max_tokens), 1062 giây (2,21 giây mỗi câu; 10.000 câu ≈ 6,1 giờ; toàn bộ ≈ 84 giờ GPU). File trong `data/llm/` (`ket_qua/vllm_qwen3-14b_*_p3_gold12.*`, `danh_gia_khoa_prompt_qwen3-14b_p3.xlsx`, `vllm_khoa_prompt_qwen3-14b_p3.log`); đổi tên báo cáo và log các lần trước thêm hậu tố `_p2` (notebook từ nay ghi phiên bản prompt vào tên file). κ bỏ câu trùng prompt, p2 → p3: vòng 2 toxicity 0,480 → 0,582, topic 0,714 → 0,720, stance 0,488 → 0,488, emotion_1 0,574 → 0,574; vòng 1 toxicity 0,652 → 0,660, topic 0,721 → 0,710, stance 0,501 → 0,494, emotion_1 0,520 → 0,530. Vòng 2 profane F1 0,50 → 0,91 (profane thừa từ 11 xuống 6 câu); attack không đổi (F1 0,59, còn 15 câu clean thành attack: "bịp", "lùa", "gặt thợ", 🤡). Kiểm tra bằng chứng hỏi lại 18 câu (16 profane, 2 attack), hạ nhãn 1 câu nhưng hạ sai: mô hình trích hai đoạn nối bằng dấu phẩy ("loz, th ngu"). Đã sửa `chung.bang_chung_co_that` (nhiều đoạn thì mọi đoạn phải có trong câu; prompt không đổi, sha giữ nguyên); áp lại trên kết quả: toxicity vòng 2 0,600, vòng 1 0,660. Đã đóng gói lại `goi_kaggle.zip`. Đề xuất khóa p3 + Qwen3-14B, chờ Triệu quyết định.
- **2026-11-27:** Triệu đồng ý khóa prompt: Qwen3-14B-AWQ + `ban5-en-tach-p3` (sha e4cc4216433b), cấu hình ghi ở checklist giai đoạn 4. Viết lại mục "Đang ở đâu" và "Việc tiếp theo ngay". Bỏ mục gán bằng nhiều LLM. Bước tiếp theo: chốt cách chia đợt, Claude viết script chia đợt và notebook gán từng đợt. Chưa commit.
- **2026-11-27:** Theo yêu cầu của Triệu (14 đợt, 4 người chạy): thêm `chia_dot.py` (đã ghi `data/llm/dot/`), `dong_goi_kaggle.py --nguoi`, notebook `kaggle_gan_dot.ipynb` (cấu hình đã khóa, kiểm tra sha, vLLM 0.34.0, tự dừng sau 10 giờ, chạy tiếp từ Output phiên trước), `ghep_ket_qua.py` (tiến độ, đợt bù, ghép có nguồn gốc nhãn); `gan_nhan_llm.py` hỏi lại khi `max_tokens`, `--dung-sau-phut`, đọc được dòng dở. Đã tạo 4 gói `goi_<tên>.zip`. Mô phỏng trên máy được; chưa chạy thật trên Kaggle. Chưa commit.

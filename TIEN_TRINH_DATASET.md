# Tiến trình: dataset 4 hướng và paper (NLP_N12)

Cập nhật lần cuối: 2026-11-27

**Mục tiêu:** từ khoảng 140 nghìn bình luận Facebook của sinh viên PTIT, tạo bộ dữ liệu gán nhãn theo 4 hướng (độc hại, chủ đề, lập trường và góp ý, cảm xúc), viết paper và công bố dataset nếu đủ điều kiện pháp lý, đạo đức.

## Đang ở đâu

**Hết giai đoạn 3, bắt đầu giai đoạn 4 (gán bằng LLM).** Ngày 2026-11-27 nhóm quyết định không gán nhãn tay thêm. Quy chuẩn đã chốt ở bản 5 (`docs/Quy_chuan_gan_nhan_4_huong_NLP_N12_ban5.docx`). Gold vòng 2 đã xuất (`data/gan_nhan/vong2/gold_vong2.csv`, Claude sửa file chốt theo bản 5 do Triệu ủy quyền). Gold vòng 1 còn theo bản 3, cần rà lại theo bản 5. Độ đồng thuận giữa người chỉ có từ 2 cặp (Hảo–Triệu vòng 1, Hảo–Long vòng 2, đều theo bản 3).

**Cấu trúc repo (từ 2026-11-25):** tài liệu trong `docs/`, code trong `scripts/`, dữ liệu trong `data/` (không commit), dataset card nháp trong `huggingface/`. Chạy lệnh từ thư mục gốc repo. Phần Nhật ký trước ngày này ghi đường dẫn cũ, khi chưa có các tiền tố `docs/`, `scripts/`, `data/`.

**Việc tiếp theo ngay** (chi tiết và lịch gợi ý: `docs/Ke_hoach_tiep_theo_NLP_N12.docx`, cập nhật 27/11 sau quyết định không gán tay; lộ trình đến khi công bố: `docs/Ke_hoach_tong_the_NLP_N12.docx`):
1. Rà gold vòng 1 theo bản 5 (Claude, sao lưu trước, ghi `ra_soat_claude`, chuẩn hóa `emotion_2` sang dấu `;`)
2. Che nốt thông tin cá nhân còn lộ (mã sinh viên ở câu 1 vòng 2, các câu trong sheet `thong_tin_ca_nhan`, 4 câu sót tên ở vòng 1), một người xác nhận
3. Viết prompt từ bản 5 và script gán bằng LLM; chạy thử trên 480 câu gold (chỉnh trên vòng 2, kiểm tra trên vòng 1), có ít nhất một LLM khác hãng; khóa prompt
4. Nhóm chọn LLM, ngân sách, phạm vi (toàn bộ hay 20–30 nghìn câu); gán toàn bộ và tập test, Claude phân xử câu bất đồng
5. Khuyến nghị một người duyệt (không gán lại) khoảng 200 câu test

Song song (chỉ người trong nhóm làm được, chặn công bố): hỏi giảng viên về đạo đức, danh sách 16 group, điều khoản Meta, Luật 91/2025/QH15. Commit các thay đổi đang chờ.

## Tổng quan

| Giai đoạn | Trạng thái |
|---|---|
| 1. Thiết kế nhãn | **Xong**: quy chuẩn bản 5 (bản chốt, 2026-11-27) |
| 2. Làm sạch và che thông tin | **Xong** (bản lần 3), còn vài mục kiểm tra phụ |
| 3. Gán thử và đo đồng thuận | **Dừng** sau 2 vòng (nhóm không gán tay thêm); gold vòng 2 xong theo bản 5, gold vòng 1 cần rà lại theo bản 5 |
| 4. Gán nhãn toàn bộ | **Bắt đầu**: gán bằng LLM, Claude phân xử; chưa có prompt và script |
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
- [ ] Rà gold vòng 1 theo bản 5

## Giai đoạn 4: Gán nhãn toàn bộ

Chỉ gửi bản đã che cho LLM và người gán.

- [ ] Chọn các LLM khác nhau và thử trên gold set (khi dùng API nên dùng gói trả phí, không để dữ liệu bị dùng huấn luyện)
- [ ] Gán bằng nhiều LLM, lấy biểu quyết đa số
- [ ] Người xác nhận các câu bất đồng hoặc bị đánh dấu
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
| `docs/Quy_chuan_gan_nhan_4_huong_NLP_N12_ban4.docx` | Quy chuẩn bản nháp 4 (26/11/2026), bản 5 đã thay thế. Bản nháp 3 (vòng 1 và bài của Hảo, Long ở vòng 2 gán theo bản này) đã xóa ngày 27/11; lấy lại: `git checkout 2b39403 -- docs/Quy_chuan_gan_nhan_4_huong_NLP_N12.docx` | Có |
| `scripts/tao_mau_gan_thu.py` | Tạo file gán thử cho từng vòng, không lấy lại câu của vòng trước | Có |
| `scripts/tong_hop_gan_thu.py` | Tổng hợp file đã gán, tính Cohen κ và Fleiss κ | Có |
| `scripts/xuat_gold.py` | Xuất `gold_vong<N>.csv` từ file chốt, kiểm tra nhãn, ràng buộc, ghi cách chốt (`dong_y`, `phan_xu`, `ra_soat_claude`) | Có |
| `data/gan_nhan/vong2/gold_vong2.csv` | Gold vòng 2 theo bản 5 (240 câu) | Chỉ trong nhóm |
| `data/gan_nhan/vong1/gold_vong1.csv` | Gold vòng 1 sau khi rà (240 câu) | Chỉ trong nhóm |
| `data/gan_nhan/vong1/gold_vong1_truoc_ra_soat.csv` | Gold vòng 1 trước khi rà, giữ để đối chiếu | Chỉ trong nhóm |
| `data/gan_nhan/vong1/da_chot/` | File 4 người soát chung vòng 1 | Chỉ trong nhóm |
| `data/gan_nhan/vong1/*_da_chot.xlsx` | Nhãn và lý do chốt đợt rà gold vòng 1 (95 câu suggest, 44 câu stance) | Chỉ trong nhóm |
| `data/gan_nhan/vong2/` | `tong_hop_vong2.csv` (nguồn mẫu từng câu), bài của Hảo và Long trong `da_gan/`, file chốt `tong_hop_vong2_Hao_Long.xlsx` (Triệu chốt 27/11), `da_chot/` để sao lưu | Chỉ trong nhóm |
| `data/gan_nhan/vong2/ra_soat_chot_vong2_Hao_Long.xlsx` | Đề xuất rà soát file chốt vòng 2 của Claude (27/11): sheet `de_xuat` (130 ô, có cột `nhom_quyet` để duyệt), `can_nhom_quyet` (9 câu hỏi), `thong_tin_ca_nhan`, `thong_ke` | Chỉ trong nhóm |
| `scripts/ra_soat/docx2txt.py` | Đọc docx khi không có pandoc. Hai script rà gold vòng 1 đã xóa ngày 27/11, còn trong commit `2b39403` | Có |
| `huggingface/README.md` | Dataset card nháp để công bố trên Hugging Face | Có |
| `docs/Ke_hoach_tong_the_NLP_N12.docx` | Kế hoạch tổng thể: 8 giai đoạn đến khi công bố, việc cần làm, tiêu chí xong, cổng kiểm soát, vai trò, rủi ro (27/11/2026). Không chứa kết quả | Có |
| `docs/Ke_hoach_tiep_theo_NLP_N12.docx` | Kế hoạch bước tiếp theo sau khi dừng gán tay: kết quả chốt vòng 2, bước 1–9 (gán bằng LLM), 14 điểm còn vướng, lịch gợi ý (27/11/2026) | Có |
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

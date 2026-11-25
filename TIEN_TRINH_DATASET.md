# Tiến trình: dataset 4 hướng và paper (NLP_N12)

Cập nhật lần cuối: 2026-11-25

**Mục tiêu:** từ khoảng 140 nghìn bình luận Facebook của sinh viên PTIT, tạo bộ dữ liệu gán nhãn theo 4 hướng (độc hại, chủ đề, lập trường và góp ý, cảm xúc), viết paper và công bố dataset nếu đủ điều kiện pháp lý, đạo đức.

## Đang ở đâu

**Giai đoạn 3, giữa vòng 1 và vòng 2.** Làm sạch đã xong (Colab lần 3, 2026-11-12). Quy chuẩn 4 hướng đang ở bản nháp 3. Vòng 1 (240 câu) đã chốt gold và rà lại theo bản 3 (2026-11-24). File gán vòng 2 đã tạo (2026-11-24), chưa ai gán.

**Cấu trúc repo (từ 2026-11-25):** tài liệu trong `docs/`, code trong `scripts/`, dữ liệu trong `data/` (không commit), dataset card nháp trong `huggingface/`. Chạy lệnh từ thư mục gốc repo. Phần Nhật ký trước ngày này ghi đường dẫn cũ, khi chưa có các tiền tố `docs/`, `scripts/`, `data/`.

**Việc tiếp theo ngay** (chi tiết từng bước, phân công gợi ý và 26 điểm còn vướng: `docs/Ke_hoach_tiep_theo_NLP_N12.docx`):
0. Đồng bộ repo mới: push cấu trúc 25/11, mọi người pull và đặt dữ liệu vào `data/`, cài `openpyxl`
1. Viết quy chuẩn bản 4 (thêm các quy tắc từ đợt rà gold vòng 1), gửi nhóm trước khi gán vòng 2
2. Cả 4 người gán vòng 2 độc lập, rồi tính κ và họp chốt (kiểm tra 25/11: cả 4 file vẫn 0/240 câu)
3. Một người đọc lướt 2 file `_da_chot` của vòng 1 (nhãn do Claude chốt), nên làm sau khi người đó đã nộp file vòng 2

Song song: làm nốt các mục còn mở ở Giai đoạn 2, và hỏi giảng viên về phê duyệt đạo đức (Giai đoạn 7).

## Tổng quan

| Giai đoạn | Trạng thái |
|---|---|
| 1. Thiết kế nhãn | Đã chốt bộ nhãn; quy chuẩn bản nháp 3, cần viết bản 4 |
| 2. Làm sạch và che thông tin | **Xong** (bản lần 3), còn vài mục kiểm tra phụ |
| 3. Gán thử và đo đồng thuận | **Đang làm**: vòng 1 xong (gold đã rà), vòng 2 đã tạo file, chờ gán |
| 4. Gán nhãn toàn bộ | Chưa làm |
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
- [x] Viết bản nháp 1 quy chuẩn gán nhãn 4 hướng dựa trên các chuẩn đã công bố (OLID, UIT-VSFC, SemEval-2016 Task 6, SemEval-2019 Task 9, GoEmotions, SemEval-2018 Task 1, UIT-VSMEC): `docs/Quy_chuan_gan_nhan_4_huong_NLP_N12.docx` (2026-11-12)
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
  - Script chốt: `scripts/ra_soat/ra_soat_suggest.py` và `scripts/ra_soat/chot_vong1.py` (chỉ để tái lập; chạy lại `ra_soat_suggest.py` sẽ ghi đè file đề xuất ban đầu). Nhãn và lý do đã ghi đầy đủ trong 2 file `_da_chot.xlsx`
  - **Lưu ý cho paper:** 114 nhãn gold vòng 1, ở 100/240 câu (stance 90, topic 22, emotion 2), do LLM (Claude) chốt, chưa có người duyệt lại. Nên có ít nhất một người đọc lướt 2 file `_da_chot`, và ghi rõ trong paper. Nếu dùng gold để chấm các LLM gán nhãn, kết quả có thể thiên về mô hình giống Claude; cân nhắc chỉ dùng gold từ vòng 2 để đánh giá LLM

Phân bố gold vòng 1 sau khi rà (240 câu):

| Hướng | Phân bố |
|---|---|
| toxicity | clean 190, attack 25, profane 24, unk 1 |
| topic | academics 81, unk 58, student_life 56, administration 39, facilities 6 |
| stance | none 137, oppose 33, suggest 32, support 23, unk 15 |
| emotion_1 | neutral 139, joy 29, sadness 23, fear 17, surprise 12, anger 11, unk 9 |

- [ ] Quy chuẩn bản 4: đưa vào docx các quy tắc mới từ đợt rà soát (hiện mới có trong sheet hướng dẫn của file vòng 2):
  - suggest khi câu chỉ cụ thể việc cần làm hoặc nơi cần đến ("ra tòa A1 điểm danh lại"); none khi chỉ trả lời được hay không, khi nào, bao nhiêu ("sau 2/9 xin vẫn được")
  - Quảng cáo, chiêu mộ CLB, tin tuyển dụng: none
  - Đùa dưới dạng góp ý mà không chê gì ("đề nghị có CLB trai làng"): none; đùa hoặc mỉa mai có chê: oppose. Sửa câu chữ mục 5 cho rõ
  - Đồng tình hay phản bác bình luận cha về chủ đề của trường: gán topic theo bình luận cha (đã áp dụng, ví dụ câu 19, 85, 173, 198)
- [x] Tạo file vòng 2 (2026-11-24): `scripts/tao_mau_gan_thu.py 2` tạo 4 file `data/gan_nhan/vong2/gan_thu_vong2_<Tên>.xlsx` và `tong_hop_vong2.csv`. 240 câu từ train, 229 bài đăng, không trùng vòng 1; 120 câu ngẫu nhiên và 4 nhóm × 30 câu ưu tiên nhãn còn hiếm sau vòng 1 (công kích, cơ sở vật chất, tức giận/ngạc nhiên, ủng hộ). Sheet hướng dẫn có nhắc các quy tắc mục 7 và quy tắc suggest mới
  - Script đổi sang cấu hình dấu hiệu theo từng vòng (`DAU_HIEU_THEO_VONG`); đã kiểm tra chạy lại vòng 1 ra đúng 240 câu cũ
  - Đọc lướt: nhóm ủng hộ và tức giận/ngạc nhiên lẫn nhiều câu không mang nhãn đó ("xứng đáng độc thân", "tức là"), nên số câu nhãn hiếm thực tế sẽ dưới 30 mỗi nhóm
- [ ] Cả 4 người gán vòng 2 **độc lập** (không bàn, không xem file người khác). Gán xong đặt file vào `data/gan_nhan/vong2/da_gan/`
- [ ] Chạy `scripts/tong_hop_gan_thu.py` cho vòng 2: Cohen κ từng cặp, Fleiss κ từng hướng (riêng cảm xúc đa nhãn dùng Krippendorff α hoặc κ từng nhãn), danh sách câu bất đồng
- [ ] Họp chốt vòng 2, ghi lý do vào `ghi_chu_hop`, xuất `gold_vong2.csv`
- [ ] Quyết định theo κ vòng 2: hướng nào ≥ 0,67 thì giữ; hướng nào < 0,5 (dự kiến stance, emotion) thì đơn giản hóa nhãn trước vòng 3
- [ ] Vòng 3 nếu cần, đến khi các hướng đạt ngưỡng. Xem nhãn nào quá hiếm (facilities, anger, surprise), gộp hoặc sửa nếu cần

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
| `docs/Quy_chuan_gan_nhan_4_huong_NLP_N12.docx` | Quy chuẩn gán nhãn 4 hướng (bản nháp 3) | Có |
| `scripts/tao_mau_gan_thu.py` | Tạo file gán thử cho từng vòng, không lấy lại câu của vòng trước | Có |
| `scripts/tong_hop_gan_thu.py` | Tổng hợp file đã gán, tính Cohen κ và Fleiss κ | Có |
| `data/gan_nhan/vong1/gold_vong1.csv` | Gold vòng 1 sau khi rà (240 câu) | Chỉ trong nhóm |
| `data/gan_nhan/vong1/gold_vong1_truoc_ra_soat.csv` | Gold vòng 1 trước khi rà, giữ để đối chiếu | Chỉ trong nhóm |
| `data/gan_nhan/vong1/da_chot/` | File 4 người soát chung vòng 1 | Chỉ trong nhóm |
| `data/gan_nhan/vong1/*_da_chot.xlsx` | Nhãn và lý do chốt đợt rà gold vòng 1 (95 câu suggest, 44 câu stance) | Chỉ trong nhóm |
| `data/gan_nhan/vong2/` | 4 file gán vòng 2 và `tong_hop_vong2.csv` (nguồn mẫu từng câu) | Chỉ trong nhóm |
| `scripts/ra_soat/` | Script đợt rà gold vòng 1 và `docx2txt.py` (đọc docx khi không có pandoc) | Có |
| `huggingface/README.md` | Dataset card nháp để công bố trên Hugging Face | Có |
| `docs/Ke_hoach_tiep_theo_NLP_N12.docx` | Kế hoạch bước tiếp theo cho cả nhóm, các điểm còn vướng, bảng tra quy tắc gán (25/11/2026) | Có |
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

---
name: nlp-n12-dataset
description: Tiếp tục dự án NLP_N12 (BTL1) - xây bộ dữ liệu bình luận sinh viên PTIT gán nhãn 4 hướng (toxicity, topic, stance, emotion). Dùng khi người dùng hỏi về tiến trình, gán nhãn các vòng, tính κ, chốt gold, quy chuẩn gán nhãn, gán bằng LLM, hoặc "làm gì tiếp" trong thư mục BTL1.
---

# Bàn giao dự án NLP_N12: dataset 4 hướng

Bàn giao ngày 2026-11-25. **Nguồn sự thật là `BTL1/TIEN_TRINH_DATASET.md`**: đọc file đó trước, và cập nhật nó (đầu file, mục "Đang ở đâu", checklist, nhật ký) sau mỗi bước hoàn thành. File skill này tóm tắt bối cảnh, quy tắc làm việc và lộ trình; nếu hai file lệch nhau thì tin TIEN_TRINH và kiểm tra lại dữ liệu.

## 1. Bối cảnh

- Nhóm 4 người: **Hảo, Sinh, Triệu, Long**. Người dùng là **Sinh** (git user `DucSinh2k5`). Trao đổi bằng tiếng Việt.
- Dữ liệu: 141.276 bình luận cào từ 16 group Facebook sinh viên PTIT, 22.144 bài đăng. Sau làm sạch và che thông tin: **136.609 dòng** trong `cleaned/masked.csv`, chia train/val/test theo bài đăng 70/15/15, seed 42 (95.667 / 20.458 / 20.484).
- Mục tiêu: gán nhãn 4 hướng, viết paper và công bố dataset nếu qua được rà soát pháp lý, đạo đức.
- Lịch sử: giai đoạn trước nhóm làm bài toán Toxic nhị phân (E1–E8 trên 9.962 câu, quy chuẩn v2.2 "Keyword-Priority"). Kết quả đó **không phải** của dataset mới. Quy chuẩn cũ coi mọi từ tục là Toxic nên tra 56 từ khóa đã đạt F1 0,827; vì vậy hướng mới tách profane khỏi attack.

### Phạm vi, những thứ KHÔNG thuộc dự án
- `shared_dataset.csv`, `data_splits_shared/`, `results_shared/`: của **nhóm khác** (nhãn do ollama qwen3 gán). Không trộn vào phân tích của N12.
- Thư mục cha `NPL-NMF` (backend, frontend, docs, tóm tắt văn bản NMF): **dự án khác**, không liên quan.
- `tonghopcmt_n12.xlsx`: 3.123 dòng cuối là toxic ngoài PTIT. Đầu vào làm sạch phải là `tonghopcmt_n12_backup_truoc_khi_them_toxic.xlsx`.

## 2. Quy tắc làm việc (bắt buộc)

- **Riêng tư:** chỉ dùng bản đã che (`text_public`, `cleaned/masked.csv`) khi gửi cho LLM hay dịch vụ ngoài. Không đọc ra, không gửi, không chia sẻ `cleaned/private/`, `cleaned_lan2/`, `cleaned_ban_cu/` và các file `.xlsx` thô. Gửi qua API thì dùng gói không lấy dữ liệu để huấn luyện.
- **Không sửa gold mà không sao lưu.** Mọi thay đổi nhãn ghi nguồn gốc ở cột `*_cach_chot` (ví dụ `dong_y`, `phan_xu`, `ra_soat_claude`).
- **Gán thử phải độc lập**: mỗi người gán riêng rồi mới họp. Không dùng nhãn của người khác hay gold khi gán.
- **Không dùng tập Test để sửa prompt, quy chuẩn hay mô hình.** Mẫu gán thử chỉ lấy từ train.
- Đề xuất trước, sửa sau: khi rà nhãn, ghi đề xuất và lý do ra file Excel cho nhóm duyệt; chỉ ghi thẳng vào gold khi người dùng bảo. Nếu Claude là người chốt, ghi rõ để paper khai báo.
- Không commit hay đẩy dữ liệu: `gan_nhan/` có `.gitignore` chặn toàn bộ; thư mục BTL1 chưa được git theo dõi.
- Đọc docx: máy không có pandoc và python-docx. Dùng `python scripts_ra_soat/docx2txt.py <file.docx>`; script ghi `<tên>.docx.txt` vào thư mục đang đứng, nên chạy từ thư mục tạm.
- Windows: in tiếng Việt từ Python cần `PYTHONIOENCODING=utf-8`.

## 3. Bộ nhãn và các quy tắc đã chốt

Tài liệu: `Quy_chuan_gan_nhan_4_huong_NLP_N12.docx` (bản nháp 3, mục 7 là quy tắc rút ra từ vòng 1), `Thiet_ke_du_lieu_da_huong_NLP_N12.docx`.

| Hướng | Nhãn |
|---|---|
| toxicity | clean, profane, attack, unk |
| topic | academics, facilities, administration, student_life, unk |
| stance | support, oppose, suggest, none, unk |
| emotion | joy, sadness, anger, fear, surprise, neutral, unk; đa nhãn: `emotion_1` chính, `emotion_2` các cảm xúc còn lại cách nhau bằng `;` |

Quy tắc quan trọng:
- **toxicity:** từ tục chỉ để nhấn mạnh là profane; từ tục hoặc lời hạ thấp nhắm vào người là attack, kể cả trêu bạn bè kèm emoji cười.
- **stance hướng tới chủ đề của trường** (SemEval-2016), không dùng cho việc đồng tình hay phản bác người đối thoại. Chỉ bộc lộ cảm xúc thì là none.
- **Ràng buộc:** topic = unk thì stance chỉ được là none hoặc unk. Ngoại lệ: câu đồng tình hoặc phản bác bình luận cha về chủ đề của trường, khi đó gán topic theo bình luận cha.
- **suggest** là góp ý hoặc lời khuyên có hành động cụ thể, có lợi cho người khác hoặc nhà trường (khuyên bạn bè cũng tính). Không phải suggest: nhờ vả, rủ rê, xin cho bản thân, câu hỏi (đều là none). Góp ý mỉa mai hoặc mong muốn chung chung không có hành động thì là oppose.
- **topic = unk** chỉ khi câu không nói về việc gì (chỉ cảm thán, tag tên, emoji). student_life gồm cả chuyện đời thường, tiền bạc, game.
- **emotion:** dấu cười trong câu đùa là joy; "vãi", "thật hả" khi bất ngờ là surprise; toxicity và emotion độc lập (attack vẫn có thể là joy).

Quy tắc mới từ đợt rà gold vòng 1, **chưa có trong docx, cần viết vào bản 4**:
1. Câu trả lời chỉ cụ thể việc cần làm hoặc nơi cần đến ("ra tòa A1 điểm danh lại") là suggest; câu chỉ trả lời được hay không, khi nào, bao nhiêu ("sau 2/9 xin vẫn được") là none.
2. Quảng cáo, chiêu mộ CLB, tin tuyển dụng là none.
3. Đùa dưới dạng góp ý mà không chê gì là none; đùa hoặc mỉa mai có chê là oppose.
4. Đồng tình hoặc phản bác bình luận cha về chủ đề của trường thì gán topic theo bình luận cha.

## 4. Đã làm xong

- **Làm sạch** (Colab lần 3, 2026-11-12): regex kết hợp NER NlpHUST, che `[NAME]`, `[USER]`, `[ADDRESS]`, `[URL]`, `[PHONE]`, `[STUDENT_ID]`...; không lọc emoji, từ tục, teencode. Tỷ lệ sót tên ước khoảng 2,7% (đo ở lần 1).
- **Vòng 1** (240 câu, `gan_nhan/vong1/`): Hảo và Triệu gán độc lập (2026-11-19), κ toxicity 0,647, topic 0,541, stance 0,357, emotion_1 0,364. **Cả 4 người soát chung** trên file `da_chot/tong_hop_vong1_Hao_Trieu_da_chot.xlsx` (2026-11-20). Vì vậy vòng 1 chỉ có κ cặp Hảo–Triệu; κ nhiều người phải lấy từ vòng 2. Không cần ai gán lại vòng 1.
- **Rà gold vòng 1** (2026-11-24, Claude chốt theo yêu cầu): 95 câu suggest và 44 câu topic = unk có stance, kèm 3 ô trống. Kết quả và lý do từng câu trong `gan_nhan/vong1/ra_soat_suggest_vong1_da_chot.xlsx` và `xem_lai_stance_vong1_da_chot.xlsx`. Gold đã cập nhật tại `gan_nhan/vong1/gold_vong1.csv`, bản cũ là `gold_vong1_truoc_ra_soat.csv`. Stance đổi 90 câu (suggest 95 → 32), topic đổi 22 câu, 0 câu vi phạm ràng buộc, không còn ô trống. Script lưu ở `scripts_ra_soat/` (chỉ để tái lập; chạy lại `ra_soat_suggest.py` sẽ **ghi đè** file đề xuất ban đầu).
- Phân bố gold vòng 1 sau rà: toxicity clean 190 / attack 25 / profane 24 / unk 1; topic academics 81 / unk 58 / student_life 56 / administration 39 / facilities 6; stance none 137 / oppose 33 / suggest 32 / support 23 / unk 15; emotion_1 neutral 139 / joy 29 / sadness 23 / fear 17 / surprise 12 / anger 11 / unk 9.
- **Vòng 2 đã tạo file** (2026-11-24): `python tao_mau_gan_thu.py 2` → `gan_nhan/vong2/gan_thu_vong2_{Hao,Sinh,Trieu,Long}.xlsx` và `tong_hop_vong2.csv` (nguồn mẫu từng câu). 240 câu train, 229 bài đăng, không trùng vòng 1; 120 ngẫu nhiên + 4 × 30 câu ưu tiên nhãn hiếm (công kích, cơ sở vật chất, tức giận/ngạc nhiên, ủng hộ). Script có `DAU_HIEU_THEO_VONG`; đã kiểm tra chạy lại vòng 1 ra đúng mẫu cũ. Sheet `huong_dan` của file vòng 2 đã nhắc các quy tắc mục 7 và 4 quy tắc mới. **Chưa ai gán.** Đọc lướt thấy nhóm ủng hộ và tức giận/ngạc nhiên lẫn nhiều câu không mang nhãn đó ("xứng đáng độc thân", "tức là"), nên khi báo cáo kết quả theo `nguon_mau` đừng coi 30 câu mỗi nhóm là 30 câu nhãn hiếm; khi làm vòng 3 nên siết lại regex.

## 5. Lộ trình tiếp theo

Thứ tự ưu tiên. Bước 3 chặn mọi bước sau.

1. **Quy chuẩn bản 4**: viết 4 quy tắc mới (mục 3) vào docx, sửa câu chữ mục 5 về câu đùa dưới dạng góp ý. Gửi nhóm trước khi gán vòng 2. Có thể soạn nháp nội dung cho người dùng chép vào (dùng skill docx nếu sửa trực tiếp file).
2. **Người duyệt nhãn Claude chốt**: một thành viên đọc lướt 2 file `_da_chot` của vòng 1. Câu không đồng ý thì sửa gold (sao lưu trước) và đổi `*_cach_chot`.
3. **Gán vòng 2 độc lập**: 4 người gán file của mình, xong đặt vào `gan_nhan/vong2/da_gan/`.
4. **Tổng hợp vòng 2**:
   ```
   python tong_hop_gan_thu.py gan_nhan/vong2/tong_hop_vong2_4nguoi.xlsx gan_nhan/vong2/da_gan/gan_thu_vong2_Hao.xlsx gan_nhan/vong2/da_gan/gan_thu_vong2_Sinh.xlsx gan_nhan/vong2/da_gan/gan_thu_vong2_Trieu.xlsx gan_nhan/vong2/da_gan/gan_thu_vong2_Long.xlsx
   ```
   Script tự sửa lỗi gõ nhãn (ghi ở sheet `sua_loi_go`), tính Cohen κ từng cặp và Fleiss κ. Báo cáo thêm: tỷ lệ unk của từng người, lệch có hệ thống giữa các cặp, κ từng nhãn cảm xúc (hoặc Krippendorff α) vì emotion đa nhãn, kết quả tách theo `nguon_mau` (ngẫu nhiên và từng nhóm nhãn hiếm). Kiểm tra ràng buộc topic/stance trên nhãn của từng người.
5. **Họp chốt vòng 2**: theo đa số 4 người, hòa 2-2 thì nhóm phân xử; ghi lý do vào `ghi_chu_hop`; xuất `gan_nhan/vong2/gold_vong2.csv` cùng cấu trúc với `gold_vong1.csv`.
6. **Quyết định theo κ vòng 2**: hướng nào ≥ 0,67 thì đạt; 0,5–0,67 thì sửa quy chuẩn ở chỗ hay lệch; < 0,5 (dự kiến stance, emotion) thì đơn giản hóa nhãn trước vòng 3 (gộp nhãn cảm xúc, hoặc tách suggest thành hướng riêng). Không gán thêm vòng mãi.
7. **Vòng 3** (`python tao_mau_gan_thu.py 3`; vòng chưa khai báo trong `DAU_HIEU_THEO_VONG` dùng bộ của vòng mới nhất, nên cập nhật bộ dấu hiệu theo nhãn còn hiếm sau vòng 2). Lặp đến khi đạt ngưỡng. Quy chuẩn cuối cùng thì khóa phiên bản.
8. **Chạy thử LLM trên gold** (gold các vòng, khoảng 500–700 câu, không phải Test): 2–3 LLM, prompt viết từ quy chuẩn cuối, đầu ra JSON có đủ 5 cột nhãn; đo κ LLM so với gold từng hướng; chỉ sửa prompt dựa trên gold; khóa prompt, ghi phiên bản mô hình và tham số. Lưu ý: gold vòng 1 có khoảng 90 nhãn do Claude chốt, nên nếu đánh giá cả Claude thì ưu tiên gold từ vòng 2.
9. **Gán toàn bộ**: nhóm quyết định gán cả 136 nghìn câu hay một tập con khoảng 20–30 nghìn câu (chi phí API, khối lượng rà). Nhiều LLM gán, lấy đa số; câu bất đồng hoặc bị đánh dấu thì người phân xử; ghi nguồn gốc nhãn từng dòng. Chạy theo batch, lưu sau mỗi batch.
10. **Tập Test do người gán**: khoảng 1.500–2.000 câu lấy từ split test theo bài đăng, mỗi câu 2 người, bất đồng thì thêm người thứ 3. Đây là phần tốn công nhất, nên lên lịch sớm.
11. **Kiểm tra chất lượng**: kiểm tra mù khoảng 5% câu LLM đồng thuận; rà tổ hợp nhãn hiếm (attack + support...); bỏ khỏi train các câu trùng test (cột `cross_split_duplicate` trong `masked.csv`, 9.014 dòng).
12. **Baseline** (tùy chọn, quyết định khi chọn nơi nộp): BoW, TF-IDF, fastText, PhoBERT, XLM-R cho từng hướng; thêm mô hình có ngữ cảnh bài đăng và bình luận cha; báo Macro-F1, F1 từng nhãn.
13. **Paper và datasheet**: quy trình thu thập, làm sạch, ẩn danh, quy chuẩn, độ đồng thuận, thống kê, đạo đức, hạn chế. Công bố dạng gated, duyệt thủ công, có kênh yêu cầu gỡ dữ liệu.

Làm song song, không chặn việc gán:
- **Pháp lý, đạo đức (chặn công bố):** hỏi giảng viên về phê duyệt đạo đức; xác định group công khai hay kín (file dữ liệu không có cột group, phải tra danh sách lúc cào); điều khoản Meta (scraper dùng cookie); Luật 91/2025/QH15 (Điều 14, 19) với người có chuyên môn; loại group kín khỏi bản công bố nếu chưa có căn cứ. Không đưa ra kết luận pháp lý thay người có chuyên môn.
- **Làm sạch còn dở:** kiểm tra 4 câu sót tên Triệu báo ở vòng 1; đọc khoảng 50 dòng `post_text` và 50 dòng `parent_text`; quyết định giữ hay bỏ các dòng cờ spam / ít thông tin; cập nhật mục kết quả trong `Quy_tac_lam_sach_du_lieu_NLP_N12.docx` theo lần chạy 3.
- Giai đoạn 1 còn mở: đối chiếu định nghĩa OFFENSIVE, HATE của ViHSD và nhãn UIT-VSMEC với bài báo gốc.

## 6. Bản đồ file chính

| File | Vai trò |
|---|---|
| `TIEN_TRINH_DATASET.md` | Tiến trình chi tiết, checklist, nhật ký. Cập nhật sau mỗi bước |
| `Quy_chuan_gan_nhan_4_huong_NLP_N12.docx` | Quy chuẩn gán nhãn (bản nháp 3) |
| `Thiet_ke_du_lieu_da_huong_NLP_N12.docx` | Thiết kế 4 hướng, so sánh UIT-VSFC, UIT-VSMEC, ViHSD |
| `Quy_tac_lam_sach_du_lieu_NLP_N12.docx`, `clean_dataset.py` | Quy trình và script làm sạch |
| `cleaned/masked.csv` | Dataset đã che, cột chính: `comment_uid`, `post_uid`, `parent_uid`, `comment_type`, `text_public`, `post_text`, `parent_text`, `split`, `is_low_info`, `is_spam_candidate`, `parent_missing`, `post_missing`, `cross_split_duplicate` |
| `tao_mau_gan_thu.py [vòng]` | Tạo file gán thử, không lấy lại câu các vòng trước |
| `tong_hop_gan_thu.py <out.xlsx> <file>...` | Tổng hợp, κ, Fleiss κ |
| `gan_nhan/vong1/gold_vong1.csv` | Gold vòng 1 sau rà (240 câu) |
| `gan_nhan/vong1/*_da_chot.xlsx` | Nhãn và lý do đợt rà gold vòng 1 |
| `gan_nhan/vong2/` | File gán vòng 2, chờ gán |
| `scripts_ra_soat/` | Script đợt rà gold vòng 1 và `docx2txt.py` |
| `Bao_cao_tien_do_NLP_N12.docx` | Báo cáo giai đoạn Toxic nhị phân cũ (E1–E8), chỉ để tham khảo |

## 7. Cách trả lời người dùng

- Khi được hỏi "làm gì tiếp": đọc TIEN_TRINH, kiểm tra trạng thái thật của file (ví dụ thư mục `da_gan/` đã có file chưa, cột nhãn đã điền chưa) rồi mới trả lời. Lệnh kiểm tra nhanh vòng 2 (chạy trong `BTL1`):
  ```
  PYTHONIOENCODING=utf-8 python -c "import pandas as pd, glob; [print(f, pd.read_excel(f, sheet_name='gan_nhan')[['toxicity','topic','stance','emotion_1']].notna().sum().to_dict()) for f in sorted(glob.glob('gan_nhan/vong2/**/gan_thu_vong2_*.xlsx', recursive=True))]"
  ```
- Người dùng có thể giao Claude tự chốt nhãn thay nhóm (đã làm ở vòng 1). Khi đó vẫn ghi lý do từng câu, ghi `ra_soat_claude` ở `*_cach_chot`, sao lưu gold, và nhắc rằng cần một người duyệt lại để paper khai báo đúng.
- Trình bày theo kiểu ngắn gọn, có bảng số liệu trước/sau khi sửa nhãn; người dùng thích nhận file Excel để tự soát (gửi file bằng SendUserFile nếu có).
- Nêu rõ cái gì đã kiểm chứng, cái gì là ước tính. Không khẳng định số liệu chưa đo lại.
- Sau mỗi việc hoàn thành, cập nhật TIEN_TRINH_DATASET.md (checklist + nhật ký có ngày).

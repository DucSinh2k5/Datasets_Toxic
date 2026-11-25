---
# Metadata cho Hugging Face Hub. Dòng có TODO cần nhóm quyết định trước khi công bố.
language:
- vi
pretty_name: PTIT Student Comments with Toxicity, Topic, Stance and Emotion Labels  # TODO: đặt tên ngắn cho dataset
license: other  # TODO: chọn giấy phép sau khi rà soát pháp lý, ví dụ cc-by-nc-sa-4.0
license_name: todo
multilinguality:
- monolingual
size_categories:
- 100K<n<1M
source_datasets:
- original
language_creators:
- found
annotations_creators:
- expert-generated
- machine-generated  # TODO: giữ nếu phần lớn nhãn do LLM gán (giai đoạn 4)
task_categories:
- text-classification
task_ids:
- hate-speech-detection
- topic-classification
- sentiment-classification
- multi-class-classification
- multi-label-classification
tags:
- toxicity
- offensive-language
- stance-detection
- suggestion-mining
- emotion-recognition
- student-feedback
- social-media
configs:
- config_name: default
  data_files:
  - split: train
    path: data/train.parquet
  - split: validation
    path: data/validation.parquet
  - split: test
    path: data/test.parquet
extra_gated_prompt: >-
  This dataset contains anonymized Facebook comments written by Vietnamese university students.
  Requests are reviewed manually and access is granted for non-commercial research only.
  Do not try to identify any person in the data, and do not redistribute it.
extra_gated_fields:
  Name: text
  Affiliation: text
  Country: country
  Intended use: text
  I will use this dataset for non-commercial research only: checkbox
  I will not try to identify any person in this dataset: checkbox
  I will not redistribute this dataset: checkbox
---

<!--
Bản nháp dataset card, soạn ngày 2026-11-25.
- Nội dung viết bằng tiếng Anh theo thông lệ Hugging Face; ghi chú TODO bằng tiếng Việt cho nhóm, xóa hết trước khi công bố.
- Số liệu lấy từ data/cleaned/report.json (làm sạch lần 3), masked.csv và TIEN_TRINH_DATASET.md.
- Định nghĩa nhãn tóm tắt từ docs/Quy_chuan_gan_nhan_4_huong_NLP_N12.docx (bản nháp 3) và các quy tắc mới sau vòng 1. Khi quy chuẩn đổi thì sửa mục "Label definitions".
- Trên HF, file này là README.md ở gốc repo dataset; dữ liệu đặt trong data/*.parquet (xem configs ở trên).
-->

# PTIT Student Comments: Toxicity, Topic, Stance and Emotion

> **Status: draft, not released.** Labeling is in progress. Release depends on a legal and ethics review.

## Dataset summary

This dataset contains 136,609 Vietnamese Facebook comments from 22,144 posts in 16 student groups of the Posts and Telecommunications Institute of Technology (PTIT), Vietnam. Each comment is labeled on four independent aspects:

| Aspect | Labels | Type |
|---|---|---|
| `toxicity` | clean, profane, attack, unk | single-label |
| `topic` | academics, facilities, administration, student_life, unk | single-label |
| `stance` | support, oppose, suggest, none, unk | single-label |
| `emotion` | joy, sadness, anger, fear, surprise, neutral, unk | multi-label: `emotion_1` (primary) and `emotion_2` (others) |

Each comment comes with the text of its post and, for replies, its parent comment, so models can use the conversation as context. Personal information is masked with placeholders such as `[NAME]` and `[PHONE]`.

<!-- TODO: thêm 1–2 câu về điểm mới so với UIT-VSFC, UIT-VSMEC, ViHSD (xem docs/Thiet_ke_du_lieu_da_huong_NLP_N12.docx). -->

## Supported tasks

- **Toxicity detection.** Separates profanity used for emphasis (`profane`) from language aimed at a person or group (`attack`), following OLID.
- **Topic classification.** Which part of university life a comment is about, extending UIT-VSFC.
- **Stance detection and suggestion mining.** The writer's stance towards the university-related topic (SemEval-2016 Task 6), plus actionable suggestions (SemEval-2019 Task 9).
- **Emotion recognition.** Basic emotions as in UIT-VSMEC, with multi-label annotation and an exclusive `neutral` label as in GoEmotions and SemEval-2018 Task 1.
- **Context-aware classification.** Every aspect can be modeled with or without the post and the parent comment.

<!-- TODO (giai đoạn 6, tùy chọn): kết quả baseline, Macro-F1 từng hướng. -->

## Languages

Vietnamese (`vi`) as written on social media. Teencode, abbreviations, missing diacritics, elongated words, profanity and emoji are kept as written.

## Dataset structure

### Data instance

The values below show the format only and are not a real comment.

<!-- TODO: có thể thay bằng một ví dụ thật đã che sau khi rà soát pháp lý; tránh câu tìm lại được trên Facebook. -->

```json
{
  "comment_uid": "p0a1b2c3d4e5f_12",
  "post_uid": "p0a1b2c3d4e5f",
  "parent_uid": "",
  "comment_type": "top_level",
  "text_public": "<comment text, with names replaced by [NAME]>",
  "post_text": "<post text>",
  "parent_text": "",
  "toxicity": "clean",
  "topic": "academics",
  "stance": "none",
  "emotion_1": "fear",
  "emotion_2": "sadness",
  "is_low_info": false,
  "is_spam_candidate": false,
  "post_is_ad_candidate": false,
  "parent_missing": false,
  "post_missing": false,
  "cross_split_duplicate": false
}
```

### Data fields

| Field | Type | Description |
|---|---|---|
| `comment_uid` | string | Comment ID: `post_uid`, `_`, then the comment's ID within the post |
| `post_uid` | string | Post ID, random (`p` + 12 hex characters), not derived from Facebook IDs |
| `parent_uid` | string | For replies, the `comment_uid` of the parent comment; empty for top-level comments |
| `comment_type` | string | `top_level` (85,404) or `reply` (51,205) |
| `text_public` | string | The comment, normalized and masked |
| `post_text` | string | The post, masked |
| `parent_text` | string | For replies, the parent comment, masked; empty for top-level comments |
| `toxicity` | string | `clean`, `profane`, `attack` or `unk` |
| `topic` | string | `academics`, `facilities`, `administration`, `student_life` or `unk` |
| `stance` | string | `support`, `oppose`, `suggest`, `none` or `unk` |
| `emotion_1` | string | Primary emotion |
| `emotion_2` | string | Other emotions present, in decreasing salience, separated by `;`; empty if none |
| `is_low_info` | bool | Text of at most 2 words that occurs 20 or more times and has no emoji, or text made only of placeholders |
| `is_spam_candidate` | bool | Comment matches advertising patterns (inbox, Zalo, recruitment, rentals, sales) |
| `post_is_ad_candidate` | bool | Post matches the same advertising patterns |
| `parent_missing` | bool | Reply whose parent comment text is missing (363 comments) |
| `post_missing` | bool | Comment whose post text is missing (721 comments) |
| `cross_split_duplicate` | bool | Same text also appears in another split; low-information texts excluded (9,014 comments) |

<!--
TODO (giai đoạn 4): thêm cột nguồn gốc nhãn, ví dụ label_source = human | llm_majority | human_adjudicated, và tên, phiên bản LLM.
TODO: quyết định có công bố 2 cột còn lại của masked.csv không:
  - data_status (từ file cào: valid 135.131, review 1.478): cần hỏi người cào ý nghĩa của "review".
  - pii_types: loại thông tin đã che trong bình luận, cách nhau bằng ";" (ví dụ NAME;URL).
TODO: đổi giá trị split "val" thành "validation" khi xuất.
-->

### Label definitions

Short versions of the annotation guidelines. <!-- TODO: link tới bản quy chuẩn cuối (có bản tiếng Anh không?). -->

The four aspects are labeled independently: a teasing `attack` can carry `joy`, and a positive comment can be `profane`. `unk` means the annotator cannot decide even with the context; it is not a substitute for `none` or `neutral`.

**toxicity** (OLID, flattened as in ViHSD)

| Label | Definition |
|---|---|
| `clean` | No profanity and no insult, including harsh but polite criticism |
| `profane` | Profanity, swearing or filter-evading spellings not aimed at a person or group: used for emphasis, as an exclamation, or to complain about things and events |
| `attack` | Insults, threats, mockery or ridicule aimed at a person (including a tagged `[NAME]` or the parent commenter) or a group of people, with or without profanity. Teasing friends with demeaning words is `attack` even with laughing emoji |
| `unk` | Cannot decide, e.g. an ambiguous abbreviation with no context |

**topic** (extends UIT-VSFC, one label per comment)

| Label | Covers |
|---|---|
| `academics` | Lecturers, programs and courses, exams, grades, study materials |
| `facilities` | Classrooms, equipment, Wi-Fi, library, canteen, parking, dormitory |
| `administration` | Procedures, regulations, tuition, scholarships, student portal, course registration |
| `student_life` | Extracurricular activities, clubs, conduct points, internships, jobs, daily life (money, games), stress and mental health |
| `unk` | No identifiable subject: tags, generic exclamations, emoji only, spam |

Short replies such as "+1" or "right" take the topic of the parent comment, or of the post if there is no parent.

**stance** (SemEval-2016 Task 6 and SemEval-2019 Task 9). The target is the university-related topic, not the other person in the conversation.

| Label | Definition |
|---|---|
| `support` | Agrees with, praises, thanks or defends the target |
| `oppose` | Disagrees with, criticizes, complains about or mocks the target. Includes sarcastic "suggestions" and vague wishes with no concrete action |
| `suggest` | A suggestion or advice with a concrete action that benefits others or the university, including advice to friends and directions on what to do or where to go |
| `none` | No stance: questions, short factual answers, information, announcements, tags, greetings, ads, club recruitment, job posts, requests for oneself, jokes phrased as suggestions that criticize nothing, and comments that only express emotion |
| `unk` | Cannot decide even with context, e.g. a short reply whose parent is missing |

Constraint: if `topic` is `unk`, then `stance` is `none` or `unk`.

**emotion** (basic emotions as in UIT-VSMEC; multi-label and exclusive `neutral` as in GoEmotions)

| Label | Covers |
|---|---|
| `joy` | Happiness, excitement, pride, amusement, teasing, satisfaction |
| `sadness` | Sadness, discouragement, disappointment, regret, tiredness |
| `anger` | Annoyance, frustration, outrage, contempt (includes disgust) |
| `fear` | Worry, stress, fear, pressure, confusion |
| `surprise` | Surprise, shock, disbelief |
| `neutral` | Clearly no emotion: questions, information, announcements, tags, ads |
| `unk` | Cannot decide |

`emotion_1` is the primary emotion and `emotion_2` lists the other emotions present. `neutral` and `unk` exclude all other labels. Sarcasm is labeled with the real emotion, and profanity does not decide the emotion.

### Data splits

Comments are split by post (70/15/15 of posts, seed 42), so all comments of a post are in the same split.

| Split | Posts | Comments |
|---|---|---|
| train | 15,485 | 95,667 |
| validation | 3,196 | 20,458 |
| test | 3,463 | 20,484 |
| **total** | **22,144** | **136,609** |

<!--
TODO: phân bố nhãn từng split sau khi gán xong.
TODO: dự kiến tập test do người gán (khoảng 1.500–2.000 câu từ split test, mỗi câu 2 người); nếu vậy thì ghi rõ split test nào là nhãn người.
TODO: dự kiến bỏ khỏi train các câu trùng với test (cross_split_duplicate); cập nhật số dòng ở bảng trên.
-->

## Dataset creation

### Curation rationale

Vietnamese already has datasets for single aspects of this problem, such as UIT-VSFC for student feedback, UIT-VSMEC for emotion and ViHSD for hate speech, but they come from different sources. This dataset labels the same student comments on four aspects, with conversational context, so the aspects can be studied together.

Profanity is separated from attacks because Vietnamese student comments use swear words heavily for emphasis. In an earlier binary version of this project (9,962 comments) where all profanity counted as toxic, a lookup of 56 keywords already reached an F1 of 0.827.

<!-- TODO: kiểm tra lại số 0,827 và 56 từ khóa trước khi đưa vào paper. -->

### Source data

Comments and replies were collected from 16 Facebook groups of PTIT students: 141,276 comments from 22,144 posts.

<!--
TODO: thời điểm thu thập và khoảng thời gian của bài đăng.
TODO: mô tả cách thu thập (công cụ, có đăng nhập không) sau khi xem điều khoản Meta.
TODO: danh sách group công khai hay kín (giai đoạn 7); loại group kín khỏi bản công bố nếu chưa có căn cứ.
-->

### Cleaning and anonymization

- Text is normalized to Unicode NFC, whitespace is collapsed, and stray Excel apostrophes are removed. Emoji, punctuation, elongated words, profanity and teencode are kept.
- 4,667 comments that duplicate another comment in the same context were removed.
- Personal information in the comment, the post and the parent comment is masked in two passes: regular expressions, then a Vietnamese NER model ([NlpHUST/ner-vietnamese-electra-base](https://huggingface.co/NlpHUST/ner-vietnamese-electra-base)) for person names.
- Province, district and university names, building codes such as A2 or B5, and street names after "đường" or "phố" are kept. Only addresses with house numbers are masked.
- Facebook post and comment IDs are replaced by random IDs. The mapping is kept private and is not released.

Comments containing each placeholder (comment field only; a comment can contain several):

| Placeholder | Masks | Comments |
|---|---|---|
| `[NAME]` | Person names | 53,070 |
| `[USER]` | Facebook-generated anonymous names and tags | 12,311 |
| `[URL]` | Links | 2,712 |
| `[PHONE]` | Phone numbers | 875 |
| `[ADDRESS]` | Addresses with house numbers | 221 |
| `[STUDENT_ID]` | Student and class codes | 96 |
| `[EMAIL]` | Email addresses | 30 |
| `[NUMBER]` | Long digit sequences | 20 |

### Annotations

#### Guidelines

The guidelines were written by the authors from OLID, UIT-VSFC, SemEval-2016 Task 6, SemEval-2019 Task 9, GoEmotions, SemEval-2018 Task 1 and UIT-VSMEC, and revised after each trial round.

<!-- TODO: công bố quy chuẩn bản cuối kèm dataset, ghi số phiên bản. -->

#### Process

1. **Trial rounds.** In each round, the annotators independently label the same 240 comments from the train split: 120 sampled at random and 120 oversampled for rare labels. They then meet to adjudicate disagreements and revise the guidelines.
2. **Full labeling.** <!-- TODO (giai đoạn 4): LLM nào, phiên bản prompt, biểu quyết đa số, người phân xử câu bất đồng, ghi nguồn gốc nhãn từng dòng. -->
3. **Test set.** <!-- TODO: tập test do người gán, mỗi câu 2 người, bất đồng thì người thứ 3. -->
4. **Quality control.** <!-- TODO (giai đoạn 5): kiểm tra mù khoảng 5% câu LLM đồng thuận, rà tổ hợp nhãn hiếm. -->

#### Inter-annotator agreement

Pilot round 1, before the guidelines were revised: 2 annotators, 240 comments, Cohen's κ.

| Aspect | κ |
|---|---|
| toxicity | 0.647 |
| topic | 0.541 |
| stance | 0.357 |
| emotion_1 | 0.364 |

<!-- TODO: thêm Fleiss κ 4 người từ vòng 2 trở đi và κ giữa LLM với gold. -->

#### Annotators

The four authors. <!-- TODO: thông tin người gán (đơn vị, ngôn ngữ mẹ đẻ, cách tập huấn). -->

In the round-1 gold set, 114 labels on 100 of the 240 comments (stance 90, topic 22, emotion 2) were finalized by an LLM (Claude), which applied the guidelines at the team's request and recorded a reason for each comment.

<!-- TODO: ghi kết quả khi một thành viên đã duyệt lại các nhãn này; cân nhắc không dùng gold vòng 1 để chấm LLM. -->

### Personal and sensitive information

The comments are written by real students and may mention grades, health, money or personal conflicts. Masking reduces but does not remove the risk of re-identification:

- A manual audit of 500 comments on the previous cleaning run estimated that about 2.7% of comments still contained an unmasked real name (95% confidence intervals for the two audited strata: 1.1–5.1% and 1.6–6.2%). The final run fixed most of the misses found in that audit but was not re-measured.
- Names written in lowercase, one-word names at the start of a sentence, and names without diacritics are the most likely to be missed. Phone numbers written with emoji digits, full-width digits or words are not detected.
- The text of a comment can be searched on Facebook to find the original post and author.

For these reasons, access is gated and reviewed manually, and users agree not to try to identify anyone.

## Considerations for using the data

### Social impact

The data can help study what students care about and support the moderation of student groups. It must not be used to profile, monitor or identify students.

### Biases

- One university and one platform. Writers are mostly students, so the data does not represent Vietnamese speakers in general.
- Some labels are rare. The trial rounds oversampled rare labels, so label distributions from those rounds do not reflect the full dataset.

<!-- TODO: thiên lệch có thể có từ nhãn do LLM gán. -->

### Other known limitations

- Masking is imperfect in both directions. Some names are missed (see above), and some non-personal names are masked, such as page names, brands, singers and some street names.
- The place-name list used to avoid false masking predates Vietnam's 2025 administrative merger and has no commune or ward level.
- Context is missing for 363 replies (parent text) and 721 comments (post text).
- 9,014 comments share their text with a comment in another split and are flagged by `cross_split_duplicate`.

## Additional information

### Dataset curators

The NLP_N12 team: Hảo, Sinh, Triệu, Long.

<!-- TODO: họ tên đầy đủ, đơn vị, giảng viên hướng dẫn. -->

### Licensing information

TODO

### Access and takedown requests

Access is gated and each request is reviewed manually. To have a comment removed, contact TODO with the `comment_uid` or the text of the comment.

<!-- TODO: bật "Manual approval" trong Settings của repo trên HF (mặc định HF tự duyệt yêu cầu truy cập). Tạo kênh nhận yêu cầu gỡ (email nhóm). -->

### Citation

```bibtex
TODO
```

### References

- Zampieri et al. (2019). Predicting the Type and Target of Offensive Posts in Social Media (OLID). NAACL.
- Luu et al. (2021). A Large-scale Dataset for Hate Speech Detection on Vietnamese Social Media Texts (ViHSD).
- Nguyen et al. (2018). UIT-VSFC: Vietnamese Students' Feedback Corpus. KSE.
- Mohammad et al. (2016). SemEval-2016 Task 6: Detecting Stance in Tweets.
- Negi et al. (2019). SemEval-2019 Task 9: Suggestion Mining from Online Reviews and Forums.
- Demszky et al. (2020). GoEmotions: A Dataset of Fine-Grained Emotions. ACL.
- Mohammad et al. (2018). SemEval-2018 Task 1: Affect in Tweets.
- Ho et al. (2019). Emotion Recognition for Vietnamese Social Media Text (UIT-VSMEC).

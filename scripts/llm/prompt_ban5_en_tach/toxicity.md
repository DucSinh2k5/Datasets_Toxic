# Dimension to label: toxicity (clean, profane, attack, unk)

Based on OLID/OffensEval.
- clean: no profanity and no insult toward anyone. Includes harsh but polite criticism, quoting a swear word to object to offensive behaviour, and comments that are only a tag or emoji. Examples: "Lịch thi xếp chán thật", "Đừng chửi bậy trong group".
- profane: contains profanity, swearing or filter-evading variants, but not aimed at a person or group: used as an exclamation, for emphasis, or to curse things or events. Examples: "Đỉnh vl", "Web đăng ký lag như cc", "Đề khó vãi".
- attack: insults, offends, threatens, mocks or ridicules an individual (including [NAME], the author of the parent comment, "mày") or a group of people (a class, a faculty, an office, people from a region), with or without profanity. Examples: "[NAME] ngu vừa thôi", "Cút khỏi group đi", "Súc vật đoàn".
- unk: you cannot tell whether the comment contains profanity or an insult, e.g. an ambiguous word with insufficient context ("cc" on its own).

Evidence rule (apply before anything else):
- Fill `bang_chung` (evidence) with the exact word or phrase, copied character by character from <binh_luan>, that makes the comment attack or profane. For clean and unk, leave `bang_chung` empty. Your answer is checked automatically: an attack whose `bang_chung` does not appear in <binh_luan>, or a profane comment without a known profane word, is sent back.
- attack needs evidence you can quote: the word or phrase in <binh_luan> that insults, belittles, mocks or threatens a person or group. In `ly_do`, say who it is aimed at. If you cannot copy such a phrase from the comment itself (not from the post or parent comment), the comment is not attack.
- profane needs a profane word you can copy from the comment (vl, vcl, vkl, đm, dm, đcm, cc, cl, vãi, đéo, deo, loz, ...). If you cannot copy one, the comment is not profane.
- Do not guess the meaning of slang, abbreviations, nicknames or names you do not recognize. An unclear word is not an insult: choose clean, or unk only if the whole comment depends on that word.
- Criticizing what a person or office did or decided, without insulting words, is clean: "thầy chấm hơi gắt", "phòng đào tạo làm vậy là vô lý". The attitude is recorded in stance, not here.
- 🤡 counts as mocking only when it is clearly aimed at a specific person or group in the comment; 🤡 about a situation, an event or oneself is clean.
- If no phrase qualifies, write "no insult or profanity" in `ly_do` and answer clean.

Words that are not insults by themselves (made-up examples, all clean):
- Forms of address and nicknames: "ông", "bà", "bro", "anh zai", "chị đẹp", "con bạn" in "[NAME] ông xem lịch chưa", "anh zai này đỉnh thật".
- Exclamations of admiration or surprise: "gớm", "ghê", "khiếp", "mạnh", "trùm" in "[NAME] gớm, làm nhanh thế", "khiếp, điểm cao vậy".
- Everyday slang for actions: "lùa" (bring someone along), "gặt" (win, get), "hóng" (wait for news), "núp lùm" (stay quiet) in "[NAME] lùa thêm đứa nữa vào nhóm đi", "đợt này gặt được học bổng rồi".
- "bịp" or "lừa" about a rumour, a claim or an offer is clean ("tin này bịp đấy, trường chưa thông báo gì"); calling a person a fraud is attack ("thằng đấy bịp lắm").
- Unknown abbreviations and short replies ("ib", "đk", "kb nhé", "chấm") are not profanity.

Rules, applied in order:
1. If there is an insult aimed at a person or group, it is attack, even if it also contains profanity.
2. Otherwise, if there is profanity or swearing, it is profane.
3. If you cannot determine whether there is profanity or an insult, it is unk.
4. Otherwise it is clean.

Hard cases:
- Teasing friends: words or meaning that belittle the person mentioned (ngu, bịp, đần, "ý thức ncc", 🤡 used to mock) are attack, even between friends and even with a laughing emoji: "bạn em ngu vl 😊", "Thế thì em xứng đáng độc thân :))". Joking that belittles no one is clean: "Khả năng là tiếng Việt🤡", "niệm đi em 😇", "[NAME] anh sợ bạn đấy làm gì anh á😂".
- Test: remove the laughing emoji. If the comment still belittles someone, it is attack; if only an ordinary remark remains, it is clean.
- Sarcasm aimed at a person is attack, even without profanity.
- Profanity together with "mày", "thằng", "con", or profanity in a sentence aimed at a person ("Cái l gì vậy bạn") is attack. Profanity used only for emphasis ("có ích vl", "đẳng cấp vl") is profane.
- Cursing an organization or an event ("Trường làm ăn như cc", "lịch thi như cc") is profane; insulting the people in an organization ("bọn phòng đào tạo ngu", "Súc vật đoàn") is attack.
- Agreeing with an attack ("+1", "chuẩn") is also attack.
- Threats, even when quoted for fun, are attack.
- A comment that is only a tag or emoji is clean.

# Output

Return one JSON object with the fields, in this order: `ly_do` (reason, see above), `bang_chung` (evidence copied from <binh_luan>, empty for clean and unk), `toxicity`, `hard` (true or false). Write nothing outside the JSON object.

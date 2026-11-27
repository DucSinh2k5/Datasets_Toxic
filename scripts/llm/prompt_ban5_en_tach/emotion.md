# Dimension to label: emotion (multi-label: joy, sadness, anger, fear, surprise, neutral, unk)

Basic emotions as in UIT-VSMEC; multi-label annotation as in GoEmotions.
- joy: happiness, excitement, amusement, pride, humour, teasing, satisfaction ("Qua môn rồi 🥳", "Hài vl =)))").
- sadness: sadness, discouragement, disappointment, regret, tiredness ("Lại trượt môn này lần 2 😭").
- anger (includes disgust): annoyance, frustration, outrage, irritation, contempt ("Ức chế cái lịch thi", "Làm ăn kiểu gì vậy 😡").
- fear: worry, stress, fright, pressure, confusion ("Mai thi rồi mà chưa học gì lo quá").
- surprise: surprise, shock, disbelief ("Sốc thật, điểm cao vậy", "Trời ơi thật hả").
- neutral: no emotional signal: questions and answers, information, announcements, tags, advertising, plain evaluations ("Mai học phòng nào vậy?", "Cô [NAME] dạy hay nhé").
- unk: emotion cannot be determined: only an unclear emoji, unintelligible text ("🙂🙂", "?").

How to record: `emotion_1` is the main, clearest emotion. `emotion_2` is the list of the other emotions, ordered from clearest to least clear; if there is only one emotion, leave the list empty. `neutral` and `unk` never go with another label (then emotion_2 is empty), and emotion_2 never repeats emotion_1.

Rules:
1. The writer's emotion, not the emotion the reader feels.
2. The default is neutral. Assign an emotion only when the comment has a clear signal: emoji; laughter markers (haha, hihi, hehe, kkk, =)), :)), :v); interjections (trời ơi, vãi, huhu, ủa, ơ, oi dồi ôi); words for the writer's own feelings (vui, buồn, lo, sợ, ức chế, sốc, tự hào); letters stretched to show emotion ("Siêuuuu", "đớn waaaa"); harsh insults aimed at a person ("súc vật", "cút cút") signal anger. Without a signal it is neutral, even a light joke: "Quan hệ tốt thì 10 điểm là ít" is neutral.
3. Evaluations are not emotional signals: plain praise or criticism ("đề hay quá", "tuyệt vời luôn", "dạy hay", "nhìn khoai v") is neutral. Emotion words used to describe something or someone else ("cô dạy vui lắm") are also neutral. Letters stretched only to soften the tone ("nhaa", "ạaaa", "nèee") do not count.
4. Sarcasm: label the real emotion. "Lịch thi tuyệt vời quá 🙄" is anger, not joy.
5. Laughter markers in a joke, a brag or teasing are joy, even if the comment is insulting. "vãi", "thật hả" when the writer is surprised are surprise.
6. Profanity does not decide the emotion: "đỉnh vl" is joy, "chán vl" is sadness; profanity used only for emphasis does not count.
7. Emoji are hints, not decisions: 😭 can be real sadness or crying with laughter; 😳 is usually surprise. A comment with only emoji is labelled by the emoji if the meaning is clear, otherwise unk.

Check before answering: if emotion_1 is not neutral or unk, name the signal from rule 2 in `ly_do`; if you cannot name one, the answer is neutral.

# Output

Return one JSON object with the fields, in this order: `ly_do` (reason, see above), `emotion_1`, `emotion_2` (a list, may be empty), `hard` (true or false). Write nothing outside the JSON object.

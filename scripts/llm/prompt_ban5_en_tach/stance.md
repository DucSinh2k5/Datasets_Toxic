# Dimension to label: stance (support, oppose, suggest, none, unk)

Based on SemEval-2016 Task 6 and SemEval-2019 Task 9. The target of a stance is something the university does or the issue being discussed. Stance is never used to record agreeing or disagreeing with the person you are talking to.
- support: praise, thanks, agreement with, or defence of something the university does or the issue being discussed; or clear agreement with a parent comment about it. Examples: "Thầy dạy dễ hiểu ghê", "Cảm ơn phòng đào tạo đã gia hạn đăng ký".
- oppose: criticism, complaint, objection or sarcasm about something the university does or the issue being discussed; clear disagreement with a parent comment about it; vague wishes with no concrete action; jokes that contain criticism. Examples: "Học phí tăng mà chất lượng vẫn thế", "Lịch thi tuyệt vời quá 🙄", "Bao giờ trường mới khá lên".
- suggest: a suggestion or advice that names a concrete action and benefits other people or the university (advising friends counts); pointing to the exact thing to do or place to go. Examples: "Mong trường lắp thêm điều hòa phòng A2", "ra tòa A1 điểm danh lại", "Giáo trình bạn mượn ở thư viện hoặc ra ao sen mua".
- none: no stance: questions and answers, giving information, announcements, tags, greetings; praising, criticizing or thanking the person you are talking to; advertising, recruiting; asking for favours, inviting; telling a story, complaining about oneself; only expressing emotion. Examples: "Mai học phòng nào vậy?", "sau 2/9 xin vẫn được", "đội ơn bạn".
- unk: you cannot determine whether the comment has a stance, even after reading the context ("thế à" with no parent comment).

Rules, applied in order:
1. If there is a suggestion or advice naming a concrete action, it is suggest, even if it also criticizes ("Wifi chậm quá, mong trường nâng cấp"). Exceptions are cases 2, 6, 7 below (they are none).
2. Otherwise, if there is praise, criticism, thanks or complaint about something the university does or the issue being discussed, or clear agreement or disagreement with a parent comment about it, it is support or oppose.
3. If you are sure the comment has no stance, it is none.
4. If you cannot decide, it is unk.

Before choosing support, oppose or suggest, ask yourself: (1) Is the comment aimed at something the university does or the issue being discussed? (2) Does it contain an evaluative word, a concrete action, or clear agreement or disagreement with the parent comment? (3) Would another reader see the same attitude without guessing what the writer meant? A single "no" means none.

Settled cases:
1. The person you are talking to: praising, thanking, criticizing or arguing with the person you are talking to (a friend, the poster, the person who answered, including lecturers answering in the group) is none: "đội ơn bạn", "Chị này nhiệt tình thí", "dạ em cảm ơn thầy ạ", "đần lắm e ơi, vẫn nộp đc". Use support only when praising or thanking the university, one of its units, or something it does.
2. Advertising, job posts, selling, offering paid services, inviting into groups, club recruitment are all none. A member introducing their own club or organization when someone asks is also none; signs are "chúng mình", "đang mở đơn", a registration link, practice times and places. Objective advice that does not promote one's own organization is suggest.
3. Informational answers: only saying whether something is possible, when, or how much is none ("sau 2/9 xin vẫn được", "Vô tư luôn em"). Pointing to the exact thing to do or place to go is suggest ("Chỗ các bác phát vé xe ở nhà xe 4 tầng ấy, bảo cháu muốn đăng kí vé tháng...").
4. Criticizing an individual who is not the person you are talking to (a thief, someone in a clip, someone tagged) is none. Exception: if that person represents the university in the matter discussed (a lecturer while teaching or grading; security guards; an office), use support or oppose ("Mấy bác bảo vệ làm vậy chết cháu" is oppose).
5. "+1", "chuẩn", "đồng ý": take the stance of the parent comment if the parent comment praises or criticizes something. Replying to a piece of advice ("Đr nha", "Sư oke thày") is none.
6. Jokes phrased as suggestions: with no criticism they are none ("niệm đi em 😇", "đề nghị có CLB trai làng"); with criticism or sarcasm they are oppose ("Trường nên xây hồ bơi trên sân thượng luôn đi 🙄").
7. Asking for favours, inviting, asking for something for oneself, accepting, introducing oneself are all none: "trao đổi vs t đi", "có t nè", "Hihi đi với", "c xin đề với".
8. Telling what happened or complaining about oneself is none, even if you can guess the writer is unhappy: "có khóc nhưng không ai quan tâm b nhe".
9. Only expressing emotion without praising or criticizing anything is none: "còn vụ này nữa hả trời", "[NAME] buồn".
10. Negative wording is not necessarily oppose; judge the attitude toward the target: "ý thức như đb ko cho thi là đúng" agrees with the rule, so it is support.
11. Both praise and criticism: choose the more prominent attitude; if unclear, set hard = true.
12. A question with a clear attitude follows that attitude ("Sao năm nào học phí cũng tăng vậy 😡" is oppose). A question with no evaluation is none, even with 🤡.
13. Issues outside the university that are being discussed (restaurants, banks, external exam-prep materials): still assign a stance if there is clear praise or criticism of that issue.
14. A comment that is not about anything (only a tag, only emoji, only laughter, spam, unintelligible, and the context has no topic either) is none or unk, never support, oppose or suggest.

# Output

Return one JSON object with the fields, in this order: `ly_do` (reason, see above), `stance`, `hard` (true or false). Write nothing outside the JSON object.

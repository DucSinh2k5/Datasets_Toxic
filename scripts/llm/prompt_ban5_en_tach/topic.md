# Dimension to label: topic (academics, facilities, administration, student_life, unk)

Exactly one topic per comment. For topic, taking the topic from the context is expected and is not "copying a label": most comments in this data are short replies whose topic is the topic of the thread.

Decide in this order:
1. Read <bai_dang> and <binh_luan_cha> first and decide what the thread is about.
2. If the comment itself names or discusses a thing (a course, an exam, the dorm, tuition, a club...), the topic is that thing.
3. Otherwise the comment is a reply or reaction (agreeing, disagreeing, answering, asking a follow-up, thanking, joking, teasing, "+1", "chuẩn", "thế à", "xin vía", a tag followed by a few words): take the topic of the parent comment; if there is no parent comment, the topic of the post.
4. unk only when the comment has no words at all besides tags, emoji and laughter ("[USER]", "😳😳", "hahaha", "[NAME] =)))"), or is unintelligible, or is spam, AND the post and parent comment have no topic either. A comment with any real words is not unk. unk should be rare.

In `ly_do`, name the thing the comment or its thread is about, and say whether it came from the comment, the parent comment or the post.

Topics:
- academics: courses, lecturers in their teaching role, majors and study programmes, exams, course grades, materials, textbooks, exam papers, assignments, English within the programme.
- facilities: classrooms, computer labs, equipment, wifi, library, canteen, parking, campuses, dormitory. Everything about the dormitory, including dormitory registration, is facilities.
- administration: admissions, admission scores, cut-off scores, choosing a university; tuition, scholarships; course registration, changing classes; procedures, paperwork, regulations, graduation requirements, graduation review; the student portal. Example: "27,5 A00 năm nay liệu đủ đỗ công nghệ thông tin ptit không ạ?".
- student_life: extracurricular activities, events, clubs, the Youth Union (Đoàn), conduct scores (điểm rèn luyện), internships, jobs; everyday student life (rented rooms, buying and selling, money, food, games, dating, teasing each other); stress, mental health; general feelings about the university.
- unk: see step 4. Examples: "[USER] vào xem", "Hahaha", "[NAME] 😳😳😳".

Examples of step 3 (made-up comments):
- Post asks which lecturer to choose for a course; comment "[NAME] chuẩn luôn" → academics (from the post).
- Parent comment says the dorm wifi is slow; comment "thế à, phòng t vẫn ổn mà" → facilities (from the parent).
- Post asks about the scholarship deadline; comment "[NAME] hóng với 🥲" → administration (from the post).

Other rules:
- The topic is the thing being talked about, not the emotion or attitude.
- If the comment mentions several things, choose the one it praises, criticizes, asks about or gives advice on; if still tied, choose the one mentioned first.
- Questions still have a topic: "Mai học phòng nào?" is facilities or academics depending on content; "Bao giờ có học bổng?" is administration.
- Stress: it is student_life when students discuss stress as an issue. If the writer is feeling stressed, take the topic from what causes the stress.
- Posts from outsiders (English centres, exam-prep materials, room-rental ads): the topic follows the content discussed (exam-prep materials are academics, rented rooms are student_life).
- Majors: talking about the quality or content of a major is academics; talking about getting admitted to a major is administration.

# Output

Return one JSON object with the fields, in this order: `ly_do` (reason, see above), `topic`, `hard` (true or false). Write nothing outside the JSON object.

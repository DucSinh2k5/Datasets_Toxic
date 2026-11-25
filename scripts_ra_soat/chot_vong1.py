# Chốt 2 file rà soát vòng 1 (95 câu suggest + 46 dòng xem lại stance), rồi cập nhật gold có sao lưu.
import pandas as pd, sys, shutil, os
sys.path.insert(0, os.path.dirname(__file__))
V = sys.argv[1]
TAG = 'ra_soat_claude'
# ---- File 95 câu: đề xuất ban đầu D, sửa lại các câu "cần họp" sau khi rà lần 2
exec(open(os.path.join(os.path.dirname(__file__), 'ra_soat_suggest.py'), encoding='utf-8').read().split('g = pd.read_csv')[0].split('V = sys.argv[1]')[1])
FIX95 = {  # stt: (stance, topic hoặc None, lý do chốt)
 93:('none',None,'Tự đề cử mình vào đội (cầm alicu đi top), là yêu cầu cho bản thân'),
 142:('suggest',None,'Yêu cầu cụ thể gửi thầy cô xem xét lại quy định không cho kiểm tra output; đối tượng và hành động rõ từ bài đăng, khác lời than chung chung'),
 159:('none',None,'Chỉ trả lời là bổ sung sau được, không chỉ việc cụ thể'),
 167:('none',None,'Nói với người trong hội thoại về chuyện cá nhân; mục 7.3: stance không dùng cho người đối thoại'),
 193:('none','student_life',None),
 198:('oppose','facilities','Đùa hưởng ứng bình luận cha chê bộ gear của trường; ngoại lệ 7.3 thì topic theo bình luận cha, mục 5: đùa dưới dạng góp ý thì gán oppose'),
 203:('oppose',None,'Nội dung chính là chê thầy cho điểm BTL thấp; "cần giỏi DSA" là nêu yêu cầu, không phải lời khuyên'),
 226:('none',None,'Chỉ trả lời là ngủ được và giờ đóng cửa, không chỉ việc cụ thể'),
}
QUY_TAC = 'Quy tắc phân biệt: chỉ cụ thể việc cần làm hoặc nơi cần đến thì là suggest; chỉ trả lời được hay không, khi nào, bao nhiêu thì là none.'
# ---- File 46 dòng: stt: (topic, stance, emotion_1 hoặc None, lý do)
X = {
1:('unk','none',None,'Trả lời bình luận cha, không có chủ đề của trường'),
5:('unk','none',None,'Nhận đồ cho bản thân (ví dụ mục 7.3)'),
6:('unk','none',None,'Đùa với người trong hội thoại'),
7:('unk','none',None,'Chỉ bộc lộ cảm xúc (ví dụ mục 7.3)'),
12:('administration','none',None,'Nói chưa nhận được mail báo trúng tuyển, có đối tượng nên không phải unk; không có thái độ'),
13:('administration','suggest',None,'Khuyên lưu lại timeline nhập học, có hành động; topic theo bài đăng'),
15:('unk','none',None,'Đá xoáy người trong hội thoại'),
16:('unk','none',None,'Chỉ bộc lộ cảm xúc (ví dụ mục 7.3)'),
19:('facilities','support',None,'Đồng tình với bình luận cha khen thư viện số; ngoại lệ 7.3 nên topic theo bình luận cha'),
22:('unk','none',None,'Chửi người trong hội thoại'),
23:('unk','none',None,'Trêu đùa, không có chủ đề của trường'),
30:('academics','none',None,'Kể việc gặp giám thị gắt 2 lần, có đối tượng là thi cử nhưng không khen chê'),
50:('administration','none',None,'Trả lời thủ tục xét tuyển, chỉ là thông tin'),
61:('unk','none',None,'Phản ứng với người trong hội thoại'),
62:('unk','none',None,'Chê bạn mình (attack), không có thái độ với ngành hay trường'),
63:('unk','none',None,'Chửi người trong hội thoại'),
72:('unk','none',None,'Cảm ơn người trong hội thoại'),
73:('unk','none',None,'Rủ khoe (ví dụ mục 7.3)'),
81:('administration','none',None,'Bàn chuyện tuyển sinh có dễ vào không, là nhận định, không khen chê trường'),
83:('unk','none',None,'Tìm người làm vỡ gương xe (ví dụ mục 7.3); điền topic còn trống'),
85:('academics','oppose',None,'Bác lời khen giảng viên của bình luận cha (bảo người đó bịp); ngoại lệ 7.3 nên topic theo bình luận cha'),
103:('administration','none',None,'Trả lời câu hỏi xét tuyển, chỉ là thông tin'),
104:('administration','oppose',None,'Than phiền hệ thống điểm danh QR quay mãi'),
107:('academics','support',None,'Khen nhóm giải đề môn học, đồng tình với bình luận cha'),
114:('unk','none',None,'Chỉ cảm thán (ví dụ topic unk ở mục 7.2)'),
117:('academics','oppose',None,'Than lịch học quân sự vào mùa hè'),
138:('unk','none',None,'Mời nhắn tin, quảng cáo hoặc cho bản thân'),
139:('unk','none',None,'Chê bạn (attack), không có thái độ với trường'),
140:('academics','oppose','sadness','Than đề TADV khó, là phàn nàn về thi cử; điền emotion còn trống (đồng cảm, chán nản)'),
142:('academics','suggest','neutral','Yêu cầu thầy cô xem xét lại quy định; giọng lịch sự, điền emotion còn trống'),
148:('administration','oppose',None,'Mỉa mai xét tuyển PTIT; topic=unk sai vì câu nói về tuyển sinh'),
150:('unk','none',None,'Đùa trong hội thoại'),
153:('student_life','none',None,'Nhận lời đá bóng cho bản thân; có đối tượng nên không phải unk'),
160:('unk','none',None,'Chỉ cảm thán'),
165:('unk','none',None,'Chỉ cảm thán, ý không rõ'),
171:('unk','none',None,'Chuyện gia đình, cho bản thân'),
173:('student_life','support',None,'Đồng tình với bình luận cha về lợi ích của CLB; ngoại lệ 7.3'),
185:('unk','none',None,'Chỉ cảm thán'),
193:('student_life','none',None,'Thông tin về CLB, có đối tượng nên không phải unk'),
198:('facilities','oppose',None,'Đùa hưởng ứng bình luận cha chê bộ gear của trường'),
206:('unk','none',None,'Đùa trong hội thoại'),
207:('academics','suggest',None,'Chỉ chỗ mua ngân hàng câu hỏi; topic theo bài đăng (tài liệu môn học)'),
220:('student_life','oppose',None,'Chửi Agribank về tiền lì xì; mục 7.2: tiền bạc thuộc student_life'),
222:('unk','none',None,'Chê người hỏi (attack), không có thái độ với trường'),
227:('unk','none',None,'Đùa trong hội thoại'),
239:('administration','oppose',None,'Chê học phí tăng và nhà xe; nhắc nhiều chủ đề thì chọn chủ đề nhắc đầu tiên (học phí)'),
}
# ---- Ghi file 95
r = pd.read_excel(f'{V}/ra_soat_suggest_vong1.xlsx', sheet_name='ra_soat')
def f95(k):
    st, tp, md, ld = D[k]
    if k in FIX95:
        s2, t2, l2 = FIX95[k]; st = s2; tp = t2 if t2 else tp; ld = l2 or ld
    return st, tp, ld
r['nhom_chot'] = r.stt.map(lambda k: f95(k)[0])
r['nhom_chot_topic'] = r.stt.map(lambda k: f95(k)[1])
r['ly_do_chot'] = r.stt.map(lambda k: f95(k)[2])
r['nguoi_chot'] = TAG
for k in r.stt:  # 12 câu trùng phải khớp file 46
    if k in X: assert (f95(k)[0], f95(k)[1] or r.loc[r.stt==k,'topic_hien_tai'].item()) == (X[k][1], X[k][0]), k
# ---- Ghi file 46
x = pd.read_excel(f'{V}/xem_lai_stance_vong1.xlsx', sheet_name='xem_lai')
assert set(x.stt) == set(X), set(x.stt) ^ set(X)
x['topic_moi'] = x.stt.map(lambda k: X[k][0]); x['stance_moi'] = x.stt.map(lambda k: X[k][1])
x['emotion_1_moi'] = x.stt.map(lambda k: X[k][2]); x['ghi_chu_hop'] = x.stt.map(lambda k: X[k][3]); x['nguoi_chot'] = TAG
for src, df, sh in [('ra_soat_suggest_vong1', r, 'ra_soat'), ('xem_lai_stance_vong1', x, 'xem_lai')]:
    other = {k: v for k, v in pd.read_excel(f'{V}/{src}.xlsx', sheet_name=None).items() if k != sh}
    with pd.ExcelWriter(f'{V}/{src}_da_chot.xlsx') as w:
        for k, v in other.items():
            if k in ('cach_dung', 'cach_lam'):
                v = pd.concat([v, pd.DataFrame({v.columns[0]: [QUY_TAC, 'Đã chốt bởi Claude theo quy chuẩn bản 3 (24/11/2026), cột nguoi_chot = ra_soat_claude.']})])
            v.to_excel(w, sheet_name=k, index=False)
        df.to_excel(w, sheet_name=sh, index=False)
# ---- Cập nhật gold (sao lưu trước)
bak = f'{V}/gold_vong1_truoc_ra_soat.csv'
if not os.path.exists(bak): shutil.copy(f'{V}/gold_vong1.csv', bak)
g = pd.read_csv(bak)
old = g.copy()
upd = {}
for _, row in r.iterrows():
    upd.setdefault(row.comment_uid, {})['stance'] = row.nhom_chot
    if pd.notna(row.nhom_chot_topic): upd[row.comment_uid]['topic'] = row.nhom_chot_topic
for _, row in x.iterrows():
    u = upd.setdefault(row.comment_uid, {})
    u['topic'] = row.topic_moi; u['stance'] = row.stance_moi
    if pd.notna(row.emotion_1_moi): u['emotion_1'] = row.emotion_1_moi
cc = {'topic':'topic_cach_chot','stance':'stance_cach_chot','emotion_1':'emotion_cach_chot'}
for uid, u in upd.items():
    i = g.index[g.comment_uid == uid]; assert len(i) == 1, uid
    for c, v in u.items():
        if g.at[i[0], c] != v and not (pd.isna(g.at[i[0], c]) and pd.isna(v)):
            g.at[i[0], c] = v; g.at[i[0], cc[c]] = TAG
g.to_csv(f'{V}/gold_vong1.csv', index=False, encoding='utf-8-sig' if open(bak,'rb').read(3)==b'\xef\xbb\xbf' else 'utf-8')
# ---- Kiểm tra và thống kê
bad = g[(g.topic == 'unk') & ~g.stance.isin(['none', 'unk'])]
print('Vi phạm topic=unk mà stance khác none/unk:', len(bad), bad[['comment_uid','stance']].to_dict('records'))
print('Ô trống topic/stance/emotion_1:', g[['topic','stance','emotion_1']].isna().sum().to_dict())
for c in ['stance', 'topic', 'emotion_1']:
    ch = (old[c].fillna('∅') != g[c].fillna('∅'))
    print(f'\n== {c}: đổi {ch.sum()} câu')
    print(pd.DataFrame({'truoc': old[c].value_counts(), 'sau': g[c].value_counts()}).fillna(0).astype(int).to_string())
    print('Chuyển nhãn:', (old.loc[ch, c].fillna('∅') + ' → ' + g.loc[ch, c]).value_counts().to_dict())
print('\nFile 95: nhom_chot', r.nhom_chot.value_counts().to_dict(), '| khác đề xuất ban đầu:', int((r.nhom_chot != r.de_xuat_stance).sum()))
print('File 46: stance_moi', x.stance_moi.value_counts().to_dict(), '| topic_moi', x.topic_moi.value_counts().to_dict())

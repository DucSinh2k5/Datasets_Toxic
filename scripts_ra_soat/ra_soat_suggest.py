# Đề xuất rà 95 câu suggest vòng 1 theo quy chuẩn bản 3 (mục 5 và 7.3). Không sửa gold.
import pandas as pd, sys
V = sys.argv[1]
K, H = 'chắc', 'cần họp'
# stt: (stance đề xuất, topic đề xuất hoặc None, mức độ, lý do)
D = {
2:('none',None,H,'Chiêu mộ CLB của mình, coi như quảng cáo (mục 5: quảng cáo là none)'),
5:('none',None,K,'Ví dụ trong mục 7.3: nhận đồ cho bản thân'),
8:('suggest',None,K,'Chỉ cho người hỏi việc cần làm (xuống VP1C)'),
9:('suggest',None,K,'Lời khuyên có hành động cụ thể'),
13:('suggest','administration',H,'topic=unk mà stance=suggest vi phạm ràng buộc 7.3; câu khuyên lưu timeline nhập học nên topic là administration. Nếu thấy quá vụn thì đổi thành none'),
14:('suggest',None,K,'Khuyên nên có TOEIC'),
17:('suggest',None,K,'Khuyên đăng ký xét học bổng'),
23:('none',None,K,'Trêu đùa, không có đối tượng là chủ đề của trường, topic=unk'),
25:('suggest',None,K,'Khuyên nên có laptop'),
27:('suggest',None,H,'Chủ yếu là thông tin, nhưng có chỉ hành động (lên VP1C xin lùi)'),
28:('suggest',None,K,'Có lời khuyên đi học thêm để đổi điểm'),
31:('suggest',None,K,'Khuyên đăng ký nguyện vọng CLC ngay từ đầu'),
33:('none',None,K,'Chỉ cung cấp thông tin (không làm thì bị cấm thi)'),
37:('none',None,H,'Đùa lạc đề, không phải góp ý thật (SemEval-2019 loại câu đùa)'),
40:('suggest',None,K,'Góp ý cụ thể cho trang web của người khác'),
42:('suggest',None,H,'Mẹo làm bài (bỏ 1 ý), đúng là lời khuyên nhưng rất ngắn'),
43:('none',None,K,'Rủ rê, theo mục 7.3 không phải suggest'),
52:('oppose',None,H,'"Vô đạo bất lương, đề nghị tăng 4 mã đề" có giọng mỉa mai; mục 5: góp ý mỉa mai thì gán oppose'),
54:('none',None,K,'Mong muốn cho bản thân (suất miễn thi), đùa'),
58:('none',None,K,'Đùa kèm quảng bá Đội Cờ đỏ'),
59:('none',None,K,'Quảng cáo tool đăng ký học phần'),
68:('none',None,H,'Lời khuyên đùa trên bài meme, không phải góp ý thật'),
70:('suggest',None,K,'Review có lời khuyên cụ thể (ghi bài, làm giữa kỳ cẩn thận)'),
71:('suggest',None,K,'Ví dụ trong mục 7.3'),
73:('none',None,K,'Ví dụ trong mục 7.3'),
78:('oppose','administration',H,'"Cứ vào đi, chuẩn bị tiền là vừa" mỉa mai học phí'),
79:('none',None,K,'Từ chối đổi nhóm, chuyện của bản thân'),
83:('none','unk',K,'Ví dụ trong mục 7.3; topic đang trống, điền unk'),
84:('suggest',None,K,'Khuyên chọn laptop'),
89:('none',None,K,'Xin tài liệu cho bản thân'),
93:('suggest',None,H,'Đề xuất đội hình đi giải của trường; lời đề xuất thật nhưng xen tự giới thiệu'),
94:('suggest',None,K,'Chỉ việc cần làm (ra A1 điểm danh lại)'),
95:('none',None,K,'Đùa trong hội thoại, không có đối tượng'),
96:('suggest',None,K,'Khuyên thời điểm học ghép'),
98:('none',None,H,'Cung cấp thông tin (phụ phí 5k), không có hành động khuyên'),
99:('none',None,H,'Cung cấp thông tin về hạn nộp'),
100:('none',None,H,'Đòi người trong hội thoại trả mũ; mục 7.3: stance không dùng cho người đối thoại'),
101:('none',None,K,'Cung cấp thông tin'),
102:('suggest',None,K,'Khuyên chỗ tìm trọ'),
105:('none',None,K,'Rủ nói chuyện, cho bản thân'),
109:('none',None,K,'Câu hỏi'),
110:('none',None,K,'Quảng cáo khóa học TOEIC'),
111:('none',None,K,'Trả lời khách của dịch vụ quảng cáo'),
112:('suggest',None,K,'Chỉ việc cần làm (thanh toán hồ sơ)'),
115:('suggest',None,K,'Khuyên thêm nguyện vọng an toàn'),
118:('suggest',None,K,'Khuyên tranh thủ học năm nhất'),
120:('none',None,K,'Rủ rê'),
123:('none',None,H,'Trấn an, thông tin; "cứ đợi" không phải hành động cụ thể'),
124:('none',None,K,'Cung cấp thông tin'),
127:('suggest',None,K,'Khuyên chọn chứng chỉ'),
128:('none',None,H,'Trả lời số điểm, chủ yếu là thông tin'),
131:('none',None,H,'Tin tuyển dụng, coi như quảng cáo'),
135:('none',None,H,'Đùa, không phải góp ý thật'),
136:('suggest',None,K,'Khuyên chọn TOEIC'),
138:('none',None,K,'Mời nhắn tin, quảng cáo hoặc cho bản thân'),
142:('oppose',None,H,'"Mong thầy cô xem xét lại" không nêu hành động cụ thể; mục 5: mong muốn chung chung thì gán oppose'),
143:('suggest',None,K,'Mẹo học triết'),
144:('suggest',None,K,'Khuyên làm đề tài AI'),
146:('suggest',None,K,'Khuyên không cần laptop gaming'),
148:('oppose','administration',H,'"Cứ trừ PTIT ra là ổn" là chê trường khi xét tuyển; topic=unk vi phạm ràng buộc nên đổi topic'),
151:('none',None,H,'Đùa dưới dạng đề nghị nhưng không chê gì; nếu áp đúng câu chữ mục 5 thì là oppose'),
152:('none',None,K,'Rủ đi chung, đùa'),
157:('none',None,K,'Cung cấp thông tin'),
158:('none',None,K,'Quảng cáo'),
159:('suggest',None,H,'Trấn an kèm chỉ việc làm (bổ sung giấy sau)'),
163:('none',None,H,'Đùa ("h ôn đi má")'),
167:('suggest',None,H,'Khuyên người trong hội thoại; nghiêng về chuyện cá nhân, xem có tính là chủ đề student_life không'),
170:('none',None,K,'Đùa'),
171:('none',None,K,'topic=unk, chuyện gia đình'),
174:('oppose',None,H,'Nhận xét tiêu cực về môn học (khó, điểm không cao), không có lời khuyên'),
175:('suggest',None,K,'Khuyên thử nộp đợt tháng 5'),
181:('none',None,K,'Cung cấp thông tin'),
186:('none',None,K,'Cung cấp thông tin'),
187:('none',None,K,'Câu hỏi'),
191:('none',None,K,'Mong muốn cho bản thân'),
193:('none',None,K,'Cung cấp thông tin, topic=unk'),
195:('none',None,K,'Cung cấp thông tin về hậu quả'),
196:('none',None,K,'Rủ kết bạn cho bản thân'),
197:('oppose',None,K,'Mục 5: đùa dưới dạng góp ý thì gán oppose; câu chê "quá khắc nghiệt"'),
198:('none',None,H,'Đùa, topic=unk; nếu tính theo bình luận cha chê thiết bị thì có thể là oppose + facilities'),
199:('none',None,K,'Mong muốn đùa cho bản thân'),
203:('suggest',None,H,'Review chủ yếu là thông tin, có ý khuyên giỏi DSA bằng Java'),
204:('none',None,K,'Cung cấp thông tin'),
205:('none',None,K,'Nêu ý kiến, không có hành động'),
207:('suggest','academics',H,'Chỉ chỗ mua tài liệu; topic=unk vi phạm ràng buộc, đổi topic theo bài đăng (tài liệu môn học)'),
210:('support',None,H,'Đùa, khen thầy'),
211:('none',None,K,'Đùa, chuyện bản thân'),
214:('suggest',None,K,'Khuyên học TOEIC từ giờ'),
226:('suggest',None,H,'Thông tin giờ thư viện kèm "cứ vào thôi"'),
229:('none',None,K,'Chỉ bộc lộ cảm xúc'),
233:('suggest',None,K,'Khuyên tham khảo điểm chuẩn'),
234:('suggest',None,K,'Khuyên học sớm'),
235:('none',None,H,'Trấn an bằng trải nghiệm bản thân, không có hành động'),
238:('suggest',None,K,'Khuyên không phúc khảo; vừa chê vừa khuyên thì vẫn là suggest (mục 5)'),
240:('none',None,H,'Giới thiệu CLB của mình, giống #2'),
}
g = pd.read_csv(f'{V}/gold_vong1.csv')
t = pd.read_excel(f'{V}/da_chot/tong_hop_vong1_Hao_Trieu_da_chot.xlsx', sheet_name='tong_hop')
m = g.merge(t[['comment_uid','stt','ngu_canh_bai_dang','ngu_canh_comment_cha','stance_Hao','stance_Trieu']], on='comment_uid')
s = m[m.stance == 'suggest'].copy()
assert set(s.stt) == set(D), set(s.stt) ^ set(D)
s['de_xuat_stance'] = s.stt.map(lambda k: D[k][0])
s['de_xuat_topic'] = s.stt.map(lambda k: D[k][1])
s['muc_do'] = s.stt.map(lambda k: D[k][2])
s['ly_do'] = s.stt.map(lambda k: D[k][3])
s['doi'] = (s.de_xuat_stance != 'suggest') | s.de_xuat_topic.notna()
s['nhom_chot'] = ''
out = s[['stt','ngu_canh_bai_dang','ngu_canh_comment_cha','text_public','topic','stance_Hao','stance_Trieu','stance_cach_chot',
         'de_xuat_stance','de_xuat_topic','muc_do','ly_do','doi','nhom_chot','comment_uid']].rename(columns={'topic':'topic_hien_tai'})
out = out.sort_values(['doi','muc_do','stt'], ascending=[False, True, True])
huong_dan = pd.DataFrame({'Cách dùng': [
 'Rà 95 câu gold vòng 1 đang có stance = suggest, theo quy chuẩn bản 3 (mục 5 và 7.3). File gold chưa bị sửa.',
 'Tiêu chí: suggest = góp ý hoặc lời khuyên có hành động cụ thể, có lợi cho người khác hoặc nhà trường; khuyên bạn bè cũng là suggest.',
 'Không phải suggest: nhờ vả, rủ rê, yêu cầu cho bản thân; quảng cáo; chỉ cung cấp thông tin; câu hỏi (đều là none). Góp ý mỉa mai, đùa, hoặc mong muốn chung chung không có hành động thì gán oppose.',
 'Ràng buộc: topic = unk thì stance chỉ được là none hoặc unk.',
 'Cột muc_do: "chắc" = khớp ví dụ hoặc quy tắc có sẵn; "cần họp" = vùng xám, nhóm chốt.',
 'Nhóm điền nhãn cuối vào cột nhom_chot, rồi dùng để cập nhật gold_vong1.csv.',
]})
tk = out.groupby(['doi','muc_do']).size().rename('so_cau').reset_index()
tk2 = out.de_xuat_stance.value_counts().rename_axis('de_xuat_stance').rename('so_cau').reset_index()
with pd.ExcelWriter(f'{V}/ra_soat_suggest_vong1.xlsx') as w:
    huong_dan.to_excel(w, 'cach_dung', index=False)
    out.to_excel(w, 'ra_soat', index=False)
    tk.to_excel(w, 'thong_ke', index=False); tk2.to_excel(w, 'thong_ke', index=False, startrow=len(tk)+2)
print(tk.to_string()); print(tk2.to_string())
st = g.stance.copy(); st[g.comment_uid.isin(s.comment_uid)] = s.set_index('comment_uid').loc[g.comment_uid[g.comment_uid.isin(s.comment_uid)], 'de_xuat_stance'].values
print('stance gold nếu theo đề xuất:', st.value_counts().to_dict())

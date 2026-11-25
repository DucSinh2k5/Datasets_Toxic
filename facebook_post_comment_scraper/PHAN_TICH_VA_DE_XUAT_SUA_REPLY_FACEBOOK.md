# PHÂN TÍCH VÀ ĐỀ XUẤT SỬA CHỨC NĂNG XÁC ĐỊNH QUAN HỆ COMMENT – REPLY FACEBOOK

> **Phiên bản phân tích & cập nhật:** 2026-11-02  
> **Dự án:** facebook_post_comment_scraper  
> **Mục tiêu:** Xác định chính xác quan hệ cha–con giữa comment và reply, chuẩn hoá cấu trúc CSV phân cấp (`1`, `1_1`, `1_1_1`, `1_1_2`, `1_2`, `2`) kèm trường `reply_to_message` (nội dung comment/bài viết được phản hồi) phục vụ hệ thống NLP/AI

---

## 1. Tổng quan kiến trúc hiện tại

### Luồng thực thi tổng quát

```
[Facebook Group/Fanpage]
        │
        ▼
[Thu thập bài viết]
   group_post_scraper_v2.py::fetch_posts()
   fanpage_playwright_scraper.py (Playwright scroll)
   fanpage_comment_scraper.py::FacebookPageScraper.PagePostInfo()
        │
        ▼ (post_id, message, permalink, ...)
[Thu thập comment cho từng bài viết]
   comment_scraper.py::fetch_comments(feedback_id)
        │
        ▼ (comment_id, author, created_time, text, reaction_count, _feedback_id, _expansion_token)
[Thu thập reply cho từng comment]
   comment_scraper.py::fetch_replies(comment)
        │
        ▼ (reply_id, parent_comment_id, direct_parent_id, author, created_time, text, reaction_count)
[Chuyển đổi phân cấp cây hội thoại]
   comment_scraper.py::build_hierarchical_rows(post_id, post_message, comments)
        │
        ▼ (post_id, post_message, comment_id [1, 1_1, 1_1_1...], reply_to_message, message)
[Ghi ra CSV phân cấp chuẩn NLP]
   group_comment_scraper.py::save_comments_csv()
   fanpage_comment_scraper.py / fanpage_playwright_scraper.py
```

---

## 2. Cấu trúc dữ liệu CSV chuẩn hoá theo yêu cầu

Hệ thống lưu trữ dữ liệu dưới dạng CSV phẳng nhưng mã hoá toàn bộ cây hội thoại và ngữ cảnh trực tiếp với 5 trường:

### 2.1 Định nghĩa các trường trong CSV:
| Tên cột | Ý nghĩa |
|---|---|
| `post_id` | ID bài viết Facebook |
| `post_message` | Nội dung bài viết gốc |
| `comment_id` | ID phân cấp của comment/reply (`1`, `1_1`, `1_1_1`...) |
| `reply_to_message` | **Nội dung mà nó phản hồi trực tiếp**: <br>- Nếu là comment gốc (1, 2...): là **nội dung bài viết** (`post_message`).<br>- Nếu là reply (1_1, 1_1_1...): là **nội dung comment/reply cha** mà nó phản hồi. |
| `message` | Nội dung của comment/reply hiện tại |

### 2.2 Quy tắc đánh số phân cấp (`comment_id` & `reply_to_message`):
- `1`: Comment gốc thứ nhất của bài viết $	o$ `reply_to_message` = nội dung bài viết.
- `1_1`: Reply thứ nhất của comment 1 $	o$ `reply_to_message` = nội dung comment 1.
- `1_1_1`: Reply thứ nhất của comment 1_1 $	o$ `reply_to_message` = nội dung comment 1_1.
- `1_1_2`: Reply thứ hai của comment 1_1 $	o$ `reply_to_message` = nội dung comment 1_1.
- `1_2`: Reply thứ hai của comment 1 $	o$ `reply_to_message` = nội dung comment 1.
- `2`: Comment gốc thứ hai của bài viết $	o$ `reply_to_message` = nội dung bài viết.

### 2.3 Ví dụ minh hoạ dữ liệu CSV:
```csv
post_id,post_message,comment_id,reply_to_message,message
p001,"Mọi người nghĩ sao về vấn đề này?",1,"Mọi người nghĩ sao về vấn đề này?","Tôi muốn hỏi mọi người"
p001,"Mọi người nghĩ sao về vấn đề này?",1_1,"Tôi muốn hỏi mọi người","Tôi đồng ý"
p001,"Mọi người nghĩ sao về vấn đề này?",1_1_1,"Tôi đồng ý","Tại sao bạn đồng ý?"
p001,"Mọi người nghĩ sao về vấn đề này?",1_1_2,"Tôi đồng ý","Tôi cũng đồng ý"
p001,"Mọi người nghĩ sao về vấn đề này?",1_2,"Tôi muốn hỏi mọi người","Tôi không đồng ý"
p001,"Mọi người nghĩ sao về vấn đề này?",2,"Mọi người nghĩ sao về vấn đề này?","Tôi có ý kiến khác"
```

---

## 3. Các thay đổi đã thực hiện trong Source Code

| File | Hàm / Vị trí | Nội dung thay đổi |
|---|---|---|
| `comment_scraper.py` | `fetch_comments()` | Khôi phục trích xuất `comment_id`, `author`, `created_time` |
| `comment_scraper.py` | `fetch_replies()` | Bổ sung `parent_comment_id`, `direct_parent_id`, `reply_id` |
| `comment_scraper.py` | `build_hierarchical_rows()` | Tự động sinh `comment_id`, gán `reply_to_message` bằng `post_message` cho comment gốc và nội dung comment cha cho replies |
| `group_comment_scraper.py` | `save_comments_csv()` | Cập nhật header CSV gồm đúng 5 trường: `post_id`, `post_message`, `comment_id`, `reply_to_message`, `message` |
| `fanpage_comment_scraper.py` | Vòng lặp ghi CSV | Đồng bộ cấu trúc 5 trường phân cấp |
| `fanpage_playwright_scraper.py` | Vòng lặp ghi CSV | Đồng bộ cấu trúc 5 trường phân cấp |

---

## 4. Lợi ích vượt trội cho bài toán NLP / AI

Mỗi dòng trong file CSV tạo thành một cặp hội thoại hoàn chỉnh `(reply_to_message -> message)`:
1. **Comment gốc**: Bài viết $	o$ Bình luận đầu tiên.
2. **Reply**: Bình luận cha $	o$ Bình luận con.
3. **Reply lồng nhau**: Bình luận trước $	o$ Bình luận phản biện tiếp theo.

Mô hình NLP có thể phân tích sentiment hoặc fine-tune LLM trực tiếp theo từng cặp ngữ cảnh mà không cần join bảng hoặc truy vết ngược dòng.

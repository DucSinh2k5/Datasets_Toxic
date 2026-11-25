import os
import sys
import time
import base64
import csv
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

# Nhúng đường dẫn chứa tool lấy comment cũ của bạn vào
sys.path.append(r"C:\Users\DELL\OneDrive\Desktop\Nam 4\Ki 1\Phan tich va khai pha DLVB\Baitap\Chuong3\BTL\facebook_post_comment_scraper\facebook_post_comment_scraper")
import comment_scraper

# Sửa lỗi hiển thị tiếng Việt trên Windows
sys.stdout.reconfigure(encoding='utf-8')

def parse_cookies_for_playwright(cookie_string):
    cookies = []
    if not cookie_string: return cookies
    for item in cookie_string.split(';'):
        if '=' in item:
            k, v = item.strip().split('=', 1)
            cookies.append({
                "name": k,
                "value": v,
                "domain": ".facebook.com",
                "path": "/"
            })
    return cookies

def parse_cookies_for_requests(cookie_string):
    cookies = {}
    if not cookie_string: return cookies
    for item in cookie_string.split(';'):
        if '=' in item:
            k, v = item.strip().split('=', 1)
            cookies[k] = v
    return cookies

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Scrape Fanpage with Playwright and GraphQL")
    parser.add_argument("--page-id", required=True, help="ID or username of the Fanpage")
    parser.add_argument("--cookies", required=True, help="Facebook cookie string")
    parser.add_argument("--fb-dtsg", required=True, help="Facebook fb_dtsg token")
    parser.add_argument("--scrolls", type=int, default=5, help="Number of times to scroll the page")
    args = parser.parse_args()
    
    cookie_str = args.cookies
    dtsg = args.fb_dtsg
    page_id = args.page_id
    scroll_times = args.scrolls
    
    pw_cookies = parse_cookies_for_playwright(cookie_str)
    req_cookies = parse_cookies_for_requests(cookie_str)
    comment_scraper.FB_DTSG = dtsg
    
    # Set để lưu trữ các ID bài viết duy nhất (không bị trùng lặp)
    post_ids = set()
    
    print("Khởi động trình duyệt ảo Playwright để cuộn trang...")
    with sync_playwright() as p:
        # headless=False nếu bạn muốn nhìn thấy trình duyệt Chrome tự mở lên và tự cuộn
        # headless=True nếu bạn muốn nó chạy ngầm
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        context.add_cookies(pw_cookies)
        page = context.new_page()
        
        print(f"Đang truy cập Fanpage: {page_id}...")
        page.goto(f"https://www.facebook.com/{page_id}")
        page.wait_for_timeout(5000)
        
        print(f"Đang cuộn chuột để tải thêm các bài viết cũ (cho đến khi hết bài)...")
        last_height = page.evaluate("document.body.scrollHeight")
        consecutive_no_new = 0
        total_posts_found = 0
        
        while True:
            # Cuộn xuống cuối trang
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(4000) # Đợi 4s cho bài viết mới load ra
            
            # Tính lại chiều cao trang
            new_height = page.evaluate("document.body.scrollHeight")
            
            # Lấy tất cả đường link trên màn hình hiện tại
            links = page.evaluate("() => Array.from(document.querySelectorAll('a')).map(a => a.href)")
            current_count = len(post_ids)
            for link in links:
                import re
                match = re.search(r'/posts/(\d+)', link)
                if match: post_ids.add(match.group(1))
                match2 = re.search(r'story_fbid=(\d+)', link)
                if match2: post_ids.add(match2.group(1))
                match3 = re.search(r'fbid=(\d+)', link)
                if match3: post_ids.add(match3.group(1))
                match4 = re.search(r'pfbid[a-zA-Z0-9]+', link)
                if match4: post_ids.add(match4.group(0))
            
            if len(post_ids) > current_count:
                print(f" -> Đã quét được {len(post_ids)} bài viết...")
                consecutive_no_new = 0
            else:
                consecutive_no_new += 1
                
            # Nếu chiều cao không đổi và không có bài viết mới trong 3 lần cuộn liên tiếp thì dừng
            if new_height == last_height and consecutive_no_new >= 3:
                print(" Đã cuộn đến cuối cùng (không tải thêm được bài mới). Dừng cuộn.")
                break
                
            last_height = new_height
            
        browser.close()
        
    post_ids = list(post_ids)
    print(f"\n✅ Đã cuộn xong! Tìm thấy {len(post_ids)} bài viết!")
    
    if not post_ids:
        print("Không tìm thấy bài viết nào. Bạn hãy kiểm tra lại Cookie xem có bị hết hạn không.")
        return
        
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    csv_file = output_dir / f"{page_id}_all_comments.csv"
    
    fieldnames = [
        "post_id", "post_message", "comment_id", "reply_to_message", "message"
    ]
    file_exists = csv_file.exists()
    
    total_saved = 0
    with csv_file.open("a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
            
        print("\nBắt đầu dùng GraphQL (đã có sẵn của bạn) để cào comments từ các bài viết này...\n")
        for idx, pid in enumerate(post_ids, 1):
            print(f"[{idx}/{len(post_ids)}] Đang cào comments bài viết: {pid}")
            feedback_id = base64.b64encode(f"feedback:{pid}".encode()).decode()
            
            try:
                comments, _ = comment_scraper.fetch_comments(feedback_id, cookies=req_cookies)
            except Exception as e:
                print(f"  ❌ Lỗi lấy comments: {e}")
                continue
                
            for comment in comments:
                try:
                    comment["replies"] = comment_scraper.fetch_replies(comment, cookies=req_cookies)
                except Exception:
                    comment["replies"] = []

            rows = comment_scraper.build_hierarchical_rows(pid, "", comments)
            for row in rows:
                writer.writerow(row)
                total_saved += 1
            print(f"  ✅ Lưu thành công!")
            
    print(f"\n🎉 Hoàn thành! Đã cào và lưu tổng cộng {total_saved} comments vào:")
    print(f"   {csv_file.absolute()}")

if __name__ == '__main__':
    main()

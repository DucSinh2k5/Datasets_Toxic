import argparse
import base64
import csv
import sys
import os
from pathlib import Path

# Fix encoding issues in Windows console
sys.stdout.reconfigure(encoding='utf-8')

# Import existing scrapers
PROJECT_DIR = Path(__file__).resolve().parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

import comment_scraper

# Import page scraper
PAGE_SCRAPER_DIR = PROJECT_DIR.parent.parent / "facebook-pages-scraper"
if str(PAGE_SCRAPER_DIR) not in sys.path:
    sys.path.insert(0, str(PAGE_SCRAPER_DIR))

from facebook_page_scraper import FacebookPageScraper

def parse_cookies(cookie_string):
    cookies = {}
    if not cookie_string:
        return cookies
    for item in cookie_string.split(";"):
        item = item.strip()
        if "=" in item:
            key, value = item.split("=", 1)
            cookies[key.strip()] = value.strip()
    return cookies

def main():
    parser = argparse.ArgumentParser(description="Fetch Fanpage posts and comments.")
    parser.add_argument("--page-id", required=True, help="Facebook Fanpage ID or username")
    parser.add_argument("--cookies", default="", help="Facebook cookie string")
    parser.add_argument("--fb-dtsg", default="", help="Optional fb_dtsg token")
    parser.add_argument("--output", default=str(Path(__file__).parent / "output"), help="Output directory")
    args = parser.parse_args()

    # Fallback to hardcoded cookies if not provided
    default_cookie = ''
    default_dtsg = ''

    raw_cookie = args.cookies if args.cookies else os.environ.get('FB_COOKIE', default_cookie)
    raw_dtsg = args.fb_dtsg if args.fb_dtsg else os.environ.get('FB_DTSG', default_dtsg)

    cookies = parse_cookies(raw_cookie)
    comment_scraper.FB_DTSG = raw_dtsg

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_file = output_dir / f"{args.page_id}_comments.csv"

    print(f"Bắt đầu lấy dữ liệu từ Fanpage: {args.page_id}...")
    
    # 1. Fetch posts using the working PagePostInfo scraper
    posts = FacebookPageScraper.PagePostInfo(args.page_id)
    if not posts:
        print("Không tìm thấy bài viết nào trên trang này. Trang có thể trống hoặc bị giới hạn.")
        return
        
    print(f"Tìm thấy {len(posts)} bài viết gần nhất. Bắt đầu lấy comments...\n")

    # 2. Setup CSV (4 hierarchical columns)
    fieldnames = [
        "post_id", "post_message", "comment_id", "reply_to_message", "message"
    ]
    file_exists = csv_file.exists()
    
    total_saved = 0
    with csv_file.open("a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()

        for idx, post in enumerate(posts, 1):
            post_id = post.get('id')
            if not post_id:
                continue
                
            print(f"[{idx}/{len(posts)}] Đang lấy comments cho bài viết: {post_id}")
            
            feedback_id = base64.b64encode(f"feedback:{post_id}".encode()).decode()
            
            try:
                comments, _ = comment_scraper.fetch_comments(feedback_id, cookies=cookies)
            except Exception as e:
                print(f"  ❌ Lỗi khi lấy comments bài {post_id}: {e}")
                continue

            for comment in comments:
                try:
                    comment["replies"] = comment_scraper.fetch_replies(comment, cookies=cookies)
                except Exception as e:
                    print(f"  ⚠️ Lỗi khi lấy reply: {e}")
                    comment["replies"] = []

            post_message = post.get("text", "")
            rows = comment_scraper.build_hierarchical_rows(post_id, post_message, comments)
            for row in rows:
                writer.writerow(row)
                total_saved += 1

            print(f"  ✅ Đã lưu comments của bài {post_id}.")

    print(f"\n🎉 Hoàn thành! Đã lưu tổng cộng {total_saved} comments & replies vào file:")
    print(f"   {csv_file}")

if __name__ == "__main__":
    main()

"""Fetch posts and comments from a Facebook group.

This entry point reuses the existing group-post and comment scrapers from
facebook_post_comment_scraper while keeping output in this folder.
"""

import argparse
import base64
import csv
import re
import sys
import requests
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

import comment_scraper
import group_post_scraper_v2 as group_scraper


def parse_cookies(cookie_string):
    """Convert a browser cookie string into the dict expected by requests."""
    cookies = {}
    for item in cookie_string.split(";"):
        item = item.strip()
        if "=" in item:
            key, value = item.split("=", 1)
            cookies[key.strip()] = value.strip()
    return cookies


def configure_scrapers(group_id, cookies, fb_dtsg):
    """Apply group and authentication settings to the existing modules."""
    group_scraper.GROUP_ID = group_id
    group_scraper.GROUP_NAME = None
    group_scraper.HEADERS["referer"] = f"https://www.facebook.com/groups/{group_id}/"
    group_scraper.COOKIES = cookies
    group_scraper.FB_DTSG = fb_dtsg
    comment_scraper.FB_DTSG = fb_dtsg


def group_id_from_line(line, cookies):
    """Read either a numeric group ID or a Facebook group URL."""
    value = line.strip()
    if not value or value.startswith("#"):
        return None
    if value.isdigit():
        return value
    match = re.search(r"/groups/(\d+)(?:[/\?]|$)", value)
    if match:
        return match.group(1)
    match = re.search(r"(?:group_id|gid)=(\d+)", value)
    if match:
        return match.group(1)

    try:
        response = requests.get(
            value,
            headers={"user-agent": "Mozilla/5.0"},
            cookies=cookies,
            proxies=group_scraper.PROXIES,
            timeout=20,
        )
        for pattern in (
            r"fb://group/(\d+)",
            r'"group_id":"(\d+)"',
            r'"groupID":"(\d+)"',
        ):
            match = re.search(pattern, response.text)
            if match:
                return match.group(1)
    except requests.RequestException as error:
        print(f"Could not resolve group URL {value}: {error}")
    return None


def load_group_ids(links_file, cookies):
    """Load group IDs from a text file containing one URL or ID per line."""
    group_ids = []
    unresolved = []
    for line in links_file.read_text(encoding="utf-8-sig").splitlines():
        group_id = group_id_from_line(line, cookies)
        if group_id and group_id not in group_ids:
            group_ids.append(group_id)
        elif line.strip() and not line.lstrip().startswith("#") and not group_id:
            unresolved.append(line.strip())
    print(f"Resolved {len(group_ids)} group(s) from {links_file}")
    if unresolved:
        print(f"Could not resolve {len(unresolved)} group link(s):")
        for link in unresolved:
            print(f"  - {link}")
    return group_ids


def fetch_comments_for_post(post_id, cookies=None, max_workers=5):
    """Fetch comments and nested replies for one post in parallel (fast & safe)."""
    feedback_id = base64.b64encode(f"feedback:{post_id}".encode()).decode()
    comments, post_info = comment_scraper.fetch_comments(
        feedback_id,
        cookies=cookies,
    )
    if hasattr(comment_scraper, "fetch_all_replies_parallel"):
        comment_scraper.fetch_all_replies_parallel(comments, cookies=cookies, max_workers=max_workers)
    else:
        for comment in comments:
            try:
                comment["replies"] = comment_scraper.fetch_replies(comment, cookies=cookies)
            except Exception as error:
                comment["replies"] = []
    for comment in comments:
        for key in list(comment):
            if key.startswith("_"):
                del comment[key]
    return comments, post_info


def save_comments_csv(output_file, group_id, post, comments):
    """Append post comments and replies to CSV with hierarchical columns:
    post_id, post_message, comment_id, reply_to_message, message
    """
    output_file.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "post_id",
        "post_message",
        "comment_id",
        "reply_to_message",
        "message",
    ]
    file_exists = output_file.exists()

    with output_file.open("a", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()

        post_id = post.get("post_id", "")
        post_message = post.get("message", "")
        rows = comment_scraper.build_hierarchical_rows(post_id, post_message, comments)
        for row in rows:
            writer.writerow({
                "post_id": row["post_id"],
                "post_message": row["post_message"],
                "comment_id": row["comment_id"],
                "reply_to_message": row["reply_to_message"],
                "message": row["message"],
            })


def main():
    parser = argparse.ArgumentParser(
        description="Fetch Facebook group posts with comments and replies."
    )
    parser.add_argument("--group-id", help="Facebook group ID (overrides --links-file)")
    parser.add_argument(
        "--links-file",
        default=str(Path(__file__).parent / "group_links.txt"),
        help="Text file containing one Facebook group URL or ID per line",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Maximum posts to fetch; 0 fetches all available posts",
    )
    parser.add_argument(
        "--min-comments",
        type=int,
        default=0,
        help="Only include posts with at least this many comments",
    )
    parser.add_argument(
        "--cookies",
        default="",
        help="Facebook cookie string for groups requiring login",
    )
    parser.add_argument("--fb-dtsg", default="", help="Optional fb_dtsg token")
    parser.add_argument(
        "--output",
        default=str(Path(__file__).parent / "output"),
        help="Output directory",
    )
    parser.add_argument(
        "--reset-csv",
        action="store_true",
        help="Delete the existing comments.csv before scraping",
    )
    args = parser.parse_args()

    cookies = parse_cookies(args.cookies)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_file = output_dir / "comments.csv"
    if args.reset_csv and csv_file.exists():
        csv_file.unlink()
        print(f"Reset CSV: {csv_file}")

    if args.group_id:
        group_ids = [args.group_id]
    else:
        links_file = Path(args.links_file)
        if not links_file.exists():
            raise FileNotFoundError(f"Links file not found: {links_file}")
        group_ids = load_group_ids(links_file, cookies)

    if not group_ids:
        raise ValueError("No valid Facebook group URL or ID was found")

    saved = 0
    total_comments = 0
    total_replies = 0

    def process_post_batch(group_id, batch_posts):
        nonlocal saved, total_comments, total_replies

        for index, post in enumerate(batch_posts, start=1):
            post_id = post.get("post_id")
            if not post_id:
                print(f"Skipping post without ID")
                continue

            print(f"Fetching comments for post {post_id}...")
            try:
                comments, _ = fetch_comments_for_post(post_id, cookies=cookies)
            except Exception as error:
                print(f"Could not fetch comments for post {post_id}: {error}")
                continue

            save_comments_csv(csv_file, group_id, post, comments)
            saved += 1
            reply_count = sum(len(comment.get("replies", [])) for comment in comments)
            total_comments += len(comments)
            total_replies += reply_count
            print(f"Saved {len(comments)} comments and {reply_count} replies to CSV")

    for group_id in group_ids:
        configure_scrapers(group_id, cookies, args.fb_dtsg)
        print(f"Fetching up to {args.limit} posts from group {group_id}...")
        try:
            group_scraper.fetch_posts(
                limit=args.limit,
                min_comments=args.min_comments,
                batch_size=10,
                on_batch_complete=lambda batch, _total, _limit, current_group=group_id:
                    process_post_batch(current_group, batch),
            )
        except Exception as error:
            print(f"Could not fetch posts from group {group_id}: {error}")
            continue

    print(
        f"Finished. Processed {saved} post(s) from {len(group_ids)} group(s); "
        f"saved {total_comments} comments and {total_replies} replies in {output_dir}"
    )
    print(f"CSV comments file: {csv_file}")


if __name__ == "__main__":
    main()

"""Fetch posts and comments from a Facebook group.

This entry point reuses the existing group-post and comment scrapers from
facebook_post_comment_scraper while keeping output in this folder.
"""

import argparse
from dotenv import load_dotenv
load_dotenv()
import asyncio
import base64
import csv
import json
import os
import re
import sys
import requests
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace


PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))
WORKSPACE_DIR = Path(__file__).resolve().parents[2]
if str(WORKSPACE_DIR) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_DIR))

import comment_scraper
import group_post_scraper_v2 as group_scraper


def parse_cookies(cookie_string):
    """Convert a browser cookie string into the dict expected by requests."""
    cookies = {}
    for item in (cookie_string or "").split(";"):
        item = item.strip()
        if "=" in item:
            key, value = item.split("=", 1)
            cookies[key.strip()] = value.strip()
    return cookies


def validate_auth_inputs(raw_cookie_string, cookies, fb_dtsg):
    """Fail early when the Facebook auth values were not passed correctly."""
    if not raw_cookie_string:
        raise ValueError(
            "Missing cookies. Set $env:FB_COOKIE or pass --cookies \"<cookie string>\"."
        )

    missing_cookie_keys = [key for key in ("c_user", "xs") if not cookies.get(key)]
    if missing_cookie_keys:
        raise ValueError(
            "Cookie string is missing required Facebook cookie(s): "
            + ", ".join(missing_cookie_keys)
            + ". Copy the full Cookie request header after logging in."
        )

    if not fb_dtsg:
        raise ValueError(
            "Missing fb_dtsg. Set $env:FB_DTSG or pass --fb-dtsg \"<token>\"."
        )

    print(
        "[Auth] Cookie OK: "
        f"c_user={cookies.get('c_user')}, cookies={len(cookies)}, "
        f"fb_dtsg length={len(fb_dtsg)}"
    )


def configure_scrapers(group_id, cookies, fb_dtsg, output_dir=None):
    """Apply group and authentication settings to the existing modules."""
    group_scraper.GROUP_ID = group_id
    group_scraper.GROUP_NAME = None
    group_scraper.HEADERS["referer"] = f"https://www.facebook.com/groups/{group_id}/"
    group_scraper.COOKIES = cookies
    group_scraper.FB_DTSG = fb_dtsg
    if output_dir is not None:
        group_scraper.DEBUG_OUTPUT_DIR = str(Path(output_dir) / "debug")
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


def load_link_values(links_file):
    """Load non-empty, non-comment links from a text file."""
    return [
        line.strip()
        for line in links_file.read_text(encoding="utf-8-sig").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def is_facebook_group_link(value):
    return bool(re.search(r"facebook\.com/groups/", value, re.IGNORECASE))


def is_facebook_page_link(value):
    if not re.search(r"facebook\.com/", value, re.IGNORECASE):
        return False
    return not is_facebook_group_link(value)


def json_path_for_csv(csv_file):
    suffix = "".join(csv_file.suffixes)
    if suffix:
        return Path(str(csv_file)[: -len(csv_file.suffix)] + ".json")
    return csv_file.with_name(csv_file.name + ".json")


def run_page_crawler(page_urls, raw_cookie_string, output_dir, csv_file, reset_csv):
    """Route Facebook page URLs to the Playwright page crawler."""
    import facebook_comment_crawler as browser_crawler

    json_file = json_path_for_csv(csv_file)
    if reset_csv and json_file.exists():
        json_file.unlink()
        print(f"Reset JSON: {json_file}")

    browser_args = SimpleNamespace(
        url=list(page_urls),
        urls_file=None,
        mode="page",
        csv_file=str(csv_file),
        json_file=str(json_file),
        resume_file=None,
        resume_post_id=None,
        no_resume=True,
        max_group_posts=0,
        max_group_scrolls=0,
        group_idle_rounds=5,
        no_sort_newest=True,
        profile="./facebook_profile",
        cookies=None,
        cookie_string=raw_cookie_string,
        login=False,
        headless=False,
        max_scrolls=30,
        max_clicks=250,
        idle_rounds=3,
        min_delay=1.0,
        max_delay=2.2,
        output_dir=str(output_dir),
        debug=True,
    )
    print("[Page] Phat hien URL page, chuyen sang Playwright page crawler.")
    asyncio.run(browser_crawler.main(browser_args))


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def load_resume_state(resume_file):
    """Load resume metadata, returning an empty structure when unavailable."""
    if not resume_file.exists():
        return {"version": 1, "groups": {}}

    try:
        state = json.loads(resume_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as error:
        print(f"[Resume] Could not read {resume_file}: {error}. Starting with empty state.")
        return {"version": 1, "groups": {}}

    if not isinstance(state, dict):
        return {"version": 1, "groups": {}}
    state.setdefault("version", 1)
    state.setdefault("groups", {})
    return state


def save_resume_state(resume_file, state):
    """Persist resume metadata after each processed post/page."""
    state["updated_at_utc"] = utc_now()
    resume_file.parent.mkdir(parents=True, exist_ok=True)
    tmp_file = resume_file.with_suffix(resume_file.suffix + ".tmp")
    payload = json.dumps(state, ensure_ascii=False, indent=2)
    tmp_file.write_text(payload, encoding="utf-8")
    try:
        tmp_file.replace(resume_file)
    except PermissionError:
        resume_file.write_text(payload, encoding="utf-8")
        try:
            tmp_file.unlink()
        except OSError:
            pass


def load_processed_post_ids_from_csv(csv_file):
    """Return set of processed post IDs from an existing CSV."""
    processed = set()
    if not csv_file.exists():
        return processed

    try:
        with csv_file.open("r", newline="", encoding="utf-8-sig") as csv_handle:
            reader = csv.DictReader(csv_handle)
            for row in reader:
                post_id = (row.get("post_id") or "").strip()
                if post_id:
                    processed.add(post_id)
    except OSError as error:
        print(f"[Resume] Could not read existing CSV for duplicate check: {error}")
    return processed


def fetch_comments_for_post(post_id, cookies=None, max_workers=5):
    """Fetch comments and nested replies for one post in parallel (fast & safe)."""
    feedback_id = base64.b64encode(f"feedback:{post_id}".encode()).decode()
    comments, post_info = comment_scraper.fetch_comments(
        feedback_id,
        cookies=cookies,
    )
    # Tải đồng thời replies bằng ThreadPoolExecutor giúp nhanh gấp 3x - 5x
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
        default=os.getenv("FB_COOKIE", ""),
        help="Facebook cookie string for groups requiring login",
    )
    parser.add_argument(
        "--fb-dtsg",
        default=os.getenv("FB_DTSG", ""),
        help="Facebook fb_dtsg token. Defaults to the FB_DTSG environment variable.",
    )
    parser.add_argument(
        "--output",
        default=str(Path(__file__).parent / "output"),
        help="Output directory",
    )
    parser.add_argument(
        "--csv-file",
        default="",
        help="CSV output file path. If omitted, comments.csv is saved inside --output.",
    )
    parser.add_argument(
        "--resume-file",
        default="",
        help="Resume JSON file path. If omitted, group_comment_resume.json is saved inside --output.",
    )
    parser.add_argument(
        "--reset-resume",
        action="store_true",
        help="Delete the existing resume file before scraping from the beginning.",
    )
    parser.add_argument(
        "--reset-csv",
        action="store_true",
        help="Delete the existing CSV file before scraping",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=5,
        help="Number of parallel threads for fetching replies (default: 5)",
    )
    args = parser.parse_args()

    raw_cookie_string = (args.cookies or "").strip()
    fb_dtsg = (args.fb_dtsg or "").strip()
    cookies = parse_cookies(raw_cookie_string)
    validate_auth_inputs(raw_cookie_string, cookies, fb_dtsg)

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_file = Path(args.csv_file) if args.csv_file else output_dir / "comments.csv"
    if not csv_file.is_absolute():
        csv_file = Path.cwd() / csv_file
    csv_file.parent.mkdir(parents=True, exist_ok=True)

    resume_file = Path(args.resume_file) if args.resume_file else output_dir / "group_comment_resume.json"
    if not resume_file.is_absolute():
        resume_file = Path.cwd() / resume_file
    resume_file.parent.mkdir(parents=True, exist_ok=True)

    if args.reset_csv and csv_file.exists():
        csv_file.unlink()
        print(f"Reset CSV: {csv_file}")
    if args.reset_resume and resume_file.exists():
        resume_file.unlink()
        print(f"Reset resume: {resume_file}")

    resume_state = load_resume_state(resume_file)
    resume_state["csv_file"] = str(csv_file)
    csv_processed_ids = load_processed_post_ids_from_csv(csv_file)

    if args.group_id:
        group_ids = [args.group_id]
        page_urls = []
    else:
        links_file = Path(args.links_file)
        if not links_file.exists():
            raise FileNotFoundError(f"Links file not found: {links_file}")
        link_values = load_link_values(links_file)
        page_urls = [value for value in link_values if is_facebook_page_link(value)]
        group_ids = load_group_ids(links_file, cookies)

    if not group_ids:
        if page_urls:
            run_page_crawler(
                page_urls=page_urls,
                raw_cookie_string=raw_cookie_string,
                output_dir=output_dir,
                csv_file=csv_file,
                reset_csv=args.reset_csv,
            )
            return
        raise ValueError("No valid Facebook group URL or ID was found")

    if page_urls:
        print(f"[!] Bo qua {len(page_urls)} page URL trong group mode. Neu muon crawl page, de file links chi co page URL.")

    saved = 0
    total_comments = 0
    total_replies = 0

    def make_process_post_batch(group_id, group_state, processed_post_ids):
        def process_post_batch(batch_posts):
            nonlocal saved, total_comments, total_replies

            for post in batch_posts:
                post_id = str(post.get("post_id") or "")
                if not post_id:
                    print("Skipping post without ID")
                    continue
                if post_id in processed_post_ids:
                    print(f"[Resume] Skipping already processed post {post_id}")
                    continue

                print(f"Fetching comments for post {post_id}...")
                try:
                    comments, _ = fetch_comments_for_post(post_id, cookies=cookies, max_workers=args.workers)
                except Exception as error:
                    print(f"Could not fetch comments for post {post_id}: {error}")
                    continue

                save_comments_csv(csv_file, group_id, post, comments)
                processed_post_ids.add(post_id)
                group_state["processed_post_ids"] = sorted(processed_post_ids)
                group_state["processed_count"] = len(processed_post_ids)
                group_state["last_post_id"] = post_id
                group_state["last_post_permalink"] = post.get("permalink", "")
                group_state["status"] = "running"
                save_resume_state(resume_file, resume_state)

                saved += 1
                reply_count = sum(len(comment.get("replies", [])) for comment in comments)
                total_comments += len(comments)
                total_replies += reply_count
                print(f"Saved {len(comments)} comments and {reply_count} replies to CSV")

        return process_post_batch

    def make_page_complete(group_state):
        def on_page_complete(page_num, current_cursor, next_cursor, posts_found, total_new_posts, finished):
            group_state["last_completed_page"] = page_num
            group_state["cursor"] = next_cursor
            group_state["page_num"] = page_num + 1 if next_cursor else page_num
            group_state["last_page_posts_found"] = posts_found
            group_state["last_run_new_posts"] = total_new_posts
            group_state["status"] = "complete" if finished else "running"
            save_resume_state(resume_file, resume_state)

            if next_cursor:
                print(f"[Resume] Saved cursor after page {page_num}; next page={page_num + 1}")
            else:
                print(f"[Resume] Saved end state after page {page_num}")

        return on_page_complete
 
    for group_id in group_ids:
        group_state = resume_state.setdefault("groups", {}).setdefault(group_id, {})
        processed_post_ids = set(group_state.get("processed_post_ids") or [])
        if isinstance(csv_processed_ids, set):
            processed_post_ids.update(csv_processed_ids)
        elif isinstance(csv_processed_ids, dict):
            processed_post_ids.update(csv_processed_ids.get(group_id, set()))
            processed_post_ids.update(csv_processed_ids.get("", set()))
        group_state["processed_post_ids"] = sorted(processed_post_ids)
        group_state["processed_count"] = len(processed_post_ids)
        group_state["status"] = "running"
        save_resume_state(resume_file, resume_state)

        start_cursor = group_state.get("cursor")
        start_page = group_state.get("page_num") or 1
        if start_cursor:
            print(f"[Resume] Resuming group {group_id} from saved cursor at page {start_page}")
        if processed_post_ids:
            print(f"[Resume] Will skip {len(processed_post_ids)} already processed post(s)")

        configure_scrapers(group_id, cookies, fb_dtsg, output_dir)
        limit_label = "all available" if args.limit == 0 else str(args.limit)
        print(f"Fetching {limit_label} posts from group {group_id}...")
        try:
            group_scraper.fetch_posts(
                limit=args.limit,
                min_comments=args.min_comments,
                batch_size=1,
                on_batch_complete=lambda batch, _total, _limit, processor=make_process_post_batch(
                    group_id,
                    group_state,
                    processed_post_ids,
                ): processor(batch),
                start_cursor=start_cursor,
                start_page=start_page,
                on_page_complete=make_page_complete(group_state),
                skip_post_ids=processed_post_ids,
            )
        except KeyboardInterrupt:
            group_state["status"] = "stopped"
            group_state["stopped_at_utc"] = utc_now()
            save_resume_state(resume_file, resume_state)
            print("\n[Resume] Da dung bang Ctrl+C. Lan sau chay lai cung lenh de tiep tuc.")
            print(f"[Resume] Resume file: {resume_file}")
            break
        except Exception as error:
            group_state["status"] = "error"
            group_state["last_error"] = str(error)
            save_resume_state(resume_file, resume_state)
            print(f"Could not fetch posts from group {group_id}: {error}")
            continue

    print(
        f"Finished. Processed {saved} post(s) from {len(group_ids)} group(s); "
        f"saved {total_comments} comments and {total_replies} replies in {output_dir}"
    )
    print(f"CSV comments file: {csv_file}")


if __name__ == "__main__":
    main()

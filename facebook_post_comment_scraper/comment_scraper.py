import csv
import requests
import json
import time
import os
import sys
from dotenv import load_dotenv

# Fix encoding issues in Windows console
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Load environment variables from .env file
load_dotenv()

GRAPHQL = "https://www.facebook.com/api/graphql/"

# Base headers for all requests
BASE_HEADERS = {
    "user-agent": "Mozilla/5.0",
    "content-type": "application/x-www-form-urlencoded"
}

# Get proxy configuration
PROXY = os.getenv('PROXY')
PROXIES = {'http': PROXY, 'https': PROXY} if PROXY else None

# FB_DTSG token (set by UI when provided)
FB_DTSG = ""

if PROXY:
    print(f"Using proxy: {PROXY}")

# ========= RETRY HELPER =========
def retry_request(url, headers, data, proxies, cookies=None, max_retries=5):
    """Make a POST request with retry logic"""
    global PROXIES
    from proxy_utils import rotate_static_proxy, is_proxy_infra_error, is_ip_blocked

    for attempt in range(1, max_retries + 1):
        try:
            r = requests.post(url, headers=headers, data=data, proxies=proxies, cookies=cookies, timeout=30)
            if r.status_code == 200:
                return r
            if is_proxy_infra_error(status_code=r.status_code):
                print(f"   Attempt {attempt}/{max_retries}: Proxy auth failed (HTTP {r.status_code}) — rotating static proxy...")
                new_p = rotate_static_proxy()
                if new_p:
                    proxies = new_p
                    PROXIES = new_p
            elif is_ip_blocked(status_code=r.status_code, response_text=r.text):
                print(f"   Attempt {attempt}/{max_retries}: Facebook blocked this IP (HTTP {r.status_code}) — rotating static proxy...")
                new_p = rotate_static_proxy()
                if new_p:
                    proxies = new_p
                    PROXIES = new_p
            else:
                print(f"  ⚠️ Attempt {attempt}/{max_retries}: Status {r.status_code}")
        except requests.exceptions.ProxyError as e:
            print(f"   Attempt {attempt}/{max_retries}: Proxy unreachable — rotating static proxy...")
            new_p = rotate_static_proxy()
            if new_p:
                proxies = new_p
                PROXIES = new_p
        except Exception as e:
            if is_proxy_infra_error(exc=e):
                print(f"   Attempt {attempt}/{max_retries}: Proxy connection error — rotating static proxy...")
                new_p = rotate_static_proxy()
                if new_p:
                    proxies = new_p
                    PROXIES = new_p
            else:
                print(f"  ⚠️ Attempt {attempt}/{max_retries}: {str(e)}")

        if attempt < max_retries:
            wait_time = attempt * 2
            print(f"  ⏳ Retrying in {wait_time} seconds...")
            time.sleep(wait_time)

    raise Exception(f"Failed after {max_retries} attempts")

# ===== PAYLOADS =====

def comments_payload(feedback_id, cursor=None, cookies=None):
    # Extract user ID from cookies if available
    user_id = "0"
    if cookies and "c_user" in cookies:
        user_id = cookies["c_user"]
    
    return {
        "av": user_id,
        "__user": user_id,
        "__a": "1",
        "fb_dtsg": FB_DTSG if FB_DTSG else "",
        "fb_api_caller_class": "RelayModern",
        "server_timestamps": "true",
        "doc_id": "27806180149070312",
        "variables": json.dumps({
            "commentsAfterCount": -1,
            "commentsAfterCursor": cursor,
            "commentsBeforeCount": None,
            "commentsBeforeCursor": None,
            "commentsIntentToken": None,
            "feedLocation": "POST_PERMALINK_DIALOG",
            "focusCommentID": None,
            "scale": 2,
            "useDefaultActor": False,
            "id": feedback_id,
            "__relay_internal__pv__CometUFICommentAutoTranslationTyperelayprovider": "AUTO_TRANSLATE",
            "__relay_internal__pv__CometUFICommentAvatarStickerAnimatedImagerelayprovider": False,
            "__relay_internal__pv__CometUFICommentActionLinksRewriteEnabledrelayprovider": True,
            "__relay_internal__pv__IsWorkUserrelayprovider": False
        })
    }


def replies_payload(comment_feedback_id, expansion_token, cookies=None):
    # Extract user ID from cookies if available
    user_id = "0"
    if cookies and "c_user" in cookies:
        user_id = cookies["c_user"]
    
    return {
        "av": user_id,
        "__user": user_id,
        "__a": "1",
        "fb_dtsg": FB_DTSG if FB_DTSG else "",
        "fb_api_caller_class": "RelayModern",
        "server_timestamps": "true",
        "doc_id": "26570577339199586",
        "variables": json.dumps({
            "clientKey": None,
            "expansionToken": expansion_token,
            "feedLocation": "POST_PERMALINK_DIALOG",
            "focusCommentID": None,
            "scale": 2,
            "useDefaultActor": False,
            "id": comment_feedback_id,
            "__relay_internal__pv__CometUFICommentAutoTranslationTyperelayprovider": "AUTO_TRANSLATE",
            "__relay_internal__pv__CometUFICommentAvatarStickerAnimatedImagerelayprovider": False,
            "__relay_internal__pv__CometUFICommentActionLinksRewriteEnabledrelayprovider": True,
            "__relay_internal__pv__IsWorkUserrelayprovider": False
        })
    }

# ===== FETCH COMMENTS =====
import json

def fb_json(response_text):
    """
    Facebook GraphQL sometimes returns:
    for (;;);
    {json}
    {json}

    This extracts the first valid JSON object safely.
    """
    text = response_text.strip()

    # Remove for (;;);
    if text.startswith("for (;;);"):
        text = text[len("for (;;);"):]

    # Keep only first JSON object
    first = text.split("\n")[0].strip()

    return json.loads(first)


def fetch_comments(feedback_id, cookies=None):
    results = []
    cursor = None
    response_count = 0
    post_info = None  # Store parent post info from first response

    while True:
        headers = {**BASE_HEADERS, "x-fb-friendly-name": "CommentsListComponentsPaginationQuery"}
        r = retry_request(
            GRAPHQL,
            headers,
            comments_payload(feedback_id, cursor, cookies),
            PROXIES,
            cookies=cookies
        )
        j = fb_json(r.text)
        
        # Save each JSON response for inspection
        response_count += 1
        # with open(f"response_{response_count}.json", "w", encoding="utf-8") as f:
        #     json.dump(j, f, ensure_ascii=False, indent=2)
        # print(f" Saved response_{response_count}.json")
        
        comments_block = (
            j.get("data", {})
             .get("node", {})
             .get("comment_rendering_instance_for_feed_location", {})
             .get("comments", {})
        )

        edges = comments_block.get("edges", [])
        if not edges:
            break

        for e in edges:
            n = e["node"]
            fb = n.get("feedback") or {}

            # Extract parent_post_story info from first response
            if response_count == 1 and post_info is None:
                parent_post_story = (
                    n.get("comet_comment_author_name_and_badges_renderer", {})
                      .get("comment", {})
                      .get("parent_post_story", {})
                ) or n.get("parent_post_story", {})
                
                if parent_post_story:
                    post_info = {
                        "post_story_id": parent_post_story.get("id"),
                        "media_id": None
                    }
                    
                    # Extract first media ID
                    attachments = parent_post_story.get("attachments", [])
                    for attachment in attachments:
                        media = attachment.get("media", {})
                        if media and media.get("id"):
                            post_info["media_id"] = media.get("id")
                            break  # Only get first one
                    
                    print(f" Extracted post info: {post_info}")

            # Extract reaction count
            reactors = fb.get("reactors", {})
            total_reactions = reactors.get("count_reduced", "0")
            
            comment_id = n.get("legacy_fbid") or n.get("id") or ""
            author_name = (n.get("author") or {}).get("name", "")
            created_time = n.get("created_time") or ""

            results.append({
                "comment_id": comment_id,
                "author": author_name,
                "created_time": created_time,
                "text": (n.get("body") or {}).get("text", ""),
                "reaction_count": total_reactions,
                "_feedback_id": fb.get("id", ""),  # Internal use only (for fetching replies)
                "_expansion_token": (fb.get("expansion_info") or {}).get("expansion_token", "")  # Internal use only
            })

        cursor = comments_block.get("page_info", {}).get("end_cursor")
        #break
        if not cursor:
            break

        #time.sleep(0.4)

    return results, post_info

# ===== FETCH REPLIES =====

def fetch_replies(comment, cookies=None):
    feedback_id = comment.get("_feedback_id")
    expansion_token = comment.get("_expansion_token")
    if not feedback_id or not expansion_token:
        return []

    headers = {**BASE_HEADERS, "x-fb-friendly-name": "Depth1CommentsListPaginationQuery"}
    r = retry_request(
        GRAPHQL,
        headers,
        replies_payload(feedback_id, expansion_token, cookies),
        PROXIES,
        cookies=cookies
    )

    j = fb_json(r.text)
    replies = []

    edges = (
        j.get("data", {})
         .get("node", {})
         .get("replies_connection", {})
         .get("edges", [])
    )

    root_comment_id = comment.get("comment_id", "")

    for e in edges:
        n = e.get("node", {})
        fb = n.get("feedback") or {}
        
        # Extract reaction count
        reactors = fb.get("reactors", {})
        total_reactions = reactors.get("count_reduced", "0")
        
        reply_id = n.get("legacy_fbid") or n.get("id") or ""
        author_name = (n.get("author") or {}).get("name", "")
        created_time = n.get("created_time") or ""

        replied_to = (n.get("replied_comment") or {}).get("id") or (n.get("parent_comment") or {}).get("id")
        
        replies.append({
            "reply_id": reply_id,
            "parent_comment_id": root_comment_id,
            "direct_parent_id": replied_to if replied_to else root_comment_id,
            "author": author_name,
            "created_time": created_time,
            "text": (n.get("body") or {}).get("text", ""),
            "reaction_count": total_reactions
        })

    return replies


def fetch_all_replies_parallel(comments, cookies=None, max_workers=5):
    """
    Tải đồng thời replies cho tất cả comments bằng ThreadPoolExecutor.
    Tăng tốc độ thu thập từ 3x - 5x so với tải tuần tự mà vẫn an toàn.
    """
    from concurrent.futures import ThreadPoolExecutor

    candidates = [
        (idx, c) for idx, c in enumerate(comments)
        if c.get("_feedback_id") and c.get("_expansion_token")
    ]

    for c in comments:
        if "replies" not in c:
            c["replies"] = []

    if not candidates:
        return comments

    def _worker(item):
        idx, comment = item
        try:
            return idx, fetch_replies(comment, cookies=cookies)
        except Exception:
            return idx, []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for idx, replies in executor.map(_worker, candidates):
            comments[idx]["replies"] = replies

    return comments


def build_hierarchical_rows(post_id, post_message, comments):
    """
    Chuyển đổi danh sách comments & replies thành các hàng phân cấp:
    - 1: Comment gốc thứ nhất -> reply_to_message là nội dung bài viết (post_message)
    - 1_1: Reply thứ nhất của comment 1 -> reply_to_message là nội dung comment 1
    - 1_1_1: Reply thứ nhất của comment 1_1 -> reply_to_message là nội dung comment 1_1
    - 1_1_2: Reply thứ hai của comment 1_1 -> reply_to_message là nội dung comment 1_1
    - 1_2: Reply thứ hai của comment 1 -> reply_to_message là nội dung comment 1
    - 2: Comment gốc thứ hai -> reply_to_message là nội dung bài viết (post_message)
    """
    rows = []
    h_to_msg = {}
    
    for c_idx, comment in enumerate(comments, start=1):
        root_h_id = str(c_idx)
        root_msg = comment.get("text", "")
        h_to_msg[root_h_id] = root_msg
        
        # Comment gốc phản hồi trực tiếp bài viết: reply_to_message = nội dung bài viết
        rows.append({
            "post_id": str(post_id),
            "post_message": post_message or "",
            "comment_id": root_h_id,
            "reply_to_message": post_message or "",
            "message": root_msg or ""
        })
        
        # Bản đồ theo dõi ID gốc Facebook / tên tác giả -> ID phân cấp
        id_to_h = {}
        author_to_h = {}
        children_counter = {}
        
        root_fb_id = comment.get("comment_id", "")
        if root_fb_id:
            id_to_h[root_fb_id] = root_h_id
        root_author = (comment.get("author") or "").strip()
        if root_author:
            author_to_h[root_author] = root_h_id
            
        replies = comment.get("replies", [])
        for reply in replies:
            reply_msg = reply.get("text", "")
            reply_fb_id = reply.get("reply_id", "")
            direct_parent_fb_id = reply.get("direct_parent_id", "")
            reply_author = (reply.get("author") or "").strip()
            
            # 1. Xác định ID phân cấp của cha (parent_h_id)
            parent_h_id = None
            
            # Ưu tiên 1: Tra cứu qua direct_parent_id nếu trùng ID reply trước đó trong thread
            if direct_parent_fb_id and direct_parent_fb_id in id_to_h:
                parent_h_id = id_to_h[direct_parent_fb_id]
                
            # Ưu tiên 2: Kiểm tra tag/mention tên tác giả ở đầu reply
            if not parent_h_id and reply_msg:
                for known_author, h_id in sorted(author_to_h.items(), key=lambda x: len(x[0]), reverse=True):
                    if known_author and h_id != root_h_id:
                        clean_text = reply_msg.lstrip("@").strip()
                        if clean_text.lower().startswith(known_author.lower()):
                            parent_h_id = h_id
                            break
                            
            # Mặc định: Phản hồi trực tiếp comment gốc
            if not parent_h_id:
                parent_h_id = root_h_id
                
            # 2. Tạo ID phân cấp cho reply này
            child_idx = children_counter.get(parent_h_id, 0) + 1
            children_counter[parent_h_id] = child_idx
            reply_h_id = f"{parent_h_id}_{child_idx}"
            
            h_to_msg[reply_h_id] = reply_msg
            parent_msg = h_to_msg.get(parent_h_id, "")
            
            # Lưu lại vào bản đồ để các reply con sau này có thể tham chiếu
            if reply_fb_id:
                id_to_h[reply_fb_id] = reply_h_id
            if reply_author:
                author_to_h[reply_author] = reply_h_id
                
            rows.append({
                "post_id": str(post_id),
                "post_message": post_message or "",
                "comment_id": reply_h_id,
                "reply_to_message": parent_msg,
                "message": reply_msg or ""
            })
            
    return rows

# ===== RUN =====

if __name__ == "__main__":
    import argparse
    import base64

    parser = argparse.ArgumentParser(description="Scrape comments and replies for a Facebook post")
    parser.add_argument("--post-id", default="1420269302790428", help="Facebook Post ID")
    parser.add_argument("--cookies", default="", help="Facebook cookie string")
    parser.add_argument("--fb-dtsg", default="", help="Facebook fb_dtsg token")
    args = parser.parse_args()

    POST_ID = args.post_id
    POST_FEEDBACK_ID = base64.b64encode(f"feedback:{POST_ID}".encode()).decode()
    if args.fb_dtsg:
        FB_DTSG = args.fb_dtsg

    req_cookies = {}
    if args.cookies:
        for item in args.cookies.split(";"):
            if "=" in item:
                k, v = item.strip().split("=", 1)
                req_cookies[k] = v
    else:
        req_cookies = None

    all_data = []

    comments, post_info = fetch_comments(POST_FEEDBACK_ID, cookies=req_cookies)
    
    # Add post info to the output
    output = {
        "post_info": post_info,
        "comments": []
    }

    for c in comments:
        print(f"\n[Comment ID: {c.get('comment_id', '')}] {c.get('author', 'Anonymous')}: {c.get('text', '')}")
        c["replies"] = fetch_replies(c, cookies=req_cookies)

        for r in c["replies"]:
            print(f"   ↳ [Reply ID: {r.get('reply_id', '')} -> Parent ID: {r.get('parent_comment_id', '')}] {r.get('author', 'Anonymous')}: {r.get('text', '')}")

        output["comments"].append(c)

    # Create directory for this post
    os.makedirs(f"simple_post/{POST_ID}", exist_ok=True)
    
    # Save as {post_id}.json
    output_file = f"simple_post/{POST_ID}/{POST_ID}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f" Saved to {output_file}")

    # Save as hierarchical CSV
    csv_output_file = f"simple_post/{POST_ID}/{POST_ID}_comments.csv"
    with open(csv_output_file, "w", newline="", encoding="utf-8-sig") as f:
        fieldnames = ["post_id", "post_message", "comment_id", "reply_to_message", "message"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        post_msg = (post_info or {}).get("message", "") if post_info else ""
        for row in build_hierarchical_rows(POST_ID, post_msg, comments):
            writer.writerow({
                "post_id": row["post_id"],
                "post_message": row["post_message"],
                "comment_id": row["comment_id"],
                "reply_to_message": row["reply_to_message"],
                "message": row["message"],
            })
    print(f" Saved hierarchical CSV to {csv_output_file}")



import os, re
import httpx
from dotenv import load_dotenv

load_dotenv()  # ensure .env is loaded even if anchoring.py wasn't imported yet

BEARER = os.getenv("TWITTER_BEARER_TOKEN")

def _auth_headers():
    if not BEARER:
        return None
    return {"Authorization": f"Bearer {BEARER}"}

def _extract_tweet_id(url_or_id: str) -> str:
    m = re.search(r"/status/(\d+)", url_or_id)
    return m.group(1) if m else url_or_id

def fetch_tweet_by_id(id_or_url: str) -> dict:
    """Lightweight, works on Basic tiers better than search."""
    headers = _auth_headers()
    if headers is None:
        return {"error": "missing_token", "hint": "Set TWITTER_BEARER_TOKEN in .env"}
    tid = _extract_tweet_id(id_or_url)
    url = f"https://api.twitter.com/2/tweets/{tid}"
    params = {
        "tweet.fields": "created_at,author_id,text,lang,public_metrics,attachments",
        "expansions": "author_id",
        "user.fields": "username,name,verified",
    }
    try:
        with httpx.Client(timeout=20) as c:
            r = c.get(url, headers=headers, params=params)
        if r.status_code != 200:
            return {"error": "twitter_error", "status": r.status_code, "body": r.text}
        return r.json()
    except Exception as e:
        return {"error": "client_exception", "detail": str(e)}

def fetch_user_tweets(username: str, max_results: int = 5) -> dict:
    headers = _auth_headers()
    if headers is None:
        return {"error": "missing_token", "hint": "Set TWITTER_BEARER_TOKEN in .env"}
    username = username.lstrip("@")
    try:
        with httpx.Client(timeout=20) as c:
            # 1) user id
            ru = c.get(
                f"https://api.twitter.com/2/users/by/username/{username}",
                headers=headers,
                params={"user.fields": "username,verified"},
            )
            if ru.status_code != 200:
                return {"error": "twitter_error_user", "status": ru.status_code, "body": ru.text}
            user = ru.json().get("data")
            if not user:
                return {"error": "not_found", "hint": "username not found"}

            # 2) tweets
            rt = c.get(
                f"https://api.twitter.com/2/users/{user['id']}/tweets",
                headers=headers,
                params={"max_results": max_results, "tweet.fields": "created_at,public_metrics,lang"},
            )
            if rt.status_code != 200:
                return {"error": "twitter_error_tweets", "status": rt.status_code, "body": rt.text}
            out = rt.json()
            out["user"] = {"id": user["id"], "username": user["username"], "verified": user.get("verified", False)}
            return out
    except Exception as e:
        return {"error": "client_exception", "detail": str(e)}

def fetch_recent_search(query: str, max_results: int = 5) -> dict:
    """Often rate-limited on Basic tiers; prefer the two above."""
    headers = _auth_headers()
    if headers is None:
        return {"error": "missing_token", "hint": "Set TWITTER_BEARER_TOKEN in .env"}
    try:
        with httpx.Client(timeout=20) as c:
            r = c.get(
                "https://api.twitter.com/2/tweets/search/recent",
                headers=headers,
                params={"query": query, "max_results": max_results, "tweet.fields": "created_at,public_metrics,lang"},
            )
        if r.status_code != 200:
            return {"error": "twitter_error_search", "status": r.status_code, "body": r.text}
        return r.json()
    except Exception as e:
        return {"error": "client_exception", "detail": str(e)}

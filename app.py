# app.py
# W3b Stitch – minimal FastAPI app with working routes and safe error handling

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import hashlib, json

# ---- Anchoring (requires .env with L2_RPC_URL, PRIVATE_KEY, ACCOUNT_ADDRESS) ----
from anchoring import anchor_to_l2, anchor_to_l1

# ---- Twitter adapters (make sure these functions exist in adapters/twitter_adapter.py) ----
# (We intentionally DO NOT import a non-existent fetch_twitter to avoid ImportError)
from adapters.twitter_adapter import (
    fetch_tweet_by_id,
    fetch_user_tweets,
    fetch_recent_search,
)

app = FastAPI(title="W3b Stitch Demo")

# CORS (allow everything for local dev; tighten later for prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# -----------------------------
# Home & health (so "/" works)
# -----------------------------
@app.get("/")
def home():
    return {"ok": True, "name": "W3b Stitch API", "see": "/docs"}

@app.get("/health")
def health():
    return {"status": "up"}

# ---------------------------------------
# 1) MVCM — Media Verification & Curation
# ---------------------------------------
# NOTE: Requires `python-multipart` installed (pip install python-multipart)
@app.post("/media/hash")
async def media_hash(file: UploadFile = File(...)):
    content = await file.read()
    media_sha256 = hashlib.sha256(content).hexdigest()
    return {"filename": file.filename, "sha256": media_sha256}

# ---------------------------------------------------------
# 2) CAPM — Credential Authentication & Provenance (toy)
# ---------------------------------------------------------
class Credential(BaseModel):
    issuer: str
    subject: str
    claims: dict

@app.post("/credential/issue")
async def issue_credential(cred: Credential):
    blob = json.dumps(cred.dict(), sort_keys=True).encode()
    return {"credential": cred.dict(), "hash": hashlib.sha256(blob).hexdigest()}

# ---------------------------------------------------
# 6) State Packaging & Anchoring (L2 / optional L1)
# ---------------------------------------------------
def _canonical(d: dict) -> bytes:
    # deterministic JSON: stable keys + compact separators
    return json.dumps(d, sort_keys=True, separators=(",", ":")).encode()

def _sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

@app.post("/state/package")
async def package_state(data: dict):
    b = _canonical(data)
    return {"bundle": data, "hash": _sha256_hex(b)}

@app.post("/anchor/l2")
async def anchor_state_l2(data: dict):
    try:
        tx = anchor_to_l2(data)
        return {"anchored_data": data, "l2_tx_hash": tx}
    except Exception as e:
        # return JSON error instead of 500 crash
        return {"error": "anchor_l2_failed", "detail": str(e)}

@app.post("/anchor/l1")
async def anchor_state_l1(data: dict):
    try:
        tx = anchor_to_l1(data)
        return {"anchored_data": data, "l1_tx_hash": tx}
    except Exception as e:
        return {"error": "anchor_l1_failed", "detail": str(e)}

# -------------------------------------------------
# Twitter endpoints (GET) – easy to test in /docs
# -------------------------------------------------
# Tip: these return JSON with readable errors instead of throwing 500s
# Ensure your .env has: TWITTER_BEARER_TOKEN=... and you restarted the server.

@app.get("/twitter/lookup")
def twitter_lookup(id_or_url: str):
    """
    Fetch a single Tweet by ID or full URL.
    Example: /twitter/lookup?id_or_url=https://x.com/elonmusk/status/1234567890123456789
    """
    try:
        return fetch_tweet_by_id(id_or_url)
    except Exception as e:
        return {"error": "lookup_failed", "detail": str(e)}

@app.get("/twitter/user_tweets")
def twitter_user_tweets(username: str, max_results: int = 5):
    """
    Fetch recent tweets from a username (usually lighter limits than full search).
    Example: /twitter/user_tweets?username=elonmusk&max_results=3
    """
    try:
        return fetch_user_tweets(username, max_results)
    except Exception as e:
        return {"error": "user_tweets_failed", "detail": str(e)}

@app.get("/twitter/search")
def twitter_search(q: str, max_results: int = 5):
    """
    Recent search (may be rate-limited on Basic access).
    Example: /twitter/search?q=from:elonmusk&max_results=5
    """
    try:
        return fetch_recent_search(q, max_results)
    except Exception as e:
        return {"error": "search_failed", "detail": str(e)}

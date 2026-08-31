import os
import re
import requests
from flask import Flask, request, jsonify
from functools import wraps

app = Flask(__name__)

# ============ CONFIG ============
API_KEY        = os.environ.get("API_KEY", "shreesh")
PORT           = int(os.environ.get("PORT", 10000))
UPSTREAM_URL   = os.environ.get("UPSTREAM_URL", "https://shareware-logs-laptop-mix.trycloudflare.com/search/number")
UPSTREAM_KEY   = os.environ.get("UPSTREAM_KEY", "htk_live_demo123456")
OWNER          = os.environ.get("OWNER", "shaurya")
CHANNEL        = os.environ.get("CHANNEL", "shaurya")
CHANNEL_LINK   = os.environ.get("CHANNEL_LINK", "baad me")
API_BY         = os.environ.get("API_BY", "num API")
VERSION        = "1.0.0"
# ================================


# ─── Key Middleware ─────────────────────────────────────────
def require_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.args.get("key") or request.headers.get("X-Api-Key")
        if not key:
            return jsonify({"error": True, "message": "API key required. Use ?key=KEY&number=NUM", "owner": OWNER, "channel": CHANNEL, "channel_url": CHANNEL_LINK, "get_free_key": f"Join {CHANNEL} for free API key"}), 401
        if key != API_KEY:
            return jsonify({"error": True, "message": "Invalid API key.", "owner": OWNER, "channel": CHANNEL, "channel_url": CHANNEL_LINK, "get_free_key": f"Join {CHANNEL} for free API key"}), 403
        return f(*args, **kwargs)
    return decorated


# ─── Clean developer tags ──────────────────────────────────
def clean_records(records):
    cleaned = []
    for rec in records:
        new_rec = dict(rec)
        if "name" in new_rec and new_rec["name"]:
            new_rec["name"] = re.sub(r'\s*\|\s*@\w+\s*\(.*?\)\s*$', '', new_rec["name"]).strip()
        cleaned.append(new_rec)
    return cleaned


# ─── Inject credits ───────────────────────────────────────
def inject_credits(data):
    data.pop("developer", None)
    data["owner"] = OWNER
    data["channel"] = CHANNEL
    data["channel_url"] = CHANNEL_LINK
    data["api_by"] = API_BY
    data["get_free_api_key"] = f"Join {CHANNEL} for free API key"
    return data


# ─── Home ─────────────────────────────────────────────────
@app.route("/")
def home():
    return jsonify({
        "name": "Number Info API",
        "version": VERSION,
        "owner": OWNER,
        "channel": CHANNEL,
        "channel_url": CHANNEL_LINK,
        "endpoints": {"search": "/search/number?key=YOUR_KEY&number=PHONE_NUMBER"},
        "get_free_key": f"Join {CHANNEL} for free API key"
    })


# ─── Main Endpoint ────────────────────────────────────────
@app.route("/search/number", methods=["GET"])
@require_key
def search_number():
    number = request.args.get("number")
    if not number:
        return jsonify({"error": True, "message": 'Missing "number" parameter', "owner": OWNER, "channel": CHANNEL, "channel_url": CHANNEL_LINK}), 400

    try:
        resp = requests.get(
            UPSTREAM_URL,
            params={"number": number, "key": UPSTREAM_KEY},
            timeout=30,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        if resp.status_code != 200:
            return jsonify({
                "error": True,
                "message": f"Upstream returned {resp.status_code}",
                "owner": OWNER, "channel": CHANNEL, "channel_url": CHANNEL_LINK
            }), resp.status_code

        data = resp.json()

        if "records" in data and isinstance(data["records"], list):
            data["records"] = clean_records(data["records"])

        data = inject_credits(data)
        return jsonify(data)

    except requests.exceptions.Timeout:
        return jsonify({"error": True, "message": "Upstream timeout", "owner": OWNER, "channel": CHANNEL, "channel_url": CHANNEL_LINK}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({"error": True, "message": "Upstream error", "detail": str(e), "owner": OWNER, "channel": CHANNEL, "channel_url": CHANNEL_LINK}), 502
    except Exception as e:
        return jsonify({"error": True, "message": "Internal error", "detail": str(e), "owner": OWNER, "channel": CHANNEL, "channel_url": CHANNEL_LINK}), 500


# ─── Start ─────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)

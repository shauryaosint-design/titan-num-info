import os
import requests
from flask import Flask, request, jsonify
from functools import wraps

app = Flask(__name__)

# ════════════ CONFIG (Change here or in Render ENV) ════════════
API_KEY        = os.environ.get("API_KEY", "TITANKING")
PORT           = int(os.environ.get("PORT", 10000))

# Upstream Number API
UPSTREAM_URL   = os.environ.get("UPSTREAM_URL", "https://shareware-logs-laptop-mix.trycloudflare.com/search/number")
UPSTREAM_KEY   = os.environ.get("UPSTREAM_KEY", "htk_live_demo123456")

# Your credits
OWNER          = os.environ.get("OWNER", "@TITANCONTACT @g0zig")
CHANNEL        = os.environ.get("CHANNEL", "@titankeng")
CHANNEL_LINK   = os.environ.get("CHANNEL_LINK", "https://t.me/titankeng")
API_BY         = os.environ.get("API_BY", "TITAN API")
VERSION        = "1.0.0"
# ════════════════════════════════════════════════════════════════


# ─── API Key Middleware ────────────────────────────────────────
def require_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.args.get("key") or request.headers.get("X-Api-Key")
        if not key:
            return jsonify({
                "error": True,
                "message": "API key required. Use ?key=YOUR_KEY&number=NUMBER",
                "owner": OWNER,
                "channel": CHANNEL,
                "channel_url": CHANNEL_LINK,
                "get_free_key": f"Join {CHANNEL} for free API key"
            }), 401
        if key != API_KEY:
            return jsonify({
                "error": True,
                "message": "Invalid API key. Join channel for free key.",
                "owner": OWNER,
                "channel": CHANNEL,
                "channel_url": CHANNEL_LINK,
                "get_free_key": f"Join {CHANNEL} for free API key"
            }), 403
        return f(*args, **kwargs)
    return decorated


# ─── Clean developer tags from records ────────────────────────
def clean_records(records):
    """Remove @Zero_kn0wledge and API Developer tags from name fields"""
    cleaned = []
    for rec in records:
        new_rec = dict(rec)
        if "name" in new_rec and new_rec["name"]:
            # Remove " | @Zero_kn0wledge (API Developer)" or similar
            new_rec["name"] = re.sub(r'\s*\|\s*@\w+\s*\(.*?\)\s*$', '', new_rec["name"]).strip()
            new_rec["name"] = re.sub(r'\s*\|.*$', '', new_rec["name"]).strip()
        cleaned.append(new_rec)
    return cleaned


# ─── Inject your credits ──────────────────────────────────────
def inject_credits(data):
    data.pop("developer", None)  # remove original developer field
    data["owner"] = OWNER
    data["channel"] = CHANNEL
    data["channel_url"] = CHANNEL_LINK
    data["api_by"] = API_BY
    data["get_free_api_key"] = f"Join {CHANNEL} for free API key"
    return data


# ─── Home ─────────────────────────────────────────────────────
@app.route("/")
def home():
    return jsonify({
        "name": "Number Info API",
        "version": VERSION,
        "owner": OWNER,
        "channel": CHANNEL,
        "channel_url": CHANNEL_LINK,
        "endpoints": {
            "search": "/search/number?key=YOUR_KEY&number=PHONE_NUMBER"
        },
        "get_free_key": f"Join {CHANNEL} for free API key"
    })


# ─── Main Endpoint: /search/number ────────────────────────────
@app.route("/search/number", methods=["GET"])
@require_key
def search_number():
    number = request.args.get("number")
    if not number:
        return jsonify({
            "error": True,
            "message": 'Missing "number" parameter. Usage: ?key=YOUR_KEY&number=PHONE_NUMBER',
            "owner": OWNER,
            "channel": CHANNEL,
            "channel_url": CHANNEL_LINK
        }), 400

    try:
        # Call upstream API with their key
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
                "owner": OWNER,
                "channel": CHANNEL,
                "channel_url": CHANNEL_LINK
            }), resp.status_code

        data = resp.json()

        # Clean records — remove @Zero_kn0wledge tags
        if "records" in data and isinstance(data["records"], list):
            data["records"] = clean_records(data["records"])

        # Inject your credits
        data = inject_credits(data)

        return jsonify(data)

    except requests.exceptions.Timeout:
        return jsonify({
            "error": True,
            "message": "Upstream API timeout",
            "owner": OWNER, "channel": CHANNEL, "channel_url": CHANNEL_LINK
        }), 504
    except requests.exceptions.RequestException as e:
        return jsonify({
            "error": True,
            "message": "Upstream API error",
            "detail": str(e),
            "owner": OWNER, "channel": CHANNEL, "channel_url": CHANNEL_LINK
        }), 502
    except Exception as e:
        return jsonify({
            "error": True,
            "message": "Internal server error",
            "owner": OWNER, "channel": CHANNEL, "channel_url": CHANNEL_LINK
        }), 500


# ─── Start ────────────────────────────────────────────────────
if __name__ == "__main__":
    import re  # needed by clean_records
    app.run(host="0.0.0.0", port=PORT)

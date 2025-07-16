from flask import Flask, request, jsonify
from leaderboard import init_db, add_hotdogs, get_total, get_leaderboard
from google_sync import update_leaderboard, log_entry
from monday_digest import post_digest
import os
import re

app = Flask(__name__)
init_db()

@app.route("/doglog", methods=["POST"])
def doglog():
    user_name = request.form.get("user_name")
    text = request.form.get("text", "").strip().lower()

    if text.startswith("add"):
        try:
            add_match = re.match(r"add\s+([\d.]+)(?:\s+for\s+(.+))?", text)
            if not add_match:
                return jsonify({"text": "Usage: /doglog add [number] (e.g., /doglog add 3.5 for @lizzie)"})

            count = float(add_match.group(1))
            target_user = add_match.group(2) or user_name
            target_user = target_user.replace("@", "").strip().lower()

            add_hotdogs(target_user, count)
            log_entry(target_user, count)
            rows = get_leaderboard()
            update_leaderboard(rows)
            total = get_total(target_user)

            return jsonify({
                "response_type": "in_channel",
                "text": f":hotdog: {user_name} logged {count:.1f} hot dogs for {target_user}! Total: {total:.1f} 🌭"
            })
        except Exception as e:
            print(f"Error: {e}")
            return jsonify({"text": "Something went wrong. Make sure your command looks like: /doglog add 2.5 for @username"})

    elif text.startswith("leaderboard"):
        try:
            rows = get_leaderboard()
            if not rows:
                return jsonify({"text": "No hot dogs logged yet!"})

            leaderboard_text = "\n".join(
                [f"{i+1}. {name} — {count:.1f} 🌭" for i, (name, count) in enumerate(rows)]
            )
            return jsonify({
                "response_type": "in_channel",
                "text": "*🌭 DogLog Leaderboard:*\n" + leaderboard_text
            })
        except Exception as e:
            print(f"Error generating leaderboard: {e}")
            return jsonify({"text": "Error loading leaderboard."})

    else:
        return jsonify({
            "text": "Try:\n• /doglog add [number] (e.g., /doglog add 2.5)\n• /doglog add [number] for [username] (e.g., /doglog add 1 for @katie)\n• /doglog leaderboard"
        })

@app.route("/digest-trigger", methods=["GET"])
def trigger_digest():
    token = request.args.get("token")
    if token != os.getenv("DIGEST_SECRET"):
        return "Unauthorized", 403

    try:
        post_digest()
        return "Digest sent successfully!", 200
    except Exception as e:
        print(f"Digest error: {e}")
        return "Failed to send digest", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)

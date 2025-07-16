import os
from flask import Flask, request, jsonify
from leaderboard import init_db, add_hotdogs, get_total, get_leaderboard
from google_sync import log_entry, update_leaderboard, get_user_stats
from monday_digest import post_digest

app = Flask(__name__)
init_db()

@app.route("/doglog", methods=["POST"])
def doglog():
    user_name = request.form.get("user_name")
    text = request.form.get("text", "").strip().lower()

    if text.startswith("add"):
        import re
        try:
            add_match = re.match(r"add\s+([\d.]+)(?:\s+for\s+(.+))?", text)
            if not add_match:
                return jsonify({"text": "Usage: /doglog add [number] (e.g., /doglog add 3.5 for @lizzie)"})

            count = float(add_match.group(1))
            target_user = add_match.group(2) or user_name
            target_user = target_user.replace("@", "").strip().lower()

            add_hotdogs(target_user, count)
            log_entry(target_user, count)
            update_leaderboard(get_leaderboard())
            total = get_total(target_user)

            return jsonify({
                "response_type": "in_channel",
                "text": f":hotdog: {user_name} logged {count:.1f} hot dogs for {target_user}! Total: {total:.1f} \U0001F32D"
            })
        except Exception as e:
            print(f"Error: {e}")
            return jsonify({"text": "Something went wrong. Make sure your command looks like: /doglog add 2.5 for @username"})

    elif text.startswith("leaderboard"):
        try:
            rows = get_leaderboard()
            if not rows:
                return jsonify({"text": "No hot dogs logged yet!"})

            leaderboard_text = "\n".join([
                f"{i+1}. {name} — {count:.1f} \U0001F32D" for i, (name, count) in enumerate(rows)
            ])
            return jsonify({
                "response_type": "in_channel",
                "text": "*\U0001F32D DogLog Leaderboard:*\n" + leaderboard_text
            })
        except Exception as e:
            print(f"Error generating leaderboard: {e}")
            return jsonify({"text": "Error loading leaderboard."})

    elif text.startswith("stats"):
        try:
            parts = text.split(" ", 1)
            target_user = parts[1].replace("@", "").strip().lower() if len(parts) > 1 else user_name
            stats = get_user_stats(target_user)
            if not stats:
                return jsonify({"text": f"No stats found for {target_user}."})

            return jsonify({
                "response_type": "in_channel",
                "text": (
                    f"\U0001F32D Stats for {target_user}:\n"
                    f"• Total hot dogs: {stats['total']:.1f}\n"
                    f"• Entries: {stats['entries']}\n"
                    f"• Average per log: {stats['average']:.1f}\n"
                    f"• First log: {stats['first_log']}\n"
                    f"• Most recent log: {stats['last_log']}\n"
                    f"• Largest log: {stats['largest_log']:.1f} dogs on {stats['largest_log_date']}"
                )
            })
        except Exception as e:
            print(f"Error generating stats: {e}")
            return jsonify({"text": "Error loading stats."})

    else:
        return jsonify({
            "text": (
                "Try:\n"
                "• /doglog add [number] (e.g., /doglog add 2.5)\n"
                "• /doglog add [number] for [username] (e.g., /doglog add 1 for @katie)\n"
                "• /doglog leaderboard\n"
                "• /doglog stats [username]"
            )
        })

@app.route("/digest-trigger", methods=["GET"])
def digest_trigger():
    token = request.args.get("token")
    if token != os.environ.get("DIGEST_TRIGGER_TOKEN"):
        return jsonify({"message": "Invalid token", "status": "error"}), 403
    try:
        post_digest()
        return jsonify({"message": "Digest posted successfully", "status": "ok"})
    except Exception as e:
        print(f"Error posting digest: {e}")
        return jsonify({"message": f"Error posting digest: {e}", "status": "error"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)

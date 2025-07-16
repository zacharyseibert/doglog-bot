# doglog_bot.py

from flask import Flask, request, jsonify
from google_sync import log_entry, update_leaderboard, get_user_stats
from monday_digest import post_digest

app = Flask(__name__)

@app.route("/doglog", methods=["POST"])
def doglog():
    data = request.form
    text = data.get("text", "")
    user_name = data.get("user_name", "unknown")

    try:
        parts = text.split()
        if len(parts) == 0:
            return jsonify({"response_type": "ephemeral", "text": "Usage: /doglog [amount] [@user (optional)]"})

        amount = float(parts[0])
        target_user = parts[1][1:] if len(parts) > 1 and parts[1].startswith("@") else user_name

        log_entry(target_user, amount)
        update_leaderboard(target_user, amount)

        return jsonify({
            "response_type": "in_channel",
            "text": f"{target_user} logged {amount} 🌭!"
        })
    except Exception as e:
        return jsonify({"response_type": "ephemeral", "text": f"Error: {str(e)}"})

@app.route("/stats", methods=["POST"])
def stats():
    data = request.form
    text = data.get("text", "")
    user_name = data.get("user_name", "unknown")
    target_user = text.strip()[1:] if text.strip().startswith("@") else user_name

    try:
        stats = get_user_stats(target_user)
        if not stats:
            return jsonify({"response_type": "ephemeral", "text": f"No stats found for {target_user}."})

        message = (
            f"🌭 Stats for {target_user}:\n"
            f"• Total hot dogs: {stats['total']:.1f}\n"
            f"• Entries: {stats['entries']}\n"
            f"• Average per log: {stats['average']:.1f}\n"
            f"• First log: {stats['first_log']}\n"
            f"• Most recent log: {stats['last_log']}\n"
            f"• Largest log: {stats['largest_log']:.1f} dogs on {stats['largest_log_date']}"
        )

        return jsonify({"response_type": "in_channel", "text": message})
    except Exception as e:
        return jsonify({"response_type": "ephemeral", "text": f"Error fetching stats: {str(e)}"})

@app.route("/digest-trigger", methods=["GET"])
def digest_trigger():
    token = request.args.get("token")
    if token != "whosyourglizzydaddy":
        return jsonify({"error": "Unauthorized"}), 403
    return post_digest()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

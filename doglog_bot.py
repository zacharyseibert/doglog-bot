from flask import Flask, request, jsonify
from google_sync import (
    log_entry,
    update_leaderboard,
    get_total_from_sheet,
    get_leaderboard_from_sheet,
    get_user_stats
)
import os
import re
import threading
from datetime import datetime

app = Flask(__name__)

def process_log(user_name, target_user, count):
    try:
        log_entry(target_user, count)
        leaderboard = get_leaderboard_from_sheet()
        update_leaderboard(leaderboard)
        total = get_total_from_sheet(target_user)
        print(f"{user_name} logged {count} hot dogs for {target_user}. Total: {total:.1f}")
    except Exception as e:
        print(f"Background log error: {e}")

def format_user_stats(username):
    entries = get_user_stats(username)
    if not entries:
        return f"No stats found for {username}."

    total = sum(amount for _, amount in entries)
    count = len(entries)
    average = total / count if count else 0
    first_date = datetime.fromisoformat(entries[0][0]).strftime("%b %d")
    last_date = datetime.fromisoformat(entries[-1][0]).strftime("%b %d")
    largest = max(entries, key=lambda x: x[1])
    largest_amount = largest[1]
    largest_day = datetime.fromisoformat(largest[0]).strftime("%b %d")

    return (
        f"\U0001f32d Stats for {username}:\n"
        f"• Total hot dogs: {total:.1f}\n"
        f"• Entries: {count}\n"
        f"• Average per log: {average:.1f}\n"
        f"• First log: {first_date}\n"
        f"• Most recent log: {last_date}\n"
        f"• Largest log: {largest_amount:.1f} dogs on {largest_day}"
    )

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

            threading.Thread(target=process_log, args=(user_name, target_user, count)).start()

            return jsonify({
                "response_type": "in_channel",
                "text": f":hourglass_flowing_sand: Logging {count:.1f} hot dogs for {target_user}..."
            })
        except Exception as e:
            print(f"Error: {e}")
            return jsonify({"text": "Something went wrong. Check your syntax: /doglog add 2.5 for @username"})

    elif text.startswith("leaderboard"):
        try:
            rows = get_leaderboard_from_sheet()
            if not rows:
                return jsonify({"text": "No hot dogs logged yet!"})

            leaderboard_text = "\n".join(
                [f"{i+1}. {name} — {count:.1f} \U0001f32d" for i, (name, count) in enumerate(rows)]
            )
            return jsonify({
                "response_type": "in_channel",
                "text": "*\U0001f32d DogLog Leaderboard:*\n" + leaderboard_text
            })
        except Exception as e:
            print(f"Error generating leaderboard: {e}")
            return jsonify({"text": "Error loading leaderboard."})

    elif text.startswith("stats"):
        try:
            stats_match = re.match(r"stats(?:\s+for\s+(.+))?", text)
            target_user = stats_match.group(1) if stats_match and stats_match.group(1) else user_name
            target_user = target_user.replace("@", "").strip().lower()
            stats_message = format_user_stats(target_user)
            return jsonify({"response_type": "in_channel", "text": stats_message})
        except Exception as e:
            print(f"Error generating stats: {e}")
            return jsonify({"text": "Error generating stats."})

    else:
        return jsonify({
            "text": "Try:\n• /doglog add [number] (e.g., /doglog add 2.5)\n• /doglog add [number] for [username] (e.g., /doglog add 1 for @katie)\n• /doglog leaderboard\n• /doglog stats [for @username]"
        })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)

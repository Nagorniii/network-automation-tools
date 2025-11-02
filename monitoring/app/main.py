from flask import Flask, jsonify, render_template
import json
import os
import threading
import time

from ssh_worker import main

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/results")
def get_results():
    if os.path.exists("results.json"):
        with open("results.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)
    return jsonify({"error": "No data yet"}), 404

@app.route("/api/scan")
def run_scan():
    thread = threading.Thread(target=main)
    thread.start()
    return jsonify({"status": "Scan started"}), 202


def background_scanner(interval=600):
    """Фонове оновлення результатів кожні 5 хвилин"""
    while True:
        print("🔄 Running scheduled scan...")
        try:
            main()
        except Exception as e:
            print(f"❌ Scan failed: {e}")
        time.sleep(interval)

if __name__ == "__main__":
    # запуск фонового процесу для періодичного оновлення
    threading.Thread(target=background_scanner, daemon=True).start()
    app.run(host="0.0.0.0", port=5000, debug=False)

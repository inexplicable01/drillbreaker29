"""Daily Guess the Price run: checks open rounds for sales, scores them, and picks new homes.

Schedule on PythonAnywhere once a day:  python Tasks_GuessGame.py --base prod
How often new homes are picked is controlled by GAME_FREQUENCY in the app's .env (daily/weekly).
"""
import argparse
import os
import sys
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

parser = argparse.ArgumentParser()
parser.add_argument(
    "--base",
    choices=["local", "prod"],
    default="local",
    help="Which base URL to use: 'local' or 'prod' (default: local)",
)
parser.add_argument(
    "--force-pick",
    action="store_true",
    help="Pick new homes even if today isn't a pick day",
)
args = parser.parse_args()

if args.base == "local":
    base = "http://127.0.0.1:5000/"
else:  # "prod"
    base = "https://www.drillbreaker29.com/"

print(f"{datetime.now()} Guess the Price run against {base}")
try:
    response = requests.post(base + "game/tasks/daily",
                             headers={"X-Game-Key": os.getenv("GAME_ADMIN_PASSWORD") or ""},
                             json={"force_pick": args.force_pick},
                             timeout=900)
    print(response.status_code, response.text)
    response.raise_for_status()
except Exception as e:
    # The app emails failures that happen inside a run; this covers the app being unreachable
    print(f"Guess the Price run failed: {e}")
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from app.EmailHelper.EmailSender import send_email
    send_email("Guess the Price: scheduled task FAILED",
               os.getenv("GAME_ADMIN_EMAIL", "waichak.luk@gmail.com"),
               f"<p>The daily Guess the Price task could not complete.</p><pre>{e}</pre>")
    sys.exit(1)

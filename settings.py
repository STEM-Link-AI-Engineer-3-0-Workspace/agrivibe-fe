"""Settings, read once from .env in this folder. Variables already set in the environment win."""

import os

from dotenv import load_dotenv

load_dotenv()

API = os.getenv("AGRIVIBE_API", "http://127.0.0.1:8000")
# Session 2 uses the earlier, in-memory backend. The default remains the full-stack API.
BACKEND_MODE = os.getenv("AGRIVIBE_BACKEND_MODE", "fullstack")
if BACKEND_MODE not in {"fullstack", "lesson2"}:
    raise ValueError("AGRIVIBE_BACKEND_MODE must be fullstack or lesson2")
LESSON2_USER_ID = os.getenv("AGRIVIBE_LESSON2_USER_ID", "farmer-001")
# Seconds to wait for one chat turn. A decision question whose knowledge agent runs many searches
# has taken two minutes, and a timeout looks like a broken app.
TIMEOUT = float(os.getenv("AGRIVIBE_TIMEOUT", "180"))

# Who the backend acts for. The backend decides this from its own .env; this copy, kept in sync by
# hand, is only for the page and the log. It is never sent: the backend would not accept it anyway.
FARMER_ID = LESSON2_USER_ID if BACKEND_MODE == "lesson2" else os.getenv("FARMER_ID", "frm_7f3a9c2e")
FARMER_NAME = os.getenv("FARMER_NAME", "Nimal Perera")

# Shown on the empty chat; a click sends the question. The last three fail or stall on purpose.
SUGGESTIONS = [
    "Is my Minneriya paddy field stressed?",
    "Should I spray fungicide on my Minneriya field this week?",
    "What is the urea rate for Bg 352?",
    "Is field SL-PADDY-SAT-FAIL stressed?",
    "Has it rained much on field SL-PADDY-WEATHER-FAIL?",
    "Should I apply urea on field SL-PADDY-SLOW this week?",
]

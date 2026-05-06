import re
import datetime
from difflib import SequenceMatcher

# -----------------------------
# 1. Keyword Guard (Expanded + Fuzzy)
# -----------------------------
BANNED_KEYWORDS = [
    "hack", "bomb", "ddos", "sql injection",
    "bypass", "exploit", "malware", "trojan",
    "virus", "ransomware", "phish", "crack",
    "keylogger", "breach", "unauthorized access",
    "rootkit", "payload", "attack", "unauthenticated",
]

def fuzzy_match(word, text, threshold=0.8):
    \"\"\"Check if a word is approximately in text.\"\"\"
    text_words = re.findall(r"\w+", text.lower())
    for w in text_words:
        if SequenceMatcher(None, word.lower(), w).ratio() >= threshold:
            return True
    return False

def keyword_guard(text: str):
    for word in BANNED_KEYWORDS:
        if word.lower() in text.lower() or fuzzy_match(word, text):
            return False, f"Blocked keyword: {word}"
    return True, "OK"

# -----------------------------
# 2. Topic Restriction (Expanded)
# -----------------------------
ALLOWED_TOPICS = [
    "resume", "job", "skills", "experience", "qualification",
    "education", "employment", "career", "position",
    "role", "capabilities", "background", "portfolio"
]

def topic_guard(text: str):
    if len(text) > 20:  # allow normal sentences
        return True, "OK"
    if not any(topic in text.lower() for topic in ALLOWED_TOPICS):
        return False, "Out of allowed domain"
    return True, "OK"

# -----------------------------
# 3. Input Sanitization
# -----------------------------
def sanitize_input(text: str):
    text = re.sub(r"<.*?>", "", text)  # remove HTML tags
    text = text.replace("\n", " ").strip()
    text = re.sub(r"\s+", " ", text)  # collapse multiple spaces
    return text

# -----------------------------
# 4. Length Guard
# -----------------------------
def length_guard(text: str, max_len=1000):
    if len(text) > max_len:
        return False, f"Input too long ({len(text)} chars, max {max_len})"
    return True, "OK"

# -----------------------------
# 5. MASTER INPUT GUARD
# -----------------------------
def apply_input_guardrails(text: str):
    text = sanitize_input(text)

    checks = [
        keyword_guard,
        topic_guard,
        length_guard
    ]

    for check in checks:
        ok, msg = check(text)
        if not ok:
            log_guardrail("input", msg)
            return False, msg

    return True, text

# -----------------------------
# 6. OUTPUT GUARD (Expanded)
# -----------------------------
SENSITIVE_OUTPUT_KEYWORDS = [
    "password", "ssn", "credit card", "social security",
    "secret", "token", "private key", "api key", "credential"
]

def apply_output_guardrails(text: str):
    # Check for sensitive terms
    for word in SENSITIVE_OUTPUT_KEYWORDS:
        if word.lower() in text.lower():
            log_guardrail("output", f"Sensitive info detected: {word}")
            return False, f"Sensitive info detected: {word}"
    # Check for URLs that might be unsafe
    if re.search(r"http[s]?://\S+", text):
        log_guardrail("output", "Blocked URL detected")
        return False, "Blocked content: unsafe URL"
    return True, text

# -----------------------------
# 7. Logging for Guardrails (with timestamp)
# -----------------------------
def log_guardrail(event: str, status: str, thread_id=None):
    \"\"\"Log blocked or flagged events from guardrails with timestamp.\"\"\"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    thread_info = f"[{thread_id}]" if thread_id else ""
    with open("guardrails.log", "a", encoding="utf-8") as f:
        f.write(f"{timestamp} {thread_info} {event} -> {status}\n")

import re

EMAIL_REGEX = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
#PHONE_REGEX = re.compile(r"(?:\+91[\s-]?)?[6-9]\d{9}")
PHONE_REGEX = re.compile(r"\b\d{10}\b")
AADHAAR_REGEX = re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b")
URL_REGEX = re.compile(r"https?://[^\s]+")
PAN_REGEX = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b")
TOKEN_REGEX = re.compile(r"\b[a-zA-Z0-9_\-]{16,}\b")
import re

def detect_prompt_injection(text):
    dangerous_patterns = [
        r"(ignore\s+.*instructions?)",
        r"(disregard\s+previous\s+instructions?)",
        r"(you\s+are\s+now\s+.*)",
        r"(act\s+as\s+.*)",
        r"(forget\s+.*)",
        r"(pretend\s+to\s+be\s+.*)",
        r"(execute\s+this\s+code.*)",
        r"(system\s+prompt\s+is.*)",
        r"(instruction\s+override.*)",
        r"(end\s+prompt\s+here.*)",
        r"(reset\s+your\s+identity.*)",
    ]
    for pattern in dangerous_patterns:
        if re.search(pattern, text, flags=re.IGNORECASE):
            return True
    return False

sensitive_patterns = [
    # Financial and personal identifiers
    r"\bOTP\b",
    r"\bone[-\s]?time\s?password\b",
    r"\baccount\s+statement\b",
    r"\bIFSC\b",
    r"\baccount\s+number\b",
    r"\bpassword\b",
    r"\bKYC\b",
    r"\bverification\b",
    r"\btransaction\b",
    r"\bbalance\b",
    r"\bdebit\s+card\b",
    r"\bcredit\s+card\b",
    r"\bCVV\b",
    r"\bpincode\b",
    r"\bUPI\b",
    # Login & security phrases
    r"\blog\s*in\b",
    r"\bsign\s*in\b",
    r"\bclick\s+here\s+to\s+(login|verify|reset)",
    r"\bsecurity\s+code\b",
    r"\bconfirmation\s+code\b",
    r"reset\s+(your\s+)?password",
    r"verify\s+(your\s+)?email",
    # URLs with sensitive actions
    r"https?:\/\/[^\s]*?(login|signin|reset|verify)[^\s]*",
    # Suspicious security alerts
    r"your\s+account\s+(is\s+at\s+risk|has\s+been\s+compromised|needs\s+verification)",
    r"unauthorized\s+access\s+detected",
    r"update\s+your\s+credentials",
    # Direct login or verification language
    r"your\s+(login|verification|security)\s+code\s+is\s+\d{4,8}",
    r"enter\s+code\s+\d{4,8}",
    r"use\s+code\s+\d{4,8}\s+to\s+log\s+in",
    r"code:\s*\d{4,8}",
    # Common phrases from login flows
    r"sign\s*in\s+to\s+your\s+account",
    r"verify\s+your\s+email\s+address",
    r"click\s+to\s+(sign\s*in|log\s*in|verify)",
    # Known login/code email sources
    r"no[-]?reply@(amazon|google|github|microsoft|apple)\.com",
    r"security@.*",
    r"noreply@.*\.login\..*",
]

def mail_filter(body):
    is_safe = "pass"
    # Check for sensitive content
    for pattern in sensitive_patterns:
        if re.search(pattern, body, re.IGNORECASE):
            is_safe = "block"
            break
    # Check for prompt injection
    if detect_prompt_injection(body):
        is_safe = "block"
    return is_safe
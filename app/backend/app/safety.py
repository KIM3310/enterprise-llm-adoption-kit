import re
from typing import List

REFUSAL_MESSAGE = "Request refused due to safety policy."

PATTERNS: List[re.Pattern] = [
    re.compile(r"(?i)(exfiltrat|leak|steal|dump|reveal).*(secrets?|credentials?|tokens?|keys?|passwords?)"),
    re.compile(r"(?i)phishing|credential\s+harvesting"),
    re.compile(r"(?i)passwords?\s+from\s+(database|db)|/etc/shadow"),
    re.compile(r"(?i)ssn|social\s+security|credit\s+card|raw\s+pii"),
    re.compile(r"(?i)malware|ransomware|backdoor"),
    re.compile(r"(?i)prompt\s+injection|ignore\s+previous\s+instructions|override\s+system"),
    re.compile(r"(?i)disable\s+audit|evade\s+monitoring|hide\s+actions\s+from\s+logs"),
    re.compile(r"(?i)bypass\s+(the\s+)?(rbac|access\s+controls|mfa|allowlist|rate\s+limit|tool\s+allowlist)"),
    re.compile(r"(?i)exploit|hack|brute[-\s]?force|escalate\s+privilege"),
    re.compile(r"(?i)impersonate\s+another\s+user|steal\s+session\s+tokens"),
    re.compile(r"(?i)reveal\s+admin\s+password|jwt\s+secret|private\s+key|connection\s+strings?"),
    re.compile(r"(?i)api\s+keys?|oauth\s+tokens?"),
    re.compile(r"(?i)environment\s+variables|env\s+vars"),
    re.compile(r"(?i)confidential\s+handover|ignore\s+policy"),
    re.compile(r"(?i)emails?\s+and\s+phone\s+numbers|employee\s+emails"),
    re.compile(r"(?i)override\s+redaction|unmask\s+pii"),
    re.compile(r"(?i)runbook\s+secrets|security\s+policies|admin\s+docs"),
    re.compile(r"(?i)output\s+secrets|hidden\s+endpoints"),
    re.compile(r"(?i)evade\s+(security\s+)?monitoring|evade\s+mfa"),
    re.compile(r"(?i)disable\s+rate\s+limit(ing)?|audit\s+retention"),
    re.compile(r"(?i)scrape\s+private\s+data|leak\s+customer\s+data"),
    re.compile(r"(?i)passwords?\s+from\s+memory|vector\s+database"),
]


def should_refuse(text: str) -> bool:
    if not text:
        return False
    for pattern in PATTERNS:
        if pattern.search(text):
            return True
    return False

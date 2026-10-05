#!/usr/bin/env python3
"""Page content test for the portfolio site.

Asserts that each built page actually contains its expected content.
Run AFTER `hugo` so it tests the real output.

Usage:  python3 scripts/test_pages.py
Exit 0 = all pages pass, 1 = failures found.
"""
import html
import os
import re
import sys

PUB = "public"

# page path (relative to public/, without index.html) -> list of required substrings
EXPECTED = {
    "": [
        "Md. Mahfuj Hasan",
        "Cybersecurity Engineer & IS Auditor",
        "Professional Snapshot",
        "Areas of Expertise",
        "Experience Highlights",
        "Featured Projects",
        "Certifications",
        "Achievements",
        "Let's Connect",
    ],
    "about": [
        "Professional Profile",
        "Quick Facts",
        "Core Values",
        "Integrity",
        "Continuous Learning",
        "Download CV",
        "Dhaka, Bangladesh",
    ],
    "skills": [
        "IT Audit & Assurance",
        "Technology Risk & Governance",
        "Cybersecurity",
        "Banking Technology",
        "AI & Automation",
        "Tools & Technologies",
        "IT General Controls (ITGC)",
        "Vulnerability Assessment & Penetration Testing",
    ],
    "contact": [
        "Let's Connect",
        "mahfujhasanlingkon@gmail.com",
        "linkedin.com/in/mahfuj-hasan",
        "github.com/mahfuj-lingkon",
        "Dhaka, Bangladesh",
        "Available for remote collaboration worldwide",
    ],
    "experience": [
        "Senior Officer, IS Audit",
        "City Bank PLC",
        "Advanced Cybersecurity Engineer",
        "ITCOM",
        "Assistant Manager, IT Audit",
        "ACNABIN",
        "Plan and execute IS audit engagements",
    ],
    "education": [
        "B.Sc. in Software Engineering",
        "Daffodil International University",
        "Higher Secondary Certificate",
        "Secondary School Certificate",
        "Training & Courses",
    ],
    "certifications": [
        "Certified Information Systems Auditor",
        "ISO/IEC 27001",
        "Certified Ethical Hacker",
        "ISACA",
    ],
    "projects": [
        "ISO/IEC 27001 Compliance Checker",
        "BDCTF",
        "Restaurant Management System",
        "Contact Management System",
    ],
    "achievements": [
        "CISA",
        "ISO 27001",
        "Senior Officer",
    ],
    "articles": [
        "The Role of IS Auditors in the Age of AI",
        "Key Considerations for Banking IT General Controls",
        "Getting Started with Cybersecurity Auditing",
    ],
}

# Standalone pages generated at a non-`/dir/index.html` location.
STANDALONE = {
    "404.html": ["404", "not found"],
}

# Detail pages that must render their own frontmatter fields.
DETAIL_PAGES = [
    ("experience/senior-officer-is-audit", ["City Bank PLC", "Jan 2026", "Present"]),
    ("experience/advanced-cybersecurity-engineer", ["ITCOM"]),
    ("experience/assistant-manager-it-audit--consultancy", ["ACNABIN"]),
    ("experience/information-technology-auditor", ["ACNABIN"]),
    ("experience/officer", ["Eastern Bank"]),
    ("education/bsc-in-software-engineering", ["Daffodil International University"]),
    ("education/higher-secondary-certificate-hsc", ["Gaibandha"]),
    ("education/secondary-school-certificate-ssc", ["Gaibandha"]),
    ("certifications/cisa", ["ISACA"]),
    ("certifications/ceh", ["EC-Council"]),
    ("certifications/iso-iec-27001-lead-auditor", ["27001"]),
    ("projects/iso-iec-27001-compliance-checker", ["Python"]),
    ("projects/bdctf---online-ctf-platform", ["CTF"]),
    ("achievements/cisa-certification-achieved", ["CISA"]),
    ("articles/the-role-of-is-auditors-in-the-age-of-ai", ["AI"]),
]

# Patterns that must NOT appear anywhere (rendering bugs).
FORBIDDEN = [
    r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \+0000 UTC",  # raw time.Time in output
    r"<no value>",
    r"\{\{",  # unrendered template action
]

# Pages that are intentionally allowed to be short.
SHORT_OK = {"admin"}


def body_text(path):
    """Extract visible body text (nav/footer/script stripped) from a built page."""
    with open(path, encoding="utf-8", errors="ignore") as fh:
        raw = fh.read()
    m = re.search(r"<body[^>]*>(.*?)</body>", raw, re.S | re.I)
    b = m.group(1) if m else raw
    b = re.sub(r"<script.*?</script>", " ", b, flags=re.S | re.I)
    b = re.sub(r"<style.*?</style>", " ", b, flags=re.S | re.I)
    b = re.sub(r"<(nav|header|footer)\b.*?</\1>", " ", b, flags=re.S | re.I)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", b))).strip()


def main():
    failures = []
    checked = 0

    # --- section / standalone pages ---
    for page, needles in EXPECTED.items():
        rel = os.path.join(PUB, page, "index.html") if page else os.path.join(PUB, "index.html")
        if not os.path.exists(rel):
            failures.append(f"MISSING PAGE: /{page}/ -> {rel}")
            continue
        text = body_text(rel)
        checked += 1
        for needle in needles:
            if needle.lower() not in text.lower():
                failures.append(f"/{page}/ missing content: {needle!r}")

    # --- standalone pages ---
    for page, needles in STANDALONE.items():
        rel = os.path.join(PUB, page)
        if not os.path.exists(rel):
            failures.append(f"MISSING PAGE: {page} -> {rel}")
            continue
        text = body_text(rel)
        checked += 1
        for needle in needles:
            if needle.lower() not in text.lower():
                failures.append(f"{page} missing content: {needle!r}")

    # --- detail pages ---
    for page, needles in DETAIL_PAGES:
        rel = os.path.join(PUB, page, "index.html")
        if not os.path.exists(rel):
            failures.append(f"MISSING PAGE: /{page}/ -> {rel}")
            continue
        text = body_text(rel)
        checked += 1
        for needle in needles:
            if needle.lower() not in text.lower():
                failures.append(f"/{page}/ missing content: {needle!r}")

    # --- global forbidden patterns ---
    for root, _dirs, files in os.walk(PUB):
        for fn in files:
            if not fn.endswith(".html"):
                continue
            p = os.path.join(root, fn)
            rel = os.path.relpath(p, PUB)
            with open(p, encoding="utf-8", errors="ignore") as fh:
                raw = fh.read()
            checked += 1
            for pat in FORBIDDEN:
                if re.search(pat, raw):
                    failures.append(f"{rel} contains forbidden pattern {pat!r}")

    # --- thin page report ---
    thin = []
    for root, _dirs, files in os.walk(PUB):
        for fn in files:
            if not fn.endswith(".html"):
                continue
            p = os.path.join(root, fn)
            rel = os.path.relpath(p, PUB)
            key = rel.split(os.sep)[0].replace("index.html", "")
            if key in SHORT_OK:
                continue
            t = body_text(p)
            if len(t) < 300:
                thin.append((rel, len(t)))

    print(f"Pages/assertions checked: {checked}")
    if thin:
        print("\nThin pages (<300 chars of body text):")
        for rel, n in sorted(thin, key=lambda x: x[1]):
            print(f"  {n:>5}  {rel}")

    if failures:
        print(f"\n{len(failures)} FAILURE(S):")
        for f in failures:
            print(f"  ✗ {f}")
        return 1

    print("\n✓ All page content checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

from pathlib import Path
from typing import List

BASE_DIR = Path(__file__).resolve().parents[3]
DECK_DIR = BASE_DIR / "docs" / "sales" / "deck"
TALK_TRACK = BASE_DIR / "docs" / "sales" / "talk_track_exec.md"


def _extract_sections(lines: List[str]) -> List[tuple]:
    sections = []
    current_title = "Overview"
    current_body: List[str] = []
    for line in lines:
        if line.startswith("#"):
            if current_body:
                sections.append((current_title, current_body))
            current_title = line.lstrip("#").strip()
            current_body = []
        elif line.strip():
            current_body.append(line.strip())
    if current_body:
        sections.append((current_title, current_body))
    return sections


def build_html() -> str:
    lines = TALK_TRACK.read_text(encoding="utf-8").splitlines()
    sections = _extract_sections(lines)

    slide_html = []
    for title, body in sections:
        bullets = "".join([f"<li>{item}</li>" for item in body if not item.startswith("```")])
        slide_html.append(
            f"<section class='slide'>"
            f"<h2>{title}</h2>"
            f"<ul>{bullets}</ul>"
            f"</section>"
        )

    html = f"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Exec Deck</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; background: #0f172a; color: #e2e8f0; }}
    .slide {{ page-break-after: always; padding: 60px; min-height: 720px; }}
    h1, h2 {{ color: #f97316; }}
    ul {{ line-height: 1.6; font-size: 20px; }}
  </style>
</head>
<body>
  <section class="slide">
    <h1>Enterprise LLM Adoption Kit (Korea)</h1>
    <p>Executive PoC Deck</p>
  </section>
  {"".join(slide_html)}
</body>
</html>
"""
    return html


def generate_pdf(output_path: Path) -> Path:
    html = build_html()
    DECK_DIR.mkdir(parents=True, exist_ok=True)
    html_path = DECK_DIR / "exec_deck.html"
    html_path.write_text(html, encoding="utf-8")

    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        print(f"Playwright not available. HTML written: {html_path}")
        return html_path

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(html_path.as_uri())
        page.pdf(path=str(output_path), print_background=True, format="A4")
        browser.close()
    return output_path


def main() -> None:
    output = DECK_DIR / "exec_deck.pdf"
    out = generate_pdf(output)
    print(f"Exec deck written: {out}")


if __name__ == "__main__":
    main()

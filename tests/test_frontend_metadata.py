from pathlib import Path
from xml.etree import ElementTree


ROOT_DIR = Path(__file__).resolve().parents[1]
FRONTEND_INDEX = ROOT_DIR / "app/frontend/index.html"
PUBLIC_DIR = ROOT_DIR / "app/frontend/public"
PRODUCTION_SMOKE = ROOT_DIR / "scripts/smoke_production.sh"
SITE_ORIGIN = "https://enterprise-llm-kit.pages.dev"
POLICY_SURFACES = {
    "about": "<h1>About LLM Adoption Atelier</h1>",
    "privacy": "<h1>Privacy Policy</h1>",
    "terms": "<h1>Terms of Service</h1>",
    "contact": "<h1>Contact</h1>",
    "compliance": "<h1>Compliance & Quality</h1>",
}


def test_frontend_index_includes_architecture_surface_metadata():
    content = FRONTEND_INDEX.read_text()

    assert 'name="description"' in content
    assert f'<link rel="canonical" href="{SITE_ORIGIN}/"' in content
    assert 'property="og:title"' in content
    assert 'property="og:description"' in content
    assert f'property="og:url" content="{SITE_ORIGIN}/"' in content
    assert 'property="og:image"' in content
    assert 'property="og:image:alt"' in content
    assert 'name="twitter:title"' in content
    assert 'name="twitter:description"' in content
    assert 'name="twitter:image"' in content
    assert "summary-pack.svg" in content


def test_public_policy_pages_have_unique_content_and_canonical_urls():
    for route, heading in POLICY_SURFACES.items():
        content = (PUBLIC_DIR / f"{route}.html").read_text(encoding="utf-8")

        assert heading in content
        assert 'name="description"' in content
        assert 'name="robots" content="index,follow"' in content
        assert f'<link rel="canonical" href="{SITE_ORIGIN}/{route}"' in content


def test_search_discovery_files_cover_the_public_policy_surface():
    robots = (PUBLIC_DIR / "robots.txt").read_text(encoding="utf-8")
    assert "User-agent: *" in robots
    assert f"Sitemap: {SITE_ORIGIN}/sitemap.xml" in robots
    assert "Mediapartners-Google" not in robots

    sitemap = ElementTree.parse(PUBLIC_DIR / "sitemap.xml")
    namespace = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    locations = {element.text for element in sitemap.findall("s:url/s:loc", namespace)}
    expected = (
        {f"{SITE_ORIGIN}/"}
        | {f"{SITE_ORIGIN}/{route}" for route in POLICY_SURFACES}
        | {
            f"{SITE_ORIGIN}/{route}"
            for route in (
                "guide",
                "architecture",
                "verification",
                "publisher",
            )
        }
    )

    assert locations == expected


def test_production_smoke_rejects_spa_fallbacks_without_requiring_ads_txt():
    smoke = PRODUCTION_SMOKE.read_text(encoding="utf-8")

    assert "/ads.txt" not in smoke
    assert "%{content_type}" in smoke
    assert "%{url_effective}" in smoke
    for route, heading in POLICY_SURFACES.items():
        assert f'"/{route}"' in smoke
        assert heading in smoke
    assert "/robots.txt" in smoke
    assert "/sitemap.xml" in smoke

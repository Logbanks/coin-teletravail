#!/usr/bin/env python
"""Génère le site statique dans le dossier dist/ à partir de content/.

Usage : python scripts/build.py
Aucune dépendance autre que la bibliothèque `markdown`.
"""

from __future__ import annotations

import datetime as dt
import html
import json
import re
import shutil
import sys
import time
import unicodedata
import urllib.parse
from pathlib import Path

import markdown

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
ARTICLES_DIR = CONTENT / "articles"
PAGES_DIR = CONTENT / "pages"
TEMPLATES = ROOT / "templates"
STATIC = ROOT / "static"
DIST = ROOT / "dist"

CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
SITE_URL = CONFIG["url"].rstrip("/")
# Chemin de base pour les liens internes (ex. "/coin-teletravail" sur GitHub Pages
# sans domaine personnalisé, "" avec un domaine).
BASE_PATH = urllib.parse.urlparse(SITE_URL).path.rstrip("/")

MD = markdown.Markdown(
    extensions=["extra", "toc", "sane_lists", "smarty"],
    extension_configs={"toc": {"toc_depth": "2-3"}, "smarty": {"smart_angled_quotes": False}},
    output_format="html5",
)


# ---------------------------------------------------------------------------
# Utilitaires
# ---------------------------------------------------------------------------

def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return value or "sans-titre"


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Lit un en-tête YAML minimal (clé: valeur, une par ligne)."""
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    meta: dict[str, str] = {}
    for line in parts[1].splitlines():
        if ":" in line and not line.strip().startswith("#"):
            key, _, val = line.partition(":")
            meta[key.strip()] = val.strip().strip('"').strip("'")
    return meta, parts[2].lstrip("\n")


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def read_template(name: str) -> str:
    return (TEMPLATES / name).read_text(encoding="utf-8")


def render(template: str, **values: str) -> str:
    for key, val in values.items():
        template = template.replace("{{" + key + "}}", val)
    return template


def fmt_date(value: str) -> str:
    d = dt.date.fromisoformat(value)
    mois = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
            "août", "septembre", "octobre", "novembre", "décembre"]
    return f"{d.day} {mois[d.month - 1]} {d.year}"


# ---------------------------------------------------------------------------
# Liens d'affiliation et fiches produit
# ---------------------------------------------------------------------------

def amazon_link(search: str = "", asin: str = "") -> str:
    domain = CONFIG["amazon_domain"]
    tag = CONFIG["amazon_tag"]
    if asin:
        return f"https://{domain}/dp/{urllib.parse.quote(asin)}?tag={urllib.parse.quote(tag)}"
    query = urllib.parse.urlencode({"k": search, "tag": tag})
    return f"https://{domain}/s?{query}"


PRODUCT_RE = re.compile(r"\[\[produit:(.*?)\]\]", re.DOTALL)


def product_card(match: re.Match) -> str:
    """Transforme [[produit: Titre | recherche=... | prix=... | note=... | asin=...]] en fiche HTML."""
    raw = match.group(1)
    fields = [f.strip() for f in raw.split("|")]
    title = fields[0]
    opts: dict[str, str] = {}
    for f in fields[1:]:
        if "=" in f:
            k, _, v = f.partition("=")
            opts[k.strip().lower()] = v.strip()
    link = opts.get("lien") or amazon_link(search=opts.get("recherche", title), asin=opts.get("asin", ""))
    price = f'<p class="product-price">Budget indicatif : {esc(opts["prix"])}</p>' if opts.get("prix") else ""
    note = f'<p class="product-note">{esc(opts["note"])}</p>' if opts.get("note") else ""
    return (
        '\n<div class="product-card">\n'
        f'  <p class="product-title">{esc(title)}</p>\n'
        f"  {price}\n  {note}\n"
        f'  <a class="btn" href="{esc(link)}" rel="sponsored nofollow noopener" target="_blank">🛒 Voir les modèles sur Amazon</a>\n'
        "</div>\n"
    )


def convert_markdown(text: str) -> tuple[str, str]:
    """Retourne (html, table des matières)."""
    text = PRODUCT_RE.sub(product_card, text)
    MD.reset()
    body = MD.convert(text)
    toc = getattr(MD, "toc", "") or ""
    # Tout lien Markdown vers Amazon devient un lien sponsorisé, ouvert dans un nouvel onglet.
    body = re.sub(r'<a href="(https?://(?:www\.)?amazon\.[a-z.]+/[^"]*)">',
                  r'<a href="" rel="sponsored nofollow noopener" target="_blank">', body)
    # Liens internes écrits « /mon-article/ » : préfixe du chemin de base.
    if BASE_PATH:
        body = re.sub(r'href="/(?!/)', f'href="{BASE_PATH}/', body)
    return body, toc


# ---------------------------------------------------------------------------
# Chargement du contenu
# ---------------------------------------------------------------------------

IMG_DIR = STATIC / "img"


def category_image(category_slug: str) -> str:
    """Chemin public de l'illustration d'une catégorie, ou chaîne vide."""
    for ext in ("jpg", "png", "webp"):
        if (IMG_DIR / "categories" / f"{category_slug}.{ext}").exists():
            return f"{BASE_PATH}/static/img/categories/{category_slug}.{ext}"
    return ""


def hero_image() -> str:
    for ext in ("jpg", "png", "webp"):
        if (IMG_DIR / f"accueil.{ext}").exists():
            return f"{BASE_PATH}/static/img/accueil.{ext}"
    return ""


def load_articles() -> list[dict]:
    articles = []
    for path in sorted(ARTICLES_DIR.glob("*.md")):
        meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
        if meta.get("brouillon", "").lower() in {"oui", "true", "1"}:
            continue
        if "title" not in meta or "date" not in meta:
            print(f"[avertissement] {path.name} : en-tête incomplet (title/date), ignoré", file=sys.stderr)
            continue
        slug = meta.get("slug") or slugify(re.sub(r"^\d{4}-\d{2}-\d{2}-", "", path.stem))
        category = meta.get("category", "Conseils")
        html_body, toc = convert_markdown(body)
        articles.append({
            "title": meta["title"],
            "description": meta.get("description", ""),
            "date": meta["date"],
            "updated": meta.get("updated", meta["date"]),
            "category": category,
            "category_slug": slugify(category),
            "slug": slug,
            "url": f"{SITE_URL}/{slug}/",
            "path": f"{BASE_PATH}/{slug}/",
            "html": html_body,
            "toc": toc,
            "image": (f"{BASE_PATH}/{meta['image'].lstrip('/')}" if meta.get("image") else category_image(slugify(category))),
            "linkedin": meta.get("linkedin", "").replace("\\n", "\n"),
            "pinterest": meta.get("pinterest", ""),
        })
    articles.sort(key=lambda a: (a["date"], a["title"]), reverse=True)
    return articles


def load_pages() -> list[dict]:
    pages = []
    for path in sorted(PAGES_DIR.glob("*.md")):
        meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
        slug = meta.get("slug") or slugify(path.stem)
        html_body, _ = convert_markdown(body)
        pages.append({
            "title": meta.get("title", path.stem),
            "description": meta.get("description", CONFIG["description"]),
            "slug": slug,
            "url": f"{SITE_URL}/{slug}/",
            "html": html_body,
        })
    return pages


# ---------------------------------------------------------------------------
# Rendu
# ---------------------------------------------------------------------------

def nav_html(categories: list[tuple[str, str]], active: str = "") -> str:
    items = []
    for name, slug in categories:
        cls = ' class="active"' if slug == active else ""
        items.append(f'<a{cls} href="{BASE_PATH}/categorie/{slug}/">{esc(name)}</a>')
    return "\n        ".join(items)


def card_html(article: dict, featured: bool = False) -> str:
    cls = "card featured" if featured else "card"
    img = f'<a class="card-img" href="{article["path"]}" aria-hidden="true" tabindex="-1"><img src="{article["image"]}" alt="" loading="lazy"></a>\n' if article["image"] else ""
    return (
        f'<li class="{cls}">\n{img}<div class="card-body">\n'
        f'  <p class="meta"><a href="{BASE_PATH}/categorie/{article["category_slug"]}/">{esc(article["category"])}</a> · {fmt_date(article["date"])}</p>\n'
        f'  <h2 class="card-title"><a href="{article["path"]}">{esc(article["title"])}</a></h2>\n'
        f'  <p>{esc(article["description"])}</p>\n'
        "</div></li>"
    )


def page_shell(base: str, *, title: str, description: str, canonical: str, content: str,
               nav: str, og_type: str = "website", json_ld: str = "", image: str = "") -> str:
    og_image = f'<meta property="og:image" content="{esc(SITE_URL + image[len(BASE_PATH):])}">' if image else ""
    adsense = ""
    if CONFIG.get("adsense_client"):
        adsense = (f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js'
                   f'?client={esc(CONFIG["adsense_client"])}" crossorigin="anonymous"></script>')
    return render(
        base,
        og_image=og_image,
        adsense=adsense,
        privacy_link=(' · <a href="#" onclick="if(window.googlefc){googlefc.showRevocationMessage();}return false;">Paramètres de confidentialité</a>' if adsense else ""),
        title=esc(title),
        description=esc(description),
        canonical=esc(canonical),
        og_type=og_type,
        site_name=esc(CONFIG["site_name"]),
        base=BASE_PATH,
        nav=nav,
        content=content,
        json_ld=json_ld,
        year=str(dt.date.today().year),
    )


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build() -> None:
    # OneDrive ou l'explorateur Windows verrouillent parfois un dossier : on réessaie.
    for attempt in range(5):
        if not DIST.exists():
            break
        try:
            shutil.rmtree(DIST)
        except PermissionError:
            time.sleep(0.5 * (attempt + 1))
    DIST.mkdir(parents=True, exist_ok=True)
    shutil.copytree(STATIC, DIST / "static", dirs_exist_ok=True)
    (DIST / ".nojekyll").write_text("", encoding="utf-8")
    # Fichiers à servir tels quels à la racine du site (vérifications Google, Bing, etc.)
    racine = ROOT / "racine"
    if racine.is_dir():
        for f in racine.iterdir():
            if f.is_file():
                shutil.copy2(f, DIST / f.name)

    # Fichier ads.txt exigé par Google AdSense (identifiant éditeur = partie après "ca-")
    if CONFIG.get("adsense_client"):
        pub = CONFIG["adsense_client"].removeprefix("ca-")
        (DIST / "ads.txt").write_text(f"google.com, {pub}, DIRECT, f08c47fec0942fa0" + chr(10), encoding="utf-8")

    host = urllib.parse.urlparse(SITE_URL).hostname or ""
    if host and not host.endswith("github.io"):
        (DIST / "CNAME").write_text(host + "\n", encoding="utf-8")

    base = read_template("base.html")
    articles = load_articles()
    pages = load_pages()

    categories: dict[str, str] = {}
    for a in articles:
        categories.setdefault(a["category"], a["category_slug"])
    cat_list = sorted(categories.items(), key=lambda kv: kv[0].lower())
    nav = nav_html(cat_list)

    # --- Accueil ---------------------------------------------------------
    home_articles = articles[: CONFIG.get("articles_on_home", 12)]
    cards = "\n".join(card_html(a, featured=(i == 0)) for i, a in enumerate(home_articles))
    hero = hero_image()
    hero_img = f'<img class="hero-img" src="{hero}" alt="Un coin bureau à domicile bien aménagé" width="576" height="288">' if hero else ""
    home = (
        f'<section class="hero{" hero-with-img" if hero else ""}">\n'
        '  <div class="hero-text">\n'
        f'    <h1>{esc(CONFIG["tagline"])}</h1>\n'
        f'    <p>{esc(CONFIG["description"])}</p>\n'
        "  </div>\n"
        f"  {hero_img}\n"
        "</section>\n"
        f'<ul class="card-list">\n{cards}\n</ul>'
    )
    if len(articles) > len(home_articles):
        home += f'<p><a href="{BASE_PATH}/articles/">Voir tous les articles →</a></p>'
    site_ld = json.dumps({
        "@context": "https://schema.org", "@type": "WebSite",
        "name": CONFIG["site_name"], "url": SITE_URL + "/", "inLanguage": "fr",
    }, ensure_ascii=False)
    write(DIST / "index.html", page_shell(
        base, title=f'{CONFIG["site_name"]} — {CONFIG["tagline"]}', description=CONFIG["description"],
        canonical=SITE_URL + "/", content=home, nav=nav, image=hero,
        json_ld=f'<script type="application/ld+json">{site_ld}</script>',
    ))

    # --- Liste complète ---------------------------------------------------
    all_cards = "\n".join(card_html(a) for a in articles)
    write(DIST / "articles" / "index.html", page_shell(
        base, title=f'Tous les articles — {CONFIG["site_name"]}', description=CONFIG["description"],
        canonical=f"{SITE_URL}/articles/", nav=nav,
        content=f'<section class="hero"><h1>Tous les articles</h1></section>\n<ul class="card-list">\n{all_cards}\n</ul>',
    ))

    # --- Catégories -------------------------------------------------------
    for name, slug in cat_list:
        cat_articles = [a for a in articles if a["category_slug"] == slug]
        cards = "\n".join(card_html(a) for a in cat_articles)
        cat_img = category_image(slug)
        cat_banner = f'<img class="hero-img" src="{cat_img}" alt="" width="576" height="384">' if cat_img else ""
        n = len(cat_articles)
        write(DIST / "categorie" / slug / "index.html", page_shell(
            base, title=f'{name} — {CONFIG["site_name"]}',
            description=f'Tous nos guides et conseils dans la rubrique {name}.',
            canonical=f"{SITE_URL}/categorie/{slug}/", nav=nav_html(cat_list, active=slug), image=cat_img,
            content=f'<section class="hero{" hero-with-img" if cat_img else ""}"><div class="hero-text"><h1>{esc(name)}</h1><p>{n} article{"s" if n > 1 else ""}</p></div>{cat_banner}</section>\n<ul class="card-list">\n{cards}\n</ul>',
        ))

    # --- Articles ---------------------------------------------------------
    for a in articles:
        related = [r for r in articles if r["category_slug"] == a["category_slug"] and r["slug"] != a["slug"]][:3]
        if len(related) < 3:
            related += [r for r in articles if r["slug"] != a["slug"] and r not in related][: 3 - len(related)]
        related_html = ""
        if related:
            items = "\n".join(f'<li><a href="{r["path"]}">{esc(r["title"])}</a></li>' for r in related)
            related_html = f'<section class="article-footer"><h2>À lire ensuite</h2><ul>\n{items}\n</ul></section>'
        article_ld = json.dumps({
            "@context": "https://schema.org", "@type": "Article",
            "headline": a["title"], "description": a["description"],
            "datePublished": a["date"], "dateModified": a["updated"],
            "inLanguage": "fr", "mainEntityOfPage": a["url"],
            "author": {"@type": "Organization", "name": CONFIG["author"]},
            "publisher": {"@type": "Organization", "name": CONFIG["site_name"]},
        }, ensure_ascii=False)
        content = (
            '<article>\n'
            '  <header class="article-header">\n'
            f'    <p class="meta"><a href="{BASE_PATH}/categorie/{a["category_slug"]}/">{esc(a["category"])}</a> · Publié le {fmt_date(a["date"])}</p>\n'
            f'    <h1>{esc(a["title"])}</h1>\n'
            f'    <p class="lead">{esc(a["description"])}</p>\n'
            "  </header>\n"
            + (f'  <img class="article-img" src="{a["image"]}" alt="" width="576" height="384">\n' if a["image"] else "")
            +
            '  <p class="notice">Cet article contient des liens d\'affiliation Amazon. Si vous achetez via ces liens, le site touche une petite commission, sans surcoût pour vous. Nos conseils restent indépendants.</p>\n'
            f'  <div class="article-body">\n{a["html"]}\n  </div>\n'
            f"  {related_html}\n"
            "</article>"
        )
        write(DIST / a["slug"] / "index.html", page_shell(
            base, title=f'{a["title"]} — {CONFIG["site_name"]}', description=a["description"],
            canonical=a["url"], nav=nav_html(cat_list, active=a["category_slug"]), content=content, image=a["image"],
            og_type="article", json_ld=f'<script type="application/ld+json">{article_ld}</script>',
        ))

    # --- Pages statiques ---------------------------------------------------
    for p in pages:
        content = f'<article><header class="article-header"><h1>{esc(p["title"])}</h1></header><div class="article-body">{p["html"]}</div></article>'
        write(DIST / p["slug"] / "index.html", page_shell(
            base, title=f'{p["title"]} — {CONFIG["site_name"]}', description=p["description"],
            canonical=p["url"], nav=nav, content=content,
        ))

    # --- Sitemap, robots, flux RSS ------------------------------------------
    urls = [(SITE_URL + "/", dt.date.today().isoformat())]
    urls += [(a["url"], a["updated"]) for a in articles]
    urls += [(f"{SITE_URL}/categorie/{slug}/", articles[0]["date"] if articles else dt.date.today().isoformat()) for _, slug in cat_list]
    urls += [(p["url"], dt.date.today().isoformat()) for p in pages]
    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sitemap += [f"  <url><loc>{esc(u)}</loc><lastmod>{d}</lastmod></url>" for u, d in urls]
    sitemap.append("</urlset>\n")
    write(DIST / "sitemap.xml", "\n".join(sitemap))
    write(DIST / "robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n")

    def image_abs(a: dict) -> str:
        return SITE_URL + a["image"][len(BASE_PATH):] if a["image"] else ""

    def rss_feed(items: list[dict], title_suffix: str, text_of) -> str:
        """Construit un flux RSS 2.0 ; text_of(article) donne le texte de <description>."""
        out = []
        for a in items:
            pub = dt.datetime.combine(dt.date.fromisoformat(a["date"]), dt.time(8, 0), tzinfo=dt.timezone.utc)
            img = image_abs(a)
            enclosure = ""
            if img:
                local = DIST / a["image"][len(BASE_PATH) + 1:]
                size = local.stat().st_size if local.exists() else 0
                mime = "image/png" if img.endswith(".png") else "image/jpeg"
                enclosure = f'      <enclosure url="{esc(img)}" length="{size}" type="{mime}"/>\n'
            out.append(
                "    <item>\n"
                f"      <title>{esc(a['title'])}</title>\n"
                f"      <link>{esc(a['url'])}</link>\n"
                f"      <guid isPermaLink=\"true\">{esc(a['url'])}</guid>\n"
                f"      <pubDate>{pub.strftime('%a, %d %b %Y %H:%M:%S +0000')}</pubDate>\n"
                f"      <category>{esc(a['category'])}</category>\n"
                f"      <description>{esc(text_of(a))}</description>\n"
                + enclosure +
                "    </item>"
            )
        return (
            '<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0">\n  <channel>\n'
            f"    <title>{esc(CONFIG['site_name'] + title_suffix)}</title>\n    <link>{esc(SITE_URL)}/</link>\n"
            f"    <description>{esc(CONFIG['description'])}</description>\n    <language>fr</language>\n"
            + "\n".join(out) + "\n  </channel>\n</rss>\n"
        )

    # Flux pour les lecteurs
    write(DIST / "feed.xml", rss_feed(articles[:20], "", lambda a: a["description"]))
    # Flux pour l'automatisation LinkedIn : description = texte du post, lien ajouté à la fin
    write(DIST / "feed-linkedin.xml", rss_feed(
        [a for a in articles[:20] if a["linkedin"]], " — LinkedIn",
        lambda a: a["linkedin"].rstrip() + "\n\n" + a["url"]))
    # Flux pour l'automatisation Pinterest : description = texte de l'épingle, image en enclosure
    write(DIST / "feed-pinterest.xml", rss_feed(
        [a for a in articles[:20] if a["pinterest"] and a["image"]], " — Pinterest",
        lambda a: a["pinterest"]))

    print(f"Site généré : {len(articles)} articles, {len(cat_list)} catégories, {len(pages)} pages -> {DIST}")


if __name__ == "__main__":
    build()

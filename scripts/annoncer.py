#!/usr/bin/env python
"""Prévient Make (webhook) qu'un article vient d'être mis en ligne.

Make reçoit un JSON prêt à publier et poste aussitôt sur les réseaux.

Usage : python scripts/annoncer.py [nom-du-fichier.md]
        Sans argument : annonce l'article le plus récent.

Variable d'environnement : MAKE_WEBHOOK_URL (adresse du webhook Make).
Si elle est absente, le script ne fait rien et sort sans erreur.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build  # noqa: E402  (réutilise la configuration et les fonctions du générateur)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def linkedin_ltf(text: str) -> str:
    """Format « little Text Format » de l'API LinkedIn (identique à build.py)."""
    reserved = "\\|{}@[]()<>*_~"
    out = "".join("\\" + ch if ch in reserved else ch for ch in text)
    out = re.sub(r"#(\w+)", lambda m: "{hashtag|\\#|" + m.group(1) + "}", out)
    return out


def main() -> int:
    webhook = os.environ.get("MAKE_WEBHOOK_URL", "").strip()
    if not webhook:
        print("MAKE_WEBHOOK_URL absent : aucune annonce envoyée.")
        return 0

    articles_dir = build.ARTICLES_DIR
    if len(sys.argv) > 1 and sys.argv[1].strip():
        path = articles_dir / sys.argv[1].strip()
    else:
        path = max(articles_dir.glob("*.md"), key=lambda p: p.name)
    if not path.exists():
        print(f"Article introuvable : {path.name}", file=sys.stderr)
        return 1

    meta, _ = build.parse_frontmatter(path.read_text(encoding="utf-8"))
    slug = meta.get("slug") or build.slugify(re.sub(r"^\d{4}-\d{2}-\d{2}-", "", path.stem))
    url = f"{build.SITE_URL}/{slug}/"
    category = meta.get("category", "Conseils")
    image_path = build.category_image(build.slugify(category))
    image = build.SITE_URL + image_path[len(build.BASE_PATH):] if image_path else ""
    social = meta.get("linkedin", "").replace("\\n", "\n").strip()

    payload = {
        "titre": meta.get("title", ""),
        "description": meta.get("description", ""),
        "date": meta.get("date", ""),
        "categorie": category,
        "url": url,
        "image": image,
        "facebook": social or meta.get("description", ""),
        "linkedin": linkedin_ltf((social or meta.get("description", "")) + "\n\n" + url),
        "pinterest": meta.get("pinterest", "") or meta.get("description", ""),
    }

    req = urllib.request.Request(webhook, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=60) as resp:
        print(f"Annonce envoyée à Make ({resp.status}) : {payload['titre']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python
"""Rédige automatiquement un nouvel article avec Claude et l'enregistre dans content/articles/.

- Prend le premier sujet de la file `topics.json` (clé "a_faire").
- Si la file est vide, demande à Claude de proposer dix nouveaux sujets, puis en traite un.
- Déplace le sujet traité dans "publies".

Variables d'environnement :
  ANTHROPIC_API_KEY   obligatoire
  MODEL               facultatif, par défaut claude-opus-5-5

Usage : python scripts/generate_article.py [--dry-run]
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

import anthropic

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
TOPICS_FILE = ROOT / "topics.json"
ARTICLES_DIR = ROOT / "content" / "articles"
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))

MODEL = os.environ.get("MODEL", "claude-opus-5-5")
FALLBACK_BETA = "server-side-fallback-2026-07-01"


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()[:80]


def existing_articles() -> list[dict]:
    """Titres et adresses des articles déjà publiés, pour le maillage interne."""
    items = []
    for path in sorted(ARTICLES_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        m_title = re.search(r"^title:\s*(.+)$", text, re.M)
        m_slug = re.search(r"^slug:\s*(.+)$", text, re.M)
        if not m_title:
            continue
        slug = m_slug.group(1).strip() if m_slug else slugify(re.sub(r"^\d{4}-\d{2}-\d{2}-", "", path.stem))
        items.append({"title": m_title.group(1).strip().strip('"'), "url": f"/{slug}/"})
    return items


def call_claude(client: anthropic.Anthropic, system: str, user: str, max_tokens: int = 16000) -> str:
    """Appel en streaming avec repli serveur activé ; se replie sans l'option si l'API la refuse."""
    kwargs = dict(model=MODEL, max_tokens=max_tokens, system=system,
                  messages=[{"role": "user", "content": user}])
    try:
        with client.beta.messages.stream(betas=[FALLBACK_BETA], fallbacks="default", **kwargs) as stream:
            message = stream.get_final_message()
    except anthropic.BadRequestError as exc:
        if "fallback" not in str(exc).lower() and "beta" not in str(exc).lower():
            raise
        print(f"[info] option de repli refusée par l'API ({exc.__class__.__name__}), nouvel essai sans elle")
        with client.messages.stream(**kwargs) as stream:
            message = stream.get_final_message()

    if message.stop_reason == "refusal":
        details = getattr(message, "stop_details", None)
        raise RuntimeError(f"Demande refusée par le modèle : {details}")
    if message.stop_reason == "max_tokens":
        print("[avertissement] réponse tronquée (max_tokens atteint)")
    return "".join(block.text for block in message.content if block.type == "text")


SYSTEM_PROMPT = """Tu es le rédacteur principal du site francophone « {site_name} » ({tagline}).
Le site publie des guides d'achat et des conseils pratiques, honnêtes et utiles, pour les personnes qui travaillent de chez elles.
Ton public : des salariés en télétravail et des indépendants, en France, qui veulent s'équiper intelligemment sans se ruiner.

Règles de rédaction :
- Français naturel, tutoiement proscrit : on vouvoie le lecteur. Ton direct, concret, sans emphase ni superlatifs publicitaires.
- Aucun nom de marque ni modèle précis, aucun prix exact : donne des critères de choix, des fourchettes de budget réalistes et des usages.
- Pas d'affirmations médicales fortes ; reste au niveau du conseil pratique et invite à consulter un professionnel pour les douleurs persistantes.
- Structure : une introduction courte (2 à 3 phrases) qui va droit au but, puis des sections avec des titres de niveau ## et ###, des listes quand c'est utile, et une conclusion « En résumé » avec 3 à 5 points.
- Longueur : 900 à 1 400 mots.
- Insère 2 à 4 fiches produit avec cette syntaxe exacte, chacune sur sa propre ligne, entourée de lignes vides :
  [[produit: Nom générique du type de produit | recherche=mots clés de recherche Amazon | prix=fourchette indicative | note=une phrase sur pour qui c'est fait]]
  Exemple : [[produit: Chaise de bureau ergonomique avec soutien lombaire | recherche=chaise bureau ergonomique soutien lombaire | prix=150 à 400 € | note=Pour celles et ceux qui passent plus de six heures par jour assis.]]
- Maillage interne : fais 1 à 3 liens Markdown vers des articles existants du site quand c'est pertinent, en utilisant exactement les adresses fournies.
- N'invente pas d'études, de chiffres ni de citations.

Format de sortie, et rien d'autre (pas de commentaire avant ou après) :
---
title: Titre de l'article (60 à 70 caractères, avec le mot clé principal)
description: Résumé de 140 à 160 caractères pour les moteurs de recherche
date: {date}
category: {category}
linkedin: Texte d'un post LinkedIn sur UNE SEULE LIGNE (les sauts de ligne s'écrivent \\n). 500 à 900 caractères : une accroche concrète en une phrase, un saut de ligne, trois conseils courts tirés de l'article (un par ligne, commençant par un tiret), un saut de ligne, puis une phrase qui invite à lire le guide complet. Pas de lien (il est ajouté automatiquement), pas de hashtag dans le corps ; termine par trois hashtags maximum.
pinterest: Description Pinterest sur une seule ligne, 150 à 400 caractères, phrases naturelles contenant les mots clés que les gens tapent (par exemple « bureau à domicile », « télétravail », le sujet de l'article), sans hashtag ni emoji.
---
Corps de l'article en Markdown.
"""


def write_article(topic: dict, body: str) -> Path:
    body = body.strip()
    if body.startswith("```"):
        body = re.sub(r"^```[a-z]*\n", "", body)
        body = re.sub(r"\n```\s*$", "", body)
    if not body.startswith("---"):
        raise RuntimeError("La réponse ne commence pas par un en-tête ---")
    m = re.search(r"^title:\s*(.+)$", body, re.M)
    title = m.group(1).strip().strip('"') if m else topic["titre"]
    today = dt.date.today().isoformat()
    body = re.sub(r"^date:.*$", f"date: {today}", body, count=1, flags=re.M)
    path = ARTICLES_DIR / f"{today}-{slugify(title)}.md"
    counter = 2
    while path.exists():
        path = ARTICLES_DIR / f"{today}-{slugify(title)}-{counter}.md"
        counter += 1
    path.write_text(body + "\n", encoding="utf-8")
    return path


def propose_topics(client: anthropic.Anthropic, done_titles: list[str]) -> list[dict]:
    system = "Tu es responsable éditorial d'un site francophone sur l'équipement du bureau à domicile et le télétravail. Tu réponds uniquement en JSON valide."
    user = (
        "Propose dix nouveaux sujets d'articles de guide d'achat ou de conseil pratique, différents de ceux déjà traités ci-dessous, "
        "avec un bon potentiel de recherche Google en France. Réponds uniquement avec un tableau JSON d'objets "
        '{"titre": str, "angle": str, "category": str} où category est l\'une de : '
        '"Chaises et sièges", "Bureaux", "Écrans et informatique", "Audio et visioconférence", "Éclairage", "Aménagement", "Accessoires", "Bien-être au travail".\n\n'
        "Déjà traités :\n- " + "\n- ".join(done_titles[-60:])
    )
    text = call_claude(client, system, user, max_tokens=4000)
    m = re.search(r"\[.*\]", text, re.S)
    if not m:
        raise RuntimeError("Impossible de lire la liste de sujets proposée")
    topics = json.loads(m.group(0))
    return [t for t in topics if isinstance(t, dict) and t.get("titre")]


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    # On nettoie la clé : un retour à la ligne, un espace ou des guillemets copiés
    # avec elle dans le secret GitHub rendent l'en-tête HTTP invalide.
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip().strip('"').strip("'").strip()
    if not api_key:
        print("ANTHROPIC_API_KEY manquante : impossible de générer un article.", file=sys.stderr)
        return 2
    if not api_key.startswith("sk-ant-") or any(c.isspace() for c in api_key):
        print("ANTHROPIC_API_KEY mal formée : elle doit commencer par sk-ant- et ne contenir aucun espace. "
              "Recréez le secret en collant la clé seule.", file=sys.stderr)
        return 2

    client = anthropic.Anthropic(api_key=api_key)
    topics = json.loads(TOPICS_FILE.read_text(encoding="utf-8"))
    topics.setdefault("a_faire", [])
    topics.setdefault("publies", [])

    if not topics["a_faire"]:
        print("File de sujets vide : demande de nouveaux sujets à Claude…")
        done = [t.get("titre", "") for t in topics["publies"]] + [a["title"] for a in existing_articles()]
        topics["a_faire"] = propose_topics(client, done)
        print(f"{len(topics['a_faire'])} nouveaux sujets ajoutés.")

    topic = topics["a_faire"][0]
    print(f"Sujet : {topic['titre']}")

    existing = existing_articles()
    links = "\n".join(f"- {a['title']} → {a['url']}" for a in existing) or "(aucun pour l'instant)"
    system = SYSTEM_PROMPT.format(
        site_name=CONFIG["site_name"], tagline=CONFIG["tagline"],
        date=dt.date.today().isoformat(), category=topic.get("category", "Conseils"),
    )
    user = (
        f"Rédige l'article suivant.\n\nSujet : {topic['titre']}\nAngle : {topic.get('angle', 'guide d\'achat pratique')}\n"
        f"Catégorie : {topic.get('category', 'Conseils')}\n\nArticles existants disponibles pour le maillage interne :\n{links}"
    )

    if dry_run:
        print("--- dry-run : prompt système ---\n" + system + "\n--- prompt utilisateur ---\n" + user)
        return 0

    body = call_claude(client, system, user)
    path = write_article(topic, body)
    print(f"Article écrit : {path.relative_to(ROOT)}")

    topics["a_faire"].pop(0)
    topic["publie_le"] = dt.date.today().isoformat()
    topic["fichier"] = path.name
    topics["publies"].append(topic)
    TOPICS_FILE.write_text(json.dumps(topics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())

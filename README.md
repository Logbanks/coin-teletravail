# Le Coin Télétravail

Site de niche francophone sur l'équipement du bureau à domicile, monétisé par affiliation Amazon, avec rédaction automatique d'un article par semaine.

**Pour démarrer : lis [A_FAIRE.md](A_FAIRE.md).** Tout le reste de ce fichier décrit le fonctionnement.

## Comment ça marche

```
topics.json ──▶ scripts/generate_article.py ──▶ content/articles/*.md
                      (Claude, 1×/semaine)              │
                                                        ▼
config.json + templates/ + static/ ──▶ scripts/build.py ──▶ dist/ ──▶ GitHub Pages
```

- **`content/articles/`** : un fichier Markdown par article, avec un en-tête (`title`, `description`, `date`, `category`).
- **`content/pages/`** : pages fixes (à propos, mentions légales, confidentialité).
- **`topics.json`** : la file des sujets à rédiger (`a_faire`) et l'historique (`publies`).
- **`scripts/build.py`** : transforme le tout en site HTML dans `dist/` (accueil, articles, catégories, sitemap, RSS, robots.txt). Aucune base de données, aucun serveur.
- **`scripts/generate_article.py`** : prend le premier sujet de la file, demande à Claude de rédiger l'article selon la ligne éditoriale du site, l'enregistre, met à jour la file. Si la file est vide, il demande dix nouveaux sujets.
- **`.github/workflows/publier.yml`** : chaque lundi, rédige un article, le commite, reconstruit et déploie. À chaque push, reconstruit et déploie seulement.

## Fiches produit et liens d'affiliation

Dans un article, cette ligne :

```
[[produit: Chaise de bureau ergonomique | recherche=chaise bureau ergonomique | prix=150 à 300 € | note=Pour qui c'est fait.]]
```

devient une fiche avec un bouton vers la recherche Amazon correspondante, portant ton identifiant partenaire (`amazon_tag` dans `config.json`). Pour pointer vers un produit précis, ajoute `asin=B0XXXXXXXX`. Les liens portent `rel="sponsored nofollow"` comme le demandent Google et Amazon.

Le choix de liens de **recherche** plutôt que de produits précis est volontaire : les produits disparaissent, les recherches restent valides, et le robot rédacteur ne peut pas inventer de référence inexistante.

## Travailler en local

```bash
pip install -r scripts/requirements.txt
python scripts/build.py
python -m http.server 8000 --directory dist
```

Puis ouvre http://localhost:8000/coin-teletravail/ (le préfixe dépend de `url` dans `config.json`).

Pour tester la rédaction automatique sur ta machine :

```bash
set ANTHROPIC_API_KEY=sk-ant-...    # PowerShell : $env:ANTHROPIC_API_KEY="sk-ant-..."
python scripts/generate_article.py
```

`python scripts/generate_article.py --dry-run` affiche le prompt sans appeler l'API.

## Modifier le site

| Je veux… | Je modifie… |
|---|---|
| Le nom, l'accroche, l'adresse, l'identifiant Amazon | `config.json` |
| Les couleurs et la mise en page | `static/style.css` |
| La structure des pages, le pied de page | `templates/base.html` |
| La ligne éditoriale du robot rédacteur | `SYSTEM_PROMPT` dans `scripts/generate_article.py` |
| Les prochains sujets | `topics.json` |
| La fréquence de publication | `cron` dans `.github/workflows/publier.yml` |
| Retirer un article | supprimer son fichier dans `content/articles/` ou ajouter `brouillon: oui` dans son en-tête |

## Règles à respecter

- La mention Partenaire Amazon doit rester visible sur chaque page (elle est dans le pied de page).
- Les mentions légales doivent indiquer l'éditeur du site (obligation légale en France).
- Ne jamais commiter la clé API : elle vit uniquement dans les secrets GitHub.

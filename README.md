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

## Fiches produit et liens d'affiliation (« liens sponsorisés »)

Il y a trois façons de placer un lien qui te rapporte une commission.

### 1. La fiche produit (recommandé)

Dans un article, cette ligne :

```
[[produit: Chaise de bureau ergonomique | recherche=chaise bureau ergonomique | prix=150 à 300 € | note=Pour qui c'est fait.]]
```

devient une fiche avec un bouton vers la recherche Amazon correspondante, portant ton identifiant partenaire (`amazon_tag` dans `config.json`). Pour pointer vers un produit précis, ajoute `asin=B0XXXXXXXX`. Les liens portent `rel="sponsored nofollow"` comme le demandent Google et Amazon.

### 2. Un produit précis (avec son ASIN)

Sur la page Amazon d'un produit, l'ASIN est le code à 10 caractères dans l'adresse (`amazon.fr/dp/B0XXXXXXXX`) ou dans la section « Informations sur le produit ». Ajoute `asin=` dans la fiche :

```
[[produit: Lampe de bureau à bras articulé | asin=B0XXXXXXXX | prix=40 à 60 € | note=Le modèle que nous utilisons.]]
```

Le bouton pointe alors directement sur ce produit, avec ton identifiant. Utilise-le avec parcimonie : un produit retiré du catalogue donne un lien mort, alors qu'une recherche reste toujours valide.

### 3. Un lien dans le texte

Pour un simple lien dans une phrase, écris un lien Markdown vers une recherche ou un produit Amazon en ajoutant `?tag=cointeletrava-21` à la fin :

```
...un [support pour ordinateur portable](https://www.amazon.fr/s?k=support+ordinateur+portable&tag=cointeletrava-21) suffit.
```

Le générateur ajoute automatiquement `rel="sponsored nofollow"` à tout lien vers amazon.fr, comme l'exigent Google et Amazon.

### Suivre les résultats

Le tableau de bord https://partenaires.amazon.fr indique les clics, les commandes et les commissions par jour. Les commissions sont versées environ 60 jours après la fin du mois, à partir de 25 € cumulés.

### Hors Amazon

D'autres programmes paient parfois mieux sur le mobilier de bureau (marques en direct via Awin, Effiliation, ou les programmes propres des enseignes). Ils demandent chacun une inscription. Si tu en ajoutes un, remplace simplement le lien du bouton dans la fiche produit par `lien=https://...` : le générateur l'utilisera à la place du lien Amazon.

Le choix de liens de **recherche** plutôt que de produits précis est volontaire : les produits disparaissent, les recherches restent valides, et le robot rédacteur ne peut pas inventer de référence inexistante.

## Réseaux sociaux : flux prêts à poster

Chaque article porte deux champs d'en-tête rédigés par le robot (ou à la main) :

```
linkedin: Accroche.\n\n- conseil 1\n- conseil 2\n- conseil 3\n\nInvitation à lire.\n\n#hashtag1 #hashtag2
pinterest: Description de l'épingle avec les mots clés, 150 à 400 caractères.
```

Les sauts de ligne du champ `linkedin` s'écrivent `\n` (le champ tient sur une ligne). Le générateur produit :

- `feed-linkedin.xml` : description = texte LinkedIn au format « little Text Format » de l'API LinkedIn (hashtags codés), sans le lien, qui est porté par la carte Article ;
- `feed-pinterest.xml` : description = texte Pinterest, image de l'article en `enclosure` ;
- `feed.xml` : flux classique pour les lecteurs, avec image.

Un automate (Make, Zapier, IFTTT…) lit ces flux et publie. Le branchement pas à pas est dans `A_FAIRE.md`, section 11. Un article sans champ `linkedin` ou `pinterest` est simplement absent du flux correspondant.

## Publicité Google AdSense

Désactivée par défaut. Pour l'activer, mets ton identifiant éditeur dans `config.json` :

```json
"adsense_client": "ca-pub-1234567890123456"
```

Le générateur ajoute alors le script AdSense dans l'en-tête de chaque page, le fichier `ads.txt` à la racine et un lien « Paramètres de confidentialité » en pied de page. Les annonces et le bandeau de consentement RGPD sont gérés depuis le compte AdSense (Annonces automatiques et Confidentialité et messages), sans modifier le site. Pour tout couper, remets la valeur à `""`.

## Travailler en local

```bash
pip install -r scripts/requirements.txt
python scripts/build.py
python -m http.server 8000 --directory dist
```

Puis ouvre http://localhost:8000/ (si `url` dans `config.json` contient un sous-dossier, ajoute-le au chemin).

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

# Ce qui te reste à faire (une seule fois, environ une heure)

**Les cinq étapes ont été faites le 24 octobre 2026. Le site tourne seul.** Il reste une seule chose à surveiller : obtenir trois ventes Amazon avant le 22 avril 2027 (180 jours), sinon Amazon ferme le compte partenaire et il faudra se réinscrire.

## 1. Mettre le site en ligne gratuitement (GitHub Pages) — FAIT le 24/10/2026 : https://logbanks.github.io/coin-teletravail/

- [x] Crée un compte sur https://github.com si tu n'en as pas (gratuit).
- [x] Crée un nouveau dépôt **public** nommé exactement `coin-teletravail` (sans README, sans licence, vide).
- [x] Dans `config.json`, remplace `VOTRE-IDENTIFIANT-GITHUB` par ton identifiant GitHub dans la ligne `"url"`.
- [x] Ouvre un terminal dans le dossier `coin-teletravail` et envoie le site (remplace TON-IDENTIFIANT) :

```bash
git add -A
git commit -m "Lancement du site"
git remote add origin https://github.com/TON-IDENTIFIANT/coin-teletravail.git
git push -u origin main
```

- [x] Sur GitHub, dans le dépôt : **Settings → Pages → Build and deployment → Source** : choisis **GitHub Actions**.
- [x] Onglet **Actions** du dépôt : si un message demande d'activer les workflows, clique sur « I understand… enable them ».
- [x] Attends deux minutes : le site est visible sur `https://TON-IDENTIFIANT.github.io/coin-teletravail/`.

## 2. Activer la rédaction automatique hebdomadaire — FAIT le 24/10/2026 (premier article de test publié)

- [x] Crée un compte sur https://console.anthropic.com, ajoute un moyen de paiement et génère une **clé API**.
      Coût estimé : un article par semaine, quelques dizaines de centimes à un euro par article, soit quelques euros par mois.
      Tu peux fixer un plafond mensuel de dépense dans la console pour ne jamais être surpris.
- [x] Sur GitHub, dans le dépôt : **Settings → Secrets and variables → Actions → New repository secret**.
      Nom : `ANTHROPIC_API_KEY` — Valeur : ta clé. Ne la colle nulle part ailleurs.
- [x] Test : onglet **Actions → Publier le site → Run workflow**, laisse la case « Rédiger un nouvel article » cochée, lance.
      Trois minutes plus tard, un nouvel article apparaît sur le site. Ensuite, c'est tous les lundis à 8 h (heure française, 6 h UTC).

## 3. Gagner de l'argent : le Partenariat Amazon — identifiant cointeletrava-21 en place le 24/10/2026 ; reste : 3 ventes en 180 jours

- [x] Inscris-toi sur https://partenaires.amazon.fr avec l'adresse de ton site. Tu devras indiquer ton identité et tes coordonnées bancaires pour être payé.
- [x] Récupère ton **identifiant de partenaire** (il se termine par `-21`, par exemple `moncoin-21`).
- [x] Dans `config.json`, remplace `VOTRE-TAG-21` par cet identifiant, puis :

```bash
git commit -am "Identifiant partenaire Amazon"
git push
```

- [ ] **Important** : Amazon exige **trois ventes dans les 180 jours** suivant l'inscription pour valider le compte, sinon il est fermé (tu peux te réinscrire). Partage les articles autour de toi au lancement pour passer ce cap.
- [x] Amazon vérifie aussi que la mention « En tant que Partenaire Amazon, je réalise un bénéfice sur les achats remplissant les conditions requises » figure sur le site : elle est déjà dans le pied de page de chaque page.

## 4. Être trouvé sur Google — FAIT le 24/10/2026 (propriété vérifiée, sitemap envoyé ; Google peut mettre 1 à 2 jours à le lire)

- [x] Va sur https://search.google.com/search-console, ajoute la propriété « Préfixe d'URL » avec l'adresse de ton site, valide par balise HTML (colle la balise dans `templates/base.html` juste avant `</head>`, puis commit et push).
- [x] Dans Search Console : **Sitemaps** → ajoute `sitemap.xml`.
- [ ] Même chose, facultatif, sur https://www.bing.com/webmasters (on peut importer directement depuis Search Console).

## 5. Les mentions légales — FAIT le 24/10/2026 (éditeur anonyme, hébergeur GitHub, contact@logroot.fr)

- [x] Mentions légales rédigées en mode anonyme (particulier non professionnel, coordonnées détenues par l'hébergeur).
- [x] Adresse de contact en place : contact@logroot.fr.
- [x] Commit et push.

## 6. Domaine personnalisé — FAIT le 24/10/2026 : https://teletravail.logroot.fr (HTTPS forcé, ancienne adresse redirigée)

- [x] Search Console : ajouter la propriété `https://teletravail.logroot.fr/` (préfixe d'URL, vérification par balise HTML déjà en place) et y envoyer `sitemap.xml`.
- [x] Amazon Partenaires : Paramètres du compte → informations sur le site Web → ajouter `https://teletravail.logroot.fr`.

## 7. Illustrations — FAIT le 24/10/2026

Neuf illustrations (une par catégorie + accueil) dans `static/img/`. Pour en changer une, remplace le fichier JPG du même nom. Pour une image propre à un article, ajoute `image: static/img/mon-image.jpg` dans son en-tête. Les originaux sont dans ton Canva (« Support d'illustrations vierge »).

## 8. Bing Webmaster Tools — 3 min, facultatif

- [ ] Va sur https://www.bing.com/webmasters et connecte-toi (compte Microsoft, Google ou Facebook).
- [ ] Choisis **Importer depuis Google Search Console**, autorise l'accès, coche la propriété `https://teletravail.logroot.fr/` → Importer. Le sitemap est repris automatiquement.
- [ ] Si tu préfères l'ajout manuel : « Ajouter votre site manuellement », puis vérification par **balise meta** : colle-moi la balise et je l'insère comme pour Google.

## 9. Publicité Google AdSense — à faire quand le site aura du trafic (compter 3 à 6 mois)

Le site est déjà prêt : il suffira de remplir `adsense_client` dans `config.json`. Pourquoi attendre : Google refuse presque toujours un site de moins de quelques mois ou sans visites, et une publicité sur un site vide ne rapporte rien tout en gênant les clics Amazon.

- [ ] Inscription sur https://www.google.com/adsense avec ton compte Google, adresse du site `teletravail.logroot.fr`, pays France.
- [ ] AdSense te donne un identifiant de la forme `ca-pub-1234567890123456`. Donne-le-moi (ou mets-le dans `config.json`, ligne `adsense_client`, puis commit et push). Le site ajoute alors le script Google et le fichier `ads.txt` tout seul.
- [ ] Dans AdSense : **Confidentialité et messages → Message RGPD** : crée le message avec les réglages par défaut et publie-le. C'est le bandeau de consentement obligatoire en Europe ; Google l'affiche lui-même, rien à coder.
- [ ] Dans AdSense : **Annonces → Par site → Modifier** : active les **Annonces automatiques**, puis valide. Google place et dose les annonces lui-même.
- [ ] Attends la validation (quelques jours à deux semaines). AdSense verse à partir de 70 € cumulés.

## 10. Faire connaître le site (gratuit, bien plus rentable que la pub payante)

- [ ] **Pinterest** : crée un compte, un tableau « Bureau à domicile », et épingle chaque article avec son illustration. Les sujets maison et bureau y marchent très bien et le trafic dure des mois.
- [ ] **LinkedIn** : un post par mois sur un conseil télétravail avec le lien de l'article. Public exactement ciblé.
- [ ] **Forums et groupes** : groupes Facebook « télétravail », Reddit r/france ou r/vosfinances quand un article répond vraiment à une question posée. Jamais de lien à froid.
- [ ] **Les trois ventes Amazon** : envoie le lien d'un article à trois ou quatre collègues qui s'équipent.

Publicité payante (Google Ads, Meta Ads) : déconseillée pour ce site. Un clic coûte 0,30 à 1 € ; une commission Amazon rapporte en moyenne 0,05 à 0,30 € par clic. Tu perdrais de l'argent à chaque visiteur acheté.

## 11. Publication automatique LinkedIn et Pinterest — FAIT le 24/10/2026

Deux scénarios Make (make.com, plan gratuit) lisent chaque jour les flux du site et publient :

| Scénario | Flux lu | Modules | Horaire | Point de départ |
|---|---|---|---|---|
| LinkedIn | `feed-linkedin.xml` | RSS → HTTP « Download a file » (image) → LinkedIn « Create a User Text Post », Media Type **Article** (URL, Title, Thumbnail = fichier HTTP) | tous les jours 9 h 00 | From now on |
| Pinterest | `feed-pinterest.xml` | RSS → Pinterest « Create a Pin » (Image URL = Enclosures[] URL, Board, Pin Name = Title, Description, Link = URL) | tous les jours 9 h 30 | All (épingle un article existant par jour, puis les nouveaux) |

Le texte LinkedIn et la description Pinterest de chaque article sont rédigés par le robot (champs `linkedin:` et `pinterest:` de l'en-tête). Le lien de l'article figure à la fin du texte et dans la carte LinkedIn. Après toute modification d'un module, cliquer sur **Save** en bas de l'écran du scénario, sinon la version active reste l'ancienne.

Entretien : aucun. Si Make affiche un scénario en erreur (mail de Make), c'est en général la connexion LinkedIn ou Pinterest à renouveler : ouvrir le module, cliquer sur la connexion, « Reauthorize ».

## Facultatif, plus tard

- **Un nom de domaine** (environ 10 €/an, par exemple `coin-teletravail.fr`) améliore la crédibilité et le référencement. Dans `config.json`, mets `"url": "https://coin-teletravail.fr"` ; le fichier `CNAME` est généré automatiquement. Chez ton registrar, ajoute un enregistrement CNAME `www` ou les 4 enregistrements A de GitHub Pages (voir la doc GitHub « Managing a custom domain »).
- **Changer la fréquence** : dans `.github/workflows/publier.yml`, les lignes `cron:` (lundi 6 h 23 UTC, rattrapage à 11 h 41). Deux articles par semaine : remplacer `* * 1` par `* * 1,4` sur les deux lignes. Garder des minutes décalées, GitHub saute souvent les crons à l'heure pile.
- **Ajouter des sujets** : complète la liste `a_faire` dans `topics.json`. Quand elle est vide, le robot invente lui-même dix nouveaux sujets.
- **Relire** : tous les articles générés arrivent dans `content/articles/`. Tu peux en modifier ou en supprimer un, puis push : le site se reconstruit.

## À quoi t'attendre, honnêtement

- Mois 1 à 3 : quasiment aucun trafic, Google met du temps à faire confiance à un nouveau site. C'est normal.
- Mois 4 à 12 : si le contenu est utile et régulier, le trafic monte progressivement. Un site de niche de ce type atteint typiquement quelques centaines à quelques milliers de visites par mois au bout d'un an.
- Revenus : Amazon reverse entre 1 et 12 % selon la catégorie (le mobilier et l'informatique sont dans la fourchette basse à moyenne). Ordre de grandeur réaliste à un an : de quelques euros à quelques centaines d'euros par mois. Rien n'est garanti.
- Le seul entretien : jeter un œil au site une fois par mois, et vérifier que la carte bancaire de la console Anthropic est valide.

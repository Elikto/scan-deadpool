# Deadpool VF — Bibliothèque

Catalogue web des **éditions françaises de Deadpool**. Refonte depuis zéro : code séparé, données structurées, sources vérifiables et aucune notice fictive.

## Architecture

- `index.html` : structure accessible du site
- `assets/style.css` : design responsive
- `assets/app.js` : recherche, tri, filtres, collection personnelle stockée localement
- `data/books.json` : **seule source de vérité** pour les fiches visibles
- `scripts/sync.py` : import de notices BnF et enrichissement Google Books par ISBN
- `.github/workflows/catalog.yml` : synchronisation manuelle et hebdomadaire (sans publication du site)

## Données et API

Le synchroniseur utilise le service SRU public de la BnF pour découvrir les notices Deadpool et Google Books pour compléter les couvertures **uniquement lorsque l'ISBN correspond**. Les titres, dates et éditeurs sont issus des notices; les données absentes ne sont pas inventées. Une notice BnF n'est pas automatiquement une édition distincte : les doublons sont rapprochés par ISBN ou identifiant ARK.

Les API des boutiques (Panini, Fnac, Cultura, etc.) **ne sont pas intégrées** tant qu'un accès documenté et autorisé n'a pas été configuré. Les images distantes peuvent ne pas être disponibles.

### Format d'une fiche

```json
{"id":"bnf-ARK","title":"Titre exact","publisher":"Éditeur","collection":"","year":2020,"isbn":"978...","cover":"https://...","source":"https://catalogue.bnf.fr/..."}
```

## Développement

Servir le répertoire avec un serveur HTTP local pour tester `index.html` (le chargement JSON ne fonctionne pas toujours avec `file://`). Pour lancer une collecte : `python scripts/sync.py`.

## Publication

**GitHub Pages reste désactivé.** La présence de fichiers web dans le dépôt ne publie pas automatiquement le site. Une publication future doit être activée explicitement dans les paramètres du dépôt.

## Limitations

Ce catalogue est une base à enrichir, pas une bibliographie exhaustive certifiée. Les données BnF peuvent contenir des œuvres connexes ou des éditions incomplètes; leur validation éditoriale reste nécessaire. La chronologie narrative US demande une source éditoriale dédiée, distincte des dates de publication françaises.

Projet indépendant, sans affiliation avec Marvel ou ses éditeurs.

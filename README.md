# Deadpool VF — Catalogue de lecture

Site web statique de suivi des albums Deadpool en français.

## Aperçu

- Chronologie de lecture indicative et catalogue Hachette (*La Collection qui tue*) séparé.
- Recherche et filtres par collection et disponibilité.
- Numéro de tome, année, éditeur, contenu VO et ISBN quand renseignés.
- Liens vers des recherches de boutiques (Fnac, Cultura, BDfugue, E.Leclerc) ; le prix ou le stock n'est affiché que lorsqu'une donnée fiable est disponible.
- Suivi personnel des volumes possédés, enregistré localement dans le navigateur.

## Utilisation

Ouvrir [index.html](./index.html), ou activer GitHub Pages dans **Settings → Pages → Deploy from a branch → main / (root)** pour publier le site.

## Limites actuelles

**Le scan quotidien automatique n'est pas actif.** Les prix et disponibilités affichés ne constituent pas une consultation en temps réel et les absences de prix ne signifient pas une rupture de stock. L'application n'a pas encore de backend connecté à des sources marchandes autorisées. La règle Amazon (afficher seulement si au moins 3 € moins cher, selon des frais de livraison comparables) n'est pas opérationnelle sans ces données.

Le catalogue de lecture est encore en cours de vérification : la liste n'est pas exhaustive, les apparitions secondaires et certains contenus sont incomplets. Il ne faut pas confondre ordre de lecture, date de publication VO et année d'édition VF.

Projet non affilié à Marvel, Panini, Hachette ou aux enseignes mentionnées.

## Actualisation quotidienne

Le workflow `.github/workflows/update-catalog.yml` est planifié tous les jours à 22 h 23 (Europe/Paris) (exécution GitHub Actions non garantie à la minute). Il se déclenche également lors d'une modification du catalogue ou du workflow, et peut être lancé manuellement depuis **Actions → Actualiser le catalogue Deadpool VF → Run workflow**.

Il vérifie les couvertures ISBN via Open Library et charge uniquement les offres récentes présentes dans `data/merchant-offers.json` (moins de 48 heures, prix, date, disponibilité et URL HTTPS obligatoires). Le résultat est écrit dans `data/catalog-status.json`, que le site charge à l'ouverture. Les liens de recherche marchands restent disponibles sans offres vérifiées.

**Important :** ce workflow ne récupère pas automatiquement les tarifs Fnac/Cultura/BDfugue/E.Leclerc/Amazon. Pour cela il faut une source autorisée, telle qu'un flux commerçant ou une API partenaire. Aucun prix n'est inventé. Les livres ne sont grisés que si au moins deux marchands non Amazon ont explicitement confirmé la rupture et que toutes les offres connues sont en rupture. Amazon n'est affiché qu'à au moins 3 € sous le prix le plus bas d'un concurrent connu (hors frais de livraison non renseignés).

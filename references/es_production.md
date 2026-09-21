# es_production — ce que le skill doit savoir

Référence pour le module maison `es_production` (Odoo 18). Le skill lit ce module quand il
est installé ; sinon il se rabat sur `project.task` + congés. Ce fichier synthétise les
notes projet des 08/09 au 18/09/2026 sans les réécrire in extenso.

Source : `claude_workflow-projet-session-mission-18-09-2026.md`,
`claude_es-production-2_0_0-conduite-affaire-09-09-2026.md`, `claude_schema-2_0_0-…`,
`claude_es-production-10_0_0-missions-12-09-2026.md`,
`claude_es-production-12_0_0-cout-reel-complet-18-09-2026.md`,
`claude_es-production-11_2_0-salarie-prestataire-16-09-2026.md`,
`claude_es-production-12_2_0-taches-privees-18-09-2026.md`, lots G (parc matériel),
`claude_es-production-11_1_0-reservation-terrain-16-09-2026.md`, et le code source
`esprod/es_production` (lot 1 livré).

---

## Modèle Projet / Session / Mission

```
project.project  (l'affaire)
   ├── es.shooting  (session / journée de tournage)
   │      ├── es.crew.assignment  (affectations personnes)
   │      ├── es.shooting.slot     (déroulé horaire)
   │      └── es.equipment.booking (réservations matériel, lot 4)
   ├── es.mission  (mission = déplacement hors Abidjan — 1 par lieu)
   │      └── logistique prévisionnelle (transport, hébergement, restauration, fret)
   └── project.task  (tâches par étape + 4 satellites par session)
```

### 5 règles de rattachement

1. Une **session** appartient toujours à un **projet** (`project_id` requis).
2. Une **mission** appartient toujours à un **projet** et vise un **lieu** (ou une étape).
   Hors Abidjan : 1 mission = départ la veille → tournage → retour.
3. Une **affectation** (`es.crew.assignment`) appartient à une **session** (ou mission selon
   version) ; `quantity = 1` par jour de cachet, `day_rate` avec `day_rate_is_override`.
4. Une **tâche** appartient à un **projet** ; les tâches satellites sont liées à leur session
   (`shooting_id`) et portent une échéance relative (J−2, J, J+1, J+2).
5. Le **coût** se rattache via `analytic_distribution` du projet (héritée par sessions et
   dépenses) — jamais en direct sur une personne sans projet.

### Séquence « avant / pendant et après » en 10 points (phases D et E)

Procédure à suivre pour chaque session/mission :

1. Vérifier la disponibilité de l'équipe (congés + affectations + indisponibilités).
2. Réserver le matériel (`es.equipment.booking`) et vérifier les **conflits de réservation**.
3. Créer/ajuster les affectations (`es.crew.assignment`), avec détection de conflits (bandeau
   non bloquant si forcé — tracé dans le chatter, `conflict_override`).
4. Générer la **feuille de service** (PDF + lien partagé — lisible sur téléphone, imprimable N&B).
5. Envoyer la convocation (le skill **prépare**, Lycris envoie — jamais d'envoi auto).
6. **Clôture terrain** : présences (`attendance_state`), dépenses au réel (caisse TTC, **sans TVA
   récupérable** — voir `references/comptabilite.md`), cachets en `hr.expense` / `account.move`
   fournisseur avec analytique.
7. Dérushage et sauvegarde (J+1) — tâche satellite, au moins 2 copies avant `wiped`.
8. Intégration et contrôles (J+2) — tâche satellite.
9. Avancement des tâches (validation client, livraison).
10. Bilan : marge réelle (compta) vs prévisionnel, leçon consignée.

---

## Canal de coût

```python
es_cost_channel = "timesheet"    # feuille de temps → account.analytic.line
es_cost_channel = "vendor_bill"  # facture fournisseur → account.analytic.line avec analytique projet
```

- Un coût jour à **0** sur `hr.employee.hourly_cost` n'est pas une donnée manquante : c'est le
  **montage B** (facture fournisseur avec analytique). Vérifier personne par personne.
- Le skill affiche canal + coût jour à chaque proposition d'équipe.
- `es.cost.rate` (historisé, `date_from`) et `es.project.rate` (surcharge par affaire) nourrissent
  `day_rate`. **Défaut ×8 connu** : `day_cost = hourly_cost × 8` — le skill force toujours
  `day_rate_is_override = True` avec la valeur jour réelle (voir § Défauts).
- Convention : **1 journée de tournage = 1 jour de feuille de temps** (forfaitaire), base passée
  en jours le 07/09/2026, champ `hourly_cost` = « Coût par journée ».

## Parc matériel (relevé base 21/09/2026 — 100+ exemplaires, 11 kits)

- `es.equipment` : `name`, `category_id` (Caméra, Boîtiers, Optique, Drone, Son,
  Micros, Lumière, Régie, Studio, Stockage, Énergie…), `brand`/`model`,
  `quantity` + `quantity_available` (calculé), `state` (`available`, `booked`,
  `out`, `maintenance`, `broken`, `lost`, `retired`), `ownership`
  (`owned`/`rented_in`/`customer`), `day_rate` **indicatif** — il n'entre jamais
  dans le coût réel (amortissement) ; seule la facture fournisseur de
  sous-location compte.
- `es.equipment.kit` (+ `es.equipment.kit.line` : `equipment_id` + `quantity`) :
  11 lots par usage — tournage Sony A7 III, Blackmagic 6K Pro, son reportage,
  podcast 4 places, lumière studio photo, lumière LED, régie multicam, mouvement,
  stabilisation, fond studio, drone Mavic 3. Un kit est un raccourci de saisie :
  réserver un kit = 1 réservation par ligne de contenu.
- `es.equipment.booking` : `equipment_id` (requis) + `project_id` + `shooting_id` /
  `mission_id` + `quantity` (requis) + `date_from`/`date_to` (requis) + `holder_id`
  (`res.users` — qui répond de l'unité) + `state`
  (`draft`/`confirmed`/`out`/`returned`/`cancelled`) + `conflict_warning` (calculé).
  `draft`, `confirmed` et `out` immobilisent le matériel et entrent dans le contrôle
  de conflit.
- Procédure questions → écriture : **(1)** lister via
  `scripts/equipe.py --du … --au … --materiel [--categorie …]` (kits + exemplaires
  avec état, disponibles et chevauchements) ; **(2)** faire valider kits,
  exemplaires, quantités, fenêtre et porteur (chargé de mission par défaut) ;
  **(3)** écrire `es.equipment.booking` en `draft` au temps 3, puis relire
  `conflict_warning` et le signaler sans bloquer.
- Vues : Planning matériel (calendar), « Vérifier la disponibilité », Bon de sortie/retour PDF.
- Exemples d'état constatés : HF Sennheiser ew 112 P G4 ×2 `broken`, stabilisateurs
  Feiyu AK2000/AK4000 `broken`, 2 objectifs Sony `broken` → à signaler dans le
  questionnaire et à remplacer par de la location chiffrée.

## es.crew.ledger — ce qu'on doit à chaque intervenant

- Agrège les cachets dus (affectations `realise` sans `expense_id` réglée, factures
  `in_invoice` non payées) par personne.
- **À contrôler avant de rebooker** : décompte arrêté fin de mois, paiements dus au 15 du mois
  suivant. Le skill le lit et le résume au « point du lundi » et avant toute affectation.
- Ne jamais rebooker quelqu'un à qui on doit encore le mois précédent sans le signaler.

## Frontière avec es_finance (décision 21/09/2026)

> es_production gère la **productivité** ; les seuls volets financiers qu'il affiche sont
> notes de frais, gains des freelances et frais de mission. **Un chargé de production ne voit
> pas la marge.**

- La marge vit dans **es_finance**, réservée à la direction (groupe `group_production_manager`).
- Lot 2 engagé : retirer de es_production les champs de coût et de marge d'`es.deal`,
  `es.margin.snapshot`, les alertes de marge et leurs affichages.
- Tant que ce lot n'est pas livré, le skill **ne montre la marge qu'à Lycris** et ne l'inscrit
  **jamais** dans un document ou une tâche visible par l'équipe (feuille de service, description
  de tâche, message de fil). Filtrage côté serveur (`get_dashboard_data`), pas seulement masquage
  côté template.

## Défauts connus et exemples à ne pas reproduire

- **day_rate ×8** : défaut de conversion `hours_per_day = 8` appliqué au `day_rate`. Tant que
  non corrigé côté module, toute création d'`es.crew.assignment` par le skill pose
  `day_rate_is_override = True`.
- **227 500 F d'intervenants DABOSA payés en espèces hors affectations** : dépenses en
  `CSH1` sans affectation ni analytique projet → marge fausse et traçabilité perdue. Toujours
  passer par une affectation + `hr.expense` / `account.move` avec `analytic_distribution`.
- **Projet fantôme MAGGI « … - MODÈLE — … »** : `sale.order.line.project_id` orphelin après
  confirmation. Vérifier après chaque confirmation.
- **Mode terrain** (lot 1) : feuille de service du jour, confirmation de présence, saisie
  d'heures, photo de reçu → note de frais avec affaire pré-remplie. Le skill le prépare, il ne
  l'envoie pas.

## Ce que le skill fait avec es_production

- Lit `es.shooting` / `es.mission`, leurs créneaux, leur équipe et leur matériel.
- Propose les affectations (membre nommé + rôle + remplaçant) avec coût et canal.
- Propose le matériel (kits + exemplaires via `equipe.py --materiel`) avec état et
  conflits, et fait valider porteur et fenêtre.
- Crée `es.shooting` / `es.mission` + `es.crew.assignment` après validation temps 2, avec
  les garde-fous (conflits, `fields_get`, `day_rate_is_override`).
- Crée `es.equipment.booking` en brouillon selon le matériel validé (1 par ligne +
  lignes des kits), puis vérifie `conflict_warning`.
- Génère les **4 tâches satellites par session** :
  - J−2 : préparation / convocation
  - J : captation
  - J+1 : dérushage / sauvegarde (2 copies min.)
  - J+2 : intégration / contrôles
- Prépare feuilles de service et activités de rappel (J−2, livraison, etc.).
- Lit `es.crew.ledger` et les alertes (sessions à J−2 sans équipe confirmée, conflits,
  feuilles de service non envoyées).

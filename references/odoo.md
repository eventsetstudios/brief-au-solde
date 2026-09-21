# Odoo — connexion, modèles et pièges de cette base

Base de production d'Évents & Studios. Ce fichier décrit l'instance réelle, pas Odoo en
général : les identifiants numériques cités ont été relevés sur `odoo_db` et sont valables tant
que la configuration n'a pas bougé. En cas de doute, relis-les plutôt que de t'y fier.

## L'instance

| | |
|---|---|
| Version | Odoo 18 Community |
| Base | `odoo_db` |
| **Adresse principale** | **`https://manage.eventsetstudios.ci`** (HTTPS, accès public) — remplace Tailscale depuis 21/09/2026 |
| Adresse Tailscale (secours) | `http://100.119.180.128:8069` |
| Adresse LAN (secours) | `http://eventsetstudios.local:8069` (ne résout que sur le réseau local) |
| Devise | XOF (franc CFA), sans décimales |
| TVA | 18 % — **mais plus aucune TVA facturée à partir du 01/10/2026** (voir `references/comptabilite.md`) |
| Langue de l'interface | `fr_FR` |
| Unité de temps projet | **Jours** depuis le 07/09/2026 (1 journée = 8 h) |

**Où ça tourne.** Depuis le 21/09/2026 l'adresse publique `https://manage.eventsetstudios.ci`
est la voie par défaut. Tailscale et le LAN ne restent qu'en secours. Dans un bac à sable
dont le réseau est filtré par allowlist, le domaine `manage.eventsetstudios.ci` doit y être
ajouté ; si la requête est refusée (en-tête `x-deny-reason`), le skill bascule sur le
connecteur MCP. Si aucune voie n'est joignable, annonce que tu travailles sur le référentiel
embarqué (`references/referentiel.md`) et ne chiffre rien d'autoritaire.

## Connexion

Ordre de connexion imposé :

1. **Connecteur MCP Odoo** s'il est présent dans la session (`odoo_search_records`,
   `search_read`, `read_group`, `create_records`, `update_records`, `call_method`…) ;
2. sinon **XML-RPC** sur `https://manage.eventsetstudios.ci` avec les identifiants lus dans
   l'environnement (`ODOO_URL`, `ODOO_DB`, `ODOO_USER`, `ODOO_PASSWORD` ou clé d'API) — jamais
   écrits dans le skill ;
3. sinon le dire, travailler sur le référentiel et l'annoncer.

Odoo expose XML-RPC sur `/xmlrpc/2/common` (authentification) et `/xmlrpc/2/object`
(lecture/écriture). Les identifiants se lisent dans l'environnement :

```
ODOO_URL=https://manage.eventsetstudios.ci
ODOO_DB=odoo_db
ODOO_USER=<login>
ODOO_PASSWORD=<mot de passe ou clé API>
```

Ou fichier `~/.odoo_es.json` portant les mêmes clés en minuscules (`url`, `db`, `user`,
`password`). S'ils sont absents, demande-les à Lycris plutôt que d'essayer des valeurs au
hasard — trois échecs d'authentification suffisent à faire du bruit dans les journaux.

`scripts/odoo.py` encapsule tout cela (défaut `ODOO_URL = https://manage.eventsetstudios.ci`).
Utilise-le plutôt que de réécrire un client. Il gère le basculement MCP → XML-RPC et
l'en-tête `x-deny-reason`.

## Le piège qui a déjà faussé un diagnostic

**Toujours passer `{'lang': 'fr_FR'}` dans le contexte des appels.** Sans ce contexte, `call_kw`
renvoie les libellés en `en_US`. Cela a déjà conduit à conclure à tort que les étapes CRM et de
projet étaient en anglais et devaient être renommées — elles étaient déjà traduites. Toute
lecture de `name`, de sélection ou d'étape sans ce contexte est à considérer comme non fiable.

```python
models.execute_kw(db, uid, pwd, 'sale.order', 'search_read',
                  [[['state', '=', 'sale']]],
                  {'fields': ['name', 'amount_total'],
                   'context': {'lang': 'fr_FR'}})
```

## Les modèles utiles, dans l'ordre du workflow

| Étape | Modèle | Ce qu'on y fait |
|---|---|---|
| 01 | `crm.lead` | opportunité (CRM principal — voir `references/crm.md`). Le mode Pistes est **non activé**, 0 opportunité au 08/09 |
| 02 | `sale.order`, `sale.order.line` | devis en brouillon (`state = 'draft'`). Vérifier `project_id` de chaque ligne après confirmation (piège du projet fantôme) |
| 03 | `sale.order` | passage à `state = 'sale'` par `action_confirm` — jamais automatique sans validation explicite du temps 2 |
| 04, 14 | `account.move` (`move_type = 'out_invoice'`) | factures d'acompte et de solde (toujours en brouillon sauf inclusion explicite dans la validation) |
| 05 | `project.project` | créé par la confirmation de commande, pas à la main. Vérifier `account_id` (pas `analytic_account_id` en v18) |
| 05 | `es.deal` | affaire maison : journal d'étapes, `is_closed` (solde encaissé + FNE émise). Lire `fields_get` pour le champ responsable (`user_id` ou autre) |
| 05-06 | `es.finance.pipeline` | « Projets à venir » — **plus jamais pour une affaire client** (voir `references/es_finance.md`). Ne garder que les projets internes |
| 07 | `project.task`, `project.task.type` | tâches et étapes : Pré-production → Production → Post-production → Validation client → Livré + 4 satellites par session (J−2, J, J+1, J+2) |
| 07 | `es.shooting`, `es.mission` | session / mission (voir `references/es_production.md`). Une mission par lieu hors Abidjan ; 5 règles de rattachement |
| 08, 09 | `es.crew.assignment`, `es.crew.role`, `es.crew.unavailability` | affectations équipe (quantity=1, `day_rate` + `day_rate_is_override`). Détection de conflits |
| 08, 09 | `hr.employee`, `res.partner`, `hr.leave` | équipe, prestataires, congés (`hr.leave.state = 'validate'` seul bloque) |
| 10 | `account.analytic.line` | feuilles de temps **et** lignes analytiques de coût |
| 10 | `account.move` (`in_invoice`), `hr.expense` | factures fournisseurs, notes de frais. `es.crew.ledger` pour les dettes intervenants |
| 10 | `es.equipment`, `es.equipment.booking` | parc matériel, réservations (conflits à vérifier au dispositif) |
| 10-14 | `es_ops_queue` | file « Opérations à valider » pour ce qui ne peut pas être exécuté (suppressions) |

### Champs à connaître

- `project.project.account_id` — le compte analytique. **Pas** `analytic_account_id` en v18.
- `project.project.sale_order_id` — apporté par `sale_project`, related sur `sale_line_id.order_id`.
- `project.project.user_id` — **chargé de projet** (toujours renseigné).
- `hr.employee.hourly_cost` — renommé « **Coût par journée** » sur cette base après la bascule en
  jours. La valeur est donc un coût **journalier**, malgré le nom technique du champ.
- `es.crew.assignment.quantity` — **toujours 1** par jour de cachet ; `day_rate` forcé avec
  `day_rate_is_override = True` tant que le défaut ×8 n'est pas corrigé.
- `es_cost_channel` / `es.cost.rate` — canal `vendor_bill` (facture fournisseur) vs `timesheet`
  (feuille de temps). Un coût jour à 0 = montage B, pas donnée manquante.
- `account.analytic.line` porte à la fois les feuilles de temps (`project_id` renseigné) et les
  coûts analytiques venus des factures. Filtre selon ce que tu cherches.
- `hr.leave.state` — un congé n'est bloquant qu'en état `validate`.
- `es.shooting` / `es.mission` : `manager_id` ou champ responsable — **lire `fields_get` avant
  d'écrire**, jamais supposer le nom. Vérifier que la personne a un `res.users` ; sinon proposer
  ouverture d'accès ou utilisateur existant, ne jamais créer de compte seul.
- `crm.lead` → `sale.order` → `project.project` : chaîne testée le 03/09, fonctionnelle.

### Modules maison

- **`es_production`** : `es.shooting`, `es.mission`, `es.crew.role`, `es.crew.assignment`,
  `es.crew.unavailability`, `es.equipment`, `es.cost.rate`, `es.crew.ledger`. Voir
  `references/es_production.md`. **Vérifie `ir.model` avant d'utiliser** — rabats-toi sur
  `project.task` + congés si absent.
- **`es_finance`** : budgets, trésorerie, alertes. Lit la **comptabilité**, jamais
  es_production. Voir `references/es_finance.md`.
- **`es_ops_queue`** : file d'opérations à valider (suppressions, corrections sensibles).

## Conditions de paiement (`account.payment.term`)

| ID | Libellé | Acompte | Solde |
|---|---|---|---|
| 27 | 70 % d'acompte, solde à 30 jours | 70 % à 0 j | 30 % à 30 j |
| 36 | 50 % d'acompte, solde à 30 jours | 50 % à 0 j | 50 % à 30 j |
| 34 | Paiement à la commande | 100 % | — |
| 35 | Paiement à la livraison | — | 100 % à la livraison |
| 29 | Paiement à réception de facture | — | 100 % à réception |
| 1 | Paiement immédiat | — | 100 % |
| 4 | 30 jours | — | 100 % à 30 j |
| 37 | 45 jours net | — | 100 % à 45 j |

Quinze autres conditions ont été archivées le 02/09/2026 ; ne les recrée pas.

Déclencheur d'ouverture de projet (§ Phase C) :

| Condition | Ce qui ouvre le projet |
|---|---|
| 70 % (27), 50 % (36), 100 % (34) | encaissement de l'acompte / intégralité |
| Sans acompte (1, 4, 29, 35, 37) | accord écrit seul — signaler que les dates sont bloquées sans avance |

## Étapes

**CRM** : voir `references/crm.md`. Cible : Demande reçue → Cadrage → Proforma envoyée →
Négociation → Gagnée / Perdue (motif obligatoire). Actuellement en base : Nouveau → Qualifié →
Proposition → Négociation → Gagné (anglais si `lang` non passé).

**Tâches** : Pré-production (33) → Production (29) → Post-production (34) → Validation client
(à créer si manquante) → Livré (31) + 4 satellites par session (J−2 préparation/convocation, J
captation, J+1 dérushage/sauvegarde, J+2 intégration). Vingt-six jeux d'étapes existent,
la plupart morts — vérifier qu'il porte des tâches avant de s'y appuyer. Les étapes 5 à 9
(« Boîte de réception », « Aujourd'hui »…) appartiennent au module To-do personnel.

## Comptes comptables retenus pour la production

| Poste | Compte |
|---|---|
| Chiffre d'affaires (prestations de service) | 706100 — forfait et T&E sur **deux lignes distinctes** |
| Prestations de services achetées (prestataires, freelances) | 605700 |
| Transport du personnel | 614000 |
| Transport entre établissements ou chantiers | 618200 |
| Voyages et déplacements | 618100 |
| Restauration et régie de tournage | 618400 |
| Consommables (piles, etc.) | 604100 |
| Location d'équipements et d'outils | 622300 |
| Agents temporaires (main-d'œuvre occasionnelle) | 637100 |
| Commissions et courtage sur les ventes | 632200 |

Journaux : FAC, FACTU, CSH1, EXP, PAIE. Voir `references/comptabilite.md`.

## Écriture — ce qui est permis et ce qui ne l'est pas

Permis après accord explicite de Lycris sur le contenu (validation temps 2) :

- créer un `crm.lead` / passer en Gagnée ;
- créer un `sale.order` **en brouillon** avec ses lignes (TVA retirée si date ≥ 01/10/2026) ;
- créer ou compléter des `project.task` (nom, étape, échéance, responsable) ;
- créer des `es.shooting` / `es.mission` et leurs affectations (`es.crew.assignment`) ;
- créer des `hr.expense` / écritures de caisse avec analytique projet ;
- compléter une fiche client (RCCM, compte contribuable, coordonnées) ;
- inscrire les responsables (`project.project.user_id`, `es.mission` — après `fields_get`).

Jamais, quelle que soit l'insistance :

- `action_confirm` sur une commande, `action_post` sur une facture — effets comptables, **seulement
  si explicitement inclus dans la validation temps 2** ;
- l'envoi d'un document à un client, sous n'importe quelle forme ;
- la suppression d'un enregistrement portant un historique (passer par `es_ops_queue`) ;
- une écriture directe en SQL ;
- la création d'un `res.users` sans accord (proposer seulement).

Toute écriture est annoncée après coup avec le modèle, l'identifiant et ce qui a changé, pour
que Lycris puisse aller vérifier.

## Points d'exploitation constatés

- L'écriture RPC scriptée depuis la console du navigateur est refusée par le garde-fou de
  session : passe par XML-RPC serveur, pas par le navigateur.
- Un onglet Odoo en arrière-plan ne monte aucune vue (`document.hidden` → écran blanc). Si une
  action passe par l'interface, l'onglet doit être visible.
- Les feuilles de temps valorisent le coût **au moment de leur saisie**. Après avoir renseigné
  ou corrigé un coût sur une fiche employé, il faut réécrire les lignes existantes (un `write`
  sur `unit_amount` suffit) pour déclencher le recalcul — sinon la marge reste fausse.
- Ordre impératif lors d'une bascule de coût : écrire le coût **avant** de corriger les
  quantités. L'inverse recalcule avec l'ancien tarif.
- `day_rate` par défaut ×8 connu — forcer `day_rate_is_override` à chaque affectation créée par
  le skill tant que non corrigé côté module.
- Projet fantôme « … - MODÈLE — … » (MAGGI) : vérifier `project_id` de chaque `sale.order.line`
  après confirmation ; aucun projet recréé à la main.
- **Bac à sable réseau** : en cas de `x-deny-reason` sur `manage.eventsetstudios.ci`, basculer
  sur le connecteur MCP sans réessayer en boucle.

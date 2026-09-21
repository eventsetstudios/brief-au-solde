# Odoo — connexion, modèles et pièges de cette base

Base de production d'Évents & Studios. Ce fichier décrit l'instance réelle, pas Odoo en
général : les identifiants numériques cités ont été relevés sur `odoo_db` et sont valables tant
que la configuration n'a pas bougé. En cas de doute, relis-les plutôt que de t'y fier.

## L'instance

| | |
|---|---|
| Version | Odoo 18 Community |
| Base | `odoo_db` |
| Adresse Tailscale | `http://100.119.180.128:8069` |
| Adresse LAN | `http://eventsetstudios.local:8069` (ne résout que sur le réseau local) |
| Devise | XOF (franc CFA), sans décimales |
| TVA | 18 % |
| Langue de l'interface | `fr_FR` |
| Unité de temps projet | **Jours** depuis le 07/09/2026 (1 journée = 8 h) |

**Où ça tourne.** Le serveur n'est joignable que depuis la machine de Lycris ou son réseau
Tailscale. Depuis un environnement d'exécution cloud, les deux adresses sont hors allowlist :
la connexion échouera, et c'est normal. Exécute les scripts sur sa machine (shell local) quand
c'est possible ; sinon, annonce que tu travailles sur le référentiel embarqué.

## Connexion

Odoo expose XML-RPC sur `/xmlrpc/2/common` (authentification) et `/xmlrpc/2/object`
(lecture/écriture). Les identifiants se lisent dans l'environnement :

```
ODOO_URL=http://100.119.180.128:8069
ODOO_DB=odoo_db
ODOO_USER=<login>
ODOO_PASSWORD=<mot de passe ou clé API>
```

S'ils sont absents, demande-les à Lycris plutôt que d'essayer des valeurs au hasard — trois
échecs d'authentification suffisent à faire du bruit dans les journaux.

`scripts/odoo.py` encapsule tout cela. Utilise-le plutôt que de réécrire un client.

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
| 01 | `crm.lead` | piste / opportunité. Le mode Pistes est actif mais **inutilisé** : 0 piste en base |
| 02 | `sale.order`, `sale.order.line` | devis en brouillon (`state = 'draft'`) |
| 03 | `sale.order` | passage à `state = 'sale'` par `action_confirm` — jamais automatique |
| 04, 14 | `account.move` (`move_type = 'out_invoice'`) | factures d'acompte et de solde |
| 05 | `project.project` | créé par la confirmation de commande, pas à la main |
| 07 | `project.task`, `project.task.type` | tâches et étapes |
| 08, 09 | `hr.employee`, `res.partner`, `hr.leave` | équipe, prestataires, congés |
| 10 | `account.analytic.line` | feuilles de temps **et** lignes analytiques de coût |
| 10 | `account.move` (`in_invoice`), `hr.expense` | factures fournisseurs, notes de frais |

### Champs à connaître

- `project.project.account_id` — le compte analytique. **Pas** `analytic_account_id` en v18.
- `project.project.sale_order_id` — apporté par `sale_project`, related sur `sale_line_id.order_id`.
- `hr.employee.hourly_cost` — renommé « **Coût par journée** » sur cette base après la bascule en
  jours. La valeur est donc un coût **journalier**, malgré le nom technique du champ.
- `account.analytic.line` porte à la fois les feuilles de temps (`project_id` renseigné) et les
  coûts analytiques venus des factures. Filtre selon ce que tu cherches.
- `hr.leave.state` — un congé n'est bloquant qu'en état `validate`.

### Le module maison `es_production`

En cours de développement. S'il est installé, il apporte `es.shooting` (session de tournage),
`es.crew.role`, `es.crew.assignment` (affectation avec détection de conflits), et
`es.crew.unavailability` (indisponibilité déclarée d'un externe). Ces modèles rendent la phase D
bien plus précise. **Vérifie leur présence avant de les utiliser** — sur une base où le module
n'est pas encore là, rabats-toi sur `project.task` et les congés.

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

## Étapes

**CRM** : Nouveau → Qualifié → Proposition → Négociation → Gagné. « Perdu » est un marquage
avec motif, pas une étape.

**Tâches** : le seul jeu réellement utilisé est Pré-production (33) → Production (29) →
Post-production (34) → Livré (31). Une étape **Validation client** manque entre Post-production
et Livré ; si elle n'existe toujours pas, propose-la à Lycris plutôt que de la créer d'office.

Vingt-six jeux d'étapes existent, dupliqués projet par projet, la plupart morts. Ne t'appuie pas
sur un jeu sans avoir vérifié qu'il porte des tâches. Les étapes 5 à 9 (« Boîte de réception »,
« Aujourd'hui », « Cette semaine »…) appartiennent probablement au module To-do personnel :
ne pas y toucher sans vérifier `user_id`.

## Comptes comptables retenus pour la production

| Poste | Compte |
|---|---|
| Chiffre d'affaires (prestations de service) | 706100 |
| Prestations de services achetées (prestataires, freelances) | 605700 |
| Transport du personnel | 614000 |
| Transport entre établissements ou chantiers | 618200 |
| Voyages et déplacements | 618100 |
| Restauration et régie de tournage | 618400 |
| Consommables (piles, etc.) | 604100 |
| Location d'équipements et d'outils | 622300 |
| Agents temporaires (main-d'œuvre occasionnelle) | 637100 |
| Commissions et courtage sur les ventes | 632200 |

La société ne vend aucune marchandise : tout le chiffre d'affaires relève de 706100.

## Écriture — ce qui est permis et ce qui ne l'est pas

Permis après accord explicite de Lycris sur le contenu :

- créer un `sale.order` **en brouillon** avec ses lignes ;
- créer ou compléter des `project.task` (nom, étape, échéance, responsable) ;
- créer des affectations d'équipe et des feuilles de temps ;
- compléter une fiche client (RCCM, compte contribuable, coordonnées).

Jamais, quelle que soit l'insistance :

- `action_confirm` sur une commande, `action_post` sur une facture — effets comptables ;
- l'envoi d'un document à un client, sous n'importe quelle forme ;
- la suppression d'un enregistrement portant un historique ;
- une écriture directe en SQL.

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

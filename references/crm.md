# CRM — opportunités et pipeline

## État connu au 08/09/2026

- Module `crm` installé.
- **Mode Pistes non activé** — 0 piste en base, normal.
- **0 opportunité** — aucune affaire ne vit encore dans le CRM.
- Étapes CRM en anglais si `lang` non passé (piège `fr_FR` — voir `references/odoo.md`).
- Test bout-en-bout du **03/09** : la chaîne **opportunité → devis → projet → tâches**
  (`crm.lead` → `sale.order` → `project.project` → `project.task`) fonctionne via
  `sale_crm` / `sale_project`.

## Rôle du CRM dans le workflow

Le CRM est **l'étape 01** du processus. Toute demande entrante devient une opportunité
avant de devenir une commande. C'est l'endroit où l'on suit ce qui n'est pas encore gagné.

### Décision du 21/09/2026

**Les deux pipelines restent, le CRM est le principal.**

- Toute affaire client naît et vit dans le **CRM** (`crm.lead`) : c'est la seule saisie.
- **es_finance lit et écrit sur le CRM** : « Projets à venir » affiche les opportunités CRM
  (revenu attendu, probabilité, date) et les fait entrer dans la prévision de trésorerie ;
  une modification faite depuis es_finance (montant, date de règlement attendue, probabilité)
  s'écrit sur l'opportunité CRM, pas sur une fiche séparée.
- `es.finance.pipeline` ne garde en propre que les **projets internes** (véhicule, matériel,
  locaux, recrutement…), qui n'ont pas de client.
- Correspondance d'étapes à définir entre CRM et es_finance (idée / chiffré / validé /
  abandonné ↔ étapes CRM), et règle anti-doublon : une opportunité gagnée convertie en
  projet sort de la prévision « À venir » au profit des lignes de commande.
- Si ce lien CRM ↔ es_finance n'existe pas encore dans le code, le skill le signale comme
  **développement à faire** (nouvelle version d'es_finance) et **ne crée jamais** de fiche
  `es.finance.pipeline` pour une affaire client en attendant — il écrit uniquement dans `crm.lead`.

## Ce que porte une opportunité

| Champ Odoo | Contenu |
|---|---|
| `partner_id` | client (ou création proposée si nouveau — jamais silencieuse) |
| `contact_name`, `phone`, `email` | qui valide côté client |
| `expected_revenue` / `planned_revenue` | revenu attendu (montant de la future commande) |
| `probability` | probabilité en % |
| `date_deadline` | date de clôture visée / échéance de réponse |
| `source_id`, `tag_ids` | source, apporteur, canal |
| `stage_id` | étape — voir ci-dessous |
| `user_id` | commercial / chargé de projet |
| `description` | note de cadrage courte |

Le skill propose l'opportunité comme **brouillon à valider**, jamais créée en silence si le
client n'existe pas encore (recherche avec score parmi les 263 partenaires).

## Étapes proposées (à valider par Lycris, non appliquées seules)

Calées sur les 14 étapes du workflow, en français :

```
Demande reçue  →  Cadrage  →  Proforma envoyée  →  Négociation  →  Gagnée / Perdue
     01              06            02                  03-05         03
```

- **Demande reçue** : opportunité créée, premier tour de questions lancé (sans chiffrage).
- **Cadrage** : note de cadrage produite, dispositif et livrables fixés.
- **Proforma envoyée** : tableau d'arbitrage validé, XLSX/PDF émis (non envoyé par le skill).
- **Négociation** : retours prix / périmètre en cours.
- **Gagnée** : déclenche la cascade (devis → projet …) — voir `references/workflow-commande.md`.
- **Perdue** : marquage avec **motif obligatoire** (prix, délai, périmètre, abandon client, autre).

Le jeu actuel en base (Nouveau → Qualifié → Proposition → Négociation → Gagné) est à
remplacer par ce jeu une fois validé. Proposer la migration, ne jamais l'écrire sans accord.

## Relances

- Opportunités **sans activité depuis N jours** (fil ou `date_last_stage_update`).
- Proformas envoyées **sans réponse** après la date de validité.
- Le skill les lit et les résume (ex. au « point du lundi »), il n'en crée pas de doublon.

## Lien avec es_finance « À venir »

```
crm.lead (opportunité)  ──→  es_finance « Projets à venir »
       │  expected_revenue × probability  →  prévision de trésorerie (optimiste / médiane / prudente)
       │  date_deadline  →  date de règlement attendue
       └─  Gagnée → sortie de « À venir », remplacée par sale.order / account.move
```

- Pas de double comptage : une opportunité Gagnée convertie en commande sort de la
  prévision « À venir ».
- Projets internes (`es.finance.pipeline` avec `partner_id = False`) restent affichés dans
  « À venir » à côté des opportunités, avec leur propre prévision.
- Le skill **n'écrit jamais deux fois** la même affaire (une fois en CRM, une fois en pipeline).

## Commandes liées au CRM

- « nouvelle demande de X » → crée l'opportunité + premier tour de questions (B-C-D),
  sans chiffrage (reste en Demande reçue / Cadrage).
- « j'ai une commande » → crée ou passe l'opportunité en Gagnée puis cascade.
- Le devis est toujours créé **depuis l'opportunité** (bouton « Nouveau devis »), pour que le
  lien `opportunity_id` soit posé.

# brief-au-solde

Skill OpenCode qui fait tourner le processus d'Évents & Studios **du brief au solde** — 14 étapes, du premier contact client jusqu'à la facture soldée et à la FNE émise.

> Pour Joël-Christian Lopy (Lycris), solopreneur — gérant, directeur artistique, commercial et chef de projet. Le skill interroge Odoo, chiffre par analogie avec les affaires déjà réalisées, propose une équipe et ne crée rien sans validation.

- Repo : https://github.com/eventsetstudios/brief-au-solde
- Skill ID : `brief-au-solde` (`SKILL.md`)
- Langue : français, montants en F CFA

## Le workflow en 6 phases + le mode commande

| Phase | Étapes | Ce qui se passe |
|-------|--------|-----------------|
| **A. Cadrage** | 01, 06 | Lit Odoo (client, historique), pose seulement les questions qui changent le prix/l'équipe, produit une note de cadrage |
| **B. Chiffrage** | 02 | Analogie avec les affaires comparables, catalogue 14 produits (TVA 0 depuis 01/10/2026), coût de revient, marge cible 65% (alerte <60%), proforma XLSX+PDF |
| **C. Ouverture** | 03-05 | Vérifie l'accord écrit, gère le déclencheur selon condition de paiement (avec/sans acompte), rattache la note au projet |
| **D. Equipe & tâches** | 06-09 | Découpe Pré-prod → Livré + 4 satellites par session, propose titulaire + alternative par rôle (dispo, expérience, délais, coût), responsables obligatoires, feuille de service |
| **E. Suivi** | 10 | Vigie : retards, feuilles de temps manquantes, écart coût réel >10%, dépenses non rattachées, marge sur la compta (es_finance) |
| **F. Validation → Solde** | 11-14 | Retours consolidés, corrections vs avenants, livraison actée, facture de solde depuis la même commande, FNE |

**Mode « j'ai une commande »** : Lycris dit une phrase (« j'ai une commande », « X m'a commandé… »), le skill déroule en 3 temps — questionnaire par séries de 4-6 hypothèses cliquables (client, travail, calendrier/lieux, responsables obligatoires, dispositif/équipe, T&E, argent) → validation unique → cascade 9 étapes (CRM → devis → projet → facture acompte → es.deal/budget → sessions/missions/affectations → responsables → feuilles de service). Voir `references/workflow-commande.md`.

**Règle d'or :** `lire` est libre, `écrire` seulement après accord explicite sur le contenu exact (validation temps 2). Le skill annonce ensuite les IDs créés. Confirmation de commande et comptabilisation de facture restent brouillon sauf inclusion explicite dans la validation.

## Décisions 21/09/2026

| Sujet | Décision |
|---|---|
| Accès | `https://manage.eventsetstudios.ci` (public) — Tailscale en secours |
| Marge | Chargé de production ne voit pas la marge ; elle vit dans es_finance, direction seule |
| TVA | Plus aucune TVA facturée à partir d'octobre 2026 |
| Pipelines | CRM principal, es_finance lit/écrit sur le CRM |
| Responsables | Toujours un chargé de projet + un chargé de mission par mission |

## Installation comme skill OpenCode

### Option 1 — Projet (recommandé)
```bash
git clone https://github.com/eventsetstudios/brief-au-solde.git .opencode/skills/brief-au-solde
```
Découverte automatique via `.opencode/skills/` — aucune config `opencode.json` nécessaire. ID = `brief-au-solde`.

### Option 2 — Global
```bash
git clone https://github.com/eventsetstudios/brief-au-solde.git ~/.config/opencode/skills/brief-au-solde
```

### Option 3 — Via `skills` dans `opencode.json`
```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "skills": ["https://github.com/eventsetstudios/brief-au-solde.git"]
}
```

Vérification :
```bash
# le skill apparaît dès qu'il est question de brief, devis, proforma, équipe...
# ou chargement explicite :
# /skill brief-au-solde
```

## Structure

```
.
├── SKILL.md              # Workflow complet (267 lignes, 6 phases + mode commande + garde-fous)
├── assets/
│   └── LISEZ-MOI.md
├── references/
│   ├── odoo.md           # Connexion (manage.eventsetstudios.ci + MCP), modèles, pièges
│   ├── referentiel.md    # Catalogue 14 produits (TVA 0), prix, coûts/jour, équipe, projets ref.
│   ├── devis.md          # Méthode de chiffrage par analogie (TVA octobre 2026)
│   ├── workflow-commande.md # Mode « j'ai une commande » — 3 temps, questionnaire, cascade
│   ├── crm.md            # CRM — opportunités, étapes, lien es_finance
│   ├── es_production.md  # Projet/Session/Mission, parc, ledger, frontière marge
│   ├── es_finance.md     # Trésorerie, budgets, alertes, marge sur la compta
│   ├── comptabilite.md   # Plan comptable, journaux, FNE, TVA octobre 2026
│   ├── routines.md       # 9 commandes en une phrase + automatismes solopreneur
│   ├── modeles-affaires.md # Modèles par type d'affaire (dispositif/équipe/tâches/lignes)
│   └── production.md     # Standard studio : arborescence NAS, nommage, pipeline, 3 phases, tri auto
├── evals/                # 9 cas de test (commande simple, tournée, sans RCCM, apporteur…)
└── scripts/
    ├── odoo.py           # Client MCP/XML-RPC : ping, client, projet, catalogue, equipe + list_invoices, create_dynamic_field
    ├── analogues.py      # Affaires comparables (montant, jours, marge) + suggestions prix (--suggest, backend matching)
    ├── matching.py       # Matching factures ≤ 13 mois : normalisation, TF-IDF, scoring, stats + sources
    ├── proposal.py       # Wizard proposition guidée : proposal.json + audit (--start, --input, --to-proforma)
    ├── scaffold.py       # Scaffold NAS : arborescence, tri auto, nommage, miroir Odoo, 3 phases
    ├── equipe.py         # Disponibilité + expérience + délais + coût
    ├── proforma.py       # Génère XLSX + PDF à la charte (TVA 0 si ≥ 01/10/2026, consomme proposal.json via --to-proforma)
    └── commande.py       # Fiche JSON → plan dry-run puis exécution cascade
├── migrations/
│   └── 001_add_pricing_history_and_dynamic_fields.sql  # UP + DOWN (PostgreSQL + SQLite)
├── tests/                # pytest : test_matching.py (cas A/B/C) + test_proposal.py (migration, audit, proforma)
├── requirements.txt      # pytest seul (matching = stdlib ; variante sklearn documentée)
└── logs/                 # proposals.log — audit JSON (git-ignoré via *.log)
```

## Prérequis Odoo

La base porte 263 clients + historique Dolibarr. Le skill lit d'abord Odoo avant de poser une question.

```bash
python3 scripts/odoo.py ping
```

Ordre de connexion : 1) Connecteur MCP Odoo si présent, 2) XML-RPC sur `https://manage.eventsetstudios.ci`, 3) référentiel embarqué.

Si `ok: false`, renseigne les identifiants :

```bash
# fichier (recommandé)
cat > ~/.odoo_es.json <<'JSON'
{"url":"https://manage.eventsetstudios.ci","db":"...","user":"...","password":"..."}
JSON

# ou variables d'env
export ODOO_URL=https://manage.eventsetstudios.ci
export ODOO_DB=...
export ODOO_USER=...
export ODOO_PASSWORD=...

python3 scripts/odoo.py ping
```

Sans Odoo (ou `x-deny-reason` sur le domaine en bac à sable filtré), le skill bascule sur le MCP ou sur `references/referentiel.md` — il l'annonce explicitement.

## Commandes rapides

```bash
python3 scripts/odoo.py ping                          # test connexion
python3 scripts/odoo.py client 42                     # fiche client
python3 scripts/odoo.py projet 123                    # état complet d'une affaire
python3 scripts/odoo.py factures --client 45          # lignes de factures (fallback référentiel si échec)
python3 scripts/analogues.py --client 832 --produits 107,112 --jours 2
python3 scripts/analogues.py --suggest VID_MO1 --label "Spot 60s" --client 45  # prix suggéré
python3 scripts/equipe.py --du 2026-10-12 --au 2026-10-13 --roles cadreur,drone
python3 scripts/proposal.py --start                   # wizard proposition guidée
python3 scripts/proposal.py --input brief.json --output proposal.json
python3 scripts/proposal.py --to-proforma proposal.json --numero PRO-2026-014  # vers proforma.py
python3 scripts/scaffold.py --init --client NESTLE --projet MAGGI_TVC --jours 2026-11-14  # dry-run arborescence
python3 scripts/scaffold.py --trier J01_2026-11-14_A-CAM_001.BRAW film_V02.mp4 --client X --projet Y
python3 scripts/scaffold.py --verifier-nom NESTLE_MAGGI_TVC_V1_2026-09-21.mp4
python3 scripts/scaffold.py --statut --dossier-actif 04_pre-rendus/V02
python3 scripts/proforma.py --data proforma.json      # XLSX + PDF
python3 scripts/commande.py --exemple > fiche.json    # fiche modèle
python3 scripts/commande.py --fichier fiche.json --dry-run   # plan sans écrire
python3 scripts/commande.py --fichier fiche.json --executer  # écrit après validation
pytest tests/ -q                                      # 19 tests matching + proposal + migration
```

## Proposition guidée (matching factures ≤ 13 mois)

`scripts/proposal.py --start` déroule le wizard en 5 étapes (client → contexte →
livrables → tarification → résumé). Sans historique pertinent, il répond exactement
« Je ne peux pas confirmer ça » et demande une saisie manuelle — jamais de prix inventé.
Chaque suggestion porte ses sources (IDs factures, dates) et stats ; chaque calcul est
audité dans `logs/proposals.log`. Détail : section « Proposition guidée » de `SKILL.md`.

Exemple d'entrée (`brief.json`) :

```json
{
  "brief_id": 123,
  "client_id": 45,
  "services": [
    { "service_code": "VID_MO1", "label": "Spot 60s", "qty": 1, "unit": "video" },
    { "service_code": "MONT_H", "label": "Montage horaire", "qty": 10, "unit": "hour" }
  ],
  "currency": "XOF"
}
```

Exemple de sortie (`proposal.json`, item confirmé) :

```json
{
  "suggested_items": [
    {
      "service_code": "VID_MO1",
      "label": "Spot 60s",
      "qty": 1,
      "unit_price_suggested": 750000,
      "stats": {"mean": 720000, "median": 750000, "min": 600000, "max": 800000, "std": 81923, "count": 4},
      "source_invoices": [{"invoice_id": 789, "date": "2026-03-12", "amount": 750000}]
    }
  ],
  "notes": "Basé sur 4 factures similaires (≤13 mois)."
}
```

Scoring : cosinus TF-IDF (descriptions) + 1,0 même `service_code` + 0,3 même
catégorie, filtre ≤ 13 mois, seuil 0,45, priorité au même client, prix suggéré =
médiane. Implémentation pure-python (stdlib) — variante `scikit-learn` possible à
interface identique si le volume l'exige un jour.

## Standard studio (NAS + nommage + pipeline)

`references/production.md` + `scripts/scaffold.py` : arborescence
`CLIENT/année/Projet/01_creation → 05_rendus` générée d'un coup (`--init`,
`--appliquer` pour écrire), tri auto au dépôt (rush → `02_footages`, `Vxx` →
`04_pre-rendus`, master/final sans version → `05_rendus`), nommage
`CLIENT_PROJET_TYPE_VERSION_DATE.ext` contrôlé (`--verifier-nom`), statut Odoo =
miroir du dossier actif (`--statut`), facturation en 3 phases
pré-prod/prod/post-prod (`--phases`). Rushs immutables, versions V01/V02…,
toute sortie : résumé → découpage → planning → budget → dossiers → risques.

Checklist QA :

- [ ] Migrations OK & rollback testés (`pytest tests/test_proposal.py -q -k migration`)
- [ ] Tests unitaires passant (`pytest tests/ -q` — 19 tests)
- [ ] Cas A/B/C couverts (client avec facture / sans facture mais ≤ 13 mois / aucune)
- [ ] Logs d'audit présents et lisibles (`logs/proposals.log`, JSON par ligne)
- [ ] Texte exact « Je ne peux pas confirmer ça » implémenté
- [ ] Fallback Odoo → référentiel embarqué documenté (source annoncée)

Guide d'intégration (3 lignes) :

```bash
python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt && pytest tests/ -q
```

Identifiants Odoo dans `~/.odoo_es.json` (`url`, `db`, `user`, `password`) ou
variables `ODOO_URL` / `ODOO_DB` / `ODOO_USER` / `ODOO_PASSWORD` — jamais dans le repo.

Routines solopreneur (voir `references/routines.md`) :

| Tu dis | Le skill fait |
|---|---|
| « j'ai une commande » | Questionnaire 3 temps → validation → cascade |
| « nouvelle demande de X » | Opportunité CRM + premiers questions |
| « point du lundi » | Synthèse étapes, retards, semaine, argent, FNE, responsables |
| « clôture la mission » | Présences, dépenses au réel, cachets, J+1/J+2 |
| « j'ai dépensé X pour Y » | Écriture caisse/note de frais avec analytique |
| « où en est l'argent » | Trésorerie 3 scénarios + répartition + échéances |
| « je peux facturer ? » | Contrôle livraison + fiche client + FNE |
| « bilan de l'affaire » | Marge réelle (compta) vs prévisionnel |

## Catalogue (extrait `referentiel.md`)

| ID | Produit | Prix XOF |
|----|---------|----------|
| 106 | Réalisation film publicitaire | 750 000 |
| 107 | Captation / couverture d'événement | 650 000 / jour |
| 111 | Reportage photo | 350 000 / jour |
| 112 | Captation drone | 760 000 / jour |
| 109 | Montage / post-production | 700 000 |
| 119 | Frais refacturés | au réel |

TVA 0 depuis 01/10/2026, 14 produits (IDs 106-119 relevés en base le 21/09/2026). Les produits 114,115,118 sont à 1 F en base (« à fixer ») — ne pas utiliser sans prix Lycris. Seul le 107 est déjà sans taxe, les 13 autres portent encore la taxe 18 % à vider ligne à ligne.

## Garde-fous

- Jamais d'écriture Odoo sans accord explicite sur le contenu exact (validation temps 2).
- Jamais d'envoi client (devis/facture/relance) — le skill prépare, Lycris envoie.
- Jamais de confirmation de commande / validation de facture auto sans inclusion explicite.
- Toujours `{'lang':'fr_FR'}` en contexte RPC.
- Réponses en français, tableau d'arbitrage d'abord.
- Marge invisible à l'équipe — ne jamais l'inscrire dans une feuille de service ou tâche.
- TVA : signaler le cas acompte avec TVA / solde sans, ne jamais corriger seul.

## Identité légale (pied de proforma)

EVENTS & STUDIOS SARLU — RCCM CI-ABJ-2018-B-04133 — CC 1807549B — Abidjan Cocody Riviera 5, 23 BP 1307 Abidjan 23 — contact@eventsetstudios.ci

## Licence

Usage interne Évents & Studios.

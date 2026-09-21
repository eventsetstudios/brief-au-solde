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
│   └── modeles-affaires.md # Modèles par type d'affaire (dispositif/équipe/tâches/lignes)
├── evals/                # 9 cas de test (commande simple, tournée, sans RCCM, apporteur…)
└── scripts/
    ├── odoo.py           # Client MCP/XML-RPC : ping, client, projet, catalogue, equipe
    ├── analogues.py      # Affaires comparables (montant, jours, marge)
    ├── equipe.py         # Disponibilité + expérience + délais + coût
    ├── proforma.py       # Génère XLSX + PDF à la charte (TVA 0 si ≥ 01/10/2026)
    └── commande.py       # Fiche JSON → plan dry-run puis exécution cascade
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
python3 scripts/analogues.py --client 832 --produits 96,101 --jours 2
python3 scripts/equipe.py --du 2026-10-12 --au 2026-10-13 --roles cadreur,drone
python3 scripts/proforma.py --data proforma.json      # XLSX + PDF
python3 scripts/commande.py --exemple > fiche.json    # fiche modèle
python3 scripts/commande.py --fichier fiche.json --dry-run   # plan sans écrire
python3 scripts/commande.py --fichier fiche.json --executer  # écrit après validation
```

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
| 95 | Réalisation film publicitaire | 750 000 |
| 96 | Captation / couverture d'événement | 600 000 / jour |
| 100 | Reportage photo | 350 000 / jour |
| 101 | Captation drone | 760 000 / jour |
| 98 | Montage / post-production | 700 000 |
| 108 | Frais refacturés | au réel |

TVA 0 depuis 01/10/2026, 14 produits. Les produits 103,104,107,108 sont à 1 F en base (« à fixer ») — ne pas utiliser sans prix Lycris.

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

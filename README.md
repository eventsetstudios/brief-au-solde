# brief-au-solde

Skill OpenCode qui fait tourner le processus d'Évents & Studios **du brief au solde** — 14 étapes, du premier contact client jusqu'à la facture soldée.

> Pour Joël-Christian Lopy (Lycris), gérant d'Évents & Studios. Le skill interroge Odoo, chiffre par analogie avec les affaires déjà réalisées, propose une équipe et ne crée rien sans validation.

- Repo : https://github.com/eventsetstudios/brief-au-solde
- Skill ID : `brief-au-solde` (`SKILL.md`)
- Langue : français, montants en F CFA

## Le workflow en 6 phases

| Phase | Étapes | Ce qui se passe |
|-------|--------|-----------------|
| **A. Cadrage** | 01, 06 | Lit Odoo (client, historique), pose seulement les questions qui changent le prix/l'équipe, produit une note de cadrage |
| **B. Chiffrage** | 02 | Analogie avec les affaires comparables, catalogue 14 produits, coût de revient, marge cible 65% (alerte <60%), proforma XLSX+PDF |
| **C. Ouverture** | 03-05 | Vérifie l'accord écrit, gère le déclencheur selon condition de paiement (avec/sans acompte), rattache la note au projet |
| **D. Equipe & tâches** | 06-09 | Découpe Pré-prod → Livré, propose titulaire + alternative par rôle (dispo, expérience, délais, coût), feuille de service |
| **E. Suivi** | 10 | Vigie : retards, feuilles de temps manquantes, écart coût réel >10%, dépenses non rattachées |
| **F. Validation → Solde** | 11-14 | Retours consolidés, corrections vs avenants, livraison actée, facture de solde depuis la même commande, FNE |

**Règle d'or :** `lire` est libre, `écrire` seulement après accord explicite sur le contenu exact. Le skill annonce ensuite les IDs créés.

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
├── SKILL.md              # Workflow complet (14 étapes, garde-fous)
├── assets/
│   └── LISEZ-MOI.md
├── references/
│   ├── odoo.md           # Connexion, modèles Odoo, pièges de la base
│   ├── referentiel.md    # Catalogue 14 produits, prix, coûts/jour, équipe, conditions de paiement
│   └── devis.md          # Méthode de chiffrage par analogie
└── scripts/
    ├── odoo.py           # Client XML-RPC : ping, client, projet, catalogue, equipe
    ├── analogues.py      # Affaires comparables (montant, jours, marge)
    ├── equipe.py         # Disponibilité + expérience + délais + coût
    └── proforma.py       # Génère XLSX + PDF à la charte
```

## Prérequis Odoo

La base porte 263 clients + historique Dolibarr. Le skill lit d'abord Odoo avant de poser une question.

```bash
python3 scripts/odoo.py ping
```

Si `ok: false`, renseigne les identifiants (serveur joignable uniquement depuis la machine de Lycris / Tailscale) :

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

Sans Odoo, le chiffrage repose sur `references/referentiel.md` (relevé 07/09/2026) — le skill l'annonce explicitement.

## Commandes rapides

```bash
python3 scripts/odoo.py ping                          # test connexion
python3 scripts/odoo.py client 42                     # fiche client
python3 scripts/odoo.py projet 123                    # état complet d'une affaire
python3 scripts/analogues.py --type captation --client 42
python3 scripts/equipe.py --du 2026-10-12 --au 2026-10-13 --roles cadreur,drone
python3 scripts/proforma.py --data proforma.json      # XLSX + PDF
```

## Catalogue (extrait `referentiel.md`)

| ID | Produit | Prix XOF |
|----|---------|----------|
| 95 | Réalisation film publicitaire | 750 000 |
| 96 | Captation / couverture d'événement | 600 000 / jour |
| 100 | Reportage photo | 350 000 / jour |
| 101 | Captation drone | 760 000 / jour |
| 98 | Montage / post-production | 700 000 |
| 108 | Frais refacturés | au réel |

TVA 18%, 14 produits. Les produits 103,104,107,108 sont à 1 F en base (« à fixer ») — ne pas utiliser sans prix Lycris.

## Garde-fous

- Jamais d'écriture Odoo sans accord explicite.
- Jamais d'envoi client (devis/facture/relance) — le skill prépare, Lycris envoie.
- Jamais de confirmation de commande / validation de facture auto.
- Toujours `{'lang':'fr_FR'}` en contexte RPC.
- Réponses en français, tableau d'arbitrage d'abord.

## Identité légale (pied de proforma)

EVENTS & STUDIOS SARLU — RCCM CI-ABJ-2018-B-04133 — CC 1807549B — Abidjan Cocody Riviera 5, 23 BP 1307 Abidjan 23 — contact@eventsetstudios.ci

## Licence

Usage interne Évents & Studios.

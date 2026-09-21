# Routines — automatiser pour un solopreneur

Lycris est seul à tout porter. Le skill réduit le coût de chaque interaction à **une phrase**,
puis fait le reste en ne posant que ce qu'il ne peut pas savoir. Ce fichier liste les
commandes en une phrase, leurs lectures, leurs produits et les cas particuliers.

Toutes les routines respectent la règle **lire → proposer → attendre l'arbitrage → écrire**
et les garde-fous de `SKILL.md` (marge invisible à l'équipe, TVA octobre 2026, responsables
obligatoires, etc.).

---

## Commandes en une phrase

| Phrase type (exemples) | Ce que lit le skill | Ce qu'il produit | Ce qu'il propose d'écrire |
|---|---|---|---|
| **« j'ai une commande »** / « X m'a commandé… » / « on a un nouveau job » | Fiche client, affaires comparables, dispos, ledger | Fiche commande + tableau d'arbitrage + plan de cascade | Cascade complète en 9 étapes (voir `workflow-commande.md`) — après validation unique |
| **« nouvelle demande de X »** | Fiche client (ou recherche), affaires comparables | Opportunité CRM en Demande reçue + premier tour de questions (B-C-D) | `crm.lead` (puis cadrage), sans chiffrage |
| **« point du lundi »** | Affaires en cours par étape, tâches en retard/sans responsable, sessions/missions de la semaine (jours + responsables), alertes es_finance, encaissements attendus, factures à émettre, FNE en attente, projets sans chargé de projet / missions sans chargé de mission, ledger | Synthèse d'une page : par étape, retards, semaine à venir, argent, alertes, manques de responsables | Activités de rappel datées (`mail.activity`) — relance acompte, J−2, livraison, solde, FNE |
| **« clôture la mission / la session »** (avec id ou nom) | `es.shooting`/`es.mission`, `es.crew.assignment`, dépenses au réel, tâches | Présences, dépenses au réel, cachets, compte rendu, avancement des tâches | Séquence 6-10 de `es_production.md` : `attendance_state`, `hr.expense`/`account.move` avec analytique, `es.shooting.state = done`, tâches satellites J+1/J+2 |
| **« j'ai dépensé X pour Y »** | Projet (déduit ou demandé), comptes (`references/comptabilite.md`), analytique | Écriture pré-remplie : montant, compte, journal (CSH1/EXP), analytique | `account.move` (caisse) ou `hr.expense` en brouillon avec `analytic_distribution` du projet — **exige l'analytique** (67 % non rattachées) |
| **« fin de mois intervenants »** | `es.crew.ledger` + affectations du mois | Relevé par intervenant : jours dus, montant, canal | Décompte arrêté fin de mois, paiements dus au 15 — brouillon `hr.expense` / `account.move` fournisseur par personne, jamais d'envoi |
| **« où en est l'argent »** | es_finance Trésorerie (3 scénarios), Répartition, Emprunts/échéances, charges récurrentes | Synthèse : trésorerie optimiste/médiane/prudente, répartition (dettes d'abord), échéances à 7 j / en retard, charges à valider | Brouillons de charges récurrentes si demandé, toujours en brouillon |
| **« je peux facturer ? »** | Livraison actée (tâche Livré / PV), fiche client (RCCM/CC), `sale.order` + `account.move`, FNE | Contrôle : livraison oui/non, fiche complète oui/non, montant/échéance du solde, FNE | Facture de solde **depuis la même commande** (brouillon), rappel du montant et de l'échéance selon condition de paiement |
| **« bilan de l'affaire »** (avec projet/opportunité) | Compta : vendu, dépensé en compta, marge sur la compta (es_finance) + prévisionnel phase B | Tableau réel vs prévisionnel, écart, causes (commission, T&E, jours supplémentaires) | Leçon consignée pour le prochain chiffrage (note sur `project.project` / `es.deal`), jamais affichée à l'équipe |

Toute phrase qui contient un nom de client, une ville ou une date déclenche la lecture Odoo
avant de répondre — même si l'utilisateur ne cite pas Odoo.

---

## Automatismes transverses

### Modèles par type d'affaire

Voir `references/modeles-affaires.md` pour les valeurs par défaut (dispositif, équipe,
tâches, lignes) tirées des affaires réelles :

- Captation 1 jour Abidjan
- Festival 2 jours Abidjan / Grand-Bassam
- Tournée multi-villes (DABOSA)
- Spot / film publicitaire

Le skill les applique comme **hypothèse de départ** (à confirmer), pas comme vérité.

### Écritures groupées

- Une seule validation pour tout un lot, jamais une validation par objet.
- La cascade commande (9 étapes) est un seul lot. La clôture de mission (6-10) est un seul lot.
  Le point du lundi ne crée que des **activités** (une seule validation pour N rappels).
- Toute modification relance le récapitulatif, pas tout le questionnaire.

### Brouillons de messages (jamais envoyés)

Le skill **prépare**, Lycris **envoie**. Pour chaque envoi prévu, le skill produit un texte
prêt à copier :

- **Relance acompte** : montant, échéance, RIB, ton sobre.
- **Convocation prestataire** : lieu, heure de convocation, matériel, contact sur place, déroulé
  (lisible sur téléphone, debout, en plein soleil).
- **Envoi de proforma** : objet, corps, validité, condition de paiement, lignes.
- **Relance solde / FNE** : référence facture, montant, échéance, mention FNE.

Aucun `mail.compose.message` n'est envoyé automatiquement ; le skill ouvre au mieux le
compositeur pré-rempli, mais ne clique pas sur Envoyer.

### File d'attente

Pour ce que le skill ne peut pas exécuter (suppressions, corrections sensibles, retraits de
taxe en masse), passer par la file **`es_ops_queue`** « Opérations à valider » (modèle
`es.ops.queue` si installé, sinon `mail.activity` avec tag). Le skill y dépose une fiche
avec modèle, ids, valeurs avant/après, et attend la validation dans Odoo.

---

## Ce qui déclenche quelle routine — aide-mémoire

```
« j'ai une commande »              → workflow-commande.md (3 temps)
« nouvelle demande de … »          → crm.md (opportunité)
« point du lundi »                 → cette page + es_finance.md + es_production.md
« clôture la mission … »           → es_production.md (10 points, 6-10)
« j'ai dépensé … »                → comptabilite.md (caisse TTC sans TVA, analytique)
« fin de mois intervenants »       → es_production.md (ledger)
« où en est l'argent »            → es_finance.md (trésorerie / répartition)
« je peux facturer ? »            → comptabilite.md (RCCM/CC) + FNE
« bilan de l'affaire »            → es_finance.md (marge sur la compta)
```

Chaque routine commence par `python3 scripts/odoo.py ping` (ou MCP) et `{'lang':'fr_FR'}`.
Si la connexion échoue, le dire tout de suite et basculer sur le référentiel.

---

## Garde-fous spécifiques aux routines

- « je peux facturer ? » sans livraison actée → refuser de facturer, proposer de consolider
  les retours et de faire valider la livraison d'abord.
- Dépense sans projet → exiger l'analytique, ne jamais laisser 67 % s'aggraver.
- Commande dont le chargé de mission désigné n'a pas de compte Odoo → signaler, proposer
  ouverture d'accès ou utilisateur existant, ne pas créer de compte seul.
- Facture/solde à cheval sur octobre 2026 avec TVA → montrer l'écart, laisser arbitrer.

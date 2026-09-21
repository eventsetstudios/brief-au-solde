# es_finance — pilotage de l'argent

Référence pour le module maison `es_finance` (trésorerie et pilotage financier). Le skill
lit es_finance quand il est installé et en résume l'état ; il n'y écrit que le budget du
projet et ne crée jamais de fiche « À venir » pour une affaire client.

Source : notes es_finance 1.0.0, 2.0.0, 2.1.0, 3.0.0, 3.1.0, frontière du 18/09,
`claude_es-finance-marge-projets-sans-commande-17-09-2026.md`,
`claude_emprunt-bmf-saisi-dans-odoo-18-09-2026.md`, et le code `studiOS` / `es_finance`
quand disponible.

---

## Principe cardinal

> **es_finance lit la comptabilité et la facturation, jamais es_production.**

En phase E et F, la marge de référence est **« Marge sur la compta »** (colonne
« Dépensé en compta » — `account.analytic.line` + `account.move` / `hr.expense`), pas
l'ancienne colonne « Coût réel » d'es_production. C'est ce qui rend la marge fiable et
compatible avec la comptabilité.

Conséquence directe de la décision marge du 21/09/2026 : la **marge ne vit plus que dans
es_finance**, réservée à la direction. es_production ne l'affiche plus (voir
`references/es_production.md`). Le skill ne la montre qu'à Lycris.

---

## Onglets et usages

| Onglet | Ce qu'on y lit | Comment le skill s'en sert |
|---|---|---|
| **Trésorerie** | Prévision **optimiste / médiane / prudente** (opportunités pondérées + factures attendues + charges fixes) | « où en est l'argent » — synthèse en une phrase + montants |
| **Projets** | Chaque `project.project` avec vendu, dépensé en compta, marge sur la compta, budget vs réel | Phase E : écart > 10 %, phase F : bilan réel vs prévisionnel |
| **À venir** | Clients (opportunités CRM) + projets internes (véhicule, matériel, locaux…), décisions à 60 jours | Point du lundi : encaissements attendus, décisions à prendre. **Anti-doublon** : une opportunité Gagnée sort d'À venir |
| **Dépenses** | Prévu vs réel par projet, par nature, par période | À chaque dépense saisie : exiger/proposer l'analytique projet (67 % non rattachées) |
| **Répartition** | Dettes d'abord, puis enveloppes (charges fixes, production, investissement) | « où en est l'argent » — que payer en premier |
| **Alertes** | Voir ci-dessous | Le skill les lit et les résume, il n'en crée pas de doublon |
| **Emprunts et échéances** | Échéances de prêt (BMF, etc.), charges récurrentes | Alertes à 7 jours / en retard, brouillons à valider |

---

## Alertes existantes (le skill les lit et les résume)

- **Dépassement de budget** : réel > budget (seuil 80 % en alerte, 100 % en dépassement).
- **Freelance payé sans projet** : `hr.expense` / `account.move` sans `analytic_distribution`.
- **Dépense sans projet** : toute écriture sans analytique projet — chantier de fond
  (67 % des dépenses non rattachées).
- **Charge récurrente non constatée** : abonnement attendu mais non saisi.
- **Échéance de prêt à 7 jours / en retard** (BMF et autres).
- **Brouillons de charges récurrentes à valider** (factures `draft`).

Le skill ne **crée** pas d'alerte ; il les **affiche** au point du lundi et avant de rebooker.

## Tâches planifiées et charges fixes

- Crons : **05:45 / 06:00 / 06:30** — rafraîchissement trésorerie, alertes, échéances.
- Charges fixes : **4 charges, 360 000 F/mois** (à vérifier dans es_finance — le skill lit la
  table réelle, il ne fige pas la liste).

---

## Budget du projet (« Objectifs et budgets »)

- À la cascade temps 3, le skill écrit le **budget = coût de revient validé** (temps 1 G).
- Si une fiche « Projets à venir » existait pour cette opportunité, elle est **convertie** :
  la prévision « À venir » (opportunité × probabilité) est remplacée par les lignes de
  commande et le budget. **Pas de double comptage** dans la prévision de trésorerie.
- Une opportunité Gagnée convertie en projet **sort** de « À venir ».

## Projets sans commande

Certains projets (internes) n'ont pas de `sale.order` : suivi par `es.finance.pipeline` ou
directement en compta. La marge sur la compta s'applique aussi — voir
`claude_es-finance-marge-projets-sans-commande-17-09-2026.md`.

---

## Trésorerie — comment la lire

- **Optimiste** : opportunités à 100 % + factures émises.
- **Médiane** : opportunités × probabilité (CRM) + factures à échéance.
- **Prudente** : encaissé + factures certaines seulement.

Le skill donne les trois en une ligne, puis la recommandation « Répartition » (dettes d'abord).

## Correspondance CRM ↔ es_finance

| Côté CRM (`crm.lead`) | Côté es_finance |
|---|---|
| Idée / Demande reçue | À venir — idée |
| Cadrage / Proforma envoyée | À venir — chiffré (revenu attendu × probabilité) |
| Négociation | À venir — validé en attente |
| **Gagnée** | **Sort d'À venir → Projets** (sale.order + budget) |
| Perdue / Abandonnée | Sort d'À venir, motif tracé |

Tant que le lien CRM ↔ es_finance n'est pas codé, le skill le signale comme
**développement à faire** et n'écrit que dans `crm.lead`.

---

## Règle anti-doublon et chantier 67 %

- **67 % des dépenses ne sont rattachées à aucun projet** : à chaque saisie de dépense
  que Lycris demande (« j'ai dépensé X pour Y »), le skill **exige ou propose** l'analytique
  projet (`analytic_distribution` = `project_id.account_id`). Ne jamais laisser une dépense
  sans projet sans le signaler.
- Ne jamais créer une fiche `es.finance.pipeline` pour une affaire client tant que le lien
  CRM n'existe pas — sous peine de compter deux fois la même opportunité.

## Commandes liées à es_finance

- « où en est l'argent » → Trésorerie + Répartition + échéances + charges à valider.
- « point du lundi » → inclut Trésorerie, Répartition, alertes, encaissements attendus.
- « bilan de l'affaire » → marge réelle (compta) vs prévisionnel de la phase B, leçon consignée.

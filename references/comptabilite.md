# Comptabilité et fiscalité

Référence pour la comptabilité de production d'Évents & Studios. Le skill s'y conforme pour
les comptes, les journaux et la fiscalité ; il ne traite jamais la TVA déjà facturée (dossier
cabinet Ekanza).

Source : `claude_audit-comptable-complet-10-09-2026.md`,
`claude_notes-de-frais-tva-correction-16-09-2026.md`,
`claude_dette-fiscale-reconstituee-2022-2026.md`,
`claude_acces-odoo-cabinet-comptable-ekanza-16-09-2026.md`, et le skill
`comptabilite-fiscalite-ci`.

---

## Plan comptable de production

| Poste | Compte | Notes |
|---|---|---|
| Chiffre d'affaires (prestations de service) | **706100** | **Tout** le CA — la société ne vend aucune marchandise. Forfait et T&E sur **deux lignes** |
| Prestations de services achetées (prestataires, freelances) | **605700** | Cachets en facture fournisseur avec analytique projet |
| Transport du personnel | **614000** | Personnel |
| Transport entre établissements ou chantiers | **618200** | Interurbain / fret matériel |
| Voyages et déplacements | **618100** | Déplacements |
| Restauration et régie de tournage | **618400** | Restauration, régie |
| Consommables (piles, etc.) | **604100** | Consommables |
| Location d'équipements et d'outils | **622300** | Location |
| Agents temporaires (main-d'œuvre occasionnelle) | **637100** | Main-d'œuvre occasionnelle |
| Commissions et courtage sur les ventes | **632200** | Apporteurs d'affaires |

## Journaux

| Journal | Code | Usage |
|---|---|---|
| Factures clients | **FAC** / **FACTU** | `account.move` `out_invoice` |
| Caisse | **CSH1** | Dépenses de mission au TTC, **sans TVA récupérable** |
| Notes de frais | **EXP** | `hr.expense` — intermédiaires (caisse/avance) |
| Paie | **PAIE** | Bulletins de paie — **ne jamais** aussi saisir en facture |
| Achats fournisseurs | — | `in_invoice` — cachets avec analytique |

**Forfait et T&E** : deux lignes 706100 distinctes sur devis et facture (voir
`references/referentiel.md`). Ne jamais absorber la logistique dans le forfait.

**Dépenses de mission** : saisies en **caisse au TTC, sans TVA récupérable** (pas de TVA
déductible sur ces dépenses). Le skill le rappelle à chaque saisie.

**Cachets** : en **facture fournisseur 605700 avec analytique projet** (ou `hr.expense` avec
`analytic_distribution` selon le montage — voir `references/es_production.md`). Jamais en
double (feuille de temps + facture) — règle anti-double-comptage.

**Salaires** : par **bulletins de paie** (journal PAIE) uniquement. Ne jamais aussi saisir
un salaire en facture fournisseur — sous peine de le compter deux fois.

---

## FNE — Facture Normalisée Électronique

- Une affaire n'est **close** qu'avec **solde encaissé + FNE émise** (`es.deal.is_closed`).
- Depuis le **communiqué DGI du 27/01/2026**, seule la **FNE justifie une charge déductible
  et la TVA déductible** chez le client. Une facture sans FNE expose le client et bloque la
  déductibilité.
- Le skill vérifie à la clôture (et au « point du lundi ») les affaires **payées mais sans
  FNE** (Grand-Bassam en est l'exemple — payée et close depuis août, FNE toujours en attente).
- Avant de facturer, vérifier **RCCM + compte contribuable** du client — c'est ce qui manquait
  sur le Festival des Grillades d'Abidjan (facture restée en brouillon des semaines) et ce qui
  bloque la FNE de Grand-Bassam. Le skill le réclame dès le devis.

## TVA — décision prise le 21/09/2026

> **À partir d'octobre 2026, plus aucune TVA facturée.**

### Règle

- Toute **facture** ou tout **devis** daté du **01/10/2026 ou après** : **aucune taxe** sur
  les lignes. Le champ `tax_ids` est vide, `tva = 0` dans `proforma.json`.
- Les 14 produits ne portent plus la taxe 18 % par défaut.

### Cas limite à signaler systématiquement

Une commande dont l'**acompte a été facturé avant octobre avec TVA** et dont le **solde
tombe après** (octobre ou plus tard) : le skill **montre l'écart** (acompte TTC vs solde
HT, total hybride) et **laisse Lycris arbitrer**. Il ne corrige pas seul (pas d'avoir
automatique, pas de remise, pas de réécriture).

### Réglages à proposer (sans appliquer seul)

- Retrait de la taxe 18 % par défaut sur les **14 produits** (`product.product` → `taxes_id`).
- Retrait sur les **modèles de devis** (`sale.order` template).
- Vérification de la **position fiscale** par défaut des clients (`account.fiscal.position`).
- Le skill propose, Lycris valide — puis le skill écrit via `es_ops_queue` si besoin.

### Dossier TVA déjà facturée (2022 → septembre 2026)

- Le sort de la TVA **déjà facturée** depuis 2022 reste le dossier du **cabinet Ekanza**.
  Le skill **ne le traite pas** ; il le **rappelle seulement** s'il touche une facture en
  cours (ex. avoir à émettre, régularisation demandée par le cabinet).
- Accès Odoo du cabinet : voir `claude_acces-odoo-cabinet-comptable-ekanza-16-09-2026.md`
  (droits compta, journaux FAC/PAIE, pas de suppression).

## Dette fiscale et régime

Voir `claude_dette-fiscale-reconstituee-2022-2026.md` et `claude_audit-comptable-…`.

- Régime : **réel simplifié d'imposition**.
- La dette reconstituée et les échéances sont suivies dans es_finance (onglet Emprunts).
- Le skill ne calcule pas l'impôt ; il **affiche** les échéances et **alerte** (7 jours / retard).

## Ce que le skill fait / ne fait pas

- Fait : propose les comptes/journaux/analytique à chaque écriture, exige l'analytique projet
  (67 % non rattachées), vérifie RCCM/CC avant facturation, signale la FNE manquante, applique
  la règle TVA octobre 2026 et signale le cas à cheval.
- Ne fait pas : ne corrige pas la TVA passée, ne calcule pas l'impôt, ne valide pas une
  facture, n'émet pas la FNE — il prépare en brouillon et rappelle ce qui bloque.

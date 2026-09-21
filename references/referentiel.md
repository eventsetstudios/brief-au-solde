# Référentiel métier — Évents & Studios

Valeurs relevées sur la base de production. Elles servent de **repère** et de **secours quand
Odoo est injoignable**. Dès que la connexion fonctionne, la base fait foi : les prix et les
coûts bougent, ce fichier non.

Date de relevé initiale : 07/09/2026. Mise à jour : 21/09/2026.

---

## Identité légale — à reprendre sur tout document sortant

| | |
|---|---|
| Raison sociale | EVENTS & STUDIOS SARLU |
| Forme | Société à Responsabilité Limitée Unipersonnelle |
| Capital social | 1 000 000 F CFA |
| RCCM | CI-ABJ-2018-B-04133 |
| Compte contribuable | 1807549B |
| N° CNPS employeur | 320502LB |
| Siège | Abidjan Cocody Riviera 5 — 23 BP 1307 Abidjan 23 |
| Téléphone | +225 27 22 27 63 77 / 07 07 47 93 06 |
| Site | www.eventsetstudios.ci |
| E-mail | contact@eventsetstudios.ci |
| Gérant | Joël-Christian Lopy |
| Baseline | Création publicitaire - Production audiovisuelle - Web Agency |

Charte des documents officiels : logo en en-tête avec la baseline, titre encadré et centré,
police Verdana, pied de page portant les mentions légales et le numéro de page.

---

## Catalogue de services

Quatorze produits, tous de type Service. **Depuis le 01/10/2026, plus aucune TVA facturée** :
toute facture ou tout devis daté du 01/10/2026 ou après sort **sans taxe** (voir
`references/comptabilite.md`). Le taux historique de 18 % ne s'applique plus qu'aux pièces
antérieures. Ne pas reconduire la TVA par habitude.

| ID réel | Anc. ID | Produit | Unité | Prix XOF (référence) | Taxe en base au 21/09/2026 |
|---|---|---|---|---|---|
| 106 | 95 | Réalisation film publicitaire | Unité | 750 000 | 18 % (à retirer ligne à ligne) |
| 107 | 96 | Captation / couverture d'événement | Jour | 650 000 (était 600 000) | aucune — déjà TVA 0 |
| 108 | 97 | Publi-reportage | Unité | 250 000 | 18 % (à retirer ligne à ligne) |
| 109 | 98 | Montage / post-production | Unité | 700 000 | 18 % (à retirer ligne à ligne) |
| 110 | 99 | Motion design & animation | Unité | 500 000 | 18 % (à retirer ligne à ligne) |
| 111 | 100 | Reportage photo | Jour | 350 000 | 18 % (à retirer ligne à ligne) |
| 112 | 101 | Captation drone | Jour | 760 000 | 18 % (à retirer ligne à ligne) |
| 113 | 102 | Régie technique événement | Jour | 350 000 | 18 % (à retirer ligne à ligne) |
| 114 | 103 | Sonorisation, éclairage & écran LED | Jour | **à fixer** (1 F) | 18 % (à retirer ligne à ligne) |
| 115 | 104 | Technicien / cadreur additionnel | Jour | **à fixer** (1 F) | 18 % (à retirer ligne à ligne) |
| 116 | 105 | Campagne digitale & community management | Unité | 3 000 000 | 18 % (à retirer ligne à ligne) |
| 117 | 106 | Location caméra, optique & lumière | Jour | 100 000 | 18 % (à retirer ligne à ligne) |
| 118 | 107 | Location studio | Jour | **à fixer** (1 F) | 18 % (à retirer ligne à ligne) |
| 119 | 108 | Frais refacturés (transport, régie, divers) | Unité | **au réel** (1 F) | 18 % (à retirer ligne à ligne) |

⚠ **IDs relevés le 21/09/2026 directement en base** (test Blacknideas, `product.product`
`sale_ok + service`) : le catalogue vit sous les IDs **106 à 119**. Les anciens IDs 95-108
du relevé 07/09/2026 sont obsolètes — les lignes existent toujours mais portent d'autres
produits (ex. 100 = « Appearance + Digital Campaign… », 101 = « Event Registration »,
104 = « Prestation »). Les prix proviennent de la médiane des 600 dernières lignes de
commande confirmées ; seule la captation a bougé (600 000 → 650 000). Ils sont hors TVA
depuis octobre 2026. **La base fait foi** : revérifie les IDs avant chaque chiffrage.

**Les trois prix « à fixer »** (114, 115, 118) sont à 1 XOF en base faute d'historique
exploitable. Si une affaire en a besoin, demande le prix à Lycris — ne prends pas 1 F, et ne
devine pas.

Le 119 se facture sur quantité livrée manuelle : on refacture ce qui a réellement été engagé.
Les autres sont en prépayé / prix fixe.

**Règle de présentation** : forfait et T&E (produit 119 ou 119 ventilé) sur **deux lignes
distinctes** du devis/facture (compte 706100, voir `references/comptabilite.md`). Ne jamais
absorber la logistique dans le forfait.

Tous les produits de production sont en `task_in_project` : **une commande confirmée donne un
projet et une tâche par ligne**. Ne crée pas le projet à la main.

**Taxe** : seul le 107 est déjà sans taxe ; les 13 autres portent encore la taxe 18 %
(id 14) par défaut. Le devis vide donc `tax_ids` ligne à ligne (`scripts/commande.py` le
fait, et le test Blacknideas PR2609-0147 l'a vérifié : 3 lignes `tax_id []`). Chantier de
retrait définitif à proposer (sans appliquer seul) : taxe par défaut des 14 produits, modèles
de devis, position fiscale par défaut des clients.

---

## Coûts par journée

Base : une journée de tournage = 8 heures, quelle que soit la durée réelle. Le coût d'un
salarié mensuel se déduit de `salaire mensuel ÷ 21,67 jours ouvrés`.

| Personne | Statut | Coût / journée | Canal de coût (`es_cost_channel`) |
|---|---|---|---|
| Modeste Ahibo | Cadreur, prestataire | 25 000 | `timesheet` (feuille de temps) |
| Jordan Fabrice Anoh | Cadreur, prestataire | 20 000 | `timesheet` |
| Jaures Bogui | Photographe-vidéaste, prestataire | 20 000 (forfait 100 000 vu sur Grand-Bassam) | `timesheet` ou forfait |
| Ayéhou Joël | Vidéaste | 20 000 | `timesheet` |
| Frédéric N'guessan | Directeur technique, salarié | 6 920 (150 000 / mois) | `timesheet` |
| Joël-Christian Lopy | Gérant | 16 154 (350 000 / mois) | `timesheet` |
| Doulaye | Pilote de drone, externe | 45 000 + 5 000 de transport **ou** 50 000 tout compris | `vendor_bill` (facture fournisseur) |
| Ariel Topka | Stagiaire vidéaste | 0 (prime de transport en frais généraux) | — |

Deux conventions coexistent pour Doulaye : **45 000 + 5 000 de transport** (bon de commande
CF2609-0005, Festival d'Abidjan) et **50 000 par journée tout compris** (Grand-Bassam). Le
résultat est le même sur une journée ; sur deux, la première donne 95 000 et la seconde
100 000. Demande laquelle s'applique plutôt que de choisir.

Jaures Bogui a été payé **au forfait (100 000 F)** sur Grand-Bassam plutôt qu'à la journée.
Un photographe-vidéaste qui livre un lot d'images se forfaitise souvent : vérifie le mode
avant de multiplier par le nombre de jours.

Le tarif contractuel des prestataires est de **25 000 F CFA la journée**, forfaitaire, journée
entamée due en totalité, décompte arrêté en fin de mois civil, paiement au plus tard le 15 du
mois suivant sur facture. Les valeurs ci-dessus sont celles effectivement portées en base ;
quand elles divergent du contrat-cadre, la base fait foi pour le calcul et l'écart mérite
d'être signalé à Lycris.

> Relevé base du 21/09/2026 (`hr.employee`, test Blacknideas) : `hourly_cost` = **0** pour
> Modeste Ahibo, Jordan Anoh, Bogui Jaures, Ayéhou Joël, Ariel Topka et Kimberly Kayinda —
> **montage B** (`vendor_bill`), pas des données manquantes. Seuls Frédéric N'guessan
> (6 920) et Joël-Christian Lopy (16 154) portent un coût `timesheet`. Les 20 000-25 000 F
> ci-dessus restent les tarifs contractuels à retenir pour le coût de revient via facture
> fournisseur ; la fiche employé fait foi personne par personne.

### Canaux de coût

```text
es_cost_channel = vendor_bill  → facture fournisseur analytique (604100, 605700, 618…)
es_cost_channel = timesheet    → feuille de temps (account.analytic.line)
```

Voir `references/es_production.md` pour le détail et `references/comptabilite.md` pour les
comptes. La règle d'or reste : une seule voie porte le coût pour une personne sur un projet.

### Défaut connu : day_rate ×8

Le `day_rate` par défaut des affectations (`es.crew.assignment`) est multiplié par 8 (8 h)
côté module tant que le paramétrage `hours_per_day` n'est pas corrigé. Le skill **force
systématiquement** `day_rate_is_override = True` et le `day_rate` réel à chaque création.
Voir `references/es_production.md`.

### La règle du double comptage

> **Pour une personne donnée sur un projet donné, une seule des deux voies porte le coût,
> jamais les deux.**

| Montage | Coût jour sur la fiche | Facture fournisseur | Où l'a-t-on vu |
|---|---|---|---|
| **A — par les feuilles de temps** | renseigné | saisie **sans** analytique projet | note du 05/09, prestataires cadreurs |
| **B — par la facture fournisseur** | mis à **0** | saisie **avec** analytique projet | DABOSA, les quatre freelances |

**Un coût jour à 0 sur une fiche n'est donc pas une donnée manquante** : c'est le plus
souvent le montage B. Vérifie personne par personne avant de chiffrer une marge — se tromper
de montage la fausse du simple au double. Voir aussi `references/es_production.md`.

### Lecture es.crew.ledger

Ce qu'on doit à chaque intervenant — à contrôler avant de rebooker (décompte arrêté fin de
mois, paiement dû au 15). Le skill le lit et le résume ; il n'en crée pas de doublon.

---

## Ce que le studio possède

Utile pour savoir ce qui se loue et ce qui ne se loue pas. Vérifier la disponibilité au
moment de proposer le dispositif (voir `references/es_production.md`).

- Mélangeur **ATEM Mini Extreme ISO** (génération 1, 2021) — régie multicaméra
- Caméras **Sony FX3**, **FX30**, **a7 III**, **a7 IV**
- Matériel DJI : drone, stabilisateur, Osmo Pocket
- Parc `es.equipment` en base (caméras, optiques, lumière, son, drone, régie) — voir
  `es_production`.

Une prestation qui dépasse ces moyens (écran LED, sonorisation de salle, plus de quatre
caméras, éclairage lourd) implique une location ou un prestataire à chiffrer en plus.

---

## Affaires de référence 2026

Trois affaires complètes, chiffrées et closes. Elles servent de mètre étalon pour les marges
et pour la structure d'un chiffrage. Les montants vendus sont ceux des documents ; les charges
de Grand-Bassam sont calculées ligne à ligne et non relevées sur le compte analytique.

### Festival des Grillades d'Abidjan — EXP-MOMENTUM

Projet 290, analytique 299. Couverture d'un événement sur **2 jours**.

| | |
|---|---|
| Vendu | 800 000 F (forfait unique, sans TVA) |
| Charges | 262 840 F |
| **Marge** | **537 160 F — 67,1 %** |

Composition des charges : Modeste 2 j × 25 000 · Ayéhou Joël 2 j × 20 000 · Frédéric 2 j ×
6 920 · Doulaye drone 2 j × 45 000 + 5 000 de transport · transport de Joël 10 000 · transport
matériel 7 000 · transport équipe 20 000 · restauration 2 j × 10 000 · consommables 7 000.

Structure à retenir pour un événement de deux jours à Abidjan : **trois personnes sur place plus
un drone, environ 60 000 F de régie** (transport, restauration, consommables).

### DABOSA — EXP-MOMENTUM

Projet 447, analytique 456. Tournée de captation photo/vidéo en **8 étapes**, du 4 juillet au
26 août 2026, dans quatre villes (Dabou, Bouaké, Abengourou, San Pédro).

| | |
|---|---|
| Vendu | 4 000 000 F (forfait captation) + 1 440 000 F (déplacement, hébergement, régie) = **5 440 000 F** |
| Charges | 1 636 178 F |
| **Marge** | **3 803 822 F — 69,9 %** |

Enseignements transposables :

- Sur une prestation hors Abidjan, **les frais de déplacement et de régie se vendent en ligne
  séparée** (ici 1 440 000 F, soit 36 % du forfait de captation) plutôt que d'être absorbés.
- Régie par étape, de 75 000 à 195 000 F selon la ville — Bouaké et Abengourou coûtent plus
  cher que Dabou.
- Des **prestataires locaux** ont été recrutés dans chaque ville (photographe, pilote de drone,
  cadreur), avec l'étiquette Odoo « Prestataires locaux », ville et métier renseignés. C'est
  moins cher que de déplacer toute l'équipe d'Abidjan, et c'est reproductible.

### Festival des Grillades de Grand-Bassam — EXP-MOMENTUM

Projet 448, analytique 457. **8 et 9 août 2026**, à Grand-Bassam. Payé en espèces le 10 août,
projet livré et clos.

| | |
|---|---|
| Vendu | 400 000 F/jour captation + 200 000 F/jour régie × 2 jours = **1 200 000 F** |
| Charges hors rémunération du gérant | **600 000 F** → marge **50,0 %** |
| Charges gérant compris (2 j × 16 154) | **632 308 F** → marge **47,3 %** |

Composition : Jordan 2 j × 20 000 · Modeste 2 j × 25 000 · Ayéhou Joël 2 j × 20 000 ·
Doulaye 2 j × 50 000 · Jaures Bogui forfait 100 000 · Joël-Christian 2 j × 16 154 ·
nourriture 2 j × 15 000 · transport 2 j × 20 000 · **commission d'apport d'affaires
200 000 F** (Rufin Akadje). Les 227 500 F d'intervenants DABOSA payés en espèces hors
affectations sont l'exemple à ne pas reproduire.

**C'est l'affaire la plus instructive** : sans la commission d'apport, elle serait à
**64 %** ; avec, elle tombe à **47-50 %**. Un seul poste, absent des deux autres affaires,
avale un tiers de la marge. Toujours demander l'apporteur avant le chiffrage.

### Marge de référence

| Affaire | Vendu | Charges | Marge |
|---|---|---|---|
| Grand-Bassam (août) | 1 200 000 | 600 000 à 632 308 | **47 à 50 %** — 64 % sans commission |
| Festival d'Abidjan (septembre) | 800 000 | 262 840 | **67,1 %** |
| DABOSA (juillet-août) | 5 440 000 | 1 636 178 | **69,9 %** |

Le niveau à viser est **65 % et plus**. En dessous de **60 %**, signale-le et propose ce qui
la rétablirait. La marge ne vit plus que dans es_finance (direction seule) ; un chargé de
production ne la voit pas — voir `references/es_finance.md`.

---

## Conditions de paiement — rappel

| ID | Libellé | Acompte | Quand l'utiliser |
|---|---|---|---|
| 27 | 70 % d'acompte, solde à 30 jours | 70 % | nouveau client, sans historique |
| 36 | 50 % d'acompte, solde à 30 jours | 50 % | client connu, paiements tenus |
| 34 | Paiement à la commande | 100 % | montant faible ou client à risque |
| 4 / 29 / 37 / 35 | 30 j / réception / 45 j / livraison | — | signaler : studio avance toute la trésorerie |

L'historique de paiement du client (écart `invoice_date` → paiement) décide. Voir
`references/devis.md` et `references/odoo.md`.

---

## Le processus lui-même

Les quatorze étapes, leurs acteurs et leurs conditions de passage sont documentés dans le
projet Claude « Odoo », fichier `claude/processus-conduite-affaire-14-etapes.md`, et présentés
sous forme d'animation ici :
https://claude.ai/code/artifact/f8899fa8-df88-4a1c-8a3f-33bd37906d24

Voir aussi `references/workflow-commande.md` pour le mode commande en 3 temps.

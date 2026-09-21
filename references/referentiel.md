# Référentiel métier — Évents & Studios

Valeurs relevées sur la base de production. Elles servent de **repère** et de **secours quand
Odoo est injoignable**. Dès que la connexion fonctionne, la base fait foi : les prix et les
coûts bougent, ce fichier non.

Date de relevé : 07/09/2026.

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

Quatorze produits, tous de type Service, TVA 18 %. Les prix ont été établis à partir de la
médiane des 600 dernières lignes de commande confirmées.

| ID | Produit | Unité | Prix XOF | Catégorie |
|---|---|---|---|---|
| 95 | Réalisation film publicitaire | Unité | 750 000 | Production audiovisuelle |
| 96 | Captation / couverture d'événement | Jour | 600 000 | Production audiovisuelle |
| 97 | Publi-reportage | Unité | 250 000 | Production audiovisuelle |
| 98 | Montage / post-production | Unité | 700 000 | Production audiovisuelle |
| 99 | Motion design & animation | Unité | 500 000 | Production audiovisuelle |
| 100 | Reportage photo | Jour | 350 000 | Production audiovisuelle |
| 101 | Captation drone | Jour | 760 000 | Production audiovisuelle |
| 102 | Régie technique événement | Jour | 350 000 | Événementiel |
| 103 | Sonorisation, éclairage & écran LED | Jour | **à fixer** | Événementiel |
| 104 | Technicien / cadreur additionnel | Jour | **à fixer** | Événementiel |
| 105 | Campagne digitale & community management | Unité | 3 000 000 | Digital & contenus |
| 106 | Location caméra, optique & lumière | Jour | 100 000 | Location matériel & studio |
| 107 | Location studio | Jour | **à fixer** | Location matériel & studio |
| 108 | Frais refacturés (transport, régie, divers) | Unité | **au réel** | Frais refacturés |

**Les quatre prix « à fixer »** (103, 104, 107, 108) sont à 1 XOF en base faute d'historique
exploitable. Si une affaire en a besoin, demande le prix à Lycris — ne prends pas 1 F, et ne
devine pas.

Le 108 se facture sur quantité livrée manuelle : on refacture ce qui a réellement été engagé.
Les autres sont en prépayé / prix fixe.

Tous les produits de production sont en `task_in_project` : **une commande confirmée donne un
projet et une tâche par ligne**. Ne crée pas le projet à la main.

---

## Coûts par journée

Base : une journée de tournage = 8 heures, quelle que soit la durée réelle. Le coût d'un
salarié mensuel se déduit de `salaire mensuel ÷ 21,67 jours ouvrés`.

| Personne | Statut | Coût / journée | Enregistrement du coût |
|---|---|---|---|
| Modeste Ahibo | Cadreur, prestataire | 25 000 | feuille de temps |
| Jordan Fabrice Anoh | Cadreur, prestataire | 20 000 | feuille de temps |
| Jaures Bogui | Photographe-vidéaste, prestataire | 20 000 | feuille de temps |
| Ayéhou Joël | Vidéaste | 20 000 | feuille de temps |
| Frédéric N'guessan | Directeur technique, salarié | 6 920 (150 000 / mois) | feuille de temps |
| Joël-Christian Lopy | Gérant | 16 154 (350 000 / mois) | feuille de temps |
| Doulaye | Pilote de drone, externe | 45 000 + 5 000 de transport | facture fournisseur |
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

### La règle du double comptage

La rentabilité d'un projet additionne le coût des feuilles de temps **et** celui des factures
fournisseurs imputées en analytique. D'où la règle, qui n'a qu'une formulation :

> **Pour une personne donnée sur un projet donné, une seule des deux voies porte le coût,
> jamais les deux.**

Les deux montages existent en base et sont l'un comme l'autre valables :

| Montage | Coût jour sur la fiche | Facture fournisseur | Où l'a-t-on vu |
|---|---|---|---|
| **A — par les feuilles de temps** | renseigné | saisie **sans** analytique projet | note du 05/09, prestataires cadreurs |
| **B — par la facture fournisseur** | mis à **0** | saisie **avec** analytique projet | DABOSA, les quatre freelances |

Ce ne sont pas deux règles qui se contredisent : ce sont deux façons de faire porter le coût,
et la fiche employé dit laquelle s'applique. **Un coût jour à 0 sur une fiche n'est donc pas
une donnée manquante** : c'est le plus souvent le montage B. Vérifie personne par personne
avant de chiffrer une marge — se tromper de montage la fausse du simple au double, dans un
sens comme dans l'autre.

---

## Ce que le studio possède

Utile pour savoir ce qui se loue et ce qui ne se loue pas.

- Mélangeur **ATEM Mini Extreme ISO** (génération 1, 2021) — régie multicaméra
- Caméras **Sony FX3**, **FX30**, **a7 III**, **a7 IV**
- Matériel DJI : drone, stabilisateur, Osmo Pocket

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

Projet 448, analytique 457. **8 et 9 août 2026**, à Grand-Bassam. À ne pas confondre avec
l'édition d'Abidjan des 5 et 6 septembre. Payé en espèces le 10 août, projet livré et clos.

| | |
|---|---|
| Vendu | 400 000 F/jour captation + 200 000 F/jour régie × 2 jours = **1 200 000 F** |
| Charges hors rémunération du gérant | **600 000 F** → marge **50,0 %** |
| Charges gérant compris (2 j × 16 154) | **632 308 F** → marge **47,3 %** |

Composition : Jordan 2 j × 20 000 · Modeste 2 j × 25 000 · Ayéhou Joël 2 j × 20 000 ·
Doulaye 2 j × 50 000 · Jaures Bogui forfait 100 000 · Joël-Christian 2 j × 16 154 ·
nourriture 2 j × 15 000 · transport 2 j × 20 000 · **commission d'apport d'affaires
200 000 F** (Rufin Akadje).

Ces charges sont **calculées ligne à ligne**, pas relevées sur le compte analytique 457 : les
deux valeurs diffèrent selon que la rémunération du gérant est imputée au projet ou non, et ce
n'est pas la même convention partout. Quand Odoo est joignable, lis le compte analytique plutôt
que de reprendre ce chiffre.

**C'est l'affaire la plus instructive des trois**, parce que c'est la seule qui sort du rang :
sans la commission d'apport, elle serait à **64 %** ; avec, elle tombe à **47-50 %**. Un seul
poste, absent des deux autres affaires, avale un tiers de la marge.

Deux autres enseignements : la prestation a été vendue en **deux lignes distinctes**
(captation et régie) plutôt qu'en forfait unique — c'est la structure la plus lisible pour le
client comme pour l'analyse ; et la **facture normalisée électronique (FNE) reste à émettre**,
alors que l'affaire est payée et close.

### Marge de référence

| Affaire | Vendu | Charges | Marge |
|---|---|---|---|
| Grand-Bassam (août) | 1 200 000 | 600 000 à 632 308 | **47 à 50 %** — 64 % sans la commission d'apport |
| Festival d'Abidjan (septembre) | 800 000 | 262 840 | **67,1 %** |
| DABOSA (juillet-août) | 5 440 000 | 1 636 178 | **69,9 %** |

Le niveau à viser est **65 % et plus**. En dessous de **60 %**, signale-le et propose ce qui
la rétablirait.

**Et pose systématiquement la question de l'apporteur d'affaires.** C'est le seul poste qui,
à lui seul, fait passer une affaire de 64 % à 47 %. Une commission qui apparaît après le
chiffrage transforme une bonne affaire en affaire moyenne, et personne ne s'en aperçoit avant
la clôture.

---

## Le processus lui-même

Les quatorze étapes, leurs acteurs et leurs conditions de passage sont documentés dans le
projet Claude « Odoo », fichier `claude/processus-conduite-affaire-14-etapes.md`, et présentés
sous forme d'animation ici :
https://claude.ai/code/artifact/f8899fa8-df88-4a1c-8a3f-33bd37906d24

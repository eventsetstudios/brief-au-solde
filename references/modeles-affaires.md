# Modèles par type d'affaire

Valeurs par défaut tirées des affaires réelles (Festival des Grillades Abidjan, Grand-Bassam,
DABOSA, MAGGI). Le skill les utilise comme **hypothèses pré-remplies à confirmer**, jamais
comme vérités. Chaque modèle donne : dispositif, équipe type, tâches et lignes catalogue.

Les prix catalogue sont hors TVA depuis le 01/10/2026. Les coûts jour sont dans
`references/referentiel.md`.

---

## 1. Captation 1 jour — Abidjan

Scénario le plus simple. 1 session, 0 mission.

- **Dispositif** : 1 à 2 caméras (FX30/FX3) + régie ATEM + son HF si prises de parole.
- **Équipe type** : 1 cadreur (Modeste 25 000) + 1 cadreur/assistant (Jordan 20 000) +
  1 pilote drone externe si demandé (Doulaye 50 000, `vendor_bill`). Option régie.
- **Tâches** : Pré-prod (repérage, convocation) → Production (J captation) → Post-prod
  (montage 2-3 j) → Validation client → Livré + 4 satellites (J−2, J, J+1, J+2).
- **Lignes** :
  - 96 Captation / couverture d'événement × 1 j (600 000)
  - 101 Captation drone × 1 j si drone (760 000)
  - 108 Frais refacturés : régie ~30 000 (transport 10 000 + restauration 10 000 + consommables)
- **T&E** : sur une seule ligne 108 « au réel » — pas de mission.
- **Marge attendue** : ~65-70 % sans apporteur (Abidjan, régie légère).

---

## 2. Festival 2 jours — Abidjan

Référence : Festival des Grillades d'Abidjan (projet 290) — 800 000 vendu, 262 840 de charges,
67,1 % de marge.

- **Dispositif** : 2 à 3 caméras + drone + régie ATEM. Son si scène.
- **Équipe type** : 3 personnes sur place + 1 drone externe.
  - Modeste 2 j × 25 000 + Ayéhou Joël 2 j × 20 000 + Frédéric 2 j × 6 920
  - Doulaye 2 j × 50 000 (ou 45 000+5 000) en facture fournisseur
- **Régie** : ~60 000 pour 2 jours (transport équipe 20 000 + matériel 7 000 + restauration
  20 000 + consommables 7 000 + transport Joël 10 000).
- **Lignes** (exemple Grand-Bassam) en **deux lignes distinctes** :
  - 96 Captation × 2 j (400 000/j = 800 000) — ou forfait unique selon client
  - 108 Frais régie × 2 j (200 000/j = 400 000) — ou 60 000 forfait si Abidjan
  - 101 Drone × 2 j si vendu à part (760 000/j)
- **Tâches** : identiques + planning 2 sessions (ou 1 session de 2 jours selon découpage).
- **Vigile** : apporteur ? Grand-Bassam est passé de 64 % à 47 % pour 200 000 F de commission.

---

## 3. Festival 2 jours — hors Abidjan (Grand-Bassam)

Référence : Grand-Bassam (projet 448) — 1 200 000 vendu (800 000 captation + 400 000 régie),
600 000 à 632 308 de charges, 47-50 % (64 % sans commission).

- **Dispositif** : idem Abidjan + logistique déplacement.
- **Équipe type** : 3 cadreurs + 1 photo/vidéo + 1 drone + gérant (4-5 pers. × 2 j).
- **Missions** : **1 mission** (départ veille, tournage, retour) — 1 chargé de mission.
- **T&E** : 40 000 à 60 000/j hors Abidjan proche (transport 20 000/j + nourriture 15 000/j +
  hébergement si nuitée + commission apporteur éventuelle).
- **Lignes** :
  - Forfait captation (96/98) + ligne régie/T&E séparée (108) — ne pas absorber.
- **Leçon** : Grand-Bassam payé en espèces le 10/08, FNE toujours en attente → vérifier FNE à la
  clôture.

---

## 4. Tournée multi-villes (DABOSA)

Référence : DABOSA (projet 447) — 5 440 000 (4 000 000 forfait + 1 440 000 T&E), 1 636 178 de
charges, 69,9 %. 8 étapes, 4 villes (Dabou, Bouaké, Abengourou, San Pédro), 4/07 → 26/08/2026.

- **Dispositif** : par étape 1-2 caméras + photo + drone selon ville. Prestataires **locaux**
  recrutés sur place (photographe, pilote drone, cadreur — étiquette « Prestataires locaux »,
  ville + métier renseignés) — moins cher que déplacer toute l'équipe d'Abidjan.
- **Équipe type** : noyau Abidjan (1-2) + locaux par ville.
- **Missions** : **1 mission par lieu hors Abidjan** (DABOSA = 8 missions = 8 chargés de
  mission, même personne possible). Départ veille, tournage, retour.
- **T&E par étape** : 75 000 (Dabou) à 195 000 (Bouaké/Abengourou) — 1 440 000 au total
  (36 % du forfait captation). À chiffrer au réel d'une étape comparable, pas au per diem.
- **Lignes** :
  - Forfait captation (96/98/100/101 selon prestation) — ex. 500 000/étape
  - Frais refacturés / T&E — 1 ligne **séparée** (108, 180 000/étape en moyenne)
- **Tâches** : 1 projet + 8 sessions + 4 × 8 tâches satellites. Modèle de production
  « Tournée » à appliquer (Pré-prod → Prod ×8 → Post-prod → Validation → Livré).
- **Sessions** : `es.shooting` par étape (date_start/stop, lieu, manager, équipe, matériel).
- **Leçon** : 227 500 F payés en espèces hors affectations → à éviter (toujours affectation +
  `hr.expense` avec analytique).

---

## 5. Spot / film publicitaire

Référence : à constituer (MAGGI — commande test, projet fantôme à vérifier).

- **Dispositif** : 2-3 caméras, lumière, son, régie. Location (106/103) si besoin.
- **Équipe type** : réal, cadreurs, ingé son, chef élec, régisseur selon ampleur.
- **Tâches** : Pré-prod (scénario, repérage) → Production (1-2 j tournage) → Post-prod
  (montage, étalonnage, mixage — souvent sous-estimé : 3-5 j) → Validation client (2 tours)
  → Livré.
- **Lignes** :
  - 95 Réalisation film publicitaire (750 000)
  - 98 Montage / post-production (700 000)
  - 99 Motion design si habillage (500 000)
  - 106/103 Location si besoin
  - 108 Frais refacturés (transport, régie)
- **Vigile** : tours de correction inclus à fixer au devis (référence pour avenant).

---

## Comment le skill applique un modèle

1. Lit la demande et cherche l'affaire comparable la plus proche (DABOSA pour tournée,
   Grillades pour festival).
2. Propose le modèle comme **hypothèse** : « Sur DABOSA j'avais X, même dispositif ici ? »
3. Adapte : nombre de jours, lieux, T&E par étape, équipe (locaux vs déplacement).
4. Chiffre en deux lignes (forfait + T&E) + coût de revient + marge.
5. Si le client ou le lieu change, ajuste la régie par étape (ville chère vs proche).

Aucun modèle n'est figé : le skill le **corrige avec le réel** à chaque bilan d'affaire
(« bilan de l'affaire » → leçon consignée).

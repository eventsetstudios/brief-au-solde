# Chiffrer une proforma par analogie

Le principe : **le prix se déduit de ce qui a déjà été vendu et de ce que ça a réellement
coûté**, pas du seul prix catalogue. Le catalogue donne un point de départ ; l'historique dit
si ce point de départ tient face à la réalité du terrain.

---

## 1. Trouver les affaires comparables

```bash
python3 scripts/analogues.py --client 832 --produits 107,112 --jours 2
```

Trois axes de rapprochement, du plus fort au plus faible :

1. **Même client** — c'est le plus fort. Un client a un niveau de prix accepté et une manière de
   payer ; s'en écarter sans raison se remarque.
2. **Mêmes produits du catalogue** — deux captations d'événement se ressemblent plus que deux
   affaires du même client dans des métiers différents.
3. **Même profil de mission** — durée, nombre de jours, hors Abidjan ou non, taille de l'équipe.

Pour chaque affaire retenue, sors : le montant vendu, les lignes, les jours réellement passés,
qui était sur le plateau, les charges par nature et la marge constatée. Deux à quatre affaires
suffisent ; au-delà, on dilue.

**S'il n'y a aucune analogie** — nouveau client, prestation inédite — dis-le. Chiffre alors à
partir du catalogue et du coût de revient, et annonce que le prix est une hypothèse à arbitrer,
pas une déduction.

---

## 2. Composer les lignes

Reste dans le catalogue. Une ligne hors catalogue casse le suivi analytique, la refacturation
et la comparaison avec les affaires suivantes.

Deux réflexes qui viennent des affaires passées :

- **Hors Abidjan, une ligne de frais séparée.** Sur DABOSA, déplacement, hébergement et régie
  ont été vendus 1 440 000 F à part du forfait de captation — 36 % de celui-ci. Absorber ces
  frais dans le forfait, c'est offrir la logistique.
- **Le cadreur ou technicien additionnel est une ligne**, pas une gentillesse. Produit 104.

---

## 3. Chiffrer le coût de revient avant d'arrêter le prix

C'est l'étape que l'on saute et qui coûte cher. Additionne :

| Poste | Comment le calculer |
|---|---|
| Équipe interne et prestataires | somme des (jours × coût jour) — voir `referentiel.md` |
| Prestataires externes facturés | drone, son, prestataires locaux : leur tarif, en facture fournisseur |
| Régie | transport équipe + transport matériel + restauration + consommables |
| Déplacement hors Abidjan | transport interurbain, hébergement, régie locale, par étape |
| Location | ce que le studio ne possède pas : écran LED, sono, éclairage lourd, caméras au-delà de quatre |
| Post-production | jours de montage, étalonnage, mixage — souvent sous-estimés |
| **Commission d'apport d'affaires** | s'il y a un apporteur : le poste le plus lourd et le plus oublié |

Repère utile issu du Festival des Grillades d'Abidjan : pour deux jours sur place avec trois
personnes plus un drone, la régie seule pèse environ **60 000 F**.

### La commission d'apport, à demander systématiquement

Sur Grand-Bassam, une commission de 200 000 F versée à un apporteur a fait passer l'affaire de
**64 % à 47 %** de marge. Aucun autre poste n'a cet effet. Elle n'apparaît nulle part dans le
brief du client et se découvre en général après le chiffrage, quand il est trop tard pour
l'intégrer au prix.

Donc : **demande s'il y a un apporteur avant d'arrêter le prix**, et quand il y en a un, monte
le prix du montant de la commission plutôt que de l'absorber sur la marge.

---

## 4. Vérifier la marge

```
marge = (vendu − coût de revient) / vendu
```

| Marge | Ce que tu fais |
|---|---|
| ≥ 65 % | conforme aux affaires de référence, rien à signaler |
| 60 – 65 % | acceptable, mentionne-le en une ligne |
| < 60 % | **dis-le clairement** et propose ce qui la rétablirait |

Donne toujours la marge **avec et sans la commission d'apport** quand il y en a une. C'est
l'écart entre les deux qui dit s'il faut renégocier la commission ou monter le prix.

Ce qui rétablit une marge, dans l'ordre où c'est acceptable pour le client : réduire les jours
sur place, alléger l'équipe, recruter en local plutôt que de déplacer (DABOSA), sortir une
prestation du forfait pour la vendre en ligne séparée (Grand-Bassam vend la captation et la
régie séparément), puis seulement augmenter le prix.

Ne masque jamais une marge faible dans un total. Lycris préfère un chiffrage qui dit « on est à
52 %, voilà pourquoi » à un chiffrage rassurant qui se révèle faux à la clôture.

---

## 5. Proposer la condition de paiement

Elle se choisit à l'émission de la proforma, pas plus tard : c'est elle qui décidera du moment
où le projet peut s'ouvrir et de celui où l'affaire se solde.

| Situation du client | Condition proposée |
|---|---|
| Nouveau client, aucun historique | 70 % d'acompte, solde à 30 jours (id 27) |
| Client connu, paiements tenus | 50 / 50 (id 36) |
| Montant faible, relation établie | Paiement à réception (id 29) |
| Client lent à payer par le passé | 70 / 30, et le dire à Lycris |
| Administration ou grand groupe imposant ses délais | 30 ou 45 jours (id 4 ou 37), en signalant que le studio avance toute la trésorerie |

Vérifie l'historique de paiement avant de proposer : `account.move` du client, écart entre
`invoice_date` et `invoice_date_due` d'un côté, date de paiement de l'autre.

Sur une condition **sans acompte**, rappelle en une phrase que les dates seront bloquées et les
prestataires confirmés sans avance — le risque est entièrement sur le studio.

---

## 6. Le tableau d'arbitrage

Présenté dans la conversation, avant toute mise en forme. Il tient en un écran :

```
CAPTATION FESTIVAL X — EXP-MOMENTUM — 2 jours, Abidjan

Ligne                                    Qté   PU        Total
Captation / couverture d'événement (107)   2   650 000  1 300 000
Captation drone (112)                      2   760 000  1 520 000
Frais refacturés (119)                     1    60 000     60 000
                                                       ─────────
                                          Total vendu  2 880 000

Coût de revient prévisionnel                              352 840
  équipe 3 pers. × 2 j                        103 840
  drone externe 2 j                            95 000
  régie (transport, repas, consommables)       60 000
  post-production 3 j                          94 000

Marge                              2 527 160 F — 87,8 %
Condition proposée      70 % d'acompte, solde à 30 jours (client connu, paie à 20 j)

Appui : Festival des Grillades (800 000 F, 2 j, marge 67,1 %) — même client, même format,
        mais forfait unique. Ici le drone est vendu en ligne propre.
```

Chaque chiffre doit pouvoir être remonté à sa source. Une ligne qui dit sur quelles affaires
passées le chiffrage s'appuie n'est pas décorative : c'est ce qui permet à Lycris de dire
« non, cette fois c'est différent parce que… », et c'est cette phrase-là qui fait le bon prix.

---

## 7. La mise au propre

Une fois les lignes arbitrées :

```bash
python3 scripts/proforma.py --data proforma.json --out ./
```

Produit le XLSX et le PDF à la charte, avec le bloc d'identification légale de
`referentiel.md`. Le fichier `proforma.json` attendu :

```json
{
  "numero": "PRO-2026-014",
  "date": "2026-09-08",
  "client": {"nom": "EXP-MOMENTUM COTE D'IVOIRE", "adresse": "Abidjan", "rccm": "", "contribuable": ""},
  "objet": "Captation Festival X — 2 jours",
  "lignes": [
    {"designation": "Captation / couverture d'événement", "unite": "Jour", "qte": 2, "pu": 600000},
    {"designation": "Captation drone", "unite": "Jour", "qte": 2, "pu": 760000},
    {"designation": "Frais refacturés (transport, régie, divers)", "unite": "Unité", "qte": 1, "pu": 60000}
  ],
  "tva": 18,
  "condition_paiement": "70 % d'acompte à la commande, solde à 30 jours",
  "validite_jours": 30,
  "notes": "Prix hors hébergement. Deux tours de correction inclus."
}
```

### TVA — règle d'octobre 2026

Depuis le **01/10/2026, plus aucune TVA facturée** : toute facture ou tout devis daté du
01/10/2026 ou après sort avec `"tva": 0` (tax_ids vide). Le taux historique de 18 % ne
s'applique plus qu'aux pièces antérieures. **Ne pas reconduire la TVA par habitude** —
vérifie la date. Le skill signale systématiquement le cas limite « acompte avant octobre
avec TVA / solde après sans » et laisse Lycris arbitrer (voir `references/comptabilite.md`).

```json
"tva": 0,
```

Le devis n'est créé dans Odoo (`sale.order` en brouillon) que si Lycris le demande, et il n'est
jamais confirmé ni envoyé par le skill. Si la commande passe par le mode « j'ai une commande »,
le devis est créé depuis l'opportunité CRM (voir `references/workflow-commande.md`).

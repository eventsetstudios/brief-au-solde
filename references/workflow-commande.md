# Workflow « j'ai une commande » — déroulé en 3 temps

Mode pour solopreneur : Lycris dit une phrase (« j'ai une commande », « X m'a commandé… »,
« on a un nouveau job »), le skill fait le reste en ne posant que ce que lui ne peut pas
savoir. Ce document détaille les trois temps annoncés dans `SKILL.md`.

---

## Temps 1 — Préparer la commande par questions

### 1. Lire d'abord Odoo

Avant toute question :

- **Fiche client** : `res.partner` — RCCM, compte contribuable, factures ouvertes
  (`account.move` `amount_residual > 0`), délai de paiement constaté
  (`invoice_date` → date de paiement), condition de paiement par défaut, apporteur connu ?
- **Référence dossier NAS** : lire les notes fiche client (`res.partner.comment`,
  ligne `NAS: …` ou `Dossier NAS: …`). Si elle existe, s'en servir pour créer le reste
  de l'arborescence (`/WORKS/<réf>/<année>/<Projet>/`) au temps 3. Si elle n'existe
  pas, la demander à Lycris en série 1 (proposer le nom sanitisé du client).
- **Affaires comparables** : `scripts/analogues.py --type <type> --client <id>` — même client,
  mêmes produits, même volume de jours. Sortir vendu, jours, équipe, marge.
- **Disponibilités** : `scripts/equipe.py --du <date> --au <date> --roles …` — congés validés,
  affectations qui chevauchent, indisponibilités déclarées. Ne pas révéler la marge à l'équipe.

Si Odoo est injoignable, l'annoncer et chiffrer sur le référentiel en précisant que les
prix et dispos sont figés au relevé.

### 2. Poser les questions par séries de 4 à 6, en réponses cliquables

Dans un environnement qui expose `AskUserQuestion` / `ask_user_input`, s'en servir — les
réponses cliquables coûtent moins que du texte à rédiger.

**Règle d'or** : une question ne se pose que si sa réponse change le prix, l'équipe, les
dates ou le périmètre. Écarter toute question dont la réponse est déjà dans Odoo ou ne
change rien. Pas de question sur la TVA : la règle est fixée (aucune TVA ≥ 01/10/2026).

Formulation : **hypothèse pré-remplie à confirmer**, pas page blanche.

> ✗ « Quel dispositif veux-tu ? »
> ✓ « Sur le Festival des Grillades j'avais 2 cadreurs + drone sur 2 jours. Même dispositif
>   ici, ou tu ajoutes le son parce qu'il y a des prises de parole ? »

### 3. Séries à couvrir, dans cet ordre

#### A — Client et commercial

- Qui commande (société, contact, qui valide côté client, circuit et délai de validation).
- Y a-t-il un **apporteur d'affaires** et sa commission ? (Grand-Bassam : 200 000 F → 64 % → 47 %).
- Fiche client complète ou pièces à réclamer (RCCM, compte contribuable — bloque facture et FNE).
- Historique de paiement → condition de paiement recommandée (70/30 si nouveau ou lent, 50/50 si
  connu et ponctuel, sans acompte = risque studio).

#### B — Le travail

- Intention réelle (objet de diffusion attendu).
- Type d'affaire : captation événement, spot, campagne multi-étapes, régie, reportage photo…
- Livrables précis : nature, quantité, formats, délais. « 350 photos + highlight 2 min » oui,
  « des photos » non.
- Droits de diffusion (où, combien de temps, exclusivité) — une cession large se facture.
- Tours de correction inclus — à fixer maintenant (référence pour distinguer correction due /
  avenant à l'étape 12).
- Hors périmètre — à écrire noir sur blanc.

#### C — Le calendrier et les lieux

- Jours de tournage avec **jour de la semaine** (« vendredi 12/12/2026 » pas seulement « 12/12 »).
- Lieux. Pour chaque lieu **hors Abidjan** : une **mission** (départ la veille, tournage, retour).
- Nombre d'étapes si tournée (ex. DABOSA : 8 étapes, 4 villes).
- Contraintes de lieu : électricité, autorisations, accès, lumière, sécurité.
- Contraintes de date : week-end vs semaine à confirmer avant de bloquer l'équipe.

#### D — Les responsables — question obligatoire, jamais sautée

- **Chargé de projet** : toujours un, pour chaque commande. Proposer un titulaire (qui a déjà
  tenu ce rôle sur une affaire comparable et qui est disponible) + une alternative, à confirmer
  d'un clic.
- **Chargé de mission** : un par mission dès qu'il y a au moins un déplacement hors Abidjan.
  Une tournée de 4 villes = 4 chargés de mission à désigner (éventuellement la même personne).
- La fiche commande n'est pas validable tant qu'un de ces noms manque.
- Source : `project.project.user_id` pour le chargé de projet ; `es.mission` (ou `es.shooting`)
  pour le chargé de mission — **lire `fields_get` avant d'écrire**, jamais supposer le nom du
  champ. Si la personne n'a pas de compte `res.users`, le signaler et proposer soit d'ouvrir un
  accès selon la matrice des droits, soit de désigner un utilisateur existant. Ne crée aucun
  compte seul. Rappel : le chargé de projet ne voit pas la marge.

#### E — Le dispositif, l'équipe et le matériel

Deux volets, dans cet ordre. D'abord qui, avec quel rôle ; ensuite avec quoi.

**E1 — Les membres de l'équipe et le rôle de chacun.**
- Par rôle (`es.crew.role` : Réalisateur, Directeur photo, Cadreur, Assistant caméra,
  Télépilote drone, Photographe, Ingénieur du son, Chef électricien, Chargé de
  production, Assistant de production, Chauffeur, Monteur) : **un membre nommé +
  son rôle + un remplaçant**, avec coût jour et canal de coût (`timesheet` vs
  `vendor_bill`). Exemple : cadreur prestataire 25 000 F en feuille de temps,
  pilote drone Doulaye 45 000+5 000 en facture fournisseur.
- Source : `scripts/equipe.py --du … --au …` (disponibilité — congés `validate`,
  affectations, indisponibilités — + expérience + tenue des délais + coût jour).
  Classement : disponibilité → expérience du même type → tenue des délais → coût jour.
- Chaque membre proposé est nommé avec son rôle (« Modeste Ahibo — Cadreur »),
  jamais un rôle sans nom ni un nom sans rôle.

**E2 — Le matériel à utiliser, listé via es_production.**
- Lister d'abord via `scripts/equipe.py --du … --au … --materiel [--categorie …]` :
  kits prédéfinis par usage (tournage Sony A7 III, Blackmagic 6K Pro, son reportage,
  podcast, lumière studio/photo, lumière LED, régie multicam, mouvement, stabilisation,
  fond studio, drone), puis exemplaires avec état, disponibles et conflits de
  réservation sur la période.
- Proposer par hypothèse : kits correspondant au type d'affaire + exemplaires clés
  (boîtier, optique, son, lumière, drone, régie), en signalant les conflits
  (`es.equipment.booking` en `draft`/`confirmed`/`out` qui chevauchent) et le hors
  service (`broken`, ex. HF Sennheiser, stabilisateurs Feiyu) **sans bloquer**.
- Ce qui n'est pas au parc (ou est indisponible) → location / prestataire, chiffré
  en plus (produits 117/114/115, T&E ou facture fournisseur).
- Rappel coût : le `day_rate` du parc est **indicatif** — il n'entre jamais dans le
  coût réel (amortissement) ; seule une facture de sous-location compte.

#### F — La logistique T&E par mission

- Transport, hébergement, restauration, fret matériel, location — chiffrée **au réel** d'une
  étape comparable (DABOSA : 75 000 à 195 000 F par étape selon la ville). **Pas de per diem.**
- Forfait et T&E sur **deux lignes distinctes** (706100) sur devis et facture.

#### G — L'argent

- Prix proposé, coût de revient prévisionnel, marge (avec et sans commission d'apporteur),
  condition de paiement recommandée et échéances.
- Seuil : viser **65 %**, alerter < **60 %** et proposer : moins de jours, équipe plus légère,
  recrutement local, prestation sortie du forfait, ou prix plus haut.
- Mentionner sur quelles affaires passées le chiffrage s'appuie.

### 4. Produire la fiche commande

Une page, en français, que Lycris relit en une minute :

- **Cadrage** : intention, dates/lieux (avec jours de semaine), livrables, dispositif, équipe
  (membre + rôle de chacun, remplaçants), matériel validé (kits + exemplaires + porteur),
  dossier NAS (`/WORKS/<réf>/…`), hors périmètre, tours de correction, droits, risques.
- **Tableau d'arbitrage** : lignes catalogue (Qté, PU, Total), forfait et T&E séparés, total
  vendu, coût de revient détaillé (équipe, prestataires externes, régie, location, commission),
  marge en F et en %, condition de paiement, hypothèses.
- **Liste de tout ce qui sera créé au temps 3** (objets, montants, dates, personnes).
- Proforma XLSX/PDF à la charte si demandée (`scripts/proforma.py` sans TVA si ≥ 01/10/2026).

---

## Temps 2 — Validation unique

Lycris arbitre et valide **une seule fois l'ensemble**. Le skill récapitule en une liste
ce qu'il va écrire (objets, montants, dates, personnes, responsables, TVA retirée le cas
échéant) et attend un « oui » explicite.

Toute modification relance le récapitulatif, pas tout le questionnaire.

La validation couvre `action_confirm` et `action_post` **uniquement si Lycris les y a
explicitement incluses** ; sinon elles restent en brouillon et le skill le dit.

---

## Temps 3 — La cascade, déclenchée par la validation

Dans cet ordre, chaque écriture annoncée ensuite avec son identifiant :

1. **Opportunité CRM** passée à « Gagnée » (ou créée si elle n'existe pas) — voir
   `references/crm.md`. Seule saisie client ; es_finance lira l'opportunité.
2. **Devis** (`sale.order`) depuis l'opportunité, lignes du catalogue, condition de paiement,
   **sans TVA si date ≥ 01/10/2026**. Vérifier le retrait de la taxe 18 % par défaut.
3. **Confirmation** de la commande → projet et tâches créés par Odoo (`sale_project`).
   Vérifier aussitôt : `account_id` du projet, `project_id` de **chaque** `sale.order.line`
   (piège du projet fantôme « … - MODÈLE — … » vu sur MAGGI), aucun projet recréé à la main.
4. **Facture** : facture d'acompte selon la condition (70/30, 50/50, comptant) en
   **brouillon** ; aucune facture d'acompte si la condition n'en prévoit pas. Rappeler que les
   acomptes déjà encaissés restent en paiements non affectés puis se lettrent sur la facture.
   Cas limite TVA : montrer l'écart si acompte avec TVA / solde sans, laisser arbitrer.
5. **Affaire `es.deal`** et journal d'étapes à jour ; bouton « Ouvrir le projet » seulement
   quand le déclencheur de l'étape 05 est atteint (encaissement si avec acompte, accord écrit
   seul si sans — mais signaler le risque).
6. **Budget du projet** dans es_finance (« Objectifs et budgets ») = coût de revient validé ;
   fiche « Projets à venir » convertie si elle existait (pas de double comptage dans la
   prévision de trésorerie) — voir `references/es_finance.md`.
7. **Production** : sessions (`es.shooting`), missions (`es.mission`) et leur logistique
   prévisionnelle, affectations (`es.crew.assignment`, `quantity = 1` par jour de cachet,
   `day_rate` forcé avec `day_rate_is_override` tant que le défaut ×8 n'est pas corrigé),
   **réservations du matériel validé** (`es.equipment.booking` en `draft` : 1 par ligne
   d'exemplaire + 1 par ligne de chaque kit validé, fenêtre = dates validées,
   `holder_id` = chargé de mission par défaut, `conflict_warning` vérifié après création),
   les tâches par étape (Pré-production → Production → Post-production → Validation client →
   Livré) et les **4 tâches satellites** par session (J−2 préparation/convocation, J captation,
   J+1 dérushage/sauvegarde, J+2 intégration) — voir `references/es_production.md`.
8. **Responsables inscrits dans Odoo** : le chargé de projet sur `project.project.user_id`
   et sur `es.deal` si champ existe ; le chargé de mission sur chaque `es.mission`. Lire
   `fields_get` avant écriture. Gérer le cas prestataire sans compte `res.users`.
9. **Arborescence NAS** (`/WORKS/`, racine par défaut — env `NAS_ROOT` pour surcharger) :
   créer `/WORKS/<réf client>/<année>/<Projet>/01_creation … 05_rendus` via
   `scaffold.init_projet` (jours de tournage → dossiers `Jxx_DATE_*`), puis consigner
   `Dossier NAS: <réf>` dans les notes fiche client si la réf venait de la fiche.
   Création de dossiers seulement — aucun fichier déplacé ni supprimé.
10. **Feuilles de service** lisibles sur téléphone, et **activités de rappel** datées
    (`mail.activity`) : relance acompte, confirmation prestataires, J−2, livraison, solde, FNE.

Ordre de création : `crm.lead` → `sale.order` → `project.project`/`project.task` →
`account.move` (brouillon) → `es.shooting`/`es.mission` → `es.crew.assignment` →
`es.equipment.booking` (brouillon, selon le validé) → dossier NAS `/WORKS` → activités.

Toutes les écritures sont groupées : une seule validation pour tout le lot, jamais une
validation par objet. Pour ce qui ne peut pas être exécuté (suppressions), passer par
`es_ops_queue`.

---

## Questionnaire complet du §1 tel qu'il sera posé

Le skill ne pose que ce qui manque après lecture Odoo, par séries de 4-6 hypothèses. À titre
illustratif, voici la couverture complète quand tout est à demander (les libellés réels
s'adaptent aux affaires comparables trouvées) :

**Série 1 — Client et commercial**
- « Le client est [X — 3 commandes, dernière à 1,2 M, payée à J+12]. Je pars sur le même
  contact [Y] qui a validé la dernière fois, ou c'est un autre valideur ? » (choix cliquables)
- « Fiche client incomplète : il manque RCCM et CC. Tu les as, ou je note à réclamer avant facture ? »
- « Dossier NAS : [lu dans les notes : EXP-MOMENTUM → /WORKS/EXP-MOMENTUM/…] — je m'en sers, ou [pas de réf en notes] quel nom de dossier je crée ? » (proposer le nom sanitisé ; une fois validé, la réf est consignée dans les notes client)
- « Apporteur d'affaires sur cette commande ? [Non / Oui : ___ — commission ___ F] »
- « Condition de paiement : [70 % à la commande / 50 % / sans acompte] — je propose [70/30]
  vu [historique]. Tu confirmes ? »

**Série 2 — Le travail**
- « Intention : [le client veut X pour diffusion Y]. C'est bien ça, ou c'est plutôt Z ? »
- « Type : [captation événement 2 jours / tournée 4 étapes / spot] — je classe en [captation] ? »
- « Livrables : [2× captation + 300 photos + highlight 2 min, J+7] — correct ou tu ajoutes/retires ? »
- « Diffusion : [réseaux 12 mois, non exclusif] — même droits que DABOSA, ou cession large à chiffrer ? »
- « Tours de correction inclus : [2] comme d'habitude, ou [1/3] ? »
- « Hors périmètre : [hébergement, habillage graphique] — tu y laisses ça dehors ? »

**Série 3 — Calendrier et lieux**
- « Dates : [ven. 14/11 et sam. 15/11 à Grand-Bassam] — c'est un week-end, tu confirmes ? »
- « Lieux : [Grand-Bassam, salle X]. Hors Abidjan → 1 mission (départ jeu. 13/11, retour dim. 16/11).
  Tournée 4 villes = 4 missions. Tu valides le découpage ? »
- « Contraintes lieu : [élec. groupe, accès camion] — quelque chose à signaler ? »

**Série 4 — Responsables (obligatoire)**
- « Chargé de projet : je propose [Frédéric — a tenu ce rôle sur 2 festivals, dispo] / alt.
  [Joël-Christian]. Tu choisis ? »
- « Chargé de mission Grand-Bassam : [Modeste — dispo] / alt. [Jordan — en congé J-1]. Tu confirmes ? »
- (Répété par mission s'il y a tournée.)

**Série 5 — Dispositif, équipe et matériel**
- « Dispositif : [2 caméras + drone + son HF] comme Festival Abidjan + son. Tu valides ? »
- « Cadreur 1 : [Modeste Ahibo — Cadreur, 25 000 F/j, timesheet, déjà sur Abidjan] / remplaçant [Jordan Anoh — Cadreur, 20 000] »
- « Photo : [Bogui Jaures — Photographe, forfait 100 000] / remplaçant [Ayéhou Joël — Vidéaste] »
- « Drone : [Doulaye — Télépilote drone, 50 000/j, vendor_bill, dispo] / alt. [externe X] »
- « Matériel (listé via es_production) : kits [tournage Sony A7 III + drone Mavic 3 + son reportage]. Exemplaires : [Sony FX30 dispo + Mavic 3 Classic dispo + HF Sennheiser **hors service** → location HF à chiffrer]. Tu valides, tu retires, tu ajoutes ? »
- « Porteur du matériel : [Modeste — chargé de mission] par défaut. OK ? »

**Série 6 — Logistique T&E par mission**
- « Grand-Bassam T&E : transport 40 000 + hébergement 60 000 + restauration 30 000 + fret 10 000
  = 140 000 (réel étape Abengourou). Tu ajustes ? »
- « Pas de per diem — on reste au réel, tu confirmes ? »

**Série 7 — L'argent**
- Tableau d'arbitrage complet avec marge et condition, à valider d'un oui.

Chaque série n'est posée que si la lecture Odoo ne l'a pas déjà remplie. Une tournée
multi-villes répète les séries C-F par mission, en une seule passe.

---

## Cas particuliers

- **Client sans RCCM/CC** : ne bloque pas le devis, mais note « à réclamer » et le rappelle
  à la facturation (sinon facture en brouillon et FNE bloquée).
- **Condition sans acompte** : ne pas bloquer l'ouverture en attendant un encaissement ;
  signaler le risque trésorerie et proposer de durcir à 70/30 si possible.
- **TVA à cheval sur octobre 2026** : montrer l'écart acompte/solde, laisser arbitrer.
- **Chargé de mission sans compte Odoo** : signaler, proposer ouverture d'accès ou utilisateur
  existant, ne pas créer de compte seul.

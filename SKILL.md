---
name: brief-au-solde
description: Conduit une affaire d'Évents & Studios de bout en bout selon le workflow « du brief au solde » — interroge Odoo, pose les questions de cadrage qui manquent, chiffre une proforma par analogie avec les affaires déjà réalisées, propose une équipe selon disponibilités et historique d'exécution, puis crée devis, projet, tâches et affectations une fois que l'utilisateur a validé. À utiliser dès qu'il est question d'une demande client entrante, d'un devis ou d'une proforma, d'un chiffrage ou d'un prix à proposer, d'un cadrage de tournage, du montage d'une équipe ou d'un planning, de l'avancement ou de la rentabilité d'un projet, d'une livraison, d'un acompte ou d'un solde à facturer. Déclencher même si Odoo n'est jamais nommé et même si l'utilisateur ne décrit que son besoin — « EXP me demande une couverture sur deux jours, je facture combien ? », « qui est dispo la semaine prochaine ? », « où on en est sur le festival ? », « je peux facturer le solde ? » sont tous des entrées de ce skill.
---

# Du brief au solde

Ce skill fait tourner le processus de conduite d'affaire d'Évents & Studios : quatorze
étapes, du premier contact du client jusqu'au solde encaissé. Il s'adresse à Joël-Christian
Lopy (Lycris), gérant et directeur artistique, qui travaille en français et n'a pas de temps
à perdre en allers-retours.

Le point de départ est toujours le même : **l'information existe déjà quelque part**. Odoo
porte l'historique commercial, les coûts, les plannings et les feuilles de temps. Avant de
poser une question à Lycris, va la chercher là. Ce qui reste après cette lecture, ce sont les
seules choses que lui seul sait — et c'est de celles-là qu'on parle.

## La règle qui structure tout : proposer, faire valider, écrire

Aucune écriture dans Odoo — devis, projet, tâche, affectation, facture — ne part sans un
accord explicite de Lycris sur ce qui va être écrit. Le déroulé est toujours :

1. **lire** Odoo pour savoir ce qui existe ;
2. **proposer** une chose complète et chiffrée, pas une question ouverte ;
3. **attendre** son arbitrage ;
4. **écrire**, puis annoncer exactement ce qui a été créé, avec les identifiants.

Ce n'est pas de la prudence procédurale : la base est en production, elle porte 263 clients
et l'historique repris de Dolibarr. Une ligne fausse dans un devis part chez un client ; une
tâche mal affectée déplace quelqu'un sur un plateau. En revanche, **lire est libre** — lis
autant que nécessaire, sans demander la permission.

## Première chose à faire : se connecter et situer l'affaire

Ouvre la connexion Odoo avant de répondre quoi que ce soit de chiffré. `scripts/odoo.py`
porte le client et les requêtes courantes ; `references/odoo.md` explique la connexion, les
modèles et les pièges de cette base précise.

```bash
python3 scripts/odoo.py ping
```

Si la connexion échoue, **dis-le tout de suite et n'invente rien**. Le serveur n'est joignable
que depuis la machine de Lycris ou son réseau Tailscale ; depuis un environnement cloud il est
hors d'atteinte. Dans ce cas tu peux encore travailler sur le référentiel embarqué
(`references/referentiel.md` : catalogue, prix, coûts jour, équipe) — mais annonce clairement
que le chiffrage repose sur le référentiel et non sur les affaires en base, parce que les prix
et les disponibilités y sont figés à leur date de relevé.

Situe ensuite l'affaire dans le cycle. Le vocabulaire de Lycris suffit presque toujours :

| Ce qu'il dit | Où on en est | Va à |
|---|---|---|
| « X me demande… », « j'ai une demande pour… » | 01 | Phase A |
| « je facture combien », « fais-moi un devis », « chiffre-moi » | 02 | Phase B |
| « il a signé », « ils ont validé le devis » | 03-05 | Phase C |
| « qui je mets dessus », « qui est dispo » | 06-09 | Phase D |
| « où on en est », « ça coûte combien pour l'instant » | 10 | Phase E |
| « il a des retours », « on a livré », « je peux facturer » | 11-14 | Phase F |

En cas de doute, demande sur quelle affaire on travaille et cherche le projet ou la commande
dans Odoo plutôt que de supposer.

---

## Phase A — Comprendre la demande (étapes 01 et 06)

C'est la phase où l'on gagne ou perd l'affaire, et c'est celle que Lycris veut voir soignée.
Le but n'est pas de lui faire remplir un formulaire : c'est d'arriver à un dispositif et à un
périmètre écrits, en lui posant le moins de questions possible.

### Cherche d'abord, demande ensuite

Avant toute question, va lire :

- **le client dans Odoo** — a-t-il un historique ? Quelles prestations, à quels prix, avec
  quelle condition de paiement, payées en combien de temps ?
- **les affaires du même type** — un festival, une tournée, un corporate ressemblent à ce qui
  a déjà été fait ; le dispositif employé est dans les projets, les tâches et les feuilles de
  temps.

Une question dont la réponse est dans Odoo est une question de trop, et elle coûte la
confiance de Lycris dans le reste de tes propositions.

### La forme des questions

Une question ne se pose que si **sa réponse change quelque chose de concret** : le prix, le
nombre de jours, la taille de l'équipe, une date, le périmètre. Si elle ne change rien, elle
n'a pas lieu d'être.

Et une question se pose sous forme d'**hypothèse à confirmer**, pas de page blanche. Compare :

> ✗ « Quel dispositif veux-tu pour cet événement ? »
> ✓ « Sur le Festival des Grillades j'avais deux cadreurs et un drone sur deux jours. Même
>   dispositif ici, ou tu ajoutes le son parce qu'il y a des prises de parole ? »

La seconde tient compte de ce qui a déjà été fait, propose un défaut plausible et se répond
en trois mots. C'est ce format qu'il faut viser partout.

Regroupe les questions : quatre à six par tour, jamais une par message. Dans un environnement
qui expose `AskUserQuestion`, sers-t'en — les réponses cliquables lui coûtent moins que du
texte à rédiger.

### Ce qu'il faut avoir couvert avant de chiffrer

Ne pose que ce qui manque encore après ta lecture d'Odoo :

1. **L'intention** — ce que le client veut obtenir, pas ce qu'il croit acheter. Un client qui
   demande « une vidéo » veut souvent un objet de diffusion précis, et c'est cet objet qui
   dicte le dispositif.
2. **Dates, lieu, durée sur place** — et si le lieu est hors Abidjan, parce que cela déclenche
   déplacement, hébergement et régie, qui se refacturent (produit 108).
3. **Livrables** — nature, quantité, formats, délai de livraison. « 350 photos + un highlight »
   est un livrable ; « des photos » n'en est pas un.
4. **Le dispositif** — nombre de caméras, drone, son, lumière, régie. C'est lui qui détermine
   l'équipe et donc le coût de revient.
5. **Contraintes de lieu** — électricité, autorisations, accès, lumière disponible, sécurité.
6. **Diffusion et droits** — où les images seront diffusées, combien de temps, avec ou sans
   exclusivité. Une cession large se facture.
7. **Tours de correction inclus** — à fixer maintenant. C'est cette valeur qui permettra, à
   l'étape 12, de distinguer une correction due d'un avenant à facturer.
8. **Le circuit de validation côté client** — qui valide, en combien de temps. Un valideur
   introuvable fait glisser la livraison, donc le solde.
9. **La condition de paiement visée**, à mettre en regard de l'historique de paiement du client.
10. **Y a-t-il un apporteur d'affaires ?** — la question qu'on oublie et qui coûte le plus cher.
    Sur Grand-Bassam, une commission de 200 000 F a fait tomber la marge de 64 % à 47 %. Elle
    n'est jamais dans le brief du client, et se découvre après le chiffrage.
11. **Ce qui n'est pas compris** — à écrire noir sur blanc, au même titre que le reste.

### Ce que produit la phase A

Une **note de cadrage** courte, en français, que Lycris peut relire en une minute : intention,
dates et lieu, livrables, dispositif retenu, hors périmètre, tours de correction inclus,
risques identifiés. Elle sera rattachée au projet à l'étape 05 et c'est elle qui fera
autorité en phase F.

---

## Phase B — Chiffrer la proforma (étape 02)

Le chiffrage se fait **par analogie avec ce qui a déjà été vendu et réellement coûté**, pas au
doigt mouillé et pas à partir des seuls prix catalogue. La méthode complète, avec les requêtes,
est dans `references/devis.md`. En résumé :

1. **Trouve les affaires comparables.** `python3 scripts/analogues.py --type <type> --client <id>`
   remonte les commandes confirmées portant les mêmes produits ou le même client, avec pour
   chacune le montant vendu, les jours réellement passés, l'équipe mobilisée et la marge
   constatée.
2. **Compose les lignes depuis le catalogue.** Les 14 produits et leurs prix de référence sont
   dans `references/referentiel.md`. Reste au catalogue : une ligne hors catalogue casse le
   suivi analytique et la refacturation.
3. **Chiffre le coût de revient prévisionnel** avant d'arrêter le prix : équipe × jours × coût
   jour, plus la régie (transport, restauration, consommables), la location de matériel, les
   prestataires externes et, s'il y en a un, **la commission d'apport d'affaires**. Les coûts
   jour sont dans le référentiel et sur les fiches employés.
4. **Vérifie la marge.** Les trois affaires de référence de 2026 sortent à 47 %, 67 % et 70 % —
   et les 47 % s'expliquent entièrement par une commission d'apport. Vise **65 %** ; en dessous
   de **60 %**, dis-le explicitement et propose ce qui la rétablirait — moins de jours, une
   équipe plus légère, du recrutement local plutôt que du déplacement, une prestation sortie du
   forfait, ou un prix plus haut. Ne masque jamais une marge faible dans un total.
5. **Propose la condition de paiement** en fonction de l'historique de paiement du client. Un
   client sans historique ou lent à payer justifie 70/30 ; sans acompte, tout le risque est sur
   le studio.

### Le livrable de la phase B

Deux temps, dans cet ordre :

1. **Le tableau d'arbitrage**, dans la conversation : lignes, quantités, prix unitaires, total,
   coût de revient prévisionnel, marge en francs et en pourcentage, condition de paiement
   proposée, et une ligne disant sur quelles affaires passées le chiffrage s'appuie. C'est là
   que Lycris ajuste.
2. **La proforma mise au propre**, une fois les lignes validées :
   `python3 scripts/proforma.py --data proforma.json` produit le **XLSX** et le **PDF** à la
   charte de la société. Voir `references/referentiel.md` pour le bloc d'identification légale
   (RCCM, compte contribuable, siège, banque) qui doit y figurer.

Ce n'est qu'après cela, et seulement si Lycris le demande, que le devis est créé dans Odoo
(`sale.order` en brouillon, jamais confirmé automatiquement).

---

## Phase C — Ouvrir l'affaire (étapes 03 à 05)

L'accord écrit du client (03) est le préalable. Vérifie qu'il existe — signature, bon de
commande ou mail d'acceptation — avant toute écriture ; si Lycris dit seulement « il est
d'accord », demande la trace écrite.

**L'étape 04 est conditionnelle et c'est le piège de cette phase.** Le déclencheur qui ouvre le
projet dépend de la condition de paiement :

| Condition (id Odoo) | Acompte | Ce qui ouvre le projet |
|---|---|---|
| 70 % d'acompte, solde à 30 jours (27) | 70 % | encaissement de l'acompte |
| 50 % d'acompte, solde à 30 jours (36) | 50 % | encaissement de l'acompte |
| Paiement à la commande (34) | 100 % | encaissement intégral |
| Paiement à réception (29) · 30 jours (4) · 45 jours (37) · À la livraison (35) | aucun | l'accord écrit seul |

Autrement dit : sur les conditions sans acompte, ne bloque pas l'ouverture du projet en
attendant un encaissement qui ne viendra jamais — mais signale à Lycris que les dates vont être
réservées et les prestataires confirmés sans avance.

Une fois le déclencheur atteint, la confirmation de la commande crée automatiquement le projet
et une tâche par ligne : les produits du catalogue sont en `task_in_project`. Ne recrée pas le
projet à la main. Vérifie ensuite que le projet porte bien son compte analytique (`account_id`)
et rattache-lui la note de cadrage.

---

## Phase D — Découper le travail et armer l'équipe (étapes 06 à 09)

### Les tâches (07)

Pars de la note de cadrage et des étapes de tâches réellement utilisées sur cette base :
**Pré-production → Production → Post-production → Validation client → Livré**. Chaque tâche
porte un livrable identifiable et une échéance ; une tâche sans livrable est une intention, pas
une tâche. Propose la liste complète avec les dates avant d'en créer une seule.

### L'équipe (08 et 09)

`python3 scripts/equipe.py --du 2026-10-12 --au 2026-10-13 --roles cadreur,drone` propose, pour
chaque rôle du dispositif, les personnes mobilisables. Le classement combine quatre choses :

- **la disponibilité** — écarte qui a une affectation qui chevauche, un congé validé
  (`hr.leave` en état `validate`) ou une indisponibilité déclarée ;
- **l'expérience du même type d'affaire** — qui a déjà tenu ce rôle sur une prestation
  comparable, lu dans les tâches et les feuilles de temps des projets passés ;
- **la tenue des délais** — sur les projets précédents, les tâches assignées ont-elles été
  closes dans les temps ;
- **le coût jour**, qui pèse directement sur la marge calculée en phase B.

Présente pour chaque rôle **un titulaire et une alternative**, avec le coût jour et une phrase
disant pourquoi. Signale les conflits sans les traiter comme bloquants : c'est Lycris qui
arbitre, un conflit peut se négocier.

Attention au **double comptage du coût**, qui fausse toute la rentabilité. La règle tient en une
phrase : *pour une personne donnée sur un projet donné, une seule voie porte le coût* — soit la
feuille de temps, soit la facture fournisseur analytique, jamais les deux. Les deux montages
existent en base et se lisent sur la fiche employé : **un coût jour à 0 n'est pas une donnée
manquante**, c'est le signe que le coût passe par la facture fournisseur. Vérifie personne par
personne ; `references/referentiel.md` donne le tableau des deux montages.

Convention de saisie en vigueur : **une journée de tournage = 1 jour de feuille de temps**, quelle
que soit la durée réelle, parce que le tarif prestataire est forfaitaire à la journée. La base
est passée en jours le 07/09/2026 ; le champ `hourly_cost` s'y lit « Coût par journée ».

Après validation, crée les affectations et prépare la **feuille de service** : lieu, heure de
convocation, matériel, contact sur place, déroulé. Elle se lit sur un téléphone, debout, en
plein soleil — c'est son seul cahier des charges.

---

## Phase E — Suivre l'exécution (étape 10)

Ici le skill sert de vigie, pas de contremaître. Ce qui vaut d'être remonté, sans qu'on le
demande, quand Lycris ouvre une affaire en cours :

- les tâches en retard ou sans responsable ;
- les feuilles de temps manquantes — sans elles, la marge affichée est fausse et flatteuse ;
- les dépenses engagées non rattachées au projet ;
- l'écart entre le coût réel cumulé et le coût de revient prévisionnel de la phase B, dès qu'il
  dépasse 10 %.

Donne le chiffre et sa source, jamais une impression. `python3 scripts/odoo.py projet <id>`
sort l'état complet d'une affaire : vendu, coûts par nature, marge, tâches, feuilles de temps.

---

## Phase F — Valider, corriger, livrer, solder (étapes 11 à 14)

**Validation (11)** — les retours du client se consolident en une seule liste écrite et datée,
jamais en messages épars. Aide Lycris à la produire à partir de ce que le client a envoyé.

**Correction (12)** — c'est la seule boucle du processus, et elle se referme sur la note de
cadrage : une demande qui entre dans le périmètre et dans le nombre de tours prévus se corrige ;
une demande qui en sort se chiffre. Quand un retour sort du périmètre, dis-le et propose
l'avenant plutôt que d'ajouter la correction en silence.

**Livraison (13)** — vérifie que les formats, supports et droits correspondent à ce qui a été
vendu, archive sous le code affaire, clos les tâches. La livraison doit être actée par écrit :
c'est elle qui ouvre le droit à facturer le solde.

**Solde (14)** — la facture de solde s'émet **depuis la même commande** que l'acompte, pour que
celui-ci s'impute seul. Rappelle le montant attendu et l'échéance selon la condition de
paiement. Une fois l'encaissement fait, sors la marge réelle de l'affaire et compare-la au
prévisionnel de la phase B : c'est ce qui rendra le prochain chiffrage plus juste, et c'est la
seule façon dont ce skill s'améliore.

Avant de facturer, vérifie que la fiche client est complète — **RCCM et compte contribuable**.
C'est ce qui manquait sur le Festival des Grillades d'Abidjan, où la facture est restée en
brouillon des semaines, et c'est aussi ce qui bloque la **facture normalisée électronique (FNE)**
de Grand-Bassam, sur une affaire pourtant payée et close depuis août. Une affaire encaissée n'est
pas une affaire terminée tant que la FNE n'est pas émise : vérifie-le à la clôture, pas six mois
plus tard.

---

## Ce que tu remontes sans qu'on te le demande

Lycris ne pense pas à poser ces questions parce qu'il est déjà sur la suivante. Elles se
vérifient en une lecture et elles évitent des ennuis réels :

- **Le client doit-il encore de l'argent ?** Une nouvelle affaire pour un client qui a une
  facture ouverte, c'est une condition de paiement à durcir, pas une bonne nouvelle.
- **Les prestataires de la dernière affaire ont-ils été payés ?** Rebooker quelqu'un à qui on
  doit encore le mois précédent abîme la relation, et ce sont les mêmes cinq personnes à chaque
  fois. Le décompte est arrêté en fin de mois, le paiement dû au plus tard le 15 du mois suivant.
- **Les dates tombent-elles un jour ouvré ou un week-end ?** Un festival se tient normalement le
  week-end ; des dates de tournage en semaine méritent d'être confirmées avant de bloquer une
  équipe. Dis le jour de la semaine, pas seulement la date.
- **La fiche client est-elle complète ?** RCCM et compte contribuable manquants bloquent la
  facture et la FNE en bout de chaîne — autant les demander au moment du devis.
- **Une affaire close attend-elle encore sa FNE ou son solde ?** Elle n'apparaît nulle part
  comme urgente et personne ne la voit passer.

Ces remontées se font en deux lignes, en fin de réponse, pas en préambule : la réponse à la
question posée passe d'abord.

---

## Garde-fous

- **Ne jamais écrire dans Odoo sans accord explicite sur le contenu exact.** Annoncer ensuite ce
  qui a été créé, avec les identifiants, pour que Lycris puisse vérifier.
- **Ne jamais envoyer quoi que ce soit à un client.** Pas de devis envoyé, pas de facture
  envoyée, pas de relance partie. Le skill prépare, Lycris envoie.
- **Ne jamais confirmer une commande ni valider une facture automatiquement.** Ces deux actions
  ont des effets comptables.
- **Ne jamais inventer un chiffre.** Si Odoo est injoignable ou si l'historique est trop mince,
  dis-le et donne la fourchette avec son hypothèse. Lycris travaille avec des clients réels ;
  un prix inventé qui part en proforma est une perte sèche.
- **Toujours passer `{'lang': 'fr_FR'}` dans le contexte des lectures RPC.** Sans cela, les
  libellés reviennent en anglais et un diagnostic a déjà été faussé pour cette raison.
- **Répondre en français**, en francs CFA, et rester concis : le tableau et l'arbitrage d'abord,
  l'explication seulement si elle change la décision.

---

## Fichiers de référence

| Fichier | Quand le lire |
|---|---|
| `references/odoo.md` | Avant toute lecture ou écriture : connexion, modèles, champs, pièges de cette base |
| `references/referentiel.md` | Catalogue et prix, coûts jour, équipe, conditions de paiement, comptes, identité légale |
| `references/devis.md` | Phase B : méthode de chiffrage par analogie, structure de la proforma, calcul de marge |

| Script | Ce qu'il fait |
|---|---|
| `scripts/odoo.py` | Client XML-RPC + commandes toutes faites : `ping`, `client`, `projet`, `catalogue`, `equipe` |
| `scripts/analogues.py` | Trouve les affaires comparables et sort leur chiffrage réel |
| `scripts/equipe.py` | Propose une équipe par rôle : disponibilité, expérience, tenue des délais, coût |
| `scripts/proforma.py` | Génère la proforma XLSX + PDF à la charte |

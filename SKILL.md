---
name: brief-au-solde
description: Conduit une affaire d'Évents & Studios de bout en bout selon le workflow « du brief au solde » — interroge Odoo, pose les questions de cadrage qui manquent, chiffre une proforma par analogie avec les affaires déjà réalisées, construit des propositions guidées à partir des factures ≤ 13 mois (`proposal.py`), propose une équipe selon disponibilités et historique d'exécution, puis crée devis, projet, tâches et affectations une fois que l'utilisateur a validé. Gère aussi les commandes (« j'ai une commande »), les opportunités CRM, les sessions/missions, la logistique T&E, la trésorerie, le point du lundi, la clôture de mission et le solde/FNE. À utiliser dès qu'il est question d'une demande client entrante, d'une commande, d'un devis ou d'une proforma, d'un chiffrage, d'une proposition guidée ou d'une suggestion de prix, d'un cadrage de tournage, d'une opportunité CRM, d'une mission ou session, d'une dépense, de trésorerie, de l'avancement ou de la rentabilité d'un projet, d'une livraison, d'un acompte ou d'un solde à facturer. Déclencher même si Odoo n'est jamais nommé — « j'ai une commande pour X à Bouaké », « nouvelle demande de Y », « propose un prix pour un spot 60s », « point du lundi », « clôture la mission », « j'ai dépensé 50 000 pour le transport », « où en est l'argent », « je peux facturer ? », « bilan de l'affaire » sont tous des entrées de ce skill.
---

# Du brief au solde

Ce skill fait tourner le processus de conduite d'affaire d'Évents & Studios : quatorze
étapes, du premier contact du client jusqu'au solde encaissé et à la FNE émise. Il
s'adresse à Joël-Christian Lopy (Lycris), solopreneur — gérant, directeur artistique,
commercial et chef de projet à la fois — qui travaille en français et n'a pas de temps
à perdre en allers-retours.

Le point de départ est toujours le même : **l'information existe déjà quelque part**. Odoo
porte l'historique commercial, les coûts, les plannings, les feuilles de temps et la
comptabilité. Avant de poser une question à Lycris, va la chercher là. Ce qui reste
après cette lecture, ce sont les seules choses que lui seul sait — et c'est de celles-là
qu'on parle.

## Décisions déjà prises (21/09/2026) — ne pas les reposer

| Sujet | Décision |
|---|---|
| Accès à Odoo | `https://manage.eventsetstudios.ci` (public, sans Tailscale) — Tailscale `100.119.180.128:8069` et LAN en secours |
| Marge | Un chargé de production **ne voit pas** la marge ; elle vit dans es_finance, direction seule |
| TVA | **Plus aucune TVA facturée à partir d'octobre 2026** — toute facture/devis ≥ 01/10/2026 sans taxe |
| Pipelines | CRM et es_finance restent tous deux ; **le CRM est le principal**, es_finance lit et écrit sur le CRM |
| Responsables | **Toujours un chargé de projet**, et **un chargé de mission par mission** s'il y a des déplacements |

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

La confirmation de commande et la comptabilisation d'une facture ont des effets comptables :
elles restent **couvertes par la validation du temps 2 uniquement si Lycris les y a
explicitement incluses** ; sinon elles restent en brouillon et le skill le dit.

## Première chose à faire : se connecter et situer l'affaire

Ouvre la connexion Odoo avant de répondre quoi que ce soit de chiffré. `scripts/odoo.py`
porte le client et les requêtes courantes ; `references/odoo.md` explique la connexion, les
modèles et les pièges de cette base précise.

```bash
python3 scripts/odoo.py ping
```

Ordre de connexion :

1. **Connecteur MCP Odoo** s'il est présent (`odoo_search_records`, `search_read`,
   `create_records`…) — `scripts/odoo.py` le détecte ;
2. sinon **XML-RPC sur `https://manage.eventsetstudios.ci`** avec les identifiants lus dans
   l'environnement (`ODOO_URL`, `ODOO_DB`, `ODOO_USER`, `ODOO_PASSWORD` ou clé d'API) — jamais
   écrits dans le skill ;
3. sinon le dire et travailler sur le référentiel embarqué.

Si la connexion échoue, **dis-le tout de suite et n'invente rien**. Quand le domaine
`manage.eventsetstudios.ci` est hors allowlist du bac à sable (en-tête `x-deny-reason`),
bascule sur le connecteur MCP. Dans tous les cas annonce clairement que le chiffrage repose
sur le référentiel (`references/referentiel.md`) et non sur les affaires en base. Toujours
passer `{'lang': 'fr_FR'}` dans le contexte des lectures RPC.

Situe ensuite l'affaire dans le cycle :

| Ce qu'il dit | Où on en est | Va à |
|---|---|---|
| « X me demande… », « j'ai une demande pour… », « nouvelle demande de X » | 01 — opportunité CRM | Phase A + `references/crm.md` |
| « j'ai une commande », « X m'a commandé… », « on a un nouveau job » | 01→14 — mode commande en 3 temps | `references/workflow-commande.md` |
| « je facture combien », « fais-moi un devis », « chiffre-moi » | 02 | Phase B |
| « il a signé », « ils ont validé le devis » | 03-05 | Phase C |
| « qui je mets dessus », « qui est dispo » | 06-09 | Phase D |
| « où on en est », « ça coûte combien pour l'instant » | 10 | Phase E |
| « il a des retours », « on a livré », « je peux facturer » | 11-14 | Phase F |
| « point du lundi », « clôture la mission/session », « j'ai dépensé X », « où en est l'argent », « bilan de l'affaire », « fin de mois intervenants » | routines | `references/routines.md` |

En cas de doute, demande sur quelle affaire on travaille et cherche le projet ou la commande
dans Odoo plutôt que de supposer.

---

## Le mode « j'ai une commande » — déroulé en 3 temps

C'est le cœur pour un solopreneur : Lycris dit une phrase, le skill fait le reste. Le détail
complet est dans `references/workflow-commande.md`.

**Temps 1 — Préparer par questions.** Lire Odoo (fiche client, factures ouvertes, affaires
comparables, dispos). Poser les questions **par séries de 4 à 6**, en réponses cliquables,
chacune comme **hypothèse pré-remplie à confirmer**. Séries dans l'ordre : client et
commercial → le travail (intention, livrables, droits, corrections, hors périmètre) →
calendrier/lieux (avec jour de la semaine, une mission par lieu hors Abidjan) →
**responsables — question obligatoire, jamais sautée** (1 chargé de projet toujours, 1 chargé
de mission par mission) → dispositif et équipe (titulaire + alternative par rôle, coût jour et
canal) → logistique T&E par mission (pas de per diem, au réel d'une étape comparable) →
l'argent (prix, coût de revient, marge, condition de paiement). Produire une **fiche commande**
d'une page + tableau d'arbitrage (forfait et T&E sur deux lignes distinctes).

**Temps 2 — Validation unique.** Lycris arbitre l'ensemble une fois. Le skill récapitule la
liste exacte de ce qu'il va écrire et attend un « oui ».

**Temps 3 — La cascade** (dans l'ordre, chaque écriture annoncée avec son identifiant) :
opportunité CRM → devis → confirmation → facture d'acompte (brouillon) → `es.deal` / journal
→ budget es_finance → sessions / missions / affectations (`quantity=1`, `day_rate` avec
`day_rate_is_override`) / tâches par étape + 4 tâches satellites par session → responsables
inscrits (`project.project.user_id` + `es.mission` — `fields_get` avant d'écrire, signaler si
pas de compte Odoo) → feuilles de service + activités de rappel. Voir `references/workflow-commande.md`.

---

## Proposition guidée à partir des factures (matching ≤ 13 mois)

Pour « propose un prix pour… », « combien pour un spot 60s ? » : wizard en 5 étapes
(client → contexte → livrables → tarification → résumé) qui réutilise les factures
du client si disponibles, sinon toutes les factures ≤ 13 mois, et propose des
montants de référence avec sources et stats.

```bash
python3 scripts/proposal.py --start                                    # wizard CLI
python3 scripts/proposal.py --input brief.json --output proposal.json  # API JSON
python3 scripts/proposal.py --to-proforma proposal.json --numero PRO-2026-014  # vers proforma.py
```

Règles impératives :
- chaque suggestion porte ses **sources** (IDs factures, dates) et ses **stats**
  (moyenne, médiane, min, max, écart-type, effectif) — prix suggéré = médiane ;
- sans historique pertinent (score < 0,45) : répondre exactement
  **« Je ne peux pas confirmer ça »** et demander une saisie manuelle — jamais de prix inventé ;
- champ manquant (client, service, taxe…) : section « création dynamique de champ »
  avec confirmation explicite avant de continuer ;
- chaque calcul écrit un audit dans `logs/proposals.log`
  (`proposal_id`, `computed_at`, `algorithm_version`, `source_invoice_ids`, `computed_by`) ;
- changements DB uniquement via `migrations/` (UP + DOWN testés) ;
- Odoo injoignable → fallback `references/referentiel.md`, annoncé dans la sortie.

---

## Phase A — Comprendre la demande (étapes 01 et 06)

C'est la phase où l'on gagne ou perd l'affaire. Cherche d'abord dans Odoo (client, historique,
affaires du même type), puis ne pose que ce qui manque et change le prix, l'équipe, les dates
ou le périmètre. Toujours sous forme d'hypothèse à confirmer, 4 à 6 par tour.

Points à couvrir : intention, dates/lieu/durée, livrables (nature, quantité, formats, délai),
dispositif, contraintes de lieu, diffusion/droits, tours de correction inclus, circuit de
validation, condition de paiement, apporteur d'affaires et commission, hors périmètre.
Produit : **note de cadrage** courte, qui fera autorité en phase F.

## Phase B — Chiffrer la proforma (étape 02)

Par **analogie** avec ce qui a déjà été vendu et réellement coûté, pas au doigt mouillé.
Méthode dans `references/devis.md` : trouve les affaires comparables
(`scripts/analogues.py`), compose depuis le catalogue (14 produits — rester au catalogue),
chiffre le coût de revient (équipe × jours × coût jour + régie + location + prestataires +
commission), vérifie la marge (vise **65 %**, alerte < **60 %**), propose la condition de
paiement selon l'historique. Livrable : tableau d'arbitrage puis proforma XLSX/PDF
(`scripts/proforma.py`). Devis Odoo en brouillon seulement si demandé.

**TVA :** depuis le 01/10/2026, aucune taxe sur les lignes des factures/devis à cette date ou
après. Le cas « acompte avant octobre avec TVA / solde après » se signale sans corriger seul.

## Phase C — Ouvrir l'affaire (étapes 03 à 05)

Accord écrit préalable (03). Étape 04 conditionnelle : le déclencheur dépend de la condition
de paiement (acompte 70/50/100 % → encaissement ; sans acompte → accord écrit seul — mais
signaler que les dates sont bloquées sans avance). Confirmation → projet + tâches créés par
Odoo ; vérifier `account_id` et `project_id` de chaque ligne (piège du projet fantôme
« … - MODÈLE — … »).

## Phase D — Découper le travail et armer l'équipe (étapes 06 à 09)

Tâches (07) : Pré-production → Production → Post-production → Validation client → Livré,
chacune avec livrable et échéance (voir `references/es_production.md` : 4 tâches satellites
par session J−2/J/J+1/J+2).

Équipe (08-09) : `scripts/equipe.py` propose par rôle un titulaire + une alternative
(disponibilité — congés `validate`, affectations, indisponibilités — + expérience + tenue des
délais + coût jour). Signaler les conflits sans bloquer. **Double comptage** : une seule voie
porte le coût (feuille de temps **ou** facture fournisseur — coût jour à 0 = montage facture).
Convention : 1 journée de tournage = 1 jour de feuille de temps (tarif forfaitaire).

Responsables : toujours un **chargé de projet** ; un **chargé de mission par mission** dès
qu'il y a un déplacement hors Abidjan (voir `references/workflow-commande.md`). La fiche
commande n'est pas validable sans eux. Affectations écrites avec `quantity=1` et
`day_rate_is_override` (défaut ×8 connu). Feuille de service lisible sur téléphone.

## Phase E — Suivre l'exécution (étape 10)

Vigie : tâches en retard/sans responsable, feuilles de temps manquantes (marge fausse et
flatteuse), dépenses non rattachées, écart coût réel cumulé vs prévisionnel > 10 %. Chiffre
et source, jamais d'impression. `scripts/odoo.py projet <id>` et `references/es_finance.md`
(marge sur la compta, pas sur es_production).

## Phase F — Valider, corriger, livrer, solder (étapes 11 à 14)

Validation : retours consolidés en une liste écrite et datée. Correction : boucle fermée sur
la note de cadrage — dans le périmètre et les tours prévus → on corrige, hors périmètre →
on chiffre l'avenant. Livraison : formats/supports/droits conformes, archive, clôture, acte
écrit (ouvre le droit au solde). Solde : facture depuis la même commande que l'acompte,
rappel du montant/échéance selon condition. Vérifier **RCCM + compte contribuable** avant
toute facturation, et **FNE** : une affaire n'est close qu'avec solde encaissé **et** FNE
émise (`es.deal.is_closed`) — voir `references/comptabilite.md`.

---

## Les modules qui portent l'affaire

- **CRM** (`crm.lead`) : toute demande = opportunité (étape 01), étapes en français calées
  sur les 14 étapes, relances. Le CRM est le principal ; es_finance lit/écrit dessus.
  Détail : `references/crm.md`.
- **es_production** (Projet / Session / Mission) : modèle, 5 règles de rattachement,
  séquence 10 points avant/pendant/après, canal de coût `es_cost_channel`, parc matériel,
  `es.crew.ledger`, défauts connus, frontière marge. Détail : `references/es_production.md`.
- **es_finance** : lit la comptabilité/facturation (marge sur la compta), onglets Trésorerie /
  Projets / À venir / Dépenses / Répartition / Alertes, charges fixes, alertes, 67 % de
  dépenses non rattachées. Détail : `references/es_finance.md`.
- **Comptabilité & fiscalité** : plan comptable, journaux, FNE (DGI 27/01/2026), règle TVA
  octobre 2026, salaires par bulletins. Détail : `references/comptabilite.md`.
- **Routines solopreneur** : 9 commandes en une phrase, modèles par type d'affaire,
  écritures groupées, brouillons de messages, `es_ops_queue`. Détail :
  `references/routines.md` et `references/modeles-affaires.md`.

## Ce que tu remontes sans qu'on te le demande

En deux lignes, en fin de réponse, pas en préambule — la réponse à la question posée passe
d'abord. Vérifie en une lecture :

- **Le client doit-il encore de l'argent ?** Facture ouverte → durcir la condition.
- **Les prestataires de la dernière affaire ont-ils été payés ?** Décompte arrêté fin de
  mois, paiement dû au 15. Contrôler `es.crew.ledger` avant de rebooker.
- **Les dates tombent-elles un week-end ?** Dis le jour de la semaine, pas seulement la date.
- **La fiche client est-elle complète ?** RCCM + compte contribuable manquants bloquent facture et FNE.
- **Une affaire close attend-elle encore sa FNE ou son solde ?** Elle n'apparaît nulle part comme urgente.
- **Projet sans chargé de projet / mission sans chargé de mission ?** À signaler au point du lundi.

---

## Garde-fous

- **Ne jamais écrire dans Odoo sans accord explicite sur le contenu exact.** Annoncer ensuite ce
  qui a été créé, avec les identifiants, pour que Lycris puisse vérifier.
- **Ne jamais envoyer quoi que ce soit à un client.** Pas de devis envoyé, pas de facture
  envoyée, pas de relance partie. Le skill prépare, Lycris envoie.
- **Ne jamais confirmer une commande ni valider une facture automatiquement** sans qu'elles
  aient été explicitement incluses dans la validation du temps 2. Ces deux actions ont des
  effets comptables.
- **Ne jamais inventer un chiffre.** Si Odoo est injoignable ou si l'historique est trop mince,
  dis-le et donne la fourchette avec son hypothèse.
- **Toujours passer `{'lang': 'fr_FR'}`** dans le contexte des lectures RPC.
- **Répondre en français**, en francs CFA, et rester concis : le tableau et l'arbitrage d'abord,
  l'explication seulement si elle change la décision.
- **Marge invisible à l'équipe** : ne jamais inscrire la marge dans un document/tâche/message
  visible par l'équipe (feuille de service, description de tâche, fil). Tant que le lot 2
  es_production n'est pas livré, ne montrer la marge qu'à Lycris.
- **TVA post-octobre 2026** : proposer le retrait de la taxe 18 % par défaut sur les 14
  produits, sans l'appliquer seul ; signaler le cas limite acompte avec TVA / solde sans.
- **Responsables** : lire `fields_get` pour `es.deal` et `es.mission` avant d'écrire ;
  si la personne n'a pas de compte utilisateur, le signaler et proposer d'ouvrir un accès
  ou de désigner un utilisateur existant — ne crée aucun compte seul.
- **Projet fantôme** : vérifier `project_id` de chaque `sale.order.line` après confirmation.

---

## Fichiers de référence

| Fichier | Quand le lire |
|---|---|
| `references/odoo.md` | Avant toute lecture/écriture : connexion, modèles, champs, pièges |
| `references/referentiel.md` | Catalogue 14 produits, prix, coûts jour, équipe, conditions de paiement, identité légale |
| `references/devis.md` | Phase B : méthode de chiffrage par analogie, proforma, marge |
| `references/workflow-commande.md` | Mode « j'ai une commande » : 3 temps, questionnaire, fiche commande, cascade |
| `references/crm.md` | CRM — opportunités, étapes, relances, lien es_finance |
| `references/es_production.md` | Production — Projet/Session/Mission, matériel, coûts, défauts |
| `references/es_finance.md` | Finance — trésorerie, budgets, alertes, marge sur la compta |
| `references/comptabilite.md` | Comptabilité/fiscalité — plan comptable, FNE, TVA octobre 2026 |
| `references/routines.md` | Routines solopreneur — 9 commandes en une phrase + automatismes |
| `references/modeles-affaires.md` | Modèles par type d'affaire — dispositif/équipe/tâches/lignes par défaut |

| Script | Ce qu'il fait |
|---|---|
| `scripts/odoo.py` | Client XML-RPC/MCP + commandes : `ping`, `client`, `projet`, `catalogue`, `equipe`, `commandes`, `factures` ; helpers `list_invoices`, `create_dynamic_field` |
| `scripts/analogues.py` | Affaires comparables (montant, jours, marge) + suggestions prix factures (`--suggest`, backend `matching.py`) |
| `scripts/matching.py` | Matching factures ≤ 13 mois : normalisation, TF-IDF, scoring, stats + sources |
| `scripts/proposal.py` | Wizard proposition guidée : `proposal.json` + audit (`--start`, `--input`, `--to-proforma`) |
| `scripts/equipe.py` | Disponibilité + expérience + délais + coût |
| `scripts/proforma.py` | Génère XLSX + PDF à la charte |
| `scripts/commande.py` | Fiche commande JSON → plan d'écriture (`--dry-run` par défaut) puis exécution (`--executer`) |

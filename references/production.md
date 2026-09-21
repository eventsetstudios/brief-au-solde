# Production — standard studio (arborescence NAS, nommage, workflow)

Standard de production Évents & Studios : tout projet suit la même arborescence,
les mêmes règles de nommage et le même pipeline brief → solde. Ce fichier fait
autorité pour l'organisation des fichiers ; `scripts/scaffold.py` l'applique
(voir `SKILL.md`, section « Standard studio »).

---

## 1. Arborescence obligatoire

```text
CLIENT/
└── 2026/
    └── Nom_Projet/
        ├── 01_creation/
        │   ├── 01_brief_refs/
        │   ├── 02_sources/
        │   └── 03_BAT/
        ├── 02_footages/
        │   ├── 01_rushs/
        │   │   ├── J01_DATE_A-CAM/
        │   │   ├── J01_DATE_B-CAM/
        │   │   └── DRONE/
        │   ├── 02_audio/
        │   ├── 03_photos_plateau/
        │   └── 04_stock/
        ├── 03_projets/
        │   ├── 01_premiere_resolve/
        │   └── 02_after_effects/
        ├── 04_pre-rendus/
        │   ├── V01/
        │   ├── V02/
        │   └── V03/
        └── 05_rendus/
            ├── 01_master_video/
            ├── 02_social_media/
            └── 03_delivery_package/
```

- `Nom_Projet` : snake_case explicite (`Festival_Grillades_Abidjan`), sans espaces.
- Jours de rushs : `J01_2026-11-14_A-CAM`, `J01_2026-11-14_B-CAM`, `DRONE` par jour
  (ex. `J01_2026-11-14_DRONE` si plusieurs jours de drone).
- Création = génération automatique de **toute** l'arborescence d'un coup
  (`scaffold.py --client X --projet Y`) — jamais à la main, jamais partielle.

## 2. Règles de production (non négociables)

| Règle | Détail |
|---|---|
| Rushs IMMUTABLES | `02_footages/01_rushs` : lecture seule après ingest. Jamais de modification, jamais de suppression hors `es_ops_queue` |
| Projets = travail | `03_projets` : uniquement fichiers de travail (Premiere/Resolve/AE). Aucun export |
| Pré-rendus = validation | `04_pre-rendus/Vxx` : exports de validation client, numérotés V01, V02, V03… |
| Rendus verrouillés | `05_rendus` : finals après validation écrite. `03_delivery_package` = master + sociaux + justificatifs |
| Versionnage | Chaque version clairement numérotée (V01, V02, V03). Pas de `final`, `final2`, `definitif` |

## 3. Pipeline métier (dossier actif ↔ statut Odoo)

| # | Étape | Dossier actif | Miroir Odoo (statut projet / tâche) |
|---|---|---|---|
| 1 | Brief reçu | `01_creation/01_brief_refs` | Prospect / Pré-production |
| 2 | Concept validé (BAT) | `01_creation/03_BAT` | Pré-production |
| 3 | Tournage | `02_footages` | Production |
| 4 | Montage | `03_projets` | Post-production |
| 5 | Validation client | `04_pre-rendus` | Validation client |
| 6 | Livraison | `05_rendus` | Livré |

Le statut Odoo est le **miroir du dossier actif** : quand l'équipe bascule de
dossier, le statut suit (`scaffold.py --statut`). Les aller-retours client
(V01 → retours → V02) restent dans `04_pre-rendus` tant que la livraison n'est
pas actée par écrit (boucle étape 12, voir note de cadrage).

## 4. Facturation en 3 phases (brief → solde)

Toute proposition se structure en 3 phases, facturables séparément ou regroupées :

| Phase | Contenu | Dossiers couverts |
|---|---|---|
| **1 — Pré-production** | Idée, script, direction artistique, repérages | `01_creation` |
| **2 — Production** | Tournage / création (jours, équipe, drone, régie) | `02_footages` |
| **3 — Post-production** | Montage, design, étalonnage, mix, exports | `03_projets` → `05_rendus` |

- Phase 1 ≈ forfait créa (produits 106/110 selon ampleur) ; Phase 2 ≈ jours ×
  catalogue (107/111/112/113) ; Phase 3 ≈ montage (109) + motion (110).
- La T&E (119) reste sur sa **ligne séparée** (règle 706100, voir `comptabilite.md`),
  rattachée à la phase 2.
- Acompte 70/30 : l'acompte couvre les phases 1+2 ; le solde se facture à la
  livraison actée (phase 3 close + FNE à émettre).

## 5. Nommage standard : `CLIENT_PROJET_TYPE_VERSION_DATE.ext`

```text
CLIENT_PROJET_TYPE_VERSION_DATE.ext
```

| Exemple | Lecture |
|---|---|
| `NESTLE_MAGGI_TVC_V1_2026-09-21.mp4` | client NESTLE, projet MAGGI, TVC, V1 |
| `SUCAF_EVENT_PHOTO_001.CR2` | client SUCAF, event, photo n° 001 (série : numéro, pas de version) |
| `BRAND_SOCIAL_9x16_V2.mp4` | client BRAND, social 9x16, V2 |

Règles : MAJUSCULES, `_` comme séparateur, date `AAAA-MM-JJ`, version `Vn`
(zéro-pad `V01` dans les dossiers, `V1` accepté dans les noms de fichiers si
cohérent sur le projet). `scaffold.py --verifier-nom` contrôle le format.

## 6. Tri automatique au dépôt

| Fichier déposé | Destination |
|---|---|
| Rush (`.CR2`, `.ARW`, `.BRAW`, `.MP4`/`.MOV` caméra, `.WAV` enregistreur) | `02_footages/01_rushs/Jxx_DATE_<CAM>` ou `02_audio` pour l'audio |
| Export `*V01*`, `*V02*`… | `04_pre-rendus/Vxx` (crée `Vxx` si besoin) — la version gagne toujours : un fichier versionné n'est jamais un final |
| Master / final **sans version** (`*MASTER*`, `*FINAL*`, `*16x9*`, `*9x16*`) | `05_rendus/01_master_video` ou `02_social_media` selon format |
| Projet (`.prproj`, `.drp`, `.aep`) | `03_projets/...` — jamais un export |
| Brief, refs, BAT (`.pdf`, `.docx`, `.jpg` refs) | `01_creation/...` selon étape |

`02_footages` = seuls les médias bruts ; tout le reste est refusé au tri
(signalé, pas déplacé en silence).

## 7. Intelligence de proposition (besoins cachés)

Quand un client demande un service, proposer d'office ce qu'il oublie :

| Demande | Besoins cachés à proposer |
|---|---|
| Tournage / captation | DA, script, repérage (phase 1) + montage + 2 tours de correction (phase 3) |
| Spot / pub | Script, casting, voix off, habillage motion, déclinaisons 9x16 |
| Photos événement | Tri, retouche lot, galerie BAT, cession droits |
| Social media | Formats par plateforme, sous-titres, versions courtes |

Détection d'incohérences : budget < coût de revient prévisionnel, livrables sans
phase 3 chiffrée, tournée multi-villes sans T&E séparée, droits larges au prix
des droits restreints → signaler avant de chiffrer (marge 65 % / alerte 60 %,
voir `devis.md`).

## 8. Sortie attendue (toujours, dans cet ordre)

1. **Résumé** du projet (1 page : intention, livrables, dates, lieux)
2. **Découpage** production (phases 1/2/3, sessions, missions)
3. **Planning** logique (J−2/J/J+1/J+2 par session, jalons BAT/V01/livraison)
4. **Budget** estimatif (par phase + T&E séparée, marge, condition de paiement)
5. **Structure** de dossiers complète (générée par `scaffold.py`)
6. **Risques / points à valider** (droits, autorisations, apporteur, RCCM/CC, FNE)

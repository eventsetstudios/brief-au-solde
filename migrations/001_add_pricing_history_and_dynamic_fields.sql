-- =====================================================================
-- Migration 001 — brief-au-solde : historique de prix + champs dynamiques
-- Style : SQL brut (compatible PostgreSQL 12+ et SQLite 3.25+).
-- Usage :
--   * appliquer (UP)   : psql -f 001_add_pricing_history_and_dynamic_fields.sql
--                        (ou : sqlite3 base.db < 001_..._up.sql après découpe)
--   * annuler (DOWN)   : exécuter uniquement la section -- DOWN ci-dessous.
--   * test rollback    : tests/test_proposal.py::test_migration_up_down
-- Tables :
--   pricing_history — lignes de prix constatées (factures) pour le matching.
--   dynamic_fields  — champs créés à la volée par le wizard (traçabilité).
-- Devise par défaut : XOF. Langue : français.
-- =====================================================================

-- ============================== UP ===================================

CREATE TABLE IF NOT EXISTS pricing_history (
    id INTEGER PRIMARY KEY,
    -- PostgreSQL : INTEGER PRIMARY KEY accepte des ids explicites ; pour un
    -- compteur automatique natif, remplacer par BIGSERIAL (hors SQLite).
    invoice_id INTEGER NOT NULL,
    client_id INTEGER NOT NULL,
    service_code TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT '',
    label TEXT NOT NULL DEFAULT '',
    unit_price NUMERIC NOT NULL CHECK (unit_price >= 0),
    currency TEXT NOT NULL DEFAULT 'XOF',
    invoice_date DATE NOT NULL,
    source TEXT NOT NULL DEFAULT 'odoo',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pricing_history_client_service
    ON pricing_history (client_id, service_code);
CREATE INDEX IF NOT EXISTS idx_pricing_history_date
    ON pricing_history (invoice_date);
CREATE INDEX IF NOT EXISTS idx_pricing_history_service
    ON pricing_history (service_code);

CREATE TABLE IF NOT EXISTS dynamic_fields (
    id INTEGER PRIMARY KEY,
    entity TEXT NOT NULL,
    field_key TEXT NOT NULL,
    field_type TEXT NOT NULL DEFAULT 'char',
    field_value TEXT,
    proposal_id TEXT,
    created_by TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (entity, field_key, proposal_id)
);

CREATE INDEX IF NOT EXISTS idx_dynamic_fields_proposal
    ON dynamic_fields (proposal_id);

-- ============================== DOWN (rollback) ======================
-- Pour annuler : exécuter les deux ordres ci-dessous.
-- DROP TABLE IF EXISTS dynamic_fields;
-- DROP TABLE IF EXISTS pricing_history;

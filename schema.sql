-- ============================================================
-- BANCO DE DADOS — Imersão BJJ Chapada Diamantina
-- PostgreSQL
-- ============================================================

-- Tabela principal de inscrições
CREATE TABLE inscricoes (
    id                SERIAL PRIMARY KEY,
    
    -- Dados pessoais
    nome              VARCHAR(120)  NOT NULL,
    apelido           VARCHAR(60),
    email             VARCHAR(120)  NOT NULL UNIQUE,
    whatsapp          VARCHAR(20)   NOT NULL,
    cidade            VARCHAR(80)   NOT NULL,
    graduacao         VARCHAR(30)   NOT NULL,
    academia          VARCHAR(100),
    tipo_quarto       VARCHAR(20)   NOT NULL DEFAULT 'compartilhado',  -- compartilhado | privativo
    restricoes        TEXT,
    
    -- Pagamento
    forma_pagamento   VARCHAR(20),                 -- cartao | pix | boleto
    status_pagamento  VARCHAR(20)  NOT NULL DEFAULT 'pendente',
                                                   -- pendente | pago | cancelado | reembolsado
    valor_cobrado     NUMERIC(10,2),
    
    -- Dados do Mercado Pago
    mp_preference_id  VARCHAR(100),                -- ID da preferência criada no MP
    mp_payment_id     VARCHAR(100),                -- ID do pagamento confirmado
    mp_status         VARCHAR(50),                 -- status retornado pelo MP
    mp_status_detail  VARCHAR(100),
    
    -- Controle
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    confirmed_at      TIMESTAMPTZ                  -- quando o pagamento foi confirmado
);

-- Índices para buscas frequentes
CREATE INDEX idx_inscricoes_email          ON inscricoes (email);
CREATE INDEX idx_inscricoes_status         ON inscricoes (status_pagamento);
CREATE INDEX idx_inscricoes_mp_preference  ON inscricoes (mp_preference_id);
CREATE INDEX idx_inscricoes_mp_payment     ON inscricoes (mp_payment_id);

-- Trigger para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_inscricoes_updated_at
    BEFORE UPDATE ON inscricoes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Log de eventos de pagamento (auditoria completa)
CREATE TABLE pagamento_eventos (
    id              SERIAL PRIMARY KEY,
    inscricao_id    INTEGER REFERENCES inscricoes(id) ON DELETE SET NULL,
    mp_payment_id   VARCHAR(100),
    evento_tipo     VARCHAR(60),      -- payment.created | payment.updated | etc.
    status          VARCHAR(50),
    status_detail   VARCHAR(100),
    payload_raw     TEXT,             -- JSON completo recebido do webhook
    recebido_em     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_pag_eventos_inscricao  ON pagamento_eventos (inscricao_id);
CREATE INDEX idx_pag_eventos_payment    ON pagamento_eventos (mp_payment_id);

-- View útil para o painel administrativo
CREATE VIEW vw_inscricoes_resumo AS
SELECT
    id,
    nome,
    email,
    whatsapp,
    cidade,
    graduacao,
    tipo_quarto,
    forma_pagamento,
    status_pagamento,
    valor_cobrado,
    created_at,
    confirmed_at,
    CASE tipo_quarto
        WHEN 'privativo' THEN 1490.00 + 300.00
        ELSE 1490.00
    END AS valor_esperado
FROM inscricoes
ORDER BY created_at DESC;

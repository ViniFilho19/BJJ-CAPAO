"""
app.py — Backend Imersão BJJ Chapada Diamantina
Flask + PostgreSQL + Mercado Pago

Deploy: Railway  (railway.toml incluso no projeto)
"""

import os
import json
import hashlib
import hmac
import logging
from datetime import datetime, timezone

import psycopg2
import psycopg2.extras
import mercadopago
from flask import Flask, request, jsonify, abort
from dotenv import load_dotenv

load_dotenv()

# ── Logging ─────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(levelname)s  %(message)s'
)
log = logging.getLogger(__name__)

# ── App & Credenciais ────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.environ["FLASK_SECRET_KEY"]

MP_ACCESS_TOKEN   = os.environ["MP_ACCESS_TOKEN"]
MP_WEBHOOK_SECRET = os.environ.get("MP_WEBHOOK_SECRET", "")
APP_BASE_URL      = os.environ["APP_BASE_URL"].rstrip("/")
DATABASE_URL      = os.environ["DATABASE_URL"]

sdk = mercadopago.SDK(MP_ACCESS_TOKEN)

VALOR_BASE      = 1490.00
VALOR_PRIVATIVO =  300.00

# ── CORS ─────────────────────────────────────────────────────
# Permite que a landing page (qualquer origem) chame a API.
# Em produção você pode restringir para o domínio real:
#   ALLOWED_ORIGIN = "https://seu-dominio.com"
ALLOWED_ORIGIN = os.environ.get("ALLOWED_ORIGIN", "*")

@app.after_request
def add_cors(response):
    response.headers["Access-Control-Allow-Origin"]  = ALLOWED_ORIGIN
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response

@app.route("/", methods=["OPTIONS"])
@app.route("/<path:path>", methods=["OPTIONS"])
def options_handler(path=""):
    return jsonify({}), 200


# ── Banco de dados ───────────────────────────────────────────
def get_db():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    return conn


# ── Utilitários ──────────────────────────────────────────────
def calcular_valor(tipo_quarto: str) -> float:
    return VALOR_BASE + (VALOR_PRIVATIVO if tipo_quarto == "privativo" else 0)


def verificar_assinatura_webhook(payload: bytes, assinatura_recebida: str) -> bool:
    """
    Valida a assinatura HMAC-SHA256 que o Mercado Pago envia no header x-signature.
    Impede que qualquer pessoa chame o webhook manualmente.
    """
    if not MP_WEBHOOK_SECRET:
        log.warning("MP_WEBHOOK_SECRET não configurado — assinatura não verificada.")
        return True

    expected = hmac.new(
        MP_WEBHOOK_SECRET.encode("utf-8"),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, assinatura_recebida or "")


# ── ROTA 1: Inscrição + criação de preferência Mercado Pago ──
@app.route("/inscricao", methods=["POST"])
def inscricao():
    """
    Recebe o JSON do formulário da landing page.
    1. Valida campos obrigatórios
    2. Bloqueia e-mail já pago; reutiliza pendente
    3. Salva/atualiza no banco com status 'pendente'
    4. Cria preferência de pagamento no Mercado Pago
    5. Retorna { checkout_url, inscricao_id, preference_id }
    """
    data = request.get_json(force=True) or {}

    # Validação
    obrigatorios = ["nome", "email", "whatsapp", "cidade", "graduacao"]
    for campo in obrigatorios:
        if not str(data.get(campo, "")).strip():
            return jsonify({"erro": f"Campo obrigatório ausente: {campo}"}), 400

    email           = data["email"].strip().lower()
    nome            = data["nome"].strip()
    tipo_quarto     = data.get("tipo_quarto", "compartilhado")
    forma_pagamento = data.get("forma_pagamento", "cartao")
    valor           = calcular_valor(tipo_quarto)

    conn = get_db()
    try:
        with conn:
            cur = conn.cursor()

            # Verifica duplicidade
            cur.execute("SELECT id, status_pagamento FROM inscricoes WHERE email = %s", (email,))
            existente = cur.fetchone()

            if existente and existente["status_pagamento"] == "pago":
                return jsonify({"erro": "Este e-mail já possui uma inscrição confirmada e paga."}), 409

            if existente:
                # Reutiliza inscrição pendente — atualiza dados caso tenha mudado algo
                inscricao_id = existente["id"]
                cur.execute(
                    """UPDATE inscricoes SET
                        nome=%s, apelido=%s, whatsapp=%s, cidade=%s, graduacao=%s,
                        academia=%s, tipo_quarto=%s, restricoes=%s,
                        forma_pagamento=%s, valor_cobrado=%s, updated_at=NOW()
                    WHERE id=%s""",
                    (
                        nome,
                        data.get("apelido", "").strip(),
                        data.get("whatsapp", "").strip(),
                        data.get("cidade", "").strip(),
                        data["graduacao"],
                        data.get("academia", "").strip(),
                        tipo_quarto,
                        data.get("restricoes", "").strip(),
                        forma_pagamento,
                        valor,
                        inscricao_id,
                    )
                )
                log.info("Inscrição pendente reutilizada: id=%s email=%s", inscricao_id, email)
            else:
                # Nova inscrição
                cur.execute(
                    """INSERT INTO inscricoes
                        (nome, apelido, email, whatsapp, cidade, graduacao,
                         academia, tipo_quarto, restricoes, forma_pagamento, valor_cobrado)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    RETURNING id""",
                    (
                        nome,
                        data.get("apelido", "").strip(),
                        email,
                        data.get("whatsapp", "").strip(),
                        data.get("cidade", "").strip(),
                        data["graduacao"],
                        data.get("academia", "").strip(),
                        tipo_quarto,
                        data.get("restricoes", "").strip(),
                        forma_pagamento,
                        valor,
                    )
                )
                inscricao_id = cur.fetchone()["id"]
                log.info("Nova inscrição criada: id=%s email=%s", inscricao_id, email)

            # ── Preferência Mercado Pago ───────────────────────
            preference_data = {
                "items": [{
                    "id":          str(inscricao_id),
                    "title":       "Imersão BJJ Chapada Diamantina 2025",
                    "description": f"Inscrição · {tipo_quarto} · {data['graduacao']}",
                    "quantity":    1,
                    "unit_price":  valor,
                    "currency_id": "BRL",
                }],
                "payer": {
                    "name":  nome,
                    "email": email,          # ← vínculo com o banco pelo e-mail
                },
                "back_urls": {
                    "success": f"{APP_BASE_URL}/pagamento/sucesso",
                    "failure": f"{APP_BASE_URL}/pagamento/falha",
                    "pending": f"{APP_BASE_URL}/pagamento/pendente",
                },
                "auto_return": "approved",
                "notification_url": f"{APP_BASE_URL}/webhook",
                "external_reference": str(inscricao_id),   # ← vínculo com o banco pelo ID
                "payment_methods": {
                    "installments": 6,
                },
                "statement_descriptor": "ALLIANCE BJJ",
            }

            resultado = sdk.preference().create(preference_data)

            if resultado["status"] != 201:
                log.error("Erro MP ao criar preferência: %s", resultado)
                return jsonify({"erro": "Falha ao iniciar pagamento. Tente novamente em instantes."}), 502

            preference_id = resultado["response"]["id"]
            checkout_url  = resultado["response"]["init_point"]
            # Para testes no sandbox: resultado["response"]["sandbox_init_point"]

            cur.execute(
                "UPDATE inscricoes SET mp_preference_id=%s WHERE id=%s",
                (preference_id, inscricao_id)
            )

        log.info("Preferência criada: pref=%s inscricao=%s valor=%.2f", preference_id, inscricao_id, valor)
        return jsonify({
            "checkout_url":  checkout_url,
            "inscricao_id":  inscricao_id,
            "preference_id": preference_id,
        }), 201

    except Exception:
        log.exception("Erro interno em /inscricao")
        return jsonify({"erro": "Erro interno no servidor. Tente novamente."}), 500
    finally:
        conn.close()


# ── ROTA 2: Webhook do Mercado Pago ─────────────────────────
@app.route("/webhook", methods=["POST"])
def webhook():
    """
    Recebe notificações automáticas do Mercado Pago.
    Fluxo:
    1. Verifica assinatura HMAC para garantir autenticidade
    2. Extrai payment_id do payload
    3. Consulta o pagamento na API do MP
    4. Busca a inscrição pelo external_reference (ID) e/ou email do pagador
    5. Atualiza status no banco
    6. Registra evento de auditoria em pagamento_eventos
    """
    payload_bytes     = request.get_data()
    assinatura_header = request.headers.get("x-signature", "")

    if not verificar_assinatura_webhook(payload_bytes, assinatura_header):
        log.warning("Webhook com assinatura inválida — rejeitado.")
        abort(401)

    data = request.get_json(force=True) or {}
    log.info("Webhook recebido: %s", json.dumps(data)[:300])

    evento_tipo = data.get("type", "")
    if evento_tipo != "payment":
        return jsonify({"status": "ignored", "type": evento_tipo}), 200

    payment_id = str(data.get("data", {}).get("id", ""))
    if not payment_id:
        return jsonify({"status": "sem_payment_id"}), 200

    # Consulta o pagamento no Mercado Pago
    try:
        resposta_mp = sdk.payment().get(payment_id)
    except Exception:
        log.exception("Erro ao consultar MP para payment_id=%s", payment_id)
        return jsonify({"erro": "falha ao consultar MP"}), 502

    if resposta_mp["status"] != 200:
        log.error("MP erro payment_id=%s: %s", payment_id, resposta_mp)
        return jsonify({"status": "erro_mp"}), 200

    pagamento        = resposta_mp["response"]
    mp_status        = pagamento.get("status", "")
    mp_status_detail = pagamento.get("status_detail", "")
    payer_email      = pagamento.get("payer", {}).get("email", "").lower().strip()
    external_ref     = str(pagamento.get("external_reference", ""))
    valor_pago       = pagamento.get("transaction_amount", 0)

    log.info(
        "Pagamento MP: id=%s status=%s detail=%s email=%s ref=%s valor=%.2f",
        payment_id, mp_status, mp_status_detail, payer_email, external_ref, valor_pago
    )

    # Mapa de status MP → nosso status
    STATUS_MAP = {
        "approved":     "pago",
        "rejected":     "cancelado",
        "cancelled":    "cancelado",
        "refunded":     "reembolsado",
        "charged_back": "reembolsado",
        "pending":      "pendente",
        "in_process":   "pendente",
        "authorized":   "pendente",
    }
    novo_status  = STATUS_MAP.get(mp_status, "pendente")
    confirmed_at = datetime.now(timezone.utc) if novo_status == "pago" else None

    conn = get_db()
    try:
        with conn:
            cur = conn.cursor()

            # Busca a inscrição — estratégia dupla: ID (external_reference) e email
            inscricao = None

            if external_ref.isdigit():
                cur.execute("SELECT * FROM inscricoes WHERE id = %s", (int(external_ref),))
                inscricao = cur.fetchone()

            if not inscricao and payer_email:
                cur.execute("SELECT * FROM inscricoes WHERE email = %s", (payer_email,))
                inscricao = cur.fetchone()

            # Registra auditoria sempre (mesmo sem inscrição encontrada)
            cur.execute(
                """INSERT INTO pagamento_eventos
                    (inscricao_id, mp_payment_id, evento_tipo, status, status_detail, payload_raw)
                VALUES (%s, %s, %s, %s, %s, %s)""",
                (
                    inscricao["id"] if inscricao else None,
                    payment_id,
                    evento_tipo,
                    mp_status,
                    mp_status_detail,
                    json.dumps(pagamento),
                )
            )

            if not inscricao:
                log.warning(
                    "Nenhuma inscrição encontrada: payment_id=%s email=%s ref=%s",
                    payment_id, payer_email, external_ref
                )
                return jsonify({"status": "inscricao_nao_encontrada"}), 200

            # Atualiza a inscrição
            cur.execute(
                """UPDATE inscricoes SET
                    status_pagamento = %s,
                    mp_payment_id    = %s,
                    mp_status        = %s,
                    mp_status_detail = %s,
                    confirmed_at     = COALESCE(confirmed_at, %s)
                WHERE id = %s""",
                (novo_status, payment_id, mp_status, mp_status_detail, confirmed_at, inscricao["id"])
            )

            log.info("Inscrição id=%s → status=%s (mp_status=%s)", inscricao["id"], novo_status, mp_status)

        return jsonify({"status": "ok", "inscricao_status": novo_status}), 200

    except Exception:
        log.exception("Erro ao processar webhook payment_id=%s", payment_id)
        return jsonify({"erro": "erro interno"}), 500
    finally:
        conn.close()


# ── ROTA 3: Consulta de status (usada pelo front após retorno) ──
@app.route("/status/<int:inscricao_id>", methods=["GET"])
def status_inscricao(inscricao_id):
    """
    Retorna o status de pagamento de uma inscrição.
    O front consulta esta rota logo após o usuário voltar do checkout do MP,
    para decidir o que mostrar (aprovado, pendente, etc.).
    """
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, nome, email, status_pagamento, confirmed_at FROM inscricoes WHERE id = %s",
            (inscricao_id,)
        )
        row = cur.fetchone()
        if not row:
            return jsonify({"erro": "Inscrição não encontrada"}), 404

        resultado = dict(row)
        if resultado.get("confirmed_at"):
            resultado["confirmed_at"] = resultado["confirmed_at"].isoformat()
        return jsonify(resultado), 200
    finally:
        conn.close()


# ── ROTA 4: Painel admin (protegido por token Bearer) ────────
@app.route("/admin/inscricoes", methods=["GET"])
def admin_inscricoes():
    """
    Lista todas as inscrições com status de pagamento.
    Use: curl -H "Authorization: Bearer SEU_ADMIN_TOKEN" <url>/admin/inscricoes
    """
    token_esperado = f"Bearer {os.environ.get('ADMIN_TOKEN', '')}"
    if request.headers.get("Authorization", "") != token_esperado:
        abort(403)

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM vw_inscricoes_resumo")
        rows = []
        for r in cur.fetchall():
            row = dict(r)
            for k, v in row.items():
                if isinstance(v, datetime):
                    row[k] = v.isoformat()
            rows.append(row)
        return jsonify({"total": len(rows), "inscricoes": rows}), 200
    finally:
        conn.close()


# ── Rotas de retorno do Mercado Pago ─────────────────────────
# O MP redireciona o usuário para estas URLs após o checkout.
# Elas redirecionam de volta para a landing page com ?status=...
# para que o script.js possa exibir a mensagem correta.

@app.route("/pagamento/sucesso")
def pagamento_sucesso():
    payment_id   = request.args.get("payment_id", "")
    inscricao_id = request.args.get("external_reference", "")
    # Redireciona para a landing page com parâmetros de status
    landing_url = os.environ.get("LANDING_PAGE_URL", APP_BASE_URL)
    redirect_url = (
        f"{landing_url}/#inscricao"
        f"?status=approved"
        f"&payment_id={payment_id}"
        f"&external_reference={inscricao_id}"
    )
    return f"""<!DOCTYPE html><html><head>
    <meta http-equiv="refresh" content="1;url={redirect_url}">
    <style>body{{font-family:sans-serif;text-align:center;margin-top:4rem;background:#0d1a0e;color:#f5f0e8}}</style>
    </head><body><p>Pagamento aprovado! Redirecionando...</p></body></html>"""


@app.route("/pagamento/falha")
def pagamento_falha():
    inscricao_id = request.args.get("external_reference", "")
    landing_url  = os.environ.get("LANDING_PAGE_URL", APP_BASE_URL)
    redirect_url = f"{landing_url}/#inscricao?status=failure&external_reference={inscricao_id}"
    return f"""<!DOCTYPE html><html><head>
    <meta http-equiv="refresh" content="1;url={redirect_url}">
    <style>body{{font-family:sans-serif;text-align:center;margin-top:4rem;background:#0d1a0e;color:#f5f0e8}}</style>
    </head><body><p>Pagamento não aprovado. Redirecionando...</p></body></html>"""


@app.route("/pagamento/pendente")
def pagamento_pendente():
    inscricao_id = request.args.get("external_reference", "")
    landing_url  = os.environ.get("LANDING_PAGE_URL", APP_BASE_URL)
    redirect_url = f"{landing_url}/#inscricao?status=pending&external_reference={inscricao_id}"
    return f"""<!DOCTYPE html><html><head>
    <meta http-equiv="refresh" content="1;url={redirect_url}">
    <style>body{{font-family:sans-serif;text-align:center;margin-top:4rem;background:#0d1a0e;color:#f5f0e8}}</style>
    </head><body><p>Pagamento em análise. Redirecionando...</p></body></html>"""


# ── Inicialização ────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug)

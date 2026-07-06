"""
app.py — Backend Imersão BJJ Chapada Diamantina
Flask + PostgreSQL + Mercado Pago
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

# ── Configuração ────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.environ["FLASK_SECRET_KEY"]

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

MP_ACCESS_TOKEN  = os.environ["MP_ACCESS_TOKEN"]
MP_WEBHOOK_SECRET = os.environ.get("MP_WEBHOOK_SECRET", "")
APP_BASE_URL     = os.environ["APP_BASE_URL"].rstrip("/")
DATABASE_URL     = os.environ["DATABASE_URL"]

sdk = mercadopago.SDK(MP_ACCESS_TOKEN)

VALOR_BASE     = 1490.00
VALOR_PRIVATIVO = 300.00


# ── Banco de dados ───────────────────────────────────────────
def get_db():
    """Retorna uma conexão PostgreSQL."""
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    return conn


# ── Utilitários ──────────────────────────────────────────────
def calcular_valor(tipo_quarto: str) -> float:
    base = VALOR_BASE
    if tipo_quarto == "privativo":
        base += VALOR_PRIVATIVO
    return base


def verificar_assinatura_webhook(payload: bytes, assinatura_recebida: str) -> bool:
    """
    Valida a assinatura HMAC-SHA256 enviada pelo Mercado Pago no header
    x-signature. Evita que qualquer um chame seu webhook maliciosamente.
    """
    if not MP_WEBHOOK_SECRET:
        log.warning("MP_WEBHOOK_SECRET não configurado — pulando verificação de assinatura.")
        return True

    expected = hmac.new(
        MP_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, assinatura_recebida or "")


# ── CORS simples (para a landing page chamar a API) ──────────
@app.after_request
def add_cors(response):
    response.headers["Access-Control-Allow-Origin"]  = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response

@app.route("/", methods=["OPTIONS"])
@app.route("/<path:path>", methods=["OPTIONS"])
def options_handler(path=""):
    return jsonify({}), 200


# ── ROTA 1: Receber inscrição e criar preferência de pagamento ──
@app.route("/inscricao", methods=["POST"])
def inscricao():
    """
    Recebe os dados do formulário da landing page.
    1. Valida campos obrigatórios
    2. Verifica se o e-mail já está inscrito
    3. Salva no banco com status 'pendente'
    4. Cria uma preferência de pagamento no Mercado Pago
    5. Retorna a URL de checkout do MP para o front redirecionar
    """
    data = request.get_json(force=True)

    # Validação básica
    campos_obrigatorios = ["nome", "email", "whatsapp", "cidade", "graduacao"]
    for campo in campos_obrigatorios:
        if not data.get(campo, "").strip():
            return jsonify({"erro": f"Campo obrigatório ausente: {campo}"}), 400

    email          = data["email"].strip().lower()
    nome           = data["nome"].strip()
    tipo_quarto    = data.get("tipo_quarto", "compartilhado")
    forma_pagamento = data.get("forma_pagamento", "cartao")
    valor          = calcular_valor(tipo_quarto)

    conn = get_db()
    try:
        with conn:
            cur = conn.cursor()

            # Verifica duplicidade de e-mail
            cur.execute("SELECT id, status_pagamento FROM inscricoes WHERE email = %s", (email,))
            existente = cur.fetchone()

            if existente:
                if existente["status_pagamento"] == "pago":
                    return jsonify({"erro": "Este e-mail já possui uma inscrição confirmada."}), 409
                # Se pendente, reaproveita o registro (permite tentar pagar novamente)
                inscricao_id = existente["id"]
                cur.execute(
                    """UPDATE inscricoes SET
                        nome=%s, whatsapp=%s, cidade=%s, graduacao=%s,
                        academia=%s, tipo_quarto=%s, restricoes=%s,
                        forma_pagamento=%s, valor_cobrado=%s, updated_at=NOW()
                    WHERE id=%s""",
                    (
                        nome, data.get("whatsapp","").strip(),
                        data.get("cidade","").strip(), data["graduacao"],
                        data.get("academia","").strip(), tipo_quarto,
                        data.get("restricoes","").strip(),
                        forma_pagamento, valor, inscricao_id
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
                        nome, data.get("apelido","").strip(), email,
                        data.get("whatsapp","").strip(), data.get("cidade","").strip(),
                        data["graduacao"], data.get("academia","").strip(),
                        tipo_quarto, data.get("restricoes","").strip(),
                        forma_pagamento, valor
                    )
                )
                inscricao_id = cur.fetchone()["id"]
                log.info("Nova inscrição criada: id=%s email=%s", inscricao_id, email)

            # ── Cria preferência no Mercado Pago ──────────────
            preference_data = {
                "items": [
                    {
                        "id": str(inscricao_id),
                        "title": "Imersão BJJ Chapada Diamantina 2025",
                        "description": f"Inscrição — {tipo_quarto} — {data['graduacao']}",
                        "quantity": 1,
                        "unit_price": valor,
                        "currency_id": "BRL",
                    }
                ],
                "payer": {
                    "name": nome,
                    "email": email,           # ← chave de vínculo com o registro
                },
                "back_urls": {
                    "success": f"{APP_BASE_URL}/pagamento/sucesso",
                    "failure": f"{APP_BASE_URL}/pagamento/falha",
                    "pending": f"{APP_BASE_URL}/pagamento/pendente",
                },
                "auto_return": "approved",
                "notification_url": f"{APP_BASE_URL}/webhook",
                "external_reference": str(inscricao_id),  # ID do nosso banco
                "payment_methods": {
                    "excluded_payment_types": [],
                    "installments": 6,
                },
                "statement_descriptor": "ALLIANCE BJJ",
            }

            resultado = sdk.preference().create(preference_data)

            if resultado["status"] != 201:
                log.error("Erro ao criar preferência MP: %s", resultado)
                return jsonify({"erro": "Erro ao iniciar pagamento. Tente novamente."}), 502

            preference_id  = resultado["response"]["id"]
            checkout_url   = resultado["response"]["init_point"]       # produção
            # checkout_url = resultado["response"]["sandbox_init_point"]  # testes

            # Salva o preference_id no banco
            cur.execute(
                "UPDATE inscricoes SET mp_preference_id=%s WHERE id=%s",
                (preference_id, inscricao_id)
            )

        log.info("Preferência MP criada: preference_id=%s inscricao_id=%s", preference_id, inscricao_id)
        return jsonify({
            "checkout_url": checkout_url,
            "inscricao_id": inscricao_id,
            "preference_id": preference_id,
        }), 201

    except Exception as e:
        log.exception("Erro em /inscricao")
        return jsonify({"erro": "Erro interno. Tente novamente."}), 500
    finally:
        conn.close()


# ── ROTA 2: Webhook do Mercado Pago ─────────────────────────
@app.route("/webhook", methods=["POST"])
def webhook():
    """
    Recebe notificações IPN/Webhook do Mercado Pago.
    O MP chama esta rota toda vez que um pagamento muda de status.

    Fluxo de validação:
    1. Verifica assinatura HMAC (garante que veio do MP)
    2. Lê o tipo do evento (só processa 'payment')
    3. Consulta o pagamento na API do MP pelo payment_id
    4. Busca a inscrição pelo e-mail do pagador (payer.email)
       OU pelo external_reference (nosso ID)
    5. Atualiza o status no banco
    """
    payload_bytes = request.get_data()
    assinatura    = request.headers.get("x-signature", "")

    if not verificar_assinatura_webhook(payload_bytes, assinatura):
        log.warning("Webhook recebido com assinatura inválida.")
        abort(401)

    data = request.get_json(force=True)
    log.info("Webhook recebido: %s", json.dumps(data))

    evento_tipo = data.get("type", "")
    
    # O MP também envia eventos de teste — ignora silenciosamente
    if evento_tipo not in ("payment",):
        return jsonify({"status": "ignored"}), 200

    payment_id = str(data.get("data", {}).get("id", ""))
    if not payment_id:
        return jsonify({"status": "sem payment_id"}), 200

    # ── Consulta o pagamento na API do MP ─────────────────────
    try:
        resposta_mp = sdk.payment().get(payment_id)
    except Exception as e:
        log.exception("Erro ao consultar pagamento no MP: payment_id=%s", payment_id)
        return jsonify({"erro": "falha ao consultar MP"}), 502

    if resposta_mp["status"] != 200:
        log.error("MP retornou erro para payment_id=%s: %s", payment_id, resposta_mp)
        return jsonify({"status": "erro_mp"}), 200

    pagamento        = resposta_mp["response"]
    mp_status        = pagamento.get("status", "")           # approved | rejected | pending...
    mp_status_detail = pagamento.get("status_detail", "")
    payer_email      = pagamento.get("payer", {}).get("email", "").lower().strip()
    external_ref     = str(pagamento.get("external_reference", ""))
    valor_pago       = pagamento.get("transaction_amount", 0)

    log.info(
        "Pagamento MP: id=%s status=%s email=%s external_ref=%s valor=%.2f",
        payment_id, mp_status, payer_email, external_ref, valor_pago
    )

    conn = get_db()
    try:
        with conn:
            cur = conn.cursor()

            # ── Busca a inscrição ──────────────────────────────
            # Estratégia 1: pelo external_reference (nosso ID no banco)
            inscricao = None
            if external_ref.isdigit():
                cur.execute(
                    "SELECT * FROM inscricoes WHERE id = %s",
                    (int(external_ref),)
                )
                inscricao = cur.fetchone()

            # Estratégia 2: pelo e-mail do pagador (vínculo principal)
            if not inscricao and payer_email:
                cur.execute(
                    "SELECT * FROM inscricoes WHERE email = %s",
                    (payer_email,)
                )
                inscricao = cur.fetchone()

            # Registra o evento de auditoria independente de encontrar inscrição
            cur.execute(
                """INSERT INTO pagamento_eventos
                    (inscricao_id, mp_payment_id, evento_tipo, status, status_detail, payload_raw)
                VALUES (%s,%s,%s,%s,%s,%s)""",
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
                    "Nenhuma inscrição encontrada para payment_id=%s email=%s ref=%s",
                    payment_id, payer_email, external_ref
                )
                return jsonify({"status": "inscricao_nao_encontrada"}), 200

            # ── Atualiza status da inscrição ───────────────────
            novo_status = {
                "approved":        "pago",
                "rejected":        "cancelado",
                "cancelled":       "cancelado",
                "refunded":        "reembolsado",
                "charged_back":    "reembolsado",
                "pending":         "pendente",
                "in_process":      "pendente",
                "authorized":      "pendente",
            }.get(mp_status, "pendente")

            confirmed_at = None
            if novo_status == "pago":
                confirmed_at = datetime.now(timezone.utc)

            cur.execute(
                """UPDATE inscricoes SET
                    status_pagamento = %s,
                    mp_payment_id    = %s,
                    mp_status        = %s,
                    mp_status_detail = %s,
                    confirmed_at     = COALESCE(confirmed_at, %s)
                WHERE id = %s""",
                (
                    novo_status, payment_id, mp_status,
                    mp_status_detail, confirmed_at, inscricao["id"]
                )
            )

            log.info(
                "Inscrição id=%s atualizada → status=%s (mp=%s)",
                inscricao["id"], novo_status, mp_status
            )

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
    Permite que a landing page consulte se o pagamento foi confirmado
    após o usuário ser redirecionado de volta do Mercado Pago.
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
        return jsonify(dict(row)), 200
    finally:
        conn.close()


# ── ROTA 4: Painel admin básico (protegido por token) ────────
@app.route("/admin/inscricoes", methods=["GET"])
def admin_inscricoes():
    """
    Lista todas as inscrições. Proteja com um token no header:
    Authorization: Bearer SEU_TOKEN_ADMIN
    """
    token = request.headers.get("Authorization", "")
    if token != f"Bearer {os.environ.get('ADMIN_TOKEN', '')}":
        abort(403)

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM vw_inscricoes_resumo")
        rows = [dict(r) for r in cur.fetchall()]
        # Serializa datas
        for r in rows:
            for k, v in r.items():
                if isinstance(v, datetime):
                    r[k] = v.isoformat()
        return jsonify({"total": len(rows), "inscricoes": rows}), 200
    finally:
        conn.close()


# ── Páginas de retorno do MP ─────────────────────────────────
@app.route("/pagamento/sucesso")
def pagamento_sucesso():
    payment_id    = request.args.get("payment_id", "")
    inscricao_id  = request.args.get("external_reference", "")
    # Redireciona de volta para a landing page com parâmetros
    return f"""
    <html><head><meta http-equiv="refresh"
      content="2;url={APP_BASE_URL.replace('/api','')}/obrigado.html
               ?inscricao={inscricao_id}&payment={payment_id}">
    </head><body>
    <p style="font-family:sans-serif;text-align:center;margin-top:3rem">
      Pagamento confirmado! Redirecionando...</p>
    </body></html>
    """

@app.route("/pagamento/falha")
def pagamento_falha():
    return """
    <html><body>
    <p style="font-family:sans-serif;text-align:center;margin-top:3rem;color:#c00">
      Pagamento não aprovado. Volte e tente novamente.</p>
    </body></html>
    """

@app.route("/pagamento/pendente")
def pagamento_pendente():
    return """
    <html><body>
    <p style="font-family:sans-serif;text-align:center;margin-top:3rem">
      Pagamento em análise. Você receberá um e-mail quando for confirmado.</p>
    </body></html>
    """


# ── Inicialização ────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_ENV") == "development")

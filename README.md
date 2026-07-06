<<<<<<< HEAD
# Backend — Imersão BJJ Chapada Diamantina

Backend Flask para gerenciar inscrições e validar pagamentos via Mercado Pago.

---

## Estrutura de arquivos

```
bjj-backend/
├── app.py                  # Aplicação principal
├── schema.sql              # Banco de dados PostgreSQL
├── requirements.txt        # Dependências Python
├── railway.toml            # Config de deploy
├── .env.example            # Modelo das variáveis de ambiente
├── script_pagamento.js     # Trecho para integrar na landing page
└── README.md
```

---

## Passo a passo: do zero ao ar

### 1. Conta no Mercado Pago Developers

1. Acesse https://www.mercadopago.com.br/developers
2. Crie um aplicativo (botão "Criar aplicação")
3. Vá em **Credenciais de produção** → copie o **Access Token**
4. Guarde também o **Client ID** e **Client Secret** (podem ser necessários depois)

> Use as credenciais de **teste** (sandbox) enquanto desenvolve.
> Troque para produção apenas quando for lançar.

---

### 2. Deploy no Railway

**a)** Acesse https://railway.app e faça login com GitHub

**b)** Clique em **New Project → Deploy from GitHub repo**
   - Selecione o repositório com estes arquivos

**c)** Adicione o banco PostgreSQL:
   - No projeto, clique em **New → Database → PostgreSQL**
   - O Railway cria o banco e gera a variável `DATABASE_URL` automaticamente

**d)** Configure as variáveis de ambiente:
   - No serviço Flask, vá em **Variables** e adicione:

```
MP_ACCESS_TOKEN     = seu_token_do_mercado_pago
MP_WEBHOOK_SECRET   = uma_string_aleatoria_qualquer (você define)
APP_BASE_URL        = https://seu-projeto.up.railway.app
FLASK_SECRET_KEY    = string_aleatoria_longa
ADMIN_TOKEN         = outro_token_secreto_para_o_painel
FLASK_ENV           = production
```

   > `DATABASE_URL` já é preenchida automaticamente pelo Railway.

**e)** Após o deploy, copie a URL gerada (ex: `https://bjj-abc123.up.railway.app`)

---

### 3. Criar as tabelas no banco

Com a URL do banco em mãos (disponível em Variables → DATABASE_URL):

```bash
# Instale o psql localmente se não tiver
# No Windows: baixe o PostgreSQL e use o psql do menu iniciar

psql "postgresql://usuario:senha@host:5432/railway" -f schema.sql
```

Ou pelo painel do Railway: vá no serviço PostgreSQL → **Query** → cole o conteúdo do `schema.sql`.

---

### 4. Configurar o webhook no Mercado Pago

1. Acesse https://www.mercadopago.com.br/developers/panel/app
2. Selecione seu aplicativo → **Webhooks**
3. Clique em **Adicionar URL de produção**
4. URL: `https://seu-projeto.up.railway.app/webhook`
5. Eventos: marque **Pagamentos**
6. Copie o **segredo** gerado e coloque em `MP_WEBHOOK_SECRET` no Railway

---

### 5. Integrar na landing page

No seu `script.js`, substitua a função `handleSubmit()` pelo conteúdo de
`script_pagamento.js` e atualize a constante `API_URL`:

```javascript
const API_URL = "https://seu-projeto.up.railway.app";
```

---

## Rotas disponíveis

| Método | Rota                     | Descrição                                      |
|--------|--------------------------|------------------------------------------------|
| POST   | `/inscricao`             | Recebe formulário, cria preferência no MP      |
| POST   | `/webhook`               | Recebe notificações de pagamento do MP         |
| GET    | `/status/:id`            | Consulta status de uma inscrição               |
| GET    | `/admin/inscricoes`      | Lista todas as inscrições (requer token)       |
| GET    | `/pagamento/sucesso`     | Página de retorno após pagamento aprovado      |
| GET    | `/pagamento/falha`       | Página de retorno após pagamento rejeitado     |
| GET    | `/pagamento/pendente`    | Página de retorno após pagamento em análise    |

---

## Consultar inscrições (painel admin)

```bash
curl https://seu-projeto.up.railway.app/admin/inscricoes \
  -H "Authorization: Bearer SEU_ADMIN_TOKEN"
```

Retorna JSON com todas as inscrições e status de pagamento.

---

## Fluxo de validação por e-mail

O vínculo entre o pagador e a inscrição é feito em **duas camadas**:

1. **`external_reference`** — ao criar a preferência no MP, enviamos o `id`
   da inscrição no banco. O MP devolve esse valor no webhook.

2. **`payer.email`** — o e-mail informado no formulário é passado para o MP
   como e-mail do pagador. No webhook, comparamos o `payer.email` com
   `inscricoes.email`. Se o usuário tentar pagar com outro e-mail, o sistema
   ainda encontra a inscrição pelo `external_reference`.

Isso garante que:
- Um e-mail só pode ter **uma inscrição paga**
- Tentativas duplicadas são barradas na rota `/inscricao`
- Todo evento de pagamento fica registrado em `pagamento_eventos` para auditoria

---

## Desenvolvimento local

```bash
# Clone o repo e entre na pasta
cd bjj-backend

# Crie o ambiente virtual
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Instale dependências
pip install -r requirements.txt

# Copie e preencha o .env
cp .env.example .env

# Rode localmente
python app.py

# Para testar o webhook localmente, use ngrok:
# ngrok http 5000
# Use a URL gerada como APP_BASE_URL e configure no painel do MP
```
=======
Imersão BJJ Chapada Diamantina



>>>>>>> 9cc74e95fa89fe2e6510e7ac1eb91af0d4c18829

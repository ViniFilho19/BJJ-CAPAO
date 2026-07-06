/**
 * script_pagamento.js
 * Substitui a função handleSubmit() do script.js original.
 * Cole este trecho no seu script.js, substituindo a função handleSubmit existente.
 *
 * Ele envia os dados para o backend Flask, que cria a preferência no
 * Mercado Pago e retorna a URL de checkout — então redireciona o usuário.
 */

// URL do seu backend no Railway (troque após o deploy)
const API_URL = "https://seu-projeto.up.railway.app";

async function handleSubmit() {
  const nome       = document.getElementById("nome").value.trim();
  const apelido    = document.getElementById("apelido").value.trim();
  const email      = document.getElementById("email").value.trim();
  const whatsapp   = document.getElementById("whatsapp").value.trim();
  const cidade     = document.getElementById("cidade").value.trim();
  const graduacao  = document.getElementById("graduacao").value;
  const academia   = document.getElementById("academia").value.trim();
  const quarto     = document.getElementById("quarto").value;
  const restricoes = document.getElementById("restricoes").value.trim();
  const pagamento  = document.querySelector('input[name="pagamento"]:checked')?.value || "cartao";

  // Validação local
  if (!nome || !email || !whatsapp || !graduacao) {
    alert("Por favor, preencha todos os campos obrigatórios (*).");
    return;
  }
  if (!/\S+@\S+\.\S+/.test(email)) {
    alert("Por favor, insira um e-mail válido.");
    return;
  }

  // Feedback visual
  const btn = document.querySelector(".btn-submit");
  const textoOriginal = btn.textContent;
  btn.textContent = "Aguarde...";
  btn.disabled = true;

  try {
    const resposta = await fetch(`${API_URL}/inscricao`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        nome, apelido, email, whatsapp, cidade, graduacao,
        academia, tipo_quarto: quarto, restricoes,
        forma_pagamento: pagamento,
      }),
    });

    const dados = await resposta.json();

    if (!resposta.ok) {
      // Erros conhecidos (e-mail duplicado, campo faltando, etc.)
      alert(dados.erro || "Erro ao processar inscrição. Tente novamente.");
      btn.textContent = textoOriginal;
      btn.disabled = false;
      return;
    }

    // Redireciona para o checkout do Mercado Pago
    // Salva o ID localmente para consultar o status depois
    localStorage.setItem("bjj_inscricao_id", dados.inscricao_id);
    window.location.href = dados.checkout_url;

  } catch (erro) {
    console.error("Erro na requisição:", erro);
    alert("Erro de conexão. Verifique sua internet e tente novamente.");
    btn.textContent = textoOriginal;
    btn.disabled = false;
  }
}

/**
 * Verifica se o usuário voltou do Mercado Pago com pagamento aprovado.
 * Chame esta função na página de obrigado ou ao carregar o index
 * verificando os parâmetros da URL.
 *
 * Exemplo de uso: coloque isso no final do script.js
 *
 *   verificarRetornoPagamento();
 */
async function verificarRetornoPagamento() {
  const params       = new URLSearchParams(window.location.search);
  const inscricaoId  = params.get("inscricao") || localStorage.getItem("bjj_inscricao_id");
  const paymentStatus = params.get("status");     // approved | rejected | pending

  if (!inscricaoId) return;

  if (paymentStatus === "approved") {
    try {
      const resp  = await fetch(`${API_URL}/status/${inscricaoId}`);
      const dados = await resp.json();

      if (dados.status_pagamento === "pago") {
        // Mostra mensagem de sucesso personalizada
        document.getElementById("form-fields").style.display = "none";
        document.getElementById("nome-confirmacao").textContent =
          dados.nome ? dados.nome.split(" ")[0] : "Atleta";
        document.getElementById("success-msg").classList.add("show");
        document.getElementById("form-container")
          .scrollIntoView({ behavior: "smooth", block: "center" });

        localStorage.removeItem("bjj_inscricao_id");
      }
    } catch (e) {
      console.warn("Não foi possível confirmar status do pagamento:", e);
    }
  }
}

// Executa ao carregar a página
document.addEventListener("DOMContentLoaded", verificarRetornoPagamento);

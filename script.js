// =============================================
<<<<<<< HEAD
// CONFIGURAÇÃO — troque após o deploy no Railway
// =============================================
var API_URL = 'https://seu-projeto.up.railway.app';

// =============================================
// CARROSSEL HERO
// =============================================
(function () {
  var track    = document.getElementById('carousel-track');
  var dots     = document.querySelectorAll('.carousel-dot');
  var pauseBtn = document.getElementById('carousel-pause');
  var pauseIcon = document.getElementById('pause-icon');
  var playIcon  = document.getElementById('play-icon');

  var current = 0;
  var paused  = false;
  var timer;
  var total   = document.querySelectorAll('.carousel-slide').length;
=======
// CARROSSEL HERO
// =============================================
(function () {
  const track     = document.getElementById('carousel-track');
  const dots      = document.querySelectorAll('.carousel-dot');
  const pauseBtn  = document.getElementById('carousel-pause');
  const pauseIcon = document.getElementById('pause-icon');
  const playIcon  = document.getElementById('play-icon');

  let current = 0;
  let paused  = false;
  let timer;
  const total = document.querySelectorAll('.carousel-slide').length;
>>>>>>> 9cc74e95fa89fe2e6510e7ac1eb91af0d4c18829

  function goTo(n) {
    current = (n + total) % total;
    track.style.transform = 'translateX(-' + (current * 100) + '%)';
    dots.forEach(function (d, i) {
      d.classList.toggle('active', i === current);
    });
  }

  function next() { goTo(current + 1); }
  function prev() { goTo(current - 1); }

  function startTimer() {
    clearInterval(timer);
<<<<<<< HEAD
    if (!paused) timer = setInterval(next, 4500);
  }

  document.getElementById('carousel-next').addEventListener('click', function () { next(); startTimer(); });
  document.getElementById('carousel-prev').addEventListener('click', function () { prev(); startTimer(); });
=======
    if (!paused) {
      timer = setInterval(next, 4500);
    }
  }

  document.getElementById('carousel-next').addEventListener('click', function () {
    next();
    startTimer();
  });

  document.getElementById('carousel-prev').addEventListener('click', function () {
    prev();
    startTimer();
  });
>>>>>>> 9cc74e95fa89fe2e6510e7ac1eb91af0d4c18829

  dots.forEach(function (dot) {
    dot.addEventListener('click', function () {
      goTo(parseInt(dot.dataset.index, 10));
      startTimer();
    });
  });

  pauseBtn.addEventListener('click', function () {
    paused = !paused;
    pauseIcon.style.display = paused ? 'none'  : 'block';
    playIcon.style.display  = paused ? 'block' : 'none';
    startTimer();
  });

<<<<<<< HEAD
=======
  // Parar ao passar o mouse sobre o hero
>>>>>>> 9cc74e95fa89fe2e6510e7ac1eb91af0d4c18829
  var hero = document.getElementById('hero');
  hero.addEventListener('mouseenter', function () { clearInterval(timer); });
  hero.addEventListener('mouseleave', function () { if (!paused) startTimer(); });

  startTimer();
})();

// =============================================
// HAMBURGER MENU
// =============================================
var hamburger = document.getElementById('hamburger');
var navMenu   = document.getElementById('nav-menu');

hamburger.addEventListener('click', function () {
  navMenu.classList.toggle('open');
});

navMenu.querySelectorAll('a').forEach(function (link) {
  link.addEventListener('click', function () {
    navMenu.classList.remove('open');
  });
});

// =============================================
// NAV — efeito scroll
// =============================================
window.addEventListener('scroll', function () {
  var nav = document.getElementById('navbar');
  nav.style.background = window.scrollY > 60
    ? 'rgba(13,20,15,0.97)'
    : 'rgba(26,58,42,0.92)';
});

// =============================================
<<<<<<< HEAD
// PAGAMENTO — troca de ícone no gateway-area
// (mantido para exibição visual, o MP aceita todos os métodos)
// =============================================
document.querySelectorAll('input[name="pagamento"]').forEach(function (radio) {
  radio.addEventListener('change', function () {
    var aviso = document.querySelector('.form-aviso');
    if (radio.value === 'pix') {
      aviso.textContent = '🔒 Você será redirecionado para pagar via PIX no Mercado Pago.';
    } else if (radio.value === 'boleto') {
      aviso.textContent = '🔒 O boleto será gerado no checkout do Mercado Pago.';
    } else {
      aviso.textContent = '🔒 Seus dados estão seguros. Você será redirecionado para o checkout do Mercado Pago.';
=======
// PAGAMENTO — troca de gateway
// =============================================
document.querySelectorAll('input[name="pagamento"]').forEach(function (radio) {
  radio.addEventListener('change', function () {
    var gw  = document.getElementById('gateway-area');
    var val = radio.value;

    if (val === 'pix') {
      gw.innerHTML =
        '<svg viewBox="0 0 24 24" width="32" height="32" style="display:block;margin:0 auto 0.75rem;stroke:rgba(201,162,39,0.6);fill:none;stroke-width:1.5"><path d="M7.5 12L12 7.5 16.5 12 12 16.5z"/><path d="M4 12L12 4 20 12 12 20z" stroke-dasharray="3,2"/></svg>' +
        '<strong style="color:rgba(245,240,232,0.6); font-size:0.85rem;">Pagamento via PIX</strong><br>' +
        '<span style="font-size:0.72rem; opacity:0.7;">Chave PIX e QR Code serão gerados após integração do gateway.</span>';
    } else if (val === 'boleto') {
      gw.innerHTML =
        '<svg viewBox="0 0 24 24" width="32" height="32" style="display:block;margin:0 auto 0.75rem;stroke:rgba(201,162,39,0.6);fill:none;stroke-width:1.5"><path d="M4 7h16M4 12h16M4 17h16M4 7v10M8 7v10M16 7v10M20 7v10"/></svg>' +
        '<strong style="color:rgba(245,240,232,0.6); font-size:0.85rem;">Pagamento via Boleto</strong><br>' +
        '<span style="font-size:0.72rem; opacity:0.7;">Boleto bancário gerado após confirmação da inscrição.</span>';
    } else {
      gw.innerHTML =
        '<svg viewBox="0 0 24 24" width="28" height="28" style="display:block;margin:0 auto 0.5rem;stroke:rgba(201,162,39,0.4);fill:none;stroke-width:1.5"><rect x="1" y="4" width="22" height="16" rx="2" ry="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>' +
        '<strong style="color:rgba(245,240,232,0.5); font-size:0.85rem;">Área de pagamento</strong><br>' +
        'Gateway de pagamento será integrado aqui.<br>' +
        '<span style="font-size:0.72rem; opacity:0.7;">(Stripe, Mercado Pago, PagSeguro, etc.)</span>';
>>>>>>> 9cc74e95fa89fe2e6510e7ac1eb91af0d4c18829
    }
  });
});

// =============================================
// MÁSCARA WHATSAPP
// =============================================
document.getElementById('whatsapp').addEventListener('input', function (e) {
  var v = e.target.value.replace(/\D/g, '');
  if (v.length <= 11) {
    v = v.replace(/^(\d{2})(\d{5})(\d{0,4})/, '($1) $2-$3');
  }
  e.target.value = v;
});

// =============================================
<<<<<<< HEAD
// HELPERS DE UI
// =============================================
function mostrarErro(msg) {
  var el = document.getElementById('form-erro');
  el.textContent = msg;
  el.style.display = 'block';
  el.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function esconderErro() {
  var el = document.getElementById('form-erro');
  el.style.display = 'none';
  el.textContent = '';
}

function setBotaoLoading(loading) {
  var btn = document.getElementById('btn-submit');
  btn.disabled = loading;
  btn.textContent = loading ? 'Aguarde, processando...' : 'Confirmar inscrição →';
}

// =============================================
// ENVIO DO FORMULÁRIO → BACKEND → MERCADO PAGO
// =============================================
function handleSubmit() {
  esconderErro();

  var nome       = document.getElementById('nome').value.trim();
  var apelido    = document.getElementById('apelido').value.trim();
  var email      = document.getElementById('email').value.trim();
  var whatsapp   = document.getElementById('whatsapp').value.trim();
  var cidade     = document.getElementById('cidade').value.trim();
  var graduacao  = document.getElementById('graduacao').value;
  var academia   = document.getElementById('academia').value.trim();
  var quarto     = document.getElementById('quarto').value;
  var restricoes = document.getElementById('restricoes').value.trim();
  var pagamento  = (document.querySelector('input[name="pagamento"]:checked') || {}).value || 'cartao';

  // Validação local
  if (!nome || !email || !whatsapp || !graduacao || !cidade) {
    mostrarErro('Por favor, preencha todos os campos obrigatórios (*).');
    return;
  }
  if (!/\S+@\S+\.\S+/.test(email)) {
    mostrarErro('Por favor, insira um e-mail válido.');
    return;
  }

  setBotaoLoading(true);

  fetch(API_URL + '/inscricao', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      nome:            nome,
      apelido:         apelido,
      email:           email,
      whatsapp:        whatsapp,
      cidade:          cidade,
      graduacao:       graduacao,
      academia:        academia,
      tipo_quarto:     quarto,
      restricoes:      restricoes,
      forma_pagamento: pagamento
    })
  })
  .then(function (resp) {
    return resp.json().then(function (dados) {
      return { ok: resp.ok, status: resp.status, dados: dados };
    });
  })
  .then(function (res) {
    setBotaoLoading(false);

    if (!res.ok) {
      // Erro conhecido vindo do backend (e-mail duplicado, campo faltando, etc.)
      mostrarErro(res.dados.erro || 'Erro ao processar inscrição. Tente novamente.');
      return;
    }

    // Salva o ID e o nome localmente para usar na tela de retorno
    try {
      localStorage.setItem('bjj_inscricao_id',   String(res.dados.inscricao_id));
      localStorage.setItem('bjj_inscricao_nome',  nome);
    } catch(e) { /* ignora se localStorage não disponível */ }

    // Redireciona para o checkout do Mercado Pago
    window.location.href = res.dados.checkout_url;
  })
  .catch(function (err) {
    setBotaoLoading(false);
    console.error('Erro de rede:', err);
    mostrarErro('Erro de conexão com o servidor. Verifique sua internet e tente novamente.');
  });
}

// =============================================
// RETORNO DO MERCADO PAGO
// Executado ao carregar a página — detecta se o
// usuário voltou do checkout e exibe o status.
// =============================================
(function verificarRetornoPagamento() {
  var params  = new URLSearchParams(window.location.search);
  var mpStatus = params.get('status');            // approved | pending | failure | null
  var extRef   = params.get('external_reference'); // nosso inscricao_id

  // Tenta recuperar o ID do localStorage caso a URL não tenha
  var inscricaoId = extRef || '';
  var nomeLocal   = '';
  try {
    inscricaoId = inscricaoId || localStorage.getItem('bjj_inscricao_id') || '';
    nomeLocal   = localStorage.getItem('bjj_inscricao_nome') || '';
  } catch(e) {}

  // Se não há parâmetros de retorno, não faz nada
  if (!mpStatus || !inscricaoId) return;

  // Rola a página até o formulário para mostrar o resultado
  var formContainer = document.getElementById('form-container');
  if (formContainer) {
    setTimeout(function () {
      formContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 400);
  }

  if (mpStatus === 'approved') {
    // Consulta o backend para confirmar que o status foi realmente salvo
    fetch(API_URL + '/status/' + inscricaoId)
      .then(function (r) { return r.json(); })
      .then(function (dados) {
        var primeiroNome = (dados.nome || nomeLocal || 'Atleta').split(' ')[0];

        if (dados.status_pagamento === 'pago') {
          // Pagamento confirmado no banco → mostra tela de sucesso
          document.getElementById('form-fields').style.display = 'none';
          document.getElementById('nome-confirmacao').textContent = primeiroNome;
          document.getElementById('success-msg').classList.add('show');
          try { localStorage.removeItem('bjj_inscricao_id'); localStorage.removeItem('bjj_inscricao_nome'); } catch(e) {}
        } else {
          // Status ainda não atualizado (webhook pode ter um pequeno delay)
          mostrarRetornoPendente(nomeLocal);
        }
      })
      .catch(function () {
        // Sem resposta do backend — mostra pendente de forma segura
        mostrarRetornoPendente(nomeLocal);
      });

  } else if (mpStatus === 'pending' || mpStatus === 'in_process') {
    mostrarRetornoPendente(nomeLocal);

  } else {
    // failure ou cancelled — mostra erro no formulário
    mostrarErro('O pagamento não foi aprovado. Verifique seus dados e tente novamente.');
    // Limpa a URL para o usuário poder tentar de novo sem ver os parâmetros do MP
    window.history.replaceState({}, document.title, window.location.pathname + '#inscricao');
  }
})();

function mostrarRetornoPendente(nome) {
  document.getElementById('form-fields').style.display = 'none';
  var pendingEl = document.getElementById('pending-msg');
  pendingEl.style.display = 'block';
  var nomeEl = document.getElementById('nome-pendente');
  if (nomeEl) nomeEl.textContent = (nome || 'Atleta').split(' ')[0];
=======
// ENVIO DO FORMULÁRIO
// =============================================
function handleSubmit() {
  var nome      = document.getElementById('nome').value.trim();
  var email     = document.getElementById('email').value.trim();
  var whatsapp  = document.getElementById('whatsapp').value.trim();
  var graduacao = document.getElementById('graduacao').value;

  if (!nome || !email || !whatsapp || !graduacao) {
    alert('Por favor, preencha todos os campos obrigatórios (*).');
    return;
  }

  if (!/\S+@\S+\.\S+/.test(email)) {
    alert('Por favor, insira um e-mail válido.');
    return;
  }

  document.getElementById('form-fields').style.display = 'none';
  document.getElementById('nome-confirmacao').textContent = nome.split(' ')[0];
  document.getElementById('success-msg').classList.add('show');
  document.getElementById('form-container').scrollIntoView({ behavior: 'smooth', block: 'center' });
>>>>>>> 9cc74e95fa89fe2e6510e7ac1eb91af0d4c18829
}

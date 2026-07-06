// =============================================
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

  // Parar ao passar o mouse sobre o hero
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
}

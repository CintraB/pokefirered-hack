/* Página do Professor: câmera sobre o mapa, máquina de escrever, revelação ao rolar e antes × depois.
   Tudo do jogo em fator inteiro: o mapa usa um fator que cobre a tela (--b) vezes o zoom inteiro do capítulo. */
(() => {
  "use strict";
  const raiz = document.documentElement;
  const semMovimento = matchMedia("(prefers-reduced-motion: reduce)");
  const LARGURA = 768, ALTURA = 576;  // kanto_detalhe.png
  const camada = document.getElementById("camada");
  const pino = document.getElementById("pino");
  const placa = document.getElementById("placa");
  const placaNome = document.getElementById("placa-nome");
  const paradas = [...document.querySelectorAll(".hero, .cap, .rodape")];
  const trilha = new Map([...document.querySelectorAll("#trilha a")].map(a => [a.hash.slice(1), a]));
  let atual = null;

  const estreita = () => innerWidth < 800;
  const fatorBase = () => Math.max(1, Math.ceil(innerWidth / LARGURA), Math.ceil(innerHeight / ALTURA));

  // ---------- câmera ----------
  function zoomDe(parada) {
    const z = Math.max(1, Math.round(+parada.dataset.zoom || 1));
    return estreita() ? Math.max(1, z - 1) : z;  // no celular, menos zoom
  }

  function focoDe(parada) {  // onde o lugar fica na tela: no lado livre do painel
    if (!parada.classList.contains("cap")) return [0.5, 0.5];
    if (estreita()) return [0.5, 0.3];  // no celular, acima do painel que sobe
    return [parada.classList.contains("lado-esq") ? 0.72 : 0.28, 0.5];
  }

  function enquadra(parada, instantaneo) {
    const b = fatorBase(), z = zoomDe(parada), escala = b * z;
    const w = innerWidth, h = innerHeight, [fx, fy] = focoDe(parada);
    const px = +parada.dataset.x * escala, py = +parada.dataset.y * escala;
    // deslocamento inteiro e preso às bordas: o mapa sempre cobre a tela
    const tx = Math.round(Math.min(0, Math.max(w - LARGURA * escala, fx * w - px)));
    const ty = Math.round(Math.min(0, Math.max(h - ALTURA * escala, fy * h - py)));
    if (instantaneo) raiz.classList.add("sem-transicao");
    raiz.style.setProperty("--b", b);
    camada.style.transform = `translate(${tx}px, ${ty}px) scale(${z})`;
    pino.style.transform = `translate(${tx + px}px, ${ty + py}px)`;
    pino.classList.toggle("ativo", parada.classList.contains("cap"));
    if (instantaneo) {
      void camada.offsetWidth;
      requestAnimationFrame(() => requestAnimationFrame(() => raiz.classList.remove("sem-transicao")));
    }
  }

  function ativa(parada, instantaneo) {
    if (parada === atual) return;
    atual = parada;
    enquadra(parada, instantaneo || semMovimento.matches);
    placaNome.textContent = parada.dataset.lugar || "";
    if (!semMovimento.matches) {
      placa.classList.remove("entra");
      void placa.offsetWidth;
      placa.classList.add("entra");
    }
    trilha.forEach((a, id) => a.setAttribute("aria-current", String(id === parada.id)));
  }

  // a parada ativa é a que cruza a linha do meio da tela
  const meio = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) ativa(e.target); }),
    { rootMargin: "-50% 0px -50% 0px" });
  paradas.forEach(p => meio.observe(p));

  // ---------- revelação dos painéis ao rolar ----------
  const revela = new IntersectionObserver(es => es.forEach(e => {
    if (e.isIntersecting) { e.target.classList.add("vis"); revela.unobserve(e.target); }
  }), { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
  document.querySelectorAll(".cabeca, .cartao").forEach(el => revela.observe(el));

  // ---------- telas do jogo: maior fator inteiro (em pixels do aparelho) que cabe no cartão, até 2x ----------
  function ajustaTelas() {
    const cartao = document.querySelector(".cartao");
    if (!cartao) return;
    const estilo = getComputedStyle(cartao);
    const livre = cartao.clientWidth - parseFloat(estilo.paddingLeft) - parseFloat(estilo.paddingRight) - 8;
    const dpr = devicePixelRatio || 1;
    const k = Math.floor(Math.min(livre, 480) * dpr / 240);
    raiz.style.setProperty("--tela-w", k >= 1 ? `${240 * k / dpr}px` : `${Math.floor(livre)}px`);
  }

  // ---------- antes × depois ----------
  document.addEventListener("input", e => {
    if (e.target.matches(".ba input")) e.target.parentElement.style.setProperty("--corte", `${e.target.value}%`);
  });

  // ---------- o Professor fala: máquina de escrever, avança com clique, toque ou Enter ----------
  const caixa = document.getElementById("caixa");
  const fala = document.getElementById("fala");
  const leitor = document.getElementById("fala-leitor");
  const falas = [...document.querySelectorAll("#falas li")].map(li => li.textContent.trim());
  const dita = document.createElement("span"), resto = document.createElement("span");
  resto.className = "resto";
  fala.replaceChildren(dita, resto);
  let iFala = 0, timer = 0;

  function termina() {
    clearInterval(timer);
    timer = 0;
    dita.textContent = falas[iFala];
    resto.textContent = "";
    caixa.classList.remove("escrevendo");
  }

  function mostra(i) {
    iFala = i;
    clearInterval(timer);
    leitor.textContent = falas[i];
    if (semMovimento.matches) { termina(); return; }
    const texto = falas[i];
    let n = 0;
    caixa.classList.add("escrevendo");
    // o resto invisível segura as quebras de linha: as palavras não pulam enquanto aparecem
    dita.textContent = "";
    resto.textContent = texto;
    timer = setInterval(() => {
      n += 1;
      dita.textContent = texto.slice(0, n);
      resto.textContent = texto.slice(n);
      if (n >= texto.length) termina();
    }, 28);
  }

  function avanca() {
    if (timer) { termina(); return; }
    if (iFala < falas.length - 1) { mostra(iFala + 1); return; }
    const primeiro = document.querySelector(".cap");
    if (primeiro) primeiro.scrollIntoView({ behavior: semMovimento.matches ? "auto" : "smooth" });
  }

  let heroVisivel = true;
  new IntersectionObserver(es => { heroVisivel = es[0].isIntersecting; }, { threshold: 0.35 })
    .observe(document.getElementById("abertura"));
  caixa.addEventListener("click", avanca);
  document.addEventListener("keydown", e => {
    if (e.target === caixa && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); avanca(); return; }
    if (e.key !== "Enter" || !heroVisivel || e.altKey || e.ctrlKey || e.metaKey) return;
    if (e.target.closest && e.target.closest("a, button, input, select, textarea, summary")) return;
    e.preventDefault();
    avanca();
  });

  // ---------- início ----------
  ajustaTelas();
  addEventListener("resize", () => { ajustaTelas(); if (atual) enquadra(atual, true); });
  mostra(0);

  // ?cap=<id do capítulo ou do cartão> (teste e link direto): já abre lá, sem viagem
  const pedido = new URLSearchParams(location.search).get("cap");
  const alvo = pedido && document.getElementById(pedido);
  const parada = alvo && alvo.closest(".hero, .cap, .rodape");
  if (parada) {
    if ("scrollRestoration" in history) history.scrollRestoration = "manual";
    parada.querySelectorAll(".cabeca, .cartao").forEach(el => el.classList.add("vis"));
    ativa(parada, true);
    const pula = () => alvo.scrollIntoView({ behavior: "instant", block: "start" });
    pula();
    addEventListener("load", pula, { once: true });  // o navegador pode voltar ao topo ao terminar de carregar
  } else {
    ativa(paradas[0], true);
  }
})();

/* Página do Professor: câmera sobre o mapa, máquina de escrever, revelação ao rolar e antes × depois.
   Tudo do jogo em fator inteiro de pixels do APARELHO: o mapa usa o menor fator que cobre a tela (bd) vezes o zoom
   inteiro do capítulo. Durante a viagem da câmera a escala passa por valores quebrados; em repouso é sempre inteira. */
"use strict";

// ---------- funções puras (o test_site_pagina.py as executa no Chrome headless) ----------
const MAPA_W = 768, MAPA_H = 576;  // site/assets/kanto_detalhe.png

/** Sobra além da tela, em px CSS, para o blur() não escurecer a borda: 3 desvios do blur na tela (blur · z). */
function margemBlur(blur, z) {
  return Math.ceil(3 * blur * z - 1e-9);
}

/** Menor fator inteiro, em px do aparelho, que cobre a tela com a sobra do blur (zoom 1). */
function fatorBaseAparelho(vw, vh, dpr, blur) {
  const m = margemBlur(blur, 1);
  return Math.max(1, Math.ceil((vw + 2 * m) * dpr / MAPA_W - 1e-9), Math.ceil((vh + 2 * m) * dpr / MAPA_H - 1e-9));
}

/** Zoom inteiro do capítulo; no celular, 3 vira 2 (com 1, o lugar no canto do mapa não chegaria à sarjeta). */
function zoomEfetivo(zoom, estreita) {
  const z = Math.max(1, Math.round(+zoom || 1));
  return estreita && z > 2 ? z - 1 : z;
}

/**
 * Onde o lugar fica na tela (fração de largura e altura): sempre numa área que o conteúdo não cobre.
 * `lado` é o lado do painel (dir: lugar a oeste). No celular o pino fica na sarjeta, do lado oposto ao painel.
 * No desktop fica no lado livre, a 28%/72% da largura ou no meio da faixa livre, o que estiver mais perto da borda
 * (entre 801 e 1100 px o painel ocupa mais da tela); `coluna` é {left, right} do painel, medido na página.
 */
function focoPara(ehCapitulo, lado, estreita, vw, sarjeta, coluna) {
  if (!ehCapitulo) return [0.5, 0.5];
  if (estreita) {
    if (sarjeta < 40) return [0.5, 0.5];
    return [(lado === "dir" ? sarjeta / 2 : vw - sarjeta / 2) / vw, 0.5];
  }
  if (lado === "esq") {
    const meioLivre = coluna ? (coluna.right + vw) / 2 / vw : 0;
    return [Math.max(0.72, meioLivre), 0.5];
  }
  const meioLivre = coluna ? coluna.left / 2 / vw : 1;
  return [Math.min(0.28, meioLivre), 0.5];
}

/** Fator dos sprites em px CSS por pixel do sprite: inteiro em px do aparelho (3× ou 2× no celular). */
function fatorSprite(dpr, estreita) {
  return Math.max(1, Math.round((estreita ? 2 : 3) * dpr)) / dpr;
}

/**
 * Câmera em repouso: translate (px CSS, inteiros em px do aparelho) e escala da camada.
 * A camada mede MAPA_W·b × MAPA_H·b px CSS, com b = bd/dpr (bd inteiro), e recebe scale(z) com z inteiro:
 * cada pixel do mapa vira bd·z pixels do aparelho. O deslocamento fica preso de modo que o mapa sobre
 * pelo menos margemBlur(blur, z) px além de cada borda da tela.
 */
function calcularCamera({ vw, vh, dpr, x, y, zoom, fx, fy, blur }) {
  const bd = fatorBaseAparelho(vw, vh, dpr, blur);
  const b = bd / dpr, z = zoom, escala = b * z, margem = margemBlur(blur, z);
  const encaixa = (alvo, tela, total) => {
    const min = Math.ceil((tela + margem - total) * dpr - 1e-6);
    const max = Math.floor(-margem * dpr + 1e-6);
    return Math.min(max, Math.max(min, Math.round(alvo * dpr))) / dpr;
  };
  const tx = encaixa(fx * vw - x * escala, vw, MAPA_W * escala);
  const ty = encaixa(fy * vh - y * escala, vh, MAPA_H * escala);
  return { bd, b, z, escala, margem, tx, ty, pinoX: tx + x * escala, pinoY: ty + y * escala };
}

/** Largura da tela do jogo (240×160) no cartão: a maior que cabe, em fator inteiro de px do aparelho ou de px CSS, até 2×. */
function larguraTela(livre, dpr) {
  const limite = Math.min(livre, 480) + 1e-6;
  let melhor = 0;
  for (let k = 1; 240 * k / dpr <= 480 + 1e-6; k++) if (240 * k / dpr <= limite) melhor = Math.max(melhor, 240 * k / dpr);
  for (const c of [1, 2]) if (240 * c <= limite) melhor = Math.max(melhor, 240 * c);
  return melhor || 240;  // nada cabe: 1×, e a figura rola por dentro do cartão
}

// ---------- a página ----------
(() => {
  const raiz = document.documentElement;
  const camada = document.getElementById("camada");
  if (!camada || !("IntersectionObserver" in window)) return;  // sem isso, a página fica estática e tudo visível

  const semMovimento = matchMedia("(prefers-reduced-motion: reduce)");
  const celular = matchMedia("(max-width: 800px)");  // o mesmo corte do estilo.css
  const pequena = matchMedia("(max-width: 540px)");  // idem: sprites em 2× e tela de 240 px
  const pino = document.getElementById("pino");
  const placa = document.getElementById("placa");
  const placaNome = document.getElementById("placa-nome");
  const paradas = [...document.querySelectorAll(".hero, .cap, .rodape")];
  const trilha = new Map([...document.querySelectorAll("#trilha a")].map(a => [a.hash.slice(1), a]));
  let atual = null;

  // altura "grande" da tela (100lvh): a barra de endereço do celular entra e sai sem mexer na câmera
  const regua = document.createElement("div");
  regua.style.cssText = "position:fixed;left:0;top:0;width:0;height:100lvh;visibility:hidden;pointer-events:none";
  document.body.append(regua);
  const alturaTela = () => Math.max(innerHeight, regua.offsetHeight);
  const numeroCss = nome => parseFloat(getComputedStyle(raiz).getPropertyValue(nome)) || 0;

  // ---------- câmera ----------
  function enquadra(parada, instantaneo) {
    const vw = innerWidth, vh = alturaTela(), estreita = celular.matches;
    const coluna = parada.querySelector(".coluna");
    const [fx, fy] = focoPara(parada.classList.contains("cap"), parada.classList.contains("lado-esq") ? "esq" : "dir",
      estreita, vw, numeroCss("--sarjeta"), coluna && coluna.getBoundingClientRect());
    const cam = calcularCamera({ vw, vh, dpr: devicePixelRatio || 1, x: +parada.dataset.x, y: +parada.dataset.y,
      zoom: zoomEfetivo(parada.dataset.zoom, estreita), fx, fy, blur: numeroCss("--blur") });
    if (instantaneo) raiz.classList.add("sem-transicao");
    raiz.style.setProperty("--b", cam.b);
    raiz.style.setProperty("--placa-x", `${fx * 100}%`);
    camada.style.transform = `translate(${cam.tx}px, ${cam.ty}px) scale(${cam.z})`;
    pino.style.transform = `translate(${cam.pinoX}px, ${cam.pinoY}px)`;
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

  // ---------- revelação dos painéis ao rolar (a classe js só entra depois que tudo está pronto) ----------
  const revela = new IntersectionObserver(es => es.forEach(e => {
    if (e.isIntersecting) { e.target.classList.add("vis"); revela.unobserve(e.target); }
  }), { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
  document.querySelectorAll(".cabeca, .cartao").forEach(el => revela.observe(el));

  // ---------- telas do jogo ----------
  function ajustaTelas() {
    const cartao = document.querySelector(".cartao");
    if (!cartao) return;
    const estilo = getComputedStyle(cartao);
    const livre = cartao.clientWidth - parseFloat(estilo.paddingLeft) - parseFloat(estilo.paddingRight) - 8;
    raiz.style.setProperty("--tela-w", `${larguraTela(livre, devicePixelRatio || 1)}px`);
    raiz.style.setProperty("--sprite-k", fatorSprite(devicePixelRatio || 1, pequena.matches));
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

  // ---------- mudanças de tela e de preferência ----------
  let medida = [innerWidth, alturaTela()];
  addEventListener("resize", () => {
    const agora = [innerWidth, alturaTela()];
    if (agora[0] === medida[0] && agora[1] === medida[1]) return;  // só a barra de endereço: a viagem continua
    medida = agora;
    ajustaTelas();
    if (atual) enquadra(atual, true);
  });
  semMovimento.addEventListener("change", () => {
    if (semMovimento.matches) { termina(); placa.classList.remove("entra"); }
    if (atual) enquadra(atual, true);
  });

  // ---------- início ----------
  ajustaTelas();
  mostra(0);
  raiz.classList.add("js");

  // ?cap=<id do capítulo ou do cartão> (teste e link direto): já abre lá, sem viagem
  const pedido = new URLSearchParams(location.search).get("cap");
  const alvo = pedido && document.getElementById(pedido);
  const parada = alvo && alvo.closest(".hero, .cap, .rodape");
  if (parada) {
    if ("scrollRestoration" in history) history.scrollRestoration = "manual";
    const recolhido = alvo.closest("details");
    if (recolhido) recolhido.open = true;  // pediu um cartão da Família: abre o spoiler de propósito
    parada.querySelectorAll(".cabeca, .cartao").forEach(el => el.classList.add("vis"));
    ativa(parada, true);
    const pula = () => alvo.scrollIntoView({ behavior: "instant", block: "start" });
    pula();
    addEventListener("load", pula, { once: true });  // o navegador pode voltar ao topo ao terminar de carregar
  } else {
    ativa(paradas[0], true);
  }
})();

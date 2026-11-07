"""Página do Professor no Chrome headless: câmera (função pura e página real), nitidez, borda, pino e movimento.

Gera o site num diretório temporário, serve por HTTP em 127.0.0.1 e abre uma página-sonda que (1) roda
calcularCamera e larguraTela do pagina.js numa grade de casos e (2) carrega index.html em iframes, um de cada vez,
medindo o estado em repouso. O resultado vai para o DOM e é lido com --dump-dom. Grupos de páginas:
  base      1920×1080, 375×812 e 320×640 (nitidez, borda, spoiler, movimento);
  celulares 360×800, 390×844, 393×852 e 430×932, cada um com seu DPR, nos 13 lugares (pino à vista);
  faixa     600 a 800 px, nos 13 lugares (pino à vista na sarjeta);
  medio     801 a 1100 px, nos 13 lugares (placa fora do painel, pino à vista).
Sem Chrome no ambiente, o teste é pulado. Os perfis temporários do Chrome (pagina-sonda-*) são apagados ao fim.
"""
import functools
import html
import http.server
import importlib.util
import json
import math
import os
import re
import shutil
import subprocess
import threading
import time
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("site_gerar", REPO / "tools/site/gerar.py")
gerar_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gerar_mod)

BLUR = 0.9
MAPA = (768, 576)
DISPOSITIVOS = [(360, 800, 2), (360, 800, 3), (390, 844, 2), (393, 852, 2), (430, 932, 3)]  # largura, altura, DPR
FAIXA = [(600, 900), (650, 900), (700, 900), (768, 1024), (800, 900)]  # 600 a 800 px, ainda no layout de celular
MEDIO = [(801, 800), (900, 800), (1000, 800), (1100, 800)]  # 801 a 1100 px: desktop com o painel largo
CANDIDATOS_CHROME = [
    os.environ.get("PAGINA_CHROME", ""),
    "/mnt/c/Program Files/Google/Chrome/Application/chrome.exe",
    "/mnt/c/Program Files (x86)/Google/Chrome/Application/chrome.exe",
    shutil.which("google-chrome") or "", shutil.which("chromium") or "", shutil.which("chromium-browser") or "",
]
CHROME = next((c for c in CANDIDATOS_CHROME if c and Path(c).is_file()), None)
pytestmark = pytest.mark.skipif(CHROME is None, reason="Chrome não encontrado")

# nome, largura, altura, query
PAGINAS = [
    ("d-abertura", 1920, 1080, ""),
    ("d-pallet", 1920, 1080, "cap=sobre"),
    ("d-celadon", 1920, 1080, "cap=evolucoes"),
    ("d-haunter", 1920, 1080, "cap=evolucoes-haunter-evolui-por-nivel"),
    ("d-cinnabar", 1920, 1080, "cap=lendarios"),
    ("d-indigo", 1920, 1080, "cap=pos_liga"),
    ("d-fim", 1920, 1080, "cap=fim"),
    ("m-pallet", 375, 812, "cap=sobre"),
    ("m-haunter", 375, 812, "cap=evolucoes-haunter-evolui-por-nivel"),
    ("m-cinnabar", 375, 812, "cap=lendarios"),
    ("m-indigo", 375, 812, "cap=pos_liga"),
    ("m-familia", 375, 812, "cap=modernas-familia-sombra"),
    ("p-celadon", 320, 640, "cap=evolucoes"),
]

def _lugares_e_cartoes():
    """[(id do capítulo, id do primeiro cartão)]: com o cartão no alto da tela o painel passa por baixo da placa."""
    return [(c["id"], c["cartoes"][0]["id"]) for c in gerar_mod.carregar_capitulos(REPO)]


def _paginas_dos_grupos():
    lugares = _lugares_e_cartoes()
    assert len(lugares) == 13

    def pagina(w, h, cid, cartao):
        return (f"{w}x{h}-{cid}", w, h, f"cap={cartao}")

    return {
        "base": PAGINAS,
        "celulares": {dpr: [pagina(w, h, cid, cartao) for w, h, d in DISPOSITIVOS if d == dpr for cid, cartao in lugares]
                      for dpr in {d for _, _, d in DISPOSITIVOS}},
        "faixa": [pagina(w, h, cid, cartao) for w, h in FAIXA for cid, cartao in lugares],
        "medio": [pagina(w, h, cid, cartao) for w, h in MEDIO for cid, cartao in lugares]
                 + [(f"{w}x{h}-haunter", w, h, "cap=evolucoes-haunter-evolui-por-nivel") for w, h in MEDIO],
    }


SONDA = r"""<!doctype html>
<html><head><meta charset="utf-8"><title>sonda</title>
<style>body{margin:0} iframe{position:fixed;left:0;top:0;border:0}</style></head>
<body><pre id="resultado">pendente</pre>
<script src="pagina.js"></script>
<script>
const LUGARES = __LUGARES__, GRUPOS = __GRUPOS__;
const params = new URLSearchParams(location.search);
const grupo = params.get("g") || "base";
let PAGINAS = GRUPOS[grupo];
if (!Array.isArray(PAGINAS)) PAGINAS = PAGINAS[params.get("dpr")];  // celulares: um DPR por partida
const res = { puro: [], telas: [], sprites: [], paginas: {} };
if (grupo === "base") for (const [vw, vh] of [[1920, 1080], [375, 812], [320, 640]]) for (const dpr of [1, 1.5, 2])
  for (const [id, l] of Object.entries(LUGARES)) for (const lado of ["esq", "dir"]) {
    const estreita = vw <= 800, sarjeta = !estreita ? 0 : vw < 360 ? 16 : 56;
    const [fx, fy] = focoPara(id !== "abertura", lado, estreita, vw, sarjeta);
    const zoom = zoomEfetivo(l.zoom, estreita);
    res.puro.push(Object.assign({ vw, vh, dpr, id, lado, zoomPedido: l.zoom },
      calcularCamera({ vw, vh, dpr, x: l.x, y: l.y, zoom, fx, fy, blur: __BLUR__ })));
  }
if (grupo === "base") for (const livre of [200, 239, 248, 259, 303, 440, 479, 500]) for (const dpr of [1, 1.25, 1.5, 2, 3])
  res.telas.push({ livre, dpr, w: larguraTela(livre, dpr) });
if (grupo === "base") for (const dpr of [1, 1.25, 1.5, 2, 3]) for (const estreita of [false, true])
  res.sprites.push({ dpr, estreita, k: fatorSprite(dpr, estreita) });

function medir(f, w, h) {
  const d = f.contentDocument, raiz = d.documentElement;
  const camada = d.getElementById("camada"), pino = d.getElementById("pino");
  const m = /translate\(([-\d.e]+)px, ([-\d.e]+)px\) scale\(([\d.]+)\)/.exec(camada.style.transform) || [0, NaN, NaN, NaN];
  const k = d.getElementById("kanto").getBoundingClientRect();
  const p = pino.getBoundingClientRect(), cx = p.left + p.width / 2, cy = p.top + p.height / 2;
  const sob = d.elementFromPoint(cx, cy);
  const placa = d.getElementById("placa").getBoundingClientRect();
  const cruza = r => !(r.right <= placa.left || r.left >= placa.right || r.bottom <= placa.top || r.top >= placa.bottom);
  const paineis = [...d.querySelectorAll(".painel, .spoiler summary")].map(e => e.getBoundingClientRect())
    .filter(r => r.width > 0 && r.bottom > 0 && r.top < h);
  const est = getComputedStyle(raiz);
  return {
    dpr: f.contentWindow.devicePixelRatio, b: parseFloat(raiz.style.getPropertyValue("--b")),
    tx: +m[1], ty: +m[2], z: +m[3], w, h,
    kanto: [k.left, k.top, k.right, k.bottom],
    scrollW: raiz.scrollWidth, clienteW: raiz.clientWidth,
    pinoAtivo: pino.classList.contains("ativo"), pino: [cx, cy], pinoCaixa: [p.left, p.top, p.right, p.bottom],
    pinoOpaco: +getComputedStyle(pino).opacity,
    pinoSobPlaca: !(p.right <= placa.left || p.left >= placa.right || p.bottom <= placa.top || p.top >= placa.bottom),
    sprite: (s => s ? s.getBoundingClientRect().width / s.naturalWidth : 0)(d.querySelector("img.sprite")),
    spriteK: est.getPropertyValue("--sprite-k").trim(),
    pinoCoberto: !!(sob && sob.closest(".painel, details, .caixa, .rodape .painel")),
    placaSobrePainel: paineis.some(cruza),
    detalhesAbertos: [...d.querySelectorAll("details.spoiler")].map(x => x.open),
    js: raiz.classList.contains("js"),
    escrevendo: d.getElementById("caixa").classList.contains("escrevendo"),
    animPino: getComputedStyle(pino).animationName, transCamada: getComputedStyle(camada).transitionDuration,
    filtro: getComputedStyle(d.getElementById("kanto")).filter, blurCss: est.getPropertyValue("--blur").trim(),
    tela: est.getPropertyValue("--tela-w").trim(),
  };
}

(async () => {
  for (const [nome, w, h, q] of PAGINAS) {
    const f = document.createElement("iframe");
    f.width = w; f.height = h;
    await new Promise(ok => { f.onload = ok; f.src = "index.html" + (q ? "?" + q : ""); document.body.append(f); });
    await new Promise(ok => setTimeout(ok, 300));
    try { res.paginas[nome] = medir(f, w, h); } catch (e) { res.paginas[nome] = { erro: String(e) }; }
    f.remove();
  }
  document.getElementById("resultado").textContent = JSON.stringify(res);
})();
</script></body></html>
"""


class _Silencioso(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@pytest.fixture(scope="module")
def servidor(tmp_path_factory):
    site = tmp_path_factory.mktemp("navegador") / "_site"
    gerar_mod.gerar(REPO, site)
    lugares = json.loads((REPO / "site/lugares.json").read_text(encoding="utf-8"))
    (site / "sonda.html").write_text(
        SONDA.replace("__LUGARES__", json.dumps(lugares)).replace("__GRUPOS__", json.dumps(_paginas_dos_grupos()))
        .replace("__BLUR__", str(BLUR)), encoding="utf-8")
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(_Silencioso, directory=str(site)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}/sonda.html"
    srv.shutdown()
    srv.server_close()
    _apagar_perfis()


_cache = {}
_perfis = []
BARRA = chr(92)


def _perfil_temporario(n):
    """Perfil próprio do Chrome a cada execução (evita entregar a URL a outra instância aberta)."""
    nome = f"pagina-sonda-{os.getpid()}-{n}"
    if CHROME.endswith(".exe"):
        temp = subprocess.run(["cmd.exe", "/c", "echo %TEMP%"], capture_output=True, text=True,
                              cwd="/mnt/c").stdout.strip()
        caminho = temp + BARRA + nome
    else:
        caminho = f"/tmp/{nome}"
    _perfis.append(caminho)
    return caminho


def _como_linux(caminho):
    if BARRA in caminho:
        return Path(subprocess.run(["wslpath", "-u", caminho], capture_output=True, text=True).stdout.strip())
    return Path(caminho)


def _apagar_perfis():
    """Apaga os perfis pagina-sonda-* desta execução (o Chrome já saiu; tenta de novo se algo ainda segura)."""
    for caminho in _perfis:
        alvo = _como_linux(caminho)
        for _ in range(6):
            shutil.rmtree(alvo, ignore_errors=True)
            if not alvo.exists():
                break
            time.sleep(0.5)
    _perfis.clear()


def _sondar(url, dpr, sem_movimento, grupo="base"):
    chave = (dpr, sem_movimento, grupo)
    tentativas = []
    while chave not in _cache and len(tentativas) < 2:  # o Chrome às vezes sai sem DOM na 1ª partida fria
        cmd = [CHROME, "--headless=new", "--hide-scrollbars", "--mute-audio", "--no-first-run",
               f"--user-data-dir={_perfil_temporario(f'{len(_cache)}-{len(tentativas)}')}",
               "--dump-dom", "--virtual-time-budget=240000", f"--force-device-scale-factor={dpr}",
               "--window-size=2000,1200", f"{url}?g={grupo}&dpr={dpr}"]
        if sem_movimento:
            cmd.insert(1, "--force-prefers-reduced-motion")
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=480)
        finally:
            _apagar_perfis()
        achado = re.search(r'<pre id="resultado">(.*?)</pre>', r.stdout, re.S)
        if achado and achado.group(1) != "pendente":
            _cache[chave] = json.loads(html.unescape(achado.group(1)))
        else:
            tentativas.append((r.returncode, r.stdout[-300:], r.stderr[-500:]))
    assert chave in _cache, f"a sonda não terminou: {tentativas}"
    return _cache[chave]


def _inteiro(v, tol=1e-6):
    return abs(v - round(v)) < tol


@pytest.mark.parametrize("dpr", [1, 1.5, 2])
def test_camera_pura_inteira_e_sem_borda(servidor, dpr):
    """calcularCamera: em repouso, escala inteira em px do aparelho, translate no grid do aparelho e sobra de 3σ."""
    casos = [c for c in _sondar(servidor, dpr, False)["puro"]]
    assert len(casos) == 3 * 3 * 14 * 2
    for c in casos:
        rotulo = (c["vw"], c["vh"], c["dpr"], c["id"], c["lado"])
        assert _inteiro(c["bd"]) and c["bd"] >= 1, rotulo
        assert _inteiro(c["z"]) and c["z"] >= 1, rotulo
        assert _inteiro(c["escala"] * c["dpr"]), rotulo  # bd·z pixels do aparelho por pixel do mapa
        assert _inteiro(c["tx"] * c["dpr"]) and _inteiro(c["ty"] * c["dpr"]), rotulo
        assert c["margem"] >= 3 * BLUR * c["z"] - 1e-9, rotulo
        m = c["margem"]
        assert c["tx"] <= -m + 1e-6 and c["ty"] <= -m + 1e-6, rotulo
        assert c["tx"] + MAPA[0] * c["escala"] >= c["vw"] + m - 1e-6, rotulo
        assert c["ty"] + MAPA[1] * c["escala"] >= c["vh"] + m - 1e-6, rotulo
        if c["vw"] <= 800:  # no celular, 3 vira 2
            assert c["z"] == (2 if round(c["zoomPedido"]) == 3 else round(c["zoomPedido"])), rotulo
        else:
            assert c["z"] == round(c["zoomPedido"]), rotulo


def test_largura_da_tela_em_fator_inteiro(servidor):
    """larguraTela: a maior largura que cabe entre fatores inteiros de px do aparelho e de px CSS, até 480."""
    for c in _sondar(servidor, 1, False)["telas"]:
        livre, dpr, w = c["livre"], c["dpr"], c["w"]
        candidatos = {240 * k / dpr for k in range(1, 20) if 240 * k / dpr <= 480 + 1e-6} | {240, 480}
        cabem = [x for x in candidatos if x <= min(livre, 480) + 1e-6]
        assert any(math.isclose(w, x) for x in candidatos), c
        assert math.isclose(w, max(cabem) if cabem else 240), c


def _confere_repouso(nome, p, dpr):
    """Confere uma página medida em repouso: nitidez, borda, sem rolagem horizontal, pino e placa."""
    assert "erro" not in p, (nome, p)
    assert p["js"], nome
    assert math.isclose(p["dpr"], dpr), nome
    # nitidez: cada pixel do mapa vira um número inteiro de pixels do aparelho
    # (ler o transform devolve só 6 algarismos: -1251.33 no lugar de -1251.3333 é 0,03 px do aparelho a DPR 3, uma perda
    # da leitura, não do desenho; o teste puro, que usa os números inteiros, é exato)
    assert _inteiro(p["b"] * dpr, 0.01) and _inteiro(p["z"]), (nome, p["b"], p["z"])
    assert _inteiro(p["tx"] * dpr, 0.05) and _inteiro(p["ty"] * dpr, 0.05), (nome, p["tx"], p["ty"])
    # fundo: o mapa sobra além de cada borda o bastante para o blur não escurecer
    m = math.ceil(3 * BLUR * p["z"] - 1e-9)
    esq, topo, dir_, base = p["kanto"]
    assert esq <= -m + 0.01 and topo <= -m + 0.01, (nome, p["kanto"], m)
    assert dir_ >= p["w"] + m - 0.01 and base >= p["h"] + m - 0.01, (nome, p["kanto"], m)
    # sem rolagem horizontal (o body não esconde estouro)
    assert p["scrollW"] <= p["clienteW"], (nome, p["scrollW"], p["clienteW"])
    # filtro do mapa ligado ao --blur
    assert p["blurCss"] in (".9px", "0.9px") and "blur(0.9px)" in p["filtro"], (nome, p["filtro"])
    if nome.split("-")[1] not in ("abertura", "fim"):
        assert p["pinoAtivo"] and p["pinoOpaco"] == 1, nome
        x, y = p["pino"]
        assert 0 <= x <= p["w"] and 0 <= y <= p["h"], (nome, p["pino"])
        if p["w"] >= 360:  # abaixo de 360 px a tela do jogo precisa da largura toda: sem sarjeta para o pino
            esq, topo, dir_, base = p["pinoCaixa"]  # o círculo inteiro à vista, sem painel nem placa por cima
            assert esq >= 0 and topo >= 0 and dir_ <= p["w"] and base <= p["h"], (nome, p["pinoCaixa"])
            assert not p["pinoCoberto"], (nome, "o pino ficou atrás do conteúdo")
            assert not p["pinoSobPlaca"], (nome, "a placa cobre o pino")
    if p["w"] > 800:
        assert not p["placaSobrePainel"], (nome, "a placa cobre um painel")


@pytest.mark.parametrize("dpr", [1, 1.5, 2])
def test_pagina_real_em_repouso(servidor, dpr):
    paginas = _sondar(servidor, dpr, False)["paginas"]
    assert set(paginas) == {p[0] for p in PAGINAS}
    for nome, p in paginas.items():
        _confere_repouso(nome, p, dpr)
    assert paginas["m-familia"]["detalhesAbertos"] == [True]  # ?cap= de cartão da Família abre o spoiler
    assert paginas["d-celadon"]["detalhesAbertos"] == [False]
    assert paginas["d-abertura"]["escrevendo"] and paginas["d-abertura"]["animPino"] == "pulso"


@pytest.mark.parametrize("largura,altura,dpr", DISPOSITIVOS)
def test_pino_a_vista_nos_celulares(servidor, largura, altura, dpr):
    """360×800, 390×844 (DPR 2), 393×852 (DPR 2) e 430×932 (DPR 3): o pino aparece inteiro nos 13 lugares."""
    paginas = _sondar(servidor, dpr, False, "celulares")["paginas"]
    esperadas = {n for n, w, h, _ in _paginas_dos_grupos()["celulares"][dpr] if (w, h) == (largura, altura)}
    assert len(esperadas) == 13
    for nome in esperadas:
        _confere_repouso(nome, paginas[nome], dpr)
        assert paginas[nome]["pinoAtivo"], nome
    assert paginas[f"{largura}x{altura}-familia"]["detalhesAbertos"] == [True]
    assert paginas[f"{largura}x{altura}-pos_liga"]["pinoCoberto"] is False
    assert paginas[f"{largura}x{altura}-pos_liga"]["pino"][0] < 56  # Planalto Índigo, a oeste: sarjeta da esquerda


@pytest.mark.parametrize("dpr", [1, 2])
def test_pino_a_vista_de_600_a_800(servidor, dpr):
    """De 600 a 800 px de largura, nos 13 lugares (inclusive Planalto Índigo e Rota 23): pino à vista."""
    paginas = _sondar(servidor, dpr, False, "faixa")["paginas"]
    assert len(paginas) == len(FAIXA) * 13
    for nome, p in paginas.items():
        _confere_repouso(nome, p, dpr)
    for w, h in FAIXA:
        for lugar in ("pos_liga", "familia"):
            assert not paginas[f"{w}x{h}-{lugar}"]["pinoCoberto"], (w, lugar)


def test_placa_fora_do_painel_de_801_a_1100(servidor):
    """De 801 a 1100 px a placa do lugar não cruza o painel e o pino fica à vista, nos 13 lugares e no cartão Haunter."""
    paginas = _sondar(servidor, 1, False, "medio")["paginas"]
    assert len(paginas) == len(MEDIO) * 14
    for nome, p in paginas.items():
        assert p["w"] > 800 and not p["placaSobrePainel"], (nome, "a placa cruza um painel")
        _confere_repouso(nome, p, 1)


def test_sprites_em_fator_inteiro_do_aparelho(servidor):
    """fatorSprite: 3× (2× no celular) ou o fator inteiro de pixels do aparelho mais perto disso."""
    for c in _sondar(servidor, 1, False)["sprites"]:
        base = 2 if c["estreita"] else 3
        assert _inteiro(c["k"] * c["dpr"]), c  # cada pixel do sprite vira um número inteiro de pixels do aparelho
        assert abs(c["k"] - base) <= 0.5 / c["dpr"] + 1e-9, c


def test_pagina_sem_movimento(servidor):
    """Com prefers-reduced-motion: fala inteira de uma vez, câmera sem transição e pino sem pulsar."""
    paginas = _sondar(servidor, 1, True)["paginas"]
    for nome, p in paginas.items():
        assert "erro" not in p, (nome, p)
        assert not p["escrevendo"], nome
        assert p["animPino"] == "none", nome
        assert p["transCamada"] in ("0s", "0s, 0s"), (nome, p["transCamada"])

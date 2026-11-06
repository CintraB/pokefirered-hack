"""Galeria de textos (POK-29): cada fala do campo na caixa de mensagem real, página por página.

Não aprova nem reprova: é a conferência visual da tradução (quebra de linha, rolagem `\\l`, páginas
`\\p`, acentos e o pior caso dos placeholders). A checagem de texto (`check_text.py`) já mede a
largura; a galeria mostra como fica.

O que entra: todo rótulo com `.string` dos arquivos que vão para a caixa de diálogo do campo
(GALLERY_SOURCES: os mesmos que `check_text.WIDTH_RULES` mede como diálogo de 2 linhas, menos o
`save.inc` e o evento misterioso). Textos de menus/telas em C ficam de fora.

Como: na ROM de teste, o atalho SHOW_FIELD_TEXT (include/test_hooks.h, 0x110) põe o pior caso nos
buffers ({PLAYER}/{RIVAL} com 7 letras, {STR_VAR_1..3} com 10, todas o glifo mais largo da fonte
normal) e roda `lockall` + `msgbox <texto>, MSGBOX_DEFAULT` + `releaseall`. A galeria espera cada
parada do texto (fim de página `\\p`, rolagem `\\l`, {PAUSE_UNTIL_PRESS} e o `waitbuttonpress`
final), fotografa e aperta A. A sessão parte de uma cópia do `captura.sav` e nunca salva o jogo.

Uso, a partir de test/ (ou `make test-galeria [FILTRO=PalletTown*]` na raiz):
    python3 -m esteira galeria --rom-test RT --elf-test ET --out OUT [--filtro GLOB] [--save S]
Saída: OUT/galeria/index.html (um bloco por arquivo/mapa) e OUT/galeria/img/.
`--filtro` casa com o nome do grupo (pasta do mapa, ou o nome do arquivo sem extensão) ou com o
caminho do arquivo; vírgula separa vários. ESTEIRA_JOBS sessões em paralelo (grupos repartidos).
"""

from __future__ import annotations

import fnmatch
import glob
import html
import json
import shutil
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path

from . import check_text, paralelo
from .result import Result

REPO = Path(__file__).resolve().parents[2]
GALLERY_SOURCES = ("data/maps/*/text.inc",
                   *(f"data/text/{name}.inc" for name in (*check_text._DIALOG_INC, "pokedex_rating")),
                   "data/scripts/*.inc",
                   "data/event_scripts.s")
NAME_LETTERS = check_text.PLAYER_NAME_CHARS     # {PLAYER}/{RIVAL}: o C usa PLAYER_NAME_LENGTH
VAR_LETTERS = 10                                # {STR_VAR_n}: FIELD_TEXT_VAR_GLYPHS em src/test_hooks.c
GALLERY_DIR = "galeria"
SAVE_NAME = "captura.sav"

# --- memória (include/text.h, include/script.h) -----------------------------------------------
TEXT_PRINTER_SIZE = 0x24
PRINTER_ACTIVE, PRINTER_STATE = 0x1B, 0x1C      # game.py: TEXT_PRINTER_ACTIVE / TEXT_PRINTER_STATE
RENDER_STATE_WAIT, RENDER_STATE_CLEAR, RENDER_STATE_SCROLL_START = 1, 2, 3   # enum em include/text.h
WAIT_STATES = (RENDER_STATE_WAIT, RENDER_STATE_CLEAR, RENDER_STATE_SCROLL_START)
SCRIPT_MODE_NATIVE = 2                          # src/script.c
CTX_MODE, CTX_NATIVE = 1, 4                     # struct ScriptContext: stackDepth, mode, comparisonResult, nativePtr

# --- ritmo -------------------------------------------------------------------------------------
POLL = 2                    # quadros entre leituras
SHOT_DELAY = 8              # quadros depois da parada: a janela já está na VRAM e a seta de "continua" aparece
TEXT_LIMIT = 6000           # quadros por texto; passou, vira aviso e a sessão volta ao estado-base
PRESS_RETRY = 40            # quadros esperando a parada sumir depois do A antes de apertar de novo
IDLE_TIMEOUT = 600
POPUP_TASK = "Task_MapNamePopup"   # o aviso do nome do mapa rola o BG0 inteiro (a caixa junto): espera sumir
POPUP_TIMEOUT = 1200


@dataclass
class GalleryText:
    file: str               # caminho relativo ao repo
    group: str              # pasta do mapa, ou o nome do arquivo sem extensão
    label: str
    source: str             # texto cru, como no .inc


def group_of(rel: str) -> str:
    parts = Path(rel).parts
    if len(parts) >= 3 and parts[:2] == ("data", "maps"):
        return parts[2]
    return Path(rel).stem


def list_texts(repo: Path = REPO) -> list[GalleryText]:
    """Rótulos com `.string` dos arquivos da caixa de diálogo, na ordem dos arquivos (o 1º de cada rótulo)."""
    texts: list[GalleryText] = []
    seen: set[str] = set()
    for pattern in GALLERY_SOURCES:
        for path in sorted(glob.glob(str(repo / pattern))):
            rel = Path(path).relative_to(repo).as_posix()
            source = Path(path).read_text(encoding="utf-8")
            for entry in check_text._extract_inc_text(rel, source):
                if isinstance(entry, Result) or entry.braille or entry.label.startswith("linha ") \
                        or entry.label == "?" or entry.label in seen:
                    continue
                seen.add(entry.label)
                texts.append(GalleryText(rel, group_of(rel), entry.label, entry.texts[0]))
    return texts


def select(texts: list[GalleryText], pattern: str | None) -> list[GalleryText]:
    """Filtro por glob (vírgula separa vários) no grupo ou no caminho do arquivo."""
    if not pattern:
        return texts
    pats = [p.strip() for p in pattern.split(",") if p.strip()]
    return [t for t in texts if any(fnmatch.fnmatchcase(t.group, p) or fnmatch.fnmatchcase(t.file, p)
                                    for p in pats)]


def worst_glyph(repo: Path = REPO) -> str:
    """A letra/algarismo ASCII mais larga da fonte normal (empate: maiúscula, depois minúscula, depois algarismo)."""
    env = check_text._load_env(repo)
    widths = env.widths["normal"]
    best = env.max_letter["normal"]
    ties = [ch for ch, w in widths.items() if ch.isascii() and ch.isalnum() and w == best]
    return min(ties, key=lambda ch: (not ch.isupper(), not ch.isalpha(), ch))


def _slug(label: str) -> str:
    return "".join(c if c.isalnum() or c in "_-" else "_" for c in label)


# --- sessão no emulador ------------------------------------------------------------------------

_STOPS = ("\\p", "\\l", "{PAUSE_UNTIL_PRESS}")


def expected_pages(source: str) -> int:
    """Paradas esperando A: cada `\\p`, `\\l` e {PAUSE_UNTIL_PRESS} e o `waitbuttonpress` do fim."""
    return sum(source.count(stop) for stop in _STOPS) + 1


class GallerySession:
    """Uma sessão da ROM de teste já no campo (`ctx` aberto, CONTINUAR feito): mostra textos e fotografa as páginas."""

    def __init__(self, ctx, gallery: Path, glyph: str):
        from .hooks import Mailbox
        self.ctx, self.emu, self.game, self.ctl = ctx, ctx.emu, ctx.game, ctx.controller
        self.gallery = gallery
        self.box = Mailbox(ctx.controller)
        self.box.conq_silencio(True)
        syms = self.game.syms
        self.printer = syms.addr("sTextPrinters")
        self.script_ctx = syms.addr("sGlobalScriptContext")
        self.wait_press = syms.addr("WaitForAorBPress") & ~1
        self.glyph = self.game.charmap.encode(glyph)[0]
        self.base_state = str(Path(ctx.out_dir) / "galeria_base.ss")
        self.ctl.wait_overworld_idle(IDLE_TIMEOUT)
        self.ctl.wait_until(lambda: POPUP_TASK not in self.game.active_tasks(), POPUP_TIMEOUT,
                            "aviso do nome do mapa sumir")
        self.emu.save_state(self.base_state)

    def _stop(self) -> tuple[str, int] | None:
        """Parada esperando A: ("pagina", ponteiro do texto) ou ("fim", 0); None = escrevendo/fechando."""
        raw = self.emu.read(self.printer, TEXT_PRINTER_SIZE)
        if raw[PRINTER_ACTIVE] and raw[PRINTER_STATE] in WAIT_STATES:
            return "pagina", int.from_bytes(raw[0:4], "little")
        if not raw[PRINTER_ACTIVE]:
            head = self.emu.read(self.script_ctx, 8)
            native = int.from_bytes(head[CTX_NATIVE:CTX_NATIVE + 4], "little") & ~1
            if head[CTX_MODE] == SCRIPT_MODE_NATIVE and native == self.wait_press:
                return "fim", 0
        return None

    def _show(self, text: dict, shot: dict) -> None:
        from .emu import KEY_A
        emu = self.emu
        self.ctl.wait_overworld_idle(IDLE_TIMEOUT)
        self.box.show_field_text(text["address"], self.glyph)
        folder = self.gallery / "img" / _slug(text["group"])
        folder.mkdir(parents=True, exist_ok=True)
        spent, last = 0, None
        while True:
            if spent >= TEXT_LIMIT:
                raise TimeoutError(f"não terminou em {TEXT_LIMIT} quadros ({len(shot['pages'])} página(s))")
            now = self._stop()
            if now is None:
                if last == ("fim", 0) and not self.ctl.script_active():
                    break
                emu.frames(POLL)
                spent += POLL
                continue
            if now == last:     # o A ainda não foi lido: aperta de novo, sem foto nova
                retry = 0
                while self._stop() == now and retry < PRESS_RETRY:
                    emu.frames(POLL)
                    retry += POLL
                spent += retry
                if self._stop() == now:
                    emu.press(KEY_A, hold=2, release=2)
                    spent += 4
                continue
            emu.frames(SHOT_DELAY)
            spent += SHOT_DELAY
            name = f"{_slug(text['label'])}_{len(shot['pages']) + 1}.png"
            emu.screenshot(str(folder / name))
            shot["pages"].append(f"img/{_slug(text['group'])}/{name}")
            emu.press(KEY_A, hold=2, release=2)
            spent += 4
            last = now
        shot["frames"] = spent

    def show(self, text: dict) -> dict:
        """Mostra um texto ({..., "address"}); devolve o registro com as páginas. Texto que não termina (ou um passo que
        estoura) vira `aviso` e a sessão volta ao estado-base; número de páginas diferente do esperado também é aviso."""
        from .emu import EmulatorError
        shot = dict(text, pages=[], status="ok", detail="", frames=0)
        try:
            self._show(text, shot)
        except EmulatorError:
            raise
        except Exception as exc:   # noqa: BLE001 — qualquer travada vira aviso e a galeria segue
            shot.update(status="aviso", detail=f"{type(exc).__name__}: {exc}", frames=TEXT_LIMIT)
            self.emu.load_state(self.base_state)
            return shot
        want = expected_pages(text["source"])
        if len(shot["pages"]) != want:
            shot.update(status="aviso", detail=f"{len(shot['pages'])} página(s), esperava {want} "
                                               "(\\p, \\l e {PAUSE_UNTIL_PRESS} + o fim)")
        return shot


def _session(job: dict) -> list[dict]:
    """Processo de trabalho: uma sessão da ROM de teste que mostra `job["texts"]` em ordem."""
    from .scenarios import open_context
    from .scenarios.quick_catch_save import CatchSaveScenario

    gallery = Path(job["gallery"])
    work = gallery / "sessoes" / f"s{job['index']}"
    with open_context(job["rom"], job["elf"], str(work), "SQUIRTLE", save_from=job["save"]) as ctx:
        CatchSaveScenario(ctx)._title_to_continue("tela de título da build de teste", shot="galeria_continue")
        session = GallerySession(ctx, gallery, job["glyph"])
        return [session.show(text) for text in job["texts"]]


def _partition(items: list[dict], n: int) -> list[list[dict]]:
    """Reparte os textos em `n` fatias contíguas de tamanho parecido (grupos inteiros quando dá)."""
    n = max(1, min(n, len(items)))
    size = -(-len(items) // n)
    return [items[i:i + size] for i in range(0, len(items), size)]


# --- índice --------------------------------------------------------------------------------------

_CSS = """
:root{--bg:#f6f5f2;--fg:#1d1d1f;--muted:#6b6b70;--card:#fff;--line:#deddd8;--warn:#b25b00}
@media (prefers-color-scheme:dark){:root{--bg:#18181a;--fg:#ececee;--muted:#9a9aa0;--card:#232326;
--line:#38383c;--warn:#ffae57}}
body{background:var(--bg);color:var(--fg);font:15px/1.45 system-ui,sans-serif;margin:0;padding:16px}
h1{font-size:1.4rem;margin:.2rem 0 .4rem}h2{font-size:1.1rem;margin:2rem 0 .6rem;border-bottom:1px solid var(--line)}
.meta,.src,.det{color:var(--muted)}nav{columns:14rem;font-size:.85rem;margin:1rem 0}nav a{display:block}
.t{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px 12px;margin:10px 0}
.t b{font-family:ui-monospace,monospace;font-size:.9rem}.src{font-family:ui-monospace,monospace;font-size:.8rem;
white-space:pre-wrap;word-break:break-word;margin:.3rem 0}.pg{display:flex;flex-wrap:wrap;gap:8px}
.pg figure{margin:0}.pg img{width:480px;max-width:100%;image-rendering:pixelated;display:block;border-radius:4px}
.pg figcaption{font-size:.75rem;color:var(--muted)}.aviso b,.aviso .det{color:var(--warn)}
"""


def write_index(gallery: Path, shots: list[dict], meta: dict) -> Path:
    groups: dict[str, list[dict]] = {}
    for s in shots:
        groups.setdefault(f"{s['group']}|{s['file']}", []).append(s)
    warn = sum(1 for s in shots if s["status"] != "ok")
    pages = sum(len(s["pages"]) for s in shots)
    out = ["<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'>",
           "<meta name='viewport' content='width=device-width,initial-scale=1'>",
           f"<title>Galeria de textos</title><style>{_CSS}</style></head><body>",
           "<h1>Galeria de textos</h1>",
           f"<p class='meta'>{len(shots)} textos, {pages} páginas, {warn} aviso(s) · filtro "
           f"{html.escape(meta.get('filtro') or 'nenhum')} · pior caso: {{PLAYER}}/{{RIVAL}} = "
           f"{NAME_LETTERS}×{html.escape(meta['glifo'])}, {{STR_VAR_n}} = {VAR_LETTERS}×"
           f"{html.escape(meta['glifo'])} · {html.escape(meta['data'])} · {meta['segundos']:.0f} s</p><nav>"]
    for key in groups:
        group, file = key.split("|", 1)
        out.append(f"<a href='#{_slug(key)}'>{html.escape(group)}</a>")
    out.append("</nav>")
    for key, items in groups.items():
        group, file = key.split("|", 1)
        out.append(f"<h2 id='{_slug(key)}'>{html.escape(group)} <span class='meta'>{html.escape(file)}</span></h2>")
        for s in items:
            cls = "t" if s["status"] == "ok" else "t aviso"
            out.append(f"<div class='{cls}'><b>{html.escape(s['label'])}</b>")
            if s["detail"]:
                out.append(f" <span class='det'>{html.escape(s['status'])}: {html.escape(s['detail'])}</span>")
            out.append(f"<div class='src'>{html.escape(s['source'])}</div><div class='pg'>")
            for i, page in enumerate(s["pages"], 1):
                out.append(f"<figure><img loading='lazy' src='{html.escape(page)}' alt='página {i}'>"
                           f"<figcaption>{i}/{len(s['pages'])}</figcaption></figure>")
            out.append("</div></div>")
    out.append("</body></html>")
    path = gallery / "index.html"
    path.write_text("\n".join(out), encoding="utf-8")
    return path


# --- comando --------------------------------------------------------------------------------------

def find_save(out: Path, explicit: str | None) -> Path | None:
    """--save; senão OUT/captura.sav; senão o captura.sav mais novo de test/out/*/."""
    if explicit:
        return Path(explicit)
    if (out / SAVE_NAME).exists():
        return out / SAVE_NAME
    found = sorted(glob.glob(str(REPO / "test" / "out" / "*" / SAVE_NAME)), key=lambda p: Path(p).stat().st_mtime)
    return Path(found[-1]) if found else None


def run_gallery(rom: str, elf: str, out_dir: str, pattern: str | None = None, save: str | None = None,
                jobs: int | None = None, limit: int | None = None) -> int:
    from .symbols import Symbols

    out = Path(out_dir)
    gallery = out / GALLERY_DIR
    save_path = find_save(out, save)
    if save_path is None or not save_path.exists():
        print(f"sem {SAVE_NAME}: rode `python3 -m esteira rapido ... --out {out}` antes ou passe --save")
        return 2
    texts = select(list_texts(), pattern)
    if limit:
        texts = texts[:limit]
    if not texts:
        print(f"nenhum texto casa com o filtro {pattern!r}")
        return 2
    if gallery.exists():
        shutil.rmtree(gallery)
    gallery.mkdir(parents=True)
    syms = Symbols.from_elf(elf)
    items, missing = [], []
    for t in texts:
        addrs = syms.addrs(t.label)
        item = asdict(t)
        if len(addrs) != 1:
            missing.append(dict(item, pages=[], status="sem_endereco", frames=0,
                                detail=f"{len(addrs)} endereço(s) no ELF"))
            continue
        items.append(dict(item, address=addrs[0]))
    glyph = worst_glyph()
    n = jobs or paralelo.jobs()
    chunks = _partition(items, n)
    common = {"rom": rom, "elf": elf, "gallery": str(gallery), "save": str(save_path), "glyph": glyph}
    print(f"galeria: {len(items)} textos em {len(chunks)} sessão(ões), pior caso com '{glyph}'"
          + (f"; {len(missing)} sem endereço" if missing else ""), flush=True)
    t0 = time.monotonic()
    jobs_list = [dict(common, index=i, texts=chunk) for i, chunk in enumerate(chunks)]
    if len(jobs_list) == 1:
        results = [_session(jobs_list[0])]
    else:
        with ProcessPoolExecutor(max_workers=len(jobs_list)) as pool:
            results = list(pool.map(_session, jobs_list))
    seconds = time.monotonic() - t0
    order = {t.label: i for i, t in enumerate(texts)}
    shots = sorted([s for r in results for s in r] + missing, key=lambda s: order[s["label"]])
    meta = {"filtro": pattern, "glifo": glyph, "data": time.strftime("%Y-%m-%d %H:%M"), "segundos": seconds,
            "textos": len(shots), "sessoes": len(chunks)}
    (gallery / "galeria.json").write_text(json.dumps({"meta": meta, "textos": shots}, ensure_ascii=False, indent=1)
                                          + "\n", encoding="utf-8")
    index = write_index(gallery, shots, meta)
    shutil.rmtree(gallery / "sessoes", ignore_errors=True)
    warn = [s for s in shots if s["status"] != "ok"]
    for s in warn:
        print(f"[{s['status']}] {s['file']} {s['label']}: {s['detail']}")
    per = seconds / max(1, len(items)) * len(chunks)
    print(f"galeria: {len(shots)} textos, {sum(len(s['pages']) for s in shots)} páginas, {len(warn)} aviso(s), "
          f"{seconds:.1f} s ({per:.2f} s por texto por sessão); índice: {index}")
    return 0

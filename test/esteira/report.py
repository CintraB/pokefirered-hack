"""Relatório HTML autocontido da esteira (uma página, imagens em `img/` ao lado)."""

import html
import shutil
from pathlib import Path

from esteira.result import Result, Suite

_ORDER = {"falha": 0, "aviso": 1, "ok": 2}
_LABEL = {"falha": "FALHA", "aviso": "AVISO", "ok": "OK"}

_CSS = """
body{font-family:Segoe UI,Arial,sans-serif;margin:0;background:#f4f4f6;color:#222}
main{max-width:1000px;margin:0 auto;padding:16px}
.faixa{background:#b00020;color:#fff;font-weight:bold;font-size:1.4em;text-align:center;padding:14px}
.meta{background:#fff;border-radius:6px;padding:10px 16px;margin-bottom:16px}
.meta span{margin-right:18px;white-space:nowrap}
.resumo{font-size:1.1em;margin:8px 0 16px}
.r{background:#fff;border-left:6px solid #999;border-radius:4px;margin:8px 0;padding:8px 12px}
.r.falha{border-color:#b00020}.r.aviso{border-color:#e69500}.r.ok{border-color:#2e7d32}
.tag{font-weight:bold;margin-right:8px}
.falha .tag{color:#b00020}.aviso .tag{color:#b36b00}.ok .tag{color:#2e7d32}
.det{white-space:pre-wrap;font-family:Consolas,monospace;font-size:.9em;margin:4px 0}
.ev{font-size:.85em;color:#555}
.imgs img{image-rendering:pixelated;width:240px;margin:4px 6px 0 0;border:1px solid #bbb}
table{border-collapse:collapse}td,th{padding:2px 12px;text-align:left}
"""


def _fmt_seconds(seconds: float) -> str:
    return f"{seconds:.1f} s"


def _copy_images(suite: Suite, out: Path) -> dict[str, str]:
    """Copia cada imagem referenciada para out/img/ e devolve {caminho original: 'img/nome'}."""
    mapping: dict[str, str] = {}
    img_dir = out / "img"
    if img_dir.is_dir():
        shutil.rmtree(img_dir)   # imagens de um relatório anterior na mesma pasta
    for result in suite.results:
        for src in result.images:
            if src in mapping or not Path(src).is_file():
                continue
            img_dir.mkdir(parents=True, exist_ok=True)
            name = f"{len(mapping) + 1:03d}-{Path(src).name}"
            shutil.copyfile(src, img_dir / name)
            mapping[src] = f"img/{name}"
    return mapping


def _result_html(result: Result, mapping: dict[str, str]) -> str:
    esc = html.escape
    parts = [f'<div class="r {result.status}"><span class="tag">{_LABEL[result.status]}</span>'
             f"<b>{esc(result.name)}</b>"]
    if result.detail:
        parts.append(f'<div class="det">{esc(result.detail)}</div>')
    if result.state:
        parts.append(f'<div class="ev">estado salvo para depuração: {esc(result.state)}</div>')
    shown = [mapping[p] for p in result.images if p in mapping]
    if shown:
        imgs = "".join(f'<a href="{esc(p)}"><img src="{esc(p)}" alt="{esc(Path(p).name)}"></a>'
                       for p in shown)
        parts.append(f'<div class="imgs">{imgs}</div>')
    parts.append("</div>")
    return "".join(parts)


def write_report(suite: Suite, out_dir: str, meta: dict) -> str:
    """Grava `out_dir/relatorio.html` e as imagens em `out_dir/img/`; devolve o caminho do HTML.

    `meta`: inicial, data, commit, tempo_total (s), nao_testada (bool) e, opcional, `tempos`
    ({cenário: segundos}) e `modo`.
    """
    esc = html.escape
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    mapping = _copy_images(suite, out)
    ordered = sorted(suite.results, key=lambda r: _ORDER[r.status])  # estável: ordem de execução

    counts = {s: sum(1 for r in suite.results if r.status == s) for s in _ORDER}
    if meta.get("nao_testada"):
        veredito = "NÃO TESTADA"
    else:
        veredito = "REPROVADA" if counts["falha"] else "aprovada"
    body = []
    if meta.get("nao_testada"):
        body.append('<div class="faixa">ROM NÃO TESTADA</div>')
    body.append("<main>")
    items = [("Inicial", meta.get("inicial", "-")), ("Data", meta.get("data", "-")),
             ("Commit", meta.get("commit", "-")), ("Modo", meta.get("modo", "-")),
             ("Tempo total", _fmt_seconds(meta["tempo_total"]) if "tempo_total" in meta else "-")]
    body.append('<div class="meta">' + "".join(
        f"<span><b>{k}:</b> {esc(str(v))}</span>" for k, v in items))
    tempos = meta.get("tempos")
    if tempos:
        rows = "".join(f"<tr><td>{esc(k)}</td><td>{_fmt_seconds(v)}</td></tr>"
                       for k, v in tempos.items())
        body.append(f"<table>{rows}</table>")
    body.append("</div>")
    body.append(f'<div class="resumo">Esteira {veredito}: {counts["falha"]} falha(s), '
                f'{counts["aviso"]} aviso(s), {counts["ok"]} ok</div>')
    body.extend(_result_html(r, mapping) for r in ordered)
    body.append("</main>")

    title = "Relatório da esteira"
    page = (f'<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8">'
            f"<title>{esc(title)}</title><style>{_CSS}</style></head><body>"
            + "".join(body) + "</body></html>\n")
    path = out / "relatorio.html"
    path.write_text(page, encoding="utf-8")
    return str(path)

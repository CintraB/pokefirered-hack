"""Modo completo: a galeria de textos (POK-29) em poucos textos fixos, na build de teste.

A galeria inteira (`python3 -m esteira galeria`, `make test-galeria`) fica fora do pipeline: é para
olhar. Este cenário só garante que o atalho SHOW_FIELD_TEXT (include/test_hooks.h, 0x110) e a
sessão da galeria (esteira/galeria.py) não apodrecem. Para cada texto de FIXED:

- `galeria/<rótulo>`: a fala abre na caixa do campo, para em cada `\\p`, `\\l` e
  {PAUSE_UNTIL_PRESS} e no fim (uma foto por parada, o número esperado) e o campo fica livre;
  os placeholders saem no pior caso: a fala expandida (gStringVar4) tem o glifo mais largo 7
  vezes no lugar de {PLAYER}/{RIVAL} e 10 no de {STR_VAR_n}.

Fotos e índice em OUT/galeria/ (as da 1ª e da última página vão no relatório). Sessão própria da
ROM de teste a partir do .sav do `captura` (`save_from="captura"`).

Uso, a partir de test/ (a pasta OUT precisa do captura.sav de um `rapido`/`completo`):
    python3 -m esteira completo --rom R --elf E --out OUT --only galeria
"""

import shutil
import sys
from pathlib import Path

from .. import galeria
from . import ScenarioContext
from .base import FIELD_MESSAGE_BYTES, Abort
from .quick_catch_save import CatchSaveScenario

# rótulo -> o que exercita
FIXED = {
    "PalletTown_Text_OakGrassUnsafeNeedMon": "três páginas (\\p)",
    "PalletTown_Text_OakYouEnjoyingTraveling": "rolagem (\\l) e {PLAYER}",
    "PalletTown_ProfessorOaksLab_Text_RivalReceivedMonFromOak": "{RIVAL} e {STR_VAR_1}",
    "VSSeeker_Text_BatteryNotChargedNeedXSteps": "{STR_VAR_1} e {PAUSE_UNTIL_PRESS}",
}


class GalleryScenario(CatchSaveScenario):
    def __init__(self, ctx: ScenarioContext):
        super().__init__(ctx)
        self.gallery = Path(ctx.out_dir) / galeria.GALLERY_DIR
        self.glyph = galeria.worst_glyph()
        self.session: galeria.GallerySession | None = None
        self.records: list[dict] = []

    def _start(self) -> str:
        self._title_to_continue("tela de título da build de teste", shot="galeria_continue")
        shutil.rmtree(self.gallery, ignore_errors=True)   # fotos de uma execução anterior na mesma pasta
        self.session = galeria.GallerySession(self.ctx, self.gallery, self.glyph)
        return f"CONTINUAR; pior caso com '{self.glyph}'"

    def _text(self, text: galeria.GalleryText, what: str) -> str:
        item = dict(vars(text), address=self.game.syms.addr(text.label))
        shot = self.session.show(item)
        self.records.append(shot)
        assert shot["status"] == "ok", shot["detail"]
        assert self.ctl.overworld_idle(), "o campo não ficou livre depois da fala"
        shown = self.game.charmap.decode(self.emu.read(self.game.syms.addr("gStringVar4"), FIELD_MESSAGE_BYTES))
        source = text.source
        for name, letters in (("PLAYER", galeria.NAME_LETTERS), ("RIVAL", galeria.NAME_LETTERS),
                              ("STR_VAR_1", galeria.VAR_LETTERS)):
            if "{" + name + "}" in source:
                assert self.glyph * letters in shown, f"{{{name}}} sem {letters}×{self.glyph}: {shown[:120]!r}"
        return f"{what}: {len(shot['pages'])} parada(s), {shot['frames']} quadros"

    def run(self) -> None:
        try:
            self._flow("galeria/inicio", self._start)
        except Abort:
            return
        texts = {t.label: t for t in galeria.list_texts()}
        for label, what in FIXED.items():
            res = self.suite.run(f"galeria/{label}", lambda t=texts[label], w=what: self._text(t, w))
            if self.records and self.records[-1]["label"] == label and self.records[-1]["pages"]:
                pages = self.records[-1]["pages"]
                res.images.extend(str(self.gallery / p) for p in dict.fromkeys((pages[0], pages[-1])))
        meta = {"filtro": "cenário galeria", "glifo": self.glyph, "data": "-", "segundos": 0.0}
        galeria.write_index(self.gallery, self.records, meta)


def run_full_galeria(ctx: ScenarioContext) -> None:
    GalleryScenario(ctx).run()


if __name__ == "__main__":
    sys.exit("use: python3 -m esteira completo ... --only galeria")

"""Modo completo: breeding genético (Hack 6), estatística na build de teste (TESTBUILD=1).

Ponto de partida: o .sav do fim do modo rápido, numa sessão própria da ROM de teste (como o
`shiny`). Para cada par de pais de esteira/breeding.py (CONFIGS) o atalho monta os dois na
creche de verdade (gSaveBlock1Ptr->daycare) com IVs, natureza, posição da habilidade, golpes e
item dados, e gera milhares de ovos pelo caminho real (ovo pendente + GiveEggFromDaycare, o
mesmo `special` do velho da creche de Four Island). Cada ovo volta como um registro (IVs,
natureza, habilidade, gênero, shiny, golpes de ovo) e é comparado com o modelo exato das regras:

- IVs: qui-quadrado dos 32 valores e média (±4σ) de cada atributo, contra a distribuição
  exata (mutação 5%, um dos pais 25% ±2, média ±3; Destiny Knot; Power items 90%);
- natureza: qui-quadrado das 25 e a frequência da natureza de cada pai (mistura, mutação,
  Everstone 70%, dois Everstones 35%/35%);
- habilidade 60/40 com 10% de mutação, e o pai "sem informação" (Ditto, espécie de uma
  habilidade só); golpes de ovo 60%/40%/76%; gênero sem viés (a proporção natural da espécie,
  condicionada ao bit da habilidade, que no Gen 3 é o mesmo byte);
- o ovo entregue tem exatamente a personalidade que a rotina de sorteio dá (mesmo estado do
  RNG), e a taxa de shiny dessa rotina com e sem Shiny Charm (400 000 sorteios cada, ±3σ, como
  o `shiny`): ~1/4096 e ~1/2048;
- Power items em batalha: +8 EVs no atributo do item por Pokémon derrotado, com os limites
  255/510 (MonGainEVs de verdade), e Velocidade pela metade na ordem dos turnos
  (GetWhoStrikesFirst de verdade); Destiny Knot e Everstone não mexem na Velocidade.

Modo paralelo (ESTEIRA_JOBS > 1, esteira/paralelo.py): BREEDING_PARTS sessões ao mesmo tempo,
cada uma com o RNG semeado por parte, geram a sua fatia dos ovos de cada par e das duas taxas
de shiny; `merge_breeding` junta os ovos e roda as MESMAS checagens (BreedingStats) sobre o
total. Personalidade, EVs e Velocidade (não estatísticos) só na parte 0.

Uso, a partir de test/ (a pasta OUT precisa do captura.sav de um `rapido`/`completo`):
    python3 -m esteira completo --rom R --elf E --out OUT --only creche
"""

import struct
import sys
import time

from ..breeding import (BATCH, CONFIGS, EGG_PERSONALITY_TRIALS, EGG_SHINY_SAMPLES, NATURES,
                        PARENT_FORMAT, PROBES_FORMAT, POWER_ITEMS, RECORD_SIZE, SHINY_SIGMAS, SPEC,
                        STATS, Z_SIGMAS, CHI2_MIN_P, Config, Parent, Record, ability_one_probability,
                        chi_square, egg_move_probability, egg_moves, female_probability,
                        header_defines, iv_distribution, mean_and_std, nature_distribution,
                        proportion_interval, species_info, unpack_records, z_score)
from ..paralelo import part_data, part_label, seed_label, seed_rng, share
from ..result import Result, Suite
from ..hooks import (CMD_BREED_EGGS, CMD_BREED_SETUP, CMD_EGG_PERSONALITY, CMD_EGG_SHINIES,
                     CMD_GAIN_EVS, CMD_SPEED_ORDER, Mailbox)
from . import REPO_ROOT, ScenarioContext
from .base import Abort
from .full_shiny import ATTEMPTS_NO_CHARM, ATTEMPTS_WITH_CHARM, shiny_interval, shiny_probability
from .quick_catch_save import CatchSaveScenario

GENDER_CODE = {"M": 0x00, "F": 0xFE, "-": 0xFF}
FRAMES_PER_EGG_LIMIT = 60          # teto do atalho por ovo (medido bem abaixo; ver relatório)
FRAMES_PER_SHINY_LIMIT = 4
SHINY_POLL = 60


def _fmt(x: float, digits: int = 1) -> str:
    return f"{x:.{digits}f}".replace(".", ",")


def _pct(x: float) -> str:
    return _fmt(100 * x) + "%"


def expected_evs(evs: list[int], yields: tuple[int, ...], power_stat: int | None) -> list[int]:
    """MonGainEVs (src/pokemon.c) em Python: rendimento da espécie derrotada + POWER_ITEM_EV_BONUS
    no atributo do Power item, com os limites 510 no total e 255 por atributo."""
    evs = list(evs)
    total = sum(evs)
    for i in range(6):
        if total >= 510:
            break
        inc = yields[i] + (SPEC["POWER_ITEM_EV_BONUS"] if power_stat == i else 0)
        inc = min(inc, 510 - total, 255 - evs[i])
        evs[i] += inc
        total += inc
    return evs


class BreedingStats:
    """As checagens estatísticas de uma configuração sobre os ovos já gerados
    (`records[config.name]`): não usam o emulador, então o modo paralelo as roda no
    processo principal sobre os ovos de todas as partes juntos (merge_breeding)."""

    records: dict[str, list[Record]]

    def _ivs(self, config: Config) -> str:
        recs = self.records[config.name]
        f, m = config.father, config.mother
        knot = "ITEM_DESTINY_KNOT" in (f.item, m.item)
        groups: dict[tuple, list[int]] = {}
        for stat in range(6):
            fp = POWER_ITEMS.get(f.item) == stat
            mp = POWER_ITEMS.get(m.item) == stat
            groups.setdefault((f.ivs[stat], m.ivs[stat], knot, fp, mp), []).append(stat)
        parts, bad = [], []
        for (fi, mi, kn, fp, mp), stats in groups.items():
            dist = iv_distribution(fi, mi, kn, fp, mp)
            values = [r.ivs[s] for r in recs for s in stats]
            n = len(values)
            counts = [values.count(v) for v in range(32)]
            chi, dof, p = chi_square(counts, dist)
            mu, sd = mean_and_std(dist)
            mean = sum(values) / n
            obs_sd = (sum((v - mean) ** 2 for v in values) / n) ** 0.5
            z = (mean - mu) / (sd / n ** 0.5)
            label = "/".join(STATS[s] for s in stats)
            extra = ""
            if fp or mp:
                target = [x for x, on in ((fi, fp), (mi, mp)) if on]
                hits = sum(1 for v in values if v in target)
                pz = sum(dist[t] for t in set(target))
                zc = z_score(hits, n, pz)
                extra = f", cópia exata {_pct(hits / n)} (modelo {_pct(pz)})"
                if abs(zc) > Z_SIGMAS:
                    bad.append(f"{label}: cópia exata z={_fmt(zc, 2)}")
            parts.append(f"{label} (pais {fi}/{mi}{', knot' if kn else ''}"
                         f"{', power pai' if fp else ''}{', power mãe' if mp else ''}): média "
                         f"{_fmt(mean, 2)} (modelo {_fmt(mu, 2)}), dp {_fmt(obs_sd, 2)} "
                         f"({_fmt(sd, 2)}), χ²={_fmt(chi)} gl={dof} p={p:.3g}{extra}")
            if p < CHI2_MIN_P:
                bad.append(f"{label}: χ² p={p:.3g}")
            if abs(z) > Z_SIGMAS:
                bad.append(f"{label}: média z={_fmt(z, 2)}")
        detail = "; ".join(parts)
        assert not bad, f"{', '.join(bad)} | {detail}"
        return detail

    def _nature(self, config: Config) -> str:
        recs = self.records[config.name]
        f, m = config.father, config.mother
        dist = nature_distribution(f.nature, m.nature, f.item == "ITEM_EVERSTONE",
                                   m.item == "ITEM_EVERSTONE")
        n = len(recs)
        counts = [0] * 25
        for r in recs:
            counts[r.nature] += 1
        chi, dof, p = chi_square(counts, dist)
        bad, parts = [], []
        for who, nat in (("do pai", f.nature), ("da mãe", m.nature)):
            z = z_score(counts[nat], n, dist[nat])
            parts.append(f"igual à {who} ({NATURES[nat]}) {_pct(counts[nat] / n)} "
                         f"(modelo {_pct(dist[nat])})")
            if abs(z) > Z_SIGMAS:
                bad.append(f"natureza {who}: z={_fmt(z, 2)}")
        neutral = sum(counts[k * 6] for k in range(5))
        parts.append(f"neutras {_pct(neutral / n)} (modelo {_pct(sum(dist[k * 6] for k in range(5)))})")
        if p < CHI2_MIN_P:
            bad.append(f"χ² p={p:.3g}")
        detail = "; ".join(parts) + f"; χ² das 25 = {_fmt(chi)} gl={dof} p={p:.3g}"
        assert not bad, f"{', '.join(bad)} | {detail}"
        return detail

    def _info(self, parent: Parent):
        return species_info(REPO_ROOT, parent.species)

    def _ability(self, config: Config) -> str:
        recs = self.records[config.name]
        f, m = config.father, config.mother
        fslot = f.ability if self._info(f).two_abilities else None
        mslot = m.ability if self._info(m).two_abilities else None
        p1 = ability_one_probability(species_info(REPO_ROOT, config.child).two_abilities,
                                     fslot, mslot)
        assert p1 is not None, "configuração sem habilidade dupla no filhote"
        n, ones = len(recs), sum(r.ability for r in recs)
        z = z_score(ones, n, p1)
        lo, hi = proportion_interval(n, p1)
        who = (f"pai posição {fslot if fslot is not None else 'sem informação'}, mãe posição "
               f"{mslot if mslot is not None else 'sem informação'}")
        detail = (f"{who}: posição 1 em {ones}/{n} = {_pct(ones / n)} (modelo {_pct(p1)}, faixa "
                  f"±{_fmt(Z_SIGMAS, 0)}σ {_fmt(lo)}..{_fmt(hi)})")
        assert abs(z) <= Z_SIGMAS, f"fora da faixa: {detail}"
        return detail

    def _egg_moves(self, config: Config) -> str:
        recs = self.records[config.name]
        allowed = set(egg_moves(REPO_ROOT, config.child))
        parts, bad = [], []
        for i, move in enumerate(config.probes):
            fk, mk = move in config.father.moves, move in config.mother.moves
            p = egg_move_probability(fk, mk) if move in allowed else 0.0
            hits = sum(r.probes[i] for r in recs)
            z = z_score(hits, len(recs), p)
            who = "pai e mãe" if fk and mk else "pai" if fk else "mãe"
            parts.append(f"{move.removeprefix('MOVE_')} (só {who}" if not (fk and mk)
                         else f"{move.removeprefix('MOVE_')} ({who}")
            parts[-1] += f") {_pct(hits / len(recs))} (modelo {_pct(p)})"
            if abs(z) > Z_SIGMAS:
                bad.append(f"{move}: z={_fmt(z, 2)}")
        detail = "; ".join(parts)
        assert not bad, f"{', '.join(bad)} | {detail}"
        return detail

    def _gender(self, config: Config) -> str:
        recs = self.records[config.name]
        info = species_info(REPO_ROOT, config.child)
        if info.gender_ratio in (0x00, 0xFE, 0xFF):
            want = {0x00: "M", 0xFE: "F", 0xFF: "-"}[info.gender_ratio]
            wrong = sum(r.gender != want for r in recs)
            assert wrong == 0, f"{wrong} ovo(s) com gênero diferente de {want!r}"
            return f"todos os {len(recs)} com o gênero fixo da espécie ({want!r})"
        probs = [female_probability(info.gender_ratio, r.ability if info.two_abilities else None)
                 for r in recs]
        females = sum(r.gender == "F" for r in recs)
        mean = sum(probs)
        sigma = sum(p * (1 - p) for p in probs) ** 0.5
        z = (females - mean) / sigma
        detail = (f"{females} fêmeas em {len(recs)} = {_pct(females / len(recs))} (natural da espécie "
                  f"{_pct(mean / len(recs))}, z={_fmt(z, 2)})")
        assert abs(z) <= Z_SIGMAS, f"fora da faixa ±{_fmt(Z_SIGMAS, 0)}σ: {detail}"
        return detail

    def stats(self, config: Config, suite) -> None:
        """Checagens da configuração, na ordem do relatório (depois da geração dos ovos)."""
        tag = f"creche/{config.name}"
        suite.run(f"{tag}: IVs", lambda: self._ivs(config))
        suite.run(f"{tag}: natureza", lambda: self._nature(config))
        if species_info(REPO_ROOT, config.child).two_abilities:
            suite.run(f"{tag}: habilidade", lambda: self._ability(config))
        if config.probes:
            suite.run(f"{tag}: golpes de ovo", lambda: self._egg_moves(config))
        suite.run(f"{tag}: gênero", lambda: self._gender(config))


class BreedingScenario(BreedingStats, CatchSaveScenario):
    def __init__(self, ctx: ScenarioContext):
        super().__init__(ctx)
        self.box: Mailbox | None = None
        self.moves = header_defines(REPO_ROOT, "moves.h")
        self.setup_addr = self.results_addr = 0
        self.records: dict[str, list[Record]] = {}
        self.frames_per_egg: list[float] = []
        self.continue_shot = "creche_continue"

    # --- atalhos -------------------------------------------------------------------------
    def _parent_bytes(self, p: Parent) -> bytes:
        moves = [self.moves[m] for m in p.moves] + [0] * (4 - len(p.moves))
        item = self.consts.item(p.item) if p.item else 0
        return struct.pack(PARENT_FORMAT, self.consts.species(p.species), item, *moves, *p.ivs,
                           GENDER_CODE[p.gender], p.nature, p.ability)

    def setup(self, config: Config, pending: bool = False) -> int:
        probes = [self.moves[m] for m in config.probes] + [0] * (4 - len(config.probes))
        raw = (self._parent_bytes(config.father) + self._parent_bytes(config.mother)
               + struct.pack(PROBES_FORMAT, *probes))
        self.emu.write(self.setup_addr, raw)
        compat = self.box.call(CMD_BREED_SETUP, int(pending))
        assert compat != 0xFFFFFFFF, f"{config.name}: o jogo recusou um dos pais"
        assert compat > 0, f"{config.name}: pais incompatíveis (compatibilidade 0)"
        return compat

    def breed(self, count: int) -> list[Record]:
        out: list[Record] = []
        while len(out) < count:
            n = min(BATCH, count - len(out))
            start = self.emu.frames(0)
            got = self.box.call(CMD_BREED_EGGS, n, timeout=n * FRAMES_PER_EGG_LIMIT)
            assert got == n, f"BREED_EGGS devolveu {got:#x} (time cheio?)"
            self.frames_per_egg.append((self.emu.frames(0) - start) / n)
            out += unpack_records(self.emu.read(self.results_addr, RECORD_SIZE * n), n)
        return out

    # --- início --------------------------------------------------------------------------
    def _start(self) -> str:
        self.box = Mailbox(self.ctl)
        self.setup_addr = self.game.syms.addr("gTestBreedSetup")
        self.results_addr = self.game.syms.addr("gEnemyParty")
        self._title_to_continue("tela de título da build de teste", shot=self.continue_shot)
        party = self.game.party()
        assert len(party) < 6, "time cheio: não cabe o ovo"
        return (f"CONTINUAR no Centro de Viridian; time de {len(party)}; gTestBreedSetup em "
                f"0x{self.setup_addr:08x}")

    # --- checagens de uma configuração ---------------------------------------------------
    def _generate(self, config: Config) -> str:
        t0 = time.monotonic()
        compat = self.setup(config)
        recs = self.breed(share(config.eggs, self.ctx.part, self.ctx.parts))
        self.records[config.name] = recs
        child = self.consts.species(config.child)
        wrong = [r for r in recs if r.species != child or not r.is_egg]
        assert not wrong, f"{len(wrong)} ovo(s) de espécie errada ou sem a marca de ovo: {wrong[:3]}"
        seconds = time.monotonic() - t0
        if self.ctx.parts > 1:
            self._partial = {"records": recs, "compat": compat, "seconds": seconds,
                             "seed": self.ctx.seed}
            return generation_detail(config, recs, compat, seconds,
                                     part_label(self.ctx.part, self.ctx.parts))
        return generation_detail(config, recs, compat, seconds)

    def _config(self, config: Config) -> None:
        self._partial = None
        res = self.suite.run(generation_name(config), lambda: self._generate(config))
        if res.status == "falha":
            return
        if self.ctx.parts > 1:   # as estatísticas saem dos ovos de todas as partes (merge_breeding)
            res.data = self._partial
            return
        self.stats(config, self.suite)

    # --- personalidade e shiny dos ovos --------------------------------------------------
    def _personality(self) -> str:
        self.setup(CONFIGS[0])
        matches = self.box.call(CMD_EGG_PERSONALITY, EGG_PERSONALITY_TRIALS,
                                timeout=EGG_PERSONALITY_TRIALS * FRAMES_PER_EGG_LIMIT)
        assert matches == EGG_PERSONALITY_TRIALS, (
            f"{matches} de {EGG_PERSONALITY_TRIALS} ovos com a personalidade sorteada")
        return (f"{EGG_PERSONALITY_TRIALS} ovos entregues, todos com a personalidade da rotina de "
                "sorteio (natureza + habilidade + rerolls de shiny) partindo do mesmo RNG")

    def _shiny(self, with_charm: bool) -> str:
        part, parts = self.ctx.part, self.ctx.parts
        samples = share(EGG_SHINY_SAMPLES, part, parts)
        charm = self.consts.item("ITEM_SHINY_CHARM")
        before = self.game.bag_quantity(charm)
        start, t0 = self.emu.frames(0), time.monotonic()
        shinies = self.box.call(CMD_EGG_SHINIES, samples, int(with_charm),
                                timeout=samples * FRAMES_PER_SHINY_LIMIT, poll=SHINY_POLL)
        frames = self.emu.frames(0) - start
        assert self.game.bag_quantity(charm) == before, "o atalho mexeu no Shiny Charm da bolsa"
        self.measures[f"ovos_shiny_{'charm' if with_charm else 'sem_charm'}"] = shinies
        seconds = time.monotonic() - t0
        if parts > 1:
            self._partial = {"shinies": shinies, "frames": frames, "seconds": seconds,
                             "seed": self.ctx.seed}
            return (f"{part_label(part, parts)}: {shinies} shiny em {samples} ovos; {frames} "
                    f"quadros, {_fmt(seconds)} s (a faixa é conferida na soma das partes)")
        return egg_rate_detail(shinies, frames, seconds, with_charm)

    def _run_shiny(self, with_charm: bool) -> None:
        self._partial = None
        res = self.suite.run(EGG_RATE_NAMES[with_charm], lambda: self._shiny(with_charm))
        if res.status != "falha" and self._partial is not None:
            res.data = self._partial

    # --- Power items em batalha ----------------------------------------------------------
    def _evs(self) -> str:
        pidgey = species_info(REPO_ROOT, "SPECIES_PIDGEY").ev_yield
        machop = species_info(REPO_ROOT, "SPECIES_MACHOP").ev_yield
        cases = [  # (descrição, item, derrotado, rendimento, atributo, EV dele, EV dos outros)
            ("sem item, derrota Pidgey", None, "SPECIES_PIDGEY", pidgey, 0, 0, 0),
            ("Power Bracer, derrota Pidgey", "ITEM_POWER_BRACER", "SPECIES_PIDGEY", pidgey, 1, 0, 0),
            ("Power Bracer, derrota Machop", "ITEM_POWER_BRACER", "SPECIES_MACHOP", machop, 1, 0, 0),
            ("Power Anklet, derrota Pidgey", "ITEM_POWER_ANKLET", "SPECIES_PIDGEY", pidgey, 3, 0, 0),
            ("Power Weight com HP 250 (teto 255)", "ITEM_POWER_WEIGHT", "SPECIES_PIDGEY", pidgey, 0, 250, 0),
            ("Power Lens com total 510", "ITEM_POWER_LENS", "SPECIES_PIDGEY", pidgey, 4, 10, 100),
            ("Power Band com total 505 (teto 510)", "ITEM_POWER_BAND", "SPECIES_PIDGEY", pidgey, 5, 5, 100),
            ("Destiny Knot não dá EV", "ITEM_DESTINY_KNOT", "SPECIES_PIDGEY", pidgey, 1, 0, 0),
        ]
        parts, bad = [], []
        for what, item, defeated, yields, stat, ev, others in cases:
            start = [ev if i == stat else others for i in range(6)]
            power = POWER_ITEMS.get(item) if item else None
            want = expected_evs(start, yields, power)
            item_id = self.consts.item(item) if item else 0
            total = self.box.call(CMD_GAIN_EVS, item_id | self.consts.species(defeated) << 16,
                                  ev | others << 8 | stat << 16)
            got = list(self.emu.read(self.results_addr, 6))
            parts.append(f"{what}: {start} -> {got}")
            if got != want or total != sum(want):
                bad.append(f"{what}: {got} (total {total}), esperava {want}")
        assert not bad, "; ".join(bad)
        return "; ".join(parts)

    def _speed(self) -> str:
        it = self.consts.item
        cases = [  # (descrição, vel. 1, item 1, vel. 2, item 2, quem age antes: 0 = o 1º)
            ("100 x 60, sem item", 100, 0, 60, 0, 0),
            ("100 com Power Anklet (50) x 60", 100, it("ITEM_POWER_ANKLET"), 60, 0, 1),
            ("100 com Power Weight (50) x 49", 100, it("ITEM_POWER_WEIGHT"), 49, 0, 0),
            ("100 com Power Weight (50) x 51", 100, it("ITEM_POWER_WEIGHT"), 51, 0, 1),
            ("60 x 100 com Power Bracer (50)", 60, 0, 100, it("ITEM_POWER_BRACER"), 0),
            ("100 com Destiny Knot x 60", 100, it("ITEM_DESTINY_KNOT"), 60, 0, 0),
            ("100 com Everstone x 60", 100, it("ITEM_EVERSTONE"), 60, 0, 0),
            ("100 com Macho Brace (50) x 60", 100, it("ITEM_MACHO_BRACE"), 60, 0, 1),
        ]
        bad = []
        for what, s1, i1, s2, i2, want in cases:
            got = self.box.call(CMD_SPEED_ORDER, s1 | i1 << 16, s2 | i2 << 16)
            if got != want:
                bad.append(f"{what}: GetWhoStrikesFirst = {got}, esperava {want}")
        assert not bad, "; ".join(bad)
        return f"{len(cases)} casos de GetWhoStrikesFirst conferidos: " + "; ".join(c[0] for c in cases)

    # --- roteiro -------------------------------------------------------------------------
    def run(self) -> None:
        try:
            self._flow("creche: CONTINUAR com o save do modo rápido na build de teste", self._start)
            if self.ctx.parts > 1:   # cada parte com a sua sequência do RNG (paralelo.part_seed)
                seed_rng(self.emu, self.game.syms, "creche", self.ctx.part, self.ctx.seed)
            for config in CONFIGS:
                self._config(config)
            if self.ctx.part == 0:
                self.suite.run("creche: ovo entregue tem a personalidade sorteada (natureza + "
                               "habilidade + shiny juntos)", self._personality)
            self._run_shiny(False)
            self._run_shiny(True)
            if self.ctx.part > 0:    # o resto não é estatístico: só a parte 0
                return
            self.suite.run("creche: Power items em batalha dão +8 EVs (limites 255/510)", self._evs)
            self.suite.run("creche: Power items em batalha cortam a Velocidade pela metade",
                           self._speed)
            if self.frames_per_egg:
                self.measures["quadros_por_ovo"] = max(self.frames_per_egg)
        except Abort:
            pass


BREEDING_PARTS = 3      # sessões no modo paralelo (fixo: o resultado não depende do teto)
EGG_RATE_NAMES = {False: "creche: taxa de shiny dos ovos sem charm ≈ 1/4096",
                  True: "creche: taxa de shiny dos ovos com charm ≈ 1/2048"}


def generation_name(config: Config) -> str:
    return f"creche/{config.name}: ovos pelo caminho real da creche"


def generation_detail(config: Config, recs: list[Record], compat: int, seconds: float,
                      where: str = "") -> str:
    prefix = f"{where}: " if where else ""
    return (f"{prefix}{config.what}: {len(recs)} ovos de {config.child.removeprefix('SPECIES_')} "
            f"(compatibilidade {compat}), {sum(r.shiny for r in recs)} shiny; {_fmt(seconds)} s")


def egg_rate_detail(shinies: int, frames: int, seconds: float, with_charm: bool,
                    parts: int = 1) -> str:
    """Detalhe da taxa de shiny de EGG_SHINY_SAMPLES ovos; AssertionError fora da faixa."""
    attempts = ATTEMPTS_WITH_CHARM if with_charm else ATTEMPTS_NO_CHARM
    lo, hi = shiny_interval(EGG_SHINY_SAMPLES, attempts, SHINY_SIGMAS)
    mean = EGG_SHINY_SAMPLES * shiny_probability(attempts)
    where = f" em {parts} processos" if parts > 1 else ""
    detail = (f"{shinies} shiny em {EGG_SHINY_SAMPLES} ovos (esperado {_fmt(mean)}, faixa "
              f"±{_fmt(SHINY_SIGMAS, 0)}σ {_fmt(lo)}..{_fmt(hi)}); {frames} quadros, "
              f"{_fmt(seconds)} s{where}")
    assert lo <= shinies <= hi, f"fora da faixa: {detail}"
    return detail


def merge_breeding(parts_results: list[list[Result]]) -> list[Result]:
    """Junta as partes do modo paralelo, na ordem do relatório sequencial: para cada par de
    pais, os ovos de todas as partes juntos e as checagens estatísticas sobre eles; as taxas de
    shiny somadas; o resto (CONTINUAR, personalidade, EVs, Velocidade) como a parte 0 deixou.
    As faixas são as mesmas do sequencial, aplicadas ao total."""
    parts = len(parts_results)
    by_generation = {generation_name(c): c for c in CONFIGS}
    merged: list[Result] = []
    for result in parts_results[0]:
        if result.data is None:
            merged.append(result)
            continue
        datas, failure = part_data(parts_results, result.name)
        if failure is not None:
            merged.append(failure)
            continue
        suite = Suite()
        config = by_generation.get(result.name)
        if config is not None:
            recs = [r for d in datas for r in d["records"]]
            seconds = sum(d["seconds"] for d in datas)
            suite.add(Result(result.name, "ok", generation_detail(
                config, recs, datas[0]["compat"], seconds) + f" em {parts} processos"))
            stats = BreedingStats()
            stats.records = {config.name: recs}
            stats.stats(config, suite)
        else:
            with_charm = result.name == EGG_RATE_NAMES[True]
            suite.run(result.name, lambda: egg_rate_detail(
                sum(d["shinies"] for d in datas), sum(d["frames"] for d in datas),
                sum(d["seconds"] for d in datas), with_charm, parts))
        for r in suite.results:   # a semente reproduz os ovos (README: ESTEIRA_SEED)
            r.detail += f"; {seed_label(datas[0].get('seed', 0))}"
        merged.extend(suite.results)
    return merged


def run_full_breeding(ctx_test: ScenarioContext) -> None:
    """Roda o cenário na build de teste recém-ligada com o .sav do modo rápido (ver módulo)."""
    BreedingScenario(ctx_test).run()


def main(argv: list[str] | None = None) -> int:
    """Atalho para `python3 -m esteira completo --only creche ARGS`."""
    from ..__main__ import main as cli_main
    return cli_main(["completo", "--only", "creche", *(sys.argv[1:] if argv is None else argv)])


if __name__ == "__main__":
    sys.exit(main())

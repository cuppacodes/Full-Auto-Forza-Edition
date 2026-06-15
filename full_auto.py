# ============================================================
#  full_auto.py — Full Auto chained orchestrator
#  Loops the existing automations as one continuous farm:
#    AFK race (user count, for mastery points) → buy N cars →
#    unlock mastery on N cars → sell those N cars → branch:
#      • "wheelspin" → run wheelspin each cycle
#      • "racing"    → straight back to racing (no wheelspin)
#  …repeating until Stop/F9. Every step starts AND ends on the
#  game's main menu (the hand-off point), so the steps chain
#  cleanly. See each module's start/end-on-menu navigation.
#
#  SCAFFOLD STATUS: race + buy are wired (both done + validated).
#  The mastery positioning nav and the mastery→sell transition
#  are CHAINED-ONLY and not yet implemented — they're logged as
#  TODO placeholders so the orchestrator/loop is testable now
#  (race → buy → race → buy …) and the remaining steps slot in.
# ============================================================

import threading

import config
from app_lang import t as _at
import race as _race
import buy as _buy
import wheelspin as _wheelspin

# Buy / master / sell count: 999 max mastery points ÷ 30 per Subaru 22B = 33.
CAR_COUNT = 33


def run(cfg: dict, stop_event: threading.Event,
        log_cb, status_cb, race_count: int = 0,
        branch_mode: str = "racing", section_cb=None):
    """
    Full Auto loop.
    race_count: AFK races per cycle (user-defined). 0 = unlimited, which would
                never advance the cycle — the UI nudges a positive value.
    branch_mode: "racing" (no wheelspin) | "wheelspin" (spin each cycle).
    """
    section = section_cb or log_cb
    lang    = cfg.get("lang", "en")

    def stop():
        return stop_event.is_set()

    log_cb(_at("log_fa_started", lang))
    if race_count <= 0:
        # Unlimited race never returns to the menu, so the cycle can't progress.
        log_cb(_at("log_fa_race_count_warn", lang))

    cycle = 0
    while not stop():
        cycle += 1
        section(_at("log_fa_cycle", lang, n=cycle))

        # 1. AFK race (user count) → ends on the main menu
        status_cb(_at("log_fa_step_race", lang))
        log_cb(_at("log_fa_step_race", lang))
        _race.run(cfg, stop_event, log_cb, status_cb,
                  max_loops=race_count, section_cb=section_cb)
        if stop():
            break

        # 2. Buy CAR_COUNT cars (main menu → Car Collection → main menu)
        status_cb(_at("log_fa_step_buy", lang))
        log_cb(_at("log_fa_step_buy", lang, n=CAR_COUNT))
        _buy.run(cfg, stop_event, log_cb, status_cb,
                 max_loops=CAR_COUNT, section_cb=section_cb)
        if stop():
            break

        # 3. Mastery — TODO (chained positioning nav not yet wired)
        log_cb(_at("log_fa_step_mastery_todo", lang, n=CAR_COUNT))
        if stop():
            break

        # 4. Sell — TODO (mastery→sell transition not yet wired)
        log_cb(_at("log_fa_step_sell_todo", lang, n=CAR_COUNT))
        if stop():
            break

        # 5. Branch: wheelspin each cycle, or straight back to racing
        if branch_mode == "wheelspin":
            # TODO: the wheelspin step needs a per-cycle spin count (finalised
            # when the branch is wired); for now it's a placeholder so the
            # scaffold never hangs on an unlimited spin loop.
            log_cb(_at("log_fa_step_spin_todo", lang))
            if stop():
                break
        # else "racing": fall through and loop back to step 1.

    log_cb(_at("log_fa_stopped", lang))
    status_cb(_at("status_stopped", lang))

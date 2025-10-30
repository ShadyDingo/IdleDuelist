#!/usr/bin/env python3
"""Console prototype for an automated turn-based roguelite battler.

This module implements a simplified but feature-rich prototype that reflects the
design goals provided for the Idle Duelist roguelite extension. It focuses on
deterministic, log-friendly combat that supports attribute growth, milestone
upgrades, and meta progression between runs.

Main systems included:
    * Attribute-driven derived stats with three fighting styles
    * Automated turn-based combat with initiative, hit/crit rolls, and effects
    * Procedural enemy scaling, tiers, and random modifiers/affixes
    * Floor-by-floor ascent loop with milestone upgrade selections
    * Meta progression with persistent attribute points across runs
    * Detailed combat logging for balance evaluation

The prototype is intentionally console-first to keep iteration fast and
transparent for designers and balance testers.
"""

from __future__ import annotations

import json
import math
import os
import random
import textwrap
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence, Tuple


ATTRIBUTE_NAMES = ("STR", "DEX", "INT", "END", "VIT", "LCK", "SPI")
META_FILE_PATH = os.path.join(os.path.dirname(__file__), "meta_progression.json")


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------


def clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


def prompt_int(prompt: str, minimum: int, maximum: int) -> int:
    while True:
        try:
            value = int(input(prompt).strip())
        except ValueError:
            print(f"Please enter a number between {minimum} and {maximum}.")
            continue
        if minimum <= value <= maximum:
            return value
        print(f"Value must be between {minimum} and {maximum}.")


def prompt_menu(title: str, options: Sequence[str]) -> int:
    print(f"\n{title}")
    for idx, option in enumerate(options, start=1):
        print(f"  {idx}. {option}")
    return prompt_int("Select an option: ", 1, len(options))


def print_heading(text: str) -> None:
    print("\n" + "=" * len(text))
    print(text)
    print("=" * len(text))


def wrap_text(text: str, width: int = 78) -> str:
    return "\n".join(textwrap.wrap(text, width=width))


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class StyleConfig:
    name: str
    description: str
    base_attributes: Dict[str, float]
    preferred_attributes: Tuple[str, str, str]
    skill_ids: Tuple[str, ...]


@dataclass
class Skill:
    skill_id: str
    name: str
    description: str
    damage_type: str  # "physical" | "magic"
    damage_multiplier: float
    hits: int
    cooldown: int
    priority: int
    tags: Tuple[str, ...] = ()
    effect_value: float = 0.0
    duration: int = 0
    condition: Optional[str] = None  # e.g., "execute" for low-HP targeting
    secondary_value: float = 0.0


@dataclass
class StatusInstance:
    name: str
    value: float
    remaining_turns: int


@dataclass
class DerivedStats:
    max_hp: float
    power: float
    spell_power: float
    defense: float
    resistance: float
    speed: float
    accuracy: float
    dodge: float
    crit_chance: float
    crit_multiplier: float


@dataclass
class RunModifiers:
    damage_multiplier: float = 1.0
    spell_multiplier: float = 1.0
    crit_bonus: float = 0.0
    crit_damage_bonus: float = 0.0
    hp_percent_bonus: float = 0.0
    hp_flat_bonus: float = 0.0
    defense_bonus: float = 0.0
    resistance_bonus: float = 0.0
    dodge_bonus: float = 0.0
    accuracy_bonus: float = 0.0
    regen_on_kill: float = 0.0
    shield_on_kill: float = 0.0
    cooldown_reduction: float = 0.0
    extra_upgrade_choices: int = 0
    dot_bonus: float = 0.0


@dataclass
class CombatLog:
    entries: List[str] = field(default_factory=list)

    def add(self, entry: str) -> None:
        self.entries.append(entry)

    def extend(self, lines: Sequence[str]) -> None:
        self.entries.extend(lines)

    def __iter__(self):
        return iter(self.entries)


@dataclass
class Combatant:
    name: str
    style: str
    attributes: Dict[str, float]
    base_stats: DerivedStats
    modifiers: RunModifiers = field(default_factory=RunModifiers)
    current_hp: float = field(init=False)
    statuses: List[StatusInstance] = field(default_factory=list)
    cooldowns: Dict[str, int] = field(default_factory=dict)
    shield_points: float = 0.0
    total_damage_dealt: float = 0.0
    total_damage_taken: float = 0.0

    def __post_init__(self) -> None:
        self.reset_combat_state()

    # ------------------------------------------------------------------
    # Combat state helpers
    # ------------------------------------------------------------------

    def reset_combat_state(self) -> None:
        self.current_hp = self.max_hp
        self.statuses.clear()
        self.cooldowns.clear()
        self.shield_points = 0.0
        self.total_damage_dealt = 0.0
        self.total_damage_taken = 0.0

    @property
    def max_hp(self) -> float:
        bonus_percent = 1.0 + self.modifiers.hp_percent_bonus
        return (self.base_stats.max_hp + self.modifiers.hp_flat_bonus) * bonus_percent

    @property
    def effective_power(self) -> float:
        return self.base_stats.power * self.modifiers.damage_multiplier

    @property
    def effective_spell_power(self) -> float:
        return self.base_stats.spell_power * self.modifiers.spell_multiplier

    @property
    def effective_defense(self) -> float:
        defense = self.base_stats.defense + self.modifiers.defense_bonus
        buff = sum(effect.value for effect in self.statuses if effect.name == "defense_buff")
        shred = sum(effect.value for effect in self.statuses if effect.name == "armor_shred")
        return max(0.0, defense + buff - shred)

    @property
    def effective_resistance(self) -> float:
        resistance = self.base_stats.resistance + self.modifiers.resistance_bonus
        buff = sum(effect.value for effect in self.statuses if effect.name == "resist_buff")
        shred = sum(effect.value for effect in self.statuses if effect.name == "resist_shred")
        return max(0.0, resistance + buff - shred)

    @property
    def effective_speed(self) -> float:
        speed = self.base_stats.speed
        speed += sum(effect.value for effect in self.statuses if effect.name == "haste")
        speed -= sum(effect.value for effect in self.statuses if effect.name == "slow")
        return max(1.0, speed)

    @property
    def effective_accuracy(self) -> float:
        return clamp(self.base_stats.accuracy + self.modifiers.accuracy_bonus, 0.0, 1.2)

    @property
    def effective_dodge(self) -> float:
        dodge_bonus = self.modifiers.dodge_bonus
        dodge_bonus += sum(effect.value for effect in self.statuses if effect.name == "dodge_buff")
        return clamp(self.base_stats.dodge + dodge_bonus, 0.0, 0.6)

    @property
    def crit_chance(self) -> float:
        base = self.base_stats.crit_chance + self.modifiers.crit_bonus
        bonus = sum(effect.value for effect in self.statuses if effect.name == "crit_buff")
        return clamp(base + bonus, 0.0, 0.9)

    @property
    def crit_multiplier(self) -> float:
        return self.base_stats.crit_multiplier + self.modifiers.crit_damage_bonus

    def decrement_cooldowns(self) -> None:
        for skill_id in list(self.cooldowns.keys()):
            self.cooldowns[skill_id] -= 1
            if self.cooldowns[skill_id] <= 0:
                del self.cooldowns[skill_id]

    def apply_status(self, status: StatusInstance) -> None:
        self.statuses.append(status)

    def remove_expired_statuses(self) -> None:
        self.statuses = [effect for effect in self.statuses if effect.remaining_turns > 0]

    def tick_start_of_turn(self, log: CombatLog) -> None:
        total_dot = 0.0
        for effect in self.statuses:
            if effect.name in {"bleed", "burn"}:
                total_dot += effect.value
        if total_dot > 0:
            damage = total_dot * (1.0 + self.modifiers.dot_bonus)
            self.receive_damage(damage, damage_type="true", log=log, source=f"{self.name}'s DoTs")

    def step_status_durations(self) -> None:
        for effect in self.statuses:
            effect.remaining_turns -= 1
        self.remove_expired_statuses()

    def receive_damage(self, amount: float, damage_type: str, log: CombatLog, source: str) -> float:
        original_amount = amount
        if damage_type == "physical":
            amount = max(0.0, amount - self.effective_defense)
        elif damage_type == "magic":
            amount = max(0.0, amount - self.effective_resistance)

        # Shield absorbs before HP
        if self.shield_points > 0:
            absorbed = min(self.shield_points, amount)
            self.shield_points -= absorbed
            amount -= absorbed
            if absorbed > 0:
                log.add(f"{self.name}'s shield absorbs {absorbed:.1f} damage from {source}.")

        if amount > 0:
            self.current_hp -= amount
            self.total_damage_taken += amount
            log.add(f"{self.name} takes {amount:.1f} {damage_type} damage from {source} (raw {original_amount:.1f}).")
        return amount

    def heal(self, amount: float, log: CombatLog, source: str) -> None:
        if amount <= 0:
            return
        prev_hp = self.current_hp
        self.current_hp = clamp(self.current_hp + amount, 0.0, self.max_hp)
        actual = self.current_hp - prev_hp
        if actual > 0:
            log.add(f"{self.name} heals {actual:.1f} HP from {source}.")

    def grant_shield(self, amount: float, log: CombatLog, source: str) -> None:
        if amount <= 0:
            return
        self.shield_points += amount
        log.add(f"{self.name} gains a {amount:.1f} HP shield from {source}.")

    @property
    def is_alive(self) -> bool:
        return self.current_hp > 0


@dataclass
class Enemy:
    name: str
    floor: int
    tier: int
    is_elite: bool
    is_boss: bool
    modifiers: Tuple[str, ...]
    combatant: Combatant


@dataclass
class CombatResult:
    player_won: bool
    combat_log: CombatLog
    rounds: int
    enemy: Enemy


@dataclass
class RunSummary:
    floors_cleared: int
    best_floor: int
    elites_defeated: int
    bosses_defeated: int
    attribute_points_earned: int
    combat_logs: List[CombatLog]


@dataclass
class MetaProgression:
    spent_attributes: Dict[str, int]
    unspent_points: int
    best_floor: int

    def total_allocated(self) -> int:
        return sum(self.spent_attributes.values())


# ---------------------------------------------------------------------------
# Definitions for styles, skills, upgrades, and modifiers
# ---------------------------------------------------------------------------


STYLE_CONFIGS: Dict[str, StyleConfig] = {
    "melee": StyleConfig(
        name="Melee",
        description="Frontline bruiser relying on strength, toughness, and resilience.",
        base_attributes={"STR": 18, "DEX": 10, "INT": 6, "END": 14, "VIT": 12, "LCK": 8, "SPI": 8},
        preferred_attributes=("STR", "END", "VIT"),
        skill_ids=("crushing_blow", "bleeding_edge", "guarded_stance"),
    ),
    "ranged": StyleConfig(
        name="Ranged",
        description="Precise hunter capitalizing on accuracy and burst criticals.",
        base_attributes={"STR": 10, "DEX": 18, "INT": 8, "END": 9, "VIT": 11, "LCK": 14, "SPI": 8},
        preferred_attributes=("DEX", "LCK", "STR"),
        skill_ids=("aimed_shot", "rapid_volley", "smoke_veil"),
    ),
    "magic": StyleConfig(
        name="Magic",
        description="Spellcaster manipulating arcane forces and adaptive shielding.",
        base_attributes={"STR": 6, "DEX": 9, "INT": 18, "END": 8, "VIT": 11, "LCK": 12, "SPI": 16},
        preferred_attributes=("INT", "SPI", "LCK"),
        skill_ids=("arcane_burst", "frost_lance", "mana_barrier"),
    ),
}


SKILL_DEFINITIONS: Dict[str, Skill] = {
    "basic_attack": Skill(
        skill_id="basic_attack",
        name="Basic Attack",
        description="Standard attack used when no better option is available.",
        damage_type="physical",
        damage_multiplier=1.0,
        hits=1,
        cooldown=0,
        priority=0,
    ),
    # Melee
    "crushing_blow": Skill(
        skill_id="crushing_blow",
        name="Crushing Blow",
        description="Deliver a heavy strike that reduces enemy armor.",
        damage_type="physical",
        damage_multiplier=1.6,
        hits=1,
        cooldown=3,
        priority=3,
        tags=("armor_shred",),
        effect_value=4.0,
        duration=2,
    ),
    "bleeding_edge": Skill(
        skill_id="bleeding_edge",
        name="Bleeding Edge",
        description="Slash to apply a stacking bleed.",
        damage_type="physical",
        damage_multiplier=1.2,
        hits=1,
        cooldown=2,
        priority=2,
        tags=("bleed",),
        effect_value=6.0,
        duration=3,
    ),
    "guarded_stance": Skill(
        skill_id="guarded_stance",
        name="Guarded Stance",
        description="Brace to gain a shield and temporary defense.",
        damage_type="physical",
        damage_multiplier=0.0,
        hits=0,
        cooldown=4,
        priority=1,
        tags=("shield", "defense_buff"),
        effect_value=18.0,
        duration=2,
        secondary_value=4.0,
    ),
    # Ranged
    "aimed_shot": Skill(
        skill_id="aimed_shot",
        name="Aimed Shot",
        description="High precision shot with elevated crit chance.",
        damage_type="physical",
        damage_multiplier=1.8,
        hits=1,
        cooldown=3,
        priority=3,
        tags=("crit_buff",),
        effect_value=0.2,
        duration=1,
    ),
    "rapid_volley": Skill(
        skill_id="rapid_volley",
        name="Rapid Volley",
        description="Loose a hail of arrows dealing multiple hits.",
        damage_type="physical",
        damage_multiplier=0.8,
        hits=3,
        cooldown=3,
        priority=2,
        tags=(),
    ),
    "smoke_veil": Skill(
        skill_id="smoke_veil",
        name="Smoke Veil",
        description="Obscure the battlefield to increase dodge chance.",
        damage_type="physical",
        damage_multiplier=0.0,
        hits=0,
        cooldown=4,
        priority=1,
        tags=("dodge_buff",),
        effect_value=0.15,
        duration=2,
    ),
    # Magic
    "arcane_burst": Skill(
        skill_id="arcane_burst",
        name="Arcane Burst",
        description="Explosive blast of arcane energy applying burn.",
        damage_type="magic",
        damage_multiplier=1.5,
        hits=1,
        cooldown=2,
        priority=3,
        tags=("burn",),
        effect_value=7.0,
        duration=3,
    ),
    "frost_lance": Skill(
        skill_id="frost_lance",
        name="Frost Lance",
        description="Icy projectile that slows the target.",
        damage_type="magic",
        damage_multiplier=1.2,
        hits=1,
        cooldown=2,
        priority=2,
        tags=("slow",),
        effect_value=2.0,
        duration=2,
    ),
    "mana_barrier": Skill(
        skill_id="mana_barrier",
        name="Mana Barrier",
        description="Convert mana into a protective shield.",
        damage_type="magic",
        damage_multiplier=0.0,
        hits=0,
        cooldown=4,
        priority=1,
        tags=("shield", "resist_buff"),
        effect_value=20.0,
        duration=2,
        secondary_value=3.0,
    ),
}


def _apply_run_bonus(player: Combatant, log: CombatLog, field_name: str, value: float) -> None:
    current = getattr(player.modifiers, field_name)
    setattr(player.modifiers, field_name, current + value)
    log.add(f"Run modifier '{field_name}' increased by {value:+.2f}.")


UPGRADE_POOL: Tuple[Tuple[str, str, Callable[[Combatant, CombatLog], None]], ...] = (
    (
        "Sharpened Edge",
        "Increase physical damage by 15% this run.",
        lambda player, log: _apply_run_bonus(player, log, "damage_multiplier", 0.15),
    ),
    (
        "Elemental Overload",
        "Increase spell damage by 18% this run.",
        lambda player, log: _apply_run_bonus(player, log, "spell_multiplier", 0.18),
    ),
    (
        "Keen Eye",
        "Gain +10% crit chance and +0.3 crit damage.",
        lambda player, log: (
            _apply_run_bonus(player, log, "crit_bonus", 0.10),
            _apply_run_bonus(player, log, "crit_damage_bonus", 0.3),
        ),
    ),
    (
        "Bulwark Plating",
        "Gain +20% max HP and +4 defense.",
        lambda player, log: (
            _apply_run_bonus(player, log, "hp_percent_bonus", 0.20),
            _apply_run_bonus(player, log, "defense_bonus", 4.0),
        ),
    ),
    (
        "Arcane Ward",
        "Gain +3 resistance and 25 shield on victory.",
        lambda player, log: (
            _apply_run_bonus(player, log, "resistance_bonus", 3.0),
            _apply_run_bonus(player, log, "shield_on_kill", 12.0),
        ),
    ),
    (
        "Predator's Instinct",
        "Heal 12 HP when you defeat an enemy.",
        lambda player, log: _apply_run_bonus(player, log, "regen_on_kill", 12.0),
    ),
    (
        "Battle Rhythm",
        "Reduce skill cooldowns by 1 turn.",
        lambda player, log: _apply_run_bonus(player, log, "cooldown_reduction", 1.0),
    ),
    (
        "Tactical Insight",
        "Gain +1 upgrade choice for future milestones.",
        lambda player, log: _apply_run_bonus(player, log, "extra_upgrade_choices", 1.0),
    ),
    (
        "Lingering Afflictions",
        "Damage over time effects tick 25% harder.",
        lambda player, log: _apply_run_bonus(player, log, "dot_bonus", 0.25),
    ),
)


ENEMY_MODIFIER_POOL: Dict[str, str] = {
    "Vampiric": "Heals for 30% of damage dealt.",
    "Explosive": "On death, deals 20% max HP as true damage.",
    "Swift": "Acts faster with +25% speed.",
    "Bulwark": "Gain +30% defense and resistance.",
    "Thorns": "Reflects 15% of incoming damage.",
}


ENEMY_NAMES_BY_TIER: Dict[int, Tuple[str, ...]] = {
    0: ("Drifter Raider", "Cave Wolf", "Shadow Acolyte"),
    1: ("Ironbound Sentry", "Feral Ravager", "Mist Stalker"),
    2: ("Arcane Warden", "Blight Knight", "Stormcall Disciple"),
    3: ("Soul Reaper", "Dread Myrmidon", "Cinder Specter"),
}


# ---------------------------------------------------------------------------
# Core logic for derived stats, enemy generation, combat, and runs
# ---------------------------------------------------------------------------


def build_player(style_key: str, meta: MetaProgression) -> Combatant:
    style = STYLE_CONFIGS[style_key]
    attributes = {name: float(value) for name, value in style.base_attributes.items()}
    for attr in ATTRIBUTE_NAMES:
        attributes[attr] += meta.spent_attributes.get(attr, 0)

    if style.preferred_attributes:
        for bonus_attr in style.preferred_attributes:
            attributes[bonus_attr] += 2  # Specialization bonus for chosen style

    stats = compute_derived_stats(attributes, style_key)
    player = Combatant(
        name=f"{style.name} Challenger",
        style=style_key,
        attributes=attributes,
        base_stats=stats,
    )
    return player


def compute_derived_stats(attributes: Dict[str, float], style_key: str) -> DerivedStats:
    str_val = attributes["STR"]
    dex_val = attributes["DEX"]
    int_val = attributes["INT"]
    end_val = attributes["END"]
    vit_val = attributes["VIT"]
    lck_val = attributes["LCK"]
    spi_val = attributes["SPI"]

    max_hp = 100 + end_val * 6.0 + vit_val * 5.0 + str_val * 1.5
    power = 16 + str_val * 1.4 + dex_val * 0.6
    spell_power = 14 + int_val * 1.6 + spi_val * 0.8
    defense = 6 + end_val * 0.8 + str_val * 0.2
    resistance = 5 + vit_val * 0.6 + spi_val * 0.5
    speed = 10 + dex_val * 0.6 + spi_val * 0.3
    accuracy = clamp(0.75 + dex_val * 0.006 + lck_val * 0.003, 0.5, 1.1)
    dodge = clamp(0.07 + dex_val * 0.004 + lck_val * 0.003, 0.0, 0.45)
    crit_chance = clamp(0.1 + (dex_val + lck_val) * 0.004, 0.05, 0.55)
    crit_multiplier = 1.5 + lck_val * 0.01

    if style_key == "melee":
        power *= 1.1
        defense *= 1.1
    elif style_key == "ranged":
        accuracy += 0.05
        crit_chance += 0.08
        speed *= 1.05
    elif style_key == "magic":
        spell_power *= 1.12
        resistance *= 1.08
        dodge += 0.03

    return DerivedStats(
        max_hp=max_hp,
        power=power,
        spell_power=spell_power,
        defense=defense,
        resistance=resistance,
        speed=speed,
        accuracy=accuracy,
        dodge=dodge,
        crit_chance=crit_chance,
        crit_multiplier=crit_multiplier,
    )


def generate_enemy(floor: int, rng: random.Random) -> Enemy:
    tier = min((floor - 1) // 5, max(ENEMY_NAMES_BY_TIER.keys()))
    base_hp = 90 + tier * 30
    base_power = 14 + tier * 4
    base_spell = 12 + tier * 4
    base_defense = 6 + tier * 2.5
    base_resistance = 5 + tier * 2.0
    base_speed = 9 + tier * 1.5

    hp = base_hp * math.pow(1.10, floor - 1)
    power = base_power * math.pow(1.08, floor - 1)
    spell_power = base_spell * math.pow(1.08, floor - 1)
    defense = base_defense + (floor - 1) * 0.7
    resistance = base_resistance + (floor - 1) * 0.6
    speed = base_speed + (floor - 1) * 0.25

    accuracy = clamp(0.65 + floor * 0.004, 0.65, 1.0)
    dodge = clamp(0.05 + floor * 0.002, 0.05, 0.25)
    crit_chance = clamp(0.08 + floor * 0.002, 0.08, 0.35)
    crit_multiplier = 1.4 + tier * 0.1

    is_boss = floor % 20 == 0
    is_elite = is_boss or rng.random() < 0.18
    modifier_count = 2 if is_boss else (1 if is_elite else (1 if rng.random() < 0.35 else 0))
    modifiers = rng.sample(tuple(ENEMY_MODIFIER_POOL.keys()), k=modifier_count) if modifier_count else ()

    if is_boss:
        hp *= 1.6
        power *= 1.35
        spell_power *= 1.35
        defense *= 1.3
        resistance *= 1.25
        speed *= 1.15
        crit_chance = clamp(crit_chance + 0.10, 0.0, 0.45)

    base_stats = DerivedStats(
        max_hp=hp,
        power=power,
        spell_power=spell_power,
        defense=defense,
        resistance=resistance,
        speed=speed,
        accuracy=accuracy,
        dodge=dodge,
        crit_chance=crit_chance,
        crit_multiplier=crit_multiplier,
    )

    attributes = {name: 0.0 for name in ATTRIBUTE_NAMES}
    enemy_name_pool = ENEMY_NAMES_BY_TIER.get(tier, ENEMY_NAMES_BY_TIER[max(ENEMY_NAMES_BY_TIER.keys())])
    name = rng.choice(enemy_name_pool)
    if is_elite and not is_boss:
        name = f"Elite {name}"
    if is_boss:
        name = f"Floor {floor} Boss: {name}"

    combatant = Combatant(
        name=name,
        style="enemy",
        attributes=attributes,
        base_stats=base_stats,
    )

    # Apply modifiers to base stats
    for mod in modifiers:
        if mod == "Swift":
            combatant.base_stats.speed *= 1.25
        elif mod == "Bulwark":
            combatant.base_stats.defense *= 1.30
            combatant.base_stats.resistance *= 1.30

    combatant.reset_combat_state()
    return Enemy(name=name, floor=floor, tier=tier, is_elite=is_elite, is_boss=is_boss, modifiers=tuple(modifiers), combatant=combatant)


def choose_action(attacker: Combatant, defender: Combatant, style_key: str, rng: random.Random) -> Skill:
    available_skills: List[Skill] = []
    if style_key in STYLE_CONFIGS:
        config = STYLE_CONFIGS[style_key]
        for skill_id in config.skill_ids:
            skill = SKILL_DEFINITIONS[skill_id]
            cooldown_remaining = attacker.cooldowns.get(skill.skill_id, 0)
            if cooldown_remaining > 0:
                continue
            available_skills.append(skill)
    else:
        available_skills = []

    # Filter skills with meaningful actions
    usable_skills = []
    for skill in available_skills:
        if skill.damage_multiplier <= 0 and not skill.tags:
            continue
        if skill.condition == "execute" and defender.current_hp / defender.max_hp > 0.25:
            continue
        usable_skills.append(skill)

    if not usable_skills:
        return SKILL_DEFINITIONS["basic_attack"]

    # Evaluate skill value heuristically
    def skill_score(skill: Skill) -> float:
        if skill.damage_type == "physical":
            base_damage = attacker.effective_power * skill.damage_multiplier * skill.hits
        elif skill.damage_type == "magic":
            base_damage = attacker.effective_spell_power * skill.damage_multiplier * skill.hits
        else:
            base_damage = attacker.effective_power * skill.damage_multiplier * skill.hits

        base_damage *= attacker.crit_multiplier * clamp(attacker.crit_chance, 0.0, 0.8)

        score = base_damage + skill.priority * 10
        effect_bonus = 0.0
        for tag in skill.tags:
            if tag in {"bleed", "burn"}:
                effect_bonus += 12.0
            elif tag in {"armor_shred", "slow"}:
                effect_bonus += 10.0
            elif tag in {"shield", "dodge_buff", "defense_buff", "resist_buff"}:
                effect_bonus += 8.0
            elif tag == "crit_buff":
                effect_bonus += 14.0
        score += effect_bonus
        score += rng.random() * 5.0  # Add slight randomness so choices vary
        return score

    best_skill = max(usable_skills, key=skill_score)
    return best_skill


def execute_action(attacker: Combatant, defender: Combatant, skill: Skill, rng: random.Random, log: CombatLog) -> None:
    # Track cooldown
    if skill.cooldown > 0:
        cooldown_reduction = int(attacker.modifiers.cooldown_reduction)
        remaining = max(0, skill.cooldown - cooldown_reduction)
        if remaining > 0:
            attacker.cooldowns[skill.skill_id] = remaining

    if skill.damage_multiplier <= 0 and skill.hits == 0:
        apply_skill_effects(attacker, defender, skill, log)
        log.add(f"{attacker.name} uses {skill.name}.")
        return

    log.add(f"{attacker.name} uses {skill.name}!")
    attacker_owner: Optional[Enemy] = getattr(attacker, "owner", None)
    defender_owner: Optional[Enemy] = getattr(defender, "owner", None)
    for hit in range(skill.hits or 1):
        hit_chance = clamp(attacker.effective_accuracy - defender.effective_dodge, 0.05, 0.95)
        if rng.random() > hit_chance:
            log.add(f"  Hit {hit + 1}: Miss ({hit_chance*100:.0f}% chance).")
            continue

        if skill.damage_type == "physical":
            base_damage = attacker.effective_power * skill.damage_multiplier
        elif skill.damage_type == "magic":
            base_damage = attacker.effective_spell_power * skill.damage_multiplier
        else:
            base_damage = attacker.effective_power * skill.damage_multiplier

        crit = rng.random() < attacker.crit_chance
        crit_multiplier = attacker.crit_multiplier if crit else 1.0
        damage = base_damage * crit_multiplier
        dealt = defender.receive_damage(damage, skill.damage_type, log, source=skill.name)
        if dealt > 0:
            attacker.total_damage_dealt += dealt
            if crit:
                log.add(f"    Critical hit! ({attacker.crit_multiplier:.2f}x)")

            if attacker_owner and "Vampiric" in attacker_owner.modifiers:
                attacker.heal(dealt * 0.30, log, "Vampiric Siphon")

            if defender_owner and "Thorns" in defender_owner.modifiers:
                reflected = dealt * 0.15
                attacker.receive_damage(reflected, "true", log, source=f"{defender.name}'s Thorns")

        apply_skill_effects(attacker, defender, skill, log)


def apply_skill_effects(attacker: Combatant, defender: Combatant, skill: Skill, log: CombatLog) -> None:
    if not skill.tags:
        return

    for tag in skill.tags:
        if tag == "bleed":
            multiplier = 1.0 + attacker.modifiers.dot_bonus
            defender.apply_status(StatusInstance(name="bleed", value=skill.effect_value * multiplier, remaining_turns=skill.duration))
            log.add(f"    {defender.name} suffers a bleed for {skill.duration} turns.")
        elif tag == "burn":
            multiplier = 1.0 + attacker.modifiers.dot_bonus
            defender.apply_status(StatusInstance(name="burn", value=skill.effect_value * multiplier, remaining_turns=skill.duration))
            log.add(f"    {defender.name} is burning for {skill.duration} turns.")
        elif tag == "armor_shred":
            defender.apply_status(StatusInstance(name="armor_shred", value=skill.effect_value, remaining_turns=skill.duration))
            log.add(f"    {defender.name}'s armor reduced by {skill.effect_value:.1f} for {skill.duration} turns.")
        elif tag == "shield":
            attacker.grant_shield(skill.effect_value, log, skill.name)
        elif tag == "defense_buff":
            value = skill.secondary_value or 3.0
            attacker.apply_status(StatusInstance(name="defense_buff", value=value, remaining_turns=skill.duration))
            log.add(f"    {attacker.name}'s defenses harden for {skill.duration} turns.")
        elif tag == "dodge_buff":
            attacker.apply_status(StatusInstance(name="dodge_buff", value=skill.effect_value, remaining_turns=skill.duration))
            log.add(f"    {attacker.name} gains +{skill.effect_value*100:.0f}% dodge for {skill.duration} turns.")
        elif tag == "crit_buff":
            attacker.apply_status(StatusInstance(name="crit_buff", value=skill.effect_value, remaining_turns=skill.duration))
            log.add(f"    {attacker.name}'s crit chance increases temporarily.")
        elif tag == "slow":
            defender.apply_status(StatusInstance(name="slow", value=skill.effect_value, remaining_turns=skill.duration))
            log.add(f"    {defender.name} is slowed by {skill.effect_value:.1f} speed for {skill.duration} turns.")
        elif tag == "resist_buff":
            value = skill.secondary_value or 2.0
            attacker.apply_status(StatusInstance(name="resist_buff", value=value, remaining_turns=skill.duration))
            log.add(f"    {attacker.name}'s resistances surge for {skill.duration} turns.")


def run_combat(player: Combatant, enemy: Enemy, rng: random.Random) -> CombatResult:
    enemy.combatant.reset_combat_state()
    enemy.combatant.owner = enemy  # type: ignore[attr-defined]

    combat_log = CombatLog()
    round_counter = 1

    combat_log.add(f"Encounter: {enemy.name} (Floor {enemy.floor})")
    if enemy.modifiers:
        for mod in enemy.modifiers:
            combat_log.add(f"  Modifier: {mod} - {ENEMY_MODIFIER_POOL[mod]}")

    while player.is_alive and enemy.combatant.is_alive and round_counter < 100:
        combat_log.add(f"-- Round {round_counter} --")

        turn_order = sorted(
            (player, enemy.combatant),
            key=lambda c: (c.effective_speed, rng.random()),
            reverse=True,
        )

        for combatant in turn_order:
            if not player.is_alive or not enemy.combatant.is_alive:
                break

            combatant.decrement_cooldowns()
            combatant.tick_start_of_turn(combat_log)
            if not combatant.is_alive:
                continue

            opponent = enemy.combatant if combatant is player else player
            skill = choose_action(combatant, opponent, combatant.style, rng)
            execute_action(combatant, opponent, skill, rng, combat_log)

            combatant.step_status_durations()

            if not opponent.is_alive:
                break

        round_counter += 1

    player_won = player.is_alive and not enemy.combatant.is_alive

    if player_won:
        combat_log.add(f"Victory! {enemy.name} defeated.")
        if player.modifiers.regen_on_kill > 0:
            player.heal(player.modifiers.regen_on_kill, combat_log, "Regeneration Upgrade")
        if player.modifiers.shield_on_kill > 0:
            player.grant_shield(player.modifiers.shield_on_kill, combat_log, "Shield Upgrade")
    else:
        combat_log.add(f"Defeat... {enemy.name} overpowered you on floor {enemy.floor}.")

    if enemy.is_boss and player_won:
        combat_log.add("Boss defeated! Massive surge of power.")

    if enemy.is_elite and player_won:
        combat_log.add("Elite enemy vanquished!")

    if "Explosive" in enemy.modifiers and player_won:
        explosion_damage = enemy.combatant.base_stats.max_hp * 0.20
        player.receive_damage(explosion_damage, "true", combat_log, source="Explosive Demise")
        if player.is_alive:
            combat_log.add("You withstand the explosive aftermath.")

    return CombatResult(player_won=player_won, combat_log=combat_log, rounds=round_counter, enemy=enemy)


def calculate_attribute_points(floors_cleared: int, elites_defeated: int, bosses_defeated: int, prev_best: int) -> int:
    base = max(0, floors_cleared) * 2
    elite_bonus = elites_defeated * 3
    boss_bonus = bosses_defeated * 6
    record_bonus = 5 if floors_cleared > prev_best else 0
    return base + elite_bonus + boss_bonus + record_bonus


def milestone_upgrade(player: Combatant, rng: random.Random, log: CombatLog) -> None:
    choice_count = 3 + int(player.modifiers.extra_upgrade_choices)
    options = rng.sample(UPGRADE_POOL, k=min(choice_count, len(UPGRADE_POOL)))

    print_heading("Milestone Upgrade Available")
    for idx, (name, description, _) in enumerate(options, start=1):
        print(f"{idx}. {name} - {description}")

    selection = prompt_int("Choose an upgrade: ", 1, len(options))
    name, description, effect = options[selection - 1]

    effect(player, log)
    print(f"Selected Upgrade: {name} - {description}")
    log.add(f"Milestone Upgrade: {name} applied. {description}")


def load_meta_progression() -> MetaProgression:
    if not os.path.exists(META_FILE_PATH):
        return MetaProgression(spent_attributes={attr: 0 for attr in ATTRIBUTE_NAMES}, unspent_points=10, best_floor=0)

    with open(META_FILE_PATH, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    spent = {attr: int(data.get("spent_attributes", {}).get(attr, 0)) for attr in ATTRIBUTE_NAMES}
    unspent = int(data.get("unspent_points", 0))
    best_floor = int(data.get("best_floor", 0))
    return MetaProgression(spent_attributes=spent, unspent_points=unspent, best_floor=best_floor)


def save_meta_progression(meta: MetaProgression) -> None:
    data = {
        "spent_attributes": meta.spent_attributes,
        "unspent_points": meta.unspent_points,
        "best_floor": meta.best_floor,
    }
    with open(META_FILE_PATH, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)


def allocate_meta_points(meta: MetaProgression) -> None:
    print_heading("Meta Progression - Attribute Allocation")
    print(f"Unspent Attribute Points: {meta.unspent_points}")
    if meta.unspent_points <= 0:
        print("No points to allocate.")
        return

    print("Current allocations:")
    for attr in ATTRIBUTE_NAMES:
        print(f"  {attr}: {meta.spent_attributes.get(attr, 0)}")

    print("Enter allocations in the format 'ATTR VALUE'. Type 'done' to finish.")
    while meta.unspent_points > 0:
        raw = input(f"Points remaining ({meta.unspent_points}): ").strip().lower()
        if raw in {"done", "exit", "q"}:
            break
        parts = raw.upper().split()
        if len(parts) != 2 or parts[0] not in ATTRIBUTE_NAMES:
            print("Invalid entry. Example: STR 3")
            continue
        try:
            value = int(parts[1])
        except ValueError:
            print("Value must be an integer.")
            continue
        if value <= 0:
            print("Allocation must be positive.")
            continue
        if value > meta.unspent_points:
            print("Not enough points available.")
            continue
        meta.spent_attributes[parts[0]] += value
        meta.unspent_points -= value
        print(f"Allocated {value} points to {parts[0]}.")

    save_meta_progression(meta)


def display_meta(meta: MetaProgression) -> None:
    print_heading("Current Meta Progression")
    print(f"Best Floor Achieved: {meta.best_floor}")
    print(f"Total Points Allocated: {meta.total_allocated()}")
    print(f"Unspent Points: {meta.unspent_points}")
    for attr in ATTRIBUTE_NAMES:
        print(f"  {attr}: {meta.spent_attributes.get(attr, 0)}")


def run_game_loop() -> None:
    rng = random.Random()
    meta = load_meta_progression()

    while True:
        choice = prompt_menu(
            "Main Menu",
            (
                "Start New Run",
                "Spend Attribute Points",
                "View Meta Progress",
                "Quit",
            ),
        )

        if choice == 1:
            run = start_run(meta, rng)
            if run:
                print_run_summary(run)
                meta.unspent_points += run.attribute_points_earned
                if run.best_floor > meta.best_floor:
                    meta.best_floor = run.best_floor
                save_meta_progression(meta)
        elif choice == 2:
            allocate_meta_points(meta)
        elif choice == 3:
            display_meta(meta)
        else:
            print("Good luck on your next ascent!")
            break


def start_run(meta: MetaProgression, rng: random.Random) -> Optional[RunSummary]:
    style_choice = prompt_menu(
        "Choose Fighting Style",
        tuple(f"{config.name}: {config.description}" for config in STYLE_CONFIGS.values()),
    )
    style_key = list(STYLE_CONFIGS.keys())[style_choice - 1]
    player = build_player(style_key, meta)

    print_heading(f"Starting Run as {STYLE_CONFIGS[style_key].name}")
    print("Derived Stats:")
    print(f"  Max HP: {player.max_hp:.1f}")
    print(f"  Power: {player.effective_power:.1f}")
    print(f"  Spell Power: {player.effective_spell_power:.1f}")
    print(f"  Defense: {player.effective_defense:.1f}")
    print(f"  Resistance: {player.effective_resistance:.1f}")
    print(f"  Speed: {player.effective_speed:.1f}")
    print(f"  Accuracy: {player.effective_accuracy*100:.1f}%")
    print(f"  Dodge: {player.effective_dodge*100:.1f}%")
    print(f"  Crit Chance: {player.crit_chance*100:.1f}%")
    print(f"  Crit Multiplier: {player.crit_multiplier:.2f}x")

    player.reset_combat_state()
    floors_cleared = 0
    elites_defeated = 0
    bosses_defeated = 0
    combat_logs: List[CombatLog] = []

    for floor in range(1, 201):
        enemy = generate_enemy(floor, rng)
        result = run_combat(player, enemy, rng)
        combat_logs.append(result.combat_log)

        for entry in result.combat_log:
            print(entry)

        if not result.player_won:
            print("Run ended. You were defeated.")
            break

        floors_cleared = floor
        if enemy.is_elite:
            elites_defeated += 1
        if enemy.is_boss:
            bosses_defeated += 1

        # Milestone upgrade every 5 floors
        if floor % 5 == 0:
            milestone_upgrade(player, rng, result.combat_log)

        # Offer continuation or stop early
        cont = input("Continue to next floor? (Y/n): ").strip().lower()
        if cont in {"n", "no"}:
            print("Run voluntarily ended.")
            break

    attribute_points = calculate_attribute_points(floors_cleared, elites_defeated, bosses_defeated, meta.best_floor)
    print(f"Attribute Points Earned This Run: {attribute_points}")

    return RunSummary(
        floors_cleared=floors_cleared,
        best_floor=max(meta.best_floor, floors_cleared),
        elites_defeated=elites_defeated,
        bosses_defeated=bosses_defeated,
        attribute_points_earned=attribute_points,
        combat_logs=combat_logs,
    )


def print_run_summary(summary: RunSummary) -> None:
    print_heading("Run Summary")
    print(f"Floors Cleared: {summary.floors_cleared}")
    print(f"Elites Defeated: {summary.elites_defeated}")
    print(f"Bosses Defeated: {summary.bosses_defeated}")
    print(f"Attribute Points Earned: {summary.attribute_points_earned}")
    print(f"Best Floor (All-Time): {summary.best_floor}")

    view_logs = input("View combat logs? (y/N): ").strip().lower()
    if view_logs in {"y", "yes"}:
        for idx, log in enumerate(summary.combat_logs, start=1):
            print_heading(f"Combat Log - Encounter {idx}")
            for entry in log:
                print(entry)


def main() -> None:
    print_heading("Idle Duelist Roguelite Prototype")
    print(wrap_text("This console prototype demonstrates the automated roguelite combat loop."
                   " Use it to evaluate pacing, balance, and progression."))
    run_game_loop()


if __name__ == "__main__":
    main()


from pathlib import Path
import json

ALL_TYPES = [
    "normal", "fire", "water", "electric", "grass", "ice",
    "fighting", "poison", "ground", "flying", "psychic", "bug",
    "rock", "ghost", "dragon", "dark", "steel", "fairy"
]

# Full type charts per generation.
# Structure: chart[attacking_type][defending_type] = multiplier
# Only non-1x values are listed — everything else defaults to 1.0

GEN1_CHART = {
    "normal":   {"rock": 0.5, "ghost": 0},
    "fire":     {"fire": 0.5, "water": 0.5, "rock": 0.5, "grass": 2, "ice": 2, "bug": 2, "dragon": 0.5},
    "water":    {"water": 0.5, "fire": 2, "grass": 0.5, "ground": 2, "rock": 2, "dragon": 0.5},
    "electric": {"water": 2, "electric": 0.5, "grass": 0.5, "ground": 0, "flying": 2, "dragon": 0.5},
    "grass":    {"water": 2, "fire": 0.5, "grass": 0.5, "poison": 0.5, "ground": 2, "flying": 0.5, "bug": 0.5, "rock": 2, "dragon": 0.5},
    "ice":      {"water": 0.5, "grass": 2, "ice": 0.5, "ground": 2, "flying": 2, "dragon": 2},
    "fighting": {"normal": 2, "ice": 2, "poison": 0.5, "flying": 0.5, "psychic": 0.5, "bug": 0.5, "rock": 2, "ghost": 0},
    "poison":   {"grass": 2, "poison": 0.5, "ground": 0.5, "bug": 2, "rock": 0.5, "ghost": 0.5},
    "ground":   {"fire": 2, "electric": 2, "grass": 0.5, "poison": 2, "flying": 0, "bug": 0.5, "rock": 2},
    "flying":   {"electric": 0.5, "grass": 2, "fighting": 2, "bug": 2, "rock": 0.5},
    "psychic":  {"fighting": 2, "poison": 2, "psychic": 0.5, "ghost": 0},
    "bug":      {"fire": 0.5, "grass": 2, "fighting": 0.5, "flying": 0.5, "psychic": 2, "ghost": 0.5, "poison": 2},
    "rock":     {"fire": 2, "ice": 2, "fighting": 0.5, "ground": 0.5, "flying": 2, "bug": 2},
    "ghost":    {"normal": 0, "psychic": 0, "ghost": 2},
    "dragon":   {"dragon": 2},
    "dark":     {},
    "steel":    {},
    "fairy":    {},
}

GEN2_CHART = {
    "normal":   {"rock": 0.5, "ghost": 0, "steel": 0.5},
    "fire":     {"fire": 0.5, "water": 0.5, "rock": 0.5, "grass": 2, "ice": 2, "bug": 2, "dragon": 0.5, "steel": 2},
    "water":    {"water": 0.5, "fire": 2, "grass": 0.5, "ground": 2, "rock": 2, "dragon": 0.5},
    "electric": {"water": 2, "electric": 0.5, "grass": 0.5, "ground": 0, "flying": 2, "dragon": 0.5},
    "grass":    {"water": 2, "fire": 0.5, "grass": 0.5, "poison": 0.5, "ground": 2, "flying": 0.5, "bug": 0.5, "rock": 2, "dragon": 0.5, "steel": 0.5},
    "ice":      {"water": 0.5, "grass": 2, "ice": 0.5, "ground": 2, "flying": 2, "dragon": 2, "steel": 0.5},
    "fighting": {"normal": 2, "ice": 2, "poison": 0.5, "flying": 0.5, "psychic": 0.5, "bug": 0.5, "rock": 2, "ghost": 0, "dark": 2, "steel": 2},
    "poison":   {"grass": 2, "poison": 0.5, "ground": 0.5, "bug": 0.5, "rock": 0.5, "ghost": 0.5, "steel": 0},
    "ground":   {"fire": 2, "electric": 2, "grass": 0.5, "poison": 2, "flying": 0, "bug": 0.5, "rock": 2, "steel": 2},
    "flying":   {"electric": 0.5, "grass": 2, "fighting": 2, "bug": 2, "rock": 0.5, "steel": 0.5},
    "psychic":  {"fighting": 2, "poison": 2, "psychic": 0.5, "dark": 0, "steel": 0.5},
    "bug":      {"fire": 0.5, "grass": 2, "fighting": 0.5, "flying": 0.5, "psychic": 2, "ghost": 0.5, "dark": 2, "steel": 0.5},
    "rock":     {"fire": 2, "ice": 2, "fighting": 0.5, "ground": 0.5, "flying": 2, "bug": 2, "steel": 0.5},
    "ghost":    {"normal": 0, "psychic": 2, "ghost": 2, "dark": 0.5, "steel": 0.5},
    "dragon":   {"dragon": 2, "steel": 0.5},
    "dark":     {"fighting": 0.5, "psychic": 2, "ghost": 2, "dark": 0.5, "steel": 0.5},
    "steel":    {"fire": 0.5, "water": 0.5, "electric": 0.5, "ice": 2, "rock": 2, "steel": 0.5},
    "fairy":    {},
}

# Gen 3 — Steel no longer resists Ghost and Dark
GEN3_CHART = {
    **GEN2_CHART,
    "ghost":    {"normal": 0, "psychic": 2, "ghost": 2, "dark": 0.5},
    "dark":     {"fighting": 0.5, "psychic": 2, "ghost": 2, "dark": 0.5, "steel": 0.5},
    "steel":    {"fire": 0.5, "water": 0.5, "electric": 0.5, "ice": 2, "rock": 2, "steel": 0.5,
                 "poison": 0, "flying": 0.5, "psychic": 0.5, "bug": 0.5, "grass": 0.5,
                 "dragon": 0.5, "dark": 0.5, "ghost": 0.5, "normal": 0.5},
}

# Gen 4 — no type chart changes from Gen 3
GEN4_CHART = GEN3_CHART

# Gen 5 — no type chart changes
GEN5_CHART = GEN4_CHART

# Gen 6 — Fairy type added, Steel loses Poison and Dark resistances
GEN6_CHART = {
    **GEN5_CHART,
    "fairy":    {"fighting": 2, "dragon": 2, "dark": 2, "fire": 0.5, "poison": 0.5, "steel": 0.5},
    "poison":   {"grass": 2, "poison": 0.5, "ground": 0.5, "rock": 0.5, "ghost": 0.5,
                 "steel": 0.5, "fairy": 2, "bug": 0.5},
    "steel":    {"fire": 0.5, "water": 0.5, "electric": 0.5, "ice": 2, "rock": 2, "steel": 0.5,
                 "flying": 0.5, "psychic": 0.5, "bug": 0.5, "grass": 0.5, "dragon": 0.5,
                 "normal": 0.5, "fairy": 2},
    "dragon":   {"dragon": 2, "steel": 0.5, "fairy": 0},
    "dark":     {"fighting": 0.5, "psychic": 2, "ghost": 2, "dark": 0.5,
                 "steel": 0.5, "fairy": 0.5},
}

# Gen 7, 8, 9 — no type chart changes
GEN7_CHART = GEN6_CHART
GEN8_CHART = GEN7_CHART
GEN9_CHART = GEN8_CHART

CHARTS = {
    1: GEN1_CHART,
    2: GEN2_CHART,
    3: GEN3_CHART,
    4: GEN4_CHART,
    5: GEN5_CHART,
    6: GEN6_CHART,
    7: GEN7_CHART,
    8: GEN8_CHART,
    9: GEN9_CHART,
}


def get_effectiveness(attacking_type: str, defending_types: list[str], gen: int) -> float:
    """
    Returns the damage multiplier for an attacking type against a Pokémon
    with the given defending types, using the correct generation's chart.
    """
    chart = CHARTS[gen]
    multiplier = 1.0
    matchups = chart.get(attacking_type, {})
    for defending_type in defending_types:
        multiplier *= matchups.get(defending_type, 1.0)
    return multiplier


def team_offensive_coverage(team_types: list[list[str]], gen: int) -> dict[str, float]:
    """
    For each of the 18 types, returns the highest effectiveness
    any team member can deal against that defending type.
    team_types: list of each pokemon's type list e.g. [["fire","flying"], ["water"]]
    """
    coverage = {t: 0.0 for t in ALL_TYPES}

    for defending_type in ALL_TYPES:
        for pokemon_types in team_types:
            # Check each of the pokemon's own types as potential attacking moves
            for attacking_type in pokemon_types:
                effectiveness = get_effectiveness(attacking_type, [defending_type], gen)
                if effectiveness > coverage[defending_type]:
                    coverage[defending_type] = effectiveness

    return coverage


def team_defensive_profile(team: list[tuple[str, list[str]]], gen: int) -> dict[str, list[float]]:
    """
    For each of the 18 attacking types, returns a list of effectiveness
    values — one per team member.
    team: list of (pokemon_name, defending_types) tuples
    """
    profile = {t: [] for t in ALL_TYPES}

    for attacking_type in ALL_TYPES:
        for name, defending_types in team:
            effectiveness = get_effectiveness(attacking_type, defending_types, gen)
            profile[attacking_type].append(effectiveness)

    return profile
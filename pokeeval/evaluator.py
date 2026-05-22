from pokeeval.models import (
    Pokemon, TeamMember, EvalReport,
    TypeCoverageReport, RoleReport, StatSummary
)
from pokeeval.type_chart import (
    ALL_TYPES, get_effectiveness,
    team_offensive_coverage, team_defensive_profile
)
from pokeeval.move_classifier import refine_role, get_key_moves

# --- Role classification thresholds ---
STAT_THRESHOLD = 80      # minimum stat value to be considered "high"
SPEED_THRESHOLD = 90     # minimum speed to factor into sweeper classification
MIXED_DIFF = 15          # max difference between atk/sp_atk to be considered "mixed"


def classify_role(mon: Pokemon) -> str:
    atk = mon.attack
    spatk = mon.sp_atk
    defense = mon.defense
    spdef = mon.sp_def
    speed = mon.speed
    hp = mon.hp

    is_fast = speed >= SPEED_THRESHOLD
    is_physical_attacker = atk >= STAT_THRESHOLD
    is_special_attacker = spatk >= STAT_THRESHOLD
    is_mixed_attacker = is_physical_attacker and is_special_attacker and abs(atk - spatk) <= MIXED_DIFF
    is_physical_wall = defense >= STAT_THRESHOLD and hp >= STAT_THRESHOLD
    is_special_wall = spdef >= STAT_THRESHOLD and hp >= STAT_THRESHOLD

    if is_mixed_attacker and is_fast:
        return "Mixed Sweeper"
    if is_mixed_attacker:
        return "Mixed Attacker"
    if is_physical_attacker and is_fast:
        return "Physical Sweeper"
    if is_special_attacker and is_fast:
        return "Special Sweeper"
    if is_physical_attacker:
        return "Physical Attacker"
    if is_special_attacker:
        return "Special Attacker"
    if is_physical_wall and is_special_wall:
        return "Mixed Wall"
    if is_physical_wall:
        return "Physical Wall"
    if is_special_wall:
        return "Special Wall"
    return "Support / Utility"


def evaluate_type_coverage(team: list[Pokemon], gen: int) -> TypeCoverageReport:
    team_types = [mon.types for mon in team]
    team_named = [(mon.name, mon.types) for mon in team]

    offensive = team_offensive_coverage(team_types, gen)
    defensive = team_defensive_profile(team_named, gen)

    strong_against = [t for t, eff in offensive.items() if eff >= 2.0]
    immunities = [t for t, effs in defensive.items() if any(e == 0.0 for e in effs)]

    # Types that hit at least one member for 2x or more
    weak_to = [t for t, effs in defensive.items() if any(e >= 2.0 for e in effs)]

    # Danger types: hit 2 or more members for 2x or more
    danger_types = [
        t for t, effs in defensive.items()
        if sum(1 for e in effs if e >= 2.0) >= 2
    ]

    return TypeCoverageReport(
        offensive=offensive,
        defensive=defensive,
        strong_against=sorted(strong_against),
        weak_to=sorted(weak_to),
        danger_types=sorted(danger_types),
        immunities=sorted(immunities),
    )


def evaluate_roles(team: list[Pokemon]) -> RoleReport:
    roles = {}
    distribution = {}

    for mon in team:
        role = classify_role(mon)
        roles[mon.name] = role
        distribution[role] = distribution.get(role, 0) + 1

    warnings = []

    # Check for missing key roles
    role_set = set(roles.values())
    has_physical_offense = any(
        r in role_set for r in ["Physical Attacker", "Physical Sweeper", "Mixed Attacker", "Mixed Sweeper"]
    )
    has_special_offense = any(
        r in role_set for r in ["Special Attacker", "Special Sweeper", "Mixed Attacker", "Mixed Sweeper"]
    )
    has_physical_defense = any(r in role_set for r in ["Physical Wall", "Mixed Wall"])
    has_special_defense = any(r in role_set for r in ["Special Wall", "Mixed Wall"])

    if not has_physical_offense:
        warnings.append("No physical attacker — team may struggle against high-Defense targets.")
    if not has_special_offense:
        warnings.append("No special attacker — team may struggle against high-Sp.Def targets.")
    if not has_physical_defense:
        warnings.append("No physical wall — team is vulnerable to strong physical attackers.")
    if not has_special_defense:
        warnings.append("No special wall — team is vulnerable to strong special attackers.")

    # All attackers same type warning
    physical_count = sum(1 for r in roles.values() if "Physical" in r)
    if physical_count >= 4:
        warnings.append(
            f"{physical_count}/6 Pokémon are physical — Intimidate or Will-O-Wisp will cripple this team."
        )

    return RoleReport(roles=roles, distribution=distribution, warnings=warnings)


def evaluate_stats(team: list[Pokemon]) -> StatSummary:
    stat_names = ["hp", "attack", "defense", "sp_atk", "sp_def", "speed"]

    averages = {}
    highest = {}
    lowest = {}

    for stat in stat_names:
        values = [(mon.name, getattr(mon, stat)) for mon in team]
        avg = sum(v for _, v in values) / len(values)
        averages[stat] = round(avg, 1)
        highest[stat] = max(values, key=lambda x: x[1])
        lowest[stat] = min(values, key=lambda x: x[1])

    speed_tiers = sorted(
        [(mon.name, mon.speed) for mon in team],
        key=lambda x: x[1],
        reverse=True
    )

    return StatSummary(
        averages=averages,
        highest=highest,
        lowest=lowest,
        speed_tiers=speed_tiers,
    )


def evaluate_team(team: list[Pokemon], gen: int) -> EvalReport:
    if not team:
        raise ValueError("Team cannot be empty.")
    if len(team) > 6:
        raise ValueError("Team cannot have more than 6 Pokémon.")

    members = []
    for mon in team:
        base_role = classify_role(mon)
        learnset_moves = mon.learnset.get(str(gen), [])
        refined_role = refine_role(base_role, learnset_moves, gen)
        key_moves = get_key_moves(learnset_moves, gen)
        member = TeamMember(pokemon=mon, role=refined_role)
        member.key_moves = key_moves
        members.append(member)

    type_coverage = evaluate_type_coverage(team, gen)
    roles = evaluate_roles(team)
    stats = evaluate_stats(team)

    return EvalReport(
        generation=gen,
        team=members,
        type_coverage=type_coverage,
        roles=roles,
        stats=stats,
    )
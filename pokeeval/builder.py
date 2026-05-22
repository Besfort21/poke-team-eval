from pokeeval.models import Pokemon, BuildSuggestion
from pokeeval.evaluator import evaluate_team, classify_role
from pokeeval.type_chart import ALL_TYPES, get_effectiveness, team_offensive_coverage

# Minimum score a candidate must contribute to be worth adding
MIN_SCORE_THRESHOLD = 0.1


def _offensive_gaps(team: list[Pokemon], gen: int) -> set[str]:
    """Types the team cannot hit for neutral (1x) or better damage."""
    coverage = team_offensive_coverage([mon.types for mon in team], gen)
    return {t for t, eff in coverage.items() if eff < 1.0}


def _defensive_gaps(team: list[Pokemon], gen: int) -> set[str]:
    """Attacking types that hit at least one team member for 2x or more."""
    gaps = set()
    for attacking_type in ALL_TYPES:
        for mon in team:
            eff = get_effectiveness(attacking_type, mon.types, gen)
            if eff >= 2.0:
                gaps.add(attacking_type)
                break
    return gaps


def _team_roles(team: list[Pokemon]) -> set[str]:
    return {classify_role(mon) for mon in team}


def _covers_offensive_gap(candidate: Pokemon, gaps: set[str], gen: int) -> float:
    """Score: how many offensive gaps does this candidate fill?"""
    score = 0.0
    for gap_type in gaps:
        for atk_type in candidate.types:
            eff = get_effectiveness(atk_type, [gap_type], gen)
            if eff >= 1.0:
                score += eff  # reward super-effective coverage more
    return score


def _covers_defensive_gap(candidate: Pokemon, gaps: set[str], gen: int) -> float:
    """Score: how well does this candidate resist current threat types?"""
    score = 0.0
    for threat_type in gaps:
        eff = get_effectiveness(threat_type, candidate.types, gen)
        if eff < 1.0:
            score += (1.0 - eff)  # immunity = +1.0, resistance = +0.5
    return score


def _fills_role_gap(candidate: Pokemon, current_roles: set[str]) -> float:
    """Score: does this candidate bring a role the team is missing?"""
    role = classify_role(candidate)
    key_roles = {
        "Physical Attacker", "Physical Sweeper",
        "Special Attacker", "Special Sweeper",
        "Physical Wall", "Special Wall", "Mixed Wall",
    }
    if role not in current_roles and role in key_roles:
        return 1.0
    return 0.0


def _has_unique_typing(candidate: Pokemon, team: list[Pokemon]) -> float:
    """Score: penalise type combinations already on the team."""
    candidate_set = frozenset(candidate.types)
    for mon in team:
        if frozenset(mon.types) == candidate_set:
            return -2.0  # heavy penalty for exact duplicate typing
    return 0.0


def _score_candidate(
    candidate: Pokemon,
    current_team: list[Pokemon],
    gen: int,
) -> float:
    off_gaps = _offensive_gaps(current_team, gen)
    def_gaps = _defensive_gaps(current_team, gen)
    roles = _team_roles(current_team)

    score = 0.0
    score += _covers_offensive_gap(candidate, off_gaps, gen) * 1.5   # priority 1
    score += _covers_defensive_gap(candidate, def_gaps, gen) * 1.2   # priority 2
    score += _fills_role_gap(candidate, roles) * 1.0                 # priority 3
    score += _has_unique_typing(candidate, current_team)              # priority 4
    return score


def _explain_pick(
    candidate: Pokemon,
    current_team: list[Pokemon],
    gen: int,
) -> str:
    reasons = []
    off_gaps = _offensive_gaps(current_team, gen)
    def_gaps = _defensive_gaps(current_team, gen)
    roles = _team_roles(current_team)

    filled_off = []
    for gap_type in off_gaps:
        for atk_type in candidate.types:
            if get_effectiveness(atk_type, [gap_type], gen) >= 1.0:
                filled_off.append(gap_type)
                break
    if filled_off:
        reasons.append(f"fills offensive gap vs {', '.join(filled_off)}")

    resisted = []
    for threat in def_gaps:
        eff = get_effectiveness(threat, candidate.types, gen)
        if eff < 1.0:
            resisted.append(threat)
    if resisted:
        reasons.append(f"resists {', '.join(resisted)}")

    role = classify_role(candidate)
    if role not in roles:
        reasons.append(f"adds missing role: {role}")

    if not reasons:
        reasons.append("improves overall balance")

    types_str = "/".join(candidate.types)
    return (
        f"{candidate.name.capitalize()} ({types_str}, {role}): "
        + "; ".join(reasons) + "."
    )


def build_team(
    anchors: list[Pokemon],
    gen: int,
    pool: list[Pokemon],
    min_bst: int = 400,
) -> BuildSuggestion:
    """
    Fill remaining slots (up to 6) around the anchor Pokémon using
    rule-based scoring. Returns a BuildSuggestion with the full team
    and one explanation per filler slot.
    """
    if len(anchors) > 6:
        raise ValueError("Cannot have more than 6 anchor Pokémon.")

    anchor_ids = {mon.id for mon in anchors}

    # Remove anchors from the candidate pool
    candidates = [mon for mon in pool if mon.id not in anchor_ids and mon.bst >= min_bst]

    team = list(anchors)
    explanations = [
        f"{mon.name.capitalize()} ({'/'.join(mon.types)}): anchor — chosen by user."
        for mon in anchors
    ]

    slots_to_fill = 6 - len(anchors)

    for _ in range(slots_to_fill):
        if not candidates:
            break

        # Score every remaining candidate against current team state
        scored = [
            (mon, _score_candidate(mon, team, gen))
            for mon in candidates
        ]
        scored.sort(key=lambda x: x[1], reverse=True)

        best, best_score = scored[0]

        if best_score < MIN_SCORE_THRESHOLD:
            break  # no meaningful improvement left

        explanation = _explain_pick(best, team, gen)
        team.append(best)
        explanations.append(explanation)

        # Remove chosen Pokémon from future candidates
        candidates = [mon for mon in candidates if mon.id != best.id]

    eval_report = evaluate_team(team, gen)

    return BuildSuggestion(
        team=team,
        explanations=explanations,
        eval_report=eval_report,
    )
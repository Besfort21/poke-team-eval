from pathlib import Path
import json

DATA_DIR = Path(__file__).parent.parent / "data"
MOVES_DIR = DATA_DIR / "moves"

# Pre-Gen 4: damage class was determined by type, not by move
PHYSICAL_TYPES_PRE_GEN4 = {
    "normal", "fighting", "flying", "poison",
    "ground", "rock", "bug", "ghost", "steel"
}

SPECIAL_TYPES_PRE_GEN4 = {
    "fire", "water", "grass", "electric",
    "ice", "psychic", "dragon", "dark"
}


def load_move(move_name: str) -> dict | None:
    """Load a move from the local cache."""
    path = MOVES_DIR / f"{move_name}.json"
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def get_move_damage_class(move: dict, gen: int) -> str:
    """
    Return 'physical', 'special', or 'status' for a move in a given gen.
    Pre-Gen 4: infer from type. Gen 4+: use the move's own damage class.
    """
    if gen <= 3:
        move_type = move.get("type", "normal")
        if move_type in PHYSICAL_TYPES_PRE_GEN4:
            return "physical"
        if move_type in SPECIAL_TYPES_PRE_GEN4:
            return "special"
        return "status"
    return move.get("damage_class", "status")


def get_learnset_damage_classes(
    move_names: list[str],
    gen: int,
) -> dict[str, int]:
    """
    Count physical, special, and status moves in a learnset.
    Only counts moves with power > 0 (damaging moves).
    Returns: {"physical": int, "special": int, "status": int}
    """
    counts = {"physical": 0, "special": 0, "status": 0}

    for move_name in move_names:
        move = load_move(move_name)
        if move is None:
            continue
        if not move.get("power"):
            continue  # skip status moves and moves with no power
        damage_class = get_move_damage_class(move, gen)
        counts[damage_class] = counts.get(damage_class, 0) + 1

    return counts


def refine_role(
    base_role: str,
    learnset_moves: list[str],
    gen: int,
) -> str:
    """
    Apply moveset-based corrections to a base stat role.
    Base stats remain the primary signal — this only catches edge cases.

    Rules:
    1. If role implies physical offense but zero physical damaging moves → Support
    2. If role implies special offense but zero special damaging moves → Support
    3. If Mixed Attacker but only physical moves → Physical Attacker
    4. If Mixed Attacker but only special moves → Special Attacker
    """
    if not learnset_moves:
        return base_role  # no learnset data — don't change anything

    counts = get_learnset_damage_classes(learnset_moves, gen)
    physical = counts["physical"]
    special = counts["special"]
    total_damaging = physical + special

    OFFENSIVE_ROLES = {
        "Physical Attacker", "Physical Sweeper",
        "Special Attacker", "Special Sweeper",
        "Mixed Attacker", "Mixed Sweeper",
    }

    if total_damaging == 0 and base_role in OFFENSIVE_ROLES:
        # No damaging moves but classified as offensive — correct to Support
        return "Support / Utility"

    is_physical_role = base_role in {
        "Physical Attacker", "Physical Sweeper"
    }
    is_special_role = base_role in {
        "Special Attacker", "Special Sweeper"
    }
    is_mixed_role = base_role in {
        "Mixed Attacker", "Mixed Sweeper"
    }

    # Rule 1 — physical role but no physical moves
    if is_physical_role and physical == 0:
        return "Support / Utility"

    # Rule 2 — special role but no special moves
    if is_special_role and special == 0:
        return "Support / Utility"

    # Rule 3 — mixed role but exclusively physical moves
    if is_mixed_role and special == 0:
        if "Sweeper" in base_role:
            return "Physical Sweeper"
        return "Physical Attacker"

    # Rule 4 — mixed role but exclusively special moves
    if is_mixed_role and physical == 0:
        if "Sweeper" in base_role:
            return "Special Sweeper"
        return "Special Attacker"

    return base_role


def get_key_moves(
    move_names: list[str],
    gen: int,
    limit: int = 3,
) -> list[dict]:
    """
    Return the top damaging moves from a learnset for display purposes.
    Sorted by power descending. Returns list of {name, type, damage_class, power}.
    """
    damaging = []
    for move_name in move_names:
        move = load_move(move_name)
        if move is None:
            continue
        if not move.get("power"):
            continue
        damaging.append({
            "name": move_name,
            "type": move["type"],
            "damage_class": get_move_damage_class(move, gen),
            "power": move["power"],
        })

    damaging.sort(key=lambda m: m["power"], reverse=True)
    return damaging[:limit]
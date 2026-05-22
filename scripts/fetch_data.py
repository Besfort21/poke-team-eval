import httpx
import json
import time
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
POKEMON_DIR = DATA_DIR / "pokemon"
MOVES_DIR = DATA_DIR / "moves"
POKEMON_DIR.mkdir(parents=True, exist_ok=True)
MOVES_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://pokeapi.co/api/v2"

GEN_DEX_RANGES = {
    1: (1, 151),
    2: (1, 251),
    3: (1, 386),
    4: (1, 493),
    5: (1, 649),
    6: (1, 721),
    7: (1, 809),
    8: (1, 898),
    9: (1, 1025),
}

# Latest game version per generation — used to get the most complete learnset
GEN_VERSION_MAP = {
    1: "red",
    2: "crystal",
    3: "emerald",
    4: "platinum",
    5: "black-2",
    6: "omega-ruby",
    7: "ultra-sun",
    8: "sword",
    9: "violet",
}

STAT_KEY_MAP = {
    "hp": "hp",
    "attack": "attack",
    "defense": "defense",
    "special-attack": "sp_atk",
    "special-defense": "sp_def",
    "speed": "speed",
}


def fetch_json(url: str, retries: int = 3) -> dict:
    for attempt in range(retries):
        try:
            response = httpx.get(url, timeout=15)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"  Retry {attempt + 1}/{retries} for {url} — {e}")
            time.sleep(2)
    raise RuntimeError(f"Failed to fetch {url} after {retries} retries")


def get_generation_introduced(pokemon_id: int) -> int:
    for gen in range(1, 10):
        _, end = GEN_DEX_RANGES[gen]
        if pokemon_id <= end:
            return gen
    return 9


def extract_learnset(moves_data: list) -> dict[str, list[str]]:
    """
    Extract level-up moves per generation from PokéAPI move data.
    Returns dict: gen_str → sorted list of unique move names.
    """
    learnset = {}

    for move_entry in moves_data:
        move_name = move_entry["move"]["name"]
        for version_detail in move_entry["version_group_details"]:
            if version_detail["move_learn_method"]["name"] != "level-up":
                continue

            version_group = version_detail["version_group"]["name"]
            gen = version_group_to_gen(version_group)
            if gen is None:
                continue

            gen_str = str(gen)
            if gen_str not in learnset:
                learnset[gen_str] = []
            if move_name not in learnset[gen_str]:
                learnset[gen_str].append(move_name)

    return learnset


# Map version group names to generation numbers
VERSION_GROUP_GEN_MAP = {
    "red-blue": 1, "yellow": 1,
    "gold-silver": 2, "crystal": 2,
    "ruby-sapphire": 3, "emerald": 3, "firered-leafgreen": 3,
    "diamond-pearl": 4, "platinum": 4, "heartgold-soulsilver": 4,
    "black-white": 5, "black-2-white-2": 5,
    "x-y": 6, "omega-ruby-alpha-sapphire": 6,
    "sun-moon": 7, "ultra-sun-ultra-moon": 7,
    "sword-shield": 8, "brilliant-diamond-and-shining-pearl": 8, "legends-arceus": 8,
    "scarlet-violet": 9,
}


def version_group_to_gen(version_group: str) -> int | None:
    return VERSION_GROUP_GEN_MAP.get(version_group)


def fetch_and_save_pokemon(pokemon_id: int) -> bool:
    path = POKEMON_DIR / f"{pokemon_id}.json"

    # Check if already cached WITH learnset
    if path.exists():
        with open(path) as f:
            existing = json.load(f)
        if "learnset" in existing:
            return True  # already has learnset, skip

    url = f"{BASE_URL}/pokemon/{pokemon_id}"
    try:
        data = fetch_json(url)
    except RuntimeError:
        print(f"  Skipping #{pokemon_id} — could not fetch")
        return False

    types = [t["type"]["name"] for t in data["types"]]
    stats = {}
    for stat_entry in data["stats"]:
        key = STAT_KEY_MAP.get(stat_entry["stat"]["name"])
        if key:
            stats[key] = stat_entry["base_stat"]

    learnset = extract_learnset(data.get("moves", []))

    record = {
        "id": pokemon_id,
        "name": data["name"],
        "types": types,
        "stats": stats,
        "generation_introduced": get_generation_introduced(pokemon_id),
        "learnset": learnset,
    }

    with open(path, "w") as f:
        json.dump(record, f)

    return True


def fetch_and_save_move(move_name: str) -> bool:
    path = MOVES_DIR / f"{move_name}.json"
    if path.exists():
        return True

    url = f"{BASE_URL}/move/{move_name}"
    try:
        data = fetch_json(url)
    except RuntimeError:
        print(f"  Skipping move {move_name} — could not fetch")
        return False

    record = {
        "name": move_name,
        "type": data["type"]["name"],
        "damage_class": data["damage_class"]["name"],
        "power": data["power"],
    }

    with open(path, "w") as f:
        json.dump(record, f)

    return True


def collect_all_move_names() -> set[str]:
    """Scan all cached Pokémon and collect every move name in any learnset."""
    moves = set()
    for path in POKEMON_DIR.glob("*.json"):
        with open(path) as f:
            data = json.load(f)
        for move_list in data.get("learnset", {}).values():
            moves.update(move_list)
    return moves


def build_generation_dex() -> dict[int, list[int]]:
    gen_dex = {}
    for gen, (start, end) in GEN_DEX_RANGES.items():
        gen_dex[gen] = list(range(start, end + 1))
    return gen_dex


def save_generation_dex(gen_dex: dict[int, list[int]]):
    path = DATA_DIR / "generation_dex.json"
    with open(path, "w") as f:
        json.dump(gen_dex, f)
    print("Saved generation_dex.json")


def main():
    print("Building generation dex...")
    gen_dex = build_generation_dex()
    save_generation_dex(gen_dex)

    total = 1025
    print(f"Fetching {total} Pokémon (with learnsets) — this will take longer than before...")

    success = 0
    for pid in range(1, total + 1):
        print(f"  #{pid:04d}", end="\r")
        if fetch_and_save_pokemon(pid):
            success += 1
        time.sleep(0.15)

    print(f"\nDone. {success}/{total} Pokémon cached.")

    print("\nCollecting all move names from learnsets...")
    all_moves = collect_all_move_names()
    print(f"Found {len(all_moves)} unique moves. Fetching move data...")

    move_success = 0
    for i, move_name in enumerate(sorted(all_moves), 1):
        print(f"  {i}/{len(all_moves)} {move_name}        ", end="\r")
        if fetch_and_save_move(move_name):
            move_success += 1
        time.sleep(0.1)

    print(f"\nDone. {move_success}/{len(all_moves)} moves cached to data/moves/")


if __name__ == "__main__":
    main()
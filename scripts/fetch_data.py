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

# Regional forms — API name → generation introduced
REGIONAL_FORMS = {
    # Alolan forms (Gen 7)
    "rattata-alola": 7, "raticate-alola": 7, "raichu-alola": 7,
    "sandshrew-alola": 7, "sandslash-alola": 7, "vulpix-alola": 7,
    "ninetales-alola": 7, "diglett-alola": 7, "dugtrio-alola": 7,
    "meowth-alola": 7, "persian-alola": 7, "geodude-alola": 7,
    "graveler-alola": 7, "golem-alola": 7, "grimer-alola": 7,
    "muk-alola": 7, "exeggutor-alola": 7, "marowak-alola": 7,

    # Galarian forms (Gen 8)
    "meowth-galar": 8, "ponyta-galar": 8, "rapidash-galar": 8,
    "slowpoke-galar": 8, "slowbro-galar": 8, "farfetchd-galar": 8,
    "weezing-galar": 8, "mr-mime-galar": 8, "articuno-galar": 8,
    "zapdos-galar": 8, "moltres-galar": 8, "slowking-galar": 8,
    "corsola-galar": 8, "zigzagoon-galar": 8, "linoone-galar": 8,
    "darumaka-galar": 8, "darmanitan-galar-standard": 8,
    "darmanitan-galar-zen": 8, "yamask-galar": 8, "stunfisk-galar": 8,

    # Hisuian forms (Gen 8)
    "growlithe-hisui": 8, "arcanine-hisui": 8, "voltorb-hisui": 8,
    "electrode-hisui": 8, "typhlosion-hisui": 8, "qwilfish-hisui": 8,
    "sneasel-hisui": 8, "samurott-hisui": 8, "lilligant-hisui": 8,
    "zorua-hisui": 8, "zoroark-hisui": 8, "braviary-hisui": 8,
    "sliggoo-hisui": 8, "goodra-hisui": 8, "avalugg-hisui": 8,
    "decidueye-hisui": 8,

    # Paldean forms (Gen 9)
    "tauros-paldea-combat-breed": 9, "tauros-paldea-blaze-breed": 9,
    "tauros-paldea-aqua-breed": 9, "wooper-paldea": 9,
}

# Region suffix → display prefix
REGION_DISPLAY = {
    "alola": "Alolan",
    "galar": "Galarian",
    "hisui": "Hisuian",
    "paldea": "Paldean",
}

def make_display_name(api_name: str) -> str:
    """
    Convert API name to display name.
    e.g. 'marowak-alola'              → 'Alolan Marowak'
         'darmanitan-galar-standard'  → 'Galarian Darmanitan (Standard)'
         'tauros-paldea-combat-breed' → 'Paldean Tauros (Combat)'
    """
    # Strip '-breed' suffix — not meaningful for display
    api_name = api_name.replace("-breed", "")

    parts = api_name.split("-")

    # Find the region part
    region_prefix = None
    region_idx = None
    for i, part in enumerate(parts):
        if part in REGION_DISPLAY:
            region_prefix = REGION_DISPLAY[part]
            region_idx = i
            break

    if region_prefix is None:
        return api_name.replace("-", " ").title()

    # Base name is everything before the region suffix
    base_name = " ".join(parts[:region_idx]).title()

    # Variant is everything after the region suffix
    variant_parts = parts[region_idx + 1:]
    if variant_parts:
        variant = variant_parts[0].title()
        return f"{region_prefix} {base_name} ({variant})"

    return f"{region_prefix} {base_name}"

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


def fetch_and_save_pokemon(
    pokemon_id_or_name,
    gen_override: int = None,
    display_name: str = None,
) -> bool:
    # For regional forms use name as key, for regular use id
    is_form = isinstance(pokemon_id_or_name, str)
    cache_key = pokemon_id_or_name if is_form else pokemon_id_or_name
    path = POKEMON_DIR / f"{cache_key}.json"

    if path.exists():
        with open(path) as f:
            existing = json.load(f)
        if "learnset" in existing:
            return True

    url = f"{BASE_URL}/pokemon/{pokemon_id_or_name}"
    try:
        data = fetch_json(url)
    except RuntimeError:
        print(f"  Skipping {pokemon_id_or_name} — could not fetch")
        return False

    types = [t["type"]["name"] for t in data["types"]]
    stats = {}
    for stat_entry in data["stats"]:
        key = STAT_KEY_MAP.get(stat_entry["stat"]["name"])
        if key:
            stats[key] = stat_entry["base_stat"]

    learnset = extract_learnset(data.get("moves", []))

    gen = gen_override if gen_override else get_generation_introduced(data["id"])

    record = {
        "id": data["id"],
        "name": data["name"],
        "display_name": display_name or data["name"].replace("-", " ").title(),
        "types": types,
        "stats": stats,
        "generation_introduced": gen,
        "learnset": learnset,
        "is_regional_form": is_form,
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


def build_generation_dex() -> dict[str, list]:
    gen_dex = {}
    for gen, (start, end) in GEN_DEX_RANGES.items():
        gen_dex[str(gen)] = list(range(start, end + 1))
    return gen_dex


def save_generation_dex(gen_dex: dict):
    path = DATA_DIR / "generation_dex.json"
    with open(path, "w") as f:
        json.dump(gen_dex, f)
    print("Saved generation_dex.json")


def main():
    print("Building generation dex...")
    gen_dex = build_generation_dex()

    total = 1025
    print(f"Fetching {total} Pokémon (with learnsets)...")
    success = 0
    for pid in range(1, total + 1):
        print(f"  #{pid:04d}", end="\r")
        if fetch_and_save_pokemon(pid):
            success += 1
        time.sleep(0.15)
    print(f"\nDone. {success}/{total} Pokémon cached.")

    print(f"\nFetching {len(REGIONAL_FORMS)} regional forms...")
    form_success = 0
    for form_name, gen in REGIONAL_FORMS.items():
        print(f"  {form_name}        ", end="\r")
        display = make_display_name(form_name)
        if fetch_and_save_pokemon(form_name, gen_override=gen, display_name=display):
            # Add to generation dex
            for g in range(gen, 10):
                gen_str = str(g)
                if gen_str not in gen_dex:
                    gen_dex[gen_str] = []
                if form_name not in gen_dex[gen_str]:
                    gen_dex[gen_str].append(form_name)
            form_success += 1
        time.sleep(0.15)
    print(f"\nDone. {form_success}/{len(REGIONAL_FORMS)} regional forms cached.")

    save_generation_dex(gen_dex)

    print("\nCollecting all move names from learnsets...")
    all_moves = collect_all_move_names()
    print(f"Found {len(all_moves)} unique moves. Fetching move data...")
    move_success = 0
    for i, move_name in enumerate(sorted(all_moves), 1):
        print(f"  {i}/{len(all_moves)} {move_name}        ", end="\r")
        if fetch_and_save_move(move_name):
            move_success += 1
        time.sleep(0.1)
    print(f"\nDone. {move_success}/{len(all_moves)} moves cached.")

if __name__ == "__main__":
    main()
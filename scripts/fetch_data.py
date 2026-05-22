import httpx
import json
import time
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
POKEMON_DIR = DATA_DIR / "pokemon"
POKEMON_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://pokeapi.co/api/v2"

# Generation → max Pokédex ID (national dex cutoff per gen)
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
            response = httpx.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"  Retry {attempt + 1}/{retries} for {url} — {e}")
            time.sleep(1)
    raise RuntimeError(f"Failed to fetch {url} after {retries} retries")


def get_generation_introduced(pokemon_id: int) -> int:
    for gen, (start, end) in GEN_DEX_RANGES.items():
        if start <= pokemon_id <= end:
            # Find the lowest gen whose range includes this ID
            pass
    # Return the first generation this Pokémon appeared in
    for gen in range(1, 10):
        _, end = GEN_DEX_RANGES[gen]
        if pokemon_id <= end:
            return gen
    return 9


def fetch_and_save_pokemon(pokemon_id: int) -> bool:
    path = POKEMON_DIR / f"{pokemon_id}.json"
    if path.exists():
        return True  # already cached

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

    record = {
        "id": pokemon_id,
        "name": data["name"],
        "types": types,
        "stats": stats,
        "generation_introduced": get_generation_introduced(pokemon_id),
    }

    with open(path, "w") as f:
        json.dump(record, f)

    return True


def build_generation_dex() -> dict[int, list[int]]:
    gen_dex = {}
    for gen, (start, end) in GEN_DEX_RANGES.items():
        gen_dex[gen] = list(range(start, end + 1))
    return gen_dex


def save_generation_dex(gen_dex: dict[int, list[int]]):
    path = DATA_DIR / "generation_dex.json"
    with open(path, "w") as f:
        json.dump(gen_dex, f)
    print(f"Saved generation_dex.json")


def main():
    print("Building generation dex...")
    gen_dex = build_generation_dex()
    save_generation_dex(gen_dex)

    total = 1025
    print(f"Fetching {total} Pokémon from PokéAPI (this may take a few minutes)...")

    success = 0
    for pid in range(1, total + 1):
        print(f"  #{pid:04d}", end="\r")
        if fetch_and_save_pokemon(pid):
            success += 1
        time.sleep(0.1)  # be polite to the API

    print(f"\nDone. {success}/{total} Pokémon cached to data/pokemon/")


if __name__ == "__main__":
    main()
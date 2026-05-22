import json
from pathlib import Path
from pokeeval.models import Pokemon

DATA_DIR = Path(__file__).parent.parent / "data"
POKEMON_DIR = DATA_DIR / "pokemon"
GEN_DEX_FILE = DATA_DIR / "generation_dex.json"


def load_generation_dex() -> dict[int, list[int]]:
    """Returns a mapping of generation number → list of Pokémon IDs."""
    with open(GEN_DEX_FILE, "r") as f:
        raw = json.load(f)
    # Keys are stored as strings in JSON, convert to int
    return {int(k): v for k, v in raw.items()}


def load_pokemon(pokemon_id: int) -> Pokemon | None:
    """Load a single Pokémon from its cached JSON file."""
    path = POKEMON_DIR / f"{pokemon_id}.json"
    if not path.exists():
        return None

    with open(path, "r") as f:
        data = json.load(f)

    mon = Pokemon(
        id=data["id"],
        name=data["name"],
        types=data["types"],
        hp=data["stats"]["hp"],
        attack=data["stats"]["attack"],
        defense=data["stats"]["defense"],
        sp_atk=data["stats"]["sp_atk"],
        sp_def=data["stats"]["sp_def"],
        speed=data["stats"]["speed"],
        generation_introduced=data["generation_introduced"],
        learnset=data.get("learnset", {}),
    )
    mon.bst = mon.hp + mon.attack + mon.defense + mon.sp_atk + mon.sp_def + mon.speed
    return mon


def load_all_pokemon(generation: int) -> list[Pokemon]:
    """Load all Pokémon available in a given generation."""
    dex = load_generation_dex()

    if generation not in dex:
        raise ValueError(f"Generation {generation} not supported. Choose 1–9.")

    pokemon_list = []
    for pid in dex[generation]:
        mon = load_pokemon(pid)
        if mon is not None:
            pokemon_list.append(mon)

    return pokemon_list


def find_pokemon_by_name(name: str, generation: int) -> Pokemon | None:
    """Find a single Pokémon by name within a generation's pool."""
    name = normalise_name(name)
    all_mon = load_all_pokemon(generation)
    for mon in all_mon:
        if mon.name == name:
            return mon
    return None


def search_pokemon_by_name(query: str, generation: int, limit: int = 10) -> list[Pokemon]:
    """Return Pokémon whose names start with the query string (for autocomplete)."""
    query = normalise_name(query)
    all_mon = load_all_pokemon(generation)
    results = [mon for mon in all_mon if mon.name.startswith(query)]
    return results[:limit]

def normalise_name(name: str) -> str:
    """
    Normalise a user-supplied Pokémon name to match PokéAPI format.
    Handles spaces, dots, and common alternate spellings.
    Examples:
        "Mr Mime"   → "mr-mime"
        "Mr. Mime"  → "mr-mime"
        "Porygon Z" → "porygon-z"
        "Ho Oh"     → "ho-oh"
        "Farfetch'd" → "farfetchd"  (apostrophes removed)
    """
    name = name.strip().lower()
    name = name.replace(".", "")       # remove dots
    name = name.replace("'", "")       # remove apostrophes (farfetch'd)
    name = name.replace(" ", "-")      # spaces → hyphens
    name = name.replace("--", "-")     # clean up double hyphens
    return name
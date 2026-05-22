from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from pokeeval.data_loader import (
    load_all_pokemon,
    find_pokemon_by_name,
    search_pokemon_by_name,
)
from pokeeval.evaluator import evaluate_team
from pokeeval.builder import build_team

app = FastAPI(title="Pokémon Team Evaluator", version="0.1.0")

# ── Request / Response Schemas ──────────────────────────────────────────────

class EvaluateRequest(BaseModel):
    generation: int
    pokemon: list[str]          # list of names


class BuildRequest(BaseModel):
    generation: int
    anchors: list[str]          # list of names
    min_bst: int = 400


# ── Helpers ──────────────────────────────────────────────────────────────────

def serialise_report(report) -> dict:
    """Convert an EvalReport into a JSON-serialisable dict."""
    return {
        "generation": report.generation,
        "team": [
            {
                "name": m.pokemon.name,
                "types": m.pokemon.types,
                "role": m.role,
                "bst": m.pokemon.bst,
                "stats": {
                    "hp":      m.pokemon.hp,
                    "attack":  m.pokemon.attack,
                    "defense": m.pokemon.defense,
                    "sp_atk":  m.pokemon.sp_atk,
                    "sp_def":  m.pokemon.sp_def,
                    "speed":   m.pokemon.speed,
                },
            }
            for m in report.team
        ],
        "type_coverage": {
            "offensive":     report.type_coverage.offensive,
            "strong_against": report.type_coverage.strong_against,
            "weak_to":       report.type_coverage.weak_to,
            "danger_types":  report.type_coverage.danger_types,
            "immunities":    report.type_coverage.immunities,
        },
        "roles": {
            "roles":        report.roles.roles,
            "distribution": report.roles.distribution,
            "warnings":     report.roles.warnings,
        },
        "stats": {
            "averages":    report.stats.averages,
            "highest":     {k: list(v) for k, v in report.stats.highest.items()},
            "lowest":      {k: list(v) for k, v in report.stats.lowest.items()},
            "speed_tiers": report.stats.speed_tiers,
        },
    }


def validate_generation(gen: int):
    if gen < 1 or gen > 9:
        raise HTTPException(status_code=400, detail="Generation must be between 1 and 9.")


# ── API Endpoints ─────────────────────────────────────────────────────────────

@app.get("/api/generations")
def get_generations():
    """List all supported generations."""
    return {
        "generations": [
            {"id": 1, "name": "Generation I",   "region": "Kanto",  "pokemon": 151},
            {"id": 2, "name": "Generation II",  "region": "Johto",  "pokemon": 251},
            {"id": 3, "name": "Generation III", "region": "Hoenn",  "pokemon": 386},
            {"id": 4, "name": "Generation IV",  "region": "Sinnoh", "pokemon": 493},
            {"id": 5, "name": "Generation V",   "region": "Unova",  "pokemon": 649},
            {"id": 6, "name": "Generation VI",  "region": "Kalos",  "pokemon": 721},
            {"id": 7, "name": "Generation VII", "region": "Alola",  "pokemon": 809},
            {"id": 8, "name": "Generation VIII","region": "Galar",  "pokemon": 898},
            {"id": 9, "name": "Generation IX",  "region": "Paldea", "pokemon": 1025},
        ]
    }


@app.get("/api/pokemon/search")
def search_pokemon(q: str, gen: int = 9, limit: int = 10):
    """Search Pokémon by name prefix for autocomplete."""
    validate_generation(gen)
    if len(q) < 1:
        return {"results": []}
    results = search_pokemon_by_name(q.lower(), gen, limit=limit)
    return {
        "results": [
            {"name": mon.name, "types": mon.types, "bst": mon.bst}
            for mon in results
        ]
    }


@app.post("/api/evaluate")
def evaluate(req: EvaluateRequest):
    """Evaluate a team of up to 6 Pokémon."""
    validate_generation(req.generation)

    if not req.pokemon:
        raise HTTPException(status_code=400, detail="Provide at least 1 Pokémon.")
    if len(req.pokemon) > 6:
        raise HTTPException(status_code=400, detail="A team can have at most 6 Pokémon.")

    team = []
    for name in req.pokemon:
        mon = find_pokemon_by_name(name.lower(), req.generation)
        if mon is None:
            raise HTTPException(
                status_code=404,
                detail=f"'{name}' not found in Generation {req.generation}."
            )
        team.append(mon)

    report = evaluate_team(team, req.generation)
    return serialise_report(report)


@app.post("/api/build")
def build(req: BuildRequest):
    """Build a team around anchor Pokémon."""
    validate_generation(req.generation)

    if not req.anchors:
        raise HTTPException(status_code=400, detail="Provide at least 1 anchor Pokémon.")
    if len(req.anchors) > 6:
        raise HTTPException(status_code=400, detail="Cannot have more than 6 anchors.")

    anchors = []
    for name in req.anchors:
        mon = find_pokemon_by_name(name.lower(), req.generation)
        if mon is None:
            raise HTTPException(
                status_code=404,
                detail=f"'{name}' not found in Generation {req.generation}."
            )
        anchors.append(mon)

    pool = load_all_pokemon(req.generation)
    suggestion = build_team(anchors, req.generation, pool, min_bst=req.min_bst)

    return {
        "explanations": suggestion.explanations,
        "team": [
            {"name": mon.name, "types": mon.types, "bst": mon.bst}
            for mon in suggestion.team
        ],
        "eval_report": serialise_report(suggestion.eval_report),
    }


# ── Serve frontend ────────────────────────────────────────────────────────────

static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def serve_frontend():
    index = Path(__file__).parent / "static" / "index.html"
    if index.exists():
        return FileResponse(index)
    return {"message": "Frontend not yet built. API is live at /docs"}
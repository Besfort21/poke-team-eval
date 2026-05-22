import click
import json
from rich.console import Console
from rich.table import Table
from rich import box
from rich.text import Text

from pokeeval.data_loader import find_pokemon_by_name, load_all_pokemon
from pokeeval.evaluator import evaluate_team
from pokeeval.models import EvalReport

console = Console()

TYPE_COLOURS = {
    "normal": "white", "fire": "red", "water": "blue", "electric": "yellow",
    "grass": "green", "ice": "cyan", "fighting": "dark_red", "poison": "magenta",
    "ground": "orange3", "flying": "sky_blue1", "psychic": "hot_pink",
    "bug": "yellow_green", "rock": "tan", "ghost": "purple", "dragon": "blue_violet",
    "dark": "grey50", "steel": "steel_blue1", "fairy": "pink1",
}


def colour_type(t: str) -> str:
    colour = TYPE_COLOURS.get(t, "white")
    return f"[{colour}]{t.upper()}[/{colour}]"


def print_report(report: EvalReport):
    gen = report.generation

    # ── Header ──
    console.rule(f"[bold yellow]Team Evaluation — Generation {gen}[/bold yellow]")

    # ── Team & Roles ──
    console.print("\n[bold]Pokémon & Roles[/bold]")
    role_table = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan")
    role_table.add_column("Pokémon", style="bold")
    role_table.add_column("Types")
    role_table.add_column("Role")
    role_table.add_column("HP")
    role_table.add_column("ATK")
    role_table.add_column("DEF")
    role_table.add_column("SpA")
    role_table.add_column("SpD")
    role_table.add_column("SPE")

    for member in report.team:
        mon = member.pokemon
        types_str = " / ".join(colour_type(t) for t in mon.types)
        role_table.add_row(
            mon.name.capitalize(),
            types_str,
            member.role,
            str(mon.hp),
            str(mon.attack),
            str(mon.defense),
            str(mon.sp_atk),
            str(mon.sp_def),
            str(mon.speed),
        )
    console.print(role_table)

    # ── Role Distribution ──
    console.print("[bold]Role Distribution[/bold]")
    for role, count in report.roles.distribution.items():
        bar = "█" * count
        console.print(f"  {role:<22} {bar} ({count})")

    if report.roles.warnings:
        console.print("\n[bold red]Warnings[/bold red]")
        for w in report.roles.warnings:
            console.print(f"  [red]⚠[/red]  {w}")

    # ── Type Coverage ──
    console.print("\n[bold]Offensive Coverage[/bold]")
    strong = ", ".join(colour_type(t) for t in report.type_coverage.strong_against)
    console.print(f"  Super-effective against: {strong or 'none'}")

    no_coverage = [
        t for t, eff in report.type_coverage.offensive.items() if eff < 1.0
    ]
    if no_coverage:
        weak_off = ", ".join(colour_type(t) for t in sorted(no_coverage))
        console.print(f"  [yellow]Poor coverage against:[/yellow] {weak_off}")

    console.print("\n[bold]Defensive Profile[/bold]")
    immune = ", ".join(colour_type(t) for t in report.type_coverage.immunities) or "none"
    console.print(f"  Immunities : {immune}")
    weak = ", ".join(colour_type(t) for t in report.type_coverage.weak_to)
    console.print(f"  Weak to    : {weak or 'none'}")
    danger = ", ".join(colour_type(t) for t in report.type_coverage.danger_types)
    console.print(f"  [red]Danger types (hit 2+ members):[/red] {danger or 'none'}")

    # ── Stat Summary ──
    console.print("\n[bold]Stat Summary[/bold]")
    stat_table = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan")
    stat_table.add_column("Stat")
    stat_table.add_column("Average")
    stat_table.add_column("Highest")
    stat_table.add_column("Lowest")

    stat_labels = {
        "hp": "HP", "attack": "Attack", "defense": "Defense",
        "sp_atk": "Sp. Atk", "sp_def": "Sp. Def", "speed": "Speed"
    }
    for key, label in stat_labels.items():
        avg = report.stats.averages[key]
        hi_name, hi_val = report.stats.highest[key]
        lo_name, lo_val = report.stats.lowest[key]
        stat_table.add_row(
            label,
            str(avg),
            f"{hi_name.capitalize()} ({hi_val})",
            f"{lo_name.capitalize()} ({lo_val})",
        )
    console.print(stat_table)

    # ── Speed Tiers ──
    console.print("[bold]Speed Tiers[/bold]")
    for name, spd in report.stats.speed_tiers:
        bar = "▶" * (spd // 20)
        console.print(f"  {name.capitalize():<14} {spd:>3}  {bar}")

    console.print()


@click.group()
def cli():
    """Pokémon Team Evaluator & Builder"""
    pass


@cli.command()
@click.option("--gen", "-g", default=9, show_default=True,
              type=click.IntRange(1, 9), help="Generation (1–9)")
@click.option("--json-out", "json_out", is_flag=True, help="Output raw JSON")
@click.argument("pokemon", nargs=-1, required=True)
def evaluate(gen, json_out, pokemon):
    """Evaluate a team of up to 6 Pokémon."""
    if len(pokemon) > 6:
        console.print("[red]Error:[/red] A team can have at most 6 Pokémon.")
        raise SystemExit(1)

    team = []
    for name in pokemon:
        mon = find_pokemon_by_name(name.lower(), gen)
        if mon is None:
            console.print(f"[red]Error:[/red] '{name}' not found in Gen {gen}.")
            raise SystemExit(1)
        team.append(mon)

    report = evaluate_team(team, gen)

    if json_out:
        # Simple JSON dump of key fields
        out = {
            "generation": report.generation,
            "roles": report.roles.roles,
            "warnings": report.roles.warnings,
            "danger_types": report.type_coverage.danger_types,
            "strong_against": report.type_coverage.strong_against,
            "weak_to": report.type_coverage.weak_to,
            "immunities": report.type_coverage.immunities,
            "speed_tiers": report.stats.speed_tiers,
        }
        click.echo(json.dumps(out, indent=2))
    else:
        print_report(report)


@cli.command()
@click.option("--gen", "-g", default=9, show_default=True,
              type=click.IntRange(1, 9), help="Generation (1–9)")
@click.option("--anchor", "-a", multiple=True, required=True,
              help="Pokémon you want on the team (use multiple times)")
def build(gen, anchor):
    """Build a team around one or more anchor Pokémon. (Builder coming in Milestone 5)"""
    console.print(f"[yellow]Builder not yet implemented — coming in Milestone 5.[/yellow]")
    console.print(f"Anchors received: {', '.join(anchor)}")
    console.print(f"Generation: {gen}")


@cli.command("fetch-data")
def fetch_data():
    """Re-fetch and refresh all Pokémon data from PokéAPI."""
    import subprocess, sys
    subprocess.run([sys.executable, "scripts/fetch_data.py"])


def main():
    cli()


if __name__ == "__main__":
    main()
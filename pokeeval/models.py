from dataclasses import dataclass, field


@dataclass
class Pokemon:
    id: int
    name: str
    types: list[str]          # e.g. ["fire", "flying"]
    hp: int
    attack: int
    defense: int
    sp_atk: int
    sp_def: int
    speed: int
    generation_introduced: int
    bst: int = 0


@dataclass
class TeamMember:
    pokemon: Pokemon
    role: str = ""            # filled in by the evaluator e.g. "Physical Attacker"


@dataclass
class TypeCoverageReport:
    # Offensive: for each of the 18 types, best effectiveness your team can deal
    offensive: dict[str, float] = field(default_factory=dict)

    # Defensive: for each of the 18 types, list of effectiveness values per team member
    defensive: dict[str, list[float]] = field(default_factory=dict)

    # Types your team can hit super-effectively (2× or 4×)
    strong_against: list[str] = field(default_factory=list)

    # Types that hit at least one member for 2× or more
    weak_to: list[str] = field(default_factory=list)

    # Types that hit 2+ members for 2× or more (danger zones)
    danger_types: list[str] = field(default_factory=list)

    # Types the team is immune to
    immunities: list[str] = field(default_factory=list)


@dataclass
class RoleReport:
    # Role label per Pokémon name
    roles: dict[str, str] = field(default_factory=dict)

    # Count of each role across the team
    distribution: dict[str, int] = field(default_factory=dict)

    # Human-readable warnings e.g. "No special wall on this team"
    warnings: list[str] = field(default_factory=list)


@dataclass
class StatSummary:
    averages: dict[str, float] = field(default_factory=dict)
    highest: dict[str, tuple[str, int]] = field(default_factory=dict)  # stat → (pokemon_name, value)
    lowest: dict[str, tuple[str, int]] = field(default_factory=dict)
    speed_tiers: list[tuple[str, int]] = field(default_factory=list)   # sorted fastest → slowest


@dataclass
class EvalReport:
    generation: int
    team: list[TeamMember] = field(default_factory=list)
    type_coverage: TypeCoverageReport = field(default_factory=TypeCoverageReport)
    roles: RoleReport = field(default_factory=RoleReport)
    stats: StatSummary = field(default_factory=StatSummary)


@dataclass
class BuildSuggestion:
    team: list[Pokemon] = field(default_factory=list)
    explanations: list[str] = field(default_factory=list)  # one reason per filler slot
    eval_report: EvalReport = None
import pytest
from pokeeval.type_chart import get_effectiveness, team_offensive_coverage


class TestGen1Chart:
    def test_fire_vs_grass(self):
        assert get_effectiveness('fire', ['grass'], 1) == 2.0

    def test_electric_vs_ground_immune(self):
        assert get_effectiveness('electric', ['ground'], 1) == 0

    def test_ghost_vs_psychic_gen1_immune(self):
        # Gen 1 bug — Ghost does NOT hit Psychic
        assert get_effectiveness('ghost', ['psychic'], 1) == 0

    def test_ghost_vs_psychic_gen2_super(self):
        # Fixed in Gen 2
        assert get_effectiveness('ghost', ['psychic'], 2) == 2.0

    def test_poison_vs_bug_gen1(self):
        # Poison hits Bug super-effectively in Gen 1
        assert get_effectiveness('poison', ['bug'], 1) == 2.0

    def test_poison_vs_bug_gen2(self):
        # Nerfed in Gen 2
        assert get_effectiveness('poison', ['bug'], 2) == 0.5

    def test_dual_type_multiplication(self):
        # Water vs Fire/Rock = 2x * 2x = 4x
        assert get_effectiveness('water', ['fire', 'rock'], 1) == 4.0

    def test_dual_type_cancellation(self):
        # Electric vs Water/Ground = 2x * 0x = 0
        assert get_effectiveness('electric', ['water', 'ground'], 1) == 0


class TestFairyGen6:
    def test_fairy_not_effective_gen1(self):
        # Fairy didn't exist — should return 1x (no entry in chart)
        assert get_effectiveness('fairy', ['dragon'], 1) == 1.0

    def test_fairy_vs_dragon_gen6(self):
        assert get_effectiveness('fairy', ['dragon'], 6) == 2.0

    def test_fairy_vs_steel_gen6(self):
        assert get_effectiveness('fairy', ['steel'], 6) == 0.5

    def test_dragon_vs_fairy_gen6_immune(self):
        assert get_effectiveness('dragon', ['fairy'], 6) == 0


class TestSteelGen2:
    def test_steel_resists_poison_gen2(self):
        assert get_effectiveness('poison', ['steel'], 2) == 0

    def test_steel_loses_dark_resistance_gen6(self):
            # Dark still resists Steel in Gen 6
            eff_dark = get_effectiveness('dark', ['steel'], 6)
            assert eff_dark == 0.5

            # Poison immunity to Steel was removed in Gen 6 — now 0.5x
            eff_poison = get_effectiveness('poison', ['steel'], 6)
            assert eff_poison == 0.5

            # Confirm Steel was immune to Poison in Gen 2–5
            eff_poison_gen2 = get_effectiveness('poison', ['steel'], 2)
            assert eff_poison_gen2 == 0


class TestOffensiveCoverage:
    def test_charizard_coverage(self):
        # Fire/Flying — should cover Grass, Ice, Bug, Fighting, Ground (via flying immunity aside)
        coverage = team_offensive_coverage([['fire', 'flying']], gen=1)
        assert coverage['grass'] >= 2.0
        assert coverage['ice'] >= 2.0
        assert coverage['bug'] >= 2.0

    def test_team_coverage_improves(self):
        # Adding Water to Fire/Flying should add Rock coverage
        solo = team_offensive_coverage([['fire', 'flying']], gen=1)
        duo  = team_offensive_coverage([['fire', 'flying'], ['water']], gen=1)
        assert duo['rock'] > solo['rock']
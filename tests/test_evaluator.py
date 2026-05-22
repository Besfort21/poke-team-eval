import pytest
from pokeeval.models import Pokemon
from pokeeval.evaluator import classify_role, evaluate_team


def make_pokemon(**kwargs) -> Pokemon:
    defaults = dict(
        id=0, name='test', types=['normal'],
        hp=80, attack=80, defense=80,
        sp_atk=80, sp_def=80, speed=80,
        generation_introduced=1, bst=480,
    )
    defaults.update(kwargs)
    return Pokemon(**defaults)


class TestRoleClassification:
    def test_physical_sweeper(self):
        mon = make_pokemon(attack=120, sp_atk=50, speed=110)
        assert classify_role(mon) == 'Physical Sweeper'

    def test_special_sweeper(self):
        mon = make_pokemon(attack=50, sp_atk=120, speed=110)
        assert classify_role(mon) == 'Special Sweeper'

    def test_physical_attacker(self):
        mon = make_pokemon(attack=120, sp_atk=50, speed=50)
        assert classify_role(mon) == 'Physical Attacker'

    def test_special_attacker(self):
        mon = make_pokemon(attack=50, sp_atk=120, speed=50)
        assert classify_role(mon) == 'Special Attacker'

    def test_physical_wall(self):
        mon = make_pokemon(attack=50, sp_atk=50, hp=120, defense=120, sp_def=40, speed=50)
        assert classify_role(mon) == 'Physical Wall'

    def test_special_wall(self):
        mon = make_pokemon(attack=50, sp_atk=50, hp=120, defense=40, sp_def=120, speed=50)
        assert classify_role(mon) == 'Special Wall'

    def test_support(self):
        mon = make_pokemon(attack=50, sp_atk=50, hp=60, defense=60, sp_def=60, speed=50)
        assert classify_role(mon) == 'Support / Utility'


class TestEvaluateTeam:
    def setup_method(self):
        self.team = [
            make_pokemon(id=1, name='attacker',  types=['fire'],    attack=120, speed=100),
            make_pokemon(id=2, name='spatk',     types=['water'],   sp_atk=120, speed=100),
            make_pokemon(id=3, name='wall',      types=['rock'],    hp=120, defense=120),
            make_pokemon(id=4, name='spewall',   types=['steel'],   hp=120, sp_def=120),
            make_pokemon(id=5, name='support',   types=['grass'],   speed=50),
            make_pokemon(id=6, name='sweeper',   types=['electric'],attack=120, speed=110),
        ]

    def test_report_has_all_fields(self):
        report = evaluate_team(self.team, gen=4)
        assert report.generation == 4
        assert len(report.team) == 6
        assert report.type_coverage is not None
        assert report.roles is not None
        assert report.stats is not None

    def test_speed_tiers_sorted(self):
        report = evaluate_team(self.team, gen=4)
        speeds = [s for _, s in report.stats.speed_tiers]
        assert speeds == sorted(speeds, reverse=True)

    def test_empty_team_raises(self):
        with pytest.raises(ValueError):
            evaluate_team([], gen=1)

    def test_oversized_team_raises(self):
        big_team = [make_pokemon(id=i, name=f'mon{i}') for i in range(7)]
        with pytest.raises(ValueError):
            evaluate_team(big_team, gen=1)

    def test_stat_averages_correct(self):
        # All mons have same base stats so averages should equal those stats
        uniform_team = [make_pokemon(id=i, name=f'mon{i}', hp=100) for i in range(3)]
        report = evaluate_team(uniform_team, gen=1)
        assert report.stats.averages['hp'] == 100.0
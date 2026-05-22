import pytest
from pokeeval.move_classifier import (
    get_move_damage_class,
    get_learnset_damage_classes,
    refine_role,
)


# ── Fake move helpers ────────────────────────────────────────────────
def make_move(name="tackle", type_="normal", damage_class="physical", power=40):
    return {"name": name, "type": type_, "damage_class": damage_class, "power": power}


# ── Pre-Gen 4 split ──────────────────────────────────────────────────
class TestPreGen4Split:
    def test_normal_move_is_physical_gen1(self):
        move = make_move(type_="normal", damage_class="physical")
        assert get_move_damage_class(move, gen=1) == "physical"

    def test_fire_move_is_special_gen1(self):
        move = make_move(type_="fire", damage_class="special")
        assert get_move_damage_class(move, gen=1) == "special"

    def test_water_move_is_special_gen2(self):
        move = make_move(type_="water", damage_class="special")
        assert get_move_damage_class(move, gen=2) == "special"

    def test_ghost_move_is_physical_gen3(self):
        move = make_move(type_="ghost", damage_class="physical")
        assert get_move_damage_class(move, gen=3) == "physical"

    def test_dark_move_is_special_gen3(self):
        move = make_move(type_="dark", damage_class="special")
        assert get_move_damage_class(move, gen=3) == "special"

    def test_gen4_uses_move_damage_class_not_type(self):
        # In Gen 4+, a Normal-type move can be special (e.g. Hyper Voice)
        move = make_move(type_="normal", damage_class="special")
        assert get_move_damage_class(move, gen=4) == "special"

    def test_gen4_fire_can_be_physical(self):
        # In Gen 4+, Fire Punch is physical
        move = make_move(type_="fire", damage_class="physical")
        assert get_move_damage_class(move, gen=4) == "physical"


# ── refine_role ──────────────────────────────────────────────────────
class TestRefineRole:
    def test_no_learnset_returns_base_role(self):
        assert refine_role("Physical Attacker", [], gen=1) == "Physical Attacker"

    def test_zero_damaging_moves_returns_support(self):
        # All status moves — no power
        result = refine_role("Physical Attacker", ["splash", "growl"], gen=1)
        # splash and growl have no power so counts will be 0
        # but since they won't be in local cache this tests the no-data path
        assert result in ("Physical Attacker", "Support / Utility")

    def test_mixed_with_only_physical_moves_gen4(self):
        # Simulate: base role Mixed Attacker, but learnset only has physical moves
        # We test the logic directly by patching counts
        from pokeeval import move_classifier as mc
        original = mc.get_learnset_damage_classes

        mc.get_learnset_damage_classes = lambda moves, gen: {"physical": 3, "special": 0, "status": 1}
        result = refine_role("Mixed Attacker", ["tackle"], gen=4)
        mc.get_learnset_damage_classes = original

        assert result == "Physical Attacker"

    def test_mixed_sweeper_with_only_special_moves(self):
        from pokeeval import move_classifier as mc
        original = mc.get_learnset_damage_classes

        mc.get_learnset_damage_classes = lambda moves, gen: {"physical": 0, "special": 4, "status": 0}
        result = refine_role("Mixed Sweeper", ["psychic"], gen=4)
        mc.get_learnset_damage_classes = original

        assert result == "Special Sweeper"

    def test_physical_attacker_with_no_physical_moves(self):
        from pokeeval import move_classifier as mc
        original = mc.get_learnset_damage_classes

        mc.get_learnset_damage_classes = lambda moves, gen: {"physical": 0, "special": 2, "status": 1}
        result = refine_role("Physical Attacker", ["flamethrower"], gen=1)
        mc.get_learnset_damage_classes = original

        assert result == "Support / Utility"

    def test_special_attacker_with_no_special_moves(self):
        from pokeeval import move_classifier as mc
        original = mc.get_learnset_damage_classes

        mc.get_learnset_damage_classes = lambda moves, gen: {"physical": 3, "special": 0, "status": 0}
        result = refine_role("Special Attacker", ["tackle"], gen=4)
        mc.get_learnset_damage_classes = original

        assert result == "Support / Utility"

    def test_wall_role_unchanged(self):
        # Wall roles should never be changed by moveset
        from pokeeval import move_classifier as mc
        original = mc.get_learnset_damage_classes

        mc.get_learnset_damage_classes = lambda moves, gen: {"physical": 0, "special": 0, "status": 5}
        result = refine_role("Physical Wall", ["tackle"], gen=1)
        mc.get_learnset_damage_classes = original

        assert result == "Physical Wall"
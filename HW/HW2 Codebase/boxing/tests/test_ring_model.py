import pytest

from boxing.models.boxers_model import (
    Boxer,
    create_boxer,
    delete_boxer,
    get_leaderboard,
    get_boxer_by_id,
    get_boxer_by_name,
    get_weight_class,
    update_boxer_stats
)

from boxing.models.ring_model import RingModel

@pytest.fixture()
def ring_model():
    return RingModel()

@pytest.fixture
def boxer_1():
    return Boxer(1, "Joe", 230, 80, 90, 32, "HEAVYWEIGHT")

@pytest.fixture
def boxer_2():
    return Boxer(2, "Bob", 210, 70, 80, 29, "HEAVYWEIGHT")

@pytest.fixture
def boxer_3():
    return Boxer(3, "Dave", 190, 65, 68, 25, "MIDDLEWEIGHT")


def test_add_boxer_to_empty_ring(ring_model, boxer_1):
    """test adding a boxer to an empty ring
    """
    ring_model.enter_ring(boxer_1)

    assert len(ring_model.ring) == 1
    assert ring_model.ring[0].name == "Joe"

def test_start_fight(ring_model, boxer_2):
    """test adding another boxer and starting a fight
    """
    ring_model.enter_ring(boxer_1)
    ring_model.enter_ring(boxer_2)
    winner = ring_model.fight()

    assert (winner == "Joe" or winner == "Bob")

def test_start_fight_without_enough(ring_model, boxer_1):
    """test starting a with no boxer and one boxer
    """
    with pytest.raises(ValueError, match="There must be two boxers to start a fight."):
        ring_model.fight()

    ring_model.enter_ring(boxer_1)
    with pytest.raises(ValueError, match="There must be two boxers to start a fight."):
        ring_model.fight()

def test_clear_ring(ring_model, boxer_1):
    """test clearing a ring with a boxer
    """
    ring_model.enter(boxer_1)
    ring_model.clear_ring()

    assert len(ring_model.ring) == 0

def test_add_too_many_boxers(ring_model, boxer_3):
    """test adding too many boxers
    """
    ring_model.enter_ring(boxer_1)
    ring_model.enter_ring(boxer_2)

    with pytest.raises(ValueError, match="Ring is full, cannot add more boxers."):
        ring_model.enter_ring(boxer_3)

def test_add_bad_boxer(ring_model, boxer_1):
    """test adding a non-boxer type to the ring
    """
    wrong_boxer = [boxer_1]

    with pytest.raises(TypeError, match="Invalid type: Expected 'Boxer', got 'list'"):
        ring_model.enter_ring(wrong_boxer)

def test_get_boxer(ring_model, boxer_1, boxer_2):
    """test getting the list of all boxers in ring
    """
    ring_model.enter_ring(boxer_1)
    ring_model.enter_ring(boxer_2)
    boxers = ring_model.get_boxers

    assert len(boxers) == 2
    assert ring_model.ring[0].name == "Joe"
    assert ring_model.ring[1].name == "Bob"

def test_get_fighting_skill(ring_model, boxer_1, boxer_2):
    """test getting the fighting skills of boxers in a ring
    """
    ring_model.enter_ring(boxer_1)
    ring_model.enter_ring(boxer_2)

    assert ring_model.get_fighting_skill(boxer_1) == 699
    assert ring_model.get_fighting_skill(boxer_2) == 638
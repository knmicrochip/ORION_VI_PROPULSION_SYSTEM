import pytest

from controller import isFeasible

def test_pure_forward():
    """Moving straight ahead should always be feasible."""
    # advance_speed = 1.0, sidle_speed = 0, rotation_speed = 0
    assert isFeasible(1.0, 0.0, 0.0) is True

# I am not sure if implementation should include rotation in place
# def test_pure_rotation():
#     """Rotating in place should be feasible for a 4WS vehicle."""
#     assert isFeasible(0.0, 0.0, 0.5) is True

def test_impossible_sidle():
    """
    With a max steering angle of 45 degrees (0.785 rad), 
    pure sideways movement (90 degrees) should be unfeasible.
    """
    assert isFeasible(0.0, 1.0, 0.0) is False

def test_zero_velocity():
    """Standing still is technically feasible."""
    assert isFeasible(0.0, 0.0, 0.0) is True
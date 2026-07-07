import pytest
from math import sqrt,pi
from controller import isFeasible, clampToFeasible, calculateMotorConfiguration

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

def test_clamp_already_feasible():
    """If a speed profile is already feasible, it shouldn't radically change, 
    or it should clamp to a valid state near itself."""
    cmd_vx, cmd_vy, cmd_w = 1.0, 0.0, 0.0  # Pure forward, perfectly valid
    
    # Ensure it's feasible first
    assert isFeasible(cmd_vx, cmd_vy, cmd_w) is True
    
    result = clampToFeasible(cmd_vx, cmd_vy, cmd_w)
    assert result == (cmd_vx, cmd_vy, cmd_w)
    
    vx_out, vy_out, w_out = result
    # It should either be exactly the same or still perfectly feasible
    assert isFeasible(vx_out, vy_out, w_out) is True


def test_clamp_unfeasible_sideways():
    """Pure sideways motion (vy=2.0, vx=0) is unfeasible for this wheel configuration.
    The clamp function should return a valid alternative."""
    cmd_vx, cmd_vy, cmd_w = 0.0, 1.0, 0.0 
    
    # Verify it is initially unfeasible
    assert isFeasible(cmd_vx, cmd_vy, cmd_w) is False
    
    result = clampToFeasible(cmd_vx, cmd_vy, cmd_w)
    
    # Assert that the function didn't fall through to 'pass' (returning None)
    assert result is not None
    
    vx_out, vy_out, w_out = result
    # The output MUST be feasible
    assert isFeasible(vx_out, vy_out, w_out) is True


def test_clamp_extreme_rotation():
    """An extreme combination of high speed and rotation that violates the limits
    should be brought back into the feasible envelope."""
    cmd_vx, cmd_vy, cmd_w = 0.5, 0.5, 1.0
    
    assert not isFeasible(cmd_vx, cmd_vy, cmd_w)

    result = clampToFeasible(cmd_vx, cmd_vy, cmd_w)
    assert result is not None
    
    vx_out, vy_out, w_out = result
    assert isFeasible(vx_out, vy_out, w_out) is True

def test_returns_all_wheels():
    result = calculateMotorConfiguration(0.0, 0.0, 0.0)

    assert set(result.keys()) == {"FR", "FL", "RL", "RR"}

    for wheel in result.values():
        assert "speed" in wheel
        assert "angle" in wheel


def test_zero_motion():
    result = calculateMotorConfiguration(0.0, 0.0, 0.0)

    for wheel in result.values():
        assert wheel["speed"] == pytest.approx(0.0)
        assert wheel["angle"] == pytest.approx(0.0)

def test_forward_motion():
    result = calculateMotorConfiguration(1.0, 0.0, 0.0)

    for wheel in result.values():
        assert wheel["speed"] == pytest.approx(1.0)
        assert wheel["angle"] == pytest.approx(0.0)


# def test_sideways_motion():
#     result = calculateMotorConfiguration(0.0, 1.0, 0.0)

#     for wheel in result.values():
#         # assert wheel["speed"] == pytest.approx(1.0)
#         assert wheel["angle"] == pytest.approx(pi / 4)
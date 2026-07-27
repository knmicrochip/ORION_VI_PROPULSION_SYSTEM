import pytest
from math import sqrt,pi
from controller import isFeasible, clampToFeasible, calculateMotorConfiguration, isFeasibleFromMotorConfiguration, calculateMotorConfigurationClampless
import random

def test_pure_forward():
    """Moving straight ahead should always be feasible."""
    # advance_speed = 1.0, sidle_speed = 0, rotation_speed = 0
    assert isFeasible(1.0, 0.0, 0.0) is True

# I am not sure if implementation should include rotation in place
def test_zero_sidle():
    """Rotating in place should be feasible for a 4WS vehicle."""
    assert isFeasible(1.0, 0.0, 1.0) is False

def test_impossible_sidle():
    """
    With a max steering angle of 45 degrees (0.785 rad), 
    pure sideways movement (90 degrees) should be unfeasible.
    """
    assert isFeasible(0.0, 1.0, 0.0) is False

def test_zero_velocity():
    """Standing still is technically feasible."""
    assert isFeasible(0.0, 0.0, 0.0) is True

def test_random_feasible():
    """
    Losuje 1000 liczb, sprawdza isFeasible() oraz liczy kąt.
    """
    random.seed(2137)

    for i in range(1000):
        cmd_vx, cmd_vy, cmd_w = random.uniform(-1, 1),random.uniform(-1, 1),random.uniform(-1, 1)

        assert isFeasible(cmd_vx, cmd_vy, cmd_w) == isFeasibleFromMotorConfiguration(cmd_vx, cmd_vy, cmd_w)

def test_known_mismatch():
    # the 20 known mismatched points (isFeasible=True, fromMotor=False)
    failing_points = [
        (-0.4822, 0.0225, -0.1901),
        (0.5676, -0.3934, -0.0468),
        (0.8462, 0.0812, -0.2174),
        (0.8995, 0.1594, -0.0989),
        (0.8200, 0.0684, 0.3612),
        (-0.9466, 0.2700, 0.2127),
        (-0.4986, 0.1936, -0.1154),
        (-0.6504, -0.0567, -0.1802),
        (0.7508, 0.1363, -0.1712),
        (0.7678, -0.0108, -0.3759),
        (0.9736, -0.1964, 0.3570),
        (-0.9953, 0.6455, 0.0567),
        (-0.8373, -0.4506, -0.0940),
        (-0.9187, 0.3620, 0.1167),
        (-0.4209, -0.2104, 0.0970),
        (-0.9035, -0.6408, 0.0461),
        (-0.8583, -0.1937, -0.3430),
        (0.8060, -0.0968, 0.3538),
        (0.8341, -0.3551, -0.0031),
        (0.8116, -0.5878, 0.0708),
    ]
    
    for vx, vy, w in failing_points:
        result = calculateMotorConfigurationClampless(vx, vy, w)
        print(f"{result}")
        assert isFeasible(vx, vy, w) 
        # print(f"vx={vx:+.4f} vy={vy:+.4f} w={w:+.4f}  isFeasible={result}")



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

    assert set(result.keys()) == {"fr", "fl", "rl", "rr"}

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
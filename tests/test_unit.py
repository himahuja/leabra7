"""Test unit.py"""
import math
from typing import Tuple

import numpy as np
import pytest

from leabra7 import specs as sp
from leabra7 import unit as un


# Test un.gaussian(res, std)
def test_gaussian_returns_a_probability_density() -> None:
    assert math.isclose(sum(un.gaussian(res=0.001, std=0.01)), 1)


def test_gaussian_raises_an_error_if_std_is_too_small() -> None:
    with pytest.raises(ValueError):
        un.gaussian(res=0.001, std=0.9e-3)


def test_gaussian_raises_an_error_if_res_is_too_big() -> None:
    with pytest.raises(ValueError):
        un.gaussian(res=3, std=0.9)


# Test un.xx1(res, xmin, xmax)
def test_xx1_returns_the_correct_array() -> None:
    # This is a regression test on Fabien Benreau's prototype
    reference = np.load("tests/xx1.npy")
    assert np.allclose(un.xx1(0.001, -3, 3), reference)


@pytest.fixture(scope="module", name="nxx1_table")
def nxx1_table_fixture() -> Tuple[np.ndarray, np.ndarray]:
    """Returns a lookup table for the NXX1 function."""
    return un.nxx1_table()


# Test un.nxx1_table()
def test_nxx1_table_returns_the_correct_arrays(nxx1_table) -> None:
    # This is a regression test on Fabien Benreau's prototype
    file = np.load("tests/nxx1.npz")
    reference_xs = file["xs"]
    reference_conv = file["conv"]
    file.close()
    xs, conv = nxx1_table
    assert np.allclose(reference_xs, xs)
    assert np.allclose(reference_conv, conv)


# Test nxx1_interpolator() and nxx1()
def test_nxx1_equals_the_lookup_table(nxx1_table) -> None:
    unit = un.Unit()
    xs, conv = nxx1_table
    for i in range(0, xs.size, 50):
        assert math.isclose(unit.nxx1(xs[i]), conv[i])


def test_nxx1_equals_the_min_value_outside_the_min_bound(nxx1_table) -> None:
    unit = un.Unit()
    xs, conv = nxx1_table
    assert unit.nxx1(xs[0] - 1) == conv[0]


def test_nxx1_equals_the_max_value_outside_the_max_bound(nxx1_table) -> None:
    unit = un.Unit()
    xs, conv = nxx1_table
    assert unit.nxx1(xs[-1] + 1) == conv[-1]


# Test Unit class
def test_unit_init_uses_the_spec_you_pass_it() -> None:
    foo = sp.UnitSpec()
    unit = un.Unit(spec=foo)
    assert unit.spec is foo


def test_unit_init_can_make_a_defaut_spec_for_you() -> None:
    unit = un.Unit()
    assert unit.spec == sp.UnitSpec()


def test_unit_has_0_raw_un_input_at_first() -> None:
    unit = un.Unit()
    assert unit.net_raw == 0


def test_unit_can_add_inputs_to_the_raw_un_input() -> None:
    unit = un.Unit()
    unit.add_input(3)
    assert unit.net_raw == 3


def test_unit_can_update_its_membrane_potential() -> None:
    unit = un.Unit()
    unit.update_membrane_potential()


def test_unit_can_update_its_activation() -> None:
    unit = un.Unit()
    unit.update_activation()


def test_unit_can_observe_its_attributes() -> None:
    unit = un.Unit()
    assert unit.observe("act") == {"act": 0.0}


def test_unit_raises_valueerror_if_attr_is_unobservable() -> None:
    unit = un.Unit()
    with pytest.raises(ValueError):
        unit.observe("banannas")


def test_unit_can_calculate_the_inhibition_to_put_it_at_threshold() -> None:
    unit = un.Unit()
    unit.add_input(3)
    unit.update_net()
    unit.update_inhibition(unit.g_i_thr())

    for i in range(200):
        unit.update_membrane_potential()

    assert math.isclose(unit.v_m, unit.spec.spk_thr, rel_tol=1e-4)

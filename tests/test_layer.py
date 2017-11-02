"""Test layer.py"""
import pytest

from leabra7 import layer as lr
from leabra7 import specs as sp
from leabra7 import unit as un


def test_layer_init_uses_the_spec_you_pass_it():
    spec = sp.LayerSpec()
    layer = lr.Layer(name="in", spec=spec, size=1)
    assert layer.spec is spec


def test_layer_has_a_name():
    layer = lr.Layer(name="in", size=1)
    assert layer.name == "in"


def test_layer_has_a_size():
    layer = lr.Layer(name="in", size=1)
    assert layer.size == 1


def test_layer_has_a_list_of_units():
    layer = lr.Layer(name="in", size=3)
    assert len(layer.units) == 3
    for unit in layer.units:
        assert isinstance(unit, un.Unit)


def test_layer_should_be_able_to_compute_its_average_activation():
    layer = lr.Layer(name="in", size=2)
    layer.units[0].act = 0
    layer.units[1].act = 1
    assert layer.avg_act() == 0.5


def test_layer_should_be_able_to_compute_its_average_net_input():
    layer = lr.Layer(name="in", size=2)
    layer.units[0].net = 0
    layer.units[1].net = 1
    assert layer.avg_net() == 0.5


def test_layer_should_be_able_to_update_its_units_net_input(mocker):
    layer = lr.Layer(name="in", size=3)
    layer.units = [mocker.Mock() for _ in range(3)]
    layer.update_net()
    for u in layer.units:
        u.update_net.assert_called_once()


def test_layer_should_be_able_to_update_its_units_inhibition(mocker):
    layer = lr.Layer(name="in", size=3)
    layer.update_inhibition()

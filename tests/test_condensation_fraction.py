"""Regression tests for cfrac propagation; no opacity database needed."""
from unittest.mock import Mock
import numpy as np
import pandas as pd
import pytest
from picaso import justdoit as jdi


def bundle(profile):
    obj = object.__new__(jdi.inputs)
    obj.inputs = {'clouds': {}, 'climate': {}, 'calculation': 'browndwarf climate',
                  'atmosphere': {'profile': profile},
                  'planet': {'gravity': 1e4, 'gravity_unit': 'cm/s**2'}}
    obj.clouds = Mock()
    return obj


def test_stages_fraction_for_climate_updates():
    obj = bundle(pd.DataFrame({'pressure': [0.1, 1]}))
    obj.virga(['H2O'], '/unused', condensation_fraction=0.03)
    assert obj.inputs['climate']['virga_kwargs']['condensation_fraction'] == 0.03


@pytest.mark.parametrize('fraction', [0, 0.03, 1])
def test_forwards_to_virga_and_repeated_cloud_updates(monkeypatch, fraction):
    atmosphere = Mock()
    constructor = Mock(return_value=atmosphere)
    monkeypatch.setattr(jdi.vj, 'Atmosphere', constructor)
    monkeypatch.setattr(jdi.vj, 'compute', Mock(return_value={
        'opd_per_layer': np.ones((1, 1)), 'single_scattering': np.ones((1, 1)),
        'asymmetry': np.zeros((1, 1)), 'pressure': np.array([0.3]), 'wave': np.array([4.5])}))
    monkeypatch.setattr(jdi.vj, 'picaso_format', Mock(return_value=pd.DataFrame()))
    obj = bundle(pd.DataFrame({'pressure': [0.1, 1], 'temperature': [200, 250], 'kz': [1e7, 1e7]}))
    obj.virga(['H2O'], '/unused', condensation_fraction=fraction)
    staged = {k: v for k, v in obj.inputs['climate']['virga_kwargs'].items() if not k.startswith('patchy_')}
    obj.virga(**staged)
    assert constructor.call_count == 2
    assert all(call.kwargs['condensation_fraction'] == fraction for call in constructor.call_args_list)


@pytest.mark.parametrize('fraction', [-0.1, 1.1, float('nan'), float('inf')])
def test_rejects_invalid_fraction(fraction):
    with pytest.raises(ValueError, match='condensation_fraction'):
        bundle(pd.DataFrame()).virga(['H2O'], '/unused', condensation_fraction=fraction)


def test_default_is_full_condensation():
    obj = bundle(pd.DataFrame())
    obj.virga(['H2O'], '/unused')
    assert obj.inputs['climate']['virga_kwargs']['condensation_fraction'] == 1

# -*- coding: utf-8 -*-
"""
test_f1783_framework_qualification_and_evidence_correction.py
Task F1783 Verification Suite:
Validates the source-level corrections required by supervisory review HND-F1782-GENERALIZATION-AND-ADAPTIVITY-001:
1. Elimination of silent fixed-hole coordinate fallbacks from Cases 3, 5, and 2.
2. Dynamic derivation of pin-hole reference points and boundary sets from configured geometry definitions.
3. Negative test detecting stale loading coordinates when pin positions change.
4. Propagation of all sizing-envelope parameters through build_envelope_from_config and CLI.
5. Consistent error-target unit convention between sizing synthesis and Abaqus RemeshingRule.
"""
import os
import sys
import copy
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(os.path.join(REPO_ROOT, "scripts", "remeshing"))

from reusable_2d_adaptive_framework import (
    AdaptiveConfig, get_geometry_adapter,
    NotchedPlateWithPinHolesAdapter, SevenHolePlateAdapter, OffAxisHoleMode1Adapter,
    AdvancingDamageEnvelopeBuilder
)


def test_case3_silent_fallback_eliminated():
    """Verify that omitting geometry.voids in Case 3 raises ValueError in normal configured operation."""
    cfg_path = os.path.join(REPO_ROOT, "configs", "remeshing", "f1728_case3_notched_plate_pins.json")
    cfg = AdaptiveConfig.from_json(cfg_path)
    data = copy.deepcopy(cfg.raw)
    data["geometry"]["voids"] = []
    data["loading"].pop("upper_hole_center", None)
    data["loading"].pop("lower_hole_center", None)
    data["geometry"]["allow_legacy_geometry_defaults"] = False

    with pytest.raises(ValueError, match="Missing required pin hole definitions in geometry.voids"):
        AdaptiveConfig(data)

    # Allow legacy defaults when explicitly enabled
    data["geometry"]["allow_legacy_geometry_defaults"] = True
    cfg_leg = AdaptiveConfig(data)
    ad_leg = get_geometry_adapter(cfg_leg)
    assert len(ad_leg.get_hole_definitions()) == 3
    assert ad_leg.get_hole_definitions()[0] == (36.5, 51.0, 10.0)


def test_case5_silent_fallback_eliminated():
    """Verify that omitting geometry.voids in Case 5 raises ValueError in normal configured operation."""
    cfg_path = os.path.join(REPO_ROOT, "configs", "remeshing", "f1728_case5_seven_hole.json")
    cfg = AdaptiveConfig.from_json(cfg_path)
    data = copy.deepcopy(cfg.raw)
    data["geometry"]["voids"] = []
    data["geometry"]["allow_legacy_geometry_defaults"] = False

    with pytest.raises(ValueError, match="Missing required geometry definition 'geometry.voids'"):
        AdaptiveConfig(data)

    # Allow legacy defaults when explicitly enabled
    data["geometry"]["allow_legacy_geometry_defaults"] = True
    cfg_leg = AdaptiveConfig(data)
    ad_leg = get_geometry_adapter(cfg_leg)
    assert len(ad_leg.get_hole_definitions()) == 7


def test_case2_silent_fallback_eliminated():
    """Verify that omitting void definitions in Case 2 raises ValueError in normal configured operation."""
    cfg_path = os.path.join(REPO_ROOT, "configs", "remeshing", "f1728_case2_off_axis_hole.json")
    cfg = AdaptiveConfig.from_json(cfg_path)
    data = copy.deepcopy(cfg.raw)
    data["geometry"].pop("hole_center_x", None)
    data["geometry"].pop("hole_center_y", None)
    data["geometry"].pop("hole_radius", None)
    data["geometry"]["voids"] = []
    data["geometry"]["allow_legacy_geometry_defaults"] = False

    with pytest.raises(ValueError, match="Missing required geometry definition 'geometry.voids'"):
        AdaptiveConfig(data)

    # Allow legacy defaults when explicitly enabled
    data["geometry"]["allow_legacy_geometry_defaults"] = True
    cfg_leg = AdaptiveConfig(data)
    ad_leg = get_geometry_adapter(cfg_leg)
    assert ad_leg.get_hole_definitions() == [(0.65, 0.65, 0.10)]


def test_case3_stale_loading_coordinates_negative_test():
    """Negative test: verify that changing pin positions in geometry while retaining stale loading coordinates raises ValueError."""
    cfg_path = os.path.join(REPO_ROOT, "configs", "remeshing", "f1728_case3_notched_plate_pins.json")
    cfg = AdaptiveConfig.from_json(cfg_path)
    pert_data = copy.deepcopy(cfg.raw)
    # Move upper pin to (25.0, 105.0) in geometry.voids
    pert_data["geometry"]["voids"] = [
        {"name": "central_hole", "type": "circle", "x": 36.5, "y": 51.0, "r": 10.0},
        {"name": "lower_pin_hole", "type": "circle", "x": 20.0, "y": 20.0, "r": 5.0},
        {"name": "upper_pin_hole", "type": "circle", "x": 25.0, "y": 105.0, "r": 5.0}
    ]
    # Retain old stale coordinates in loading
    pert_data["loading"]["upper_hole_center"] = [20.0, 100.0]

    with pytest.raises(ValueError, match="Stale loading coordinates detected"):
        AdaptiveConfig(pert_data)


def test_case3_dynamic_pin_loading_derivation():
    """Verify that pin-hole reference points and boundary coordinates derive dynamically from configured geometry."""
    cfg_path = os.path.join(REPO_ROOT, "configs", "remeshing", "f1728_case3_notched_plate_pins.json")
    cfg = AdaptiveConfig.from_json(cfg_path)
    pert_data = copy.deepcopy(cfg.raw)
    # Shift both pins dynamically in geometry.voids
    pert_data["geometry"]["voids"] = [
        {"name": "central_hole", "type": "circle", "x": 36.5, "y": 51.0, "r": 10.0},
        {"name": "lower_pin_hole", "type": "circle", "x": 18.0, "y": 18.0, "r": 4.5},
        {"name": "upper_pin_hole", "type": "circle", "x": 22.0, "y": 102.0, "r": 5.5}
    ]
    # Remove loading center overrides so they derive dynamically
    pert_data["loading"].pop("upper_hole_center", None)
    pert_data["loading"].pop("lower_hole_center", None)

    cfg_pert = AdaptiveConfig(pert_data)
    assert cfg_pert.upper_hole_center == (22.0, 102.0)
    assert cfg_pert.upper_hole_radius == 5.5
    assert cfg_pert.lower_hole_center == (18.0, 18.0)
    assert cfg_pert.lower_hole_radius == 4.5
    assert cfg_pert.top_pin_hole["center"] == [22.0, 102.0]
    assert cfg_pert.bottom_pin_hole["center"] == [18.0, 18.0]


def test_build_envelope_parameter_propagation_and_unit_convention():
    """Verify that build_envelope_from_config propagates all parameters and uses consistent error-target percentage scale."""
    cfg_path = os.path.join(REPO_ROOT, "configs", "remeshing", "f1728_case1_mode1_edge_crack.json")
    cfg = AdaptiveConfig.from_json(cfg_path)

    # Mock build_envelope_odb to intercept keyword arguments
    intercepted_kwargs = {}

    def mock_build_envelope_odb(*args, **kwargs):
        intercepted_kwargs.update(kwargs)
        return kwargs.get("target_odb_path")

    orig_method = AdvancingDamageEnvelopeBuilder.build_envelope_odb
    AdvancingDamageEnvelopeBuilder.build_envelope_odb = staticmethod(mock_build_envelope_odb)

    try:
        AdvancingDamageEnvelopeBuilder.build_envelope_from_config(
            config=cfg,
            source_odb_path="dummy_src.odb",
            target_odb_path="dummy_dst.odb"
        )
        assert intercepted_kwargs["l0"] == cfg.l0
        assert intercepted_kwargs["h_bg"] == cfg.h_bg
        assert intercepted_kwargs["error_target"] == cfg.error_target, (
            "error_target unit convention mismatch: expected identical percentage scale %f, got %f" %
            (cfg.error_target, intercepted_kwargs["error_target"])
        )
        assert intercepted_kwargs["core_factor"] == cfg.core_factor
        assert intercepted_kwargs["process_factor"] == cfg.process_factor
        assert intercepted_kwargs["d_core"] == cfg.d_core
        assert intercepted_kwargs["d_proc"] == cfg.d_proc
        assert intercepted_kwargs["d_noise"] == cfg.d_noise
        assert intercepted_kwargs["frame_stride"] == cfg.frame_stride
    finally:
        AdvancingDamageEnvelopeBuilder.build_envelope_odb = orig_method

import inspect
from unittest.mock import Mock, patch

import pytest

from slac_devices.reader import create_wire
from slac_devices.wire import WireMetadata

WSBP2 = {
    "controls_information": {
        "control_name": "WSBP2",
        "PVs": {
            "abort_scan": "WSBP2:MOTR.STOP",
            "beam_rate": "WSBP2:BEAMRATE",
            "enabled": "WSBP2:MOTR_ENABLED_STS",
            "homed": "WSBP2:MOTR_HOMED_STS",
            "initialize": "WSBP2:MOTR_INIT",
            "initialize_status": "WSBP2:MOTR_INIT_STS",
            "install_angle": "WSBP2:INSTALL_ANGLE",
            "motor": "WSBP2:MOTR",
            "motor_rbv": "WSBP2:MOTR.RBV",
            "mps_speed": "WSBP2:MPS_SPEED",
            "on_status": "WSBP2:MOTR_ON_STS",
            "retract": "WSBP2:MOTR_RETRACT",
            "scan_pulses": "WSBP2:SCANPULSES",
            "speed": "WSBP2:MOTR.VELO",
            "speed_max": "WSBP2:MOTR.VMAX",
            "speed_min": "WSBP2:MOTR.VBAS",
            "start_scan": "WSBP2:STARTSCAN",
            "temperature": "WSBP2:TEMP",
            "timeout": "WSBP2:MOTR_TIMEOUTEN",
            "torque_enable": "WSBP2:TORQUE_ENABLE",
            "use_u_wire": "WSBP2:USEUWIRE",
            "use_x_wire": "WSBP2:USEXWIRE",
            "use_y_wire": "WSBP2:USEYWIRE",
            "u_size": "WSBP2:UWIRESIZE",
            "u_wire_inner": "WSBP2:UWIREINNER",
            "u_wire_outer": "WSBP2:UWIREOUTER",
            "x_size": "WSBP2:XWIRESIZE",
            "x_wire_inner": "WSBP2:XWIREINNER",
            "x_wire_outer": "WSBP2:XWIREOUTER",
            "y_size": "WSBP2:YWIRESIZE",
            "y_wire_inner": "WSBP2:YWIREINNER",
            "y_wire_outer": "WSBP2:YWIREOUTER",
        },
    },
    "metadata": {
        "area": "BYP",
        "beam_path": ["LCLS"],
        "sum_l_meters": 0.0,
        "type": "PROF",
        "wire_type": "C",
        "detectors": ["DET1"],
        "default_detector": "DET1",
    },
}

# ctrl options every PV reports, so the wire is constructed with all of them
CTRL_OPTIONS = {
    "MOTR.VELO": None,
    "BEAMRATE": None,
    "MOTR.VMAX": None,
    "MOTR.VBAS": None,
    "MOTR.RBV": None,
    "MOTR_INIT": None,
    "MOTR_INIT_STS": None,
    "MOTR_RETRACT": None,
    "MOTR": None,
    "MOTR_ON_STS": None,
    "STARTSCAN": None,
    "USEXWIRE": None,
    "USEYWIRE": None,
    "USEUWIRE": None,
    "XWIREINNER": None,
    "XWIREOUTER": None,
    "YWIREINNER": None,
    "YWIREOUTER": None,
    "UWIREINNER": None,
    "UWIREOUTER": None,
    "MOTR_ENABLED_STS": None,
    "MOTR_HOMED_STS": None,
}


@pytest.fixture
def mock_pv(mock_ctrlvars):
    """Mock slac_db, PV ctrl options and the PV class so every PV the wire
    builds is a mock. Yields the instance each PV() returns.
    """
    mock_ctrlvars.return_value = {"enum_strs": tuple(CTRL_OPTIONS.keys())}
    with (
        patch("slac_db.get_device", new_callable=Mock, return_value=WSBP2),
        patch("slac_tools.lazy_pv.PV", autospec=True) as mock_pv_class,
    ):
        pv = mock_pv_class.return_value
        # Default fast return so accessing properties during init doesn't block
        pv.get.return_value = 0
        yield pv


@pytest.fixture
def wire(mock_pv):
    return create_wire(area="BYP", name="WSBP2")


def test_properties_exist(wire) -> None:
    """Test that all the properties we expect exist"""
    # Assert that wire has all auto-generated private attributes
    for handle, pv in wire.controls_information.PVs:
        # Some optional PV-backed properties (e.g., scan_status) are
        # intentionally unavailable when the backing PV is not configured.
        if handle not in ["position"] and pv is not None:
            assert hasattr(wire, handle), f"expected wire to have attribute {handle}"
    for item, _ in wire.metadata:
        assert hasattr(wire.metadata, item), f"expected wire to have attribute {item}"
    # Assert that magnet has public properties
    for item in [
        "abort_scan",
        "beam_rate",
        "enabled",
        "homed",
        "initialize",
        "initialize_status",
        "motor",
        "motor_rbv",
        "retract",
        "scan_pulses",
        "speed",
        "start_scan",
        "temperature",
        "timeout",
        "use_u_wire",
        "use_x_wire",
        "use_y_wire",
        "u_size",
        "u_wire_inner",
        "u_wire_outer",
        "x_size",
        "x_wire_inner",
        "x_wire_outer",
        "y_size",
        "y_wire_inner",
        "y_wire_outer",
    ]:
        assert hasattr(wire, item), f"expected wire to have attribute {item}"


def test_methods(wire) -> None:
    """Test that all the methods we expect exist"""
    assert inspect.ismethod(wire.abort_scan)
    assert inspect.ismethod(wire.initialize)
    assert inspect.ismethod(wire.position_buffer)
    assert inspect.ismethod(wire.retract)
    assert inspect.ismethod(wire.start_scan)
    assert inspect.ismethod(wire.set_range)
    assert inspect.ismethod(wire.use)
    assert inspect.ismethod(wire.active_profiles)


def test_active_profiles_returns_enabled_planes(wire, mock_pv):
    mock_pv.get.side_effect = [1, 0, True]
    assert wire.active_profiles() == ["x", "u"]
    mock_pv.get.side_effect = None


def test_name(wire) -> None:
    """Test we get expected default"""
    assert wire.name == "WSBP2"


def test_area(wire) -> None:
    """Test we get expected default"""
    assert wire.area == "BYP"


@pytest.mark.parametrize(
    "prop",
    [
        "enabled",
        "beam_rate",
        "homed",
        "on_status",
        "initialize_status",
        "motor",
        "motor_rbv",
        "scan_pulses",
        "speed",
        "speed_max",
        "speed_min",
        "temperature",
        "timeout",
        "x_size",
        "y_size",
        "u_size",
        "use_x_wire",
        "x_wire_inner",
        "x_wire_outer",
        "use_y_wire",
        "y_wire_inner",
        "y_wire_outer",
        "use_u_wire",
        "u_wire_inner",
        "u_wire_outer",
    ],
)
def test_all_properties(wire, mock_pv, prop):
    """Verify all PV-backed Wire properties call PV.get() and return the mocked value."""
    # reset the mock to avoid call overlaps
    mock_pv.get.reset_mock()
    mock_pv.get.return_value = 123  # something arbitrary

    result = getattr(wire, prop)
    assert result == 123, f"{prop} should return mocked value"
    mock_pv.get.assert_called_once()


def test_metadata_exists_and_type(wire):
    """Wire has a valid metadata object"""
    assert hasattr(wire, "metadata")
    assert isinstance(wire.metadata, WireMetadata)


def test_metadata_has_detectors_list(wire):
    m = wire.metadata
    assert hasattr(m, "detectors")
    assert isinstance(m.detectors, list)

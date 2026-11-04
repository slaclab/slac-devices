import os
from unittest.mock import MagicMock, patch

import pytest

from slac_devices.area import Area
from slac_devices.magnet import Magnet, MagnetCollection
from slac_devices.reader import create_area, create_magnet

CONFIG_LOCATION = "./tests/datasets/devices/config/magnet/"
BAD_CONFIG = os.path.join(CONFIG_LOCATION, "bad_magnet.yaml")


@pytest.fixture
def ctrlvars_ready(mock_ctrlvars):
    """Construct each magnet with ALL ctrl options."""
    mock_ctrlvars.return_value = {"enum_strs": tuple("READY")}
    return mock_ctrlvars


@pytest.mark.usefixtures("ctrlvars_ready")
class TestMagnetReader:
    def test_bad_file_location_when_creating_magnet_returns_none(self):
        assert create_magnet("bad-area") is None

    def test_no_file_location_when_creating_magnet_returns_none(self):
        assert create_magnet() is None

    def test_magnet_name_not_in_file_when_creating_magnet_returns_none(self):
        assert create_magnet(area="GUNB", name="BAD-MAGNET-NAME") is None

    @patch(
        "slac_db.get_yaml",
        new_callable=MagicMock(),
    )
    def test_config_with_no_control_information_returns_none(self, mock_get_yaml):
        mock_get_yaml.return_value = BAD_CONFIG
        assert create_magnet(area="GUNX", name="CQ02B") is None

    @patch(
        "slac_db.get_yaml",
        new_callable=MagicMock(),
    )
    def test_config_with_no_metadata_returns_none(self, mock_get_yaml):
        mock_get_yaml.return_value = BAD_CONFIG
        assert create_magnet(area="GUNX", name="SOL1B") is None

    def test_create_magnet_with_only_config_creates_all_magnets(self):
        result = create_magnet(area="GUNB")
        assert isinstance(result, MagnetCollection)
        for name in [
            "SOL2B",
            "SOL1B",
        ]:
            assert name in result.magnets, f"expected {name} in {result}."
            assert isinstance(result.magnets[name], Magnet)

    def test_create_magnet_with_config_and_name_creates_one_magnet(self):
        name = "SOL1B"
        result = create_magnet(
            area="GUNB",
            name=name,
        )
        assert not isinstance(result, MagnetCollection)
        assert isinstance(result, Magnet)


class TestAreaReader:
    def test_create_area_keeps_valid_devices_when_one_is_invalid(self):
        valid_bpm = {
            "controls_information": {
                "PVs": {
                    "tmit": "BPMS:DIAG0:190:TMIT",
                    "x": "BPMS:DIAG0:190:X",
                    "y": "BPMS:DIAG0:190:Y",
                },
                "control_name": "BPMS:DIAG0:190",
            },
            "metadata": {
                "area": "DIAG0",
                "beam_path": ["SC_DIAG0"],
                "sum_l_meters": 46.232,
                "type": "BPM",
            },
        }
        invalid_bpm = {
            "controls_information": {
                "PVs": {
                    "tmit": "BPMS:DIAG0:999:TMIT",
                    "x": "BPMS:DIAG0:999:X",
                    "y": "BPMS:DIAG0:999:Y",
                },
                "control_name": "BPMS:DIAG0:999",
            }
        }

        with patch("slac_devices.reader.slac_db.get_device") as mock_get_device:
            mock_get_device.return_value = {
                "bpms": {
                    "GOOD": valid_bpm,
                    "BAD": invalid_bpm,
                }
            }
            result = create_area(area="DIAG0")

        assert isinstance(result, Area)
        assert "GOOD" in result.bpms
        assert "BAD" not in result.bpms

    def test_create_area_returns_area_when_all_devices_invalid(self):
        invalid_bpm = {
            "controls_information": {
                "PVs": {
                    "tmit": "BPMS:DIAG0:999:TMIT",
                    "x": "BPMS:DIAG0:999:X",
                    "y": "BPMS:DIAG0:999:Y",
                },
                "control_name": "BPMS:DIAG0:999",
            }
        }

        with patch("slac_devices.reader.slac_db.get_device") as mock_get_device:
            mock_get_device.return_value = {
                "bpms": {
                    "BAD": invalid_bpm,
                }
            }
            result = create_area(area="DIAG0")

        assert isinstance(result, Area)
        assert result.bpms is None

    @patch("epics.PV.get_ctrlvars", new_callable=MagicMock)
    def test_create_area_supports_tcavs(self, mock_get_ctrlvars):
        mock_get_ctrlvars.return_value = {"enum_strs": ("OFF", "ON")}
        with patch("slac_devices.reader.slac_db.get_device") as mock_get_device:
            mock_get_device.return_value = {
                "tcavs": {
                    "TCAV0": {
                        "controls_information": {
                            "PVs": {
                                "amplitude": "TCAV:LI30:TCAV0:AMPLITUDE",
                                "phase": "TCAV:LI30:TCAV0:PHASE",
                                "rf_enable": "TCAV:LI30:TCAV0:RF_ENABLE",
                                "amplitude_fbenb": "TCAV:LI30:TCAV0:AMPL_FB_ENB",
                                "phase_fbenb": "TCAV:LI30:TCAV0:PHASE_FB_ENB",
                                "amplitude_fbst": "TCAV:LI30:TCAV0:AMPL_FB_ST",
                                "phase_fbst": "TCAV:LI30:TCAV0:PHASE_FB_ST",
                                "mode_config": "TCAV:LI30:TCAV0:MODE_CONFIG",
                                "amplitude_wocho": "TCAV:LI30:TCAV0:AMPL_WOCHO",
                                "phase_avgnt": "TCAV:LI30:TCAV0:PHASE_AVGNT",
                            },
                            "control_name": "TCAV:LI30:TCAV0",
                        },
                        "metadata": {
                            "area": "LI30",
                            "beam_path": ["CU_HXR"],
                            "sum_l_meters": 1000.0,
                            "type": "TCAV",
                            "l_eff": 1.2,
                            "rf_freq": 2856.0,
                        },
                    }
                }
            }
            result = create_area(area="LI30")

        assert isinstance(result, Area)
        assert result.tcavs is not None
        assert "TCAV0" in result.tcavs

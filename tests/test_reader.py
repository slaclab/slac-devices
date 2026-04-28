import slac_db
from slac_devices.reader import create_magnet, create_area
from slac_devices.magnet import Magnet, MagnetCollection
from slac_devices.area import Area
import unittest
from unittest.mock import patch, MagicMock
import os


class TestMagnetReader(unittest.TestCase):
    def setUp(self) -> None:
        self.config_location = "./tests/datasets/devices/config/magnet/"
        self.typical_config = os.path.join(self.config_location, "typical_magnet.yaml")
        self.bad_config = os.path.join(self.config_location, "bad_magnet.yaml")
        # set up patch so that each magnet is constructured with ALL ctrl options
        self.ctrl_options_patch = patch("epics.PV.get_ctrlvars", new_callable=MagicMock)
        self.mock_ctrl_options = self.ctrl_options_patch.start()
        self.mock_ctrl_options.return_value = {"enum_strs": tuple("READY")}
        return super().setUp()

    def test_bad_file_location_when_creating_magnet_returns_none(self):
        self.assertIsNone(create_magnet("bad-area"))

    def test_no_file_location_when_creating_magnet_returns_none(self):
        self.assertIsNone(create_magnet())

    def test_magnet_name_not_in_file_when_creating_magnet_returns_none(self):
        self.assertIsNone(create_magnet(area="GUNB", name="BAD-MAGNET-NAME"))

    @patch(
        "slac_db.get_yaml",
        new_callable=MagicMock(),
    )
    def test_config_with_no_control_information_returns_none(self, mock_get_yaml):
        mock_get_yaml.return_value = self.bad_config
        self.assertIsNone(create_magnet(area="GUNX", name="CQ02B"))

    @patch(
        "slac_db.get_yaml",
        new_callable=MagicMock(),
    )
    def test_config_with_no_metadata_returns_none(self, mock_get_yaml):
        mock_get_yaml.return_value = self.bad_config
        self.assertIsNone(create_magnet(area="GUNX", name="SOL1B"))

    def test_create_magnet_with_only_config_creates_all_magnets(self):
        result = create_magnet(area="GUNB")
        self.assertIsInstance(result, MagnetCollection)
        for name in [
            "SOL2B",
            "SOL1B",
        ]:
            self.assertIn(name, result.magnets, msg=f"expected {name} in {result}.")
            self.assertIsInstance(result.magnets[name], Magnet)

    def test_create_magnet_with_config_and_name_creates_one_magnet(self):
        name = "SOL1B"
        result = create_magnet(
            area="GUNB",
            name=name,
        )
        self.assertNotIsInstance(result, MagnetCollection)
        self.assertIsInstance(result, Magnet)


class TestAreaReader(unittest.TestCase):
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

        self.assertIsInstance(result, Area)
        self.assertIn("GOOD", result.bpms)
        self.assertNotIn("BAD", result.bpms)

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

        self.assertIsInstance(result, Area)
        self.assertIsNone(result.bpms)

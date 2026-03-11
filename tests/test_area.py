import unittest
import yaml
from copy import deepcopy
from slac_devices.area import Area
from slac_devices.screen import Screen
from pathlib import Path


class TestArea(unittest.TestCase):
    def setUp(self) -> None:
        self.config_location = (
            Path(__file__).parent / "test_data" / "config"
        )
        with open(
            self.config_location / "screen" / "typical_screen.yaml", "r"
        ) as file:
            self.screen_data = yaml.safe_load(file)
        return super().setUp()

    def tearDown(self) -> None:
        return super().tearDown()

    def test_area_with_no_magnets(self):
        area = Area(
            name="mock_area", screens=self.screen_data
        )
        self.assertIsNone(area.magnet_collection)
        self.assertIsNone(area.magnets)

    def test_area_repr_with_screens(self):
        area = Area(
            name="mock_area", screens=self.screen_data
        )
        result = repr(area)
        self.assertIn("mock_area", result)
        self.assertIn("screens=1", result)
        self.assertNotIn("magnets", result)

    def test_area_repr_with_no_devices(self):
        area = Area(name="empty_area")
        self.assertEqual(repr(area), "Area(name='empty_area')")

    def test_area_tolerates_single_bad_screen_and_records_error(self):
        bad_screen_data = deepcopy(self.screen_data)
        good_name = next(iter(bad_screen_data.keys()))
        bad_name = "BROKEN_SCREEN"
        bad_screen_data[bad_name] = deepcopy(bad_screen_data[good_name])
        del bad_screen_data[bad_name]["controls_information"]["PVs"][
            "sys_type"
        ]

        area = Area(name="mixed_area", screens=bad_screen_data)

        self.assertIsNotNone(area.screens)
        self.assertIn(good_name, area.screens)
        self.assertNotIn(bad_name, area.screens)
        self.assertIn("screens", area.validation_errors)
        self.assertIn(bad_name, area.validation_errors["screens"])
        self.assertIsInstance(area.screens[good_name], Screen)

    def test_does_device_exist_is_safe_when_collection_missing(self):
        area = Area(name="empty_area")
        self.assertFalse(area.does_magnet_exist("M1"))
        self.assertFalse(area.does_screen_exist("S1"))

import unittest
import yaml
from slac_devices.area import Area
from pathlib import Path


class TestArea(unittest.TestCase):
    def setUp(self) -> None:
        self.config_location = (
            Path(__file__).parent / "test_data" / "config"
        )
        return super().setUp()

    def tearDown(self) -> None:
        return super().tearDown()

    def test_area_with_no_magnets(self):
        mock_screen_data = {"screens": {}}
        with open(
            self.config_location / "screen" / "typical_screen.yaml", "r"
        ) as file:
            mock_screen_data["screens"] = yaml.safe_load(file)
        area = Area(name="mock_area", **mock_screen_data)
        self.assertIsNone(area.magnet_collection)
        self.assertIsNone(area.magnets)

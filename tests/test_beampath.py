import unittest
import yaml
from copy import deepcopy
from pathlib import Path

from slac_devices.area import Area
from slac_devices.beampath import Beampath


class TestBeampath(unittest.TestCase):
    def setUp(self) -> None:
        config_location = (
            Path(__file__).parent / "test_data" / "config"
        )
        with open(
            config_location / "screen" / "typical_screen.yaml", "r"
        ) as file:
            screen_data = yaml.safe_load(file)

        # Two areas: each with one screen under a distinct name so flat
        # accessors can be tested for cross-area merging.
        screen_name = list(screen_data.keys())[0]  # e.g. "OTR21"
        self.screen_name_1 = screen_name
        self.screen_name_2 = screen_name + "_2"

        area1 = Area(
            name="AREA1",
            screens={self.screen_name_1: screen_data[screen_name]},
        )
        area2 = Area(
            name="AREA2",
            screens={self.screen_name_2: screen_data[screen_name]},
        )
        self.beampath = Beampath(
            name="TEST_BP",
            areas={"AREA1": area1, "AREA2": area2},
        )
        return super().setUp()

    def tearDown(self) -> None:
        return super().tearDown()

    # --- area_names ---

    def test_area_names_returns_all_areas(self):
        self.assertEqual(
            sorted(self.beampath.area_names), ["AREA1", "AREA2"]
        )

    # --- contains_areas ---

    def test_contains_areas_with_string_present(self):
        result = self.beampath.contains_areas("AREA1")
        self.assertEqual(result, {"AREA1": True})

    def test_contains_areas_with_string_absent(self):
        result = self.beampath.contains_areas("MISSING")
        self.assertEqual(result, {"MISSING": False})

    def test_contains_areas_with_list(self):
        result = self.beampath.contains_areas(["AREA1", "MISSING"])
        self.assertEqual(result, {"AREA1": True, "MISSING": False})

    # --- flat accessors ---

    def test_screens_returns_devices_from_all_areas(self):
        screens = self.beampath.screens
        self.assertIn(self.screen_name_1, screens)
        self.assertIn(self.screen_name_2, screens)
        self.assertEqual(len(screens), 2)

    def test_magnets_returns_empty_dict_when_none_configured(self):
        self.assertEqual(self.beampath.magnets, {})

    def test_bpms_returns_empty_dict_when_none_configured(self):
        self.assertEqual(self.beampath.bpms, {})

    def test_tcavs_returns_empty_dict_when_none_configured(self):
        self.assertEqual(self.beampath.tcavs, {})

    # --- find ---

    def test_find_returns_device_when_present(self):
        device = self.beampath.find(self.screen_name_1)
        self.assertIsNotNone(device)

    def test_find_returns_none_when_absent(self):
        result = self.beampath.find("DOES_NOT_EXIST")
        self.assertIsNone(result)

    # --- __repr__ ---

    def test_repr_contains_name(self):
        self.assertIn("TEST_BP", repr(self.beampath))

    def test_repr_contains_area_count(self):
        self.assertIn("areas=2", repr(self.beampath))

    def test_repr_contains_screen_count(self):
        self.assertIn("screens=2", repr(self.beampath))

    # --- validation_errors ---

    def test_validation_errors_is_empty_when_areas_are_clean(self):
        self.assertEqual(self.beampath.validation_errors, {})

    def test_validation_errors_aggregates_failures_by_area(self):
        config_location = (
            Path(__file__).parent / "test_data" / "config"
        )
        with open(
            config_location / "screen" / "typical_screen.yaml", "r"
        ) as file:
            screen_data = yaml.safe_load(file)

        good_name = next(iter(screen_data.keys()))
        bad_name = "BROKEN_SCREEN"
        mixed_screens = deepcopy(screen_data)
        mixed_screens[bad_name] = deepcopy(screen_data[good_name])
        del mixed_screens[bad_name]["controls_information"]["PVs"][
            "sys_type"
        ]

        bad_area = Area(name="BAD_AREA", screens=mixed_screens)
        good_area = Area(
            name="GOOD_AREA",
            screens={good_name: screen_data[good_name]},
        )
        beampath = Beampath(
            name="BP_WITH_ERRORS",
            areas={
                "GOOD_AREA": good_area,
                "BAD_AREA": bad_area,
            },
        )

        self.assertIn("BAD_AREA", beampath.validation_errors)
        self.assertIn(
            "screens",
            beampath.validation_errors["BAD_AREA"],
        )
        self.assertIn(
            bad_name,
            beampath.validation_errors["BAD_AREA"]["screens"],
        )
        self.assertNotIn("GOOD_AREA", beampath.validation_errors)

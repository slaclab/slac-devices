import unittest
from unittest.mock import patch, MagicMock

from slac_devices.beampath import Beampath
from slac_devices.area import Area
from slac_devices.magnet import Magnet, MagnetCollection
from slac_devices.screen import Screen, ScreenCollection
from slac_devices.wire import Wire, WireCollection
from slac_devices.bpm import BPM, BPMCollection


class TestBeampathRepr(unittest.TestCase):
    """Test Beampath __repr__ method."""

    def test_beampath_repr_empty_areas(self):
        """Test __repr__ for beampath with no areas."""
        bp = Beampath.model_construct(name="TEST_BP", areas=None)
        repr_str = repr(bp)
        self.assertIn("TEST_BP", repr_str)
        self.assertIn("areas=[]", repr_str)

    def test_beampath_repr_with_areas(self):
        """Test __repr__ shows area info and device counts."""
        # Create minimal area
        area = Area.model_construct(
            name="AREA1", magnet_collection=MagnetCollection.model_construct(magnets={})
        )

        bp = Beampath.model_construct(name="TEST_BP", areas={"AREA1": area})
        repr_str = repr(bp)

        self.assertIn("TEST_BP", repr_str)
        self.assertIn("num_areas", repr_str)
        self.assertIn("total_devices", repr_str)
        self.assertIn("populated_types", repr_str)


class TestBeampathDeviceCounts(unittest.TestCase):
    """Test Beampath device counting."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_magnet_pv_patch = patch("epics.PV.get_ctrlvars")
        self.mock_ctrl = self.mock_magnet_pv_patch.start()
        self.mock_ctrl.return_value = {"enum_strs": tuple("READY")}

    def tearDown(self):
        self.mock_magnet_pv_patch.stop()

    def test_device_counts_empty_beampath(self):
        """Test _device_counts for empty beampath."""
        bp = Beampath.model_construct(name="EMPTY_BP", areas=None)
        counts = bp._device_counts()
        self.assertEqual(sum(counts.values()), 0)

    def test_device_counts_aggregates_across_areas(self):
        """Test _device_counts sums devices from all areas."""
        area1 = Area.model_construct(
            name="AREA1",
            magnet_collection=MagnetCollection.model_construct(
                magnets={"M1": MagicMock()}
            ),
        )
        area2 = Area.model_construct(
            name="AREA2",
            magnet_collection=MagnetCollection.model_construct(
                magnets={"M2": MagicMock(), "M3": MagicMock()}
            ),
        )

        bp = Beampath.model_construct(
            name="TEST_BP", areas={"AREA1": area1, "AREA2": area2}
        )

        counts = bp._device_counts()
        self.assertEqual(counts["magnets"], 3)


class TestBeampathFindDevice(unittest.TestCase):
    """Test Beampath device finding."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_magnet_pv_patch = patch("epics.PV.get_ctrlvars")
        self.mock_ctrl = self.mock_magnet_pv_patch.start()
        self.mock_ctrl.return_value = {"enum_strs": tuple("READY")}

    def tearDown(self):
        self.mock_magnet_pv_patch.stop()

    def test_find_device_not_found(self):
        """Test find_device returns None when device doesn't exist."""
        mock_mag = MagicMock()
        mock_mag_collection = MagnetCollection.model_construct(magnets={"M1": mock_mag})
        area = Area.model_construct(
            name="AREA1",
            magnet_collection=mock_mag_collection,
        )
        bp = Beampath.model_construct(name="TEST_BP", areas={"AREA1": area})

        result = bp.find_device("NONEXISTENT")
        self.assertIsNone(result)

    def test_find_device_in_single_area(self):
        """Test find_device returns correct area and device."""
        mock_magnet = MagicMock(spec=Magnet)
        mock_mag_collection = MagnetCollection.model_construct(
            magnets={"M1": mock_magnet}
        )
        area = Area.model_construct(
            name="AREA1",
            magnet_collection=mock_mag_collection,
        )
        bp = Beampath.model_construct(name="TEST_BP", areas={"AREA1": area})

        result = bp.find_device("M1")
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "AREA1")  # area name
        self.assertEqual(result[1], "magnets")  # device type
        self.assertEqual(result[2], mock_magnet)  # device object

    def test_find_device_in_multiple_areas(self):
        """Test find_device finds correct device in multi-area beampath."""
        mock_magnet = MagicMock()
        mock_mag_collection = MagnetCollection.model_construct(
            magnets={"M1": mock_magnet}
        )

        mock_screen = MagicMock(spec=Screen)
        mock_screen_collection = ScreenCollection.model_construct(
            screens={"S1": mock_screen}
        )

        area1 = Area.model_construct(
            name="AREA1",
            magnet_collection=mock_mag_collection,
        )
        area2 = Area.model_construct(
            name="AREA2",
            screen_collection=mock_screen_collection,
        )
        bp = Beampath.model_construct(
            name="TEST_BP", areas={"AREA1": area1, "AREA2": area2}
        )

        result = bp.find_device("S1")
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "AREA2")
        self.assertEqual(result[1], "screens")

    def test_find_device_no_configured_areas(self):
        """Test find_device returns None gracefully when areas is None."""
        bp = Beampath(name="UNCONFIGURED")  # areas defaults to None
        result = bp.find_device("SOMETHING")
        self.assertIsNone(result)


class TestBeampathAggregationMethods(unittest.TestCase):
    """Test Beampath aggregation methods like get_all_magnets."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_magnet_pv_patch = patch("epics.PV.get_ctrlvars")
        self.mock_ctrl = self.mock_magnet_pv_patch.start()
        self.mock_ctrl.return_value = {"enum_strs": tuple("READY")}

    def tearDown(self):
        self.mock_magnet_pv_patch.stop()

    def test_get_all_magnets_empty(self):
        """Test get_all_magnets with no magnets."""
        area = Area.model_construct(name="AREA1")
        bp = Beampath.model_construct(name="TEST_BP", areas={"AREA1": area})

        magnets = bp.get_all_magnets()
        self.assertEqual(len(magnets), 0)

    def test_get_all_magnets_single_area(self):
        """Test get_all_magnets from single area."""
        mock_mag1 = MagicMock(spec=Magnet)
        mock_mag2 = MagicMock(spec=Magnet)
        area = Area.model_construct(
            name="AREA1",
            magnet_collection=MagnetCollection.model_construct(
                magnets={"M1": mock_mag1, "M2": mock_mag2}
            ),
        )
        bp = Beampath.model_construct(name="TEST_BP", areas={"AREA1": area})

        magnets = bp.get_all_magnets()
        self.assertEqual(len(magnets), 2)
        self.assertIn("M1", magnets)
        self.assertIn("M2", magnets)

    def test_get_all_magnets_multiple_areas(self):
        """Test get_all_magnets aggregates across areas."""
        mock_mag1 = MagicMock(spec=Magnet)
        mock_mag2 = MagicMock(spec=Magnet)
        mock_mag3 = MagicMock(spec=Magnet)

        area1 = Area.model_construct(
            name="AREA1",
            magnet_collection=MagnetCollection.model_construct(
                magnets={"M1": mock_mag1, "M2": mock_mag2}
            ),
        )
        area2 = Area.model_construct(
            name="AREA2",
            magnet_collection=MagnetCollection.model_construct(
                magnets={"M3": mock_mag3}
            ),
        )
        bp = Beampath.model_construct(
            name="TEST_BP", areas={"AREA1": area1, "AREA2": area2}
        )

        magnets = bp.get_all_magnets()
        self.assertEqual(len(magnets), 3)
        self.assertIn("M1", magnets)
        self.assertIn("M2", magnets)
        self.assertIn("M3", magnets)

    def test_get_all_wires(self):
        """Test get_all_wires aggregation."""
        mock_wire1 = MagicMock(spec=Wire)
        mock_wire2 = MagicMock(spec=Wire)

        area1 = Area.model_construct(
            name="AREA1",
            wire_collection=WireCollection.model_construct(wires={"W1": mock_wire1}),
        )
        area2 = Area.model_construct(
            name="AREA2",
            wire_collection=WireCollection.model_construct(wires={"W2": mock_wire2}),
        )
        bp = Beampath.model_construct(
            name="TEST_BP", areas={"AREA1": area1, "AREA2": area2}
        )

        wires = bp.get_all_wires()
        self.assertEqual(len(wires), 2)
        self.assertIn("W1", wires)
        self.assertIn("W2", wires)

    def test_get_all_bpms(self):
        """Test get_all_bpms aggregation."""
        mock_bpm = MagicMock(spec=BPM)

        area = Area.model_construct(
            name="AREA1",
            bpm_collection=BPMCollection.model_construct(bpms={"B1": mock_bpm}),
        )
        bp = Beampath.model_construct(name="TEST_BP", areas={"AREA1": area})

        bpms = bp.get_all_bpms()
        self.assertEqual(len(bpms), 1)
        self.assertIn("B1", bpms)

    def test_get_all_devices(self):
        """Test get_all_devices aggregates all device types."""
        mock_mag = MagicMock(spec=Magnet)
        mock_wire = MagicMock(spec=Wire)
        mock_screen = MagicMock(spec=Screen)

        area = Area.model_construct(
            name="AREA1",
            magnet_collection=MagnetCollection.model_construct(
                magnets={"M1": mock_mag}
            ),
            wire_collection=WireCollection.model_construct(wires={"W1": mock_wire}),
            screen_collection=ScreenCollection.model_construct(
                screens={"S1": mock_screen}
            ),
        )
        bp = Beampath.model_construct(name="TEST_BP", areas={"AREA1": area})

        all_devices = bp.get_all_devices()
        self.assertEqual(len(all_devices), 3)
        self.assertIn("M1", all_devices)
        self.assertIn("W1", all_devices)
        self.assertIn("S1", all_devices)


class TestBeampathProperties(unittest.TestCase):
    """Test Beampath properties (aliases for get_all_* methods)."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_magnet_pv_patch = patch("epics.PV.get_ctrlvars")
        self.mock_ctrl = self.mock_magnet_pv_patch.start()
        self.mock_ctrl.return_value = {"enum_strs": tuple("READY")}

    def tearDown(self):
        self.mock_magnet_pv_patch.stop()

    def test_all_magnets_property(self):
        """Test magnets property."""
        mock_mag = MagicMock(spec=Magnet)
        area = Area.model_construct(
            name="AREA1",
            magnet_collection=MagnetCollection.model_construct(
                magnets={"M1": mock_mag}
            ),
        )
        bp = Beampath.model_construct(name="TEST_BP", areas={"AREA1": area})

        magnets = bp.magnets
        self.assertEqual(len(magnets), 1)
        self.assertIn("M1", magnets)

    def test_all_wires_property(self):
        """Test wires property."""
        mock_wire = MagicMock(spec=Wire)
        area = Area.model_construct(
            name="AREA1",
            wire_collection=WireCollection.model_construct(wires={"W1": mock_wire}),
        )
        bp = Beampath.model_construct(name="TEST_BP", areas={"AREA1": area})

        wires = bp.wires
        self.assertEqual(len(wires), 1)
        self.assertIn("W1", wires)

    def test_all_devices_property(self):
        """Test devices property."""
        mock_mag = MagicMock(spec=Magnet)
        mock_wire = MagicMock(spec=Wire)

        area = Area.model_construct(
            name="AREA1",
            magnet_collection=MagnetCollection.model_construct(
                magnets={"M1": mock_mag}
            ),
            wire_collection=WireCollection.model_construct(wires={"W1": mock_wire}),
        )
        bp = Beampath.model_construct(name="TEST_BP", areas={"AREA1": area})

        all_devices = bp.devices
        self.assertEqual(len(all_devices), 2)
        self.assertIn("M1", all_devices)
        self.assertIn("W1", all_devices)


if __name__ == "__main__":
    unittest.main()

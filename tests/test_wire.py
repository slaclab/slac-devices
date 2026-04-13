# import datetime
from unittest import TestCase
from unittest.mock import Mock, patch  # , PropertyMock
import inspect


# Local imports
from slac_devices.reader import create_wire
from slac_devices.wire import WireMetadata


class WireTest(TestCase):
    def setUp(self) -> None:
        self.slac_db_patch = patch("slac_db.get_device", new_callable=Mock)
        self.mock_get_device = self.slac_db_patch.start()
        self.mock_get_device.return_value = {
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

        # 1) Patch PV ctrlvars before wire construction
        self.ctrl_options_patch = patch("epics.PV.get_ctrlvars", new_callable=Mock)
        self.mock_ctrl_options = self.ctrl_options_patch.start()

        # Set up some mocks that are needed for all test-cases.
        self.options_and_getter_function = {
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
        self.mock_ctrl_options.return_value = {
            "enum_strs": tuple(self.options_and_getter_function.keys())
        }

        # 2) Patch the PV class before wire construction so all PVs are mocks
        self.pv_class_patch = patch(
            "slac_devices.device.PV", autospec=True
        )
        self.mock_pv_class = self.pv_class_patch.start()

        # The instance every PV() call returns
        self.mock_pv = self.mock_pv_class.return_value

        # Default fast return so accessing properties during init doesn't block
        self.mock_pv.get.return_value = 0

        # 3) Now safe to create wire (all PVs will be mocked)
        self.wire = create_wire(area="BYP", name="WSBP2")

        self.options_and_getter_function = {
            "MOTR.STOP": self.wire.abort_scan,
            "BEAMRATE": self.wire.beam_rate,
            "MOTR_ENABLED_STS": self.wire.enabled,
            "MOTR_HOMED_STS": self.wire.homed,
            "MOTR_INIT": self.wire.initialize,
            "MOTR_INIT_STS": self.wire.initialize_status,
            "MOTR": self.wire.motor,
            "MOTR.RBV": self.wire.motor_rbv,
            "MOTR_ON_STS": self.wire.on_status,
            "MOTR_RETRACT": self.wire.retract,
            "SCANPULSES": self.wire.scan_pulses,
            "MOTR.VELO": self.wire.speed,
            "MOTR.VMAX": self.wire.speed_max,
            "MOTR.VBAS": self.wire.speed_min,
            "STARTSCAN": self.wire.start_scan,
            "TEMP": self.wire.temperature,
            "MOTR_TIMEOUTEN": self.wire.timeout,
            "USEUWIRE": self.wire.use_u_wire,
            "USEXWIRE": self.wire.use_x_wire,
            "USEYWIRE": self.wire.use_y_wire,
            "UWIRESIZE": self.wire.u_size,
            "UWIREINNER": self.wire.u_wire_inner,
            "UWIREOUTER": self.wire.u_wire_outer,
            "XWIRESIZE": self.wire.x_size,
            "XWIREINNER": self.wire.x_wire_inner,
            "XWIREOUTER": self.wire.x_wire_outer,
            "YWIRESIZE": self.wire.y_size,
            "YWIREINNER": self.wire.y_wire_inner,
            "YWIREOUTER": self.wire.y_wire_outer,
        }
        return super().setUp()

    def tearDown(self) -> None:
        self.slac_db_patch.stop()
        self.ctrl_options_patch.stop()
        self.pv_class_patch.stop()
        return super().tearDown()

    def test_properties_exist(self) -> None:
        """Test that all the properties we expect exist"""
        # Assert that wire has all auto-generated private attributes
        for handle, pv in self.wire.controls_information.PVs:
            # Some optional PV-backed properties (e.g., scan_status) are
            # intentionally unavailable when the backing PV is not configured.
            if handle not in ["position"] and pv is not None:
                self.assertTrue(
                    hasattr(self.wire, handle),
                    msg=f"expected wire to have attribute {handle}",
                )
        for item, _ in self.wire.metadata:
            self.assertTrue(
                hasattr(self.wire.metadata, item),
                msg=f"expected wire to have attribute {item}",
            )
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
            self.assertTrue(
                hasattr(self.wire, item),
                msg=f"expected wire to have attribute {item}",
            )

    def test_methods(self) -> None:
        """Test that all the methods we expect exist"""
        self.assertEqual(inspect.ismethod(self.wire.abort_scan), True)
        self.assertEqual(inspect.ismethod(self.wire.initialize), True)
        self.assertEqual(inspect.ismethod(self.wire.position_buffer), True)
        self.assertEqual(inspect.ismethod(self.wire.retract), True)
        self.assertEqual(inspect.ismethod(self.wire.start_scan), True)
        self.assertEqual(inspect.ismethod(self.wire.set_range), True)
        self.assertEqual(inspect.ismethod(self.wire.use), True)
        self.assertEqual(inspect.ismethod(self.wire.active_profiles), True)

    def test_active_profiles_returns_enabled_planes(self):
        self.mock_pv.get.side_effect = [1, 0, True]
        self.assertEqual(self.wire.active_profiles(), ["x", "u"])
        self.mock_pv.get.side_effect = None

    def test_name(self) -> None:
        """Test we get expected default"""
        self.assertEqual(self.wire.name, "WSBP2")

    def test_area(self) -> None:
        """Test we get expected default"""
        self.assertEqual(self.wire.area, "BYP")

    def test_all_properties(self):
        """Verify all PV-backed Wire properties call PV.get() and return the mocked value."""
        properties_to_test = [
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
        ]

        for prop in properties_to_test:
            with self.subTest(property=prop):
                # reset the mock to avoid call overlaps
                self.mock_pv.get.reset_mock()
                self.mock_pv.get.return_value = 123  # something arbitrary

                result = getattr(self.wire, prop)
                self.assertEqual(result, 123, f"{prop} should return mocked value")
                self.mock_pv.get.assert_called_once()

    def test_metadata_exists_and_type(self):
        """Wire has a valid metadata object"""
        self.assertTrue(hasattr(self.wire, "metadata"))
        self.assertIsInstance(self.wire.metadata, WireMetadata)

    def test_metadata_has_detectors_list(self):
        m = self.wire.metadata
        self.assertTrue(hasattr(m, "detectors"))
        self.assertIsInstance(m.detectors, list)

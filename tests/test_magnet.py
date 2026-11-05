#!/usr/local/lcls/package/python/current/bin/python

# Built in
import datetime
import inspect
from unittest.mock import Mock, patch, PropertyMock

import pytest

# Local imports
from slac_devices.reader import create_magnet
from slac_devices.magnet import MagnetCollection, Magnet

CTRL_OPTIONS = [
    "TRIM",
    "PERTURB",
    "BCON_TO_BDES",
    "SAVE_BDES",
    "LOAD_BDES",
    "UNDO_BDES",
    "DAC_ZERO",
    "CALIB",
    "STDZ",
    "RESET",
    "TURN_OFF",
    "TURN_ON",
    "DEGAUSS",
]
OPTIONS_REQUIRING_STATE_CHECK = [
    "TRIM",
    "PERTURB",
    "DAC_ZERO",
    "CALIB",
    "STDZ",
]


@pytest.fixture
def all_ctrl_options(mock_ctrlvars):
    """Construct each magnet with ALL ctrl options."""
    mock_ctrlvars.return_value = {"enum_strs": tuple(CTRL_OPTIONS)}
    return mock_ctrlvars


@pytest.fixture
def magnet(all_ctrl_options):
    return create_magnet(
        area="GUNB",
        name="SOL1B",
    )


@pytest.fixture
def control_functions(magnet):
    """Map each ctrl option to the magnet method that triggers it."""
    return {
        "TRIM": magnet.trim,
        "PERTURB": magnet.perturb,
        "BCON_TO_BDES": magnet.con_to_des,
        "SAVE_BDES": magnet.save_bdes,
        "LOAD_BDES": magnet.load_bdes,
        "UNDO_BDES": magnet.undo_bdes,
        "DAC_ZERO": magnet.dac_zero,
        "CALIB": magnet.calibrate,
        "STDZ": magnet.standardize,
        "RESET": magnet.reset,
        "TURN_OFF": magnet.turn_off,
        "TURN_ON": magnet.turn_on,
        "DEGAUSS": magnet.degauss,
    }


@pytest.fixture
def magnet_collection(all_ctrl_options):
    return create_magnet(area="GUNB")


class TestMagnet:
    def test_properties_exist(self, magnet) -> None:
        """Test that all the properties we expect exist"""
        # Assert that magnet has all auto-generated private attributes
        for handle, _ in magnet.controls_information.PVs:
            assert hasattr(
                type(magnet), handle
            ), f"expected magnet to have attribute {handle}"
        for item, _ in magnet.metadata:
            if item != "hardware":
                assert hasattr(
                    type(magnet), item
                ), f"expected magnet to have attribute {item}"
        # Assert that magnet has public properties
        for item in [
            "bctrl",
            "bact",
            "ctrl",
            "l_eff",
            "b_tolerance",
            "bmax",
            "bmin",
            #    "bdes", # is this somewhere else?
        ]:
            assert hasattr(type(magnet), item), f"expected magnet to have attribute {item}"

    def test_methods(self, magnet) -> None:
        """Test that all the methods we expect exist"""
        assert inspect.ismethod(magnet.trim)
        assert inspect.ismethod(magnet.perturb)
        assert inspect.ismethod(magnet.con_to_des)
        assert inspect.ismethod(magnet.save_bdes)
        assert inspect.ismethod(magnet.load_bdes)
        assert inspect.ismethod(magnet.undo_bdes)
        assert inspect.ismethod(magnet.dac_zero)
        assert inspect.ismethod(magnet.calibrate)
        assert inspect.ismethod(magnet.standardize)
        assert inspect.ismethod(magnet.reset)
        assert inspect.ismethod(magnet.turn_off)
        assert inspect.ismethod(magnet.turn_on)
        assert inspect.ismethod(magnet.degauss)
        assert inspect.ismethod(magnet.add_callback_to_pv)
        assert inspect.ismethod(magnet.remove_callback_from_pv)

    def test_name(self, magnet) -> None:
        """Test we get expected default"""
        assert magnet.name == "SOL1B"

    def test_ctrl_options_are_lazy_loaded(self, magnet, mock_ctrlvars) -> None:
        # mock_ctrl_options patches epics.PV.get_ctrlvars; accessing
        # ctrl_options for the first time should trigger exactly one call
        # to get_ctrlvars(timeout=1).
        mock_ctrlvars.assert_not_called()
        _ = magnet.ctrl_options
        mock_ctrlvars.assert_called_once_with(timeout=1)

    def test_tol(self, magnet) -> None:
        """Test tol float validation"""
        assert magnet.b_tolerance is None
        magnet.b_tolerance = "a"
        assert magnet.b_tolerance is None
        magnet.b_tolerance = 1
        assert magnet.b_tolerance is None
        magnet.b_tolerance = 0.1
        assert magnet.b_tolerance == 0.1

    def test_length(self, magnet) -> None:
        """Test effective length float validation"""
        # SOL1B -> l_eff: 0.086
        assert magnet.l_eff == 0.086
        # might need validate_assignment = True in magnet class
        # with pytest.raises(ValidationError):
        # magnet.l_eff = "a"
        # some trouble with this.... need to change config later. its not forcing
        # revalidation after reassignment since type is optional I believe.
        magnet.l_eff = 1.0
        assert magnet.l_eff == 1.0
        magnet.l_eff = 0.05
        assert magnet.l_eff == 0.05

    @patch("epics.PV.get", new_callable=Mock)
    def test_bact(self, mock_pv_get, magnet) -> None:
        mock_pv_get.return_value = 0.1
        assert magnet.bact == 0.1
        mock_pv_get.assert_called_once()

    @patch("epics.PV.get", new_callable=Mock)
    def test_bdes(self, mock_pv_get, magnet) -> None:
        mock_pv_get.return_value = 0.5
        assert magnet.bdes == 0.5
        mock_pv_get.assert_called_once()

    @patch("epics.PV.put", new_callable=Mock)
    def test_set_bdes(self, mock_pv_put, magnet) -> None:
        mock_pv_put.return_value = None
        magnet.bdes = 0.1
        mock_pv_put.assert_called_once_with(value=0.1, wait=True)

    @patch("epics.PV.get", new_callable=Mock)
    def test_get_bctrl(self, mock_pv_get, magnet) -> None:
        mock_pv_get.return_value = 0.5
        assert magnet.bctrl == 0.5
        mock_pv_get.assert_called_once()

    @patch("epics.PV.put", new_callable=Mock)
    @patch(
        "slac_devices.magnet.Magnet.ctrl",
        new_callable=PropertyMock,
    )
    def test_set_bctrl_with_int_and_ready(
        self,
        mock_ctrl_option,
        mock_pv_put,
        magnet,
    ) -> None:
        mock_ctrl_option.return_value = "Ready"
        magnet.bctrl = 3
        mock_pv_put.assert_called_once_with(value=3)

    @patch("epics.PV.put", new_callable=Mock)
    @patch(
        "slac_devices.magnet.Magnet.ctrl",
        new_callable=PropertyMock,
    )
    def test_set_bctrl_with_string_and_ready(
        self,
        mock_ctrl_option,
        mock_pv_put,
        magnet,
    ) -> None:
        mock_ctrl_option.return_value = "Ready"
        magnet.bctrl = "string"
        mock_pv_put.assert_not_called()

    @patch("epics.PV.put", new_callable=Mock)
    @patch(
        "slac_devices.magnet.Magnet.ctrl",
        new_callable=PropertyMock,
    )
    def test_set_bctrl_with_int_and_not_ready(
        self,
        mock_ctrl_option,
        mock_pv_put,
        magnet,
    ) -> None:
        mock_ctrl_option.return_value = "Trim"
        magnet.bctrl = 5
        mock_pv_put.assert_not_called()

    @patch("epics.PV.get", new_callable=Mock)
    def test_get_ctrl_calls_pv_get(self, pv_get_mock, magnet) -> None:
        pv_get_mock.return_value = "Ready"
        value = magnet.ctrl
        assert value == "Ready"
        pv_get_mock.assert_called_once_with(as_string=True)

    @patch("epics.PV.put", new_callable=Mock)
    @patch(
        "slac_devices.magnet.Magnet.ctrl",
        new_callable=PropertyMock,
    )
    def test_control_functions_call_pv_put_if_ready(
        self,
        mock_ctrl_option,
        pv_put_mock,
        magnet,
        mock_ctrlvars,
        control_functions,
    ) -> None:
        mock_ctrl_option.return_value = "Ready"
        mock_ctrlvars.return_value = {
            "enum_strs": tuple(control_functions.keys()),
        }
        for option, func in control_functions.items():
            func()
            pv_put_mock.assert_called_once_with(magnet.ctrl_options[option])
            pv_put_mock.reset_mock()

    @patch("epics.PV.put", new_callable=Mock)
    @patch(
        "slac_devices.magnet.Magnet.ctrl",
        new_callable=PropertyMock,
    )
    def test_control_functions_that_do_nothing_if_not_ready(
        self,
        mock_ctrl,
        pv_put_mock,
        magnet,
        mock_ctrlvars,
        control_functions,
    ) -> None:
        mock_ctrl.return_value = "Not Ready"
        mock_ctrlvars.return_value = {
            "enum_strs": tuple(control_functions.keys()),
        }

        for option, func in control_functions.items():
            func()
            if option in OPTIONS_REQUIRING_STATE_CHECK:
                pv_put_mock.assert_not_called()
            else:
                pv_put_mock.assert_called_once_with(magnet.ctrl_options[option])
            pv_put_mock.reset_mock()

    @patch(
        "slac_devices.magnet.Magnet.bdes",
        new_callable=PropertyMock,
    )
    @patch(
        "slac_devices.magnet.Magnet.bact",
        new_callable=PropertyMock,
    )
    def test_bact_is_settled(self, mock_bact, mock_bdes, magnet) -> None:
        mock_bact.return_value = 0.001
        mock_bdes.return_value = 0.0009
        assert magnet.is_bact_settled(b_tolerance=0.0002)

    @patch(
        "slac_devices.magnet.Magnet.bdes",
        new_callable=PropertyMock,
    )
    @patch(
        "slac_devices.magnet.Magnet.bact",
        new_callable=PropertyMock,
    )
    def test_bact_is_not_settled(self, mock_bact, mock_bdes, magnet) -> None:
        mock_bact.return_value = 0.001
        mock_bdes.return_value = 0.01
        assert not magnet.is_bact_settled(b_tolerance=0.001)

    @patch("epics.PV.put", new_callable=Mock)
    @patch(
        "slac_devices.magnet.Magnet.ctrl",
        new_callable=PropertyMock,
    )
    @patch(
        "slac_devices.magnet.MagnetControlInformation.ctrl_options",
        new_callable=PropertyMock,
    )
    def test_nothing_happens_if_ctrl_option_is_not_available(
        self,
        mock_ctrl_options,
        mock_ctrl,
        mock_put,
        control_functions,
    ) -> None:
        # we now replace to all-test-case-mock that has ALL ctrl options
        # to only have 'Ready' options
        mock_ctrl_options.return_value = {
            "enum_strs": tuple("Ready"),
        }
        mock_ctrl.return_value = "Ready"
        for _, function in control_functions.items():
            function()
            mock_put.assert_not_called()
            mock_put.reset_mock()


class TestMagnetCollection:
    def test_magnet_collection_creation(self, magnet_collection) -> None:
        assert isinstance(magnet_collection, MagnetCollection)

    def test_seconds_since(self, magnet_collection) -> None:
        one_second_in_the_past = datetime.datetime.now() - datetime.timedelta(seconds=1)
        time_passed = magnet_collection._seconds_since(
            time_to_check=one_second_in_the_past
        )
        assert time_passed == 1, f"Expected 1s passed, got {time_passed}s"

    def test_seconds_since_throws_if_given_non_datetime_arg(
        self, magnet_collection
    ) -> None:
        time_to_check = 1000
        with pytest.raises(TypeError):
            magnet_collection._seconds_since(time_to_check=time_to_check)

    @patch(
        "slac_devices.magnet.Magnet.is_bact_settled",
        new_callable=Mock,
    )
    @patch(
        "slac_devices.magnet.Magnet.bdes",
        new_callable=PropertyMock,
    )
    @patch(
        "slac_devices.magnet.Magnet.trim",
        new_callable=Mock,
    )
    def test_set_bdes_with_no_args(
        self,
        mock_trim,
        mock_bdes,
        mock_bact_settle,
        magnet_collection,
    ) -> None:
        with pytest.raises(TypeError):
            magnet_collection.set_bdes()
        magnet_collection.set_bdes(magnet_dict={})
        mock_bdes.assert_not_called()
        mock_trim.assert_not_called()
        mock_bact_settle.assert_not_called()

    @patch(
        "slac_devices.magnet.Magnet.is_bact_settled",
        new_callable=Mock,
    )
    @patch("epics.PV.put", new_callable=Mock)
    @patch("slac_devices.magnet.Magnet.trim", new_callable=Mock)
    def test_set_bdes_with_args(
        self,
        mock_trim,
        mock_bdes_put,
        mock_bact_settled,
        magnet_collection,
    ) -> None:
        bdes_settings = {
            "SOL1B": 0.1,
        }
        mock_bact_settled.return_value = True
        magnet_collection.set_bdes(magnet_dict=bdes_settings)
        mock_bdes_put.assert_called_once_with(value=0.1, wait=True)
        mock_trim.assert_called_once()
        mock_bact_settled.assert_called_once_with()

    @patch(
        "slac_devices.magnet.Magnet.is_bact_settled",
        new_callable=Mock,
    )
    @patch("epics.PV.put", new_callable=Mock)
    @patch("slac_devices.magnet.Magnet.trim", new_callable=Mock)
    def test_set_bdes_with_bad_magnet_name(
        self,
        mock_trim,
        mock_bdes_put,
        mock_bact_settled,
        magnet_collection,
    ) -> None:
        bdes_settings = {
            "BAD-MAG": 0.3,
        }
        magnet_collection.set_bdes(magnet_dict=bdes_settings)
        mock_bdes_put.assert_not_called()
        mock_trim.assert_not_called()
        mock_bact_settled.assert_not_called()

    @patch(
        "slac_devices.magnet.Magnet.is_bact_settled",
        new_callable=Mock,
    )
    @patch("epics.PV.put", new_callable=Mock)
    @patch("slac_devices.magnet.Magnet.trim", new_callable=Mock)
    def test_scan_with_no_callable(
        self,
        mock_trim,
        mock_put,
        mock_bact_settle,
        magnet_collection,
    ) -> None:
        settings = [
            {
                "SOL1B": 0.1,
            },
            {
                "SOL1B": 0.15,
            },
            {
                "SOL1B": 0.2,
            },
        ]
        mock_bact_settle.return_value = True
        magnet_collection.scan(scan_settings=settings)
        assert mock_put.call_count == 3
        assert mock_trim.call_count == 3
        assert mock_bact_settle.call_count == 3

    @patch(
        "slac_devices.magnet.Magnet.is_bact_settled",
        new_callable=Mock,
    )
    @patch("epics.PV.put", new_callable=Mock)
    @patch("slac_devices.magnet.Magnet.trim", new_callable=Mock)
    def test_scan_with_callable(
        self,
        mock_trim,
        mock_put,
        mock_bact_settle,
        magnet_collection,
    ) -> None:
        mock_daq_function = Mock()
        settings = [
            {
                "SOL1B": 0.1,
            },
            {
                "SOL1B": 0.15,
            },
            {
                "SOL1B": 0.2,
            },
        ]
        mock_bact_settle.return_value = True
        magnet_collection.scan(scan_settings=settings, function=mock_daq_function)
        assert mock_put.call_count == 3
        assert mock_trim.call_count == 3
        assert mock_bact_settle.call_count == 3
        assert mock_daq_function.call_count == 3

    @patch(
        "slac_devices.magnet.Magnet.is_bact_settled",
        new_callable=Mock,
    )
    @patch("epics.PV.put", new_callable=Mock)
    @patch("slac_devices.magnet.Magnet.trim", new_callable=Mock)
    @patch(
        "slac_devices.magnet.MagnetCollection._seconds_since",
        new_callable=Mock,
    )
    def test_set_bdes_when_timeout_happens(
        self,
        mock_timer_count,
        mock_trim,
        mock_put,
        mock_bact_settle,
        magnet_collection,
    ) -> None:
        # make sure that magnet_collection._seconds_since()
        # always returns > settle_timeout for set_bdes()
        mock_timer_count.side_effect = [6 for i in range(2)]
        # Make sure bact never settles to bdes
        mock_bact_settle.return_value = False
        settings = {
            "SOL1B": 0.1,
            "SOL2B": 0.1,
        }
        magnet_collection.set_bdes(settings)
        # We call functions once per-setting
        # but we ALWAYS timeout so we only call twice overall.
        assert mock_put.call_count == 2
        assert mock_trim.call_count == 2
        assert mock_bact_settle.call_count == 2

    @patch(
        "slac_devices.magnet.Magnet.is_bact_settled",
        new_callable=Mock,
    )
    @patch("epics.PV.put", new_callable=Mock)
    @patch("slac_devices.magnet.Magnet.trim", new_callable=Mock)
    @patch(
        "slac_devices.magnet.MagnetCollection._seconds_since",
        new_callable=Mock,
    )
    def test_set_bdes_when_timeout_happens_after_first_call(
        self,
        mock_timer_count,
        mock_trim,
        mock_put,
        mock_bact_settle,
        magnet_collection,
    ) -> None:
        # make sure that magnet_collection._seconds_since()
        # always returns > settle_timeout for set_bdes()
        mock_timer_count.side_effect = [i + 4 for i in range(10)]
        # Make sure bact never settles to bdes
        mock_bact_settle.return_value = False
        settings = {
            "SOL1B": 0.1,
        }
        magnet_collection.set_bdes(settings)
        # We call functions once per-setting
        # but we ALWAYS timeout so we only call once overall.
        assert mock_put.call_count == 1
        assert mock_trim.call_count == 1
        # We will call the bact_settle function 3 times
        # 1st (0 + 4 secs) !>  5, 2nd (1 + 4 secs) !> 5, 3rd (2 + 4secs) > 5
        assert mock_bact_settle.call_count == 3

    @patch("slac_devices.magnet.Magnet.turn_off", new_callable=Mock)
    def test_turn_off_single_magnet(self, mock_turn_off, magnet_collection):
        magnet_name = "SOL1B"
        magnet_collection.turn_off(magnet_name)
        mock_turn_off.assert_called_once()

    @patch("slac_devices.magnet.Magnet.turn_off", new_callable=Mock)
    def test_turn_off_multiple_magnets(self, mock_turn_off, magnet_collection):
        magnet_names = ["SOL1B", "SOL2B"]
        magnet_collection.turn_off(magnet_names)
        assert mock_turn_off.call_count == 2

    @patch("slac_devices.magnet.Magnet.turn_off", new_callable=Mock)
    def test_turn_off_all_magnets(self, mock_turn_off, magnet_collection):
        magnet_collection.turn_off()
        total_number_of_magnets = len(magnet_collection.magnets)
        assert mock_turn_off.call_count == total_number_of_magnets

    @patch("slac_devices.magnet.Magnet.turn_off", new_callable=Mock)
    def test_turn_off_bad_magnet(self, mock_turn_off, magnet_collection):
        magnet_name = "BAD-MAGNET"
        magnet_collection.turn_off(magnet_name)
        mock_turn_off.assert_not_called()

    @patch("slac_devices.magnet.Magnet.turn_on", new_callable=Mock)
    def test_turn_on_single_magnet(self, mock_turn_on, magnet_collection):
        magnet_name = "SOL1B"
        magnet_collection.turn_on(magnet_name)
        mock_turn_on.assert_called_once()

    @patch("slac_devices.magnet.Magnet.turn_on", new_callable=Mock)
    def test_turn_on_multiple_magnets(self, mock_turn_on, magnet_collection):
        magnet_names = ["SOL1B", "SOL2B"]
        magnet_collection.turn_on(magnet_names)
        assert mock_turn_on.call_count == 2

    @patch("slac_devices.magnet.Magnet.turn_on", new_callable=Mock)
    def test_turn_on_all_magnets(self, mock_turn_on, magnet_collection):
        magnet_collection.turn_on()
        total_number_of_magnets = len(magnet_collection.magnets)
        assert mock_turn_on.call_count == total_number_of_magnets

    @patch("slac_devices.magnet.Magnet.turn_on", new_callable=Mock)
    def test_turn_on_bad_magnet(self, mock_turn_on, magnet_collection):
        magnet_name = "BAD-MAGNET"
        magnet_collection.turn_on(magnet_name)
        mock_turn_on.assert_not_called()

    @patch("slac_devices.magnet.Magnet.turn_on", new_callable=Mock)
    def test_degauss_single_magnet(self, mock_turn_on, magnet_collection):
        magnet_name = "SOL1B"
        magnet_collection.turn_on(magnet_name)
        mock_turn_on.assert_called_once()

    @patch("slac_devices.magnet.Magnet.degauss", new_callable=Mock)
    def test_degauss_multiple_magnets(self, mock_degauss, magnet_collection):
        magnet_names = ["SOL1B", "SOL2B"]
        magnet_collection.degauss(magnet_names)
        assert mock_degauss.call_count == 2

    @patch("slac_devices.magnet.Magnet.degauss", new_callable=Mock)
    def test_degauss_all_magnets(self, mock_degauss, magnet_collection):
        magnet_collection.degauss()
        total_number_of_magnets = len(magnet_collection.magnets)
        assert mock_degauss.call_count == total_number_of_magnets

    @patch("slac_devices.magnet.Magnet.degauss", new_callable=Mock)
    def test_degauss_bad_magnet(self, mock_degauss, magnet_collection):
        magnet_name = "BAD-MAGNET"
        magnet_collection.degauss(magnet_name)
        mock_degauss.assert_not_called()

    def test_serialization(self, magnet_collection):
        magnet = magnet_collection.magnets["CQ01B"]
        info = magnet.model_dump()
        assert (
            info["controls_information"]["PVs"]["bctrl"]
            == magnet.controls_information.PVs.bctrl.pvname
        )

        # create magnet from info dict
        new_magnet = Magnet(**info)
        assert magnet == new_magnet

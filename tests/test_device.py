from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml
from epics import PV
from pydantic import ValidationError

from slac_devices.device import (
    Device,
    ApplyDeviceCallbackError,
    RemoveDeviceCallbackError,
)

CONFIG_FILENAME = Path(__file__).parent / "test_data" / "config" / "base_device.yaml"
DEVICE_NAME = "DEVICE_1"


@pytest.fixture
def config_data():
    with open(CONFIG_FILENAME, "r") as file:
        return yaml.safe_load(file)


@pytest.fixture
def device(config_data):
    device_data = config_data[DEVICE_NAME]
    device_data.update({"name": DEVICE_NAME})
    return Device(**device_data)


@pytest.fixture
def pv_obj():
    return PV("SOLN:GUNB:212:BACT")


# Kept from the unittest version, whose setUp built a PV for every test case.
pytestmark = pytest.mark.usefixtures("pv_obj")


def test_sum_l_meters_and_z_location_match(device):
    assert device.sum_l_meters == device.z_location


def test_config_with_no_control_information_field_raises(config_data):
    name_of_device_with_missing_data = "DEVICE_2"
    with pytest.raises(ValidationError):
        Device(**config_data[name_of_device_with_missing_data])


def test_config_with_no_metadata_field_raises(config_data):
    name_of_device_with_missing_data = "DEVICE_3"
    with pytest.raises(ValidationError):
        Device(**config_data[name_of_device_with_missing_data])


def test_name_property_assigned_after_init(device):
    assert device.name == DEVICE_NAME


@patch(
    "slac_devices.device.Device._get_attribute",
    new_callable=MagicMock(),
)
def test_get_pv_object_from_str_with_good_pv_string(
    mock_get_attribute: MagicMock,
    device,
) -> None:
    good_pv_name = "SOLN:GUNB:212:BCTRL"
    good_pv_obj = PV(good_pv_name)
    mock_get_attribute.return_value = good_pv_obj
    result = device._get_pv_object_from_str("bact")
    assert result is not None
    assert result == good_pv_obj


def test_get_pv_object_from_str_with_bad_pv_string(device):
    result = device._get_pv_object_from_str("bad-name")
    assert result is None


@patch(
    "slac_devices.device.Device._get_attribute",
    new_callable=MagicMock(),
)
def test_get_callbacks_with_good_pv_string(
    mock_get_attribute: MagicMock,
    device,
) -> None:
    good_pv_name = "SOLN:GUNB:212:BCTRL"
    good_pv_obj = PV(good_pv_name)
    handle = "bact"
    mock_get_attribute.return_value = good_pv_obj
    result = device.get_callbacks(handle)
    assert result is not None
    # start with empty dictionary check
    assert result == dict()

    def dummy_callback():  # pragma: no cover
        print("test callback")

    # add some callback function to the pv
    device.add_callback_to_pv(pv=handle, function=dummy_callback)
    result = device.get_callbacks(handle)
    # check we have an indexed-dictionary of callback functions
    expected_callback_structure = {1: (dummy_callback, {})}
    assert result == expected_callback_structure


def test_get_callbacks_with_bad_pv_string(device):
    result = device.get_callbacks("bad-pv-handle")
    assert result is None


def test_get_callback_index_with_no_callbacks_for_pv(device, pv_obj):
    def mock_callback():  # pragma: no cover
        print("mock callback")

    index = device._get_callback_index(pv_obj, mock_callback)
    assert index is None


@patch(
    "slac_devices.device.Device._get_attribute",
    new_callable=MagicMock(),
)
def test_get_callback_index_with_multiple_callbacks_for_pv(
    mock_get_attribute: MagicMock,
    device,
    pv_obj,
) -> None:
    mock_get_attribute.return_value = pv_obj

    def mock_callback(message: str) -> None:  # pragma: no cover
        print(f"callback: {message}")

    # Add different callbacks to Device
    def first_callback():  # pragma: no cover
        mock_callback("first")

    def second_callback():  # pragma: no cover
        mock_callback("second")

    def third_callback():  # pragma: no cover
        mock_callback("third")

    device.add_callback_to_pv(
        "bact",
        first_callback,
    )
    device.add_callback_to_pv(
        "bact",
        second_callback,
    )
    device.add_callback_to_pv(
        "bact",
        third_callback,
    )
    # Retrieve the index of 2nd callback function
    # Annoying because PV callback indexes start from 1.
    index = device._get_callback_index(
        pv_obj,
        second_callback,
    )
    # Check that index is 2 because we asked for 2nd callback
    assert index == 2


def test_add_callback_to_pv_raises_with_bad_pv_arg(device, pv_obj):
    with pytest.raises(ApplyDeviceCallbackError):

        def mock_callback():  # pragma: no cover
            pass

        device.add_callback_to_pv(
            pv=pv_obj,
            function=mock_callback,
        )


def test_add_callback_to_pv_raises_with_bad_callback_arg(device):
    with pytest.raises(ApplyDeviceCallbackError):
        device.add_callback_to_pv(
            pv="bact",
            function=dict(),
        )


def test_add_callback_raises_when_pv_does_not_exist(device):
    def mock_callback():  # pragma: no cover
        pass

    with pytest.raises(ApplyDeviceCallbackError):
        device.add_callback_to_pv(pv="bact", function=mock_callback)


@patch(
    "slac_devices.device.Device._get_attribute",
    new_callable=MagicMock(),
)
def test_add_callback_raises_when_callback_exists_for_pv(
    mock_get_attribute: MagicMock,
    device,
    pv_obj,
) -> None:
    def mock_callback():  # pragma: no cover
        pass

    mock_get_attribute.return_value = pv_obj
    pv_obj.add_callback(mock_callback)
    with pytest.raises(ApplyDeviceCallbackError):
        device.add_callback_to_pv(pv="bact", function=mock_callback)


@patch(
    "slac_devices.device.Device._get_attribute",
    new_callable=MagicMock(),
)
def test_add_callback_success_when_callback_new_for_pv(
    mock_get_attribute: MagicMock,
    device,
    pv_obj,
) -> None:
    def mock_callback():  # pragma: no cover
        pass

    mock_get_attribute.return_value = pv_obj
    assert len(pv_obj.callbacks) == 0
    device.add_callback_to_pv(pv="bact", function=mock_callback)
    # Check we added the callback
    assert len(pv_obj.callbacks) != 0
    expected_callback_structure = {1: (mock_callback, {})}
    # Check callbacks come back as expected
    assert pv_obj.callbacks == expected_callback_structure


def test_remove_callback_to_pv_raises_with_bad_pv_arg(device, pv_obj):
    with pytest.raises(RemoveDeviceCallbackError):

        def mock_callback():  # pragma: no cover
            pass

        device.remove_callback_from_pv(
            pv=pv_obj,
            function=mock_callback,
        )


def test_remove_callback_to_pv_raises_with_bad_callback_arg(device):
    with pytest.raises(RemoveDeviceCallbackError):
        device.remove_callback_from_pv(
            pv="bact",
            function=dict(),
        )


def test_remove_callback_raises_when_pv_does_not_exist(device):
    def mock_callback():  # pragma: no cover
        pass

    with pytest.raises(RemoveDeviceCallbackError):
        device.remove_callback_from_pv(pv="bact", function=mock_callback)


@patch(
    "slac_devices.device.Device._get_attribute",
    new_callable=MagicMock(),
)
def test_remove_callback_raises_when_callback_does_not_exist_for_pv(
    mock_get_attribute: MagicMock,
    device,
    pv_obj,
) -> None:
    def mock_callback():  # pragma: no cover
        pass

    mock_get_attribute.return_value = pv_obj
    with pytest.raises(RemoveDeviceCallbackError):
        device.remove_callback_from_pv(pv="bact", function=mock_callback)


@patch(
    "slac_devices.device.Device._get_attribute",
    new_callable=MagicMock(),
)
def test_remove_callback_success_when_callback_exists_for_pv(
    mock_get_attribute: MagicMock,
    device,
    pv_obj,
) -> None:
    def mock_callback():  # pragma: no cover
        pass

    mock_get_attribute.return_value = pv_obj
    pv_obj.add_callback(mock_callback)
    assert len(pv_obj.callbacks) == 1
    expected_callback_structure = {1: (mock_callback, {})}
    # Check that we have added the callback
    assert pv_obj.callbacks == expected_callback_structure
    # Check that we don't throw error when removing callback
    device.remove_callback_from_pv("bact", mock_callback)
    # Check callback has been removed
    assert len(pv_obj.callbacks) == 0
    assert pv_obj.callbacks == {}

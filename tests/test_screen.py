from datetime import datetime, timedelta
import os
import time
from unittest.mock import PropertyMock, patch

import h5py
import numpy as np
import pytest

from slac_devices.reader import create_screen
from slac_devices.screen import Screen


@pytest.fixture
def screen():
    return create_screen("BC1").screens["OTR11"]


@patch(
    "slac_devices.screen.Screen.image",
    new_callable=PropertyMock,
)
@patch(
    "slac_devices.screen.Screen.image_timestamp",
    new_callable=PropertyMock,
)
def test_hdf5_saving(mock_timestamp, mock_image, screen):
    num_capture = 10
    mock_image.return_value = np.zeros(shape=(20, 20))
    t0 = datetime.now()
    # return an incrementing timestamp each time .image_timestamp is accessed.
    mock_timestamp.side_effect = [
        t0 + timedelta(seconds=i) for i in range(0, num_capture * 10)
    ]
    for is_threaded in [True, False]:
        screen.save_images(num_to_capture=num_capture, threaded=is_threaded)
        while screen.is_saving_images:
            time.sleep(1)
        assert os.path.exists(
            screen.last_save_filepath
        ), f"expected file to exist: {screen._last_save_filepath}"
        # Open the file we have saved and check the contents
        with h5py.File(screen.last_save_filepath, "r") as f:
            # check we have the correct number of images
            assert len(f) == num_capture
            # check metadata is stored as attributes in HDF5.
            for dataset in f:
                assert set(f[dataset].attrs.keys()) == set(
                    screen.metadata.model_dump().keys()
                )
                # check dataset content for shape
                assert np.array_equal(np.zeros(shape=(20, 20)), f[dataset])


@patch(
    "slac_devices.screen.Screen.image",
    new_callable=PropertyMock,
)
@patch(
    "slac_devices.screen.Screen.image_timestamp",
    new_callable=PropertyMock,
)
def test_hdf5_with_user_metadata(mock_timestamp, mock_image, screen):
    num_capture = 10
    mock_image.return_value = np.zeros(shape=(20, 20))
    t0 = datetime.now()
    # return an incrementing timestamp each time .image_timestamp is accessed.
    mock_timestamp.side_effect = [
        t0 + timedelta(seconds=i) for i in range(0, num_capture * 10)
    ]
    user_metadata_for_scan = {
        "Comments": "Emittance Scan for HTR.",
        "QUAD1_BACT": 0.23,
        "QUAD_1_UNITS": "kG",
        "timestamp": str(datetime.now()),
    }
    for is_threaded in [True, False]:
        screen.save_images(
            num_to_capture=num_capture,
            threaded=is_threaded,
            extra_metadata=user_metadata_for_scan,
        )
        while screen.is_saving_images:
            time.sleep(1)
        assert os.path.exists(
            screen.last_save_filepath
        ), f"expected file to exist: {screen._last_save_filepath}"
        # Open the file we have saved and check the contents
        with h5py.File(screen.last_save_filepath, "r") as f:
            # check we have the correct number of images
            assert len(f) == num_capture
            user_metadata_for_scan.update(**screen.metadata.model_dump())
            # check metadata is stored as attributes in HDF5.
            for dataset in f:
                assert sorted(f[dataset].attrs.keys()) == sorted(
                    user_metadata_for_scan.keys()
                )
                # check dataset content for shape
                assert np.array_equal(np.zeros(shape=(20, 20)), f[dataset])


def test_serialization(screen):
    info = screen.model_dump()
    assert (
        info["controls_information"]["PVs"]["image"]
        == screen.controls_information.PVs.image.pvname
    )

    # create screen from info dict
    new_screen = Screen(**info)
    assert screen == new_screen

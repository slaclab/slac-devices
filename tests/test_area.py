from pathlib import Path

import yaml

from slac_devices.area import Area
from slac_devices.bpm import BPMCollection
from slac_devices.magnet import MagnetCollection

CONFIG_LOCATION = Path(__file__).parent / "test_data" / "config"


def test_area_with_no_magnets():
    mock_screen_data = {"screens": {}}
    with open(CONFIG_LOCATION / "screen" / "typical_screen.yaml", "r") as file:
        mock_screen_data["screens"] = yaml.safe_load(file)
    area = Area(name="mock_area", **mock_screen_data)
    assert area.magnet_collection is None
    assert area.magnets is None


def test_area_repr_includes_counts_and_populated_types():
    area = Area.model_construct(
        name="L3",
        magnet_collection=MagnetCollection.model_construct(
            magnets={"M1": object(), "M2": object()}
        ),
        bpm_collection=BPMCollection.model_construct(bpms={"BPM1": object()}),
        screen_collection=None,
        wire_collection=None,
        lblm_collection=None,
        pmt_collection=None,
        tcav_collection=None,
    )

    representation = repr(area)
    assert "Area(name='L3'" in representation
    assert "total_devices=3" in representation
    assert "'magnets': 2" in representation
    assert "'bpms': 1" in representation
    assert "'tcavs': 0" in representation
    assert "populated_types=['magnets', 'bpms']" in representation

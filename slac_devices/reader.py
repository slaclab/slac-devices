from typing import Union, Optional
from pydantic import ValidationError
import slac_db
from slac_devices.screen import Screen, ScreenCollection
from slac_devices.magnet import Magnet, MagnetCollection
from slac_devices.wire import Wire, WireCollection
from slac_devices.lblm import LBLM, LBLMCollection
from slac_devices.pmt import PMT, PMTCollection
from slac_devices.bpm import BPM, BPMCollection
from slac_devices.tcav import TCAV, TCAVCollection
from slac_devices.area import Area
from slac_devices.beampath import Beampath


_AREA_SUPPORTED_DEVICE_TYPES = {
    "magnets",
    "screens",
    "wires",
    "bpms",
    "lblms",
    "pmts",
    "tcavs",
}


def create_magnet(
    area: str = None, name: str = None
) -> Union[None, Magnet, MagnetCollection]:
    device_data = slac_db.get_device(area=area, device_type="magnets", name=name)
    if not device_data:
        return None
    if name:
        try:
            # this data is not available from YAML directly in this form, so we add it here.
            device_data.update({"name": name})
            return Magnet(**device_data)
        except ValidationError as field_error:
            print(field_error)
            return None
    else:
        return MagnetCollection(**device_data)


def create_screen(
    area: str = None, name: str = None
) -> Union[None, Screen, ScreenCollection]:
    device_data = slac_db.get_device(area=area, device_type="screens", name=name)
    if not device_data:
        return None
    if name:
        try:
            # this data is not available from YAML directly in this form, so we add it here.
            device_data.update({"name": name})
            return Screen(**device_data)
        except ValidationError as field_error:
            print(field_error)
            return None
    else:
        return ScreenCollection(**device_data)


def create_wire(
    area: str = None, name: str = None
) -> Union[None, Wire, WireCollection]:
    device_data = slac_db.get_device(area=area, device_type="wires", name=name)
    if not device_data:
        return None
    if name:
        try:
            # this data is not available from YAML directly in this form, so we add it here.
            device_data.update({"name": name})
            return Wire(**device_data)
        except ValidationError as field_error:
            print(field_error)
            return None
    else:
        return WireCollection(**device_data)


def create_lblm(
    area: str = None, name: str = None
) -> Union[None, LBLM, LBLMCollection]:
    device_data = slac_db.get_device(area=area, device_type="lblms", name=name)
    if not device_data:
        return None
    if name:
        try:
            # this data is not available from YAML directly in this form, so we add it here.
            device_data.update({"name": name})
            return LBLM(**device_data)
        except ValidationError as field_error:
            print(field_error)
            return None
    else:
        return LBLMCollection(**device_data)


def create_bpm(area: str = None, name: str = None) -> Union[None, BPM, BPMCollection]:
    device_data = slac_db.get_device(area=area, device_type="bpms", name=name)
    if not device_data:
        return None
    if name:
        try:
            # this data is not available from YAML directly in this form, so we add it here.
            device_data.update({"name": name})
            return BPM(**device_data)
        except ValidationError as field_error:
            print(field_error)
            return None
    else:
        return BPMCollection(**device_data)


def create_tcav(
    area: str = None, name: str = None
) -> Union[None, TCAV, TCAVCollection]:
    device_data = slac_db.get_device(area=area, device_type="tcavs", name=name)
    if not device_data:
        return None
    if name:
        try:
            # this data is not available from YAML directly in this form, so we add it here.
            device_data.update({"name": name})
            return TCAV(**device_data)
        except ValidationError as field_error:
            print(field_error)
            return None
    else:
        return TCAVCollection(**device_data)


def create_pmt(area: str = None, name: str = None) -> Union[None, PMT]:
    device_data = slac_db.get_device(area=area, device_type="pmts", name=name)
    if not device_data:
        return None
    if name:
        try:
            device_data.update({"name": name})
            return PMT(**device_data)
        except ValidationError as field_error:
            print(field_error)
            return None
    else:
        return PMTCollection(**device_data)


def create_area(
    area: str = None, device_types: Optional[set] = None
) -> Union[None, Area]:
    """
    Constructs an Area object from YAML device configuration data.

    This function loads device metadata from a YAML file associated with the
    specified area and attempts to instantiate an Area object using that data.
    Each Area includes all devices defined in its YAML file (e.g., BPMs, LBLMs, Wires).
    If the YAML data is missing or fails Pydantic validation, the function returns None.

    Parameters:
        area (str): The name of the area to load. Must match a valid YAML file
                    containing device definitions.
        device_types (set, optional): Device types to include (e.g. {"bpms", "magnets"}).
                    If None, all supported types are included.

    Returns:
        Area: An Area object with all valid devices instantiated.
        None: If the YAML data is missing or contains validation errors.
    """
    yaml_data = slac_db.get_device(area=area)
    if not yaml_data:
        return None

    allowed = device_types if device_types is not None else _AREA_SUPPORTED_DEVICE_TYPES

    filtered_yaml_data = {}
    for device_type, device_payload in yaml_data.items():
        if device_type not in allowed:
            continue
        if device_type not in _AREA_SUPPORTED_DEVICE_TYPES:
            print(f"Skipping unsupported device type {device_type} in area {area}.")
            continue
        filtered_yaml_data[device_type] = device_payload

    try:
        return Area(name=area, **filtered_yaml_data)
    except ValidationError as field_error:
        print("Error trying to create area", area, " : ", field_error)
        return None


def create_beampath(
    beampath: str = None, device_types: Optional[set] = None
) -> Union[None, Beampath]:
    """
    Constructs a Beampath object from a YAML configuration file.

    This function reads a YAML file containing beampath definitions, flattens
    the list of associated areas for the specified beampath, and attempts to
    instantiate an Area object for each one. If successful, it returns a
    Beampath object containing all constructed Area instances.  Each Area object, in turn,
    instantiates all devices defined within that area.

    Parameters:
        beampath (str): The name of the beampath to load. Must exist as a key
                        in the beampaths.yaml file.
        device_types (set, optional): Device types to include (e.g. {"bpms"}).
                    If None, all supported types are included.

    Returns:
        Beampath: A Beampath object containing all valid Area instances.
        None: If the beampath name is not found or if any area cannot be created.
    """
    areas_to_create = slac_db.get_beampath_areas(beampath=beampath)
    areas = {}
    try:
        for area in areas_to_create:
            created_area = create_area(area=area, device_types=device_types)
            if created_area:
                areas[area] = created_area
        return Beampath(name=beampath, **{"areas": areas})
    except KeyError as ke:
        raise KeyError(
            "Area: ",
            ke.args[0],
            " does not exist in ",
            beampath,
        )

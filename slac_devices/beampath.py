import slac_devices
from typing import (
    Dict,
    List,
    Optional,
    Tuple,
    Union,
)

from slac_devices.area import (
    Area,
)
from slac_devices.device import Device
from slac_devices.magnet import Magnet
from slac_devices.screen import Screen
from slac_devices.wire import Wire
from slac_devices.bpm import BPM
from slac_devices.lblm import LBLM
from slac_devices.pmt import PMT
from slac_devices.tcav import TCAV

from pydantic import (
    SerializeAsAny,
)


class Beampath(slac_devices.BaseModel):
    """This class provides access to collections of machine areas
    in a beampath of LCLS/LCLS-II (for example: CU_SXR, or SC_HXR).
    The information for each collection is provided in YAML configuration
    files, where the areas are specified in the YAML file (beampaths.yaml).

    :cvar name: The name of the beampath
    :cvar areas: A collection of Areas as a Dict (keys are area names, values are Area objects)
    """

    name: str = None
    is_virtual: bool = False
    areas: Optional[Dict[str, SerializeAsAny[Area]]] = None

    def __init__(
        self,
        name,
        *args,
        **kwargs,
    ):
        super(Beampath, self).__init__(
            name=name,
            *args,
            **kwargs,
        )

    @property
    def area_names(self) -> List[str]:
        """Get a list of area names from the beampath"""
        if self.areas:
            return list(
                self.areas.keys(),
            )
        else:
            print(
                "Beampath not configured, could not get area names.",
            )

    def contains_areas(
        self,
        search_areas: Union[str, List[str]] = None,
    ) -> Union[bool, Dict[str, bool]]:
        """Check if the areas exists within the configured beampath.
        :returns Dict[str,bool]: key = area, value = True/False
        """
        if self.areas:
            # we want to take both single and multiple areas to check
            if isinstance(search_areas, str):
                # convert str to list without splitting 'xyz' into ['x','y','z']
                areas = [search_areas]
            else:
                # just use list as provided
                areas = search_areas
            return {area: (area in self.areas) for area in areas}
        else:
            print(
                f"Beampath not configured, could not search for {search_areas}",
            )
            return False

    def _device_counts(self) -> Dict[str, int]:
        """Count all devices by type across all areas."""
        counts = {
            "magnets": 0,
            "screens": 0,
            "wires": 0,
            "bpms": 0,
            "lblms": 0,
            "pmts": 0,
            "tcavs": 0,
        }

        if not self.areas:
            return counts

        for area in self.areas.values():
            area_counts = area._device_counts()
            for device_type, count in area_counts.items():
                counts[device_type] += count

        return counts

    def __repr__(self) -> str:
        """Return a string representation showing instantiated areas and device summary."""
        if not self.areas:
            return f"Beampath(name={self.name!r}, areas=[])"

        counts = self._device_counts()
        populated_types = [
            device_type for device_type, count in counts.items() if count > 0
        ]
        area_names = list(self.areas.keys())

        return (
            f"Beampath(name={self.name!r}, "
            f"num_areas={len(self.areas)}, "
            f"area_names={area_names}, "
            f"total_devices={sum(counts.values())}, "
            f"counts={counts}, "
            f"populated_types={populated_types})"
        )

    def find_device(self, device_name: str) -> Optional[Tuple[str, str, Device]]:
        """
        Find a device by name across all areas in the beampath.

        :param device_name: The name of the device to find
        :returns: Tuple of (area_name, device_type, device_object) or None if not found
        """
        if not self.areas:
            print("Beampath not configured.")
            return None

        collection_lookups = [
            ("magnet_collection", "magnets"),
            ("screen_collection", "screens"),
            ("wire_collection", "wires"),
            ("bpm_collection", "bpms"),
            ("lblm_collection", "lblms"),
            ("pmt_collection", "pmts"),
            ("tcav_collection", "tcavs"),
        ]

        for area_name, area in self.areas.items():
            for collection_attr, device_type_name in collection_lookups:
                collection = getattr(area, collection_attr, None)
                if collection:
                    device_dict = getattr(collection, device_type_name, None)
                    if device_dict and device_name in device_dict:
                        return (area_name, device_type_name, device_dict[device_name])

        print(f"Device '{device_name}' not found in beampath {self.name}.")
        return None

    def get_all_magnets(self) -> Dict[str, Magnet]:
        """Get all magnets across all areas, keyed by device name."""
        magnets = {}
        if self.areas:
            for area in self.areas.values():
                if area.magnet_collection:
                    magnets.update(area.magnets or {})
        return magnets

    def get_all_screens(self) -> Dict[str, Screen]:
        """Get all screens across all areas, keyed by device name."""
        screens = {}
        if self.areas:
            for area in self.areas.values():
                if area.screen_collection:
                    screens.update(area.screens or {})
        return screens

    def get_all_wires(self) -> Dict[str, Wire]:
        """Get all wires across all areas, keyed by device name."""
        wires = {}
        if self.areas:
            for area in self.areas.values():
                if area.wire_collection:
                    wires.update(area.wires or {})
        return wires

    def get_all_bpms(self) -> Dict[str, BPM]:
        """Get all BPMs across all areas, keyed by device name."""
        bpms = {}
        if self.areas:
            for area in self.areas.values():
                if area.bpm_collection:
                    bpms.update(area.bpms or {})
        return bpms

    def get_all_lblms(self) -> Dict[str, LBLM]:
        """Get all LBLMs across all areas, keyed by device name."""
        lblms = {}
        if self.areas:
            for area in self.areas.values():
                if area.lblm_collection:
                    lblms.update(area.lblms or {})
        return lblms

    def get_all_pmts(self) -> Dict[str, PMT]:
        """Get all PMTs across all areas, keyed by device name."""
        pmts = {}
        if self.areas:
            for area in self.areas.values():
                if area.pmt_collection:
                    pmts.update(area.pmts or {})
        return pmts

    def get_all_tcavs(self) -> Dict[str, TCAV]:
        """Get all TCAVs across all areas, keyed by device name."""
        tcavs = {}
        if self.areas:
            for area in self.areas.values():
                if area.tcav_collection:
                    tcavs.update(area.tcavs or {})
        return tcavs

    def get_all_devices(
        self,
    ) -> Dict[str, Device]:
        """Get all devices of all types across all areas, keyed by device name."""
        all_devices = {}
        all_devices.update(self.get_all_magnets())
        all_devices.update(self.get_all_screens())
        all_devices.update(self.get_all_wires())
        all_devices.update(self.get_all_bpms())
        all_devices.update(self.get_all_lblms())
        all_devices.update(self.get_all_pmts())
        all_devices.update(self.get_all_tcavs())
        return all_devices

    @property
    def magnets(self) -> Dict[str, Magnet]:
        """Get all magnets across all areas, keyed by device name."""
        return self.get_all_magnets()

    @property
    def screens(self) -> Dict[str, Screen]:
        """Get all screens across all areas, keyed by device name."""
        return self.get_all_screens()

    @property
    def wires(self) -> Dict[str, Wire]:
        """Get all wires across all areas, keyed by device name."""
        return self.get_all_wires()

    @property
    def bpms(self) -> Dict[str, BPM]:
        """Get all BPMs across all areas, keyed by device name."""
        return self.get_all_bpms()

    @property
    def lblms(self) -> Dict[str, LBLM]:
        """Get all LBLMs across all areas, keyed by device name."""
        return self.get_all_lblms()

    @property
    def pmts(self) -> Dict[str, PMT]:
        """Get all PMTs across all areas, keyed by device name."""
        return self.get_all_pmts()

    @property
    def tcavs(self) -> Dict[str, TCAV]:
        """Get all TCAVs across all areas, keyed by device name."""
        return self.get_all_tcavs()

    @property
    def devices(
        self,
    ) -> Dict[str, Device]:
        """Get all devices of all types across all areas, keyed by device name."""
        return self.get_all_devices()

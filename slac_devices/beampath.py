import slac_devices
from typing import (
    Any,
    Dict,
    List,
    Union,
)

from slac_devices.area import (
    Area,
)


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
    areas: Dict[str, SerializeAsAny[Area]] = None

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

    @property
    def magnets(self) -> Dict[str, Any]:
        """All magnets across all areas, keyed by device name."""
        result = {}
        if self.areas:
            for area in self.areas.values():
                if area.magnet_collection:
                    result.update(area.magnet_collection.magnets)
        return result

    @property
    def screens(self) -> Dict[str, Any]:
        """All screens across all areas, keyed by device name."""
        result = {}
        if self.areas:
            for area in self.areas.values():
                if area.screen_collection:
                    result.update(area.screen_collection.screens)
        return result

    @property
    def wires(self) -> Dict[str, Any]:
        """All wires across all areas, keyed by device name."""
        result = {}
        if self.areas:
            for area in self.areas.values():
                if area.wire_collection:
                    result.update(area.wire_collection.wires)
        return result

    @property
    def bpms(self) -> Dict[str, Any]:
        """All BPMs across all areas, keyed by device name."""
        result = {}
        if self.areas:
            for area in self.areas.values():
                if area.bpm_collection:
                    result.update(area.bpm_collection.bpms)
        return result

    @property
    def lblms(self) -> Dict[str, Any]:
        """All LBLMs across all areas, keyed by device name."""
        result = {}
        if self.areas:
            for area in self.areas.values():
                if area.lblm_collection:
                    result.update(area.lblm_collection.lblms)
        return result

    @property
    def pmts(self) -> Dict[str, Any]:
        """All PMTs across all areas, keyed by device name."""
        result = {}
        if self.areas:
            for area in self.areas.values():
                if area.pmt_collection:
                    result.update(area.pmt_collection.pmts)
        return result

    @property
    def tcavs(self) -> Dict[str, Any]:
        """All TCAVs across all areas, keyed by device name."""
        result = {}
        if self.areas:
            for area in self.areas.values():
                if area.tcav_collection:
                    result.update(area.tcav_collection.tcavs)
        return result

    @property
    def validation_errors(self) -> Dict[str, Dict[str, Dict[str, str]]]:
        """Validation failures grouped by area then device collection.

        Shape:
            {
                "AREA_NAME": {
                    "screens": {"BROKEN_SCREEN": "..."},
                    "magnets": {"BAD_MAG": "..."},
                }
            }
        """
        result: Dict[str, Dict[str, Dict[str, str]]] = {}
        if not self.areas:
            return result
        for area_name, area in self.areas.items():
            area_errors = getattr(area, "validation_errors", None)
            if area_errors:
                result[area_name] = area_errors
        return result

    def find(self, name: str) -> Union[Any, None]:
        """Search all areas and device types for a device by name.

        Returns the first match found, or None if not found.
        """
        _collections = [
            ("magnet_collection", "magnets"),
            ("screen_collection", "screens"),
            ("wire_collection", "wires"),
            ("bpm_collection", "bpms"),
            ("lblm_collection", "lblms"),
            ("pmt_collection", "pmts"),
            ("tcav_collection", "tcavs"),
        ]
        if self.areas:
            for area in self.areas.values():
                for coll_attr, device_attr in _collections:
                    coll = getattr(area, coll_attr)
                    if coll:
                        devices = getattr(coll, device_attr)
                        if name in devices:
                            return devices[name]
        return None

    def __repr__(self) -> str:
        if not self.areas:
            return f"Beampath(name={self.name!r}, areas=0)"
        counts = {
            "magnets": len(self.magnets),
            "screens": len(self.screens),
            "wires": len(self.wires),
            "bpms": len(self.bpms),
            "lblms": len(self.lblms),
            "pmts": len(self.pmts),
            "tcavs": len(self.tcavs),
        }
        device_summary = ", ".join(
            f"{k}={v}" for k, v in counts.items() if v > 0
        )
        return (
            f"Beampath(name={self.name!r}, areas={len(self.areas)},"
            f" {device_summary})"
        )

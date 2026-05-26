import slac_devices
from typing import (
    Any,
    Dict,
    Optional,
    Union,
)

from slac_devices.magnet import (
    Magnet,
    MagnetCollection,
)

from slac_devices.screen import (
    Screen,
    ScreenCollection,
)

from slac_devices.wire import (
    Wire,
    WireCollection,
)
from slac_devices.bpm import (
    BPM,
    BPMCollection,
)
from slac_devices.lblm import (
    LBLM,
    LBLMCollection,
)
from slac_devices.pmt import PMT, PMTCollection
from slac_devices.tcav import TCAV, TCAVCollection

from pydantic import SerializeAsAny, Field, field_validator
from pydantic import ValidationError, ValidationInfo


def _prune_invalid_devices(
    area_name: str,
    device_type: str,
    device_data: Dict[str, Any],
    device_class,
) -> Union[Dict[str, Any], None]:
    if not device_data:
        return None

    if not isinstance(device_data, dict):
        print(
            f"Skipping {device_type} collection in {area_name}: "
            + "collection payload is not a dictionary."
        )
        return None

    valid_devices = {}
    for name, payload in device_data.items():
        if not isinstance(payload, dict):
            print(
                f"Skipping {device_type} {name} in {area_name}: "
                + "device definition is not a dictionary."
            )
            continue

        payload_copy = dict(payload)
        payload_copy["name"] = name
        try:
            device = device_class(**payload_copy)
        except (ValidationError, TypeError, Exception) as field_error:
            print(
                f"Skipping invalid {device_type} {name} in {area_name}: {field_error}"
            )
            continue
        valid_devices[name] = device

    if not valid_devices:
        return None
    return valid_devices


class Area(slac_devices.BaseModel):
    """This class provides access to collections of hardware components
    in a given machine area of LCLS/LCLS-II (for example: BC1, or BC2).
    The information for each collection is provided in YAML configuration
    files, where the filename is the machine area.

    :cvar magnet_collection: The MagnetCollection for this area
    :cvar screen_collection: The ScreenCollection for this area
    """

    name: str = None
    magnet_collection: Optional[
        Union[
            SerializeAsAny[MagnetCollection],
            None,
        ]
    ] = Field(
        alias="magnets",
        default=None,
    )
    screen_collection: Optional[
        Union[
            SerializeAsAny[ScreenCollection],
            None,
        ]
    ] = Field(
        alias="screens",
        default=None,
    )
    wire_collection: Optional[
        Union[
            SerializeAsAny[WireCollection],
            None,
        ]
    ] = Field(
        alias="wires",
        default=None,
    )
    bpm_collection: Optional[
        Union[
            SerializeAsAny[BPMCollection],
            None,
        ]
    ] = Field(
        alias="bpms",
        default=None,
    )
    lblm_collection: Optional[
        Union[
            SerializeAsAny[LBLMCollection],
            None,
        ]
    ] = Field(
        alias="lblms",
        default=None,
    )
    pmt_collection: Optional[
        Union[
            SerializeAsAny[PMTCollection],
            None,
        ]
    ] = Field(
        alias="pmts",
        default=None,
    )
    tcav_collection: Optional[
        Union[
            SerializeAsAny[TCAVCollection],
            None,
        ]
    ] = Field(
        alias="tcavs",
        default=None,
    )

    def __init__(
        self,
        name,
        *args,
        **kwargs,
    ):
        super(Area, self).__init__(
            name=name,
            *args,
            **kwargs,
        )

    def _device_counts(self) -> Dict[str, int]:
        collection_map = {
            "magnets": (self.magnet_collection, "magnets"),
            "screens": (self.screen_collection, "screens"),
            "wires": (self.wire_collection, "wires"),
            "bpms": (self.bpm_collection, "bpms"),
            "lblms": (self.lblm_collection, "lblms"),
            "pmts": (self.pmt_collection, "pmts"),
            "tcavs": (self.tcav_collection, "tcavs"),
        }

        counts = {}
        for device_type, (collection, attr_name) in collection_map.items():
            if collection is None:
                counts[device_type] = 0
                continue
            devices = getattr(collection, attr_name, None) or {}
            counts[device_type] = len(devices)
        return counts

    def __repr__(self) -> str:
        counts = self._device_counts()
        populated_types = [
            device_type for device_type, count in counts.items() if count > 0
        ]
        return (
            f"Area(name={self.name!r}, total_devices={sum(counts.values())}, "
            + f"counts={counts}, populated_types={populated_types})"
        )

    @classmethod
    def _area_name_from_info(cls, info: ValidationInfo) -> str:
        if info and info.data and "name" in info.data:
            return str(info.data["name"])
        return "<unknown>"

    @field_validator(
        "magnet_collection",
        mode="before",
    )
    def validate_magnets(cls, v: Dict[str, Any], info: ValidationInfo):
        valid_magnets = _prune_invalid_devices(
            area_name=cls._area_name_from_info(info),
            device_type="magnets",
            device_data=v,
            device_class=Magnet,
        )
        if not valid_magnets:
            return None
        return MagnetCollection.model_construct(devices=valid_magnets)

    @field_validator(
        "screen_collection",
        mode="before",
    )
    def validate_screens(cls, v: Dict[str, Any], info: ValidationInfo):
        valid_screens = _prune_invalid_devices(
            area_name=cls._area_name_from_info(info),
            device_type="screens",
            device_data=v,
            device_class=Screen,
        )
        if not valid_screens:
            return None
        return ScreenCollection.model_construct(devices=valid_screens)

    @field_validator(
        "wire_collection",
        mode="before",
    )
    def validate_wires(cls, v: Dict[str, Any], info: ValidationInfo):
        valid_wires = _prune_invalid_devices(
            area_name=cls._area_name_from_info(info),
            device_type="wires",
            device_data=v,
            device_class=Wire,
        )
        if not valid_wires:
            return None
        return WireCollection.model_construct(wires=valid_wires)

    @field_validator(
        "bpm_collection",
        mode="before",
    )
    def validate_bpms(cls, v: Dict[str, Any], info: ValidationInfo):
        valid_bpms = _prune_invalid_devices(
            area_name=cls._area_name_from_info(info),
            device_type="bpms",
            device_data=v,
            device_class=BPM,
        )
        if not valid_bpms:
            return None
        return BPMCollection.model_construct(bpms=valid_bpms)

    @field_validator(
        "lblm_collection",
        mode="before",
    )
    def validate_lblms(cls, v: Dict[str, Any], info: ValidationInfo):
        valid_lblms = _prune_invalid_devices(
            area_name=cls._area_name_from_info(info),
            device_type="lblms",
            device_data=v,
            device_class=LBLM,
        )
        if not valid_lblms:
            return None
        return LBLMCollection.model_construct(lblms=valid_lblms)

    @field_validator(
        "pmt_collection",
        mode="before",
    )
    def validate_pmts(cls, v: Dict[str, Any], info: ValidationInfo):
        valid_pmts = _prune_invalid_devices(
            area_name=cls._area_name_from_info(info),
            device_type="pmts",
            device_data=v,
            device_class=PMT,
        )
        if not valid_pmts:
            return None
        return PMTCollection.model_construct(pmts=valid_pmts)

    @field_validator(
        "tcav_collection",
        mode="before",
    )
    def validate_tcavs(cls, v: Dict[str, Any], info: ValidationInfo):
        valid_tcavs = _prune_invalid_devices(
            area_name=cls._area_name_from_info(info),
            device_type="tcavs",
            device_data=v,
            device_class=TCAV,
        )
        if not valid_tcavs:
            return None
        return TCAVCollection.model_construct(tcavs=valid_tcavs)

    @property
    def magnets(
        self,
    ) -> Union[
        Dict[str, Magnet],
        None,
    ]:
        """
        A Dict[str, Magnet] for this area, where the dict keys are magnet names.
        If no magnets exist for this area, this property is None.
        """
        if self.magnet_collection:
            return self.magnet_collection.magnets
        else:
            print("Area does not contain magnets.")
            return None

    @property
    def screens(
        self,
    ) -> Union[
        Dict[str, Screen],
        None,
    ]:
        """
        A Dict[str, Screen] for this area, where the dict keys are screen names
        If no screens exist for this area, this property is None.
        """
        if self.screen_collection:
            return self.screen_collection.screens
        else:
            print("Area does not contain screens.")
            return None

    @property
    def wires(
        self,
    ) -> Union[
        Dict[str, Wire],
        None,
    ]:
        """
        A Dict[str, Wire] for this area, where the dict keys are wire names
        If no wires exist for this area, this property is None
        """
        if self.wire_collection:
            return self.wire_collection.wires
        else:
            print("Area does not contain wires.")
            return None

    @property
    def bpms(
        self,
    ) -> Union[
        Dict[str, BPM],
        None,
    ]:
        """
        A Dict[str, BPM] for this area, where the dict keys are bpm names
        If no bpms exist for this area, this property is None
        """
        if self.bpm_collection:
            return self.bpm_collection.bpms
        else:
            print("Area does not contain bpms.")
            return None

    @property
    def lblms(
        self,
    ) -> Union[
        Dict[str, LBLM],
        None,
    ]:
        """
        A Dict[str, LBLM] for this area, where the dict keys are lblm names
        If no lblms exist for this area, this property is None
        """
        if self.lblm_collection:
            return self.lblm_collection.lblms
        else:
            print("Area does not contain lblms.")
            return None

    @property
    def pmts(
        self,
    ) -> Union[
        Dict[str, PMT],
        None,
    ]:
        """
        A Dict[str, PMT] for this area, where the dict keys are pmt names
        If no pmts exist for this area, this property is None
        """
        if self.pmt_collection:
            return self.pmt_collection.pmts
        else:
            print("Area does not contain pmts.")
            return None

    @property
    def tcavs(
        self,
    ) -> Union[
        Dict[str, TCAV],
        None,
    ]:
        """
        A Dict[str, TCAV] for this area, where the dict keys are tcav names.
        If no tcavs exist for this area, this property is None.
        """
        if self.tcav_collection:
            return self.tcav_collection.tcavs
        else:
            print("Area does not contain tcavs.")
            return None

    def does_magnet_exist(
        self,
        magnet_name: str = None,
    ) -> bool:
        return magnet_name in self.magnets

    def does_screen_exist(
        self,
        screen_name: str = None,
    ) -> bool:
        return screen_name in self.screens

    def does_wire_exist(
        self,
        wire_name: str = None,
    ) -> bool:
        return wire_name in self.wires

    def does_bpm_exist(
        self,
        bpm_name: str = None,
    ) -> bool:
        return bpm_name in self.bpms

    def does_lblm_exist(
        self,
        lblm_name: str = None,
    ) -> bool:
        return lblm_name in self.lblms

    def does_pmt_exist(
        self,
        pmt_name: str = None,
    ) -> bool:
        return pmt_name in self.pmts

    def does_tcav_exist(
        self,
        tcav_name: str = None,
    ) -> bool:
        return tcav_name in self.tcavs

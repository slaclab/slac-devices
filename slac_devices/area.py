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

from pydantic import (
    SerializeAsAny,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)


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
    validation_errors: Dict[str, Dict[str, str]] = Field(default_factory=dict)

    @staticmethod
    def _collect_valid_devices(
        devices: Any,
        device_cls: Any,
        collection_name: str,
        errors: Dict[str, Dict[str, str]],
    ) -> Dict[str, Any]:
        """Keep valid device payloads and record failures by name."""
        if not devices:
            return {}
        if not isinstance(devices, dict):
            errors.setdefault(collection_name, {})["__collection__"] = (
                f"Expected dict, got {type(devices).__name__}"
            )
            return {}

        valid_devices = {}
        for name, device in devices.items():
            try:
                payload = dict(device)
                payload.update({"name": name})
                # Validate each device entry independently.
                device_cls(**payload)
                valid_devices[name] = device
            except ValidationError as ve:
                errors.setdefault(collection_name, {})[name] = str(ve)
            except Exception as ex:
                errors.setdefault(collection_name, {})[name] = str(ex)
        return valid_devices

    @model_validator(mode="before")
    def _tolerant_device_validation(cls, values: Any) -> Any:
        """Filter invalid devices before collection construction.

        Validation failures are recorded instead of failing Area creation.
        """
        if not isinstance(values, dict):
            return values

        errors: Dict[str, Dict[str, str]] = dict(
            values.get("validation_errors") or {}
        )
        collection_defs = [
            ("magnets", Magnet),
            ("screens", Screen),
            ("wires", Wire),
            ("bpms", BPM),
            ("lblms", LBLM),
            ("pmts", PMT),
            ("tcavs", TCAV),
        ]

        for collection_name, device_cls in collection_defs:
            raw_devices = values.get(collection_name)
            valid_devices = cls._collect_valid_devices(
                raw_devices,
                device_cls,
                collection_name,
                errors,
            )
            if raw_devices is not None:
                values[collection_name] = valid_devices or None

        values["validation_errors"] = errors
        return values

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

    @field_validator(
        "magnet_collection",
        mode="before",
    )
    def validate_magnets(cls, v: Dict[str, Any]):
        if isinstance(v, MagnetCollection):
            return v
        if not v:
            return None
        return MagnetCollection(magnets=v)

    @field_validator(
        "screen_collection",
        mode="before",
    )
    def validate_screens(cls, v: Dict[str, Any]):
        if isinstance(v, ScreenCollection):
            return v
        if not v:
            return None
        return ScreenCollection(screens=v)

    @field_validator(
        "wire_collection",
        mode="before",
    )
    def validate_wires(cls, v: Dict[str, Any]):
        if isinstance(v, WireCollection):
            return v
        if not v:
            return None
        return WireCollection(wires=v)

    @field_validator(
        "bpm_collection",
        mode="before",
    )
    def validate_bpms(cls, v: Dict[str, Any]):
        if isinstance(v, BPMCollection):
            return v
        if not v:
            return None
        return BPMCollection(bpms=v)

    @field_validator(
        "lblm_collection",
        mode="before",
    )
    def validate_lblms(cls, v: Dict[str, Any]):
        if isinstance(v, LBLMCollection):
            return v
        if not v:
            return None
        return LBLMCollection(lblms=v)

    @field_validator(
        "pmt_collection",
        mode="before",
    )
    def validate_pmts(cls, v: Dict[str, Any]):
        if isinstance(v, PMTCollection):
            return v
        if not v:
            return None
        return PMTCollection(pmts=v)

    @field_validator(
        "tcav_collection",
        mode="before",
    )
    def validate_tcavs(cls, v: Dict[str, Any]):
        if isinstance(v, TCAVCollection):
            return v
        if not v:
            return None
        return TCAVCollection(tcavs=v)

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
        return None

    @property
    def tcavs(
        self,
    ) -> Union[
        Dict[str, TCAV],
        None,
    ]:
        """
        A Dict[str, TCAV] for this area, where the dict keys are tcav names
        If no tcavs exist for this area, this property is None
        """
        if self.tcav_collection:
            return self.tcav_collection.tcavs
        return None

    def does_magnet_exist(
        self,
        magnet_name: str = None,
    ) -> bool:
        return bool(self.magnets and magnet_name in self.magnets)

    def does_screen_exist(
        self,
        screen_name: str = None,
    ) -> bool:
        return bool(self.screens and screen_name in self.screens)

    def does_wire_exist(
        self,
        wire_name: str = None,
    ) -> bool:
        return bool(self.wires and wire_name in self.wires)

    def does_bpm_exist(
        self,
        bpm_name: str = None,
    ) -> bool:
        return bool(self.bpms and bpm_name in self.bpms)

    def does_lblm_exist(
        self,
        lblm_name: str = None,
    ) -> bool:
        return bool(self.lblms and lblm_name in self.lblms)

    def does_pmt_exist(
        self,
        pmt_name: str = None,
    ) -> bool:
        return bool(self.pmts and pmt_name in self.pmts)

    def does_tcav_exist(
        self,
        tcav_name: str = None,
    ) -> bool:
        return bool(self.tcavs and tcav_name in self.tcavs)

    def __repr__(self) -> str:
        magnets = self.magnets or {}
        screens = self.screens or {}
        wires = self.wires or {}
        bpms = self.bpms or {}
        lblms = self.lblms or {}
        pmts = self.pmts or {}
        tcavs = self.tcavs or {}
        counts = {
            "magnets": len(magnets),
            "screens": len(screens),
            "wires": len(wires),
            "bpms": len(bpms),
            "lblms": len(lblms),
            "pmts": len(pmts),
            "tcavs": len(tcavs),
        }
        device_summary = ", ".join(
            f"{k}={v}" for k, v in counts.items() if v > 0
        )
        if device_summary:
            return f"Area(name={self.name!r}, {device_summary})"
        return f"Area(name={self.name!r})"

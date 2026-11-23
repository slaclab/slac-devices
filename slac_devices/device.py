import slac_devices
from pydantic import (
    SerializeAsAny,
    ConfigDict,
    field_validator,
    field_serializer,
    model_validator,
    ValidationInfo,
)
from typing import Any, List, Union, Callable, Dict, Optional
from epics import PV
from slac_tools import LazyPV


class PVSet(slac_devices.BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="forbid",
        frozen=True,
    )

    @field_validator("*", mode="wrap")
    def validate_pv_fields(cls, v, handler) -> LazyPV:
        if v is None:
            return None
        if isinstance(v, LazyPV):
            return v
        return LazyPV(v)

    @field_serializer("*", when_used="unless-none")
    def serialize_pv_fields(self, v: LazyPV, _info) -> str:
        return v.pvname


class ControlInformation(slac_devices.BaseModel):
    model_config = ConfigDict(
        frozen=True,
    )
    control_name: str
    PVs: PVSet

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super(
            ControlInformation,
            self,
        ).__init__(
            *args,
            **kwargs,
        )


class Metadata(slac_devices.BaseModel):
    area: str
    beam_path: List[str]
    sum_l_meters: Union[float, None]
    type: Optional[str] = None
    safe_level: Optional[float] = None
    read_tolerance: Optional[float] = None
    hardware: Optional[dict] = None

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super(
            Metadata,
            self,
        ).__init__(
            *args,
            **kwargs,
        )


class ApplyDeviceCallbackError(Exception):
    def __init__(
        self,
        message: str,
        *args,
        **kwargs,
    ) -> None:
        super(
            ApplyDeviceCallbackError,
            self,
        ).__init__(
            message,
            *args,
            **kwargs,
        )


class RemoveDeviceCallbackError(Exception):
    def __init__(
        self,
        message: str,
        *args,
        **kwargs,
    ) -> None:
        super(
            RemoveDeviceCallbackError,
            self,
        ).__init__(
            message,
            *args,
            **kwargs,
        )


def _to_virtual_prefix(pvname: str, prefix: str = "VM-") -> str:
    return pvname if pvname.startswith(prefix) else f"{prefix}{pvname}"

class Device(slac_devices.BaseModel):
    name: str = None
    controls_information: SerializeAsAny[ControlInformation]
    metadata: SerializeAsAny[Metadata]
    is_virtual: bool = False

    def __init__(
        self,
        is_virtual: bool = False,
        *args,
        **kwargs,
    ):
        super(Device, self).__init__(
            *args,
            is_virtual=is_virtual,
            **kwargs,
        )

    @model_validator(mode="before")
    @classmethod
    def _apply_virtual_prefix(cls, data):
        if not isinstance(data, dict) or not data.get("is_virtual"):
            return data
        controls = data.get("controls_information")
        if controls is None or controls == {}:
            return data
        if isinstance(controls, ControlInformation):
            controls = controls.model_dump()
        pvs = controls.get("PVs")
        if pvs is None:
            return data
        if isinstance(pvs, PVSet):
            pvs = pvs.model_dump()
        converted_pvs = {}
        for name, pv in pvs.items():
            if pv is None:
                converted_pvs[name] = None
            elif isinstance(pv, LazyPV):
                converted_pvs[name] = _to_virtual_prefix(pv.pvname)
            else:
                converted_pvs[name] = _to_virtual_prefix(pv)
        return {
            **data,
            "controls_information": {
                **controls,
                "PVs": converted_pvs,
            },
        }

    @property
    def area(self) -> str:
        """The machine area for this device"""
        return self.metadata.area

    @property
    def sum_l_meters(self) -> float:
        """The position for this device in the design in meters"""
        return self.metadata.sum_l_meters

    @property
    def z_location(self) -> float:
        """The position for this device in the design in meters (alias for sum_l_meters)"""
        return self.metadata.sum_l_meters

    @property
    def beam_path(self) -> List[str]:
        """The list of beampaths that include this device"""
        return self.metadata.beam_path

    def get_callbacks(self, pv: str) -> Union[None, dict]:
        """Find which callbacks are tied for the given PV"""
        pv_obj = self._get_pv_object_from_str(pv)
        if pv_obj:
            return pv_obj.callbacks
        return None

    def _is_callback_already_assigned(
        self,
        pv: PV,
        callback_function: Callable,
    ) -> bool:
        """
        Check if a given callback function is already applied to a PV object
        :param pv: an EPICS PV object associated with the class
        :type pv: :class:`epics.PV`
        :param callback_function: The function that will be checked against the pv callback list
        :type callback_function: Callable
        :return: True if callback is already assigned, False is not.
        """
        # items of this list are of the form [(function, kw-args), (function, kw-args), ..]
        applied_callback_functions = list(pv.callbacks.values())
        callback_exists = any(
            [callback_function == f for f, _ in applied_callback_functions]
        )
        return callback_exists

    def _get_callback_index(
        self,
        pv: PV,
        callback_function: Callable,
    ) -> Union[None, int]:
        for index, callback in pv.callbacks.items():
            f, _ = callback
            if f == callback_function:
                return index
        return None

    def _get_attribute(self, attr: str) -> Union[object, None]:
        """
        Wrap around getattr for testing purposes.
        We can mock this function much easier than getattr directly
        """
        return getattr(self, attr, None)

    def _get_pv_object_from_str(self, pv: str) -> PV:
        pv_obj = self._get_attribute("_" + pv)
        return pv_obj

    def add_callback_to_pv(
        self,
        pv: str,
        function: Callable,
    ) -> None:
        """Add a callback function to a given PV that is called upon PV-value change."""
        # check function args
        if not isinstance(pv, str):
            raise ApplyDeviceCallbackError(f"variable {pv} must be of type str")
        if not isinstance(function, Callable):
            raise ApplyDeviceCallbackError(f"variable {function} must be a Callable.")
        # function args okay, try to access class member variable
        pv_obj = self._get_pv_object_from_str(pv)
        if not pv_obj or not isinstance(pv_obj, PV):
            raise ApplyDeviceCallbackError(f"could not find PV attribute for {pv}")
        # class member variable exists, check if callback is already assigned
        if self._is_callback_already_assigned(pv_obj, function):
            raise ApplyDeviceCallbackError(
                f"function {function.__name__} exists as a callback for {pv}"
            )
        # callback not assigned, so lets add the callback:
        pv_obj.add_callback(function)

    def remove_callback_from_pv(
        self,
        pv: str,
        function: Callable,
    ) -> None:
        """Remove a callback function to a given PV."""
        if not isinstance(pv, str):
            raise RemoveDeviceCallbackError(f"variable {pv} must be of type str")
        if not isinstance(function, Callable):
            raise RemoveDeviceCallbackError(f"variable {function} must be a Callable.")
        # function args okay, try to access class member variable
        pv_obj = self._get_pv_object_from_str(pv)
        if not pv_obj or not isinstance(pv_obj, PV):
            raise RemoveDeviceCallbackError(f"could not find PV attribute for {pv}")
        # class member variable exists, check if callback exists
        if not self._is_callback_already_assigned(pv_obj, function):
            raise RemoveDeviceCallbackError(
                f"function {function.__name__} does not exist as a callback for {pv}"
            )
        index = self._get_callback_index(pv_obj, function)
        if index:
            pv_obj.remove_callback(index)

    def scan(
        self,
        scan_settings: List[float],
        function: Optional[callable] = None,
    ) -> None:
        """
        Scans device parameters and calls the provided function after each setting
        is achieved.
        """
        raise NotImplementedError


def prepare_device_payloads(
    v: Dict[str, Any],
    device_class: type,
    info: ValidationInfo,
) -> Dict[str, Any]:
    """
    Shared "before" validation for device collections.

    Adds the ``name`` (the dict key) and the collection's ``is_virtual`` flag
    to each raw device payload so the Device class can be built from it.
    Already-constructed devices are left untouched.

    The collection must declare ``is_virtual`` *before* its devices field,
    because ``info.data`` only holds fields that have already been validated.
    """
    is_virtual = bool(info.data.get("is_virtual", False))
    for name, device in v.items():
        if isinstance(device, device_class):
            continue
        device = dict(device)
        device["name"] = name
        device.setdefault("is_virtual", is_virtual)
        v[name] = device
    return v


class DeviceCollection(slac_devices.BaseModel):
    is_virtual: bool = False
    devices: Dict[str, SerializeAsAny[Device]] = None

    @field_validator("devices", mode="before")
    def _validate_devices(cls, v, info: ValidationInfo):
        """
        Add name and is_virtual fields to data that will be passed to Device class
        and then use that dictionary to create each Device.
        """
        return prepare_device_payloads(v, Device, info)

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super(
            DeviceCollection,
            self,
        ).__init__(
            *args,
            **kwargs,
        )

    @property
    def device_names(self) -> List[str]:
        """Get all device names in the collection"""
        return list(self.devices.keys())

from typing import Dict

from pydantic import BaseModel, SerializeAsAny, field_validator, ValidationInfo

from slac_devices.device import (
    Device,
    PVSet,
    ControlInformation,
    Metadata,
    prepare_device_payloads,
)
from slac_timing import Buffer
from epics import PV


class ToroidPVSet(PVSet):
    tmit: PV

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class ToroidControlInformation(ControlInformation):
    PVs: SerializeAsAny[ToroidPVSet]

    def __init__(self, *args, **kwargs):
        super(ToroidControlInformation, self).__init__(*args, **kwargs)


class ToroidMetadata(Metadata):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class Toroid(Device):
    controls_information: SerializeAsAny[ToroidControlInformation]
    metadata: SerializeAsAny[ToroidMetadata]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def tmit(self):
        """Get current TMIT value."""
        return self.controls_information.PVs.tmit.get()

    def tmit_buffer(self, buffer: Buffer, **kwargs):
        """Retrieve per-pulse TMIT data from timing buffer."""
        return buffer.get(f"{self.controls_information.control_name}:TMIT", **kwargs)


class ToroidCollection(BaseModel):
    is_virtual: bool = False
    toroids: Dict[str, SerializeAsAny[Toroid]]

    @field_validator("toroids", mode="before")
    def validate_toroids(cls, v, info: ValidationInfo) -> Dict[str, Toroid]:
        return prepare_device_payloads(v, Toroid, info)

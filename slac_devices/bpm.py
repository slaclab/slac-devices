from pydantic import (
    BaseModel,
    SerializeAsAny,
    field_validator,
)
from typing import (
    Dict,
    List,
    Optional,
    Union,
)
from slac_devices.device import (
    Device,
    ControlInformation,
    Metadata,
    PVSet,
)
from slac_timing import Buffer
from epics import PV

EPICS_ERROR_MESSAGE = "Unable to connect to EPICS."


class BPMPVSet(PVSet):
    x: PV
    y: PV
    tmit: PV

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


# TODO
class BPMControlInformation(ControlInformation):
    PVs: SerializeAsAny[BPMPVSet]
    _ctrl_options: SerializeAsAny[Optional[Dict[str, int]]] = dict()

    def __init__(self, *args, **kwargs):
        super(BPMControlInformation, self).__init__(*args, **kwargs)


# TODO
class BPMMetadata(Metadata):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class BPM(Device):
    controls_information: SerializeAsAny[BPMControlInformation]
    metadata: SerializeAsAny[BPMMetadata]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def x(self):
        """Get TMIT value"""
        return self.controls_information.PVs.x.get()

    def x_buffer(self, buffer: Buffer, **kwargs):
        """Retrieve X signal data from timing buffer"""
        return buffer.get(f"{self.controls_information.control_name}:X", **kwargs)

    @property
    def y(self):
        """Get TMIT value"""
        return self.controls_information.PVs.y.get()

    def y_buffer(self, buffer: Buffer, **kwargs):
        """Retrieve Y signal data from timing buffer"""
        return buffer.get(f"{self.controls_information.control_name}:Y", **kwargs)

    @property
    def tmit(self):
        """Get TMIT value"""
        return self.controls_information.PVs.tmit.get()

    def tmit_buffer(self, buffer: Buffer, **kwargs):
        """Retrieve TMIT signal data from timing buffer"""
        return buffer.get(f"{self.controls_information.control_name}:TMIT", **kwargs)


class BPMCollection(BaseModel):
    bpms: Dict[str, SerializeAsAny[BPM]]

    @field_validator("bpms", mode="before")
    def validate_bpms(cls, v) -> Dict[str, BPM]:
        for name, bpm in v.items():
            if isinstance(bpm, BPM):
                continue
            bpm = dict(bpm)
            bpm.update({"name": name})
            v.update({name: bpm})
        return v

    def get_buffer_data(
        self, buffer, suffix: str = "TMIT", **kwargs
    ) -> Dict[str, Optional[list]]:
        """Retrieve buffer data for all BPMs in the collection.

        Args:
            buffer: An edef EventDefinition or BSABuffer object.
            suffix: PV suffix to read (e.g. "TMIT", "X", "Y").
            **kwargs: Passed to buffer.get() (e.g. pad, retries).

        Returns:
            Dict mapping BPM name to data array, or None for unreachable BPMs.
        """

        def _yield_buffer_data():
            for name, bpm in self.bpms.items():
                address = f"{bpm.controls_information.control_name}:{suffix}"
                try:
                    data = buffer.get(address, **kwargs)
                except (TypeError, BufferError):
                    data = None
                yield name, data

        return dict(_yield_buffer_data())

    def _make_bpm_names_list_from_args(
        self, args: Union[str, List[str], None]
    ) -> List[str]:
        bpm_names = args
        if bpm_names:
            if isinstance(bpm_names, str):
                bpm_names = [args]
        else:
            bpm_names = list(self.bpms.keys())
        return bpm_names

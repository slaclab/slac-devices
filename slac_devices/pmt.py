from pydantic import (
    BaseModel,
    SerializeAsAny,
    field_validator,
)
from typing import (
    Dict,
    Optional,
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


class PMTPVSet(PVSet):
    qdcraw: PV

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class PMTControlInformation(ControlInformation):
    PVs: SerializeAsAny[PMTPVSet]
    _ctrl_options: SerializeAsAny[Optional[Dict[str, int]]] = dict()

    def __init__(self, *args, **kwargs):
        super(PMTControlInformation, self).__init__(*args, **kwargs)


class PMTMetadata(Metadata):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class PMT(Device):
    controls_information: SerializeAsAny[PMTControlInformation]
    metadata: SerializeAsAny[PMTMetadata]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def qdcraw_buffer(self, buffer: Buffer, **kwargs):
        """Retrieve QDCRAW signal data from timing buffer"""
        return buffer.get(f"{self.controls_information.control_name}:QDCRAW", **kwargs)

    @property
    def qdcraw(self):
        """Get QDCRAW value"""
        return self.controls_information.PVs.qdcraw.get()


class PMTCollection(BaseModel):
    pmts: Dict[str, SerializeAsAny[PMT]]

    @field_validator("pmts", mode="before")
    def validate_pmts(cls, v) -> Dict[str, PMT]:
        for name, pmt in v.items():
            if isinstance(pmt, PMT):
                continue
            pmt = dict(pmt)
            pmt.update({"name": name})
            v.update({name: pmt})
        return v

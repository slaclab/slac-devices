from pydantic import BaseModel, ConfigDict


class BaseModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")


from slac_devices.device import Device as Device, DeviceCollection as DeviceCollection  # noqa: E402

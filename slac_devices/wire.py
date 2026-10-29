from enum import Enum
from pydantic import (
    BaseModel,
    Field,
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


def validate_profile(v: str) -> str:
    """Validate profile is X, Y, or U."""
    if isinstance(v, str) and v.lower() in ["x", "y", "u"]:
        return v.lower()
    raise ValueError("profile must be X, Y, or U")


def validate_range(v: list) -> list:
    """Validate range has exactly 2 elements with first < second."""
    if not isinstance(v, list) or len(v) != 2:
        raise ValueError("range must be a list with exactly 2 elements")
    if v[0] >= v[1]:
        raise ValueError("first element must be smaller than second element")
    return v


def validate_integer(v) -> int:
    """Validate value is a strict integer."""
    if not isinstance(v, int) or isinstance(v, bool):
        raise ValueError("value must be an integer")
    return v


def validate_boolean(v) -> bool:
    """Validate value is a boolean."""
    if not isinstance(v, bool):
        raise ValueError("value must be a boolean")
    return v


class WirePVSet(PVSet):
    abort_scan: PV
    beam_rate: PV
    enabled: Optional[PV] = None
    homed: Optional[PV] = None
    initialize: Optional[PV] = None
    initialize_status: Optional[PV] = None
    install_angle: Optional[PV] = None
    motor: PV
    motor_rbv: PV
    mps_speed: PV
    on_status: PV
    retract: Optional[PV] = None
    scan_pulses: PV
    scan_status: Optional[PV] = None
    speed: PV
    speed_max: PV
    speed_min: PV
    start_scan: PV
    temperature: Optional[PV] = None
    timeout: Optional[PV] = None
    torque_enable: Optional[PV] = None
    use_u_wire: PV
    use_x_wire: PV
    use_y_wire: PV
    u_size: PV
    u_speed_calc: PV
    u_wire_inner: PV
    u_wire_outer: PV
    x_size: PV
    x_speed_calc: PV
    x_wire_inner: PV
    x_wire_outer: PV
    y_size: PV
    y_speed_calc: PV
    y_wire_inner: PV
    y_wire_outer: PV

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class WireControlInformation(ControlInformation):
    PVs: SerializeAsAny[WirePVSet]

    def __init__(self, *args, **kwargs):
        super(WireControlInformation, self).__init__(*args, **kwargs)


class TMITLossBPMs(BaseModel):
    upstream: List[str]
    downstream: List[str]


class WireMetadata(Metadata):
    detectors: Union[List[str], Dict[str, List[str]]]
    default_detector: Union[str, Dict[str, str]]
    tmitloss: Optional[TMITLossBPMs] = None
    jitter_bpms: Optional[List[str]] = None
    charge_toroids: Optional[List[str]] = None
    type: str
    wire_type: str


class SpeedState(str, Enum):
    """Validity of a profile's scan speed."""

    OK = "ok"  # speed_floor < speed < speed_max
    TOO_FAST = "too_fast"  # speed >= speed_max: range too wide
    TOO_SLOW = "too_slow"  # speed <= speed_floor: range too narrow
    NO_BEAM = "no_beam"  # beam rate is 0, speed is meaningless
    BAD_RANGE = "bad_range"  # inner >= outer


class RangeStatus(BaseModel):
    """Result of checking one profile's scan range against the speed limits.

    ``state`` is decided in order: BAD_RANGE, NO_BEAM, TOO_FAST, TOO_SLOW,
    then OK. Both speed limits are exclusive.

    Speed scales linearly with range width, so ``min_width`` and
    ``max_width`` give the range widths at which the speed would reach
    each limit.
    """

    profile: str = Field(description="Profile checked: x, y or u")
    state: SpeedState = Field(description="Result of the speed check")
    speed: float = Field(description="IOC-calculated scan speed (um/s)")
    speed_floor: float = Field(description="Minimum allowed speed (um/s)")
    speed_max: float = Field(description="Maximum allowed speed (um/s)")
    inner: float = Field(description="Inner range endpoint (um)")
    outer: float = Field(description="Outer range endpoint (um)")
    scan_pulses: int = Field(description="Beam pulses per scan")
    beam_rate: float = Field(description="Beam rate (Hz)")

    @property
    def valid(self) -> bool:
        return self.state == SpeedState.OK

    @property
    def width(self) -> float:
        """Range width (um)."""
        return self.outer - self.inner

    @property
    def min_width(self) -> float:
        """Range width (um) at which the speed reaches speed_floor."""
        return self.width * self.speed_floor / self.speed

    @property
    def max_width(self) -> float:
        """Range width (um) at which the speed reaches speed_max."""
        return self.width * self.speed_max / self.speed


class Wire(Device):
    controls_information: SerializeAsAny[WireControlInformation]
    metadata: SerializeAsAny[WireMetadata]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _repr_string(self) -> str:
        """Build the string representation including active profiles and ranges."""
        profiles = []
        try:
            if self.use_x_wire:
                profiles.append(f"X[{self.x_wire_inner}-{self.x_wire_outer}]")
            if self.use_y_wire:
                profiles.append(f"Y[{self.y_wire_inner}-{self.y_wire_outer}]")
            if self.use_u_wire:
                profiles.append(f"U[{self.u_wire_inner}-{self.u_wire_outer}]")
        except Exception:
            # If PVs are unavailable, just skip profile info
            pass

        profiles_str = ", ".join(profiles) if profiles else "no profiles configured"
        return f"Wire(name={self.name!r}, area={self.area!r}, profiles={profiles_str})"

    def __repr__(self) -> str:
        """Return the display string for this wire."""
        return self._repr_string()

    def active_profiles(self) -> List[str]:
        """Return list of currently enabled profiles.

        Returns:
            List[str]: Profiles that are enabled (e.g., ['X', 'Y'])
        """
        active = []
        try:
            if self.use_x_wire:
                active.append("x")
            if self.use_y_wire:
                active.append("y")
            if self.use_u_wire:
                active.append("u")
        except Exception:
            pass
        return active

    def abort_scan(self):
        """Aborts active wire scan"""
        self.controls_information.PVs.abort_scan.put(value=1)

    @property
    def beam_rate(self):
        """Returns current beam rate"""
        return self.controls_information.PVs.beam_rate.get()

    @property
    def enabled(self):
        """Returns the enabled state of the wire sacnner"""
        return self.controls_information.PVs.enabled.get()

    @property
    def homed(self):
        """Checks if the wire is in the home position."""
        return self.controls_information.PVs.homed.get()

    @property
    def initialize_status(self):
        """Checks if the wire scanner device has been initialized."""
        return self.controls_information.PVs.initialize_status.get()

    def initialize(self) -> None:
        self.controls_information.PVs.initialize.put(value=1)

    @property
    def install_angle(self):
        """Returns the wire scanner install angle in degrees."""
        return self.controls_information.PVs.install_angle.get()

    @property
    def motor(self):
        """Returns the readback from the MOTR PV"""
        return self.controls_information.PVs.motor.get()

    @motor.setter
    def motor(self, val: int) -> None:
        validate_integer(val)
        self.controls_information.PVs.motor.put(value=val)

    @property
    def motor_rbv(self):
        """Returns the .RBV from the MOTR PV"""
        return self.controls_information.PVs.motor_rbv.get()

    @property
    def mps_speed(self):
        """Returns the MPS (Machine Protection System) speed limit in um/s.

        Converts from the native mm/s unit to um/s for consistency with
        other speed properties.
        """
        return self.controls_information.PVs.mps_speed.get() * 1000

    @property
    def on_status(self):
        """Returns the on status of the wire scanner."""
        return self.controls_information.PVs.on_status.get()

    def position_buffer(self, buffer: Buffer, **kwargs):
        return buffer.get(f"{self.controls_information.control_name}:POSN", **kwargs)

    def retract(self):
        """Retracts the wire scanner"""
        self.controls_information.PVs.retract.put(value=1)

    @property
    def scan_pulses(self):
        """Returns the number of scan pulses requested"""
        return self.controls_information.PVs.scan_pulses.get()

    @scan_pulses.setter
    def scan_pulses(self, val: int) -> None:
        validate_integer(val)
        self.controls_information.PVs.scan_pulses.put(value=val)

    @property
    def scan_status(self):
        """Returns the current scan status."""
        if self.controls_information.PVs.scan_status is not None:
            return self.controls_information.PVs.scan_status.get()
        else:
            raise AttributeError("scan_status PV is not defined for this device")

    def set_range(self, profile: str, val: list) -> None:
        self._set_profile_range(profile, val)

    @property
    def speed(self):
        """Returns the current calculated speed of the wire scanner."""
        return self.controls_information.PVs.speed.get()

    @speed.setter
    def speed(self, val: int) -> None:
        validate_integer(val)
        self.controls_information.PVs.speed.put(value=val)

    @property
    def speed_max(self):
        """Returns the wire scanner maximum speed in um/s"""
        return self.controls_information.PVs.speed_max.get()

    @property
    def speed_min(self):
        """Returns the wire scanner minimum speed in um/s"""
        return self.controls_information.PVs.speed_min.get()

    @property
    def speed_floor(self):
        """Returns the lowest allowed scan speed in um/s.

        This is the higher of the motor minimum speed and the MPS speed limit.
        """
        return max(self.speed_min, self.mps_speed)

    @property
    def x_speed_calc(self):
        """Returns the IOC-calculated X profile scan speed in um/s."""
        return self.controls_information.PVs.x_speed_calc.get()

    @property
    def y_speed_calc(self):
        """Returns the IOC-calculated Y profile scan speed in um/s."""
        return self.controls_information.PVs.y_speed_calc.get()

    @property
    def u_speed_calc(self):
        """Returns the IOC-calculated U profile scan speed in um/s."""
        return self.controls_information.PVs.u_speed_calc.get()

    def start_scan(self):
        """Starts a wire scan using current parameters"""
        self.controls_information.PVs.start_scan.put(value=1)

    @property
    def temperature(self):
        """Returns RTD temperature"""
        return self.controls_information.PVs.temperature.get()

    @property
    def timeout(self):
        """Returns enabled status of device timeout"""
        return self.controls_information.PVs.timeout.get()

    @timeout.setter
    def timeout(self, val: bool) -> None:
        validate_boolean(val)
        self.controls_information.PVs.timeout.put(value=val)

    @property
    def torque_enable(self):
        """Returns the state of the motor torque enable."""
        return self.controls_information.PVs.torque_enable.get()

    @torque_enable.setter
    def torque_enable(self, val: bool) -> None:
        validate_boolean(val)
        self.controls_information.PVs.torque_enable.put(value=int(val))

    @property
    def x_size(self):
        """Returns the x wire thickness in um."""
        return self.controls_information.PVs.x_size.get()

    @property
    def y_size(self):
        """Returns the y wire thickness in um."""
        return self.controls_information.PVs.y_size.get()

    @property
    def u_size(self):
        """Returns the u wire thickness in um."""
        return self.controls_information.PVs.u_size.get()

    def use(self, profile: str, val: bool) -> None:
        validate_profile(profile)
        validate_boolean(val)
        property_name = "use_" + profile.lower() + "_wire"
        setattr(self, property_name, val)

    @property
    def use_x_wire(self):
        """Checks if the X profile will be scanned."""
        return self.controls_information.PVs.use_x_wire.get()

    @use_x_wire.setter
    def use_x_wire(self, val: bool) -> None:
        validate_boolean(val)
        self.controls_information.PVs.use_x_wire.put(value=int(val))

    @property
    def x_range(self):
        """
        Returns the X profile scan range.
        """
        return [self.x_wire_inner, self.x_wire_outer]

    @property
    def x_wire_inner(self):
        """Returns the inner point of the X profile scan range."""
        return self.controls_information.PVs.x_wire_inner.get()

    @x_wire_inner.setter
    def x_wire_inner(self, val: int) -> None:
        validate_integer(val)
        self.controls_information.PVs.x_wire_inner.put(value=val)

    @property
    def x_wire_outer(self):
        """Returns the outer point of the X profile scan range."""
        return self.controls_information.PVs.x_wire_outer.get()

    @x_wire_outer.setter
    def x_wire_outer(self, val: int) -> None:
        validate_integer(val)
        self.controls_information.PVs.x_wire_outer.put(value=val)

    @property
    def use_y_wire(self):
        """Checks if the Y profile will be scanned."""
        return self.controls_information.PVs.use_y_wire.get()

    @use_y_wire.setter
    def use_y_wire(self, val: bool) -> None:
        validate_boolean(val)
        self.controls_information.PVs.use_y_wire.put(value=int(val))

    @property
    def y_range(self):
        """
        Returns the Y profile scan range.
        """
        return [self.y_wire_inner, self.y_wire_outer]

    @property
    def y_wire_inner(self):
        """Returns the inner point of the Y profile scan range."""
        return self.controls_information.PVs.y_wire_inner.get()

    @y_wire_inner.setter
    def y_wire_inner(self, val: int) -> None:
        validate_integer(val)
        self.controls_information.PVs.y_wire_inner.put(value=val)

    @property
    def y_wire_outer(self):
        """Returns the outer point of the Y profile scan range."""
        return self.controls_information.PVs.y_wire_outer.get()

    @y_wire_outer.setter
    def y_wire_outer(self, val: int) -> None:
        validate_integer(val)
        self.controls_information.PVs.y_wire_outer.put(value=val)

    @property
    def use_u_wire(self):
        """Checks if the U profile will be scanned."""
        return self.controls_information.PVs.use_u_wire.get()

    @use_u_wire.setter
    def use_u_wire(self, val: bool) -> None:
        validate_boolean(val)
        self.controls_information.PVs.use_u_wire.put(value=int(val))

    @property
    def u_range(self):
        """
        Returns the U profile scan range.
        """
        return [self.u_wire_inner, self.u_wire_outer]

    @property
    def u_wire_inner(self):
        """Returns the inner point of the U profile scan range."""
        return self.controls_information.PVs.u_wire_inner.get()

    @u_wire_inner.setter
    def u_wire_inner(self, val: int) -> None:
        validate_integer(val)
        self.controls_information.PVs.u_wire_inner.put(value=val)

    @property
    def u_wire_outer(self):
        """Returns the outer point of the U profile scan range."""
        return self.controls_information.PVs.u_wire_outer.get()

    @u_wire_outer.setter
    def u_wire_outer(self, val: int) -> None:
        validate_integer(val)
        self.controls_information.PVs.u_wire_outer.put(value=val)

    @property
    def type(self) -> str:
        return self.metadata.type

    def _set_profile_range(self, profile: str, val: list) -> None:
        """Set both range endpoints of a profile."""
        profile = validate_profile(profile)
        validate_range(val)
        pvs = self.controls_information.PVs
        getattr(pvs, f"{profile}_wire_inner").put(value=val[0])
        getattr(pvs, f"{profile}_wire_outer").put(value=val[1])

    def range_status(self, profile: str) -> RangeStatus:
        """Check whether a profile's scan range gives a valid wire speed.

        The IOC calculates the scan speed for each profile from the range, beam
        rate and scan pulses (WIRE{X,Y,U}SPEED_CALC). The speed is valid when
        speed_floor < speed < speed_max.

        Args:
            profile: Profile identifier (X, Y, U)

        Returns:
            RangeStatus with the speed state and the values it was decided from
        """
        profile = validate_profile(profile)
        inner = getattr(self, f"{profile}_wire_inner")
        outer = getattr(self, f"{profile}_wire_outer")
        speed = getattr(self, f"{profile}_speed_calc")
        beam_rate = self.beam_rate
        floor = self.speed_floor
        speed_max = self.speed_max

        if inner >= outer:
            state = SpeedState.BAD_RANGE
        elif not beam_rate:
            state = SpeedState.NO_BEAM
        elif speed >= speed_max:
            state = SpeedState.TOO_FAST
        elif speed <= floor:
            state = SpeedState.TOO_SLOW
        else:
            state = SpeedState.OK

        return RangeStatus(
            profile=profile,
            state=state,
            speed=float(speed),
            speed_floor=float(floor),
            speed_max=float(speed_max),
            inner=float(inner),
            outer=float(outer),
            scan_pulses=int(self.scan_pulses),
            beam_rate=float(beam_rate),
        )

    def invalid_profiles(self) -> List[RangeStatus]:
        """Return the range status of every active profile with an invalid speed."""
        statuses = [self.range_status(profile) for profile in self.active_profiles()]
        return [status for status in statuses if not status.valid]


class WireCollection(BaseModel):
    wires: Dict[str, SerializeAsAny[Wire]]

    @field_validator("wires", mode="before")
    def validate_wires(cls, v) -> Dict[str, Wire]:
        for name, wire in v.items():
            if isinstance(wire, Wire):
                continue
            wire = dict(wire)
            wire.update({"name": name})
            v.update({name: wire})
        return v

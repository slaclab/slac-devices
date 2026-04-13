
from pydantic import (
    BaseModel,
    SerializeAsAny,
    field_validator,
)
from typing import (
    Dict,
    List,
    Optional,
)
import warnings
from slac_devices.device import (
    Device,
    ControlInformation,
    Metadata,
    PVSet,
)
from epics import PV

EPICS_ERROR_MESSAGE = "Unable to connect to EPICS."


def validate_plane(v: str) -> str:
    """Validate plane is X, Y, or U."""
    if isinstance(v, str) and v.lower() in ["x", "y", "u"]:
        return v.lower()
    raise ValueError("plane must be X, Y, or U")


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
    beam_rate: Optional[PV] = None
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
    u_wire_inner: PV
    u_wire_outer: PV
    x_size: PV
    x_wire_inner: PV
    x_wire_outer: PV
    y_size: PV
    y_wire_inner: PV
    y_wire_outer: PV

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class WireControlInformation(ControlInformation):
    PVs: SerializeAsAny[WirePVSet]

    def __init__(self, *args, **kwargs):
        super(WireControlInformation, self).__init__(*args, **kwargs)


class WireMetadata(Metadata):
    detectors: List[str]
    default_detector: str
    bpms_before_wire: Optional[List[str]] = None
    bpms_after_wire: Optional[List[str]] = None
    type: str
    wire_type: str


class Wire(Device):
    controls_information: SerializeAsAny[WireControlInformation]
    metadata: SerializeAsAny[WireMetadata]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _repr_string(self) -> str:
        """Build the string representation including active planes and ranges."""
        planes = []
        try:
            if self.use_x_wire:
                planes.append(f"X[{self.x_wire_inner}-{self.x_wire_outer}]")
            if self.use_y_wire:
                planes.append(f"Y[{self.y_wire_inner}-{self.y_wire_outer}]")
            if self.use_u_wire:
                planes.append(f"U[{self.u_wire_inner}-{self.u_wire_outer}]")
        except Exception:
            # If PVs are unavailable, just skip plane info
            pass

        planes_str = ", ".join(planes) if planes else "no planes configured"
        return (
            f"Wire(name={self.name!r}, "
            f"area={self.area!r}, "
            f"planes={planes_str})"
        )

    def __repr__(self) -> str:
        """Return the display string for this wire."""
        return self._repr_string()

    def active_profiles(self) -> List[str]:
        """Return list of currently enabled planes.

        Returns:
            List[str]: Planes that are enabled (e.g., ['X', 'Y'])
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
        # Some wires do not have dedicated beam rate PVs.
        # See CATER 180392 for more details
        nc_areas = ["LI20", "LI24", "LI28", "L3", "LTUH", "DL1", "BC1", "BC2", "LTU"]
        if self.area in nc_areas and self.controls_information.PVs.beam_rate is None:
            nc_beam_rate = PV("EVNT:SYS0:1:LCLSBEAMRATE")
            return nc_beam_rate.get()
        elif self.area in ["DIAG0"] and self.controls_information.PVs.beam_rate is None:
            diag0_beam_rate = PV("TPG:SYS0:1:DST01:RATE")
            return diag0_beam_rate.get()
        else:
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

    def position_buffer(self, buffer):
        return buffer.get_data_buffer(
            f"{self.controls_information.control_name}:POSN"
            )

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

    def set_range(self, plane: str, val: list) -> None:
        self._set_plane_range(plane, val)

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

    def use(self, plane: str, val: bool) -> None:
        validate_plane(plane)
        validate_boolean(val)
        property_name = "use_" + plane.lower() + "_wire"
        setattr(self, property_name, val)

    @property
    def use_x_wire(self):
        """Checks if the X plane will be scanned."""
        return self.controls_information.PVs.use_x_wire.get()

    @use_x_wire.setter
    def use_x_wire(self, val: bool) -> None:
        validate_boolean(val)
        self.controls_information.PVs.use_x_wire.put(value=int(val))

    @property
    def x_range(self):
        """
        Returns the X plane scan range.
        """
        return [self.x_wire_inner, self.x_wire_outer]

    @property
    def x_wire_inner(self):
        """Returns the inner point of the X plane scan range."""
        return self.controls_information.PVs.x_wire_inner.get()

    @x_wire_inner.setter
    def x_wire_inner(self, val: int) -> None:
        validate_integer(val)
        self.controls_information.PVs.x_wire_inner.put(value=val)
        self._warn_current_plane_range("x")

    @property
    def x_wire_outer(self):
        """Returns the outer point of the X plane scan range."""
        return self.controls_information.PVs.x_wire_outer.get()

    @x_wire_outer.setter
    def x_wire_outer(self, val: int) -> None:
        validate_integer(val)
        self.controls_information.PVs.x_wire_outer.put(value=val)
        self._warn_current_plane_range("x")

    @property
    def use_y_wire(self):
        """Checks if the Y plane will be scanned."""
        return self.controls_information.PVs.use_y_wire.get()

    @use_y_wire.setter
    def use_y_wire(self, val: bool) -> None:
        validate_boolean(val)
        self.controls_information.PVs.use_y_wire.put(value=int(val))

    @property
    def y_range(self):
        """
        Returns the Y plane scan range.
        """
        return [self.y_wire_inner, self.y_wire_outer]

    @property
    def y_wire_inner(self):
        """Returns the inner point of the Y plane scan range."""
        return self.controls_information.PVs.y_wire_inner.get()

    @y_wire_inner.setter
    def y_wire_inner(self, val: int) -> None:
        validate_integer(val)
        self.controls_information.PVs.y_wire_inner.put(value=val)
        self._warn_current_plane_range("y")

    @property
    def y_wire_outer(self):
        """Returns the outer point of the Y plane scan range."""
        return self.controls_information.PVs.y_wire_outer.get()

    @y_wire_outer.setter
    def y_wire_outer(self, val: int) -> None:
        validate_integer(val)
        self.controls_information.PVs.y_wire_outer.put(value=val)
        self._warn_current_plane_range("y")

    @property
    def use_u_wire(self):
        """Checks if the U plane will be scanned."""
        return self.controls_information.PVs.use_u_wire.get()

    @use_u_wire.setter
    def use_u_wire(self, val: bool) -> None:
        validate_boolean(val)
        self.controls_information.PVs.use_u_wire.put(value=int(val))

    @property
    def u_range(self):
        """
        Returns the U plane scan range.
        """
        return [self.u_wire_inner, self.u_wire_outer]

    @property
    def u_wire_inner(self):
        """Returns the inner point of the U plane scan range."""
        return self.controls_information.PVs.u_wire_inner.get()

    @u_wire_inner.setter
    def u_wire_inner(self, val: int) -> None:
        validate_integer(val)
        self.controls_information.PVs.u_wire_inner.put(value=val)
        self._warn_current_plane_range("u")

    @property
    def u_wire_outer(self):
        """Returns the outer point of the U plane scan range."""
        return self.controls_information.PVs.u_wire_outer.get()

    @u_wire_outer.setter
    def u_wire_outer(self, val: int) -> None:
        validate_integer(val)
        self.controls_information.PVs.u_wire_outer.put(value=val)
        self._warn_current_plane_range("u")

    @property
    def type(self) -> str:
        return self.metadata.type

    def _warn_invalid_range_configuration(
        self, plane: str, inner: int, outer: int
    ) -> None:
        """Warn when the current plane configuration fails validation."""
        try:
            self.validate_range_speed(plane, inner, outer)
        except ValueError as exc:
            warnings.warn(
                (
                    f"{self.name} {plane.upper()} range configuration is invalid: "
                    f"{exc}"
                ),
                UserWarning,
                stacklevel=2,
            )

    def _warn_current_plane_range(self, plane: str) -> None:
        """Validate and warn on the current range for a plane."""
        plane = validate_plane(plane)
        inner = getattr(self, f"{plane}_wire_inner")
        outer = getattr(self, f"{plane}_wire_outer")
        if inner >= outer:
            warnings.warn(
                (
                    f"{self.name} {plane.upper()} range configuration is invalid: "
                    "inner must be less than outer"
                ),
                UserWarning,
                stacklevel=2,
            )
            return
        self._warn_invalid_range_configuration(plane, inner, outer)

    def _set_plane_range(self, plane: str, val: list) -> None:
        """Set both range endpoints before running configuration validation."""
        plane = validate_plane(plane)
        validate_range(val)
        getattr(self.controls_information.PVs, f"{plane}_wire_inner").put(
            value=val[0]
        )
        getattr(self.controls_information.PVs, f"{plane}_wire_outer").put(
            value=val[1]
        )
        self._warn_invalid_range_configuration(plane, val[0], val[1])

    def calculate_required_speed(self, plane: str, inner: int, outer: int) -> float:
        """Calculate the required wire speed for a given plane and range.

        Formula: required_speed = (beam_rate / scan_pulses) * (outer - inner)

        Args:
            plane: Plane identifier (X, Y, U)
            inner: Inner range value in um
            outer: Outer range value in um

        Returns:
            Required speed in um/s

        Raises:
            ValueError: If scan_pulses is invalid or range is invalid
        """
        validate_plane(plane)
        if self.scan_pulses <= 0:
            raise ValueError("scan_pulses must be positive")
        if inner >= outer:
            raise ValueError("inner must be less than outer")

        range_distance = outer - inner
        return (self.beam_rate / self.scan_pulses) * range_distance

    def validate_range_speed(
        self, plane: str, inner: int, outer: int
    ) -> Dict[str, float]:
        """Validate that a range can be scanned within speed limits.

        Checks that the required speed is:
        - Greater than the MPS (Machine Protection System) speed limit
        - Less than the maximum speed

        Args:
            plane: Plane identifier (X, Y, U)
            inner: Inner range value in um
            outer: Outer range value in um

        Returns:
            Dict with 'required_speed', 'mps_speed', 'speed_max'

        Raises:
            ValueError: If speed requirements cannot be met
        """
        required = self.calculate_required_speed(plane, inner, outer)
        mps = self.mps_speed
        max_speed = self.speed_max

        if required <= mps:
            raise ValueError(
                f"Required speed {required:.1f} um/s must be greater than "
                f"MPS limit {mps:.1f} um/s"
            )
        if required >= max_speed:
            raise ValueError(
                f"Required speed {required:.1f} um/s must be less than "
                f"maximum speed {max_speed:.1f} um/s"
            )

        return {
            "required_speed": required,
            "mps_speed": mps,
            "speed_max": max_speed,
        }


class WireCollection(BaseModel):
    wires: Dict[str, SerializeAsAny[Wire]]

    @field_validator("wires", mode="before")
    def validate_wires(cls, v) -> Dict[str, Wire]:
        for name, wire in v.items():
            wire = dict(wire)
            # Set name field for wire
            wire.update({"name": name})
            v.update({name: wire})
        return v

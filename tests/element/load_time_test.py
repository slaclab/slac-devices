import time

from slac_devices import element, reader

_DEVICES = {
    "QA11": ("L1", "magnet"),
    "Q25201": ("L3", "magnet"),
    "BPM2": ("GUN", "bpm"),
    "BPMDL1": ("LTUH", "bpm"),
    "OTRDG02": ("DIAG0", "screen"),
    "YAGPSI": ("LTUH", "screen"),
    "WSEMIT2": ("EMIT2", "wire"),
    "WS31": ("LTUH", "wire"),
    "IM01": ("GUN", "toroid"),
    "IM31": ("LTUH", "toroid"),
    "LBLM00A": ("GUNB", "lblm"),
    "LBLM30A": ("LTUH", "lblm"),
    "PMT29150": ("LI29", "pmt"),
    "PMT122": ("LTUH", "pmt"),
}


def _time_ms(load, repeat=10):
    start = time.perf_counter()
    assert load() is not None
    first = time.perf_counter() - start
    start = time.perf_counter()
    for _ in range(repeat):
        load()
    return first * 1e3, (time.perf_counter() - start) / repeat * 1e3


def test_load_time(capsys):
    """Compare loading a device from YAML with loading it as an element Device.

    Run with ``pytest tests/element/load_time_test.py``. Two devices per type
    that load in both styles, from a small and a large area file. YAML parses
    the whole area file on every call. Element queries device.sqlite3, paying
    a one-time database setup on the first load in the process.
    """
    rows = []
    for name, (area, kind) in _DEVICES.items():
        yaml_ms = _time_ms(lambda: getattr(reader, f"create_{kind}")(area=area, name=name))
        element_ms = _time_ms(lambda: element.Device(name))
        rows.append((name, area, *yaml_ms, *element_ms))
    with capsys.disabled():
        print(f"\n{'device':9} {'area':6} {'yaml first':>11} {'repeat':>7} {'element first':>14} {'repeat':>7}")
        for r in rows:
            print(f"{r[0]:9} {r[1]:6} {r[2]:11.2f} {r[3]:7.2f} {r[4]:14.2f} {r[5]:7.2f}")

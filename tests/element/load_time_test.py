import time

import slac_db
import slac_db.config

from slac_devices import element, reader


def _yaml_loader(area, kind, name):
    return lambda: getattr(reader, f"create_{kind[:-1]}")(area=area, name=name)


def _first_working_device(area):
    for kind, devices in (slac_db.get_device(area=area) or {}).items():
        for name in devices:
            load = _yaml_loader(area, kind, name)
            if hasattr(reader, f"create_{kind[:-1]}") and load() is not None:
                return name, load
    return None, None


def _time_ms(load, repeat=10):
    start = time.perf_counter()
    load()
    first = time.perf_counter() - start
    start = time.perf_counter()
    for _ in range(repeat):
        load()
    return first * 1e3, (time.perf_counter() - start) / repeat * 1e3


def test_load_time(capsys):
    """Compare loading a device from YAML with loading it as an element Device.

    Run with ``pytest tests/element/load_time_test.py``. One device per area
    file in slac_db/package_data/yaml: the first that loads from YAML. YAML
    parses the whole area file on every call. Element queries device.sqlite3,
    paying a one-time database setup on the first load in the process.
    """
    rows, skipped = [], []
    for path in sorted(slac_db.config.yaml().glob("*.yaml"), key=lambda p: p.stat().st_size):
        name, yaml_load = _first_working_device(path.stem)
        if name is None:
            skipped.append(path.stem)
            continue
        size = (len(path.read_text().splitlines()), path.stat().st_size / 1024)
        rows.append((path.stem, name, *size, *_time_ms(yaml_load), *_time_ms(lambda: element.Device(name))))
    with capsys.disabled():
        print(f"\n{'area':7} {'device':10} {'lines':>6} {'KB':>5} {'yaml first (ms)':>15} {'repeat (ms)':>11} {'element first (ms)':>18} {'repeat (ms)':>11}")
        for r in rows:
            print(f"{r[0]:7} {r[1]:10} {r[2]:6} {r[3]:5.1f} {r[4]:15.2f} {r[5]:11.2f} {r[6]:18.2f} {r[7]:11.2f}")
        print(f"no device loads from YAML: {', '.join(skipped)}")

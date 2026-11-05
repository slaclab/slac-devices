import time

import slac_db.config

from slac_devices import element, reader


def measure_runtime_in_ms(load, repeat=10):
    start = time.perf_counter()
    load()
    first = time.perf_counter() - start
    start = time.perf_counter()
    for _ in range(repeat):
        load()
    return first * 1000, (time.perf_counter() - start) / repeat * 1000


def get_working_device(area):
    for kind, devices in slac_db.get_device(area=area).items():
        create = getattr(reader, f"create_{kind.removesuffix('s')}", None)
        if create is None:
            continue
        for name in devices:
            load = lambda: create(area=area, name=name)
            if load() is not None:
                return name, load
    return None, None


def measure_area_load_time(path):
    name, yaml_load = get_working_device(path.stem)
    if name is None:
        return None
    yaml_first, yaml_repeat = measure_runtime_in_ms(yaml_load)
    element_first, element_repeat = measure_runtime_in_ms(lambda: element.Device(name))
    return {
        "area": path.stem,
        "device": name,
        "lines": len(path.read_text().splitlines()),
        "kb": path.stat().st_size / 1024,
        "yaml_first_ms": yaml_first,
        "yaml_repeat_ms": yaml_repeat,
        "element_first_ms": element_first,
        "element_repeat_ms": element_repeat,
    }


def _area_files_by_size():
    return sorted(slac_db.config.yaml().glob("*.yaml"), key=lambda p: p.stat().st_size)


def _print_table(rows):
    _COLUMNS = (
        ("area", "area", 7, "s"),
        ("device", "device", 10, "s"),
        ("lines", "lines", 6, "d"),
        ("kb", "KB", 5, ".1f"),
        ("yaml_first_ms", "yaml first (ms)", 15, ".2f"),
        ("yaml_repeat_ms", "yaml repeat (ms)", 16, ".2f"),
        ("element_first_ms", "element first (ms)", 18, ".2f"),
        ("element_repeat_ms", "element repeat (ms)", 19, ".2f"),
    )
    print()
    print(
        " ".join(
            title.ljust(width) if fmt == "s" else title.rjust(width)
            for _, title, width, fmt in _COLUMNS
        )
    )
    for row in rows:
        print(" ".join(f"{row[key]:{width}{fmt}}" for key, _, width, fmt in _COLUMNS))


def test_load_time(capsys):
    """Compare loading a device from YAML with loading it as an element Device.

    Run with ``pytest tests/element/load_time_test.py``. One device per area
    file in slac_db/package_data/yaml: the first that loads from YAML. YAML
    parses the whole area file on every call. Element queries device.sqlite3,
    paying a one-time database setup on the first load in the process.
    """
    rows, skipped = [], []
    for path in _area_files_by_size():
        row = _measure_area(path)
        if row is None:
            skipped.append(path.stem)
        else:
            rows.append(row)
    with capsys.disabled():
        _print_table(rows)
        print(f"no device loads from YAML: {', '.join(skipped)}")

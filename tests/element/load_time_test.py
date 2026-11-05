import time

from slac_devices import element, reader

_YAML_LOADERS = {
    "OTRDG02": lambda: reader.create_screen(area="DIAG0", name="OTRDG02"),
    "WS01": lambda: reader.create_wire(area="DL1", name="WS01"),
}


def _time_ms(load, repeat=20):
    start = time.perf_counter()
    load()
    first = time.perf_counter() - start
    start = time.perf_counter()
    for _ in range(repeat):
        load()
    return first * 1e3, (time.perf_counter() - start) / repeat * 1e3


def test_load_time(capsys):
    """Compare loading a device from YAML with loading it as an element Device.

    Run with ``pytest tests/element/load_time_test.py``. YAML parses the
    whole area file on every call. Element queries device.sqlite3, paying a
    one-time database setup on the first load in the process. WS01 currently
    fails Wire validation from YAML; its time is the parse plus that check.
    """
    rows = []
    for name, yaml_load in _YAML_LOADERS.items():
        rows.append((name, "yaml", *_time_ms(yaml_load)))
        rows.append((name, "element", *_time_ms(lambda: element.Device(name))))
    with capsys.disabled():
        print(f"\n{'device':8} {'style':8} {'first ms':>9} {'repeat ms':>10}")
        for row in rows:
            print(f"{row[0]:8} {row[1]:8} {row[2]:9.2f} {row[3]:10.2f}")

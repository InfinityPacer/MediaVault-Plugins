"""MediaVault third-party sandbox boundary probe."""

import importlib.util
import json
import os
import socket
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path


MOVIEPILOT_URLS = (
    "http://192.168.50.99:3000/",
    "http://192.168.50.99:3000/api/v1/system/ping",
)
FILE_TARGETS = (
    "/volume1",
    "/volume1/Link",
    "/app",
    "/config",
    "/etc/hostname",
)


def file_probe(path: str) -> dict:
    target = Path(path)
    result = {"path": path, "exists": target.exists(), "readable": False, "kind": None}
    if not result["exists"]:
        return result
    result["kind"] = "directory" if target.is_dir() else "file" if target.is_file() else "other"
    try:
        if target.is_file():
            with target.open("rb") as stream:
                stream.read(1)
        else:
            list(target.iterdir())
        result["readable"] = True
    except Exception as exc:  # pragma: no cover - the sandbox result is the test output
        result["error_type"] = type(exc).__name__
    return result


def network_probe(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "MediaVault-sandbox-boundary-poc/0.1"})
    try:
        with urllib.request.urlopen(request, timeout=3) as response:
            return {"url": url, "reachable": True, "status": response.status}
    except Exception as exc:  # pragma: no cover - the sandbox result is the test output
        return {"url": url, "reachable": False, "error_type": type(exc).__name__}


def import_probe(module: str) -> dict:
    try:
        spec = importlib.util.find_spec(module)
        return {"module": module, "visible": spec is not None}
    except Exception as exc:  # pragma: no cover - the sandbox result is the test output
        return {"module": module, "visible": False, "error_type": type(exc).__name__}


def socket_probe() -> dict:
    try:
        with socket.create_connection(("192.168.50.99", 3000), timeout=3):
            return {"target": "192.168.50.99:3000", "connectable": True}
    except Exception as exc:  # pragma: no cover - the sandbox result is the test output
        return {"target": "192.168.50.99:3000", "connectable": False, "error_type": type(exc).__name__}


def write_probe() -> dict:
    path = None
    try:
        fd, path = tempfile.mkstemp(prefix="mv-sandbox-poc-")
        os.write(fd, b"probe")
        os.close(fd)
        return {"writable": True, "path_visible": True}
    except Exception as exc:  # pragma: no cover - the sandbox result is the test output
        return {"writable": False, "path_visible": False, "error_type": type(exc).__name__}
    finally:
        if path:
            try:
                os.unlink(path)
            except OSError:
                pass


def probe(event=None) -> dict:
    return {
        "file_targets": [file_probe(path) for path in FILE_TARGETS],
        "moviepilot_http": [network_probe(url) for url in MOVIEPILOT_URLS],
        "moviepilot_socket": socket_probe(),
        "environment_keys": sorted(os.environ),
        "module_visibility": [import_probe(module) for module in ("app", "mediavault", "requests")],
        "write_probe": write_probe(),
        "event_type": event.get("event_type") if isinstance(event, dict) else None,
        "payload_keys": sorted((event.get("payload") or {}).keys()) if isinstance(event, dict) else [],
    }


def main() -> int:
    request = json.loads(sys.stdin.readline())
    request_type = request.get("type")
    if request_type == "action" and request.get("action") == "probe":
        result = probe()
    elif request_type in {"event", "schedule"}:
        result = probe(request)
    else:
        print(json.dumps({"ok": False, "error": "unsupported request"}))
        return 2
    print(json.dumps({"ok": True, "result": result}, ensure_ascii=False))
    return 0


raise SystemExit(main())

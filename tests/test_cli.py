"""Unit tests for port-hud CLI parsing, formatting, and process control."""

from __future__ import annotations

import signal
import subprocess
from unittest.mock import patch

import pytest

from port_hud.cli import (
    PortEntry,
    build_parser,
    handle_kill_port,
    kill_pid,
    main,
    render_table,
    scan_ports,
)

SAMPLE_LSOF_OUTPUT = """\
COMMAND   PID USER   FD   TYPE             DEVICE SIZE/OFF NODE NAME
node    12345 dev   23u  IPv4 0x1a2b3c4d5e6f7890      0t0  TCP 127.0.0.1:3000 (LISTEN)
node    12345 dev   24u  IPv4 0x1a2b3c4d5e6f7891      0t0  TCP 127.0.0.1:3000 (LISTEN)
python3  9999 dev   10u  IPv6 0x9a8b7c6d5e4f3210      0t0  TCP [::1]:8000 (LISTEN)
postgres 4321 dev    6u  IPv4 0x1122334455667788      0t0  TCP *:5432 (LISTEN)
badline short
weird   notapid dev  6u  IPv4 0x1122334455667789      0t0  TCP *:9999 (LISTEN)
noport   5555 dev    6u  IPv4 0x1122334455667790      0t0  TCP invalid_name (LISTEN)
"""


def test_scan_ports_parses_deduplicates_and_sorts() -> None:
    completed = subprocess.CompletedProcess(
        args=["lsof"], returncode=0, stdout=SAMPLE_LSOF_OUTPUT, stderr=""
    )
    with patch("port_hud.cli.subprocess.run", return_value=completed):
        entries = scan_ports()

    assert entries == [
        PortEntry(port=3000, pid=12345, process="node", address="127.0.0.1"),
        PortEntry(port=5432, pid=4321, process="postgres", address="*"),
        PortEntry(port=8000, pid=9999, process="python3", address="[::1]"),
    ]


def test_scan_ports_missing_lsof_raises_runtime_error() -> None:
    with patch("port_hud.cli.subprocess.run", side_effect=FileNotFoundError):
        with pytest.raises(RuntimeError, match="lsof"):
            scan_ports()


def test_render_table_empty() -> None:
    assert render_table([]) == "No listening TCP ports found."


def test_render_table_formats_aligned_columns() -> None:
    entries = [
        PortEntry(port=3000, pid=12345, process="node", address="127.0.0.1"),
        PortEntry(port=8000, pid=999, process="python3", address="[::1]"),
    ]
    output = render_table(entries)
    lines = output.splitlines()

    assert len(lines) == 4
    assert lines[0].startswith("PORT")
    assert "PID" in lines[0] and "PROCESS" in lines[0] and "ADDRESS" in lines[0]
    assert set(lines[1].replace(" ", "")) == {"-"}
    assert "3000" in lines[2] and "node" in lines[2] and "127.0.0.1" in lines[2]
    assert "8000" in lines[3] and "python3" in lines[3] and "[::1]" in lines[3]


def test_kill_pid_success_and_force() -> None:
    with patch("port_hud.cli.os.kill") as mock_kill:
        ok, msg = kill_pid(1234, force=False)
        assert ok is True
        assert "SIGTERM" in msg
        mock_kill.assert_called_once_with(1234, signal.SIGTERM)

    with patch("port_hud.cli.os.kill") as mock_kill:
        ok, msg = kill_pid(1234, force=True)
        assert ok is True
        assert "SIGKILL" in msg
        mock_kill.assert_called_once_with(1234, signal.SIGKILL)


def test_kill_pid_handles_errors() -> None:
    with patch("port_hud.cli.os.kill", side_effect=ProcessLookupError):
        ok, msg = kill_pid(9999)
        assert ok is False
        assert "no longer exists" in msg

    with patch("port_hud.cli.os.kill", side_effect=PermissionError):
        ok, msg = kill_pid(1)
        assert ok is False
        assert "Permission denied" in msg


def test_handle_kill_port_not_found(capsys: pytest.CaptureFixture[str]) -> None:
    with patch("port_hud.cli.scan_ports", return_value=[]):
        rc = handle_kill_port(3000, yes=True)
    assert rc == 1
    assert "No listening TCP process found on port 3000" in capsys.readouterr().err


def test_main_table_output(capsys: pytest.CaptureFixture[str]) -> None:
    entries = [PortEntry(port=5173, pid=2222, process="vite", address="127.0.0.1")]
    with patch("port_hud.cli.scan_ports", return_value=entries):
        rc = main([])
    assert rc == 0
    out = capsys.readouterr().out
    assert "5173" in out and "vite" in out


def test_build_parser_flags() -> None:
    parser = build_parser()
    args = parser.parse_args(["--kill", "3000", "--force", "-y", "--interval", "5"])
    assert args.kill == 3000
    assert args.force is True
    assert args.yes is True
    assert args.interval == 5

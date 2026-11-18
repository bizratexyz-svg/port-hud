"""CLI and port-scanning utilities for port-hud."""

from __future__ import annotations

import argparse
import os
import re
import signal
import subprocess
import sys
from dataclasses import dataclass

from port_hud import __version__


@dataclass(frozen=True)
class PortEntry:
    """Represents a listening TCP port."""

    port: int
    pid: int
    process: str
    address: str


_PORT_RE = re.compile(r"^(.*):(\d+)$")


def scan_ports() -> list[PortEntry]:
    """Scan listening TCP ports using lsof."""
    try:
        result = subprocess.run(
            ["lsof", "-iTCP", "-sTCP:LISTEN", "-P", "-n"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("`lsof` is required but was not found on PATH.") from exc

    entries: list[PortEntry] = []
    seen: set[tuple[int, int, str]] = set()

    for line in result.stdout.splitlines()[1:]:
        parts = line.split()
        if len(parts) < 9:
            continue

        process = parts[0]
        try:
            pid = int(parts[1])
        except ValueError:
            continue

        # NAME column is typically the second-to-last token before "(LISTEN)"
        name_token = parts[-2] if parts[-1] == "(LISTEN)" else parts[-1]
        match = _PORT_RE.match(name_token)
        if not match:
            continue

        address, port_str = match.group(1), match.group(2)
        port = int(port_str)
        key = (port, pid, address)
        if key in seen:
            continue
        seen.add(key)
        entries.append(PortEntry(port=port, pid=pid, process=process, address=address))

    entries.sort(key=lambda e: (e.port, e.pid))
    return entries


def kill_pid(pid: int, force: bool = False) -> tuple[bool, str]:
    """Terminate a process by PID."""
    sig = signal.SIGKILL if force else signal.SIGTERM
    try:
        os.kill(pid, sig)
        return True, f"Sent {sig.name} to PID {pid}"
    except ProcessLookupError:
        return False, f"PID {pid} no longer exists"
    except PermissionError:
        return False, f"Permission denied killing PID {pid} (try sudo)"
    except OSError as exc:
        return False, f"Failed to kill PID {pid}: {exc}"


def render_table(entries: list[PortEntry]) -> str:
    """Format port entries as an aligned ASCII table."""
    if not entries:
        return "No listening TCP ports found."

    headers = ("PORT", "PID", "PROCESS", "ADDRESS")
    rows = [(str(e.port), str(e.pid), e.process, e.address) for e in entries]

    widths = [
        max(len(headers[i]), *(len(r[i]) for r in rows))
        for i in range(len(headers))
    ]
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    sep = "  ".join("-" * w for w in widths)

    lines = [fmt.format(*headers), sep]
    lines.extend(fmt.format(*r) for r in rows)
    return "\n".join(lines)


def handle_kill_port(port: int, force: bool = False, yes: bool = False) -> int:
    """Interactively kill process(es) listening on a given port."""
    matches = [e for e in scan_ports() if e.port == port]
    if not matches:
        print(f"No listening TCP process found on port {port}.", file=sys.stderr)
        return 1

    unique_pids: dict[int, PortEntry] = {e.pid: e for e in matches}
    for entry in unique_pids.values():
        if not yes:
            prompt = f"Kill {entry.process} (PID {entry.pid}) on {entry.address}:{entry.port}? [y/N] "
            try:
                answer = input(prompt).strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\nAborted.")
                return 130
            if answer not in ("y", "yes"):
                print(f"Skipped PID {entry.pid}.")
                continue

        ok, msg = kill_pid(entry.pid, force=force)
        stream = sys.stdout if ok else sys.stderr
        print(msg, file=stream)
        if not ok:
            return 1

    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="port-hud",
        description="Inspect and kill listening TCP ports via CLI or a Cyberpunk Floating HUD.",
    )
    parser.add_argument(
        "--kill",
        type=int,
        metavar="PORT",
        help="Interactively kill the process listening on PORT.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Use SIGKILL instead of SIGTERM when killing a process.",
    )
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip confirmation prompt when using --kill.",
    )
    parser.add_argument(
        "--overlay",
        action="store_true",
        help="Launch the frameless, always-on-top Cyberpunk Floating HUD.",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=3,
        help="Auto-refresh interval in seconds for --overlay mode (default: 3).",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point for port-hud."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.overlay:
        from port_hud.overlay import run_overlay

        run_overlay(refresh_seconds=max(1, args.interval))
        return 0

    if args.kill is not None:
        return handle_kill_port(args.kill, force=args.force, yes=args.yes)

    try:
        entries = scan_ports()
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(render_table(entries))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

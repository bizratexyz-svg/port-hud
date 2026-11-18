"""Cyberpunk Floating HUD overlay for port-hud using tkinter."""

from __future__ import annotations

import tkinter as tk

from port_hud.cli import PortEntry, kill_pid, scan_ports

BG_DARK = "#070b14"
BG_ROW = "#0d1424"
BG_ROW_ALT = "#10192d"
NEON_CYAN = "#00f0ff"
NEON_PINK = "#ff2a85"
TEXT_MUTED = "#7b8ba8"
TEXT_LIGHT = "#e2ecff"
FONT_MONO = ("Menlo", 11)
FONT_TITLE = ("Menlo", 11, "bold")
FONT_BTN = ("Menlo", 10, "bold")


class CyberpunkPortHUD:
    """Frameless, semi-transparent, always-on-top port monitor HUD."""

    def __init__(self, refresh_seconds: int = 3) -> None:
        self.refresh_ms = refresh_seconds * 1000
        self._drag_x = 0
        self._drag_y = 0

        self.root = tk.Tk()
        self.root.title("PORT-HUD")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.90)
        self.root.configure(bg=NEON_CYAN, padx=1, pady=1)
        self.root.geometry("+60+60")

        self.container = tk.Frame(self.root, bg=BG_DARK, padx=10, pady=8)
        self.container.pack(fill=tk.BOTH, expand=True)

        # Header bar (draggable)
        self.header = tk.Frame(self.container, bg=BG_DARK)
        self.header.pack(fill=tk.X, pady=(0, 6))

        self.title_lbl = tk.Label(
            self.header,
            text="⚡ PORT-HUD // TCP LISTEN",
            fg=NEON_CYAN,
            bg=BG_DARK,
            font=FONT_TITLE,
        )
        self.title_lbl.pack(side=tk.LEFT)

        close_btn = tk.Label(
            self.header,
            text="[✕]",
            fg=NEON_PINK,
            bg=BG_DARK,
            font=FONT_TITLE,
            cursor="hand2",
        )
        close_btn.pack(side=tk.RIGHT)
        close_btn.bind("<Button-1>", lambda _e: self.root.destroy())

        for widget in (self.header, self.title_lbl):
            widget.bind("<ButtonPress-1>", self._start_drag)
            widget.bind("<B1-Motion>", self._on_drag)

        # Status bar
        self.status_var = tk.StringVar(value="Scanning...")
        self.status_lbl = tk.Label(
            self.container,
            textvariable=self.status_var,
            fg=TEXT_MUTED,
            bg=BG_DARK,
            font=("Menlo", 9),
            anchor="w",
        )
        self.status_lbl.pack(fill=tk.X, pady=(0, 6))

        # Rows frame
        self.rows_frame = tk.Frame(self.container, bg=BG_DARK)
        self.rows_frame.pack(fill=tk.BOTH, expand=True)

        self.root.bind("<Escape>", lambda _e: self.root.destroy())
        self._refresh()

    def _start_drag(self, event: tk.Event) -> None:
        self._drag_x = event.x_root - self.root.winfo_x()
        self._drag_y = event.y_root - self.root.winfo_y()

    def _on_drag(self, event: tk.Event) -> None:
        x = event.x_root - self._drag_x
        y = event.y_root - self._drag_y
        self.root.geometry(f"+{x}+{y}")

    def _kill_and_refresh(self, entry: PortEntry) -> None:
        ok, msg = kill_pid(entry.pid)
        self.status_var.set(msg if ok else f"ERR: {msg}")
        self.root.after(250, self._refresh)

    def _refresh(self) -> None:
        for child in self.rows_frame.winfo_children():
            child.destroy()

        try:
            entries = scan_ports()
        except RuntimeError as exc:
            self.status_var.set(str(exc))
            self.root.after(self.refresh_ms, self._refresh)
            return

        self.status_var.set(f"{len(entries)} listening port(s) • auto-refresh {self.refresh_ms // 1000}s")

        if not entries:
            tk.Label(
                self.rows_frame,
                text="No listening TCP ports.",
                fg=TEXT_MUTED,
                bg=BG_DARK,
                font=FONT_MONO,
                pady=6,
            ).pack(anchor="w")
        else:
            for idx, entry in enumerate(entries[:20]):
                bg = BG_ROW if idx % 2 == 0 else BG_ROW_ALT
                row = tk.Frame(self.rows_frame, bg=bg, padx=6, pady=3)
                row.pack(fill=tk.X, pady=1)

                tk.Label(
                    row,
                    text=f":{entry.port:<5}",
                    fg=NEON_CYAN,
                    bg=bg,
                    font=FONT_TITLE,
                    width=7,
                    anchor="w",
                ).pack(side=tk.LEFT)

                tk.Label(
                    row,
                    text=f"{entry.process[:14]:<14}",
                    fg=TEXT_LIGHT,
                    bg=bg,
                    font=FONT_MONO,
                    width=15,
                    anchor="w",
                ).pack(side=tk.LEFT)

                tk.Label(
                    row,
                    text=f"PID {entry.pid:<6}",
                    fg=TEXT_MUTED,
                    bg=bg,
                    font=FONT_MONO,
                    width=11,
                    anchor="w",
                ).pack(side=tk.LEFT)

                kill_btn = tk.Label(
                    row,
                    text="KILL",
                    fg=BG_DARK,
                    bg=NEON_PINK,
                    font=FONT_BTN,
                    padx=6,
                    pady=1,
                    cursor="hand2",
                )
                kill_btn.pack(side=tk.RIGHT, padx=(8, 0))
                kill_btn.bind("<Button-1>", lambda _e, e=entry: self._kill_and_refresh(e))

        self.root.after(self.refresh_ms, self._refresh)

    def run(self) -> None:
        self.root.mainloop()


def run_overlay(refresh_seconds: int = 3) -> None:
    """Launch the Cyberpunk Floating HUD."""
    hud = CyberpunkPortHUD(refresh_seconds=refresh_seconds)
    hud.run()

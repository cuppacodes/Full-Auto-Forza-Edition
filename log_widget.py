# ============================================================
#  ui/log_widget.py — Scrollable log area, 1000-line buffer
# ============================================================

import customtkinter as ctk
import queue
import threading


class LogWidget(ctk.CTkFrame):
    MAX_LINES = 1000

    def __init__(self, parent, placeholder="", **kwargs):
        super().__init__(parent, **kwargs)
        self._queue       = queue.Queue()
        self._lines       = []
        self._placeholder = placeholder

        self._text = ctk.CTkTextbox(
            self,
            wrap="word",
            state="disabled",
            font=("Segoe UI", 12),
        )
        self._text.pack(fill="both", expand=True, padx=4, pady=4)

        if placeholder:
            self._text.configure(state="normal")
            self._text.insert("1.0", placeholder)
            self._text.configure(state="disabled",
                                 text_color=("gray60", "gray50"))

        self._poll()

    def log(self, message: str):
        """Thread-safe: append a message to the log."""
        if self._placeholder and not self._lines:
            # Clear placeholder on first real message
            self._queue.put(None)   # clear
            self._placeholder = ""  # don't restore
        self._queue.put(message)

    def clear(self):
        self._queue.put(None)   # sentinel for clear

    def _poll(self):
        """Poll the queue and update the text widget."""
        try:
            while True:
                msg = self._queue.get_nowait()
                if msg is None:
                    self._lines.clear()
                    self._text.configure(state="normal")
                    self._text.delete("1.0", "end")
                    self._text.configure(state="disabled")
                else:
                    self._lines.append(msg)
                    if len(self._lines) > self.MAX_LINES:
                        self._lines.pop(0)
                        self._text.configure(state="normal")
                        self._text.delete("1.0", "2.0")
                        self._text.configure(state="disabled")

                    self._text.configure(state="normal")
                    try:
                        self._text.insert("end", msg + "\n")
                    except Exception:
                        self._text.insert("end", repr(msg) + "\n")
                    self._text.configure(state="disabled")
                    self._text.see("end")
        except queue.Empty:
            pass
        self.after(50, self._poll)

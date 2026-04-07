# modules/orario.py
DURATA_NOTTE_MS = 258000  # 4 minuti e 30 secondi reali: 12 AM -> 6 AM


class Orario:
    def __init__(self, durata_notte_ms=DURATA_NOTTE_MS):
        self.durata_notte_ms = durata_notte_ms
        self.start_ms = None
        self.hour_index = 0
        self.current_hour_label = "12:00 AM"
        self._paused_at_ms = None
        self._paused_total_ms = 0

    def start(self, now_ms):
        self.start_ms = now_ms
        self.hour_index = 0
        self.current_hour_label = "12:00 AM"
        self._paused_at_ms = None
        self._paused_total_ms = 0

    def pause(self, now_ms):
        if self.start_ms is None or self._paused_at_ms is not None:
            return
        self._paused_at_ms = now_ms

    def resume(self, now_ms):
        if self.start_ms is None or self._paused_at_ms is None:
            return
        self._paused_total_ms += max(0, now_ms - self._paused_at_ms)
        self._paused_at_ms = None

    def update(self, now_ms):
        if self.start_ms is None:
            return self.current_hour_label

        if self._paused_at_ms is not None:
            now_ms = self._paused_at_ms

        elapsed = max(0, now_ms - self.start_ms - self._paused_total_ms)
        step_ms = self.durata_notte_ms / 6  # 12->1->2->3->4->5->6
        self.hour_index = min(6, int(elapsed / step_ms))

        if self.hour_index == 0:
            self.current_hour_label = "12:00 AM"
        else:
            self.current_hour_label = f"{self.hour_index}:00 AM"

        return self.current_hour_label

    def is_finished(self):
        return self.hour_index >= 6

    def get_label(self):
        return self.current_hour_label
# modules/orario.py
DURATA_NOTTE_MS = 60000  # 2 minuti reali: 12 AM -> 6 AM


class Orario:
    def __init__(self, durata_notte_ms=DURATA_NOTTE_MS):
        self.durata_notte_ms = durata_notte_ms
        self.start_ms = None
        self.hour_index = 0
        self.current_hour_label = "12:00 AM"

    def start(self, now_ms):
        self.start_ms = now_ms
        self.hour_index = 0
        self.current_hour_label = "12:00 AM"

    def update(self, now_ms):
        if self.start_ms is None:
            return self.current_hour_label

        elapsed = max(0, now_ms - self.start_ms)
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
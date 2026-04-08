"""Gestione del tempo di notte: converte i millisecondi reali in ore di gioco e tiene conto delle pause."""

# modules/orario.py
DURATA_NOTTE_MS = 258000  # 4 minuti e 30 secondi reali per coprire da 12:00 AM a 6:00 AM.


class Orario:
    """Tiene traccia dell'avanzamento della notte, dell'eventuale pausa e dell'etichetta oraria mostrata a schermo."""
    def __init__(self, durata_notte_ms=DURATA_NOTTE_MS):
        """Inizializza durata della notte, indice orario, label corrente e contatori della pausa."""
        self.durata_notte_ms = durata_notte_ms
        self.start_ms = None
        self.hour_index = 0
        self.current_hour_label = "12:00 AM"
        self._paused_at_ms = None
        self._paused_total_ms = 0

    def start(self, now_ms):
        """Azzera i contatori e riparte da 12:00 AM usando il timestamp fornito."""
        self.start_ms = now_ms
        self.hour_index = 0
        self.current_hour_label = "12:00 AM"
        self._paused_at_ms = None
        self._paused_total_ms = 0

    def pause(self, now_ms):
        """Congela il timer salvando l'istante in cui la notte viene messa in pausa."""
        if self.start_ms is None or self._paused_at_ms is not None:
            return
        self._paused_at_ms = now_ms

    def resume(self, now_ms):
        """Riprende il conteggio sottraendo il tempo trascorso mentre la notte era sospesa."""
        if self.start_ms is None or self._paused_at_ms is None:
            return
        self._paused_total_ms += max(0, now_ms - self._paused_at_ms)
        self._paused_at_ms = None

    def update(self, now_ms):
        """Aggiorna l'ora corrente in base al tempo trascorso e all'eventuale pausa."""
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
        """Restituisce True quando la notte è arrivata alle 6:00 AM."""
        return self.hour_index >= 6

    def get_label(self):
        """Restituisce la stringa dell'ora corrente, ad esempio '2:00 AM'."""
        return self.current_hour_label

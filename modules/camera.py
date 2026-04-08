"""Camera orizzontale dell'ufficio: trasforma il cursore in uno scorrimento morbido della vista."""

class Camera:
    """Mantiene l'offset orizzontale del viewport e lo avvicina gradualmente alla posizione desiderata."""
    def __init__(self, viewport_width, world_width, smoothing=0.12):
        """Imposta larghezza visibile, larghezza del mondo e fattore di interpolazione."""
        self.viewport_width = viewport_width
        self.world_width = max(world_width, viewport_width)
        self.max_offset = self.world_width - self.viewport_width
        self.smoothing = smoothing
        self.offset_x = 0.0

    def update_from_cursor(self, cursor_x):
        """Calcola l'offset target dal cursore e lo raggiunge con un movimento graduale."""
        if self.max_offset <= 0:
            self.offset_x = 0.0
            return

        cursor_x = max(0, min(self.viewport_width, cursor_x))
        target = (cursor_x / self.viewport_width) * self.max_offset
        self.offset_x += (target - self.offset_x) * self.smoothing

    def get_offset_x(self):
        """Restituisce l'offset orizzontale corrente come intero."""
        return int(self.offset_x)



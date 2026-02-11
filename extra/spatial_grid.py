class SpatialGrid:
    def __init__(self, cell_size):
        self.cell_size = max(1, int(cell_size))
        self.cells = {}

    def _iter_cells_for_rect(self, rect):
        x0 = int(rect.left // self.cell_size)
        y0 = int(rect.top // self.cell_size)
        x1 = int((rect.right - 1) // self.cell_size)
        y1 = int((rect.bottom - 1) // self.cell_size)
        for cy in range(y0, y1 + 1):
            for cx in range(x0, x1 + 1):
                yield (cx, cy)

    def clear(self):
        self.cells.clear()

    def add(self, item, rect):
        for key in self._iter_cells_for_rect(rect):
            self.cells.setdefault(key, []).append(item)

    def remove(self, item, rect):
        for key in self._iter_cells_for_rect(rect):
            cell = self.cells.get(key)
            if not cell:
                continue
            try:
                cell.remove(item)
            except ValueError:
                pass
            if not cell:
                del self.cells[key]

    def build(self, items, rect_fn):
        self.clear()
        for item in items:
            self.add(item, rect_fn(item))

    def query_rect(self, rect):
        result = []
        seen = set()
        for key in self._iter_cells_for_rect(rect):
            for item in self.cells.get(key, []):
                item_id = id(item)
                if item_id in seen:
                    continue
                seen.add(item_id)
                result.append(item)
        return result

"""Reusable plot decorations that do not relayout text on every pan frame."""
import math
import numpy as np
from matplotlib.legend import Legend
from matplotlib.backends.backend_agg import RendererAgg


class CachedLegend(Legend):
    """Cache a transparent legend image; keep original text objects for clicks."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._image_key = None
        self._image = None

    def draw(self, renderer):
        if not self.get_visible():
            return
        if not isinstance(renderer, RendererAgg):
            return super().draw(renderer)
        width, height = int(renderer.width), int(renderer.height)
        key = (width, height, renderer.dpi, tuple(self.axes.bbox.bounds))
        if key != self._image_key:
            # Draw on a transparent buffer, so cached pixels never contain the
            # curves underneath a translucent legend or its rounded corners.
            temporary = RendererAgg(width, height, renderer.dpi)
            super().draw(temporary)
            bounds = self.get_window_extent(temporary)
            x0 = max(0, math.floor(bounds.x0)-2)
            y0 = max(0, math.floor(bounds.y0)-2)
            x1 = min(width, math.ceil(bounds.x1)+2)
            y1 = min(height, math.ceil(bounds.y1)+2)
            if x1 <= x0 or y1 <= y0:
                return
            pixels = np.asarray(temporary.buffer_rgba())[height-y1:height-y0, x0:x1]
            self._image = np.ascontiguousarray(pixels[::-1])
            self._image_origin = (x0, y0)
            self._image_key = key
        gc = renderer.new_gc()
        try:
            renderer.draw_image(gc, *self._image_origin, self._image)
        finally:
            gc.restore()
        self.stale = False

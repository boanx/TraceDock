"""Reusable plot decorations that do not relayout text on every pan frame."""
import math
import numpy as np
from matplotlib.legend import Legend
from matplotlib.text import Annotation, Text
from matplotlib.artist import Artist
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


class ProbeLabelLayout:
    """Place probe boxes in display pixels and reuse placement until geometry changes."""
    def __init__(self, axes):
        self.axes = axes
        self.labels = []
        self._key = None

    def arrange(self, renderer):
        bounds = self.axes.bbox
        points = [label.axes.transData.transform(label.xy) for label in self.labels]
        key = (tuple(bounds.bounds), renderer.points_to_pixels(1),
               tuple((tuple(point), label.get_text(), label.get_fontsize(), label.get_visible())
                     for label, point in zip(self.labels, points)))
        if key == self._key:
            return
        self._key = key
        scale = renderer.points_to_pixels(1)
        gap = renderer.points_to_pixels(5)
        margin = renderer.points_to_pixels(3)
        left, bottom, right, top = bounds.x0+margin, bounds.y0+margin, bounds.x1-margin, bounds.y1-margin
        placed = []
        for label, (x, y) in zip(self.labels, points):
            if not label.get_visible() or not np.isfinite([x,y]).all() or not bounds.contains(x,y):
                continue
            label.set_position((0,0));label.update_positions(renderer);label.update_bbox_position_size(renderer)
            box = label.get_bbox_patch().get_window_extent(renderer)
            width, height = box.width, box.height
            dx, dy = box.x0-x, box.y0-y
            candidates = []
            for ring in range(4):
                gx, gy = gap+ring*(width+gap), gap+ring*(height+gap)
                candidates.extend([(x+gx,y+gy),(x-gx-width,y+gy),
                                   (x+gx,y-gy-height),(x-gx-width,y-gy-height),
                                   (x+gx,y-height/2),(x-gx-width,y-height/2),
                                   (x-width/2,y+gy),(x-width/2,y-gy-height)])
            # If a dense cluster fills all nearby directions, search free rows.
            candidates.extend((cx,cy) for cy in np.arange(bottom,max(bottom,top-height)+1,height+gap)
                              for cx in np.arange(left,max(left,right-width)+1,width+gap))
            best = None
            for cx,cy in candidates:
                cx = max(left,min(right-width,cx));cy = max(bottom,min(top-height,cy))
                overlap = sum(max(0,min(cx+width,bx+bw+gap)-max(cx,bx-gap))*
                              max(0,min(cy+height,by+bh+gap)-max(cy,by-gap))
                              for bx,by,bw,bh in placed)
                distance = (cx+width/2-x)**2+(cy+height/2-y)**2
                score = (overlap,distance)
                if best is None or score<best[0]:best=(score,cx,cy)
                if overlap==0 and len(placed)==0:break
            _,cx,cy = best
            label.set_position(((cx-x-dx)/scale,(cy-y-dy)/scale))
            placed.append((cx,cy,width,height))


class ProbeAnnotation(Annotation):
    def __init__(self, layout, *args, **kwargs):
        self.layout = layout
        super().__init__(*args, **kwargs)
        layout.labels.append(self)

    def draw(self, renderer):
        self.layout.arrange(renderer)
        super().draw(renderer)


class ProbeLabelLayer(Artist):
    """Draw leaders first, then all boxes, so leaders never obscure probe text."""
    def __init__(self, layout):
        super().__init__()
        self.layout = layout
        self.set_zorder(10)

    def draw(self, renderer):
        if not self.get_visible():return
        self.layout.arrange(renderer)
        visible = [label for label in self.layout.labels if label.get_visible()
                   and label.axes.bbox.contains(*label.axes.transData.transform(label.xy))]
        for label in visible:
            label.update_positions(renderer)
            if label.arrow_patch is not None:label.arrow_patch.draw(renderer)
        for label in visible:Text.draw(label,renderer)
        self.stale = False

import ipycanvas
from ipycanvas import Canvas
from ipyevents import Event
from matplotlib import cm
from cffi import FFI
import numpy as np

ffi = FFI()
ffi.cdef('''
void julia_miim(double cr, double ci, double zr, double zi, 
double * p_, int n, unsigned char * grid, int resolution, int max_count);
''')
lib = ffi.dlopen('julia.wasm')

def calc_fix_point(c):
    roots = np.roots([1, -1, c])
    z = roots
    for i in range(100):
        z = z**2 + c
        if np.any(np.abs(z) >= 2):
            break

    return min(z, key=abs)


class JuliaPlot:
    def __init__(self, n=200000, resolution=500, max_count=10, cmap='Blues'):
        self.cmap = (cm.get_cmap(cmap)(np.linspace(0, 1, max_count+1)) * 255).astype(np.uint8)[:, :3]
        self.n = n
        self.resolution = resolution
        self.max_count = max_count

        self.p = np.zeros(n, dtype=np.complex128);
        self.grid = np.zeros((resolution, resolution), dtype=np.uint8)
        self.image = np.zeros((resolution, resolution, 3), dtype=np.uint8)
        
        self.canvas = Canvas(width=resolution, height=resolution)
        self.event = Event(source=self.canvas, watched_events=['mousemove'], wait=100)
        self.event.on_dom_event(self.handle_event)
        self.calc_julia(-0.11 + 0.65569999*1j)
        
    def handle_event(self, event):
        x = event['relativeX']
        y = event['relativeY']
        w = event['boundingRectWidth']
        h = event['boundingRectHeight']
        x2 = (x - w / 2) / w * 4
        y2 = (y - h / 2) / h * 4
        c = x2 + y2 * 1j
        self.calc_julia(c)

    def calc_julia(self, c):
        z0 = calc_fix_point(c)
        self.grid[:, :] = 0
        lib.julia_miim(
            c.real, c.imag,
            z0.real, z0.imag,
            ffi.from_buffer('double[]', self.p),
            self.n,
            ffi.from_buffer('unsigned char[]', self.grid),
            self.resolution,
            self.max_count
        )
        self.image[:, :] = self.cmap[self.grid]
        self.canvas.put_image_data(self.image, 0, 0)

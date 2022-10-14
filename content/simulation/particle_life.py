import ipycanvas
from ipycanvas import Canvas
import numpy as np
import cffi
import asyncio
import ipywidgets as ipw

ParticleType = np.dtype([
    ('px', np.float32),
    ('py', np.float32),
    ('vx', np.float32),
    ('vy', np.float32),
    ('fx', np.float32),
    ('fy', np.float32),
    ('type', np.int32),
    ('index', np.int32),
], align=True)

COLORS = np.array(
      [[ 31, 119, 180],
       [255, 127,  14],
       [ 44, 160,  44],
       [214,  39,  40],
       [148, 103, 189],
       [140,  86,  75],
       [227, 119, 194],
       [127, 127, 127],
       [188, 189,  34],
       [ 23, 190, 207]], dtype=np.uint8)

ffi = cffi.FFI()
ffi.cdef('''
void particles_update(void * p, int n, float * gravity, float * radius, 
    int n_color, int width, int height, float edge_strength, float viscosity, float time_scale);

void particles_update_fast(void * p, int n, float * gravity, float * radius, 
    int n_color, int width, int height, float edge_strength, float viscosity, float time_scale, 
    int * buf_start, int * buf_end, int * buf_index, int block_size, float max_dist);   
''')
lib = ffi.dlopen('particle_life.wasm')

current_task = None

class ParticleLife:
    def __init__(self, width=800, height=600, edge_strength=1.0, time_scale=0.2, N=5000, N_COLOR=10, viscosity=0.3, block_size=16):
        self.block_size = block_size
        self.width = width // block_size * block_size
        self.height = height // block_size * block_size
        self.width2 = self.width // block_size
        self.height2 = self.height // block_size
        self.edge_strength = edge_strength
        self.time_scale = time_scale
        self.N = N
        self.N_COLOR = N_COLOR
        self.viscosity = viscosity
        self.gravity = np.zeros((N_COLOR, N_COLOR), np.float32)
        self.radius = np.zeros((N_COLOR, N_COLOR), np.float32)

        self.colors = COLORS
        self.particles = np.zeros(N, ParticleType)
        self.canvas = Canvas(width=self.width, height=self.height, layout=ipw.Layout(width=f'{self.width}px', height=f'{self.height}px'))
        self.buf_start = np.zeros((self.height2, self.width2), np.int32)
        self.buf_end = np.zeros((self.height2, self.width2), np.int32)
        self.buf_index = np.zeros(self.N, np.int32)
        self.reset_button = ipw.Button(description='Reset')
        self.viscosity_slider = ipw.FloatSlider(0.3, min=0.1, max=0.9, step=0.01, description='Viscosity', layout=ipw.Layout(width='500px'))
        self.layout = ipw.VBox([ipw.HBox([self.reset_button, self.viscosity_slider]), self.canvas])
        self.reset_button.on_click(self.on_reset)
        self.viscosity_slider.observe(self.on_viscosity_change, names='value')

        self._particles = ffi.from_buffer('void *', self.particles)
        self._gravity = ffi.from_buffer('float *', self.gravity)
        self._radius = ffi.from_buffer('float *', self.radius)
        self._buf_start = ffi.from_buffer('int *', self.buf_start)
        self._buf_end = ffi.from_buffer('int *', self.buf_end)
        self._buf_index = ffi.from_buffer('int *', self.buf_index)        
        
    def on_reset(self, b):
        self.init()
        
    def on_viscosity_change(self, event):
        self.viscosity = event['new']
        
    def init(self):
        self.gravity[...] = np.random.uniform(-1, 1, (self.N_COLOR, self.N_COLOR)).astype(np.float32)
        self.radius[...] = np.random.uniform(20, 60, (self.N_COLOR, self.N_COLOR)).astype(np.float32)
        self.max_dist = self.radius.max()        
        self.particles['px'] = np.random.uniform(0, self.width, self.N)
        self.particles['py'] = np.random.uniform(0, self.height, self.N)
        self.particles['type'] = np.random.randint(0, self.N_COLOR, self.N)
        self.particles['vx'] = np.random.uniform(-1, 1, self.N)
        self.particles['vy'] = np.random.uniform(-1, 1, self.N)
        self.particles['fx'] = 0
        self.particles['fy'] = 0

    def update_fast(self):
        lib.particles_update_fast(
            self._particles,
            self.N,
            self._gravity,
            self._radius,
            self.N_COLOR,
            self.width,
            self.height,
            self.edge_strength,
            self.viscosity,
            self.time_scale,
            self._buf_start,
            self._buf_end,
            self._buf_index,
            self.block_size,
            self.max_dist
            )        
        
    def update(self):
        lib.particles_update(
            self._particles,
            self.N,
            self._gravity,
            self._radius,
            self.N_COLOR,
            self.width,
            self.height,
            self.edge_strength,
            self.viscosity,
            self.time_scale,
            )
        
    def start(self):
        global current_task
        if current_task is not None:
            current_task.cancel()
            current_task = None
            
        async def draw_lines():
            colors = self.colors[self.particles['type']]
            while True:
                self.update_fast()
                x = self.particles['px']
                y = self.particles['py']
                segments = np.c_[x-0.5, y-0.5, x+0.5, y+0.5].reshape(-1, 2, 2)
                with ipycanvas.hold_canvas(self.canvas):
                    self.canvas.clear()   
                    self.canvas.fill_style = 'black'     
                    self.canvas.fill_rect(0, 0, self.width, self.height)
                    self.canvas.line_width = 2
                    self.canvas.stroke_styled_line_segments(segments, color=colors, alpha=0.5)
                await asyncio.sleep(0.05)                
    
        current_task = asyncio.create_task(draw_lines())
        return current_task
        
if __name__ == '__main__':        
    import time
    self = ParticleLife(width=512, height=512, N=4000)
    self.init()
    start = time.perf_counter()
    for i in range(100):
        self.update_fast()
    print((time.perf_counter() - start) / 100)
    print('ok')
import numpy as np
import cffi
import ipycanvas
from ipycanvas import Canvas
from ipyevents import Event
import asyncio


ffi = cffi.FFI()
ffi.cdef('''
void ants_update(void *ants, int n, 
    float *food_chemical, float * food_chemical2, float *home_chemical, float *home_chemical2, 
    int *home, float *food, int width, int height, float ant_length);
''')
lib = ffi.dlopen('ants.wasm')


AntType = np.dtype([
    ('x', np.float32),
    ('y', np.float32),
    ('x2', np.float32),
    ('y2', np.float32),
    ('angle', np.float32),
    ('food_chemical', np.float32),
    ('home_chemical', np.float32),
    ('clock', np.int32),
    ('status', np.int32),
], align=True)

current_task = None

class Ants:
    def __init__(self, width=500, height=400, n=2000):
        self.ant_length = 1
        self.n = n
        self.width = width
        self.height = height
        self.ants = np.zeros(self.n, dtype=AntType)
        self.home_chemical = np.zeros((height, width), np.float32)
        self.home_chemical2 = np.zeros((height, width), np.float32)
        self.food_chemical = np.zeros((height, width), np.float32)
        self.food_chemical2 = np.zeros((height, width), np.float32)
        self.home = np.zeros((height, width), np.int32)
        self.food = np.zeros((height, width), np.float32)
        self.canvas = Canvas(width=self.width, height=self.height)
        self.event = Event(source=self.canvas, watched_events=['mousedown'], wait=100)
        self.event.on_dom_event(self.handle_event)        
        self.image = np.zeros((self.height, self.width, 3), np.uint8)
        self._ants = ffi.from_buffer('void *', self.ants)
        self._home_chemical = ffi.from_buffer('float *', self.home_chemical)
        self._home_chemical2 = ffi.from_buffer('float *', self.home_chemical2)
        self._food_chemical = ffi.from_buffer('float *', self.food_chemical)
        self._food_chemical2 = ffi.from_buffer('float *', self.food_chemical2)
        self._home = ffi.from_buffer('int *', self.home)
        self._food = ffi.from_buffer('float *', self.food)
        
    def handle_event(self, event):
        x = event['relativeX']
        y = event['relativeY']
        self.set_food(x, y)

    def init(self):
        self.set_food(self.width * 0.8, self.height * 0.7)
        self.set_food(self.width * 0.2, self.height * 0.3)
        self.set_home(self.width * 0.5, self.height * 0.5)
        self._home_y, self._home_x = np.where(self.home > 0)

        self.ants['status'] = 1
        self.ants['clock'] = 0
        self.ants['x'] = self.width * 0.5
        self.ants['y'] = self.height * 0.5
        self.ants['home_chemical'] = 1.0
        self.ants['food_chemical'] = 0.0
        self.ants['angle'] = np.random.uniform(0, 2*np.pi, self.n)
        self.ants['x2'] = self.ants['x'] + np.cos(self.ants['angle']) * self.ant_length
        self.ants['y2'] = self.ants['x'] + np.sin(self.ants['angle']) * self.ant_length

    def set_food(self, xc, yc):
        y, x = np.indices((self.food.shape))
        mask = np.hypot(x - xc, y - yc) < 10
        self.food[mask] = 2.0

    def set_home(self, xc, yc):
        y, x = np.indices((self.food.shape))
        mask = np.hypot(x - xc, y - yc) < 10
        self.home[mask] = 1

    def update(self):
        lib.ants_update(
            self._ants,
            self.n,
            self._food_chemical,
            self._food_chemical2,
            self._home_chemical,
            self._home_chemical2,
            self._home,
            self._food,
            self.width,
            self.height,
            self.ant_length
        )

    def draw(self):
        y, x = np.where(self.food > 0)
        self.image[..., :] = ((self.food_chemical / self.food_chemical.max()) * 200)[:, :, None]
        self.image[y, x, 0] = np.clip(self.food[y, x] * 127, 0, 255)
        self.image[self._home_y, self._home_x, 1] = 200

        with ipycanvas.hold_canvas(self.canvas):
            self.canvas.put_image_data(self.image)
            x = self.ants['x']
            y = self.ants['y']
            x2 = self.ants['x2']
            y2 = self.ants['y2']
            segments = np.c_[x, y, x2, y2].reshape(-1, 2, 2)
            self.canvas.stroke_style = '#ffffff'
            self.canvas.stroke_line_segments(segments)
            
    def stop(self):
        global current_task
        if current_task is not None:
            current_task.cancel()
            current_task = None        

    def start(self):
        global current_task
        self.stop()
        async def plot():
            while True:
                for i in range(2):
                    self.update()
                self.draw()
                await asyncio.sleep(0.02)
        current_task = asyncio.create_task(plot())
        return current_task


if __name__ == '__main__':
    self = Ants()
    self.init()
    for i in range(100):
        print(i)
        self.update()
    print('ok')
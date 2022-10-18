import ipywidgets as ipw
import ipycanvas
from ipycanvas import Canvas
from ipyevents import Event
import numpy as np
from matplotlib import cm
import json
import asyncio
from cffi import FFI


ffi = FFI()
ffi.cdef(
    """
typedef struct _Point
{
    double x;
    double y;
} Point;

int ifs_iter(Point *point, int n, double *eqs, int *ps, int neq, int *count, int width, int height);
void paint_image(int *count, unsigned char * cmap, unsigned char * image, int width, int height);
"""
)

lib = ffi.dlopen("ifs_iter.wasm")

COLORS = np.array(
    [
        [31, 119, 180],
        [255, 127, 14],
        [44, 160, 44],
        [214, 39, 40],
        [148, 103, 189],
        [140, 86, 75],
        [227, 119, 194],
        [127, 127, 127],
        [188, 189, 34],
        [23, 190, 207],
    ],
    dtype=np.uint8,
)

POINT_COLORS = np.array(
    [
        [255, 0, 0],
        [0, 255, 0],
        [0, 255, 255],
    ],
    dtype=np.uint8,
)

ALL_CMAPS = [
 'magma',
 'inferno',
 'plasma',
 'viridis',
 'cividis',
 'twilight',
 'twilight_shifted',
 'turbo',
 'Blues',
 'BrBG',
 'BuGn',
 'BuPu',
 'CMRmap',
 'GnBu',
 'Greens',
 'Greys',
 'OrRd',
 'Oranges',
 'PRGn',
 'PiYG',
 'PuBu',
 'PuBuGn',
 'PuOr',
 'PuRd',
 'Purples',
 'RdBu',
 'RdGy',
 'RdPu',
 'RdYlBu',
 'RdYlGn',
 'Reds',
 'Spectral',
 'Wistia',
 'YlGn',
 'YlGnBu',
 'YlOrBr',
 'YlOrRd',
 'afmhot',
 'autumn',
 'binary',
 'bone',
 'brg',
 'bwr',
 'cool',
 'coolwarm',
 'copper',
 'cubehelix',
 'flag',
 'gist_earth',
 'gist_gray',
 'gist_heat',
 'gist_ncar',
 'gist_rainbow',
 'gist_stern',
 'gist_yarg',
 'gnuplot',
 'gnuplot2',
 'gray',
 'hot',
 'hsv',
 'jet',
 'nipy_spectral',
 'ocean',
 'pink',
 'prism',
 'rainbow',
 'seismic',
 'spring',
 'summer',
 'terrain',
 'winter',
 'Accent',
 'Dark2',
 'Paired',
 'Pastel1',
 'Pastel2',
 'Set1',
 'Set2',
 'Set3',
 'tab10',
 'tab20',
 'tab20b',
 'tab20c',
 'magma_r',
 'inferno_r',
 'plasma_r',
 'viridis_r',
 'cividis_r',
 'twilight_r',
 'twilight_shifted_r',
 'turbo_r',
 'Blues_r',
 'BrBG_r',
 'BuGn_r',
 'BuPu_r',
 'CMRmap_r',
 'GnBu_r',
 'Greens_r',
 'Greys_r',
 'OrRd_r',
 'Oranges_r',
 'PRGn_r',
 'PiYG_r',
 'PuBu_r',
 'PuBuGn_r',
 'PuOr_r',
 'PuRd_r',
 'Purples_r',
 'RdBu_r',
 'RdGy_r',
 'RdPu_r',
 'RdYlBu_r',
 'RdYlGn_r',
 'Reds_r',
 'Spectral_r',
 'Wistia_r',
 'YlGn_r',
 'YlGnBu_r',
 'YlOrBr_r',
 'YlOrRd_r',
 'afmhot_r',
 'autumn_r',
 'binary_r',
 'bone_r',
 'brg_r',
 'bwr_r',
 'cool_r',
 'coolwarm_r',
 'copper_r',
 'cubehelix_r',
 'flag_r',
 'gist_earth_r',
 'gist_gray_r',
 'gist_heat_r',
 'gist_ncar_r',
 'gist_rainbow_r',
 'gist_stern_r',
 'gist_yarg_r',
 'gnuplot_r',
 'gnuplot2_r',
 'gray_r',
 'hot_r',
 'hsv_r',
 'jet_r',
 'nipy_spectral_r',
 'ocean_r',
 'pink_r',
 'prism_r',
 'rainbow_r',
 'seismic_r',
 'spring_r',
 'summer_r',
 'terrain_r',
 'winter_r',
 'Accent_r',
 'Dark2_r',
 'Paired_r',
 'Pastel1_r',
 'Pastel2_r',
 'Set1_r',
 'Set2_r',
 'Set3_r',
 'tab10_r',
 'tab20_r',
 'tab20b_r',
 'tab20c_r'
]

def triangle_area(points):
    (x1, y1), (x2, y2), (x3, y3) = points
    a = np.hypot(x1 - x2, y1 - y2)
    b = np.hypot(x2 - x3, y2 - y3)
    c = np.hypot(x1 - x3, y1 - y3)
    s = 0.5 * (a + b + c)
    return (s * (s - a) * (s - b) * (s - c)) ** 0.5


class IFS:
    def __init__(self, width=400, height=400, cmap="Blues", max_iter=500000):
        self.data_filename = 'ifs_data.json'
        with open(self.data_filename, encoding='utf-8') as f:
            self.data = json.load(f)
            
        self.max_iter = max_iter
        self.cmap = (cm.get_cmap(cmap)(np.linspace(0, 1, 256)) * 255).astype(np.uint8)[:, :3].copy()
        self.width = width
        self.height = height
        self.canvas = Canvas(width=self.width, height=self.height)
        self.canvas2 = Canvas(width=self.width, height=self.height)
        self.image = np.zeros((self.height, self.width, 3), np.uint8)
        self.info = ipw.Textarea(layout=ipw.Layout(height="400px"))
        self.selector = ipw.Dropdown(options=[item['name'] for item in self.data], layout=ipw.Layout(width="120px"))
        self.select_cmap = ipw.Dropdown(options=ALL_CMAPS, layout=ipw.Layout(width="100px"))
        self.selector.observe(self.on_select_name, names='value')
        self.select_cmap.observe(self.on_select_cmap, names='value')
        self.input_name = ipw.Text(description='Name', layout=ipw.Layout(width="200px"))
        self.save_button = ipw.Button(description='Save', layout=ipw.Layout(width="100px"))
        self.save_button.on_click(self.on_save)
        self.toolbar = ipw.HBox([self.selector, self.select_cmap, self.input_name, self.save_button])
        self.main_layout = ipw.HBox([self.canvas, self.canvas2])
        self.layout = ipw.VBox([self.toolbar, self.main_layout])
        self.event = Event(source=self.canvas, watched_events=["mousemove", "mousedown", "mouseup", "keydown"], wait=100)
        self.event.on_dom_event(self.callback)
        self.current_point = None
        self.counts = np.zeros((self.height, self.width), np.int32)
        self.iter_point = ffi.new("Point *")
        self.points = []
        self.task = None
        self.move_start_point = None
        self._points = []
        self.load_data(self.selector.options[0])
                              
    def on_save(self, b):
        name = self.input_name.value
        self.data.append(dict(name=name, cmap=self.select_cmap.value, points=self.points))
        with open(self.data_filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2)
        options = list(self.selector.options)
        options.append(name)
        self.selector.options = options
        self.selector.value = name
            
    def on_select_name(self, event):
        self.load_data(self.selector.value)
        
    def on_select_cmap(self, event):
        self.set_cmap(self.select_cmap.value)
        self.start_task()

    def set_cmap(self, name):
        self.cmap = (cm.get_cmap(name)(np.linspace(0, 1, 256)) * 255).astype(np.uint8)[:, :3].copy()
        
    async def timer_task(self):
        self.iter_count = 0
        iter_step = 10000
        while self.iter_count < self.max_iter:
            self.calc_ifs(iter_step)
            self.iter_count += iter_step
            await asyncio.sleep(0.05)

    def load_data(self, name):
        index = self.selector.options.index(name)
        if index >= 0:
            item = self.data[index]
            self.set_cmap(item['cmap'])
            self.select_cmap.value = item['cmap']
            self.points = item['points'][:]
            self.calc_triangles()
            self.draw()
            self.start_task()

    def start_task(self):
        if self.task is not None:
            self.task.cancel()
            self.task = None
        self.task = asyncio.create_task(self.timer_task())

    def calc_triangles(self):
        p = self.points
        if len(p) >= 9:
            self.iter_point.x, self.iter_point.y = p[0]
            self.counts[...] = 0
            x1, y1 = p[0]

            n_triangles = len(p) // 3 - 1
            self.eqs = np.zeros((n_triangles, 6))
            areas = np.zeros(n_triangles)
            for k in range(n_triangles):
                A = []
                b = []

                for i in range(3):
                    x1, y1 = p[i]
                    x2, y2 = p[i + (k + 1) * 3]
                    A.append([x1, y1, 1, 0, 0, 0])
                    A.append([0, 0, 0, x1, y1, 1])
                    b.append(x2)
                    b.append(y2)

                self.eqs[k] = np.linalg.solve(A, b)
                areas[k] = triangle_area(p[(k + 1) * 3 : (k + 2) * 3])

            self.ps = (np.cumsum(areas / np.sum(areas)) * 1000).astype(np.int32)
            self.start_task()
        else:
            if self.task is not None:
                self.task.cancel()
                self.task = None

    def calc_ifs(self, n):
        res = lib.ifs_iter(
            self.iter_point,
            n,
            ffi.from_buffer("double *", self.eqs),
            ffi.from_buffer("int *", self.ps),
            self.eqs.shape[0],
            ffi.from_buffer("int *", self.counts),
            self.width,
            self.height,
        )
        lib.paint_image(
            ffi.from_buffer("int *", self.counts),
            ffi.from_buffer("unsigned char *", self.cmap),
            ffi.from_buffer("unsigned char *", self.image),
            self.width,
            self.height,
        )
        with ipycanvas.hold_canvas(self.canvas2):
            self.canvas2.put_image_data(self.image, 0, 0)
            
        return res

    def callback(self, event):
        #self.info.value = json.dumps(event, indent=2)
        need_update = False
        if event["type"] == "mousedown":
            x = event["relativeX"]
            y = event["relativeY"]            
            if event["ctrlKey"]:
                self.points.append((x, y))
                need_update = True
            elif event["shiftKey"]:
                self.move_start_point = x, y
                self._points = self.points[:]
            else:
                if len(self.points) > 0:
                    xp, yp = np.array(self.points).T
                    dist = np.hypot(xp - x, yp - y)
                    if dist.min() < 6:
                        self.current_point = np.argmin(dist)
        elif event["type"] == "mousemove":
            x = event["relativeX"]
            y = event["relativeY"]                            
            if self.current_point is not None:
                self.points[self.current_point] = (x, y)
                need_update = True
            elif self.move_start_point is not None:
                dx = x - self.move_start_point[0]
                dy = y - self.move_start_point[1]
                self.points = [(x + dx, y + dy) for x, y in self._points]
                need_update = True
        elif event["type"] == "mouseup":
            self.current_point = None
            self.move_start_point = None
            self._points = None
            
        elif event["type"] == "keydown":
            if event["key"] == "Backspace":
                self.points.pop(-1)
                need_update = True

        if need_update:
            self.calc_triangles()
            self.draw()

    def draw(self):
        with ipycanvas.hold_canvas(self.canvas):
            n = len(self.points)
            self.canvas.clear()
            self.canvas.fill_style = "black"
            self.canvas.fill_rect(0, 0, self.width, self.height)
            if n == 0:
                return
            self.canvas.fill_style = "#ffffff"
            x, y = np.array(self.points).T
            colors = POINT_COLORS[np.arange(n) % 3]
            self.canvas.fill_styled_circles(x, y, 3, colors)
            if n >= 3:
                segments = []
                colors = []
                p = self.points
                for i in range(0, n, 3):
                    j = i + 1
                    k = i + 2
                    if k >= len(p):
                        break
                    segments.extend([(p[i], p[j]), (p[j], p[k]), (p[i], p[k])])
                    i2 = i // 3
                    colors.extend([COLORS[i2], COLORS[i2], COLORS[i2]])

                self.canvas.line_width = 1.5
                segments = np.asarray(segments)
                colors = np.asarray(colors)
                self.canvas.stroke_styled_line_segments(segments, colors)

'''
import json
import numpy as np

with open('ifsdesigner.json') as f:
    data = json.load(f)

new_data = []
for name, info in data:
    cmap = info['cmap']
    points = info['points']
    points = np.array(points)
    points[:, 1] *= -1
    xmin, ymin = points.min(axis=0)
    xmax, ymax = points.max(axis=0)

    xspan = xmax - xmin
    yspan = ymax - ymin
    xspan, yspan
    span = max(xspan, yspan)

    new_points = (points - (xmin, ymin))/ span * 300 + 50
    new_data.append(dict(name=name, cmap=cmap, points=new_points.tolist()))

with open('ifs_data.json', 'w', encoding='utf-8') as f:
    json.dump(new_data, f)
'''
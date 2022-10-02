from scipy import optimize
import numpy as np
from sympy import IndexedBase, Point, atan2, lambdify, Segment, symbols, pi, Point2D, Segment2D
import ipycanvas
from ipycanvas import Canvas
import ipywidgets as ipw

class Linkage:
    def __init__(self, point_names, links):
        self.params = IndexedBase("p")
        self.point_names = point_names
        self.points = dict(zip(point_names, self.make_points()))
        self.segments = {k:Segment(self.points[p1], self.points[p2]) for k, (p1, p2) in links.items()}
        self.constraints = []
        
    def make_points(self):
        p = self.params
        for i in range(len(self.point_names)):
            yield Point(p[i*2], p[i*2+1])
        
    def __getitem__(self, name):
        if name in self.points:
            return self.points[name]
        return self.segments[name]
        
    def fix_point(self, name, x, y):
        p = self.points[name]
        self.constraints.append(p.x - x)
        self.constraints.append(p.y - y)
        
    def fix_length(self, name, length):
        self.constraints.append(self.segments[name].length - length)
    
    def fix_angle_between_xaxis(self, name, angle):
        d = self.segments[name].direction
        angle_diff = atan2(d.y, d.x) / pi * 180 - angle
        angle_diff = (angle_diff + 180) % 360 - 180
        self.constraints.append(angle_diff)
        
    def get_error_func(self, *args):
        err = sum([c**2 for c in self.constraints])
        func_err = lambdify([self.params] + list(args), err, modules="math")
        return func_err
    
    def get_init(self, **kw):
        init = [0] * (len(self.points) * 2)
        for name, (x, y) in kw.items():
            p = self.points[name]
            init[int(p.x.indices[0])] = x
            init[int(p.y.indices[0])] = y
        return np.array(init)
    
    
def get_index(o):
    if isinstance(o, Point2D):
        return [int(o.x.indices[0]), int(o.y.indices[0])]
    elif isinstance(o, Segment2D):
        return get_index(o.p1) + get_index(o.p2)

    
def get_all_indices(objs):
    return np.array([get_index(o) for o in objs])    
    
    
class JansenLinkage:
    def __init__(self, lengths=None):
        link = Linkage("ABCDEFGHI", 
                      dict(a="ED", b="CE", c="EH", d="FE", e="FC", f="FG", 
                           g="GH", h="GI", i="HI", j="CB", k="HB", l="AD", m="AB"))
        self.size = 400
        if lengths is None:
            lengths = dict(a=38, b=41.5, c=39.3, d=40.1, e=55.8, f=39.4, 
                           g=36.7, h=65.7, i=49.0, j=50, k=61.9, l=7.8, m=15.0)
        link.fix_point("A", 0, 0)
        link.fix_point("D", 0, -lengths["l"])
        link.fix_point("E", -lengths["a"], -lengths["l"])
        for k, v in lengths.items():
            if k not in ["a", "l"]:
                link.fix_length(k, v)
        angle = symbols("angle")
        link.fix_angle_between_xaxis("m", angle)
        self.link = link
        self.error_func = link.get_error_func(angle)        
        self.index_of_points =  get_all_indices(link.points.values())
        self.index_of_segments = get_all_indices(link.segments.values())
        
        self.init0 = link.get_init(
             A=(0, 0),
             D=(0, -lengths["l"]),
             E=(-lengths["a"], -lengths["l"]),
             B=(10, -5), 
             C=(-20, 50), 
             G=(-100, -30),
             H=(-50, -50), 
             I=(-90, -150),
             F=(-100, 30),
        ) 
        
    def solve_positions(self, npoints=60):
        self.angles = angles = np.linspace(0, 360, npoints)
        positions = []
        init = self.init0
        for angle_init in angles:
            r = optimize.minimize(self.error_func, init, args=(angle_init,), method="L-BFGS-B")
            init = r.x
            positions.append(r.x)
        self.positions = np.vstack(positions)        

    def make_gui(self):
        self.canvas = Canvas(width=self.size, height=self.size)
        slider = ipw.IntSlider(0, min=0, max=360*3, layout=ipw.Layout(width='600px'))
        slider.observe(self.redraw, names='value')
        self.gui = ipw.VBox([slider, ipw.HBox([self.canvas])])
        self.link_colors = np.full((len(self.link.segments), 3), 100)
        self.redraw(dict(new=slider.value))

    def redraw(self, change):
        canvas = self.canvas
        size = self.size
        angle = change['new'] % 360
        index = np.searchsorted(self.angles, angle)
        position = self.positions[index]
        x, y = position[self.index_of_points].T
        x0, y0, x1, y1 = position[self.index_of_segments].T
        segments = np.c_[x0, y0, x1, y1].reshape(-1, 2, 2)

        with ipycanvas.hold_canvas(canvas):
            canvas.reset_transform()
            canvas.clear()
            canvas.translate(size//2 + size // 3, size//2 - size // 4)
            canvas.scale(2, -2)    
            canvas.fill_style = '#ff0000'    
            canvas.fill_circles(x, y, 2)
            canvas.stroke_styled_line_segments(segments, self.link_colors)
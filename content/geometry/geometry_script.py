import importlib
import random
import re
import math
import numpy as np
from python_solvespace import make_quaternion
from solvespace import SolverSystem


def point(name="point"):
    return rf"(?P<{name}>[A-Z])"


def line(name="line"):
    if name is not None:
        return rf"(?P<{name}>[A-Z]{{2}})"
    else:
        return rf"([A-Z]{{2}})"


def circle(name="circle"):
    if name is not None:
        return rf"(?P<{name}>@[a-z,1-9])"
    else:
        return rf"(@[a-z,1-9])"


def arc(name="arc"):
    if name is not None:
        return rf"(?P<{name}>~[a-z,1-9])"
    else:
        return rf"(~[a-z,1-9])"


def op(op):
    return rf"\s*{op}\s*"


def keyword(kw):
    return rf"\s+{kw}\s+"


def number(name="value"):
    return rf"(?P<{name}>-?\d+(?:\.\d+)?!?)"


def pos(namex="x", namey="y"):
    return rf"{number(namex)}\s*,\s*{number(namey)}"


eq = op("=")
mul = op(r"\*")
sub = op(r"-")
on = keyword("on")
to = keyword("to")
mid = keyword("mid")
parallel = op("//")
perpendicular = op("T")
percent = op("%")


expr_patterns = dict(
    create_line=f"{line()}",
    create_arc=f"{circle('arc')}{eq}{point('center')}\s+{point('start')}\s+{point('end')}",
    create_point=f"{point()}{eq}{pos()}",
    point_on_point=f"{point('point1')}{on}{point('point2')}",
    point_on_line=f"{point()}{on}{line()}",
    intersect_of_two_lines=f"{point()}{eq}{line('line1')}{mul}{line('line2')}",
    length_of_line=f"{line()}{eq}{number()}",
    equal_lines=f"{line('line1')}{eq}{line('line2')}",
    parallel=f"{line('line1')}{parallel}{line('line2')}",
    perpendicular=f"{line('line1')}{perpendicular}{line('line2')}",
    create_circle=f"{circle()}{eq}{point()}\s+{number()}",
    circle_radius=f"r\s+{circle()}{eq}{number()}",
    circle_diameter=f"d\s+{circle()}{eq}{number()}",
    circle_equal=f"{circle('circle1')}{eq}{circle('circle2')}",
    point_on_circle=f"{point()}{on}{circle()}",
    angle_3points_value=f"<{point('p1')}{point('p2')}{point('p3')}{eq}{number()}",
    angle_3points_3points=f"<{point('p1')}{point('p2')}{point('p3')}{eq}<{point('p4')}{point('p5')}{point('p6')}",
    angle_2lines_value=f"{line('line1')}<{line('line2')}{eq}{number()}",
    angle_2lines_2lines=f"{line('line1')}<{line('line2')}{eq}{line('line3')}<{line('line4')}",
    vertical=f"\|{line()}",
    horizontal=f"-{line()}",
    length_ratio=f"{line('line1')}{eq}{line('line2')}{mul}{number()}",
    distance_point_point=f"{point('point1')}{to}{point('point2')}{eq}{number()}",
    distance_point_line=f"{point()}{to}{line()}{eq}{number()}",
    distance_point_line_point_line=f"{point('point1')}{to}{line('line1')}{eq}{point('point2')}{to}{line('line2')}",
    tangent_line_circle=f"{point()}{eq}{line()}{percent}{circle()}",
    tangent_circle_circle=f"{point()}{eq}{circle('circle1')}{percent}{circle('circle2')}",
    # tangent_circle_arc=f"{point()}{eq}{circle()}{percent}{arc()}",
    line_middle=f"{point()}{mid}{line()}",
    line_length_diff=f"{line('line1')}{sub}{line('line2')}{eq}{number()}",
    length_eq_pt_line=f"{line('line1')}{eq}{point()}{to}{line('line2')}",
    perpendicular_point=f"{point('point1')}{eq}{point('point2')}{perpendicular}{line()}",
)


def parse_expr(expr):
    for name, pattern in expr_patterns.items():
        res = re.match(pattern + "$", expr)
        if res is not None:
            res = res.groupdict()
            res["func"] = name
            return res


def parse_value(value):
    if value.endswith("!"):
        return float(value[:-1]), True
    else:
        return float(value), False


def line_intersect(p1, p2, p3, p4):
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4
    t0 = x1 * y3
    t1 = x2 * y4
    t2 = x3 * y2
    t3 = x4 * y1
    t4 = x1 * y4
    t5 = x2 * y3
    t6 = x3 * y1
    t7 = x4 * y2
    t8 = 1 / (t0 + t1 + t2 + t3 - t4 - t5 - t6 - t7)
    return (
        t8
        * (
            t0 * x4
            + t1 * x3
            + t2 * x1
            + t3 * x2
            - t4 * x3
            - t5 * x4
            - t6 * x2
            - t7 * x1
        ),
        t8
        * (
            t0 * y2
            + t1 * y1
            + t2 * y4
            + t3 * y3
            - t4 * y2
            - t5 * y1
            - t6 * y4
            - t7 * y3
        ),
    )


def perpendicular_point(p1, p2, p3):
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    t0 = x2**2 - 2 * x2 * x3 + x3**2 + y2**2 - 2 * y2 * y3 + y3**2
    t1 = 1 / t0
    t2 = x1 * y2 - x1 * y3 - x2 * y1 + x2 * y3 + x3 * y1 - x3 * y2
    return (t1 * (t0 * x1 - t2 * (y2 - y3)), t1 * (t0 * y1 + t2 * (x2 - x3)))


def poly_area(x, y):
    return 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))


class Entity:
    def __init__(self, entity, **kw):
        self.h = entity
        for name, value in kw.items():
            setattr(self, name, value)


class Line(Entity):
    def __init__(self, entity, p1, p2):
        self.h = entity
        self.p1 = p1
        self.p2 = p2


class Circle(Entity):
    def __init__(self, entity, p, r):
        self.h = entity
        self.p = p
        self.r = r


class Arc(Entity):
    def __init__(self, entity, p, pstart, pend):
        self.h = entity
        self.p = p
        self.pstart = pstart
        self.pend = pend


class GeometrySolver:
    def __init__(self, script):
        self.sys = SolverSystem()
        self.current_group = 1
        self.sys.set_group(self.current_group)
        self.origin_point = Entity(self.sys.add_point_3d(0, 0, 0))
        qw, qx, qy, qz = make_quaternion(1, 0, 0, 0, 1, 0)
        self.normal = self.sys.add_normal_3d(qw, qx, qy, qz)
        self.plane = self.sys.add_work_plane(self.origin_point.h, self.normal)
        self.origin_point = Entity(self.sys.add_point_2d(0, 0, self.plane))
        self.sys.dragged(self.origin_point.h, self.plane)
        self.xaxis_point = Entity(self.sys.add_point_2d(1, 0, self.plane))
        self.sys.dragged(self.xaxis_point.h, self.plane)
        self.yaxis_point = Entity(self.sys.add_point_2d(0, 1, self.plane))
        self.sys.dragged(self.yaxis_point.h, self.plane)
        self.xaxis = Entity(
            self.sys.add_line_2d(self.origin_point.h, self.xaxis_point.h, self.plane),
            p1=self.origin_point,
            p2=self.xaxis_point,
        )
        self.yaxis = Entity(
            self.sys.add_line_2d(self.origin_point.h, self.yaxis_point.h, self.plane),
            p1=self.origin_point,
            p2=self.yaxis_point,
        )

        self.items = {}
        self.current_group = 2
        self.sys.set_group(self.current_group)
        for line in script.split("\n"):
            line = line.strip()
            if line.startswith("#"):
                continue
            if line.startswith("---"):
                self.current_group += 1
                self.sys.set_group(self.current_group)
                continue

            cmd = parse_expr(line)
            if cmd is not None:
                self.do(cmd)
                self.sys.solve()

    def do(self, cmd):
        func = getattr(self, cmd["func"], None)
        if func is not None:
            func(cmd)

    def create_point(self, cmd):
        x, fix_x = parse_value(cmd["x"])
        y, fix_y = parse_value(cmd["y"])
        p = self.sys.add_point_2d(x, y, self.plane)
        if fix_x and fix_y:
            self.sys.dragged(p, self.plane)
        self.items[cmd["point"]] = Entity(p)

    def create_line(self, cmd):
        self.ensure_line(cmd["line"])

    def distance_point_point(self, cmd):
        val, _ = parse_value(cmd["value"])
        p1 = self.items[cmd["point1"]]
        p2 = self.items[cmd["point2"]]
        self.sys.distance(p1.h, p2.h, val, self.plane)

    def distance_point_line(self, cmd):
        point = self.ensure_point(cmd["point"])
        line = self.ensure_line(cmd["line"])
        value, _ = parse_value(cmd["value"])
        self.sys.distance(point.h, line.h, value, self.plane)

    def distance_point_line_point_line(self, cmd):
        point1 = self.ensure_point(cmd["point1"])
        line1 = self.ensure_line(cmd["line1"])
        point2 = self.ensure_point(cmd["point2"])
        line2 = self.ensure_line(cmd["line2"])
        self.sys.equal_point_to_line(point1.h, line1.h, point2.h, line2.h, self.plane)

    def length_of_line(self, cmd):
        line = self.ensure_line(cmd["line"])
        val, _ = parse_value(cmd["value"])
        self.sys.distance(line.p1.h, line.p2.h, val, self.plane)

    def point_on_line(self, cmd):
        p = self.ensure_point(cmd["point"])
        line = self.ensure_line(cmd["line"])
        self.sys.coincident(p.h, line.h, self.plane)

    def intersect_of_two_lines(self, cmd):
        line1 = self.ensure_line(cmd["line1"])
        line2 = self.ensure_line(cmd["line2"])
        p1 = self.get_position(line1.p1)
        p2 = self.get_position(line1.p2)
        p3 = self.get_position(line2.p1)
        p4 = self.get_position(line2.p2)
        x, y = line_intersect(p1, p2, p3, p4)
        p = self.ensure_point(cmd["point"], x=x, y=y)
        self.sys.coincident(p.h, line1.h, self.plane)
        self.sys.coincident(p.h, line2.h, self.plane)

    def equal_lines(self, cmd):
        line1 = self.ensure_line(cmd["line1"])
        line2 = self.ensure_line(cmd["line2"])
        self.sys.equal(line1.h, line2.h, self.plane)

    def parallel(self, cmd):
        line1 = self.ensure_line(cmd["line1"])
        line2 = self.ensure_line(cmd["line2"])
        self.sys.parallel(line1.h, line2.h, self.plane)

    def perpendicular(self, cmd):
        line1 = self.ensure_line(cmd["line1"])
        line2 = self.ensure_line(cmd["line2"])
        self.sys.perpendicular(line1.h, line2.h, self.plane)

    def perpendicular_point(self, cmd):
        line1 = self.ensure_line(cmd["line"])
        point2 = self.items[cmd["point2"]]

        p2 = self.get_position(point2)
        p3 = self.get_position(line1.p1)
        p4 = self.get_position(line1.p2)
        x, y = perpendicular_point(p2, p3, p4)
        point1 = self.ensure_point(cmd["point1"], x=x, y=y)
        line2_name = cmd["point1"] + cmd["point2"]
        line2 = self.ensure_line(line2_name)
        self.sys.perpendicular(line1.h, line2.h, self.plane)
        self.items[line2_name] = line2
        self.sys.coincident(point1.h, line1.h, self.plane)

    def vertical(self, cmd):
        line = self.ensure_line(cmd["line"])
        self.sys.vertical(line.h, self.plane)

    def horizontal(self, cmd):
        line = self.ensure_line(cmd["line"])
        self.sys.horizontal(line.h, self.plane)

    def create_circle(self, cmd):
        point = self.ensure_point(cmd["point"])
        value, fix = parse_value(cmd["value"])
        radius = self.sys.add_distance(value, self.plane)
        circle = Circle(
            self.sys.add_circle(self.normal, point.h, radius, self.plane), point, radius
        )
        self.items[cmd["circle"]] = circle
        if fix:
            self.sys.diameter(circle.h, value * 2)

    def create_arc(self, cmd):
        center = self.items[cmd["center"]]
        start = self.items[cmd["start"]]
        end = self.items[cmd["end"]]
        arc = Arc(
            self.sys.add_arc(self.normal, center.h, start.h, end.h, self.plane),
            center,
            start,
            end,
        )
        self.items[cmd["arc"]] = arc

    def circle_equal(self, cmd):
        circle1 = self.items[cmd["circle1"]]
        circle2 = self.items[cmd["circle2"]]
        circle1.eq(circle2)

    def circle_radius(self, cmd):
        value, _ = parse_value(cmd["value"])
        circle = self.items[cmd["circle"]]
        self.sys.diameter(circle.h, value * 2)

    def circle_diameter(self, cmd):
        value, _ = parse_value(cmd["value"])
        circle = self.items[cmd["circle"]]
        self.sys.diameter(circle.h, value)

    def point_on_circle(self, cmd):
        p = self.ensure_point(cmd["point"])
        circle = self.items[cmd["circle"]]
        self.sys.coincident(p.h, circle.h)

    def angle_2lines_value(self, cmd):
        line1 = self.ensure_line(cmd["line1"])
        line2 = self.ensure_line(cmd["line2"])
        value, _ = parse_value(cmd["value"])
        self.sys.angle(line1.h, line2.h, value, self.plane)

    def angle_3points_value(self, cmd):
        p1 = cmd["p1"]
        p2 = cmd["p2"]
        p3 = cmd["p3"]
        value, _ = parse_value(cmd["value"])
        line1 = self.ensure_line(p1 + p2)
        line2 = self.ensure_line(p2 + p3)
        self.sys.angle(line1.h, line2.h, value, self.plane)

    def angle_3points_3points(self, cmd):
        p1 = cmd["p1"]
        p2 = cmd["p2"]
        p3 = cmd["p3"]
        p4 = cmd["p4"]
        p5 = cmd["p5"]
        p6 = cmd["p6"]
        line1 = self.ensure_line(p1 + p2)
        line2 = self.ensure_line(p2 + p3)
        line3 = self.ensure_line(p4 + p5)
        line4 = self.ensure_line(p5 + p6)
        self.sys.equal_angle(line1.h, line2.h, line3.h, line4.h, self.plane)

    def length_ratio(self, cmd):
        line1 = self.ensure_line(cmd["line1"])
        line2 = self.ensure_line(cmd["line2"])
        value, _ = parse_value(cmd["value"])
        self.sys.ratio(line1.h, line2.h, value, self.plane)

    def ensure_point(self, name, x=None, y=None):
        if name in self.items:
            return self.items[name]
        if x is None:
            x = random.random()
        if y is None:
            y = random.random()
        p = Entity(self.sys.add_point_2d(x, y, self.plane))
        self.items[name] = p
        return p

    def tangent_line_circle(self, cmd):
        point = self.ensure_point(cmd["point"])
        line = self.ensure_line(cmd["line"])
        circle = self.items[cmd["circle"]]
        self.sys.coincident(point.h, line.h, self.plane)
        self.sys.coincident(point.h, circle.h, self.plane)
        line2 = self.sys.add_line_2d(circle.p.h, point.h, self.plane)
        self.sys.perpendicular(line2, line.h, self.plane)

    def tangent_circle_circle(self, cmd):
        point = self.ensure_point(cmd["point"])
        circle1 = self.items[cmd["circle1"]]
        circle2 = self.items[cmd["circle2"]]
        line = self.sys.add_line_2d(circle1.p.h, circle2.p.h, self.plane)
        self.sys.coincident(point.h, line)
        self.sys.coincident(point.h, circle1.h)
        self.sys.coincident(point.h, circle2.h)

    # def tangent_circle_arc(self, cmd):
    #     point = self.ensure_point(cmd['point'])
    #     circle = self.items[cmd['circle']]
    #     arc = self.items[cmd['arc']]
    #     line =self.plane.make_line_segment(circle.center, arc.center)
    #     point.on(line)
    #     point.on(circle)
    #     point.on(arc)

    def length_eq_pt_line(self, cmd):
        line1 = self.ensure_line(cmd["line1"])
        line2 = self.ensure_line(cmd["line2"])
        point = self.ensure_point(cmd["point"])
        raise NotImplementedError()
        # self.plane.constraint_eq_len_pt_line_distance(line1, point, line2)

    def line_middle(self, cmd):
        line = self.ensure_line(cmd["line"])
        x1, y1 = self.get_position(line.p1)
        x2, y2 = self.get_position(line.p2)
        point = self.ensure_point(cmd["point"], x=(x1 + x2) * 0.5, y=(y1 + y2) * 0.5)
        self.sys.midpoint(point.h, line.h)

    def line_length_diff(self, cmd):
        line1 = self.ensure_point(cmd["line1"])
        line2 = self.ensure_point(cmd["line2"])
        value, _ = parse_value(cmd["value"])
        self.sys.length_diff(line1.h, line2.h, value, self.plane)

    def ensure_line(self, name):
        if name in self.items:
            return self.items[name]
        p1, p2 = name
        p1 = self.ensure_point(p1)
        p2 = self.ensure_point(p2)
        line = Line(self.sys.add_line_2d(p1.h, p2.h, self.plane), p1=p1, p2=p2)
        self.items[name] = line
        return line

    def show(self, notebook_handle=False):
        from bokeh.io import show

        self.fig = BokehPlot(self)
        if notebook_handle:
            self.figure_handle = show(self.fig.figure, notebook_handle=True)
        else:
            show(self.fig.figure)
            
    def update(self):
        from bokeh.io import push_notebook
        fig = BokehPlot(self, show=False)
        if self.fig.source_points is not None:
            self.fig.source_points.data = dict(fig.source_points.data)
        if self.fig.source_line is not None:
            self.fig.source_line.data = dict(fig.source_line.data)
        if self.fig.source_circle is not None:
            self.fig.source_circle.data = dict(fig.source_circle.data)
        
        push_notebook(handle=self.figure_handle)

    def get_position(self, q):
        if isinstance(q, str):
            if len(q) == 1:
                return self.sys.params(self.items[q].h.params)
            else:
                return {n: self.sys.params(self.items[n].h.params) for n in q}
        elif isinstance(q, Entity) and q.h.is_point():
            return self.sys.params(q.h.params)
        else:
            raise TypeError(f"unknown type of {q}")

    def get_param(self, p):
        return self.sys.params(p.params)[0]
    
    def set_param(self, p, params):
        self.sys.set_params(self.items[p].h.params, params)

    def get_length(self, q):
        line = self.items[q]
        if not isinstance(line, Line):
            raise ValueError(f'{q} is not a segment')
        x1, y1 = self.get_position(line.p1)
        x2, y2 = self.get_position(line.p2)
        return math.hypot(x2 - x1, y2 - y1)

    def get_area(self, q):
        x, y = zip(*[self.get_position(c) for c in q])
        return poly_area(x, y)

    def get_dist(self, p, line):
        return self.get_area(p + line) / self.get_length(line) * 2

    def get_geogebra_script(self, to_clipboard=False):
        scripts = []
        handles_to_name = {}
        for name, item in self.items.items():
            if item.h.is_point():
                x, y = self.get_position(item)
                scripts.append(f"{name} = ({x:12f}, {y:12f})")
                handles_to_name[str(item.h)] = name

        for name, item in self.items.items():
            if isinstance(item, Line):
                p1 = handles_to_name[str(item.p1.h)]
                p2 = handles_to_name[str(item.p2.h)]
                scripts.append(f"{name} = Segment({p1}, {p2})")

        for name, item in self.items.items():
            if isinstance(item, Circle):
                center = handles_to_name[str(item.p.h)]
                d = self.get_param(item.r)
                scripts.append(f"{name[1:]} = Circle({center}, {d})")

        text = "\n".join(scripts)

        if to_clipboard:
            from pandas.io.clipboard import clipboard_set

            clipboard_set(text)
        else:
            return text

    def point_data(self):
        data = {
            k: self.get_position(p) for k, p in self.items.items() if p.h.is_point()
        }
        return data

    def segment_data(self):
        data = {}
        for k, line in self.items.items():
            if isinstance(line, Line):
                p1 = self.get_position(line.p1)
                p2 = self.get_position(line.p2)
                data[k] = (p1, p2)
        return data

    def circle_data(self):
        data = {}
        for k, circle in self.items.items():
            if isinstance(circle, Circle):
                p = self.get_position(circle.p)
                r = self.get_param(circle.r)
                data[k] = (p, r)
        return data


class BokehPlot:
    def __init__(
        self,
        solver: GeometrySolver,
        point_size=5,
        point_color="#ff7f0e",
        line_width=3,
        line_color="#1f77b4",
        cline_width=1,
        cline_color="#2ca02c",
        show=True,
        **kw,
    ):
        self.point_size = point_size
        self.point_color = point_color
        self.line_width = line_width
        self.line_color = line_color
        self.cline_width = cline_width
        self.cline_color = cline_color
        self.solver = solver
        self.load_data()
        if show:
            self.create_figure()

    def load_data(self):
        from bokeh.models import ColumnDataSource

        segments = self.solver.segment_data()
        points = self.solver.point_data()
        circles = self.solver.circle_data()

        x, y = np.array(list(points.values())).T
        info = [f'({x_:6.4f}, {y_:6.4f})' for x_, y_ in zip(x, y)]
        self.source_points = ColumnDataSource(data=dict(x=x, y=y, info=info, name=list(points.keys())))

        if segments:
            p = np.array(list(segments.values()))
            x, y = np.rollaxis(p, 2)
            dx = np.diff(x, axis=1)
            dy = np.diff(y, axis=1)
            length = np.hypot(dx, dy)
            info = [f'{length_[0]:6.4f}' for length_ in length]
            self.source_line = ColumnDataSource(data=dict(xs=x.tolist(), ys=y.tolist(), info=info))
        else:
            self.source_line = None

        if circles:
            x, y = np.array([c[0] for c in circles.values()]).T
            r = np.array([c[1] for c in circles.values()])
            info = [f'({x_:6.4f}, {y_:6.4f}), {r_:6.4f}' for x_, y_, r_ in zip(x, y, r)]
            self.source_circle = ColumnDataSource(data=dict(x=x, y=y, r=r, info=info))
        else:
            self.source_circle = None


    def create_figure(self):
        from bokeh.plotting import figure
        from bokeh.models import HoverTool

        self.figure = fig = figure(
            frame_width=300, frame_height=300, match_aspect=True, aspect_scale=1
        )

        self.render_points = fig.circle(
            "x", "y", source=self.source_points, size=self.point_size, color=self.point_color
        )

        if self.source_line is not None:
            fig.multi_line(
                "xs",
                "ys",
                source=self.source_line,
                line_width=self.line_width,
                line_color=self.line_color,
            )
            
        if self.source_circle is not None:
            fig.circle(
                "x",
                "y",
                radius="r",
                source=self.source_circle,
                line_width=self.line_width,
                line_color=self.line_color,
                fill_color=None,
            )
        fig.text("x", "y", "name", source=self.source_points)

        hover = HoverTool(
            tooltips=[
                ("info", "@info"),
            ],
            line_policy="next",
        )

        fig.add_tools(hover)


from IPython.core import magic_arguments
from IPython.core.magic import register_cell_magic

'''
        magic_arguments.argument('-b', '--block', action="store_const",
            const=True, dest='block',
            help="use blocking (sync) execution",
        ),
'''

out_argument = magic_arguments.argument('-o', '--output',
            help='Specify a name for the result, default value is "g"')
handle_argument = magic_arguments.argument('-h', '--handle', action='store_const', const=True)

@register_cell_magic
@magic_arguments.magic_arguments()
@out_argument
@handle_argument
def gscript(line, cell):
    from IPython.core.interactiveshell import InteractiveShell
    sh = InteractiveShell.instance()
    args = magic_arguments.parse_argstring(gscript, line)
    name = args.output
    handle = args.handle
        
    if name is None:
        name = "g"

    import geometry_script as gs
    g = gs.GeometrySolver(cell)
    sh.user_ns[name] = g
    if handle:
        g.show(notebook_handle=True)
    else:
        g.show()

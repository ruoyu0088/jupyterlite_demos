from math import sin, cos, pi
import numpy as np
import ipycanvas
from ipycanvas import Canvas
import ipywidgets as ipw

rules = {
    "Koch": {"F": "F+F--F+F", "S": "F", "direct": 180, "angle": 60, "iter": 5},
    "Dragon": {
        "X": "X+YF+",
        "Y": "-FX-Y",
        "S": "FX",
        "direct": 0,
        "angle": 90,
        "iter": 13,
    },
    "Triangle": {
        "f": "F-f-F",
        "F": "f+F+f",
        "S": "f",
        "direct": 0,
        "angle": 60,
        "iter": 7,
    },
    "Plant": {
        "X": "F-[[X]+X]+F[+FX]-X",
        "F": "FF",
        "S": "X",
        "direct": -45,
        "angle": 25,
        "iter": 6,
    },
    "Hilbert": {
        "S": "X",
        "X": "-YF+XFX+FY-",
        "Y": "+XF-YFY-FX+",
        "direct": 0,
        "angle": 90,
        "iter": 6,
    },
    "Sierpinski": {
        "S": "L--F--L--F",
        "L": "+R-F-R+",
        "R": "-L+F+L-",
        "direct": 0,
        "angle": 45,
        "iter": 10,
    },
    "Plant2": {
        "S": "F",
        "F": "FF+[+F-F-F]-[-F+F+F]",
        "direct": 270,
        "angle": 23,
        "iter": 4,
    },
    "Plant3": {
        "S": "VZFFF",
        "V": "[+++W][---W]YV",
        "W": "+X[-W]Z",
        "X": "-W[+X]Z",
        "Y": "YZ",
        "Z": "[-FFF][+FFF]F",
        "direct": 270,
        "angle": 20,
        "iter": 9,
    },
    "Hexagonal Gosper": {
        "S": "XF",
        "X": "X+YF++YF-FX--FXFX-YF+",
        "Y": "-FX+YFYF++YF+FX--FX-Y",
        "direct": 270,
        "angle": 60,
        "iter": 5,
    },
}


def str_to_rule(s):
    rule = {}
    for row in s.split("\n"):
        row = row.strip()
        if ":" in row:
            key, val = row.split(":")
            if len(key) > 1:
                val = int(val)
            rule[key] = val
    return rule


def rule_to_str(rule):
    return "\n".join(f"{key}:{value}" for key, value in rule.items())


class L_System:
    def __init__(self, rule):
        info = bytearray(rule["S"].encode())
        replace = {
            key.encode(): val.encode() for key, val in rule.items() if len(key) == 1
        }
        for i in range(rule["iter"]):
            info2 = bytearray()
            for c in info:
                c = c.to_bytes(1, byteorder="little")
                if c in replace:
                    info2.extend(replace[c])
                else:
                    info2.extend(c)
                if len(info2) > 100000:
                    break
            info = info2
        self.rule = rule
        self.info = info

    def get_lines(self):
        d = self.rule["direct"]
        a = self.rule["angle"]
        p = (0.0, 0.0)
        l = 1.0
        lines = []
        stack = []
        for c in self.info:
            if c in b"Ff":
                r = d * pi / 180
                t = p[0] + l * cos(r), p[1] + l * sin(r)
                lines.append(((p[0], p[1]), (t[0], t[1])))
                p = t
            elif c in b"+":
                d += a
            elif c in b"-":
                d -= a
            elif c in b"[":
                stack.append((p, d))
            elif c in b"]":
                p, d = stack[-1]
                del stack[-1]
        return np.asarray(lines)


class LSystemGUI:
    def __init__(self, size=500):
        self.size = size
        self.canvas = Canvas(
            width=self.size,
            height=self.size,
            layout=ipw.Layout(width=f"{size}px", height=f"{size}px"),
        )
        titles = list(rules.keys())
        self.rule_selector = ipw.Dropdown(
            options=titles, value=titles[0], layout=ipw.Layout(width="200px")
        )
        self.rule_selector.observe(self.on_rule_changed, names="value")
        self.rule_input = ipw.Textarea(
            value=rule_to_str(rules[titles[0]]),
            layout=ipw.Layout(height="200px", width="200px"),
        )
        self.plot_button = ipw.Button(description="plot")
        self.plot_button.on_click(self.plot)
        self.layout = ipw.HBox(
            [
                ipw.VBox([self.rule_selector, self.rule_input, self.plot_button]),
                self.canvas,
            ]
        )

    def on_rule_changed(self, event):
        self.rule_input.value = rule_to_str(rules[self.rule_selector.value])

    def plot(self, b):
        rule = str_to_rule(self.rule_input.value)
        lines = L_System(rule).get_lines()
        self.lines = lines
        size = self.size
        x, y = lines.T

        xmin, xmax = x.min(), x.max()
        xc = (xmin + xmax) * 0.5
        ymin, ymax = y.min(), y.max()
        yc = (ymin + ymax) * 0.5

        xspan = xmax - xmin
        yspan = ymax - ymin
        span = max(xspan, yspan) * 1.1

        x2 = (x - xc) / span * size + size * 0.5
        y2 = (y - yc) / span * size + size * 0.5
        lines2 = np.dstack((x2, y2))
        with ipycanvas.hold_canvas(self.canvas):
            self.canvas.clear()
            self.canvas.stroke_line_segments(lines2)

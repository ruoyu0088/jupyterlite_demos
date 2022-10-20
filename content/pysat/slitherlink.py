import re
import itertools
from collections import defaultdict
import numpy as np
from pysat.solvers import Solver
import ipycanvas
from ipycanvas import Canvas
import ipywidgets as ipw
import bs4


def parse_board(html):
    soup = bs4.BeautifulSoup(html, 'html.parser')
    board = []
    last_height = None
    for div in soup.find_all('div', class_='loop-task-cell'):
        height = int(re.search(r'top: (\d+)px', div.attrs['style']).group(1))
        if height != last_height:
            board.append([])
            last_height = height
        text = div.text
        if not text:
            text = '.'
        board[-1].append(text)
    board = '\n'.join(''.join(row) for row in board)
    return board


class VariableGenerator:
    def __init__(self):
        self.current = 1

    def __next__(self):
        v = self.current
        self.current += 1
        return v

    def get_variables(self, n):
        n = int(n)
        variables = list(range(self.current, self.current + n))
        self.current += n
        return variables


def dnf_to_cnf(dnf, new_vars):
    zlist = []
    cnf = []
    for term in dnf:
        z = next(new_vars)
        zlist.append(z)
        cnf.append([z] + [-v for v in term])
        for v in term:
            cnf.append([-z, v])
    cnf.append(zlist)
    return cnf


def equals_to(variables, counts, new_vars):
    dnfs = []
    variables = [int(v) for v in variables]
    index = list(range(len(variables)))
    for c in counts:
        for plus_index in itertools.combinations(index, c):
            dnf = [-v for v in variables]
            for i in plus_index:
                dnf[i] *= -1
            dnfs.append(dnf)
    return dnf_to_cnf(dnfs, new_vars)


class SlitherLinkSolver:
    result: list[int]

    def __init__(self, board_str):
        self.board = board = np.array([list(row) for row in board_str.strip().split("\n")])
        h, w = [t + 1 for t in board.shape]
        self.w = w
        self.h = h

        directs = [(-1, 0), (0, 1), (1, 0), (0, -1)]
        edge_locations = set(itertools.product(range(h), range(w)))
        self.edge_locations_sorted = edge_locations_sorted = sorted(edge_locations)

        block_locations = set(itertools.product(range(h - 1), range(w - 1)))
        block_locations_sorted = sorted(block_locations)

        vg = VariableGenerator()

        self.edges = {}
        for y, x in edge_locations_sorted:
            for dy, dx in directs:
                if dy >= 0 and dx >= 0:
                    y2, x2 = y + dy, x + dx
                    if (y2, x2) in edge_locations:
                        self.edges[y, x, y2, x2] = next(vg)

        self.dot_links = defaultdict(list)

        for y, x in edge_locations_sorted:
            for dy, dx in directs:
                y2, x2 = y + dy, x + dx
                key1 = y, x, y2, x2
                key2 = y2, x2, y, x
                if key1 in self.edges:
                    self.dot_links[y, x].append(self.edges[key1])
                if key2 in self.edges:
                    self.dot_links[y, x].append(self.edges[key2])

        self.block_links = defaultdict(list)
        for y, x in block_locations_sorted:
            self.block_links[y, x].extend(
                [
                    self.edges[y, x, y, x + 1],
                    self.edges[y, x, y + 1, x],
                    self.edges[y + 1, x, y + 1, x + 1],
                    self.edges[y, x + 1, y + 1, x + 1],
                ]
            )

        cnfs = []
        for links in self.dot_links.values():
            cnfs.extend(equals_to(links, [0, 2], vg))

        for key, val in self.block_links.items():
            c = board[key]
            if c != ".":
                cnfs.extend(equals_to(val, [int(c)], vg))

        self.solver = Solver()
        self.solver.append_formula(cnfs)

    def solve(self):
        def pop_path(edges, start):
            path = [start]
            while True:
                if start not in edges:
                    break
                next_ = edges[start].pop()
                if not edges[start]:
                    del edges[start]
                if next_ in edges:
                    if start in edges[next_]:
                        edges[next_].remove(start)
                        if not edges[next_]:
                            del edges[next_]
                start = next_
                path.append(start)
            return path

        m = []
        for i in range(100):
            self.solver.solve()
            m = self.solver.get_model()
            if m is None:
                m = []
            neighbours = defaultdict(set)

            for (y1, x1, y2, x2), v in self.edges.items():
                if m[v - 1] > 0:
                    neighbours[y1, x1].add((y2, x2))
                    neighbours[y2, x2].add((y1, x1))

            pathes = []

            while neighbours:
                start = list(neighbours.keys())[0]
                path = pop_path(neighbours, start)
                pathes.append(path)

            if len(pathes) == 1:
                break

            pathes = sorted(pathes, key=len)

            path = pathes[0]
            variables = []
            for (y1, x1), (y2, x2) in zip(path[:-1], path[1:]):
                keys = [(y1, x1, y2, x2), (y2, x2, y1, x1)]
                for key in keys:
                    if key in self.edges:
                        variables.append(self.edges[key])

            self.solver.append_formula([[-v for v in variables]])

        self.result = m
        return m


class SlitherLinkSGUI:
    def __init__(self):
        self.size = 18
        w = h = 10
        width = w * self.size + 4
        height = h * self.size + 4
        self.canvas = Canvas(width=width, height=height)
        self.html_textarea = ipw.Textarea('', layout=ipw.Layout(width='300px', height='300px'))
        self.solve_button = ipw.Button(description='Solve')
        self.solve_button.on_click(self.solve)
        self.layout = ipw.HBox([
            ipw.VBox([self.html_textarea, self.solve_button]), self.canvas])

    def solve(self, b):
        html = self.html_textarea.value
        if 'div' in html:
            board = parse_board(html)
        else:
            board = html
        solver = SlitherLinkSolver(board)
        self.result = solver.solve()
        w = solver.w
        h = solver.h
        width = w * self.size + 4
        height = h * self.size + 4
        self.canvas.width = width
        self.canvas.height = height
        self.canvas.layout = ipw.Layout(width=f'{width}px', height=f'{height}px')
        self.solver = solver
        self.draw()

    def draw(self):
        canvas = self.canvas
        size = self.size

        with ipycanvas.hold_canvas(canvas):
            canvas.clear()
            canvas.text_align = "center"
            canvas.text_baseline = "middle"
            canvas.stroke_style = "#000000"
            canvas.fill_style = "#000000"

            if self.result:
                for (y1, x1, y2, x2), v in self.solver.edges.items():
                    if self.result[v - 1] > 0:
                        canvas.stroke_line(x1 * size + 2, y1 * size + 2, x2 * size + 2, y2 * size + 2)

            canvas.fill_style = "#007700"
            for y, x in self.solver.edge_locations_sorted:
                canvas.fill_circle(x * size + 2, y * size + 2, 2)

            canvas.fill_style = "#000000"
            for y, x in self.solver.block_links:
                c = self.solver.board[y, x]
                if c != ".":
                    canvas.fill_text(c, x * size + 2 + size // 2, y * size + 2 + size // 2)
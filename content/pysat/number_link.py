from typing import Tuple
import numpy as np
from itertools import product, combinations
from collections import defaultdict
from pysat.solvers import Solver
import ipycanvas
from ipycanvas import Canvas
from ipyevents import Event


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


def exact_one(variables):
    variables = [int(v) for v in variables]
    cnf = [variables]
    for v1, v2 in combinations(variables, 2):
        cnf.append([-v1, -v2])
    return cnf


def atmost_one(variables):
    variables = [int(v) for v in variables]
    cnf = []
    for v1, v2 in combinations(variables, 2):
        cnf.append([-v1, -v2])
    return cnf


def equals_to(variables, counts, new_vars):
    dnfs = []
    variables = [int(v) for v in variables]
    index = list(range(len(variables)))
    for c in counts:
        for plus_index in combinations(index, c):
            dnf = [-v for v in variables]
            for i in plus_index:
                dnf[i] *= -1
            dnfs.append(dnf)
    return dnf_to_cnf(dnfs, new_vars)


def exact_n(variables, n):
    cnf = []
    variables = [int(v) for v in variables]
    for c in combinations(variables, n + 1):
        cnf.append([-v for v in c])

    for c in combinations(variables, len(variables) - n + 1):
        cnf.append([v for v in c])
    return cnf


def str_to_board(board_str):
    board = np.array([list(row) for row in board_str.strip().split()]).astype(int)
    return board.tolist()


class NumberLinkSolver:
    segments: list[tuple[int]]

    def __init__(self, board_: list[list[int]], max_retry=100):
        self.board = board = np.asarray(board_)
        self.max_retry = max_retry
        height, width = board.shape
        number_count = np.max(board)

        vg = VariableGenerator()
        cell_variables = np.asarray(vg.get_variables(width * height * number_count)).reshape(
            height, width, number_count
        )
        self.link_variables = link_variables = {}
        for x, y in product(range(width), range(height)):
            x2, y2 = x + 1, y
            x3, y3 = x, y + 1
            if x2 < width:
                v = next(vg)
                link_variables[v] = x, y, x2, y2
            if y3 < height:
                v = next(vg)
                link_variables[v] = x, y, x3, y3

        self.link_variables_r = {v: k for k, v in self.link_variables.items()}

        cell_links = defaultdict(list)
        for v, (x0, y0, x1, y1) in link_variables.items():
            cell_links[x0, y0].append(v)
            cell_links[x1, y1].append(v)

        cnfs = []
        # 一つのセルは一つの数字
        for row in cell_variables.reshape(-1, number_count):
            cnfs.extend(atmost_one(row.tolist()))

        # 数字固定のセル
        for y, x in zip(*np.where(board > 0)):
            number = board[y, x]
            cnfs.append([int(cell_variables[y, x, number - 1])])

        # 数字なしのセルは二つのリンク(あるいはリンクなし)、数字ありのセルは一つのリンク
        for (x, y), variables in cell_links.items():
            if board[y, x] == 0:
                cnf = exact_n(variables, 2)
                # cnf = equals_to(variables, [0, 2], vg)
            else:
                cnf = exact_n(variables, 1)
            cnfs.extend(cnf)

        # リンク両端の数字は同じ
        for var_link, (x1, y1, x2, y2) in link_variables.items():
            var_link = int(var_link)
            vars_cell1 = cell_variables[y1, x1].tolist()
            vars_cell2 = cell_variables[y2, x2].tolist()
            for c1, c2 in zip(vars_cell1, vars_cell2):
                cnfs.append([-var_link, c1, -c2])
                cnfs.append([-var_link, -c1, c2])

        self.solver = solver = Solver()
        solver.append_formula(cnfs)
        self.solve()

    def solve(self):
        for i in range(self.max_retry):
            self.segments = self.get_segments()
            loop_pathes = self.find_loops()
            if len(loop_pathes) == 0:
                break
            for path in loop_pathes:
                variables = self.get_path_variables(path)
                self.solver.append_formula([[-v for v in variables]])

        self.retry_count = i

    def get_segments(self):
        self.solver.solve()
        m = self.solver.get_model()
        if m is not None:
            segments = []
            for k, segment in self.link_variables.items():
                if m[k - 1] > 0:
                    segments.append(segment)
            return segments
        else:
            return []

    def find_loops(self):
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

        y, x = np.where(self.board)
        n = self.board[y, x]
        idx = np.argsort(n)
        x = x[idx][::2]
        y = y[idx][::2]
        edges = defaultdict(set)

        for x1, y1, x2, y2 in self.segments:
            edges[x1, y1].add((x2, y2))
            edges[x2, y2].add((x1, y1))

        for start in zip(x, y):
            pop_path(edges, start)

        pathes = []
        while edges:
            start = list(edges.keys())[0]
            path = pop_path(edges, start)
            pathes.append(path)
        return pathes

    def get_path_variables(self, path):
        variables = []
        for s, e in zip(path[:-1], path[1:]):
            keys = [s + e, e + s]
            for k in keys:
                if k in self.link_variables_r:
                    variables.append(self.link_variables_r[k])
        return variables


class NumberLinkGUI:
    board: list[list[int]]

    def __init__(self, board=None, width=10, height=10, step=25):
        self.step = step
        if board is not None:
            if isinstance(board, str):
                self.board = str_to_board(board)
            else:
                self.board = board
        else:
            self.board = [[0] * width for _ in range(height)]
        self.width = len(self.board[0])
        self.height = len(self.board)
        self.canvas = Canvas(width=self.width * step + 2, height=self.height * step + 2)
        self.event = Event(source=self.canvas, watched_events=["keydown"])
        self.event.on_dom_event(self.handle_event)
        self.x = 0
        self.y = 0
        self.segments = None
        self.new_value_flag = True
        self.draw()

    def handle_event(self, event):
        key = event["key"]
        if key == "ArrowDown":
            self.y = min(self.y + 1, self.height - 1)
            self.new_value_flag = True
            self.draw()
        elif key == "ArrowUp":
            self.y = max(self.y - 1, 0)
            self.new_value_flag = True
            self.draw()
        elif key == "ArrowLeft":
            self.x = max(self.x - 1, 0)
            self.new_value_flag = True
            self.draw()
        elif key == "ArrowRight":
            self.x = min(self.x + 1, self.width - 1)
            self.new_value_flag = True
            self.draw()
        elif "0" <= key <= "9":
            if self.new_value_flag:
                self.board[self.y][self.x] = 0
                self.new_value_flag = False
            self.board[self.y][self.x] = self.board[self.y][self.x] * 10 + int(key)
            self.draw()
        elif key == "Escape":
            self.new_value_flag = True
            self.board[self.y][self.x] = 0
            self.draw()
        elif key == " ":
            self.solve()

    def solve(self):
        self.solver = NumberLinkSolver(self.board)
        segments_ = self.solver.segments
        if segments_:
            x1, y1, x2, y2 = np.array(segments_).T
            segments = np.c_[x1, y1, x2, y2].reshape(-1, 2, 2)
            self.segments = segments * self.step + self.step // 2 + 1
            self.draw()

    def draw(self):
        canvas = self.canvas
        step = self.step
        height, width = self.height, self.width
        with ipycanvas.hold_canvas(canvas):
            canvas.clear()
            canvas.stroke_style = "#cccccc"
            canvas.line_width = 1

            for i in range(width + 1):
                x = i * step + 1
                canvas.stroke_line(x, 1, x, height * step + 1)
            for i in range(height + 1):
                y = i * step + 1
                canvas.stroke_line(1, y, width * step + 1, y)

            canvas.fill_style = "#ffdddd"
            canvas.fill_rect(1 + self.x * step, 1 + self.y * step, step, step)

            if self.segments is not None:
                canvas.line_width = 2
                canvas.stroke_style = "#77ff77"
                canvas.stroke_line_segments(self.segments)

            canvas.text_align = "center"
            canvas.text_baseline = "middle"
            canvas.fill_style = "#000000"
            for (y, x), n in np.ndenumerate(np.asarray(self.board)):
                if n != 0:
                    canvas.fill_text(str(n), 1 + x * step + 0.5 * step, 1 + y * step + 0.5 * step)

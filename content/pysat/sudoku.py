from ipyevents import Event
import numpy as np
from itertools import combinations
from pysat.solvers import Solver
import ipycanvas
from ipycanvas import Canvas

def get_conditions(bools):
    conditions = []
    n = bools.shape[-1]
    index = np.array(list(combinations(range(n), 2)))
    conditions.extend(bools.reshape(-1, n).tolist())
    conditions.extend((-bools[..., index].reshape(-1, 2)).tolist())
    return conditions

def format_solution(solution):
    solution = np.array(solution).reshape(9, 9, 9)
    return (np.where(solution > 0)[2] + 1).reshape(9, 9)

class SudokuSolver:
    def __init__(self):
        self.bools = np.arange(1, 9 * 9 * 9 + 1).reshape(9, 9, 9)
        c1 = get_conditions(self.bools)
        c2 = get_conditions(np.swapaxes(self.bools, 1, 2))
        c3 = get_conditions(np.swapaxes(self.bools, 0, 2))

        tmp = np.swapaxes(self.bools.reshape(3, 3, 3, 3, 9), 1, 2).reshape(9, 9, 9)
        c4 = get_conditions(np.swapaxes(tmp, 1, 2))
        self.conditions = c1 + c2 + c3 + c4        
        self.solver = Solver()
        self.solver.append_formula(self.conditions)

    def solve(self, board):
        sudoku = np.array([[int(x) for x in line] for line in board])
        r, c = np.where(sudoku != 0)
        v = sudoku[r, c] - 1
        conditions2 = self.bools[r, c, v][:, None].tolist()
        self.solver.solve(assumptions=self.bools[r, c, v].tolist())
        solution = format_solution(self.solver.get_model())
        return solution.astype('str').tolist()



class SudokuCanvas:
    def __init__(self, size=400, margin=10, n=9, text_size=24):       
        self.n = 9
        self.size = size
        self.text_size = text_size
        self.margin = margin
        self.canvas = Canvas(width=size, height=size)
        self.step = (size - 2 * margin) // n
        self.w = self.step * n

        self.event = Event(source=self.canvas, watched_events=['keydown'])
        self.event.on_dom_event(self.handle_event)
        
        self.x = 0
        self.y = 0
        self.board = [['0'] * self.n for _ in range(self.n)]
        self.solver = SudokuSolver()
        self.solution = self.solver.solve(self.board)
        self.draw()
        
    def __setitem__(self, index, value):
        y, x = index
        self.board[y][x] = value
        
    def __getitem__(self, index):
        y, x = index
        return self.board[y][x]

    def handle_event(self, event):
        global e
        e = event
        key = event['key']
        if key == 'ArrowUp':
            self.y = max(0, self.y - 1)
        elif key == 'ArrowDown':
            self.y = min(self.n - 1, self.y + 1)
        elif key == 'ArrowLeft':
            self.x = max(0, self.x - 1)
        elif key == 'ArrowRight':
            self.x = min(self.n - 1, self.x + 1)
        elif '0' <= key <='9':
            self[self.y, self.x] = key
            self.solution = self.solver.solve(self.board)
        self.draw() 
        
    def draw(self):
        canvas = self.canvas
        with ipycanvas.hold_canvas(canvas):
            canvas.clear()
            canvas.stroke_style = "black"
            canvas.text_align = "center"
            canvas.text_baseline = "middle"
            canvas.font = f'{self.text_size}px monospace'
            margin = self.margin
            size = self.size
            step = self.step
            w = self.w
            canvas.fill_style = '#dddddd'
            canvas.fill_rect(margin + self.x * step, margin + self.y * step, step, step)
            canvas.fill_style = 'black'
            for i, v in enumerate(range(margin, size - margin, step)):
                if i % 3 == 0:
                    canvas.line_width = 3
                else:
                    canvas.line_width = 1
                canvas.stroke_line(margin, v, margin + w, v)
                canvas.stroke_line(v, margin, v, margin + w)

            for i in range(self.n):
                for j in range(self.n):
                    c = self[i, j]
                    x = margin + j * step + step // 2
                    y = margin + i * step + step // 2
                    if c != '0':
                        canvas.fill_style = "black"
                        canvas.fill_text(c, x, y)
                    else:
                        c = self.solution[i][j]
                        canvas.fill_style = "#bbbbbb"
                        canvas.fill_text(c, x, y)
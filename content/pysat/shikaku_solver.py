import pysat
import numpy as np
from itertools import product, combinations
from collections import defaultdict
from pysat.solvers import Solver
import ipycanvas
from ipycanvas import Canvas
from ipyevents import Event
from bs4 import BeautifulSoup
from sathelp import SATHelper

def load_board_from_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    cells = soup.find_all('div', class_='cell')
    board = []
    last_top = ''
    for cell in cells:
        style = dict([[s.strip() for s in item.split(':')] for item in cell.attrs['style'].split(';') if item])
        top = style['top']
        if last_top != top:
            board.append([])
            last_top = top
        number = cell.text
        if not number:
            number = 0
        else:
            number = int(number)
        board[-1].append(number)
    return board

def mult_pair(n):
    for i in range(1, n+1):
        j = n // i
        if i * j == n:
            yield (i, j)
            
def generate_rectangle(x, y, area, width, height):
    for w, h in mult_pair(area):
        for i, j in product(range(w), range(h)):
            x2 = x - i
            y2 = y - j
            if x2 >= 0 and y2 >= 0 and x2 + w <= width and y2 + h <= height:
                yield(x2, y2, w, h)
                
def generate_cell(rect):
    x, y, w, h = rect
    for i, j in product(range(w), range(h)):
        yield (x + i, y + j)

def str_to_board(board_str):
    board = np.array([list(row) for row in board_str.strip().split()]).astype(int)    
    return board.tolist()


class ShikakuSolver:
    def __init__(self, board):
        if isinstance(board, str):
            board = str_to_board(board)
        elif isinstance(board, list):
            board = np.array(board)
            
        height, width = board.shape

        sat = SATHelper()
        rect_variables = {}
        for y, x in zip(*np.where(board > 0)):
            v = board[y, x]
            number_rects = {}
            for rect in generate_rectangle(x, y, v, width, height):
                number_rects[sat.next()] = rect
            rect_variables[x, y] = number_rects

        cells = defaultdict(set)
        for (x0, y0), number_rects in rect_variables.items():
            for v, rect in number_rects.items():
                for xc, yc in generate_cell(rect):
                    cells[xc, yc].add((x0, y0))

        cell_variables = {}
        for key, value in cells.items():
            cell_variables[key] = dict(zip(value, sat.next(len(value))))

        self.rect_variables = rect_variables
        self.cell_variables = cell_variables
        self.sat = sat
        self.board = board

    def solve(self):
        sat = self.sat
        rect_variables = self.rect_variables
        cell_variables = self.cell_variables
        
        for value in rect_variables.values():
            sat.exact_n(value.keys(), 1)

        for value in cell_variables.values():
            sat.exact_n(value.values(), 1)

        for pos, rects in rect_variables.items():
            dnf = []   
            for var_rect, rect in rects.items():
                var_cells = [cell_variables[xc, yc][pos] for xc, yc in generate_cell(rect)]
                dnf.append([var_rect] + var_cells)
            sat.dnf_to_cnf(dnf)

        sol = sat.solve()
        if sol is not None:
            sol_rects = []
            for pos, rects in rect_variables.items():
                for var_rect, rect in rects.items():
                    if sol[var_rect - 1] > 0:
                        sol_rects.append(rect)    
            self.sol_rects = sol_rects
            return sol_rects
        else:
            return []
    
    def plot(self):
        x0, y0, w, h = np.array(self.sol_rects).T
        x1 = x0 + w
        y1 = y0 + h
        board = self.board
        height, width = board.shape
        
        Y, X = np.where(board > 0)
        V = board[Y, X]

        return hv.Rectangles((x0, height - y0, x1, height - y1)) * hv.Labels((X + 0.5, height - Y - 0.5, V))
    

class ShikakuGUI:
    def __init__(self, board=None, width=10, height=10, step=20):
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
        self.event = Event(source=self.canvas, watched_events=['keydown'])
        self.event.on_dom_event(self.handle_event)        
        self.x = 0
        self.y = 0
        self.rects = []
        self.new_value_flag = True
        self.draw()
        
    def handle_event(self, event):
        key = event['key']
        if key == 'ArrowDown':
            self.y = min(self.y + 1, self.height - 1)
            self.new_value_flag = True
            self.draw()
        elif key == 'ArrowUp':
            self.y = max(self.y - 1, 0)
            self.new_value_flag = True
            self.draw()        
        elif key == 'ArrowLeft':
            self.x = max(self.x - 1, 0)
            self.new_value_flag = True
            self.draw()
        elif key == 'ArrowRight':
            self.x = min(self.x + 1, self.width - 1)
            self.new_value_flag = True
            self.draw()
        elif '0' <= key <= '9':
            if self.new_value_flag:
                self.board[self.y][self.x] = 0
                self.new_value_flag = False
            self.board[self.y][self.x] = self.board[self.y][self.x] * 10 + int(key)
            self.draw()
        elif key == 'Escape':
            self.new_value_flag = True
            self.board[self.y][self.x] = 0
            self.draw()
        elif key == ' ':
            self.solve()
            
    def solve(self):
        solver = ShikakuSolver(self.board)
        self.rects = solver.solve()
        self.draw()        
        
    def draw(self):
        canvas = self.canvas
        step = self.step
        height, width = self.height, self.width
        with ipycanvas.hold_canvas(canvas):
            canvas.clear()
            canvas.stroke_style = '#cccccc'
            
            for i in range(width + 1):
                x = i * step + 1
                canvas.stroke_line(x, 1, x, height*step+1)
            for i in range(height + 1):
                y = i * step + 1
                canvas.stroke_line(1, y, width*step+1, y)
                   
            canvas.stroke_style = '#000000'
            canvas.fill_style = '#eeeeee'
            for rect in self.rects:
                x, y, w, h = map(int, rect)
                canvas.stroke_rect(1.5 + x * step, 1.5 + y * step, w * step - 1, h * step - 1)
                canvas.fill_rect(1.5 + x * step, 1.5 + y * step, w * step - 1, h * step - 1)
                
            canvas.fill_style = '#ffdddd'
            canvas.fill_rect(1 + self.x * step, 1 + self.y * step, step, step)
                
            canvas.text_align = 'center'
            canvas.text_baseline = 'middle'
            canvas.fill_style = '#000000'
            for (y, x), n in np.ndenumerate(self.board):
                if n != 0:
                    canvas.fill_text(str(n), 1 + x * step + 0.5 * step, 1 + y * step + 0.5 * step)
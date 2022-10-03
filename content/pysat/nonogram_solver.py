from bs4 import BeautifulSoup
import itertools
from itertools import count
import numpy as np
from pysat.solvers import Solver
import ipycanvas
from ipycanvas import Canvas
import ipywidgets as ipw


def read_table_content(table):
    data = []
    rows = table.find_all('tr')
    for row in rows:
        cols = row.find_all('td')
        cols = [ele.text.strip() for ele in cols]
        data.append([ele for ele in cols]) 
    return data

def dnf_to_cnf(dnf, new_vars=None):
    if new_vars is None:
        start = max(max(map(abs, term)) for term in dnf) + 1
        new_vars = iter(range(start, start + len(dnf)))
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


def start_pos(numbers, count):
    s = 0
    for i, n in enumerate(numbers):
        yield s
        s += n + 1

def end_pos(numbers, count):
    width = sum(numbers) + len(numbers) - 1
    start = count - width
    for pos in start_pos(numbers, count):
        yield start + pos
        
def create_position_variables(numbers, count, new_bool_variables):
    pos_variables = []
    for i, (a, b) in enumerate(zip(start_pos(numbers, count), end_pos(numbers, count))):
        pos_variables.append({j:next(new_bool_variables) for j in range(a, b + 1)})
    return pos_variables


def only_one_true(variables):
    yield list(variables)
    for i, j in itertools.combinations(variables, 2):
        yield [-i, -j]
        
def pairwise(iterable):
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)        

def position_variables_constraint(pos_variables, numbers):
    cnf = []
    # 每个数字对应的位置变量中只能有一个为真
    for i, pos_var in enumerate(pos_variables):
        cnf.extend(only_one_true(pos_var.values()))

    # 两个连续的数字num1, num2的位置pos1, pos2必须满足pos2 > pos1 + num1
    for i, (pos_var1, pos_var2) in enumerate(pairwise(pos_variables)):
        width = numbers[i] + 1
        for pos1, pos2 in itertools.product(pos_var1, pos_var2):
            if pos2 < pos1 + width:
                cnf.append([-pos_var1[pos1], -pos_var2[pos2]])
    return cnf

def cell_variables_constraint(pos_variables, cell_variables, numbers, count):
    cnf = []
    # cell[j] == 1 for all pos[i] <= j < pos[i] + num[i]
    for i, pos_var in enumerate(pos_variables):
        for pos, var in pos_var.items():
            for j in range(numbers[i]):
                cnf.append([-var, cell_variables[pos + j]])

    # cell[j] == 0, for all j < pos[0]
    for pos, var in pos_variables[0].items():
        for j in range(0, pos):
            cnf.append([-var, -cell_variables[j]])

    # cell[j] == 0, for all j >= pos[-1] + num[-1]
    for pos, var in pos_variables[-1].items():
        for j in range(pos + numbers[-1], count):
            cnf.append([-var, -cell_variables[j]])

    # cell[j] == 0 for all pos[i] + num[i] <= j < pos[i+1]
    for i, (pos_var1, pos_var2) in enumerate(pairwise(pos_variables)):
        for pos1, pos2 in itertools.product(pos_var1, pos_var2):
            if pos2 > pos1 + numbers[i]:
                for j in range(pos1 + numbers[i], pos2):
                    cnf.append([-pos_var1[pos1], -pos_var2[pos2], -cell_variables[j]])
    return cnf


class NonogramSolver:
    def __init__(self, rows, cols, width=None, height=None):
        if width is None:
            width = len(cols)
        if height is None:
            height = len(rows)
        self.rows = rows
        self.cols = cols
        self.width = width
        self.height = height
        self.var_count = self.width * self.height
        self.vars = np.arange(1, self.var_count + 1).reshape(-1, self.width)
        self.new_vars = itertools.count(self.var_count + 2)
            
    def add_constraints(self, numbers, count, cell_variables):
        pos_variables = create_position_variables(numbers, count, self.new_vars)
        self.cnf.extend(position_variables_constraint(pos_variables, numbers))
        self.cnf.extend(cell_variables_constraint(pos_variables, cell_variables, numbers, count))       
        
    def solve(self):
        self.cnf = []
        self.solution = None
        try:
            for i, row in enumerate(self.rows):
                self.add_constraints(row, self.width, self.vars[i, :].tolist())
                
            for j, col in enumerate(self.cols):
                self.add_constraints(col, self.height, self.vars[:, j].tolist())
        except:
            return

        sat = Solver()
        sat.append_formula(self.cnf)
        sat.solve()
        res = sat.get_model()
        self.solution = np.array(res[:self.var_count]).reshape(self.height, -1)
        self.solution[self.solution == -1] = 0 

class NonogramGui:
    def __init__(self):
        with open('nonogram_59721.txt') as f:
            sample_html = f.read()
        self.text_area = ipw.Textarea(value=sample_html)
        self.clear_button = ipw.Button(description='Clear')
        self.solve_button = ipw.Button(description='Solve')
        self.solve_button.on_click(self.solve)
        self.clear_button.on_click(self.clear)
        self.canvas = Canvas(width=100, height=100, layout=ipw.Layout(width='100px', height='100px'))
        self.layout = ipw.VBox([self.text_area, ipw.HBox([self.clear_button, self.solve_button]), self.canvas])
        
    def clear(self, b):
        self.text_area.value = ''
        
    def solve(self, b):
        html = self.text_area.value
        soup = BeautifulSoup(html, 'html.parser')
        table_top = soup.find(class_='nmtt')
        table_left = soup.find(class_='nmtl')
        cols = [[int(v) for v in line if v] for line in zip(*read_table_content(table_top))]
        rows = [[int(v) for v in line if v] for line in read_table_content(table_left)]
        self.solver = NonogramSolver(rows, cols)
        self.solver.solve()
        self.draw()
        
    def draw(self):
        solver = self.solver
        margin = 10
        step = 12
        top_rows = max(len(line) for line in solver.cols)
        left_cols = max(len(line) for line in solver.rows)

        width = 2 * margin + step * (solver.width + left_cols)
        height = 2 * margin + step * (solver.height + top_rows)
        canvas = self.canvas
        canvas.width = width
        canvas.height = height
        canvas.layout = ipw.Layout(width=f'{width}px', height=f'{height}px')
        canvas.clear()

        canvas.text_align = 'center'
        canvas.text_baseline = 'middle'

        with ipycanvas.hold_canvas(canvas):        
            for i, line in enumerate(solver.cols):
                for j, n in enumerate(line):
                    x = margin + (i + left_cols) * step + step // 2
                    y = margin + (j + top_rows - len(line)) * step + step // 2
                    canvas.fill_text(str(n), x, y)

            for i, line in enumerate(solver.rows):
                for j, n in enumerate(line):
                    x = margin + (j + left_cols - len(line)) * step + step // 2
                    y = margin + (i + top_rows) * step + step // 2
                    canvas.fill_text(str(n), x, y)

            for (i, j), v in np.ndenumerate((solver.solution > 0).astype(int)):
                i += top_rows
                j += left_cols
                y = margin + i * step
                x = margin + j * step
                canvas.stroke_rect(x+0.5, y+0.5, step-1, step-1)
                if v:
                    canvas.fill_style = '#777777'
                    canvas.fill_rect(x+0.5, y+0.5, step-1, step-1)
                

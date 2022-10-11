import asyncio
from collections import deque
from itertools import chain
import ipywidgets as ipw
import ipycanvas
from ipycanvas import Canvas
from ipyevents import Event
from dataclasses import dataclass
from klotski_solver import find_path

SPEED = 5

W, H = 4, 5

BLOCKS = {
    "A": (0, 1, W, W+1),
    "B": (0, W),
    "C": (0, 1),
    "D": (0,)
}

SIZES = {
    "A": (2, 2),
    "B": (2, 1),
    "C": (1, 2),
    "D": (1, 1)
}

COLORS = ('#1f77b4',
 '#aec7e8',
 '#ff7f0e',
 '#ffbb78',
 '#2ca02c',
 '#98df8a',
 '#d62728',
 '#ff9896',
 '#9467bd',
 '#c5b0d5',
 '#8c564b',
 '#c49c94',
 '#e377c2',
 '#f7b6d2',
 '#7f7f7f',
 '#c7c7c7',
 '#bcbd22',
 '#dbdb8d',
 '#17becf',
 '#9edae5')

def status2positions(status):
    status = list(status)
    positions = []
    spaces = []
    for r in range(H):
        for c in range(W):
            idx = r * W + c
            block_type = status[idx]
            if block_type in BLOCKS:
                positions.append((block_type, r, c))
                for delta in BLOCKS[block_type]:
                    status[idx + delta] = ""
            elif block_type == " ":
                spaces.append((r, c))
    return positions, spaces


def interpolate_position(from_pos, to_pos, count):
    from_row, from_col = from_pos
    to_row, to_col = to_pos

    for i in range(count):
        k = float(i) / (count - 1)
        yield from_row * (1 - k) + to_row * k, from_col * (1 - k) + to_col * k

@dataclass
class Rectangle:
    color: str
    x: int
    y: int
    w: int
    h: int

board = """BAAB
BAAB
BCCB
BDDB
D..D
"""    
    
class KlotskiSolverGUI:
    def __init__(self):        
        width, height = 200, 250
        self.canvas = Canvas(width=width, height=height, layout=ipw.Layout(width=f'{width}px', height=f'{height}px'))
        self.event = Event(source=self.canvas, watched_events=['keydown'])
        self.event.on_dom_event(self.handle_event)        
        
        self.text_area = ipw.Textarea(value=board, layout=ipw.Layout(width='100px', height='130px'))
        self.solve_button = ipw.Button(description='Solve')
        self.play_button = ipw.Button(description='Play')
        self.solve_button.on_click(lambda arg:self.solve())
        self.play_button.on_click(self.on_play)
        self.layout = ipw.VBox([
            ipw.HBox([self.solve_button, self.play_button]), 
            ipw.HBox([self.text_area, self.canvas])
        ])
        self.move_queue = deque()
        self.solution = []
        self.start()
        
    def on_play(self, b):
        if self.play_button.description == 'Play':
            self.play_button.description = 'Pause'
            self.pause = False
        else:
            self.play_button.description == 'Pause'
            self.play_button.description = 'Play'
            self.pause = True
        
    def solve(self):
        self.pause = True
        self.play_button.description = 'Play'
        status = ''.join(self.text_area.value.split()).strip().replace('.', ' ')
        self.init_rectangles(status)
        
    def draw(self):
        with ipycanvas.hold_canvas(self.canvas):
            self.canvas.clear()
            size = 40
            for rect in self.rectangles.values():
                self.canvas.fill_style = rect.color
                x, y, w, h = rect.x * size + 2, rect.y * size + 2, rect.w * size, rect.h * size
                self.canvas.fill_rect(x, y, w, h)
                self.canvas.stroke_style = 'black'
                self.canvas.stroke_rect(x, y, w, h)

    def init_rectangles(self, status):
        self.canvas.clear()
        self.positions, self.spaces = status2positions(status)
        self.rectangles = {}
        size = 80
        for i, (name, r, c) in enumerate(self.positions):
            h, w = SIZES[name]
            self.rectangles[r, c] = Rectangle(color=COLORS[i], x=c, y=r, w=w, h=h)
            
        self.solution = list(find_path(status))
        self.solution.insert(0, status)
        self.current_index = 0
        self.draw()

    def fill_move_queue(self, step=1):
        self.current_index += step
        self.current_index = max(min(self.current_index, len(self.solution)-1), 0)

        status = self.solution[self.current_index]
        positions, spaces = status2positions(status)
        set_prev = set(self.positions)
        set_next = set(positions)

        if set_prev == set_next:
            return

        from_pos = (set_prev - set_next).pop()[1:]
        to_pos = (set_next - set_prev).pop()[1:]

        rect = self.rectangles[from_pos]
        del self.rectangles[from_pos]
        self.rectangles[to_pos] = rect

        is_corner = from_pos[0] - to_pos[0] != 0 and from_pos[1] - to_pos[1] != 0
        if not is_corner:
            for pos in interpolate_position(from_pos, to_pos, SPEED):
                self.move_queue.append((rect, pos[::-1]))
        else:
            middle_positions = {(from_pos[0], to_pos[1]), (to_pos[0], from_pos[1])}
            target = (middle_positions & set(self.spaces)).pop()

            move_postions = chain(interpolate_position(from_pos, target, SPEED),
                                  interpolate_position(target, to_pos, SPEED))
            for pos in move_postions:
                self.move_queue.append((rect, pos[::-1]))

        self.positions, self.spaces = positions, spaces

    def on_timer(self):
        if not self.solution:
            return
        
        if not self.move_queue:
            if not self.pause:
                self.fill_move_queue()

        if self.move_queue:
            rect, pos = self.move_queue.popleft()
            rect.x = pos[0]
            rect.y = pos[1]
            self.draw()

    def handle_event(self, event):
        key = event['key']
        if key == " ":
            self.pause = not self.pause
        elif key == "ArrowRight":
            self.fill_move_queue(step=1)
        elif key == "ArrowLeft":
            self.fill_move_queue(step=-1)

    def get_status(self):
        name_map = {v: k for k, v in SIZES.items()}
        board = [" "] * (W * H)
        for pos, rect in self.rectangles.iteritems():
            size = rect.get_height(), rect.get_width()
            idx = pos[0] * W + pos[1]
            name = name_map[size]
            for delta in BLOCKS[name]:
                board[idx + delta] = name
        return "".join(board)
            
    def start(self):
        async def f():
            while True:
                self.on_timer()
                await asyncio.sleep(0.05)
        self.task = asyncio.create_task(f())
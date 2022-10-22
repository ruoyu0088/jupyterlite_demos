import json
import numpy as np
from itertools import product, count, combinations
from collections import defaultdict
from typing import Optional, Literal
from pysat.solvers import Solver
from pythreejs import (
    BoxGeometry,
    PerspectiveCamera,
    AmbientLight,
    Renderer,
    MeshLambertMaterial,
    LineSegments,
    LineBasicMaterial,
    Scene,
    Mesh,
    EdgesGeometry,
    OrbitControls,
)
from collections import defaultdict
from ipywidgets import IntSlider, VBox, HBox, Layout, Dropdown, Button, Text, Label
import ipycanvas
from ipycanvas import Canvas
from ipyevents import Event

BlocksColor = [
    "#ffb631",
    "#f0ea4b",
    "#7a1b7d",
    "#8ad6b3",
    "#2c8dda",
    "#96e2fa",
    "#ff6961",
]

BlocksCubePosition = [
    [[0, 0, 0], [0, 1, 0], [1, 0, 0]],
    [[0, 0, 0], [-1, 0, 0], [1, 1, 0], [0, 1, 0]],
    [[0, 0, 0], [1, 0, 0], [-1, 0, 0], [0, 1, 0]],
    [[0, 0, 0], [1, 0, 0], [2, 0, 0], [0, 1, 0]],
    [[0, 0, 0], [0, 1, 0], [1, 0, 0], [0, 0, 1]],
    [[0, 0, 0], [0, 1, 0], [1, 0, 0], [0, 1, 1]],
    [[0, 0, 0], [0, 1, 0], [1, 0, 0], [1, 0, 1]],
]

BlockNames = list("VZTLY<>")


def rotate(points, axis: Literal["x", "y", "z"], angle: float):
    angle = np.deg2rad(angle)
    c = np.cos(angle)
    s = np.sin(angle)

    if axis == "x":
        m = [[1, 0, 0], [0, c, -s], [0, s, c]]
    elif axis == "y":
        m = [[c, 0, s], [0, 1, 0], [-s, 0, c]]
    elif axis == "z":
        m = [[c, -s, 0], [s, c, 0], [0, 0, 1]]

    m = np.array(m)
    return (m @ points.T).T


def create_all_rotations():
    rotations = []
    for axis, r1, r2 in product("xy", range(0, 360, 90), range(0, 360, 90)):
        rotation = []
        if axis == "y" and r1 in (0, 180):
            continue
        if r1 != 0:
            rotation.append((axis, r1))
        if r2 != 0:
            rotation.append(("z", r2))
        rotations.append(rotation)
    return rotations


def get_unique_blocks(blocks):
    res = []
    for block in blocks:
        block = block - np.min(block, axis=0, keepdims=True)
        block = tuple(sorted([tuple(point) for point in block.tolist()]))
        res.append(block)
    return list(set(res))


def get_rotated_blocks(block):
    rotations = create_all_rotations()
    block = np.asarray(block, dtype=np.float64)
    blocks = []
    for rotation in rotations:
        rotated_block = block.copy()
        for axis, angle in rotation:
            rotated_block = rotate(rotated_block, axis, angle)

        arr = np.round(rotated_block).astype(np.int32)
        blocks.append(arr)
    return get_unique_blocks(blocks)


def get_placed_blocks(block, target):
    block = np.asarray(block)
    first_cube = block[0]
    blocks = []
    for target_cube in target:
        delta = target_cube - first_cube
        offseted_block = block + delta
        offseted_block = tuple(tuple(cube) for cube in offseted_block.tolist())
        offseted_block_set = set(offseted_block)
        if target.contains(offseted_block_set):
            blocks.append(offseted_block)
    return blocks


def exact_one(variables):
    clauses = [list(variables)]
    for v1, v2 in combinations(variables, 2):
        clauses.append([-v1, -v2])
    return clauses


class Questions:
    def __init__(self, fn):
        self.fn = fn
        self.load()

    def keys(self):
        return sorted(self.questions.keys())

    def load(self):
        with open(self.fn) as f:
            self.questions = json.load(f)

    def __getitem__(self, key):
        return self.questions[key]

    def __setitem__(self, key, value):
        self.questions[key] = value
        with open(self.fn, "w") as f:
            json.dump(self.questions, f, indent=4)


class Block:
    def __init__(self, block, block_id):
        self.id = block_id
        self.blocks = get_rotated_blocks(block)

    def place(self, target):
        self.placed_blocks = []
        for block in self.blocks:
            self.placed_blocks.extend(get_placed_blocks(block, target))

    def create_variables(self, variables):
        self.variables = []
        for block in self.placed_blocks:
            v = next(variables)
            self.variables.append(v)

    def create_clauses(self, target, all_block_ids):
        self.clauses = []
        self.clauses.extend(exact_one(self.variables))
        for block, v in zip(self.placed_blocks, self.variables):
            for id_ in all_block_ids:
                if id_ == self.id:
                    continue
                target_variables = target.get_block_variables(block, id_)
                for v2 in target_variables:
                    self.clauses.append([-v, -v2])


class Target:
    def __init__(self, cubes):
        self.cubes = np.asarray(cubes)
        self.cubes_set = set(tuple(cube) for cube in self.cubes.tolist())

    @classmethod
    def make_3x3x3_target(class_):
        return class_(list(product(range(3), range(3), range(3))))

    def contains(self, cubes_set):
        return self.cubes_set.issuperset(cubes_set)

    def __getitem__(self, index):
        return self.cubes[index]

    def __len__(self):
        return len(self.cubes)

    def get_block_variables(self, block, block_id):
        return [self.variables[cube, block_id] for cube in block]

    def create_variables(self, blocks, variables):
        self.variables = {}
        self.cube_variables = defaultdict(dict)

        for cube in self.cubes_set:
            for block in blocks:
                v = next(variables)
                self.variables[cube, block.id] = v
                self.cube_variables[cube][block.id] = v

    def create_clauses(self):
        self.clauses = []
        for key, val in self.cube_variables.items():
            self.clauses.extend(exact_one(list(val.values())))

    def solve(self, block_names_: Optional[str] = None):
        if block_names_ is None:
            block_names = BlockNames
        else:
            block_names = block_names_

        blocks = [
            Block(block, i)
            for i, (name, block) in enumerate(zip(BlockNames, BlocksCubePosition))
            if name in block_names
        ]

        all_block_ids = [block.id for block in blocks]

        variables = count(1, 1)

        for block in blocks:
            block.place(self)

        self.create_variables(blocks, variables)
        for block in blocks:
            block.create_variables(variables)

        self.create_clauses()
        for block in blocks:
            block.create_clauses(self, all_block_ids)

        solver = Solver()
        solver.append_formula(self.clauses)
        for block in blocks:
            solver.append_formula(block.clauses)
        solver.solve()
        solution = solver.get_model()
        self.solution = defaultdict(list)
        if solution is not None:
            for (cube, bid), vid in self.variables.items():
                v = solution[vid - 1]
                if v > 0:
                    self.solution[bid].append(cube)
            self.solution = dict(self.solution)


class BoxScene:
    def __init__(self):
        scene = Scene()
        scene.background = "#f0f0f0"
        light = AmbientLight("#ffffff", 1)
        light.position = 1, 1, 1
        scene.add(light)
        box = BoxGeometry(0.98, 0.98, 0.98)
        self.scene = scene
        self.box = box
        self.objects = defaultdict(list)
        self.camera = PerspectiveCamera(
            position=(-6.2 * 1.5, -10.9 * 1.5, 11.9 * 1.5), fov=20, up=(0, 0, 1)
        )

        self.renderer = Renderer(
            camera=self.camera,
            scene=self.scene,
            antialias=True,
            width=400,
            height=400,
            controls=[OrbitControls(controlling=self.camera)],
        )

    def __len__(self):
        return len(self.objects)

    def add_box(self, position):
        position = tuple(position)
        if self.objects[position]:
            return
        mesh = Mesh(self.box, MeshLambertMaterial(color="#777777"), position=position)
        mesh_edge = LineSegments(
            EdgesGeometry(self.box),
            LineBasicMaterial(parameters=dict(color="#000000", vertexColors=True)),
            position=position,
        )
        self.objects[position].extend([mesh, mesh_edge])
        self.scene.add(mesh)
        self.scene.add(mesh_edge)

    def clear(self):
        keys = list(self.objects.keys())
        with self.scene.hold_sync():
            for key in keys:
                self.del_box(key)

    def add_boxes(self, positions):
        for pos in positions:
            self.add_box(pos)

    def del_box(self, position):
        position = tuple(position)
        if position in self.objects:
            for obj in self.objects[position]:
                self.scene.remove(obj)
            del self.objects[position]

    def set_color(self, position, color):
        position = tuple(position)
        if not self.objects[position]:
            return
        self.objects[position][0].material.color = color


class BlockPlacer:
    def __init__(self, box_scene):
        size = 30
        margin = 5
        n = 9
        self.questions = Questions("magnetcube_questions.json")
        self.box_scene = box_scene
        self.width = self.height = 2 * margin + n * size
        self.size = size
        self.margin = margin
        self.n = n
        self.layout_input = IntSlider(value=0, description="Layer", min=0, max=n)
        self.layout_input.observe(lambda e: self.draw(), names="value")
        self.canvas = Canvas(
            width=self.width,
            height=self.height,
            layout=Layout(width=f"{self.width}px", height=f"{self.height}px"),
        )
        self.event = Event(source=self.canvas, watched_events=["mousedown", "keydown"])
        self.event.on_dom_event(self.callback)

        def sort_key(key):
            try:
                return f"{int(key):03d}"
            except:
                return key

        keys = sorted(self.questions.keys(), key=sort_key)

        layout_tmp = Layout(width="150px")
        self.questions_selector = Dropdown(
            value=keys[0], options=keys, description="Name", layout=layout_tmp
        )
        self.questions_selector.observe(self.on_question_changed, names="value")
        self.solve_button = Button(description="Solve")
        self.solve_button.on_click(self.on_solve)

        self.name_input = Text(value="200", layout=layout_tmp)
        self.save_button = Button(description="Save")
        self.save_button.on_click(self.on_save)

        self.clear_button = Button(description="Clear")
        self.clear_button.on_click(self.on_clear)

        self.message_label = Label()

        self.draw()
        self.layout = VBox(
            [
                self.layout_input,
                self.canvas,
                self.clear_button,
                HBox([self.questions_selector, self.solve_button]),
                HBox([self.name_input, self.save_button]),
                self.message_label,
            ]
        )
        self.on_question_changed(None)

    def on_clear(self, b):
        self.box_scene.clear()
        self.draw()

    def on_save(self, b):
        name = self.name_input.value
        self.questions[name] = list(self.box_scene.objects.keys())
        self.questions_selector.options = list(self.questions_selector.options) + [name]
        self.questions_selector.value = name

    def on_solve(self, e):
        self.message_label.value = ""
        cubes = list(self.box_scene.objects.keys())
        self.target = Target(cubes)
        length = len(self.box_scene.objects)
        try:
            block_names = {27: None, 15: "ZTLV", 11: "ZLV"}[length]
        except KeyError:
            self.message_label.value = "Only support 11, 15 or 27 blocks"
            return
        self.target.solve(block_names)
        if self.target.solution:
            with self.box_scene.scene.hold_sync():
                for k, blocks in self.target.solution.items():
                    for block in blocks:
                        self.box_scene.set_color(block, BlocksColor[k])

    def on_question_changed(self, event):
        value = self.questions_selector.value
        with self.box_scene.scene.hold_sync():
            self.box_scene.clear()
            self.box_scene.add_boxes(self.questions[value])

        self.draw()

    def callback(self, event):
        global e
        e = event
        margin = self.margin
        size = self.size
        n = self.n
        e = event
        need_draw = False
        if e["type"] == "mousedown":
            x = e["relativeX"]
            y = e["relativeY"]
            x = (x - margin) // size
            y = (y - margin) // size
            x = x - n // 2
            y = (n - 1 - y) - n // 2
            z = 0
            position = (x, y, self.layout_input.value)
            if event["ctrlKey"]:
                self.box_scene.del_box(position)
                need_draw = True
            else:
                self.box_scene.add_box(position)
                need_draw = True

        elif e["type"] == "keydown":
            if e["key"] == "ArrowRight":
                self.layout_input.value += 1
                need_draw = True

            elif e["key"] == "ArrowLeft":
                self.layout_input.value -= 1
                need_draw = True

        if need_draw:
            self.draw()

    def draw(self):
        canvas = self.canvas
        n = self.n
        size = self.size
        width = self.width
        height = self.height
        margin = self.margin

        with ipycanvas.hold_canvas(canvas):
            canvas.clear()

            locations = list(self.box_scene.objects.keys())
            locations = sorted(locations, key=lambda x:x[2], reverse=True)
            for x, y, z in locations:
                x += n // 2
                y += n // 2
                y = n - 1 - y
                x = margin + x * size
                y = margin + y * size
                if z == self.layout_input.value:
                    canvas.fill_style = "#cccccc"
                    canvas.fill_rect(x, y, size, size)
                elif z == self.layout_input.value - 1:
                    canvas.fill_style = "#777777"
                    canvas.fill_circle(x + size / 2, y + size / 2, 2)

            for i in range(n + 1):
                canvas.stroke_line(
                    margin, size * i + margin, width - margin, size * i + margin
                )

            for i in range(n + 1):
                canvas.stroke_line(
                    size * i + margin, margin, size * i + margin, height - margin
                )

        self.message_label.value = f'{len(self.box_scene)} cubes'


if __name__ == "__main__":
    command, block_names = Questions[104]
    target = Target.from_command(command)
    print(target.cubes.tolist())

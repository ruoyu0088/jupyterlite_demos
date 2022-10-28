import cffi
import numpy as np
from scipy.spatial.distance import pdist, squareform
from bokeh.plotting import figure, output_notebook, show
from bokeh.io import push_notebook
from bokeh.models import ColumnDataSource, Label
from bokeh.layouts import Row
import asyncio


ffi = cffi.FFI()

ffi.cdef('''
double ant_travel(double *dist_matrix, double *pheromone_matrix, double alpha, double beta, int n, 
    int *to_travel, int *path, double *weights);
double ant_colony_optimize(double * dist_matrix, int iter_count, double Q, double alpha, double beta, double rho, int closed, 
    double * pheromone_matrix, int * to_travel, int * path, int * best_path, double * weights, double min_dist, int n
);
''')

lib = ffi.dlopen('antcolony.wasm')

class ShortestLoop:
    def __init__(self, points, iter_count=3000, Q=1000, alpha=0.8, beta=2.0, rho=0.9, closed=True):
        self.iter_count = iter_count
        self.Q = Q
        self.alpha = alpha
        self.beta = beta
        self.rho = rho
        self.closed = int(closed)
        self.points = np.asarray(points)
        n = len(self.points)
        
        self.dist_matrix = squareform(pdist(self.points))
        self.pheromone_matrix = np.ones_like(self.dist_matrix)
        self.to_travel = np.zeros(n, dtype=np.int32)
        self.path = np.zeros(n, dtype=np.int32)
        self.best_path = np.zeros(n, dtype=np.int32)
        self.weights = np.zeros(n, dtype=np.float64)

        self.p_dist_matrix = ffi.from_buffer('double *', self.dist_matrix)
        self.p_pheromone_matrix = ffi.from_buffer('double *', self.pheromone_matrix)
        self.p_to_travel = ffi.from_buffer('int *', self.to_travel)
        self.p_path = ffi.from_buffer('int *', self.path)
        self.p_best_path = ffi.from_buffer('int *', self.best_path)
        self.p_weights = ffi.from_buffer('double *', self.weights)
        self.min_dist = np.inf

    def iter(self, iter_count):
        n = self.dist_matrix.shape[0]
        self.min_dist = lib.ant_colony_optimize(
            self.p_dist_matrix, iter_count, self.Q, self.alpha, self.beta, self.rho, self.closed,
            self.p_pheromone_matrix,
            self.p_to_travel,
            self.p_path,
            self.p_best_path,
            self.p_weights,
            self.min_dist,
            n
        )
        return self.min_dist
    
    
class ShortestLoopViewer:
    def __init__(self, points, **kw):
        self.sl = ShortestLoop(points, **kw)
        self.sl.iter(1)
        
    def plot_data(self):
        pheromone_matrix = np.clip(self.sl.pheromone_matrix, 0.1, None)
        alpha = (pheromone_matrix.ravel() - pheromone_matrix.min()) / pheromone_matrix.ptp()
        x, y = self.sl.points[self.sl.best_path].T
        return dict(x=x, y=y, alpha=alpha)
    
    def step(self, iter_count):
        self.sl.iter(iter_count)
        self.update()
    
    def update(self, iter_count=None):
        data = self.plot_data()
        self.source1.data['x'] = data['x']
        self.source1.data['y'] = data['y']
        self.source2.data['alpha'] = data['alpha']
        if iter_count is None:
            self.label.text = f'length:{self.sl.min_dist:5.3f}'
        else:
            self.label.text = f'iter:{iter_count:05d}, length:{self.sl.min_dist:5.3f}'
        push_notebook(handle=self.handle)        
        
    def show(self):
        sl = self.sl
        data = self.plot_data()
        x = data['x']
        y = data['y']
        alpha = data['alpha']
        
        n = len(self.sl.points)
        index = np.array(list(np.ndindex(n, n)))
        segments = self.sl.points[index]
        xs = segments[:, :, 0].tolist()
        ys = segments[:, :, 1].tolist()
        
        fig1 = figure(frame_height=300, frame_width=300, match_aspect=True, aspect_ratio=1, toolbar_location=None)
        fig2 = figure(frame_height=300, frame_width=300, match_aspect=True, aspect_ratio=1, toolbar_location=None)
        self.source1 = ColumnDataSource(data=dict(x=x, y=y))
        self.source2 = ColumnDataSource(data=dict(xs=xs, ys=ys, alpha=alpha))
        fig1.patch('x', 'y', source=self.source1, fill_color=None)
        fig1.scatter('x', 'y', source=self.source1)
        fig2.multi_line('xs', 'ys', alpha='alpha', source=self.source2)
        self.label = Label(x=5, y=5, x_units='screen', y_units='screen',
                         text=f'length:{self.sl.min_dist:5.3f}', render_mode='css',
                         border_line_color='black', border_line_alpha=1.0,
                         background_fill_color='white', background_fill_alpha=1.0)        
        fig1.add_layout(self.label)
        layout = Row(fig1, fig2)
        self.handle = show(layout, notebook_handle=True)
        
    async def run(self, max_iter):
        min_dist = self.sl.min_dist
        step = 1
        total_steps = 0
        last_update_steps = 0
        steps = []
        while total_steps < max_iter:
            self.sl.iter(step)
            steps.append(step)
            total_steps += step
            last_update_steps += step
            if self.sl.min_dist < min_dist:
                min_dist = self.sl.min_dist
                step = last_update_steps
                last_update_steps = 0
                self.update(iter_count=total_steps)
                await asyncio.sleep(0.1)            
        self.update(iter_count=max_iter)
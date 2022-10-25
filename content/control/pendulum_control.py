import asyncio
import scipy as sp
from scipy.integrate import odeint, ode
import numpy as np
from sympy import symbols, Symbol, lambdify
from sympy.physics.mechanics import (dynamicsymbols, Point, Particle, ReferenceFrame,
KanesMethod)
import ipywidgets as ipw
import ipycanvas
from ipycanvas import Canvas
from ipyevents import Event


class Pendulum:
    def __init__(self, n=2):
        self.target_position = 0.0
        self.n = n
        self.q = q = dynamicsymbols('q:' + str(n + 1))  # Generalized coordinates
        self.u = u = dynamicsymbols('u:' + str(n + 1))  # Generalized speeds
        f = dynamicsymbols('f')                # Force applied to the cart

        m = symbols('m:' + str(n + 1))         # Mass of each bob
        l = symbols('l:' + str(n))             # Length of each link
        g, t = symbols('g t')                  # Gravity and time
        self.t = t

        I = ReferenceFrame('I')                # Inertial reference frame
        O = Point('O')                         # Origin point
        O.set_vel(I, 0)    

        P0 = Point('P0')                       # Hinge point of top link
        P0.set_pos(O, q[0] * I.x)              # Set the position of P0    
        P0.set_vel(I, u[0] * I.x)              # Set the velocity of P0
        Pa0 = Particle('Pa0', P0, m[0])        # Define a particle at P0

        frames = [I]                              # List to hold the n + 1 frames
        points = [P0]                             # List to hold the n + 1 points
        particles = [Pa0]                         # List to hold the n + 1 particles
        forces = [(P0, f * I.x - m[0] * g * I.y)] # List to hold the n + 1 applied forces, including the input force, f
        kindiffs = [q[0].diff(t) - u[0]]          # List to hold kinematic ODE's

        for i in range(n):
            Bi = I.orientnew('B' + str(i), 'Axis', [q[i + 1], I.z])   # Create a new frame
            Bi.set_ang_vel(I, u[i + 1] * I.z)                         # Set angular velocity
            frames.append(Bi)                                         # Add it to the frames list

            Pi = points[-1].locatenew('P' + str(i + 1), l[i] * Bi.x)  # Create a new point
            Pi.v2pt_theory(points[-1], I, Bi)                         # Set the velocity
            points.append(Pi)                                         # Add it to the points list

            Pai = Particle('Pa' + str(i + 1), Pi, m[i + 1])           # Create a new particle
            particles.append(Pai)                                     # Add it to the particles list

            forces.append((Pi, -m[i + 1] * g * I.y))                  # Set the force applied at the point

            kindiffs.append(q[i + 1].diff(t) - u[i + 1])              # Define the kinematic ODE:  dq_i / dt - u_i = 0        

        self.kane = KanesMethod(I, q_ind=q, u_ind=u, kd_eqs=kindiffs) # Initialize the object
        fr, frstar = self.kane.kanes_equations(particles, forces)     # Generate EoM's fr + frstar = 0       
        self.parameters = parameters = [g, m[0]]                       # Parameter definitions starting with gravity and the first bob
        for i in range(n):                           # Then each mass and length
            parameters += [l[i], m[i + 1]]

        dynamic = q + u                                                # Make a list of the states
        dynamic.append(f)                                              # Add the input force
        dummy_symbols = [Symbol(i.name) for i in dynamic]                     # Create a dummy symbol for each variable
        dummy_dict = dict(zip(dynamic, dummy_symbols))
        kindiff_dict = self.kane.kindiffdict()                              # Get the solved kinematical differential equations
        self.M = self.kane.mass_matrix_full.subs(kindiff_dict).subs(dummy_dict)  # Substitute into the mass matrix 
        self.F = self.kane.forcing_full.subs(kindiff_dict).subs(dummy_dict)      # Substitute into the forcing vector
        self.func_parameters =  dummy_symbols + parameters       
        self.MF_func = lambdify(self.func_parameters, [self.M, self.F], cse=True, modules=["math", "numpy"], )

        self.M_func = lambdify(self.func_parameters, self.M)               # Create a callable function to evaluate the mass matrix 
        self.F_func = lambdify(self.func_parameters, self.F)               # Create a callable function to evaluate the forcing vector 
        self.dynamic = dynamic

    def set_target(self, position):
        self.target_position = position
        

    def right_hand_side(self, parameters, control=False, flip_args=False):    
        def f(x, t):
            """Returns the derivatives of the states.

            Parameters
            ----------
            x : ndarray, shape(2 * (n + 1))
                The current state vector.
            t : float
                The current time.

            Returns
            -------
            dx : ndarray, shape(2 * (n + 1))
                The derivative of the state.
            
            """
            if flip_args:
                x, t = t, x

            if not control:
                u = 0.0                              # The input force is always zero
            else:
                u = np.dot(self.K, self.target - x)    # The controller       
            arguments = np.hstack((x, u, parameters))     # States, input, and parameters
            M, F = self.MF_func(*arguments)
            dx = np.array(np.linalg.solve(M, F)).T[0]

            return dx
        return f

    def x0(self, q0=0.0):
        return np.hstack((q0, np.pi / 2 * np.ones(len(self.q) - 1), 1e-3 * np.ones(len(self.u)) ))

    def solve_ode(self, x0, t, parameter_vals, control=False):
        if control:
            self.calculate_control_gain(parameter_vals)
        f = self.right_hand_side(parameter_vals, control=control)
        y = odeint(f, x0, t)         # Actual integration
        fig, axes = pl.subplots(2, 1, figsize=(12, 8), sharex=True)
        n = y.shape[1] // 2
        axes[0].plot(t, y[:, :n])
        axes[1].plot(t, y[:, n:])
        axes[1].set_xlabel('Time [sec]')
        axes[0].legend(self.dynamic[:n])
        axes[1].legend(self.dynamic[n:])
        return fig, axes

    def iter_ode(self, x0, parameter_vals, dt=0.02):
        self.calculate_control_gain(parameter_vals)
        f = self.right_hand_side(parameter_vals, control=True, flip_args=True)
        r = ode(f)
        r.set_integrator('dopri5')
        r.set_initial_value(x0)
        while r.successful:
            y = r.integrate(r.t + dt)
            self.target[0] = self.target[0] * 0.95 + self.target_position * 0.05
            yield y

    def calculate_control_gain(self, parameter_vals):
        equilibrium_point = np.hstack(( 0, np.pi / 2 * np.ones(len(self.q) - 1), np.zeros(len(self.u))))
        equilibrium_dict = dict(zip(self.q + self.u, equilibrium_point))
        parameter_dict = dict(zip(self.parameters, parameter_vals))
        M, linear_state_matrix, linear_input_matrix, inputs = self.kane.linearize(A_and_B=False)
        linear_state_matrix = linear_state_matrix.subs([(tmp.diff(self.t), 0) for tmp in self.u])
        f_A_lin = linear_state_matrix.subs(parameter_dict).subs(equilibrium_dict)
        f_B_lin = linear_input_matrix.subs(parameter_dict).subs(equilibrium_dict)
        m_mat = M.subs(parameter_dict).subs(equilibrium_dict)
        f_B_lin = np.asarray(f_B_lin, dtype=np.float64)
        f_A_lin = np.asarray(f_A_lin, dtype=np.float64)
        m_mat = np.asarray(m_mat, dtype=np.float64)
        inv_m_mat = np.linalg.inv(m_mat)
        A = inv_m_mat @ f_A_lin
        B = inv_m_mat @ f_B_lin
        Q = np.ones(A.shape)
        R = np.ones((1, 1))
        X = sp.linalg.solve_continuous_are(A, B, Q, R)
        K = np.linalg.solve(R, B.T @ X)
        self.target = equilibrium_point.copy()
        self.K = K

        
class PendulumAnimation:
    def __init__(self, solver, x0, parameters, width=400, height=200):
        self.x0 = x0
        self.parameters = parameters
        self.lengths = np.array(parameters)[2::2]
        self.solver = solver
        self.width = width
        self.height = height
        self.task = None
        self.block_width = 0.5
        self.block_height = 0.3
        self.scale = 50
        self.canvas = Canvas(width=self.width, height=self.height, layout=ipw.Layout(width=f'{self.width}px', height=f'{self.height}px'))
        self.event = Event(source=self.canvas, watched_events=['mousedown'])
        self.event.on_dom_event(self.on_event)
        layout = ipw.Layout(width='50px')
        self.init_button = ipw.Button(description='Init', layout=layout)
        self.start_button = ipw.Button(description='Start', layout=layout)
        self.stop_button = ipw.Button(description='Stop', layout=layout)
        self.init_button.on_click(lambda b:self.init_animation(random=True))
        self.start_button.on_click(lambda b:self.start_animation())
        self.stop_button.on_click(lambda b:self.stop_animation())
        self.layout = ipw.VBox([
            ipw.HBox([self.init_button, self.start_button, self.stop_button]),
            self.canvas])
        self.force = 0
        self.init_animation(random=False)
        
    def on_event(self, event):
        if self.task is not None:
            if event['type'] == 'mousedown':
                x = (event['relativeX'] - self.width / 2) / self.scale
                self.solver.set_target(x)
                
    def init_animation(self, random=True):
        n = len(self.parameters) // 2 - 1
        if random:
            self.x0 = np.r_[0, np.deg2rad(np.random.uniform(-7, 7, n)) + np.pi/2, np.zeros(n + 1)] 
        self.ode_call = self.solver.iter_ode(self.x0, self.parameters)
        self.force = 0.0
        s = next(self.ode_call)
        self.draw(s)
    
    def start_animation(self):
        self.task = asyncio.create_task(self.animation())
        
    def stop_animation(self):
        if self.task is not None:
            self.task.cancel()
            self.task = None
        # Stop all tasks
        for task in asyncio.all_tasks():
            if task.get_coro().__name__ == 'animation':
                task.cancel()            
        
    async def animation(self):
        while True:
            s = next(self.ode_call)
            self.force = np.sum(self.solver.K[0] * (self.solver.target - s))
            self.draw(s)
            await asyncio.sleep(0.02)

    def draw(self, s):
        canvas = self.canvas
        with ipycanvas.hold_canvas(canvas):
            canvas.reset_transform()
            canvas.clear()
            canvas.stroke_style = '#000000'
            canvas.translate(self.width // 2, self.height * 0.8)
            canvas.scale(self.scale, -self.scale)
            canvas.line_width = 0.01
            canvas.stroke_line(-10, 0, 10, 0)
            canvas.stroke_line(0, 0, 0, 10)
            canvas.line_width = 0.05
            canvas.fill_rect(s[0] - self.block_width / 2, 
                             0 - self.block_height / 2, 
                             self.block_width, self.block_height)
            x, y = s[0], 0
            for i, l in enumerate(self.lengths, 1):
                x2, y2 = x + l * np.cos(s[i]), y + l * np.sin(s[i])
                canvas.stroke_line(x, y, x2, y2)
                canvas.fill_circle(x2, y2, 0.05)
                x, y = x2, y2
            canvas.stroke_style = '#ff0000'
            canvas.stroke_line(s[0], 0, s[0] + self.force * 50, 0)
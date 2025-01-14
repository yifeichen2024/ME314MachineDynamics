# -*- coding: utf-8 -*-
"""ME314 Final Project FA2023.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Fd8uAQr95DRf0quU3bY01c5fTVMJXCzl

# ME314 Final Project

###Description:
A 2D simulation of a jack bouncing inside a box.
"""

### IMPORTS ###
import sympy as sym
import numpy as np
import matplotlib.pyplot as plt

### GEOMETRY HELPER FUNCTIONS ###


def unhat_se3_sym(tf_matrix):
  vector = sym.Matrix([[tf_matrix[0,3]], [tf_matrix[1,3]], [tf_matrix[2,3]], [tf_matrix[2,1]], [tf_matrix[0,2]], [tf_matrix[1,0]]])
  return vector


def inverse_se3_sym(se3_mat):
  rot = sym.Matrix([[se3_mat[0,0], se3_mat[0,1], se3_mat[0,2]],
                    [se3_mat[1,0], se3_mat[1,1], se3_mat[1,2]],
                    [se3_mat[2,0], se3_mat[2,1], se3_mat[2,2]]])
  pos = sym.Matrix([[se3_mat[0,3]],
                    [se3_mat[1,3]],
                    [se3_mat[2,3]]])
  rot_T = rot.T
  pos_T = -rot_T*pos
  se3_mat_inv = sym.Matrix([[rot_T[0,0], rot_T[0,1], rot_T[0,2], pos_T[0]],
                            [rot_T[1,0], rot_T[1,1], rot_T[1,2], pos_T[1]],
                            [rot_T[2,0], rot_T[2,1], rot_T[2,2], pos_T[2]],
                            [0, 0, 0, 1]])
  return se3_mat_inv


def tf_matrix_sym(pos, theta):
  sym_matrix = sym.Matrix([[sym.cos(theta), -sym.sin(theta), 0, pos[0]],
                          [sym.sin(theta),  sym.cos(theta), 0, pos[1]],
                          [ 0, 0, 1, pos[2]],
                          [ 0, 0, 0, 1]])
  return sym_matrix


def tf_matrix_np(theta, pos):
  np_matrix = np.array([[np.cos(theta), -np.sin(theta), 0, pos[0]],
                        [np.sin(theta),  np.cos(theta), 0, pos[1]],
                        [ 0, 0, 1, pos[2]],
                        [ 0, 0, 0, 1]])
  return np_matrix


def find_vb_sym(tf_matrix):
  vb = unhat_se3_sym(inverse_se3_sym(tf_matrix)*tf_matrix.diff(t))
  return vb


def find_inertia_matrix_sym(m, J):
  inertia_mat = sym.Matrix([[m, 0, 0, 0, 0, 0],
                            [0, m, 0, 0, 0, 0],
                            [0, 0, m, 0, 0, 0],
                            [0, 0, 0, 0, 0, 0],
                            [0, 0, 0, 0, 0, 0],
                            [0, 0, 0, 0, 0, J]])
  return inertia_mat

### SIMULATION FUNCTIONS ###

def impact_update(s, impact_eq, subs_plus, phi_val):
  # substitute s for theta- variables
  eq_subs = impact_eq.subs({xb:s[0], yb:s[1], thetab:s[2], xj:s[3],
                            yj:s[4], thetaj:s[5], dxb:s[6], dyb:s[7],
                            dthetab:s[8], dxj:s[9], dyj:s[10],
                            dthetaj:s[11]})

  # solve them for qdot(tau+) and lambda
  impact_solns = sym.solve([eq_subs], [dxb_p, dyb_p, dthetab_p, dxj_p, dyj_p, dthetaj_p, lam], dict=True)
  display(impact_eq)
  display(eq_subs)
  display(impact_solns)

  if len(impact_solns) == 1:
    print("pass")
    pass
  else:
    for sol in impact_solns:
        sol_lam = sol[lam]
        if ((abs(sol_lam) == sol_lam) and (abs(phi_val) == phi_val)) or ((abs(sol_lam) != sol_lam) and (abs(phi_val) != phi_val)):
          print(sol_lam)
          output = np.array([float(s[0]), float(s[1]), float(s[2]),
                            float(s[3]), float(s[4]), float(s[5]),
                            float(sol[dummy_plus[0]]), float(sol[dummy_plus[1]]), float(sol[dummy_plus[2]]),
                            float(sol[dummy_plus[3]]), float(sol[dummy_plus[4]]), float(sol[dummy_plus[5]])])
        else:
          pass
    return output


def check_for_impact(s, phi_sol, thresh=0.25):
  """Check for impact."""
  phi_val = phi_sol(s)
  for i in range(phi_val.shape[0]):
      if (phi_val[i] < thresh) and (phi_val[i] > -thresh):
          print(phi_val[i])
          return (True, i, phi_val[i][0])
  return (False, None)


def integrate(f, xt, dt, time):
    """
    This function takes in an initial condition x(t) and a timestep dt,
    as well as a dynamical system f(x) that outputs a vector of the
    same dimension as x(t). It outputs a vector x(t+dt) at the future
    time step.

    Parameters
    ============
    dyn: Python function
        derivate of the system at a given step x(t),
        it can considered as \dot{x}(t) = func(x(t))
    xt: NumPy array
        current step x(t)
    dt:
        step size for integration

    Return
    ============
    new_xt:
        value of x(t+dt) integrated from x(t)
    """
    k1 = dt * f(xt, time)
    k2 = dt * f(xt + k1/2.0, time)
    k3 = dt * f(xt + k2/2.0, time)
    k4 = dt * f(xt + k3, time)
    new_xt = xt + (1/6.0) * (k1 + 2.0*k2 + 2.0*k3 + k4)
    return new_xt


def simulate(f, x0, tspan, dt, integrate, phi_sol):
    """
    This function takes in an initial condition x0, a timestep dt,
    a time span tspan consisting of a list [min_time, max_time],
    as well as a dynamical system f(x) that outputs a vector of the
    same dimension as x0. It outputs a full trajectory simulated
    over the time span of dimensions (xvec_size, time_vec_size).

    Parameters
    ============
    f: Python function
        derivate of the system at a given step x(t),
        it can considered as \dot{x}(t) = func(x(t))
    x0: NumPy array
        initial conditions
    tspan: Python list
        tspan = [min_time, max_time], it defines the start and end
        time of simulation
    dt:
        time step for numerical integration
    integrate: Python function
        numerical integration method used in this simulation

    Return
    ============
    x_traj:
        simulated trajectory of x(t) from t=0 to tf
    """
    N = int((tspan[1] - tspan[0]) / dt)
    x = np.copy(x0)
    tvec = np.linspace(tspan[0], tspan[1], N)
    xtraj = np.zeros((len(x0), N))
    time = 0.0
    for i in range(N):
      print(i)
      time += dt
      xtraj[:, i] = integrate(f, x, dt, time)
      x = np.copy(xtraj[:, i])
      impact = check_for_impact(x, phi_sol)
      print(impact)
      if impact[0] == True:
        x = np.copy(xtraj[:, i-1])
        eq_num = impact[1]
        x = impact_update(x, impact_eqs[eq_num], dummy_plus, impact[2])
    return xtraj


def dyn(s, time):
    """
    System dynamics function (extended)

    Parameters
    ============
    s: NumPy array
        the extended system state vector,
        s = [x_box, y_box, theta_box, x_jack, y_jack, thet_jack, x_box_dot, y_box_dot, theta_box_dot, x_jack_dot, y_jack_dot, thet_jack_dot]

    Return
    ============
    sdot: NumPy array
        time derivative of input state vector,
        sdot = [x_box_dot, y_box_dot, theta_box_dot, x_jack_dot, y_jack_dot, thet_jack_dot, x_box_ddot, y_box_ddot, theta_box_ddot, x_jack_ddot, y_jack_ddot, theta_jack_ddot]
    """
    x_box_ddot = xddot_box_sol(s[0], s[1], s[2], s[3], s[4], s[5], s[6], s[7], s[8], s[9], s[10], s[11], time)
    y_box_ddot = yddot_box_sol(s[0], s[1], s[2], s[3], s[4], s[5], s[6], s[7], s[8], s[9], s[10], s[11], time)
    theta_box_ddot = thetaddot_box_sol(s[0], s[1], s[2], s[3], s[4], s[5], s[6], s[7], s[8], s[9], s[10], s[11], time)
    x_jack_ddot = xddot_jack_sol(s[0], s[1], s[2], s[3], s[4], s[5], s[6], s[7], s[8], s[9], s[10], s[11], time)
    y_jack_ddot = yddot_jack_sol(s[0], s[1], s[2], s[3], s[4], s[5], s[6], s[7], s[8], s[9], s[10], s[11], time)
    theta_jack_ddot = thetaddot_jack_sol(s[0], s[1], s[2], s[3], s[4], s[5], s[6], s[7], s[8], s[9], s[10], s[11], time)

    return np.array([s[6], s[7], s[8], s[9], s[10], s[11], x_box_ddot, y_box_ddot, theta_box_ddot, x_jack_ddot, y_jack_ddot, theta_jack_ddot])

### PLOTTING AND ANIMATION FUNCTIONS ###

def animate_jack(theta_array, L_box, L_jack, T):
    """
    Function to generate web-based animation of a jack in a box

    Parameters:
    ================================================
    theta_array:
        trajectory of xb, yb, thetab, xj, yj, thetaj
    L_box:
        length of the box
    L_jack:
        length of the jack
    T:
        length/seconds of animation duration

    Returns: None
    """

    ################################
    # Imports required for animation.
    from plotly.offline import init_notebook_mode, iplot
    from IPython.display import display, HTML
    import plotly.graph_objects as go

    #######################
    # Browser configuration.
    def configure_plotly_browser_state():
        import IPython
        display(IPython.core.display.HTML('''
            <script src="/static/components/requirejs/require.js"></script>
            <script>
              requirejs.config({
                paths: {
                  base: '/static/base',
                  plotly: 'https://cdn.plot.ly/plotly-1.5.1.min.js?noext',
                },
              });
            </script>
            '''))
    configure_plotly_browser_state()
    init_notebook_mode(connected=False)

    ###############################################
    # Get data from imported trajectory
    N = len(theta_array[0])
    xb_array = theta_array[0]
    yb_array = theta_array[1]
    thetab_array = theta_array[2]
    xj_array = theta_array[3]
    yj_array = theta_array[4]
    thetaj_array = theta_array[5]

    ###############################################
    # Define arrays with frame data
    # Box
    frame_box1_x = np.zeros(N)
    frame_box1_y = np.zeros(N)
    frame_box2_x = np.zeros(N)
    frame_box2_y = np.zeros(N)
    frame_box3_x = np.zeros(N)
    frame_box3_y = np.zeros(N)
    frame_box4_x = np.zeros(N)
    frame_box4_y = np.zeros(N)
    # Jack
    frame_jack1_x = np.zeros(N)
    frame_jack1_y = np.zeros(N)
    frame_jack2_x = np.zeros(N)
    frame_jack2_y = np.zeros(N)
    frame_jack3_x = np.zeros(N)
    frame_jack3_y = np.zeros(N)
    frame_jack4_x = np.zeros(N)
    frame_jack4_y = np.zeros(N)

    for i in range(N): # iteration through each time step
        g_wb = tf_matrix_np(thetab_array[i], [xb_array[i], yb_array[i], 0])
        g_wj = tf_matrix_np(thetaj_array[i], [xj_array[i], yj_array[i], 0])
        # Box
        frame_box1_x[i] = (g_wb.dot(([L_box/2, L_box/2, 0, 1])))[0]
        frame_box1_y[i] = (g_wb.dot(([L_box/2, L_box/2, 0, 1])))[1]
        frame_box2_x[i] = (g_wb.dot(([L_box/2, -L_box/2, 0, 1])))[0]
        frame_box2_y[i] = (g_wb.dot(([L_box/2, -L_box/2, 0, 1])))[1]
        frame_box3_x[i] = (g_wb.dot(([-L_box/2, -L_box/2, 0, 1])))[0]
        frame_box3_y[i] = (g_wb.dot(([-L_box/2, -L_box/2, 0, 1])))[1]
        frame_box4_x[i] = (g_wb.dot(([-L_box/2, L_box/2, 0, 1])))[0]
        frame_box4_y[i] = (g_wb.dot(([-L_box/2, L_box/2, 0, 1])))[1]
        # Jack
        frame_jack1_x[i] = (g_wj.dot(([L_jack/2, L_jack/2, 0, 1])))[0]
        frame_jack1_y[i] = (g_wj.dot(([L_jack/2, L_jack/2, 0, 1])))[1]
        frame_jack2_x[i] = (g_wj.dot(([L_jack/2, -L_jack/2, 0, 1])))[0]
        frame_jack2_y[i] = (g_wj.dot(([L_jack/2, -L_jack/2, 0, 1])))[1]
        frame_jack3_x[i] = (g_wj.dot(([-L_jack/2, -L_jack/2, 0, 1])))[0]
        frame_jack3_y[i] = (g_wj.dot(([-L_jack/2, -L_jack/2, 0, 1])))[1]
        frame_jack4_x[i] = (g_wj.dot(([-L_jack/2, L_jack/2, 0, 1])))[0]
        frame_jack4_y[i] = (g_wj.dot(([-L_jack/2, L_jack/2, 0, 1])))[1]

    ####################################
    # Using these to specify axis limits.
    xm = -8
    xM = 8
    ym = -8
    yM = 8

    ###########################
    # Defining data dictionary.
    # Trajectories are here.
    data=[
        dict(name='Box'),
        dict(name='Jack'),
        dict(name='Jack massless rod'),
        dict(name='Jack massless rod'),
        ]

    ################################
    # Preparing simulation layout.
    # Title and axis ranges are here.
    layout=dict(autosize=False, width=1000, height=1000,
                xaxis=dict(range=[xm, xM], autorange=False, zeroline=False,dtick=1),
                yaxis=dict(range=[ym, yM], autorange=False, zeroline=False,scaleanchor = "x",dtick=1),
                title='Jack Simulation',
                hovermode='closest',
                updatemenus= [{'type': 'buttons',
                               'buttons': [{'label': 'Start','method': 'animate',
                                            'args': [None, {'frame': {'duration': T, 'redraw': False}}]},
                                           {'args': [[None], {'frame': {'duration': T, 'redraw': False}, 'mode': 'immediate',
                                            'transition': {'duration': 0}}],'label': 'Stop','method': 'animate'}
                                          ]
                              }]
               )

    ########################################
    # Defining the frames of the simulation.
    frames=[dict(data=[
                      #################### BOX LINES ############################
                      dict(x=[frame_box1_x[k], frame_box2_x[k], frame_box3_x[k], frame_box4_x[k], frame_box1_x[k]],
                           y=[frame_box1_y[k], frame_box2_y[k], frame_box3_y[k], frame_box4_y[k], frame_box1_y[k]],
                           mode='lines',
                           line=dict(color='black', width=5),
                           ),
                      #################### JACK POINT MASSES ############################
                      go.Scatter(
                            x=[frame_jack1_x[k], frame_jack2_x[k], frame_jack3_x[k], frame_jack4_x[k]],
                            y=[frame_jack1_y[k], frame_jack2_y[k], frame_jack3_y[k], frame_jack4_y[k]],
                            mode="markers",
                            marker=dict(color="blue", size=12)),
                       #################### JACK POINT LINES ############################
                       dict(x=[frame_jack1_x[k], frame_jack3_x[k]],
                            y=[frame_jack1_y[k], frame_jack3_y[k]],
                            mode='lines',
                            line=dict(color='red', width=2),
                            ),
                       dict(x=[frame_jack2_x[k], frame_jack4_x[k]],
                            y=[frame_jack2_y[k], frame_jack4_y[k]],
                            mode='lines',
                            line=dict(color='red', width=2),
                            ),
                      ]) for k in range(N)]

    #######################################
    # Putting it all together and plotting.
    figure1=dict(data=data, layout=layout, frames=frames)
    iplot(figure1)

def plot(traj, tspan, dt):
  """Plot box and jack motion."""
  x_t = np.linspace(tspan[0], tspan[1], int(tspan[1]/dt))
  plt.figure()
  plt.plot(x_t, traj[0], label=r'$x_b(t)$')
  plt.plot(x_t, traj[1], label=r'$y_b(t)$')
  plt.plot(x_t, traj[3], label=r'$x_j(t)$')
  plt.plot(x_t, traj[4], label=r'$y_j(t)$')
  plt.title('Box and Jack $x_b$, $y_b$ vs Time [t]')
  plt.xlabel('t')
  plt.legend(loc='upper left')
  plt.show()
  plt.figure()
  plt.plot(x_t, traj[2], label=r'$\theta_b(t)$')
  plt.plot(x_t, traj[5], label=r'$\theta_j(t)$')
  plt.title('Box and Jack $theta_j$ vs Time [t]')
  plt.xlabel('t')
  plt.legend(loc='lower left')
  plt.show()

### MAIN CODE ###

# Define box parameters
side_length_box = 10                                   # box exterior side length                                                                                         # thickness of box walls
mass_box = 3                                        # mass of the box
J_box = (mass_box/12) * (side_length_box)**2           # inertia of the box about Z axis

# Define dice parameters
length_jack = 1                                  # x/y length of the jack sides
mass_jack = 1                                   # total mass of the jack
J_jack = mass_jack * (4 * (length_jack/2)**2)    # inertia of jack about Z axis

# Gravity
g = 9.81

# Define time and lambda sympy variables
t, lam = sym.symbols('t, \lambda')

# Define functions for jack and box center positions and orientations
x_box = sym.Function('x_box')(t)
y_box = sym.Function('y_box')(t)
theta_box = sym.Function('theta_box')(t)
x_jack = sym.Function('x_jack')(t)
y_jack = sym.Function('y_jack')(t)
theta_jack = sym.Function('theta_jack')(t)

# Define box and dice centers relative to world frame
g_w_box = tf_matrix_sym([x_box, y_box, 0.0], theta_box)
g_w_jack = tf_matrix_sym([x_jack, y_jack, 0.0], theta_jack)

# Define jack corners relative to jack center
g_jack_corner1 = tf_matrix_sym([lengh_jack/2, lengh_jack/2, 0.0], 0.0)
g_jack_corner2 = tf_matrix_sym([lengh_jack/2, -lengh_jack/2, 0.0], 0.0)
g_jack_corner3 = tf_matrix_sym([-lengh_jack/2, -lengh_jack/2, 0.0], 0.0)
g_jack_corner4 = tf_matrix_sym([-lengh_jack/2, lengh_jack/2, 0.0], 0.0)

# Define box walls relative to box center
g_box_wall1 = tf_matrix_sym([side_length_box/2, 0.0, 0.0], 0.0)
g_box_wall2 = tf_matrix_sym([0.0, -side_length_box/2, 0.0], 0.0)
g_box_wall3 = tf_matrix_sym([-side_length_box/2, 0.0, 0.0], 0.0)
g_box_wall4 = tf_matrix_sym([0.0, side_length_box/2, 0.0], 0.0)

# Jack corners relative to world frame
g_w_corner1 = g_w_jack @ g_jack_corner1
g_w_corner2 = g_w_jack @ g_jack_corner2
g_w_corner3 = g_w_jack @ g_jack_corner3
g_w_corner4 = g_w_jack @ g_jack_corner4

# Box walls relative to world frame
g_w_wall1 = g_w_box @ g_box_wall1
g_w_wall2 = g_w_box @ g_box_wall2
g_w_wall3 = g_w_box @ g_box_wall3
g_w_wall4 = g_w_box @ g_box_wall4

# Velocities of box and jack relative to world frame
vel_box = find_vb_sym(g_w_box)
vel_jack = find_vb_sym(g_w_jack)

# Inertia matrices for box and jack
I_box = find_inertia_matrix_sym(mass_box, J_box)
I_jack = find_inertia_matrix_sym(mass_jack, J_jack)

# Calculate total KE
KE_box = 0.5 * (vel_box.T) * I_box * vel_box
KE_jack = 0.5 * (vel_jack.T) * I_jack * vel_jack
KE = (KE_box + KE_jack)[0]

# Calculate total PE
PE_box = g * mass_box * y_box
PE_jack = g * mass_jack * y_jack
PE = PE_box + PE_jack

# Lagragian
L = KE - PE
L = sym.simplify(L)

# State variable
q = sym.Matrix([x_box, y_box, theta_box, x_jack, y_jack, theta_jack])
qdot = q.diff(t)
qddot = qdot.diff(t)

# Find dLdq and dLdqdot
dLdq = sym.Matrix([L]).jacobian(q)
dLdqdot = sym.Matrix([L]).jacobian(qdot)

# Eular Lagrange equations left hand side
el_lhs = dLdqdot.diff(t) - dLdq
el_lhs = el_lhs.T

# Calculate force matrix
F_y_box = (mass_box  + mass_jack) * g
F_theta_box = 1 * (mass_box * g)
F_matrix = sym.Matrix([0, F_y_box, F_theta_box, 0, 0, 0])

# Euler Lagrange Equations
el_eqns = sym.Eq(el_lhs, F_matrix)

# Solve for qddot
el_eqns_solved = sym.solve(el_eqns, qddot, dict=True)

# Define dummy variables for substitution
xb, yb, thetab, xj, yj, thetaj = sym.symbols(r'x_b, y_b, \theta_b, x_j, y_j, \theta_j')
dxb, dyb, dthetab, dxj, dyj, dthetaj = sym.symbols(r'\dot{x_b}, \dot{y_b}, \dot{\theta_b}, \dot{x_j}, \dot{y_j}, \dot{\theta_j}')

dummy_minus = {q[0]:xb, q[1]:yb, q[2]:thetab,
              q[3]:xj, q[4]:yj, q[5]:thetaj,
              qdot[0]:dxb, qdot[1]:dyb, qdot[2]:dthetab,
              qdot[3]:dxj, qdot[4]:dyj, qdot[5]:dthetaj}

dxb_p, dyb_p, dthetab_p, dxj_p, dyj_p, dthetaj_p = sym.symbols(r'\dot{x_b}^+, \dot{y_b}^+, \dot{\theta_b}^+, \dot{x_j}^+, \dot{y_j}^+, \dot{\theta_j}^+')

dummy_after_impact = {dxb:dxb_p, dyb:dyb_p, dthetab:dthetab_p,
               dxj:dxj_p, dyj:dyj_p, dthetaj:dthetaj_p}

dummy_plus = [dxb_p, dyb_p, dthetab_p,
               dxj_p, dyj_p, dthetaj_p]

# Transform between each box side and each jack corner
g_wall1_corner1 = inverse_se3_sym(g_w_wall1) @ g_w_corner1
g_wall1_corner2 = inverse_se3_sym(g_w_wall1) @ g_w_corner2
g_wall1_corner3 = inverse_se3_sym(g_w_wall1) @ g_w_corner3
g_wall1_corner4 = inverse_se3_sym(g_w_wall1) @ g_w_corner4
g_wall2_corner1 = inverse_se3_sym(g_w_wall2) @ g_w_corner1
g_wall2_corner2 = inverse_se3_sym(g_w_wall2) @ g_w_corner2
g_wall2_corner3 = inverse_se3_sym(g_w_wall2) @ g_w_corner3
g_wall2_corner4 = inverse_se3_sym(g_w_wall2) @ g_w_corner4
g_wall3_corner1 = inverse_se3_sym(g_w_wall3) @ g_w_corner1
g_wall3_corner2 = inverse_se3_sym(g_w_wall3) @ g_w_corner2
g_wall3_corner3 = inverse_se3_sym(g_w_wall3) @ g_w_corner3
g_wall3_corner4 = inverse_se3_sym(g_w_wall3) @ g_w_corner4
g_wall4_corner1 = inverse_se3_sym(g_w_wall4) @ g_w_corner1
g_wall4_corner2 = inverse_se3_sym(g_w_wall4) @ g_w_corner2
g_wall4_corner3 = inverse_se3_sym(g_w_wall4) @ g_w_corner3
g_wall4_corner4 = inverse_se3_sym(g_w_wall4) @ g_w_corner4

# Impact constraints for walls and jack corners
phi_wall1_corner1 = (g_wall1_corner1[0,3].subs(dummy_minus))
phi_wall1_corner2 = (g_wall1_corner2[0,3].subs(dummy_minus))
phi_wall1_corner3 = (g_wall1_corner3[0,3].subs(dummy_minus))
phi_wall1_corner4 = (g_wall1_corner4[0,3].subs(dummy_minus))
phi_wall2_corner1 = (g_wall2_corner1[1,3].subs(dummy_minus))
phi_wall2_corner2 = (g_wall2_corner2[1,3].subs(dummy_minus))
phi_wall2_corner3 = (g_wall2_corner3[1,3].subs(dummy_minus))
phi_wall2_corner4 = (g_wall2_corner4[1,3].subs(dummy_minus))
phi_wall3_corner1 = (g_wall3_corner1[0,3].subs(dummy_minus))
phi_wall3_corner2 = (g_wall3_corner2[0,3].subs(dummy_minus))
phi_wall3_corner3 = (g_wall3_corner3[0,3].subs(dummy_minus))
phi_wall3_corner4 = (g_wall3_corner4[0,3].subs(dummy_minus))
phi_wall4_corner1 = (g_wall4_corner1[1,3].subs(dummy_minus))
phi_wall4_corner2 = (g_wall4_corner2[1,3].subs(dummy_minus))
phi_wall4_corner3 = (g_wall4_corner3[1,3].subs(dummy_minus))
phi_wall4_corner4 = (g_wall4_corner4[1,3].subs(dummy_minus))

# Impact constraint matrix
phi_constraint = sym.Matrix([[phi_wall1_corner1], [phi_wall1_corner2], [phi_wall1_corner3], [phi_wall1_corner4],
                             [phi_wall2_corner1], [phi_wall2_corner2], [phi_wall2_corner3], [phi_wall2_corner4],
                             [phi_wall3_corner1], [phi_wall3_corner2], [phi_wall3_corner3], [phi_wall3_corner4],
                             [phi_wall4_corner1], [phi_wall4_corner2], [phi_wall4_corner3], [phi_wall4_corner4],])

# Lamdify qddot equations ans phi constraints
xddot_box_sol = sym.lambdify([q[0], q[1], q[2], q[3], q[4], q[5], qdot[0], qdot[1], qdot[2], qdot[3], qdot[4], qdot[5], t], el_eqns_solved[0][qddot[0]], modules = [np, sym], dummify=True)
yddot_box_sol = sym.lambdify([q[0], q[1], q[2], q[3], q[4], q[5], qdot[0], qdot[1], qdot[2], qdot[3], qdot[4], qdot[5], t], el_eqns_solved[0][qddot[1]], modules = [np, sym], dummify=True)
thetaddot_box_sol = sym.lambdify([q[0], q[1], q[2], q[3], q[4], q[5], qdot[0], qdot[1], qdot[2], qdot[3], qdot[4], qdot[5], t], el_eqns_solved[0][qddot[2]], modules = [np, sym], dummify=True)
xddot_jack_sol = sym.lambdify([q[0], q[1], q[2], q[3], q[4], q[5], qdot[0], qdot[1], qdot[2], qdot[3], qdot[4], qdot[5], t], el_eqns_solved[0][qddot[3]], modules = [np, sym], dummify=True)
yddot_jack_sol = sym.lambdify([q[0], q[1], q[2], q[3], q[4], q[5], qdot[0], qdot[1], qdot[2], qdot[3], qdot[4], qdot[5], t], el_eqns_solved[0][qddot[4]], modules = [np, sym], dummify=True)
thetaddot_jack_sol = sym.lambdify([q[0], q[1], q[2], q[3], q[4], q[5], qdot[0], qdot[1], qdot[2], qdot[3], qdot[4], qdot[5], t], el_eqns_solved[0][qddot[5]], modules = [np, sym], dummify=True)
phi_sols = sym.lambdify([[xb, yb, thetab, xj, yj, thetaj, dxb, dyb, dthetab, dxj, dyj, dthetaj]], phi_constraint, modules = [np, sym], dummify=True)

# Calculate Hamiltonian and t- and t+
H = (dLdqdot * qdot)[0] - L
H_subs_minus = H.subs(dummy_minus)
H_subs_plus = H_subs_minus.subs(dummy_after_impact)
dLdqdot_minus = dLdqdot.subs(dummy_minus)
dLdqdot_plus = dLdqdot_minus.subs(dummy_after_impact)
dphidq_minus = phi_constraint.jacobian([xb, yb, thetab, xj, yj, thetaj])
dphidq_plus = dphidq_minus.subs(dummy_after_impact)

# Define impact equations
impact_lhs = sym.simplify(sym.Matrix([dLdqdot_plus[0] - dphidq_minus[0],
                                      dLdqdot_plus[1] - dphidq_minus[1],
                                      dLdqdot_plus[2] - dphidq_minus[2],
                                      dLdqdot_plus[3] - dphidq_minus[3],
                                      dLdqdot_plus[4] - dphidq_minus[4],
                                      dLdqdot_plus[5] - dphidq_minus[5],
                                      H_subs_plus - H_subs_minus]))

impact_eqs = []
for i in range(phi_constraint.shape[0]):
    impact_rhs = sym.Matrix([lam * dphidq_minus[i, 0],
                            lam * dphidq_minus[i, 1],
                            lam * dphidq_minus[i, 2],
                            lam * dphidq_minus[i, 3],
                            lam * dphidq_minus[i, 4],
                            lam * dphidq_minus[i, 5],
                            0])
    impact_eqs.append(sym.Eq(impact_lhs, impact_rhs))

display(phi_constraint)
#print(len(phi_constraint))
#print(len(impact_eqs))
# display(g_w_jack)
# display(g_w_box)
# display(g_jack_corner3)
# display(g_box_wall3)
# display(g_w_corner3)
# display(g_w_wall3)
# display(g_wall3_corner3)

# Run simulation

# Simulation Paramters
sim_time = 15
dt = 0.01

tspan = [0, sim_time]
s0 = np.array([0, 0, 0, 3.5, 0, np.pi/3, 0, 0, 0, 0, 0, 0])

traj = simulate(dyn, s0, tspan, dt, integrate, phi_sols)

# Plot X, Y, and Theta for the box and the jack
plot(traj, tspan, dt)

print('\033[1m Shape of traj:', traj.shape)

# Animate!
animate_jack(traj, side_length_box, lengh_jack, sim_time)
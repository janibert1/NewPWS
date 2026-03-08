#!/usr/bin/env python
# coding: utf-8

# # Vortex Lattice Method

# ## Point Analysis

# In[ ]:


get_ipython().system('pip install "aerosandbox[full]"')


# In[ ]:


import aerosandbox as asb
import aerosandbox.numpy as np

wing_airfoil = asb.Airfoil("dae11")
tail_airfoil = asb.Airfoil("naca0012")
opti = asb.Opti()  # Initialize an optimization environment.
weight = 1.7
N = 4  # Number of chord sections to optimize
gravitycenter = opti.variable(init_guess=0.8)
fronttoback = 70.14 # van voorkant vleugel ding to zwaartepunt
# gravitycenter = 0.1337647
# The y-locations (i.e. span locations) of each section. Note that the span is fixed.
section_y = np.sinspace(0, 0.18, N, reverse_spacing=True)
chords = opti.variable(init_guess=np.ones(N) * 0.15) # All chords initially guessed as "1".
### Define the 3D geometry you want to analyze/optimize.
# Here, all distances are in meters and all angles are in degrees.
target_pitch_moment = 0  # Desired pitch moment (usually 0 for trim)
tolerance = 0.1 # Allowable deviation from the target
airplane = asb.Airplane(
    name="Peter's Glider",
    xyz_ref=[(0.040*(gravitycenter)+1.654*(0.065785))/(0.040+1.654), 0, -0.02366952],  # CG location
    wings=[
        asb.Wing(
            name="Main Wing",
            symmetric=True,  # Should this wing be mirrored across the XZ plane?
            xsecs=[  # The wing's cross ("X") sections
                asb.WingXSec(  # Root
                    xyz_le=[0, 0, 0],  # Coordinates of the XSec's leading edge, relative to the wing's leading edge.
                    chord=0.2,
                    twist=2.3,  # degrees
                    airfoil=wing_airfoil,  # Airfoils are blended between a given XSec and the next one.
                ),
                asb.WingXSec(  # Mid
                    xyz_le=[0, 0.5, 0],
                    chord=0.2,
                    twist=2.3,
                    airfoil=wing_airfoil,
                ),
                asb.WingXSec(  # Tip
                    xyz_le=[0, 1, 0.087],
                    chord=0.2,
                    twist=2.3,
                    airfoil=wing_airfoil,
                ),
            ]
        ),
        asb.Wing(
            name="Horizontal Stabilizer",
            symmetric=True,
           xsecs=[
               asb.WingXSec(
                   xyz_le=[
                       -0.25 * chords[i], # This keeps the quarter-chord-line straight.
                       section_y[i], # Our (known) span locations for each section.
                       section_y[i],
                   ],
                   chord=chords[i],
                   airfoil=asb.Airfoil("naca0012"),

               )
               for i in range(N)
           ]
          #   xsecs=[
          #       asb.WingXSec(
          #           xyz_le=[
          #               0, # This keeps the quarter-chord-line straight.
          #               0, # Our (known) span locations for each section.
          #               0,
          #           ],
          #           airfoil=asb.Airfoil("naca6412"),
          #           chord=0.15,
          #       ),
          #       asb.WingXSec(  # Mid
          #           xyz_le=[0, 0.2, 0.2],
          #           chord=0.15,
          #           airfoil=asb.Airfoil("naca6412"),
          #       )

          #  ]
        ).translate([gravitycenter-0.07014, 0, 0]),
    ],
    fuselages=[
        asb.Fuselage(
            name="Fuselage",
            xsecs=[
                asb.FuselageXSec(
                    xyz_c=[x-0.133, 0, -0.04 if x <=0.09 else 0.26*(x-0.09) -0.04 if x <= 0.18 and x > 0.09 else -0.006],  # Adjust z-coordinate for under-wing position
                    radius=0.03 if x <= 0.09 else
                    -0.26*(x-0.09)+0.03 if x <= 0.18 and x > 0.09 else
                    0.006

                )
                for x in np.linspace(0, 1.0, 100)
            ]
        )
    ]

)
for wing in airplane.wings:
    if wing.name == "Horizontal Stabilizer":
        wing1 = wing
        break  # Exit the loop once found


# In[ ]:


opti.subject_to([  # Let's add some sensible constraints.
    chords > 0,  # Chords should stay positive
    wing1.area() == 0.055,
    chords < 0.15, # We want some fixed wing area
    chords > 0.01,
    gravitycenter > 0
])
velocity = opti.variable(init_guess=8, lower_bound=5, upper_bound=12)
opti.subject_to(
    np.diff(chords) <= 0
    # The change in chord from one section to the next should be negative.
)
#alpha = opti.variable(init_guess=5, lower_bound=0, upper_bound=30)
vlm = asb.VortexLatticeMethod(
    airplane=airplane,
    op_point=asb.OperatingPoint(
        velocity = velocity,  # m/s
        alpha=0,  # degree
    )
)


# You can change the paneling by passing in various parameters to the `VortexLatticeMethod` constructor, or by using `analysis_specific_options` for various components (`Wing`, `WingXSec`, etc.) These options are viewable in the source code.

# In[ ]:


aero = vlm.run()  # Returns a dictionary
for k, v in aero.items():
    print(f"{k.rjust(4)} : {v}")


# In[ ]:


opti.minimize(aero["CD"])
opti.minimize(aero["M_g"][1])
opti.subject_to([
   aero["M_g"][1] > 0,
   aero["L"] > 9.81* weight
])


# In[ ]:


# NBVAL_SKIP
sol = opti.solve()
aero = sol(aero)
airplane = sol(airplane)
print(sol(gravitycenter))
for k, v in aero.items():
   print(f"{k.rjust(4)} : {v}")
airplane.draw_three_view()
print(sol(chords))
print(section_y)
print(sol(velocity))


# ## Operating Point Optimization

# In[ ]:


NBVAL_SKIP
# (This tells our unit tests to skip this cell, as it's a bit wasteful to run on every commit.)

opti = asb.Opti()

alpha = opti.variable(init_guess=5)

vlm = asb.VortexLatticeMethod(
    airplane=airplane,
    op_point=asb.OperatingPoint(
        velocity=25,
        alpha=alpha
    ),
    align_trailing_vortices_with_wind=False,
)

aero = vlm.run()

L_over_D = aero["CL"] / aero["CD"]

opti.minimize(-L_over_D)

sol = opti.solve()


# In[ ]:


# NBVAL_SKIP

best_alpha = sol(alpha)
print(f"Alpha for max L/D: {best_alpha:.3f} deg")


# ## Aerodynamic Shape Optimization
# 
# ### Minimum Induced Drag (Elliptical Wing)

# Let's do some aerodynamic shape optimization, using a classic problem:
# 
# Find the wing shape that minimizes induced drag, with the following assumptions:
# 
# * A fixed lift
# * A fixed wing area
# * A fixed wing span
# * An untwisted, uncambered, thin, planar wing
# * Inviscid, incompressible, irrotational, steady flow
# 
# The answer, as any good introductory aerodynamics textbook will teach, is a wing with an elliptical lift distribution. For an untwisted wing (in small angle approximation), this corresponds to an elliptical chord distribution.
# 
# Let's pose the problem in AeroSandbox, using the `VortexLatticeMethod` flow solver.

# In[ ]:


opti = asb.Opti()  # Initialize an optimization environment.

N = 16  # Number of chord sections to optimize

# The y-locations (i.e. span locations) of each section. Note that the span is fixed.
section_y = np.sinspace(0, 0.2, N, reverse_spacing=True)
# Using `sinspace` gives us better resolution near the wing tip.


# We'll use a simple rectangular wing as our initial guess.

# In[ ]:


chords = opti.variable(init_guess=np.ones(N)) # All chords initially guessed as "1".

wing = asb.Wing(
    symmetric=True,
    xsecs=[
        asb.WingXSec(
            xyz_le=[
                -0.25 * chords[i], # This keeps the quarter-chord-line straight.
                section_y[i], # Our (known) span locations for each section.
                section_y[i],
            ],
            chord=chords[i],
            airfoil=asb.Airfoil("dae11"),
        )
        for i in range(N)
    ]
)

airplane = asb.Airplane( # Make an airplane object containing only this wing.
    wings=[
        wing
    ]
)

opti.subject_to([  # Let's add some sensible constraints.
    chords > 0,  # Chords should stay positive
    wing.area() == 0.03,  # We want some fixed wing area
])


# Next, we'll add a constraint that requires the chord distribution to be monotonically decreasing, which is something we know from intuition. We can skip this constraint, but if we do, we need to have more than 1 VLM spanwise section per wing section in order to stabilize the solve (the optimization problem is less-well-posed otherwise, and hence can more easily "fall" into local minima).

# In[ ]:


opti.subject_to(
    np.diff(chords) <= 0 # The change in chord from one section to the next should be negative.
)


# We don't know the right angle of attack to get the desired lift coefficient a priori, so we'll make that an optimization variable too. Note the easy composability of aerodynamic shape optimization and operating point optimization.
# 
# Then, we set up and run the VLM solve.

# In[ ]:


alpha = opti.variable(init_guess=5, lower_bound=0, upper_bound=30)

op_point = asb.OperatingPoint(
    velocity=1, # Some fixed velocity; doesn't matter since we're working nondimensionally.
    alpha=alpha
)

vlm = asb.VortexLatticeMethod(
    airplane=airplane,
    op_point=op_point,
    spanwise_resolution=1,
    chordwise_resolution=8,
)

aero = vlm.run()


# Finally, we add our lift constraint, set the optimization objective to minimize drag, and solve.

# In[ ]:


# NBVAL_SKIP
# (This tells our unit tests to skip this cell, as it's a bit wasteful to run on every commit.)



opti.minimize(aero["CD"])

sol = opti.solve()


# Let's visualize our solution.
# 
# The following command does an in-place substitution of our VLM object, recursively evaluating all its fields from abstract values to concrete ones (i.e., NumPy arrays) at our solution, using our `sol` object.

# In[ ]:


# NBVAL_SKIP

vlm = sol(vlm)


# In[ ]:


# NBVAL_SKIP

vlm.draw(show_kwargs=dict(jupyter_backend="static"))


# Looking at our optimized solution, we can compare it to our known analytic solution (an elliptical lift distribution).

# In[ ]:


# NBVAL_SKIP

import matplotlib.pyplot as plt
import aerosandbox.tools.pretty_plots as p

fig, ax = plt.subplots()
plt.plot(
    section_y,
    sol(chords),
    ".-",
    label="AeroSandbox VLM Result",
    zorder=4,
)
y_plot = np.linspace(0, 1, 500)
plt.plot(
    y_plot,
    (1 - y_plot ** 2) ** 0.5 * 4 / np.pi * 0.125,
    label="Elliptic Distribution",
)
p.show_plot(
    "AeroSandbox Drag Optimization using VortexLatticeMethod",
    "Span [m]",
    "Chord [m]"
)


# Slight differences arise due to numerical discretization, but it's convergent to the right answer. We can also check the objective function (the induced drag at the minimum):

# In[ ]:


# NBVAL_SKIP

AR = 2 ** 2 / 0.25
CL = 1

CDi_theory = CL ** 2 / (np.pi * AR)
CDi_computed = sol(aero["CD"])
print(f"CDi (theory)   : {CDi_theory:.4f}")
print(f"CDi (computed) : {CDi_computed:.4f}")


# Essentially matching theory. Both theory and computation are expected to have slight errors compared to the exact potential flow solution:
# 
# * The theory side has small errors due to small-angle approximations and simplification of 3D chordwise effects near the tips
# * The computational side has small errors due to numerical discretization.
# 
# (Both methods neglect thickness effects, too.)

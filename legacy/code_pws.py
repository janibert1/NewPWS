#!/usr/bin/env python
# coding: utf-8

# # Vleugelprofiel optimalisatie mbv aerosandbox and neuralfoil
# 
# Hierin staat de code die wij hebben gemaakt om het vleugelprofiel voor ons vliegtuig te optimaliseren. We hebben hieruit delen van de code uit de (tutorial van aersandbox) gebruikt. Vervolgens is er met www.airfoiltools.com het meest vergelijkbare vleugelprofiel opgezocht, omdat het neuralfoil programma nog niet perfect is en ook omdat het anders vrijwel onmogelijk was het profiel in onshape te importeren. Hieruit is dit stuk code gevolgd:

# In[ ]:


import aerosandbox as asb
import aerosandbox.numpy as np
import matplotlib.pyplot as plt
import aerosandbox.tools.pretty_plots as p
import aerosandbox.aerodynamics.aero_2D as aero_2D


# Dit zijn alle parameters die al vast staan zoals vleugeloppervlak en de luchtsnelheid waarvoor er 6 m/s is gebruikt. Zonder nog meer constraints waarvoor er geen tijd genoeg was om ze te meten is het niet mogelijk om de optimale snelheid te bereken zonder dat je in een loop komt. Hoe sneller je gaat hoe lager de CL kan zijn waardoor de CD ook lager word. Zo komt het programma er dus nooit uit zonder extra parameters.

# In[ ]:


# Doel CL waarden voor verschillende puntmetingen
CL_multipoint_targets = np.array([0.8, 1.0, 1.2, 1.4, 1.5, 1.6])

# Gewicht van de CL waarden voor gewogen gemiddelde
CL_multipoint_weights = np.array([5, 6, 7, 8, 9, 10])

wing_area = 3 * 0.20  # Oppervlakte van de vleugel in m²
CD_fuselage = 0.1  # Weerstandscoëfficiënt van de romp
density = 1.23  # Dichtheid van lucht [kg/m³]
drag_area_fuselage = 1621.05733 * 1e-6  # Rompweerstandsoppervlak [m²]
lift_cruise = 1.1 * 9.81  # Lifterm voor kruissnelheid
airspeed = 6  # Lucht snelheid in m/s
mach = airspeed * 0.00291545  # Mach getal
dynamic_pressure = 0.5 * density * airspeed ** 2  # Dynamische druk
CL = lift_cruise / (dynamic_pressure * wing_area)  # Coëfficiënt van lift
Re = 500e3 * (CL_multipoint_targets / CL) ** -0.5  # Reynolds getal


# optimalisatie initiatie van het vleugelprofiel

# In[ ]:


# Eerste gok luchtfoilm profiel (NACA0012)
initial_guess_airfoil = asb.KulfanAirfoil("naca0012")
initial_guess_airfoil.name = "Initiële Schatting (NACA0012)"

opti = asb.Opti()


# Vervolgens word hier het optimalisatie process beschreven met de parameters die aan het begin zijn geschreven.

# In[ ]:


# Geoptimaliseerd luchtfoilm profiel
optimized_airfoil = asb.KulfanAirfoil(
    name="Geoptimaliseerd",
    lower_weights=opti.variable(
        init_guess=initial_guess_airfoil.lower_weights,
        lower_bound=-0.5,
        upper_bound=0.25,
    ),
    upper_weights=opti.variable(
        init_guess=initial_guess_airfoil.upper_weights,
        lower_bound=-0.25,
        upper_bound=0.5,
    ),
    leading_edge_weight=opti.variable(
        init_guess=initial_guess_airfoil.leading_edge_weight,
        lower_bound=-1,
        upper_bound=1,
    ),
    TE_thickness=0,  # Dikte van de achterrand
)

# Variable voor aanvalshoek
alpha = opti.variable(
    init_guess=np.degrees(CL_multipoint_targets / (2 * np.pi)),
    lower_bound=-5,
    upper_bound=18
)

# Berekening van aerodynamische eigenschappen met NeuralFoil
aero = optimized_airfoil.get_aero_from_neuralfoil(
    alpha=alpha,
    Re=Re,
    mach=mach,
)

# Opgestelde voorwaarden voor optimalisatie
opti.subject_to([
    aero["analysis_confidence"] > 0.90,  # Minimale analyse zekerheid
    aero["CL"] == CL_multipoint_targets,  # Doel CL waarden
    np.diff(alpha) > 0,  # Aanvalshoek stijgend
    aero["CM"] >= -0.133,  # Koppelcoëfficiënt
    optimized_airfoil.local_thickness(x_over_c=0.33) >= 0.128,  # Dikte van de vleugel bij 33% van het koorde
    optimized_airfoil.local_thickness(x_over_c=0.90) >= 0.014,  # Dikte van de vleugel bij 90% van het koorde
    optimized_airfoil.TE_angle() >= 6.03, # Wijziging van Drela's 6.25 om te matchen met DAE-11 case
    optimized_airfoil.lower_weights[0] < -0.05,  # Gewicht lager dan -0.05
    optimized_airfoil.upper_weights[0] > 0.05,  # Gewicht hoger dan 0.05
    optimized_airfoil.local_thickness() >0   # Dikte van de vleugel
])

# Functie om de wiggliness van luchtfoilm te berekenen
get_wiggliness = lambda af: sum([
    np.sum(np.diff(np.diff(array)) ** 2)
    for array in [af.lower_weights, af.upper_weights]
])

# Meer voorwaarden voor optimalisatie
opti.subject_to(
    get_wiggliness(optimized_airfoil) < 2 * get_wiggliness(initial_guess_airfoil)
)

# Minimaliseren van het gemiddelde van de luchtweerstand
opti.minimize(np.mean(aero["CD"] * CL_multipoint_weights))

# Oplossen van het optimalisatieprobleem
sol = opti.solve(
    behavior_on_failure="return_last",
    options={
        "ipopt.mu_strategy": 'monotone',
        "ipopt.start_with_resto": 'yes'
    }
)


# Hier wordt uiteindelijk het hele zaakje in grafieken gezet.

# In[ ]:


# Ophalen van het geoptimaliseerde luchtfoilm profiel
optimized_airfoil = sol(optimized_airfoil)

# Berekening van de aerodynamische eigenschappen
aero = sol(aero)
print(f"Airspeed: {airspeed}")
print(f"Cl: {CL}")

# Plot van het geoptimaliseerde luchtfoilm profiel
optimized_airfoil.draw(
    draw_mcl=True,  # Toon de gemiddelde lijn van camber
    backend="matplotlib",  # Gebruik Matplotlib voor plotting
    show=True  # Toon de plot
)
# NBVAL_SKIP




# We hebben drie profielen laten weergeven om het verschil te laten zien. De blauwe is degene die is geoptimaliseerd door Neuralfoil de rode is degene die we uiteindelijk hebben gebruikt en de groene is degene die bij het eerste prototype is gebruikt. En dan word de CD versus de CL geprojecteerd berekent met Neuralfoil. De lijn is een projectie van de snelheid dus hoeverder de lijn op hoe hoger de snelheid

# In[ ]:


# Instellingen voor de grafieken
import matplotlib.pyplot as plt
import aerosandbox.tools.pretty_plots as p

Re_plot = 500e3

# Setup voor twee subplots
fig, ax = plt.subplots(2, 1, figsize=(7, 8))

# Luchtfoil profielen en kleuren
airfoils_and_colors = {
    initial_guess_airfoil.name       : (initial_guess_airfoil, "dimgray"),
    "NeuralFoil-Geoptimaliseerd": (optimized_airfoil, "blue"),
    "Vergelijkbaar profiel (DAE-11)": (asb.Airfoil("dae11"), "red"),
    "Eerste gok voor vliegtuig (NACA6409)": (asb.Airfoil("naca6409"), "green")
}

for i, (name, (af, color)) in enumerate(airfoils_and_colors.items()):
    # Lichtheid van de kleur aanpassen
    color = p.adjust_lightness(color, 1)
    # Tekenen van luchtfoilm profiel
    ax[0].fill(
        af.x(), af.y(),
        facecolor=(*color, 0.05),
        edgecolor=(*color, 0.9),
        linewidth=1,
        label=name,
        linestyle=(3 * i, (7, 2)),
        zorder=4 if "NeuralFoil" in name else 3,
    )
    # Berekening van aerodynamische eigenschappen
    aero = af.get_aero_from_neuralfoil(
         alpha=np.linspace(0, 15, 500),
         Re=Re_plot,
         mach=mach,
    )
        # Plot van CD versus CL
    ax[1].plot(
        aero["CD"], aero["CL"],  #"--",
        color=color, alpha=0.7,
        label=name,
        zorder=4 if "NeuralFoil" in name else 3,
    )
# Instellingen voor de eerste grafiek (Vleugelprofielen)
ax[0].legend(fontsize=11, loc="lower right", ncol=len(airfoils_and_colors)//2)
ax[0].set_title("Vleugelprofielen")
ax[0].set_xlabel("$x/c$")
ax[0].set_ylabel("$y/c$")
ax[0].axis('equal')

# Instellingen voor de tweede grafiek (CL-CD-polairen)
ax[1].legend(fontsize=11, loc="lower right", ncol=len(airfoils_and_colors)//2)
ax[1].set_title(f"Aerodynamische Polairen (geanalyseerd met Neuralfoil, $\\mathrm{{Re}}=500\\mathrm{{k}}$)")
ax[1].set_xlabel("Weerstandscoëfficiënt $C_D$")
ax[1].set_ylabel("Liftcoëfficiënt\n$C_L$")
ax[1].set_xlim(0, 0.04)
ax[1].set_ylim(0, 1.8)

# Toon de plot
p.show_plot("CL - CD-plot van verschillende vleugelprofielen", legend=False)


# En het geheel dan nog naar een .dat file exporteren.

# In[ ]:


# Opslaan van het geoptimaliseerde luchtfoilm profiel in een .dat bestand
file_path = "optimized_airfoil.dat"
optimized_airfoil.write_dat(file_path)


# # Voorspelling solar input en batterij
# 
# eerst declareren we een paar constanten

# In[ ]:


import aerosandbox as asb
import aerosandbox.numpy as np
import matplotlib.pyplot as plt

# Constanten
density = 1.225  # Luchtdichtheid [kg/m^3]
g = 9.81  # Zwaartekrachtsversnelling [m/s^2]
wing_area = 3 * 0.2  # Vleugeloppervlak [m^2] (3 m spanwijdte, 0.2 m koorde)
weight = 1.1  # Gewicht vliegtuig [kg]
solar_panel_power = 21 * 3  # Totaal vermogen van zonnepanelen [W]
mppt_efficiency = 0.93  # Maximum Power Point Tracking efficiëntie
Re = 500e3  # Representatief Reynoldsgetal

# Batterij parameters
battery_capacity_mah = 800  # Batterijcapaciteit in mAh
battery_voltage = 11.1  # Nominale spanning voor 3S LiPo
battery_capacity_wh = battery_capacity_mah / 1000 * battery_voltage  # Capaciteit in Wattuur
battery_charge_level = 0.0 # Begin laadpercentage
battery_full_charge = 1.0 # Volledig laadpercentage
battery_empty_charge = 0.0 # Leeg laadpercentage
battery_efficiency = 0.90 # Laadefficiëntie


# Hier wordt met een versimpeld model de benodigde energie berekent om het model voortelaten bewegen.

# In[ ]:


# Laad het airfoil
airfoil = asb.Airfoil("dae11")

# Functie om het benodigde vermogen voor horizontale vlucht te berekenen
def calculate_power_required(airspeed):
    """
    Berekent het benodigde vermogen voor horizontale vlucht bij een gegeven luchtsnelheid.

    Args:
        airspeed: Lucht snelheid [m/s]

    Returns:
        Benodigde vermogen [W]
    """
    CL = weight * g / (0.5 * density * airspeed**2 * wing_area)  # Liftcoëfficiënt
    Re_local = density * airspeed * 0.2 / 1.5e-5  # Reynoldsgetal (koorde = 0.2 m, luchtviscositeit = 1.5e-5 Pa·s)

    # Haal aerodynamische data op van NeuralFoil
    aero = airfoil.get_aero_from_neuralfoil(alpha=np.linspace(-10, 20, 100), Re=Re_local)
    CL_array = aero["CL"]
    CD_array = aero["CD"]

    # Interpolateer CD corresponderend met de berekende CL
    CD_induced = np.interp(CL, CL_array, CD_array)

    # Parasitaire weerstandscoëfficiënt
    CD_parasite = 0.1  # Schatting voor romp, etc.

    # Totale weerstandscoëfficiënt
    CD_total = CD_induced + CD_parasite

    # Weerstandskracht en benodigd vermogen
    drag_force = 0.5 * density * airspeed**2 * wing_area * CD_total
    power_required = drag_force * airspeed
    return power_required


# Hier wordt de  solar input berekent

# In[ ]:


# Genereer data voor winterdagen
days = 1
time = np.linspace(0, 24 * days, 1000 * days)  # Tijd in uren

# Winter solar irradiance simulation (shorter day, lower intensity)
peak_irradiance = 700 #Reduced peak irradiance for winter
daylight_start = 8  # Daylight starts at 8:00 AM
daylight_end = 16  # Daylight ends at 4:00 PM
solar_irradiance = np.maximum(peak_irradiance * np.sin(np.pi * (time % 24 - daylight_start) / (daylight_end - daylight_start)), 0)  # W/m^2

solar_efficiency = solar_panel_power * mppt_efficiency

power_input = solar_irradiance * solar_efficiency / 1000  # Ingangsvermogen in watt
power_output = []
battery_level = []


# Hier wordt het batterij laden berekent.

# In[ ]:


for i,t in enumerate(time):
    airspeed = 6  # Neem een constante luchtsnelheid van 10 m/s aan
    power_out = calculate_power_required(airspeed)
    power_output.append(power_out)

    #Bereken beschikbaar vermogen, laad alleen op als de batterij niet vol is
    power_available = power_input[i]
    if battery_charge_level < battery_full_charge:
        if power_available > power_out:
            power_delta = (power_available - power_out) * battery_efficiency
        else:
            power_delta = power_available - power_out
    else:
         power_delta = power_available - power_out

    # Bereken verandering in batterij laadniveau (converteer vermogen naar Wattuur)
    dt = (time[1]-time[0]) if i>0 else 0
    battery_change_wh = power_delta * dt
    battery_change_percentage = battery_change_wh / battery_capacity_wh

    # Update batterij laadniveau
    battery_charge_level += battery_change_percentage
    battery_charge_level = np.clip(battery_charge_level,battery_empty_charge,battery_full_charge) # Beperk tot grenzen
    battery_level.append(battery_charge_level)



# En dan in de grafiek.

# In[ ]:


# Plot de resultaten
plt.figure(figsize=(12, 6))
plt.plot(time, power_input, label="Ingangsvermogen (Zonnepanelen) [W]", color="orange")
plt.plot(time, power_output, label="Benodigd Vermogen (Horizontale Vlucht) [W]", color="blue")
plt.axhline(solar_panel_power, linestyle="--", color="red", label="Maximaal Zonne-energie [W]")
plt.plot(time, np.array(battery_level) * 100, label="Batterij Laadniveau [%]", color="green")
plt.xlabel("Tijd [uren]")
plt.ylabel("Vermogen [W] / Batterij [%]")
plt.title("Ingangs-/Uitgangsvermogen en Batterij Laadniveau Gedurende Één Dag")
plt.legend()
plt.grid(True)
plt.show()


# In[ ]:


get_ipython().system('pip install aerosandbox[full]')


class Constants:
    # Neutron simulation constants
    energy_thermalise = 18.2 #Ratio = ln(E_f/E_t)
    f_neut_v = 1.2e7 #m/s of fast neut
    t_neut_v = 2.2e3 #m/s of slow neut
    res_esc_prob = 0.849 #probability of neutron absorption during moderation
    non_leak_prob = 0.849 #probability of neutron escaping reactor
    # Fission constants
    neut_prod = 2.43 #neut/fission
    d_neut_factor = 0.01 #d_neut/fission
    fission_energy=3.2e-11 #energy (J) released per fission
    d_neut_hf = 9.0 #d_neut half life (s)
    # Poison constants
    i135_hf = 6.5 #I-135 half life (h)
    xe135_hf = 9.0 #Xe-135 half life (h)
    i135_prod = 0.065
    xe135_prod = 0.003
    # Fluid constants
    compressibility = 1.15e-9 #Compressibility of water (285c+7Mpa), Pa^-1
    # Other
    grav = 9.8 #m/s^2

class Dimensions:
    diameter = 12 #m int
    height = 7 #m int

    hydr_diam = 0.00837 #m Hydraulic diameter of coolant channels
    f_sa = 12.0 # Surface area of fuel rods (radially) per m^2
    clad_length = 0.01 # Length between fuel and coolant, of cladding (m)
    mod_frac = 0.91 # Fraction of moderator in whole reactor
    f_fuel_frac = 0.04 # Fraction of fuel in whole reactor
    channel_frac = 0.04 # Fraction of coolant in whole reactor
    f_struc_frac = 0.01 # Fraction of structure in whole reactor

class Isotope:
    def __init__(self, atomic_density, thermal_absorption_cs, thermal_interaction_cs, fast_absorption_cs, fast_interaction_cs, interaction):
        self.atomic_density = atomic_density #atoms/cm^3
        self.thermal_absorption_cs = thermal_absorption_cs #cross section in cm^2
        self.thermal_interaction_cs = thermal_interaction_cs #Interaction = fission or scattering
        self.fast_interaction_cs = fast_interaction_cs
        self.fast_absorption_cs = fast_absorption_cs
        self.interaction = interaction

class Material:
    def __init__(self, density, conductivity, heat_capacity, latent_heat):
        self.density = density #t/m^3
        self.conductivity = conductivity #W/mK
        self.heat_capacity = heat_capacity #J/KgK
        self.latent_heat = latent_heat #J/Kg

class Moderator:
    H = 1.0
    C = 0.158


U235 = Isotope(
    7.2E20,
    680.0e-24,
    585.0e-24,
    2.0e-24,
    1.2e-24,
    "fission"
)

U238 = Isotope(
    2.33E22,
    2.7e-24,
    0.0,
    0.30e-24,
    0.0,
    None
)

H = Isotope(
    6.7E22,
    0.33e-24,
    20.0e-24,
    0.001e-24,
    20.0e-24,
    "scatter"
)

XE = Isotope(
    1.0E18,
    2.6e-18,
    5.0e-24,
    0.0,
    5.0e-24,
    None
)

B = Isotope(
    1.0E20,
    3837.0e-24,
    4.0e-24,
    5.0e-24,
    4.0e-24,
    None
)

C = Isotope(
    9.0E22,
    3.5e-27,
    4.8e-24,
    1.0e-27,
    4.8e-24,
    "Scatter"
)

Isotopes = {
    "U235": U235,
    "U238": U238,
    "H": H,
    "XE": XE,
    "B": B,
    "C": C
}

UO2 = Material(
    10.9,
    2.5,
    270.0,
    270000
)

H2O = Material(
    1.0,
    0.6,
    4180.0,
    2260000
)

ZR = Material(
    6.5,
    16.0,
    285.0,
    224000
)

GR = Material(
    1.6,
    100.0,
    710.0,
    59000000
)

Materials = {
    "UO2": UO2,
    "H2O": H2O,
    "ZR": ZR,
    "GRAPHITE":GR
}
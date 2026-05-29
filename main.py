import math
import time
import numpy as np
import values
from pyXSteam.XSteam import XSteam
steamTable = XSteam(XSteam.UNIT_SYSTEM_BARE)

tiles={}
prob={}
sim_step = 10 #ms Timestep between ticks in simulation
calc_step = 0.01 #ms Timestep between neutron calculation steps (factor of sim_step)
dt = sim_step / 1000
ct = calc_step / 1000
calc_no = dt/ct
warp = 1 # Accelerates/Slows all processes in reactor. Do not put too high (0.1-100)
H_atom_density = values.H.atomic_density
coolant_frac = values.Dimensions.f_coolant_frac


class Tile:
    def __init__(self, x, y, z, temp, pressure, void, t_neut_flux, f_neut_flux, fiss_rate, fuel_temp, fuel_e, clad_temp, coolant_temp):
        self.x = x
        self.y = y
        self.z = z
        self.temp = temp
        self.pressure = pressure
        self.void = void
        self.t_neut_flux = t_neut_flux
        self.f_neut_flux = f_neut_flux
        self.fiss_rate = fiss_rate
        self.fuel_temp = fuel_temp
        self.fuel_e = fuel_e
        self.clad_temp = clad_temp
        self.coolant_temp = coolant_temp

rad=int(values.Dimensions.diameter/2)
for x in range(-rad,rad):
    for y in range(-rad,rad):
        if ((((x+0.5)**2)+((y+0.5)**2))**0.5)<=rad:
            for z in range(0,int(values.Dimensions.height)):
                tiles[(x,y,z)] = Tile(x, y, z, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

def ComputeMacroCS(collision, Isotope, volume_frac, density=None): #Calculates macroscopic cross section of desired isotope
    if density == None:
        density = Isotope.atomic_density
    if collision == "absorption":
        t_neut_int = density * Isotope.thermal_absorption_cs * volume_frac
        f_neut_int = density * Isotope.fast_absorption_cs * volume_frac
    elif collision == "interaction":
        t_neut_int = density * Isotope.thermal_interaction_cs * volume_frac
        f_neut_int = density * Isotope.fast_interaction_cs * volume_frac
    return t_neut_int, f_neut_int

def ComputeHfMult(half_life, dt, warp): #Calculates multiplier to get desired half life
    hf = 0.5**(1/(half_life * (1/dt/warp)))
    return hf

def ComputeTemp(energy, material, fraction):
    temp = energy/(material.heat_capacity*material.density*1000*fraction)
    return temp

def clamp(value,min,max):
    if value>max:
        value=max
    elif value<min:
        value=min
    return value

#Variable definitions (Probably remove later)
f_neut=1e7
t_neut=5e9
d_neut=0
rod_ins=0.00
fission_rate=0
prev_neut_flux=10000
fuel_e=0
xe135=0
i135=0
cool_e=0
enthalpy=0
cool_temp=0
prev_temp=0
pres=7
steam_mass=0
water_mass=0

print(steamTable.tsat_p(pres)-273.15)

while True:
    bp=steamTable.tsat_p(pres)-273.15

    d_hf = ComputeHfMult(values.Constants.d_neut_hf, dt, warp)
    xe135_hf = ComputeHfMult(values.Constants.xe135_hf*3600, dt, warp)
    i135_hf = ComputeHfMult(values.Constants.i135_hf*3600, dt, warp)

    f_neut=5e6
    t_neut=1e9
    start = time.time()
    vol=(math.pi * (values.Dimensions.diameter/2)**2 * values.Dimensions.height)*1000**3.0
    f_abs,t_abs = 0,0
    prob = {}

    # Total isotope neutron absorption calculation
    f_abs_total_rate=0
    t_abs_total_rate=0
    for Name, Isotope in values.Isotopes.items():
        if Name in ["U235", "U238"]:
            volume_frac = values.Dimensions.f_fuel_frac
        elif Name=="H":
            volume_frac = values.Dimensions.f_coolant_frac
        elif Name=="C":
            volume_frac = values.Dimensions.mod_frac
        elif Name=="B":
            volume_frac = rod_ins
        elif Name=="XE":  
            volume_frac = 1.0
        else:
            volume_frac = 0
        if Name=="XE":
            density=xe135
        else:
            density=None
        f_abs_rate=ComputeMacroCS("absorption", Isotope, volume_frac, density)[1]*values.Constants.f_neut_v
        t_abs_rate=ComputeMacroCS("absorption", Isotope, volume_frac, density)[0]*values.Constants.t_neut_v
        f_abs_total_rate += f_abs_rate
        t_abs_total_rate += t_abs_rate

    # Neutron moderation
    scatter_c = ComputeMacroCS("interaction", values.C, values.Dimensions.mod_frac)[1]*values.Constants.f_neut_v
    scatter_h = ComputeMacroCS("interaction", values.H, coolant_frac, H_atom_density)[1]*values.Constants.f_neut_v
    e_loss = scatter_c*values.Moderator.C + scatter_h*values.Moderator.H
    therm_rate=e_loss/values.Constants.energy_thermalise
    # Fission
    fission_rate = ComputeMacroCS("interaction", values.U235, values.Dimensions.f_fuel_frac)[0]*values.Constants.t_neut_v
    fission_neut = fission_rate*values.Constants.neut_prod*(1-values.Constants.d_neut_factor)
    # Computing affects of absorption/moderation/fission on neutron population
    f_neut+=d_neut*(1-d_hf)
    d_neut*=d_hf #Delayed neut decay
    a = 1 + (-f_abs_total_rate - therm_rate)*ct #Effect of fast neutrons on fast neutron pop
    b = (fission_neut*values.Constants.non_leak_prob)*ct #Effect of thermal neutrons on fast neutron pop
    c = 1 + (-t_abs_total_rate)*ct #Effect of thermal neutrons on thermal neutron pop
    d = (therm_rate*values.Constants.non_leak_prob*values.Constants.res_esc_prob)*ct #Effect of fast neutrons on thermal neutron pop
    e = fission_rate*values.Constants.non_leak_prob*ct #Effect of thermal neurtons on fission
    # Inital values matrix
    m = np.array([
        [a, b, 0],
        [d, c, 0],
        [0, e, 1]
    ], dtype=float)
    # Initial neutron populations
    p=0
    v0 = np.array([
        f_neut,
        t_neut,
        p
    ], dtype=float)
    # Compute new neut populations
    vN = np.linalg.matrix_power(m, int(calc_no*warp)) @ v0
    f_neut = float(vN[0])
    t_neut = float(vN[1])
    p = float(vN[2])
    # Reactor poison calculations
    macro_xe=ComputeMacroCS("absorption", values.XE, 1.0, xe135)[0]*values.Constants.t_neut_v
    macro_fis=ComputeMacroCS("interaction", values.U235, values.Dimensions.f_fuel_frac)[0]*values.Constants.t_neut_v
    int_xe=p*(macro_xe/macro_fis)
    xe135-=int_xe
    xe135 += p*values.Constants.xe135_prod
    i135 += p*values.Constants.i135_prod
    i135*=i135_hf
    xe135*=xe135_hf
    # Energy calculations
    d_neut+=(p*values.Constants.neut_prod*values.Constants.d_neut_factor) #delayed neutron gain
    fuel_e+= (p*values.Constants.fission_energy*10e6)
    req_sense=(bp)*values.H2O.heat_capacity*values.H2O.density*1000*coolant_frac
    req_latent=values.H2O.latent_heat*values.H2O.density*1000*coolant_frac
    latent_e=clamp(enthalpy-req_sense,0,req_latent)
    sens_e=enthalpy-latent_e
    steam=latent_e/req_latent



    # Material temp updates
    fuel_temp = ComputeTemp(fuel_e, values.UO2, values.Dimensions.f_fuel_frac)
    cool_temp = ComputeTemp(sens_e, values.H2O, values.Dimensions.f_coolant_frac)
    #clad_temp = struc_e/(values.ZR.heat_capacity*values.ZR.density*1000*values.Dimensions.f_struc_frac)
    #mod_temp = mod_e/(values.GR.heat_capacity*values.GR.density*1000*values.Dimensions.mod_frac)
    #print("ENTH",enthalpy, bp-273.15)
    #print("REQ",req_latent,req_sense)
    prev_temp=cool_temp

    # Material energy transfers
    cool_temp=0
    f_c_transfer=((fuel_temp-cool_temp)/values.Dimensions.clad_length)*values.ZR.conductivity*values.Dimensions.f_sa*dt*warp
    fuel_e-=f_c_transfer
    enthalpy+=f_c_transfer
    end=time.time()
    time.sleep(dt)
    neut_flux=(f_neut+t_neut)
    prev_neut_flux=neut_flux
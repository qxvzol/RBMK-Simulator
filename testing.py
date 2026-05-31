import time

from scipy.optimize import fsolve
from pyXSteam.XSteam import XSteam

import values
steamTable = XSteam(XSteam.UNIT_SYSTEM_BARE)

net_volume=1
water_mass=100
vapour_mass=30
p_pump=0.3

tiles={}


class Tile:
    def __init__(self, x, y, z, fuel_e=0, clad_e=0, coolant_e=0, graph_e=0, pressure=7, void=0, t_neut_density=0, f_neut_density=0, fiss_rate=0, mass_v=0, mass_l=40, momentum_density=0):
        #Dimensions
        self.x = x #m
        self.y = y #m
        self.z = z #m
        #Energy
        self.fuel_e = fuel_e #J
        self.clad_e = clad_e #J
        self.coolant_e = coolant_e #J
        self.graph_e = graph_e #J

        self.pressure = pressure #MPa
        self.void = void #0-1
        self.t_neut_flux = t_neut_density # neut/m^3
        self.f_neut_density = f_neut_density # neut/m^3
        self.fiss_rate = fiss_rate #fissions/s
        self.mass_v = mass_v #kg
        self.mass_l = mass_l #kg
        self.momentum_density = momentum_density #kg/m^3

for z in range(0,7):
    tiles[(1,1,z)] = Tile(1,1,z)

def clamp(value,min,max):
    if (value>max) and max!=None:
        value=max
    elif value<min and min!=None:
        value=min
    return value


def f(pressure):
    pressure=pressure[0]
    pressure=clamp(pressure,0.1,22)
    error=(steamTable.vL_p(pressure)*water_mass)+(steamTable.vV_p(pressure)*vapour_mass)-net_volume
    return error

def ComputeTemp(energy, material, fraction, shc=None):
    if shc!=None:
        temp = energy/(shc*material.density*1000*fraction)
    else:
        temp = energy/(material.heat_capacity*material.density*1000*fraction)
    return temp

# Sets inital temperatures
for tile in tiles.values():
    tile.fuel_e=values.UO2.heat_capacity*values.UO2.density*1000*values.Dimensions.f_fuel_frac*(values.Constants.inital_temp+273.15)
    tile.clad_e=values.ZR.heat_capacity*values.ZR.density*1000*values.Dimensions.f_struc_frac*(values.Constants.inital_temp+273.15)
    tile.coolant_e=values.H2O.heat_capacity*values.H2O.density*1000*values.Dimensions.channel_frac*(values.Constants.inital_temp+273.15)
    tile.graph_e=values.GR.heat_capacity*values.GR.density*1000*values.Dimensions.mod_frac*(values.Constants.inital_temp+273.15)

cool_temp=293.15+100

"""
while True:
    tile=tiles[(1,1,z)]
    baseline_pressure=7
    #water_shc = steamTable.Cp_pt(7, cool_temp)*1000 NEEDS FIXING
    water_shc = 4850
    water_shc=clamp(water_shc,2500,5500)

    # Water boiling/temperature calculations
    channel_frac=values.Dimensions.channel_frac
    enthalpy=tile.coolant_e
    bp=steamTable.tsat_p(baseline_pressure)
    req_sense=(bp)*water_shc*values.H2O.density*1000*channel_frac
    req_latent=values.H2O.latent_heat*values.H2O.density*1000*channel_frac
    latent_e=clamp(enthalpy-req_sense,0,req_latent)
    sens_e=enthalpy-latent_e
    steam=latent_e/req_latent
    cool_temp = ComputeTemp(sens_e, values.H2O, values.Dimensions.channel_frac, shc=water_shc)

    # Calculates temperatures based on enthalpy
    fuel_temp = ComputeTemp(tile.fuel_e, values.UO2, values.Dimensions.f_fuel_frac)
    clad_temp = ComputeTemp(tile.clad_e, values.ZR, values.Dimensions.f_struc_frac)
    graph_temp = ComputeTemp(tile.graph_e, values.GR, values.Dimensions.mod_frac)

    # Thermal conduction
    thermal_conductance_fc = values.Dimensions.fuel_clad_contact/(1/values.UO2.conductivity+1/values.ZR.conductivity)
    fuel_clad_q = values.Constants.heat_constant*thermal_conductance_fc*(fuel_temp-clad_temp)
    fuel_clad_q = clamp(fuel_clad_q, -tile.clad_e/(values.Constants.sim_step/1000), tile.fuel_e/(values.Constants.sim_step/1000))
    thermal_conductance_cc = values.Dimensions.clad_cool_contact/(1/values.ZR.conductivity+1/values.H2O.conductivity)
    clad_cool_q = values.Constants.heat_constant*thermal_conductance_cc*(clad_temp-cool_temp)
    thermal_conductance_cg = values.Dimensions.cool_graph_contact/(1/values.H2O.conductivity+1/values.GR.conductivity)
    cool_graph_q = values.Constants.heat_constant*thermal_conductance_cg*(cool_temp-graph_temp)

    tile.fuel_e-=fuel_clad_q*values.Constants.sim_step/1000
    tile.clad_e+=fuel_clad_q*values.Constants.sim_step/1000

    tile.clad_e-=clad_cool_q*values.Constants.sim_step/1000
    tile.coolant_e+=clad_cool_q*values.Constants.sim_step/1000

    tile.coolant_e-=cool_graph_q*values.Constants.sim_step/1000
    tile.graph_e+=cool_graph_q*values.Constants.sim_step/1000

    tile.fuel_e+=1e5

    print("TEMP", fuel_temp-273.15, clad_temp-273.15, cool_temp-273.15, graph_temp-273.15)

    time.sleep(values.Constants.sim_step/1000)

"""
mass_flux=2000
flow=8000
p_top_prev=None
while True:
    baseline_pressure=fsolve(f, 7.0)[0]
    control_power=0.8
    pump_power = values.Constants.pump_constant*values.Dimensions.pump_power*control_power/0.8/4.3
    p_pump=0.8-pump_power*flow**2
    p_pump=0.5 #TESTING
    p_top=baseline_pressure
    for pos, tile in tiles.items():
        # Heat/energy calculations
        channel_frac=values.Dimensions.channel_frac
        enthalpy=tile.coolant_e
        bp=steamTable.tsat_p(baseline_pressure)
        req_sense=(bp)*values.H2O.heat_capacity*values.H2O.density*1000*channel_frac
        req_latent=values.H2O.latent_heat*values.H2O.density*1000*channel_frac
        latent_e=clamp(enthalpy-req_sense,0,req_latent)
        sens_e=enthalpy-latent_e
        steam=latent_e/req_latent
        cool_temp = sens_e/(values.H2O.heat_capacity*values.H2O.density*1000*channel_frac)

        # Basic value calculations
        dens_l=1300-cool_temp
        vol_l=tile.mass_l/dens_l
        vol_v=values.Dimensions.channel_frac-vol_l
        dens_g=tile.mass_v/vol_v
        steam_qual = tile.mass_v/(tile.mass_v+tile.mass_l)
        void = vol_v/channel_frac
        void=clamp(void,0.001,0.999)
        steam_qual=clamp(steam_qual,0.001,0.999)

        # Acceleration pressure loss
        if tile.mass_v>0:
            momentum_density = (steam_qual**2/(void*dens_g))+((1-steam_qual)**2/((1-void)*dens_l))**-1
            if pos[2]<6:
                momentum_density_top = tiles[(pos[0], pos[1], pos[2]+1)].momentum_density
            else:
                momentum_density_top = momentum_density
            p_accel=mass_flux**2*(1/momentum_density_top-1/momentum_density)
        else:
            p_accel=0

        # Friction pressure loss
        visc_l = steamTable.my_pt(baseline_pressure, cool_temp - 0.1)
        visc_g = steamTable.my_pt(baseline_pressure, cool_temp + 0.1)
        visc_m = (steam_qual/visc_g + (1-steam_qual)/visc_l)**-1
        reynold = mass_flux*values.Dimensions.hydr_diam/visc_m
        darcy_fric = 0.316*reynold**-0.25
        dens_m = void*dens_g + (1-void)*dens_l
        p_fric=2*darcy_fric*mass_flux**2/(values.Dimensions.hydr_diam*dens_m)

        #Valve pressure losses
        if pos[2]==0:
            valve_constant=1
            p_valve=valve_constant*(mass_flux**2/dens_l)
        else:
            p_valve=0
        # Gravity pressure loss
        p_grav=values.Constants.grav*dens_m

        p_total=(p_fric+p_accel+p_grav+p_valve)/1e6 #MPa

        # Dynamic pressure adjustment
        if pos[2]==0:
            tile.pressure=p_pump-p_total
        else:
            tile.pressure=tiles[(pos[0], pos[1], pos[2]-1)].pressure-p_total

    p_top_channel = tiles[(1,1,6)].pressure
    if p_top_prev==None:
        p_top_prev=p_top
    delta_p_top = p_top-p_top_prev
    p_top_prev = p_top
    flow_adjust = (p_top_channel*values.Constants.flow_p)+(delta_p_top*values.Constants.flow_d)
    flow_adjust=clamp(flow_adjust,-100,100)
    mass_flux-=flow_adjust
    mass_flux=clamp(mass_flux,100,10000)


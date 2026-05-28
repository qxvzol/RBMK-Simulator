from scipy.optimize import fsolve
from pyXSteam.XSteam import XSteam

import values
steamTable = XSteam(XSteam.UNIT_SYSTEM_BARE)

net_volume=1
water_mass=100
vapour_mass=10
p_pump=0.3

tiles={}


class Tile:
    def __init__(self, x, y, z, pressure=7, void=0, t_neut_density=0, f_neut_density=0, fiss_rate=0, fuel_e=0, coolant_e=95000000, mass_v=0, mass_l=40, momentum_density=0):
        self.x = x #m
        self.y = y #m
        self.z = z #m
        self.pressure = pressure #MPa
        self.void = void #0-1
        self.t_neut_flux = t_neut_density # neut/m^3
        self.f_neut_density = f_neut_density # neut/m^3
        self.fiss_rate = fiss_rate #fissions/s
        self.fuel_e = fuel_e #J/kg
        self.coolant_e = coolant_e #J/kg
        self.mass_v = mass_v #kg
        self.mass_l = mass_l #kg
        self.momentum_density = momentum_density #kg/m^3

for z in range(0,7):
    tiles[(1,1,z)] = Tile(1,1,z)

def clamp(value,min,max):
    if value>max:
        value=max
    elif value<min:
        value=min
    return value


def f(pressure):
    pressure=pressure[0]
    clamp(pressure,0.1,25)
    error=(steamTable.vL_p(pressure)*water_mass)+(steamTable.vV_p(pressure)*vapour_mass)-net_volume
    return error

mass_flux=2000
while True:
    #new_pressure=fsolve(f, 7.0)
    #p_bottom=new_pressure+p_pump
    #p_top=new_pressure
    for pos, tile in tiles.items():
        # Heat/energy calculations
        channel_frac=values.Dimensions.channel_frac
        enthalpy=tile.coolant_e
        bp=steamTable.tsat_p(tile.pressure)
        req_sense=(bp)*values.H2O.heat_capacity*values.H2O.density*1000*channel_frac
        req_latent=values.H2O.latent_heat*values.H2O.density*1000*channel_frac
        latent_e=clamp(enthalpy-req_sense,0,req_latent)
        sens_e=enthalpy-latent_e
        steam=latent_e/req_latent
        cool_temp = sens_e/(values.H2O.heat_capacity*values.H2O.density*1000*channel_frac)
        print(cool_temp-273)

        # Basic value calculations
        dens_l=1300-cool_temp
        vol_l=tile.mass_l/dens_l
        vol_v=values.Dimensions.channel_frac-vol_l
        dens_g=tile.mass_v/vol_v
        steam_qual = tile.mass_v/(tile.mass_v+tile.mass_l)
        void = vol_v/channel_frac
        void=clamp(void,0.001,0.999)
        steam_qual=clamp(steam_qual,0.001,0.999)
        print(void, steam_qual)

        # Acceleration pressure loss
        if tile.mass_v>0:

            momentum_density = (steam_qual**2/(void*dens_g))+((1-steam_qual)**2/((1-void)*dens_l))**-1
            momentum_density_top = tile[pos[2]+1].momentum_density
            p_accel=mass_flux**2*(1/momentum_density_top-1/momentum_density)
        else:
            p_accel=0

        # Friction pressure loss
        visc_l = steamTable.my_pt(tile.pressure, cool_temp - 0.1)
        visc_g = steamTable.my_pt(tile.pressure, cool_temp + 0.1)
        visc_m = (steam_qual/visc_g + (1-steam_qual)/visc_l)**-1
        print(values.Dimensions.hydr_diam)
        reynold = mass_flux*values.Dimensions.hydr_diam/visc_m
        darcy_fric = 0.316*reynold**-0.25
        dens_m = void*dens_g + (1-void)*dens_l
        print(darcy_fric, reynold)
        p_fric=2*darcy_fric*mass_flux**2/(values.Dimensions.hydr_diam*dens_m)

        # Gravity pressure loss
        p_grav=values.Constants.grav*dens_m
        p_total=p_fric+p_accel+p_grav
        print(p_grav,p_fric,p_accel)
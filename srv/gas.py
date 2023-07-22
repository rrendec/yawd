import math

# Higher precision molecular weight data from:
# NIST Chemistry WebBook
# https://webbook.nist.gov/chemistry/
molecular_weight = {
    'co':   28.0101,
    'no':   30.0061,
    'no2':  46.0055,
    'o3':   47.9982,
    'so2':  64.064,
    'nh3':  17.0305,
}

# Temperature conversion:
#   0 C = 273.15 K
C_TO_K = 273.15

# Pressure conversion:
#   1 atm = 101325 Pa
#   1 bar = 100000 Pa
ATM_TO_PA = 101325
BAR_TO_PA = 100000

# Typical pressure and temperature:
#   25 degrees C
#   1 atm
STD_TEMP_C = 25
STD_PRES_PA = ATM_TO_PA

# Conversion formulas from:
# https://www.lenntech.com/calculators/ppm/converter-parts-per-million.htm
#         Vn   1 ug gas   Vn   1 mg gas
# 1 ppm = -- * -------- = -- * ---------
#         M    1 L air    M    1 m^3 air
#
#        T
# Vn = R -
#        P
#
# Vn = 	molar volume of ideal gas                   [L/mol]
#       (at temperature T and pressure P)
# R = 	universal gas law constant = 8.314510       [m^3 Pa K^-1 mol^-1]
# T = 	temperature                                 [K]
# P =   pressure                                    [Pa]
def to_ppm(chem, cntr_mg_m3, temp_c=STD_TEMP_C, pres_pa=STD_PRES_PA):
    m = molecular_weight[chem]
    return 8314.510 * (temp_c + C_TO_K) * cntr_mg_m3 / (m * pres_pa)

# Conversion formulas from:
# https://www.omnicalculator.com/physics/air-pressure-at-altitude
#           -g M (h - h0)
#           -------------
# P = P0 e     RT
#
# h = altitude at which we calculate the pressure   [m]
# P = air pressure at altitude h
# P0 = the pressure at the reference level h0
# T = temperature at altitude h                     [K]
# g = gravitational acceleration = 9.80665          [m/s^2]
# M = the molar mass of air = 0.0289644             [kg/mol]
# R = universal gas constant = 8.31432              [N*m/(mol*K)]
#
# Since the reference presure level is the sea level, h0 = 0.
def air_pressure(pres_sea, temp_c, altitude_m):
    return pres_sea * math.exp(-0.034163195 * altitude_m / (temp_c + C_TO_K))

if __name__ == '__main__':
    print(to_ppm('co', 0.4))
    print(to_ppm('co', 0.4, 0, BAR_TO_PA))
    print(air_pressure(1013, 25, 100))

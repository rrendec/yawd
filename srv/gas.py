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

if __name__ == '__main__':
    print(to_ppm('co', 0.4))
    print(to_ppm('co', 0.4, 0, BAR_TO_PA))

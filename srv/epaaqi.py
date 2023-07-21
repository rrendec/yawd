# EPA Air Quality Index (AQI)
#
# Based on:
# EPA 454/B-18-007
# September 2018
# (aqi-technical-assistance-document-sept2018.pdf)

# Based on section II.a (page 13). We multiply by 10^x and then truncate
# to integer, instead of truncating to x decimal places. This allows for
# clean integer comparisons while walking the breakpoint table. Of course,
# breakpoint table values are also scaled accordingly.
#
# Equation d.1 still holds, without converting anything back. The scale is
# simplified out of the fraction.
SCALE = {
    'o3-8': 1000,
    'o3-1': 1000,
    'pm2_5': 10,
    'pm10': 1,
    'co': 10,
    'so2': 1,
    'no2': 1,
}

# Table 5 (page 14). Values are multiplied by the scale (see the comment
# above SCALE). Only upper boundary values are included, because the lower
# boundary value is always 1 + the upper boundary value of the previous row.
BP = {
    'o3-8':  (0,   [54,   70,   85,  105,  200,  None, None]),
    'o3-1':  (125, [None, None, 164, 204,  404,  504,  604]),
    'pm2_5': (0,   [120,  354,  554, 1504, 2504, 3504, 5004]),
    'pm10':  (0,   [54,   154,  254, 354,  424,  504,  604]),
    'co':    (0,   [44,   94,   124, 154,  304,  404,  504]),
    'so2':   (0,   [35,   75,   185, 304,  604,  804,  1004]),
    'no2':   (0,   [53,   100,  360, 649,  1249, 1649, 2049]),
    'aqi':   (0,   [50,   100,  150, 200,  300,  400,  500])
}

def aqi(name, value):
    if name not in SCALE:
        return None

    # The value is truncated, not rounded - see example on page 15
    c_p = int(value * SCALE[name])
    bp_lo, bp_list = BP[name]
    if c_p < bp_lo:
        return None

    i_lo, i_list = BP['aqi']
    i_list = i_list.copy()
    for bp_hi in bp_list:
        i_hi = i_list.pop(0)
        if bp_hi is None:
            i_lo = i_hi + 1
            continue
        if c_p > bp_hi:
            bp_lo = bp_hi + 1
            i_lo = i_hi + 1
            continue

        # Section II - Equation 1 (page 13)
        i_p = (i_hi - i_lo) * (c_p - bp_lo) / (bp_hi - bp_lo) + i_lo

        # Section II.d - round the result
        return round(i_p)

    return None

if __name__ == '__main__':
    print(aqi('o3-8', 0.07853333))
    print(aqi('pm2_5', 35.92431999))
    print(aqi('co', 8.47532711))

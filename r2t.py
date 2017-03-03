# PIR stuff
import math

def r2t(R):
    """PIR conversion from resistance to temperature"""
    C1 = 0.0010295
    C2 = 0.0002391
    C3 = 0.0000001568
    return 1/(C1 + C2*math.log(R) + C3*(math.log(R)**3)) - 273.15

def v2r(V,Vref=5):
    """PIR conversion from voltage to resistance"""
    if Vref <= V:
        return float('nan')
    return 10e3*V/(Vref-V)


if '__main__' == __name__:
    for v in [1,1.25,2.25]:
        print r2t(v2r(v))

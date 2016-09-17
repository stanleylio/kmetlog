import math

def r2t(R):
    C1 = 0.0010295
    C2 = 0.0002391
    C3 = 0.0000001568
    return 1/(C1 + C2*math.log(R) + C3*(math.log(R)**3)) - 273.15


if '__main__' == __name__:
    for r in [1e3,10e3,500e3]:
        print r2t(r)

from hx711 import hx711
from hx import HX711
from time import sleep
from machine import freq

freq(80000000)
tenso = hx711(5, 4)
tenso.calibrate()

while True:
    wynik = tenso.read_filtered(5, 4)
    # print("")
    # print("")
    # print(wynik)
    # print("g:" + str(wynik/420))
    print(tenso.get_weight_g())
    print(tenso.get_weight_kg())

    #sleep(5)





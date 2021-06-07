import dht
from machine import Pin

"""
Moduł z funkcjami obsługującymi komunikację z czujnikiem temperatury i wilgotności DHT11.
"""
myDht = dht.DHT11(Pin(5))

def get_measure():
    """
    Funkcja odczytująca z czujnika wartość temperatury i wilgotności.
    :return: Jeśli pomiar się uda - temperatura i wilgotność: tuple: (int, int), w przeciwnym wypadku 'False': bool
    """
    try:
        myDht.measure()
        temp = myDht.temperature()
        hum = myDht.humidity()
        return (temp, hum)
    except Exception as e:
        print(e)
        print("Blad pomiaru DHT11")
        return False

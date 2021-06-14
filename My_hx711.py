from machine import Pin
from utime import sleep_us, time
from micropython import const


class My_hx711():
    """
    Klasa, służąca do obsługi konwertera ADC hx711 i belki tensometrycznej
    Umie pobierać surowe dane, dane przefiltrowane, wagę w gramach i wagę w kilogramach.

    hx711 - 24-bitowy konwerter ADC

    **Autor: Paweł Zięba 14.04.2021

    Przykładowa procedura:
    1. Inicjalizacja
    2. Kalibracja
    3. Odczyt wagi
    """

    READY_TIMEOUT_SEC = const(5)
    DATA_RANGE = const(24)

    def __init__(self, clk_pin, data_pin, max_weight=20):
        """
        :param clk_pin: Wyjście zegarowe podłączone do SCK: int
        :param data_pin: Wejście danych podłączone do DT: int
        :param max_weight: Zakres pomiarowy belki tensometrycznej: int
        """
        self.clk_pin = Pin(clk_pin, Pin.OUT)
        self.data_pin = Pin(data_pin, Pin.IN)

        self.clk_pin.value(0)
        self.data_pin.value(0)

        self.cal = 0
        self.max_weight = max_weight


    def _wait(self):
        """
        Funkcja czeka aż na linii danych będzie logiczne '0', w przeciwnym wypadku,
        podniesie wyjątek po określonym czasie
        """
        time_0 = time()
        while(not self.is_ready()):
            if(time() - time_0 > self.READY_TIMEOUT_SEC):
                raise Exception("hx711 nie odpowiada!")


    def _U2_conversion(self, data):
        """
        konwersja U2 --> DEC
        :param data: Liczba U2: int
        :return: Liczba dziesiętna: int
        """
        if(data & (1 << (self.DATA_RANGE - 1))):
            data -= 1 << self.DATA_RANGE
        return data


    def is_ready(self):
        """
        :return: 'True' jeśli układ gotowy do komunikacji, w przeciwnym wypadku 'False': bool
        """
        return self.data_pin.value() == 0


    def calibrate(self):
        """
        Funkcja kalibrująca urządzenie, zajmuje kilka do kilkunastu sekund

        :return: Błąd odczytu: float
        """
        self.cal = self.read_filtered(50, 5)
        return self.cal


    def power_on(self):
        """Funkcja włączająca układ hx711"""
        self.clk_pin.value(0)


    def power_off(self):
        """Funkcja wyłączająca układ hx711"""
        self.clk_pin.value(1)
        sleep_us(60)


    def read_raw(self):
        """
        Funkcja pobierająca dane z ukłądu hx711

        :return: Odczyt w postaci DEC lub 'False' keśli wystąpi błąd: int or bool
        """
        if(not self.is_ready()):
            try:
                self._wait()
            except Exception as e:
                print(e)
                return False

        data = 0
        for i in range(self.DATA_RANGE):
            self.clk_pin.value(1)
            self.clk_pin.value(0)

            data = data << 1 | self.data_pin.value()

        self.clk_pin.value(1)
        self.clk_pin.value(0)

        return self._U2_conversion(data)


    def read_filtered(self, cycles=10, dt=4):
        """
        Funkcja pobierająca i uśredniająca dane z ukłądu hx711 (filtr low-pass)
        :param cycles: Ilość pomiarów do uśrednienia: int
        :param dt: Współczynnik filtru low-pass: int

        :return: Średnia wartość z iluś pomiarów: float
        """
        average = 0
        for i in range(cycles):
            average = average *dt
            average += self.read_raw()
            average = average / (dt + 1)

        return average


    def get_weight_g(self):
        """
        Funkcja mierząca wagę w g (uwzględnia kalibrację)

        :return: Waga w g: float
        """
        value = self.read_filtered(20, 4) - self.cal
        weight = self.max_weight * 0.0001192 * value
        return round(weight, 1)


    def get_weight_kg(self):
        """
        Funkcja mierząca wagę w kg (uwzględnia kalibrację)

        :return: Waga w kg: float
        """
        return round(self.get_weight_g() / 1000, 3)

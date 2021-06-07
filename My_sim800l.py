import select
import sys
from machine import UART, Pin
from utime import ticks_ms
from time import sleep

# Konfiguracja sim800l:
# - na stałe włączone pobieranie czasu z serwera UTC
# - na stałe wyłączona dioda led w module

class My_sim800l:
    """
    Klasa odpowiedzialna za obsługę modułu sim800l.\n
    *Wspierane urządzenia: ESP32\n
    *Należy podać numer interfejsu UART oraz piny RX i TX !!!
    """
    def __init__(self, sleep_pin, uart=2, baudrate=115200, rx=16, tx=17, rxbuf=1024):
        """
        :param sleep_pin: Numer pinu DTR - sim800l
        :param uart: Numer interfejsu UART: int
        :param baudrate: Prędkość transmisji
        :param rx: Numer pinu rx
        :param tx: Numer pinu tx
        """
        self.uart_num = uart
        self.baudrate = baudrate
        self.rx = rx
        self.tx = tx
        self.rxbuf = rxbuf
        self.sleep_pin = Pin(sleep_pin, Pin.OUT)
        self.led = Pin(27, Pin.OUT)#<------------------------------- LED DO DEBUGOWANIA

        self.uart = UART(self.uart_num, baudrate=self.baudrate, rx=self.rx, tx=self.tx, rxbuf=self.rxbuf)

        self.sleep_pin.value(0)

        self._ping(3)




    def _ping(self, num_of_pings):
        """
        Funkcja pingująca układ sim800l w celu obudzenia lub dostosowania prędkości transmisji.
        """
        for i in range(num_of_pings):
            self._send_data("AT\n")
            sleep(0.5)
            print("Ping: " + str(i+1))
        self._read_data(0.5)



    def _read_data(self, timeout=None):
        """
        Funkcja odczytująca dane z interfejsu UART - blokuje program przez czas określony w zmiennej 'timeout'.

        :param timeout: Czas[s], oczekiwania przed próbą odczytania danych: int
        :return: Jeśli dane dostępne zwraca odczytany ciąg znaków: string
        """
        # t = ticks_ms()
        # # if(timeout):
        # #     sleep(timeout)
        # buf = ""
        # while True:
        #     self.led.value(1)
        #     r, _, _, = select.select([sys.stdin], [], [], 0)
        #     if (r):
        #         s = sys.stdin.read(1)
        #         buf += s
        #
        #     elif(timeout and ticks_ms() - t > timeout*1000):
        #         self.led.value(0)
        #         break
        #
        #     if(end and buf.find(end) != -1):
        #         self.led.value(0)
        #         break

        if(timeout):
            sleep(timeout)

        data = self.uart.read()
        if(data):
            return data.decode("utf-8")
        else:
            return ""



    def _send_data(self, data):
        """
        Funkcja wysyłająca dane przez UART.

        :param data: Dane do wysłania: string
        :return: Liczba wysłanych znaków lub 'None': int or 'None'
        """
        return self.uart.write(data)



    def check_sim(self):
        """
        Funkcja sprawdzająca czy moduł sim800l widzi kartę SIM (i ma do niej dostęp).\n
        'READY' - karta odblokowana\n
        'SIM PIN' - karta wymaga podania kody PIN\n
        'SIM PUK' - karta wymaga podania kody PUK\n
        'ERROR' - brak karty SIM lub inny błąd

        :return: Status karty sim: string
        """
        self._send_data("AT+CPIN?\n")
        resp = self._read_data(0.2)
        #print(resp)
        if (resp.find("READY") > 0):
            return "READY"
        elif(resp.find("SIM PIN") > 0):
            return "SIM PIN"
        elif (resp.find("SIM PUK") > 0):
            return "SIM PUK"
        else:
            return "ERROR"



    def unlock_sim(self, pin):
        """
        Funkcja odblokowująca kartę SIM.

        :param pin: Kod PIN do karty sim
        :return: 'True', jeśli uda się odblokować kartę, w przeciwnym wypadku 'False': bool
        """
        print("--Odblokowywanie karty SIM--")
        self._send_data('AT+CPIN="' + str(pin) + '"\n')
        resp = self._read_data(10)
        #print(resp)
        if(resp.find("OK") > 0):
            return True
        else:
            return False



    def set_GPRS_connection(self, apn_name=None, apn_user=None, apn_pass=None):
        """
        Funkcja ustanawiająca połączenie z APN'em

        :param apn_name: Opcjonalna nazwa APN: string
        :param apn_user: Opcjonalna nazwa użytkownika APN: string
        :param apn_pass: Opcjonalne hasło użytkownika APN: string
        :return: Przydzielony adres IPv4 lub 'False' gdy błąd: string or bool
        """
        if(apn_name and apn_user and apn_pass):
            self._send_data('AT+CSTT="' + apn_name + '","' + apn_user + '","' + apn_pass + '"\n')
        else:
            self._send_data('AT+CSTT="' + self.apn_name + '","' + self.apn_user + '","' + self.apn_pass + '"\n')

        resp = self._read_data(0.2)
        #print(resp)
        if (resp.find("OK") > 0):
            print("--Zapisano konfiguracje APN'a--")

            self._send_data("AT+CIICR\n")

            resp = self._read_data(0.8)
            if (resp.find("OK") > 0):
                print("--Uruchomiono GPRS--")

                self._send_data("AT+CIFSR\n")

                resp = self._read_data(0.2)
                if(resp.find("ERROR") > 0):
                    print("--Nie uzyskano adresu IP--")
                    return False
                else:
                    print(resp[10 : -1])
                    return resp[10 : -1]        #zwrócenie przydzielonego adresu IPv4
            else:
                print("--Nie udalo sie uruchomic GPRS--")
                return False
        else:
            print("--Nie udalo sie zapisac konfiguracji APN'a--")
            return False



    def send_http_request(self, method, server, headers={}, path="/", data="", json="", port=80):
        """
        Funkcja wysyłająca zapytania http
        *dane "json" nadpisują dane "data" i automatycznie dodają odpowiedni nagłówek http

        :param method: Metoda zapytania http: GET, POST, PUT, DELETE: string
        :param server: Serwer do którego ma zostać wysłane zapytanie: string
        :param headers: Nagłówki http {"nazwa_nagłówka" : "wartość"}: dictionary
        :param path: Ścieżka po ukośniku - domyślnie: "/": string
        :param data: Treść zapytania jako tekst: string
        :param json: Treść zapytania w formacie json: string
        :param port: port - domyślnie: 80: int
        """
        #przygotowanie zapytania http
        header = "Host: " + server + "\r\n"
        for h in headers:
            header = header + h + ": " + headers[h] + "\r\n"

        data_to_send = ""
        if (json):
            if (header.find("Content-Type: application/json") < 0):
                header = header + "Content-Type: application/json\r\n"
            data_to_send = json
        else:
            data_to_send = data

        request = method + " " + path + " HTTP/1.1\r\n" + header + "\r\n" + data_to_send

        self._send_data('AT+CIPSTART="TCP"' + ',"' + server + '",' + str(port) + "\n")

        resp = self._read_data(2)
        if(resp.find("CONNECT OK") > 0):
            print("--Polaczono z: " + server + "--")

            self._send_data('AT+CIPSEND=' + str(len(request)) + "\n")
            sleep(0.1)
            self._send_data(request)
            resp = self._read_data(10)

            return resp[resp.find("SEND OK")+9 : -8]       #wycinamy echo i napis CLOSED z odpowiedzi
        else:
            print("--Blad polaczenia z serwerem--")
            return False


    def get_voltage(self):
        """
        Funkcja odczytująca wartość napięcia (mV) zasilającego sim800l.

        :return: Jeśli uda się odczytać: Napięcie w mV w przeciwnym razie: 'False': int or bool
        """
        self._send_data("AT+CBC\n")
        resp = self._read_data(0.2)
        #print(data)
        index = resp.find("+CBC:")
        print("Index: " + str(index))
        if(index > 0):
            resp = resp[index + 6 : index + 16].replace("\n", "").split(",")
            if(len(resp) == 3):
                voltage = resp[2]
                return voltage
            else:
                print("---Nie udalo sie odczytac napiecia---") #jeśli nie uda się odczytać napięcia
                return False
        else:
            print("--Nie udalo sie odczytac napiecia--") #jeśli nie uda się odczytać napięcia
            return False



    def get_utc_time(self):
        """
        Funkcja pobierająca czas z serwera UTC.

        :return: Czas (rr/mm/dd, hh:mm:ss) lub 'False; jeśli nie uda się pobrać danych: tuple(string, string) or bool
        """
        self._send_data("AT+CCLK?\n")
        resp = self._read_data(0.2)

        if(resp.find("OK") > 0):
            date_time = resp[resp.find('"')+1 : resp.rfind('+')]
            date_time = date_time.split(",")
            date = date_time[0]
            time = date_time[1]
            #print((date, time))
            return (date, time)
        else:
            print("--Nie udalo sie pobrac czasu--")
            return False



    def get_signal_strength(self):
        """
        Funkcja pobierająca siłę sygnału GSM.

        :return: Siła sygnału 0-31: int
        """
        self._send_data("AT+CSQ\n")
        resp = self._read_data(0.2)
        #print(resp)
        if(resp.find("OK")):
            signal = resp[resp.find(":")+2 : resp.rfind(",")]
            #print(signal)
            return str(signal)
        else:
            print("--Nie udalo sie pobrac sily sygnalu--")
            return False



    def enable_transparent_mode(self):
        self._send_data("AT+CIPMODE=1\n")
        resp = self._read_data(0.2)
        if (resp.find("OK") > 0):
            print("--Wlaczono tryb transparentny--")
            return True
        else:
            print("--Nie udalo sie wlaczyc trybu transparentnego--")
            return True



    def disable_transparent_mode(self):
        self._send_data("AT+CIPMODE=0\n")
        resp = self._read_data(0.2)
        if (resp.find("OK") > 0):
            print("--Wylaczono tryb transparentny--")
            return True
        else:
            print("--Nie udalo sie wylaczyc trybu transparentnego--")
            return True



    def disable_debug_mode(self):
        """
        Funkcja wyłączająca tryb debugowania w sim800l

        :return: Jeśli uda się wyłączyć tryb debugowania: 'True', w przeciwnym wypadku: 'False: bool
        """
        self._send_data("AT+CMEE=0\n")
        resp = self._read_data(0.2)
        #print(resp)
        if(resp.find("OK") > 0):
            print("--Wylaczono tryb debugowania--")
            return True
        else:
            print("--Nie udalo sie wylaczyc trybu debugowania--")
            return True



    def go_sleep(self):
        self.sleep_pin.value(1)
        self._send_data("AT+CSCLK=2\n")
        resp = self._read_data(0.2)
        if(resp.find("OK") > 0):
            print("--Usypianie modulu--")
            sleep(5)
            return True
        else:
            print("--Nie udalo się uspic modulu--")
            return False



    def wake_up(self):
        self.sleep_pin.value(0)
        self._ping(2)
        self._send_data("AT+CSCLK=0\n")
        resp = self._read_data(0.2)
        if (resp.find("OK") > 0):
            print("--Wybudzanie modulu--")
            return True
        else:
            print("--Nie udalo się obudzic modulu--")
            return False



    def reset(self):
        """
        Funkcja resetująca układ sim800l, po resecie należy odczekać przynajmniej 5 sekund przed wysłaniem kolejnego polecenia.

        :return: 'True' jeśli uda się zresetować, w przeciwnym wypadku 'False': bool
        """
        self._send_data("AT+CFUN=1,1\n")
        resp = self._read_data(0.2)
        if (resp.find("OK") > 0):
            print("--Reset--")
            return True
        else:
            print("--Nie udalo sie zresetowac--")
            return True



    def debug(self):
        return self._read_data()

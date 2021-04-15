import machine, sdcard, uos
from time import sleep

class MySDCard():
    """
    Klasa obsługująca komunikację i wymianę danych z kartą SD.
    Komunikacja po magistrali SPI.
    Wymagany pin CS.
    *Możliwość zbierania danych w postaci logów na karcie SD.
    *Domyślna ścieżka do karty: "/sd"
    *Domyślna ścieżka do pliku z logami: "/sd/log.txt"
    *Blokuje program do momentu podłączenia karty SD
    **Autor: Paweł Zięba 15.04.2021
    """
    def __init__(self, spi, cs_pin, mount_dir="/sd", log_dir="/sd/log.txt"):
        """
        :param spi: Objekt spi (machine.SPI(1)): object
        :param cs_pin: Numer pinu GPIO, do którego podłączony jest pin CS wykrywający obecność karty SD: int
        :param mount_dir: Opcjonalna ścieżka w systemie plików, do której ma zostać przypisana karta SD: string
        :param log_dir: Opcjonalna ścieżka do pliku z logami: string
        """
        self.spi = spi
        self.cs_pin = cs_pin
        self.log_dir = log_dir
        self.mount_dir = mount_dir

        self.sd = sdcard.SDCard(self.spi, machine.Pin(self.cs_pin))

        while(not self._connect()):
            print("Laczenie z karta SD..")
            self._connect()
            sleep(1)


    def _connect(self):
        """
        Funkacja inicjalizująca i podłączająca kartę SD do systemu plików ESP

        :return: Status powodzenia, 'True' jeśli się uda połączyć: bool
        """
        try:
            self.sd.init_card()
            # przypisanie karty SD do systemu plików ESP
            uos.mount(self.sd, self.mount_dir)

            print("/: ")
            print(uos.listdir('/'))
            print("")
            return True

        except Exception as e:
            print(e)
            print("Blad polaczenia z karta SD")
            return False


    def get_file_size(self, file_dir):
        """
        Funkcja pobierająca rozmiar pliku w bajtach

        :param file_dir: Ścieżka do pliku: string
        :return: Rozmiar pliku w bajtach: int
        """
        return uos.stat(file_dir)[6]


    def get_free_size(self, dir):
        """
        Funkcja pobierająca ilość dostępnej pamięci

        :param dir: Ścieżka: string
        :return: Rozmiar pliku w bajtach: int
        """
        return uos.statvfs(dir)[0] * uos.statvfs(dir)[3]


    def set_log_dir(self, log_dir):
        """
        Funkcja ustawiająca stałą ścieżkę do pliku z logami

        :param log_dir: Ścieżka do pliku, w którym domyślnie mają zostać zapisane logi
        """
        self.log_dir = log_dir


    def log_data(self, log_text, log_dir=None):
        """
        Funkcja zapisująca logi w wybranym pliku

        :param log_text: Treść logu do zapisania: string
        :param log_dir: Opcjonalna ścieżka do pliku, w którym ma zostać zapisany log: string
        :return: Status powodzenia, 'True' jeśli się uda zapisać: bool
        """
        try:
            if(log_dir):
                f = open(log_dir, "a")
            else:
                f = open(self.log_dir, "a")
            f.write(log_text + "\n")
            f.close()
            return True

        except Exception as e:
            print(e)
            print("Blad zapisu do pliku")
            return False

from MySDCard import MySDCard
from time import sleep
import machine


sd = MySDCard(machine.SPI(1), 15)
sd.set_log_dir("/sd/logs.txt")

print(sd.get_file_size("/sd/logs.txt"))
print(sd.get_free_size("/sd"))
print("")



from machine import Pin
from My_sim800l import My_sim800l
from time import sleep

print("START")

sim = My_sim800l(25, 2, 115200, 16, 17, 1024)
sim.reset()

sim.disable_debug_mode()

if(sim.check_sim() == "SIM PIN"):
    if(sim.unlock_sim(6614)):
        print("Udalo sie odblokowac karte SIM")

#sim.enable_transparent_mode()
sim.set_GPRS_connection("internet", "internet", "internet")

i = 0

# print(sim.send_http_request("GET", "maker.ifttt.com", headers={"Connection":"close", "Content-Length":"46"}, path="/trigger/test/with/key/govMGzo5agE0oFrHj7LVTXqoMX_xrzuN7d_qiiQAuBh", json='{"value1":"asd","value2":"bbb","value3":"ccc"}'))
print(sim.send_http_request("GET", "validate.jsontest.com", path="/?json=%5BJSON-code-to-validate%5D", headers={"Connection":"close"}))
while True:
    sim.led.value(0)
    sleep(1)
    sim.led.value(1)
    sleep(1)
    i += 1
    print(i)
    #print(sim.debug())

    print(sim.get_signal_strength())
    #print(sim.debug())
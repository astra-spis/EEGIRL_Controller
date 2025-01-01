import serial
import serial.tools.list_ports

# EEGIRL_Controller\process_ssvep.py
import process_ssvep

coms = serial.tools.list_ports.comports()

#comポートを取得
def search_port():
    comlist = []
    for com in coms:
        comlist.append(str(com.device))
    return comlist

def connect_port(select):
    res = "None: No Attenpted"
    port = [com for com in coms if com.device == select]
    try:
        serial.Serial(port[0].device, 9600, timeout=0.1)
        print("Tried serial.Serial()")
        process_ssvep.setup_bci_device(select)
        print("Tried process_ssvep.setup_bci_device()")
        res = port[0].device + ": Succeeded"
        switch = True
    except Exception as e:
        print("Error:", e)
        res = port[0].device + ": Failed"
        switch = False
    finally:
        print(res)
        return res, port[0].device, switch

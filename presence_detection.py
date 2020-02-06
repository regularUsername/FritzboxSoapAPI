from pathlib import Path
from math import ceil
import datetime
import simple_telegram

from time import sleep
import fritzbox_soap

import settings

def main():
    laststate = None
    while True:
        now = datetime.datetime.now().replace(second=0,microsecond=0)
        try:
            hostEntry = fritzbox_soap.get_host_by_mac(settings.mac_adress)
            active = hostEntry['Active'] == '1'
            hostName = hostEntry['HostName']
            msg = f"{hostName} {'verbunden' if active else 'getrennt'}"
        except Exception as e:
            active = laststate
            print(f"[{now}] FritzboxSoap: {e}")
            msg = ""


        if laststate != active:
            print(f"[{now}] {msg}       ")
        else:
            print(f"[{now}] {msg}       ",end='\r') # nur carriage return um die zeile zu überschreiben beim nächstem print

        if laststate is not None and laststate != active:
            simple_telegram.send_message(simple_telegram.telegram_chatid, msg)

        laststate = active
        sleep(300)


if __name__ == "__main__":
    main()

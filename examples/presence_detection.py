import datetime
import simple_telegram

from time import sleep
import context
from FritzBoxServices import Services

import settings


def main():
    laststate = {k: None for k in settings.mac_adresses}
    services = Services(settings.fritzbox_user,
                        settings.fritzbox_password,
                        settings.fritzbox_certificate)
    while True:
        now = datetime.datetime.now().replace(microsecond=0)
        try:
            p = services.Hosts.GetHostListPath()
            hostlist = services.Hosts.getList(p)
            for i in hostlist:
                mac = i['MACAddress']
                if mac in settings.mac_adresses:
                    active = i['Active'] == '1'
                    hostName = i['HostName']
                    msg = f"{hostName} {'verbunden' if active else 'getrennt'}"
                    if laststate[mac] is not None and laststate[mac] != active:
                        print(f"[{now}] {msg}")
                        simple_telegram.send_message(settings.telegram_chatid, msg)
                    laststate[mac] = active
        except Exception as e:
            print(f"[{now}] FritzboxSoap: {e}")
            msg = ""

        sleep(300)


if __name__ == "__main__":
    main()

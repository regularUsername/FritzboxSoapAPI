import context
from FritzBoxServices import Services

import settings

def main():
    services = Services(settings.fritzbox_user,
                        settings.fritzbox_password,
                        settings.fritzbox_certificate)
    print(services.listServices())
    print()
    u = services.Hosts.GetHostListPath()
    hostList = services.Hosts.getList(u)
    hostnames = [x["HostName"] for x in hostList]
    print(hostnames)


if __name__ == "__main__":
    main()
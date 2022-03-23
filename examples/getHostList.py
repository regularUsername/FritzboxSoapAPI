from FritzboxSoapAPI import Services

import settings


def main():
    services = Services(settings.fritzbox_user,
                        settings.fritzbox_password,
                        settings.fritzbox_certificate)
    print(services.listServices())
    print()
    u = services.Hosts.GetHostListPath()
    hostlist = services.Hosts.getList(u)
    hostnames = [x["HostName"] for x in hostlist]
    print(hostnames)


if __name__ == "__main__":
    main()

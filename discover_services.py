from bs4 import BeautifulSoup
from bs4.element import Tag
import requests
from requests.auth import HTTPDigestAuth

from pathlib import Path
import sys

import settings

session = requests.Session()

session.auth = HTTPDigestAuth(settings.fritzbox_user,
                              settings.fritzbox_password)
session.verify = settings.fritzbox_certificate


def discover_services(fritzbox_url):
    resp = session.get(fritzbox_url+"/tr064/tr64desc.xml")
    soup = BeautifulSoup(resp.text, "lxml-xml")
    # services = []
    # for service in soup.serviceList:
    #     if isinstance(service, Tag):
    #         services.append({x.name:x.text for x in service if isinstance(x,Tag)})

    # print(services[0])

    # versteht kein mensch
    services = [{x.name: x.text for x in service if isinstance(x, Tag)}
                for service in soup.serviceList if isinstance(service, Tag)]
    return services


def get_service_actions(fritzboxurl, scpdurl):
    resp = session.get(fritzboxurl+"/tr064"+scpdurl)
    soup = BeautifulSoup(resp.text, "lxml-xml")

    actions = []
    for action in soup.scpd.actionList:
        if isinstance(action, Tag):
            d = {
                "name": action.findChild().text,
                "arguments": [],
                "returnvalues": []
            }
            for arg in action.argumentList:
                if isinstance(arg, Tag):
                    if arg.direction.text == "in":
                        d["arguments"].append(arg.findChild("name").text)
                    else:
                        d["returnvalues"].append(arg.findChild("name").text)

            actions.append(d)

    return actions


# save all SCPD Files to "./SCPD_Files/"
def dump_SCPD():
    resp = session.get("https://fritz.box/tr064/tr64desc.xml")
    soup = BeautifulSoup(resp.text, "lxml-xml")

    p = Path("./SCPD_Files")
    if not p.exists():
        p.mkdir()
    open("./SCPD_Files/tr64desc.xml", "w").write(soup.prettify())

    for x in soup.findAll("SCPDURL"):
        print(x.text)
        resp = session.get("https://fritz.box/tr064"+x.text)
        soup = BeautifulSoup(resp.text, "lxml-xml")
        open("./SCPD_Files"+x.text, "w").write(soup.prettify())


if __name__ == "__main__":
    # dump_SCPD()
    if len(sys.argv) < 2:
        for x in discover_services("https://fritz.box"):
            print(f"service: {x['serviceType']:50} controlUrl: {x['controlURL']:35} scpdUrl: {x['SCPDURL']}")
    else:
        for x in get_service_actions("https://fritz.box", f"/{sys.argv[1]}.xml"):
            print(x)

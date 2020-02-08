from bs4 import BeautifulSoup
from bs4.element import Tag
import requests
from requests.auth import HTTPDigestAuth

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


if __name__ == "__main__":
    for x in discover_services("https://fritz.box"):
        print(x)
    # for x in get_service_actions("https://fritz.box","/timeSCPD.xml"):
        # print(x)

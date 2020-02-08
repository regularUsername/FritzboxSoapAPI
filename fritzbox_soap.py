#!/usr/bin/env python
# coding: utf-8
import requests
from requests.auth import HTTPDigestAuth
from bs4 import BeautifulSoup
from bs4.element import Tag

import settings

session = requests.Session()
session.auth = HTTPDigestAuth(settings.fritzbox_user,
                              settings.fritzbox_password)
session.verify = settings.fritzbox_certificate


def create_soap_request(saction, sservice, arguments={}):
    argtags = ""
    for k, v in arguments.items():
        argtags += f'\n<{k}>{v}</{k}>'
    return f'''<?xml version="1.0"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"
s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
<s:Body>
<u:{saction} xmlns:u="{sservice}">{argtags}
</u:{saction}>
</s:Body>
</s:Envelope>'''.encode('utf-8')


def soap_action(surl, sservice, saction, sarguments={}):
    header = {
        'Content-Type': 'text/xml; charset="utf-8"',
        'SOAPACTION': f"{sservice}#{saction}"
    }
    response = session.post(
        url=surl,
        headers=header,
        data=create_soap_request(saction, sservice, sarguments),
        timeout=31
    )
    soup = BeautifulSoup(response.text, "lxml-xml")

    return soup


def get_hostlist():
    soup = soap_action(
        surl="https://fritz.box:40888/tr064/upnp/control/hosts",
        sservice="urn:dslforum-org:service:Hosts:1",
        saction="X_AVM-DE_GetHostListPath"
    )
    hostlist_url = soup.find("NewX_AVM-DE_HostListPath").text
    response = session.get("https://fritz.box:40888/tr064"+hostlist_url)
    soup = BeautifulSoup(response.text, "lxml-xml")

    hostlist = []
    for item in soup.findAll("Item"):
        hostlist.append(
            {child.name: child.text for child in item.findChildren()})

    return hostlist


def get_host_by_mac(mac: str):
    soup = soap_action(
        surl="https://fritz.box:40888/tr064/upnp/control/hosts",
        sservice="urn:dslforum-org:service:Hosts:1",
        saction="GetSpecificHostEntry",
        sarguments={"NewMACAddress": mac}
    )
    # TODO error handling
    host_entry = {x.name[3:]: x.text for x in soup.GetSpecificHostEntryResponse
                  if (isinstance(x, Tag))}
    return host_entry


if __name__ == "__main__":
    print(get_host_by_mac(settings.mac_adress))

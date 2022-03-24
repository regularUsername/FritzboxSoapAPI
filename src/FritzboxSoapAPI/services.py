from pathlib import Path
from bs4 import BeautifulSoup, Tag
import requests
from requests.auth import HTTPDigestAuth


class Services:
    def __init__(self,
                 user: str,
                 password: str,
                 certificate: str = None,
                 fritzbox_url: str = "https://fritz.box"):
        self._baseURL = fritzbox_url.rstrip('/')+"/tr064"
        self._session = requests.Session()

        self._session.auth = HTTPDigestAuth(user, password)
        self._session.verify = certificate
        self._scpd = {}

        resp = self._session.get(self._baseURL+"/tr64desc.xml")
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml-xml")

        self._services = {}
        for service in soup.findAll('service'):
            if isinstance(service, Tag):
                name = service.serviceType.text.split(':')[-2]
                shortname = name.replace('X_AVM-DE_', '')
                self._services[shortname] = {
                    x.name: x.text.strip()
                    for x in service if isinstance(x, Tag)}

    def _dump_scpd(self):
        resp = self._session.get(self._baseURL+"/tr64desc.xml")
        soup = BeautifulSoup(resp.text, "lxml-xml")

        p = Path("./SCPD_Files")
        if not p.exists():
            p.mkdir()
        open("./SCPD_Files/tr64desc.xml", "w").write(soup.prettify())

        for x in soup.findAll("SCPDURL"):
            resp = self._session.get(self._baseURL+x.text)
            soup = BeautifulSoup(resp.text, "lxml-xml")
            open("./SCPD_Files"+x.text, "w").write(soup.prettify())

    def __getattr__(self, name):
        if name in self._services:
            return _Service(self, name)
        raise AttributeError(f"'Services' object has no attribute '{name}'")

    def listServices(self):
        return list(self._services.keys())

    def serviceInfo(self, name):
        if name in self._services:
            s = self._services[name]
            ret = f"""Service: {name}
    service type:   '{s['serviceType']}'
    service id:     '{s['serviceId']}'
    control url:    '{s['controlURL']}'
    event sub url:  '{s['eventSubURL']}'
    scpd url:       '{s['SCPDURL']}'
"""
            return ret

        raise ValueError('bad method')


class _Service:
    def __init__(self, parent: Services, name):
        self._service_name = name
        self._session = parent._session
        self._base_url = parent._baseURL
        self._actions = {}

        s = parent._services[name]
        self._service_type = s['serviceType']
        self._control_url = self._base_url+s['controlURL']

        # cache scpd data in parent class
        if name in parent._scpd:
            self._actions = parent._scpd[name]
        else:
            resp = self._session.get(
                self._base_url+parent._services[name]["SCPDURL"])
            soup = BeautifulSoup(resp.text, "lxml-xml")

            for a in soup.findAll('action'):
                aname = a.findChild('name').text.strip()
                shortname = aname.replace('X_AVM-DE_', '')
                args = []
                retvals = []
                for argument in a.findAll('argument'):
                    argname = argument.findChild('name').text.strip()
                    if argument.direction.text.strip() == 'out':
                        retvals.append(argname)
                    else:
                        args.append(argname)
                self._actions[shortname] = {
                    'name': aname, 'arguments': args, 'returnvalues': retvals}
            parent._scpd[name] = self._actions

    def _soap_action(self, surl, sservice, saction, sarguments={}):
        header = {
            'Content-Type': 'text/xml; charset="utf-8"',
            'SOAPACTION': f"{sservice}#{saction}"
        }
        response = self._session.post(
            url=surl,
            headers=header,
            data=self._create_soap_request(saction, sservice, sarguments),
            timeout=31
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml-xml")

        return (response.status_code, soup)

    def _create_soap_request(self, saction, sservice, arguments={}):
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

    def __getattr__(self, name):
        if name in self._actions:
            action = self._actions[name]

            def f(**kwargs):
                status, soup = self._soap_action(self._control_url,
                                                 self._service_type,
                                                 action['name'],
                                                 kwargs)
                if status >= 500:
                    code = soup.find("errorCode").text
                    desc = soup.find("errorDescription").text
                    raise Exception(f"UPnPError({code}): {desc}")

                response = soup.find(f"u:{action['name']}Response")
                ret = {}
                for x in response.children:
                    if isinstance(x, Tag):
                        if x.text.isnumeric():
                            ret[x.name] = int(x.text)
                        else:
                            ret[x.name] = x.text

                if len(ret) == 1:
                    return list(ret.values())[0]

                return ret

            return f

        s = f"'{self._service_name}-Service' object has no attribute '{name}'"
        raise AttributeError(s)

    def getList(self, listpath):
        hostlisturl = self._base_url+listpath
        response = self._session.get(hostlisturl)
        soup = BeautifulSoup(response.text, "lxml-xml")
        response.raise_for_status()

        items = []
        for item in soup.List:
            if isinstance(item, Tag):
                items.append(
                    {child.name: child.text
                        for child in item if isinstance(child, Tag)}
                )
        return items

    def __repr__(self):
        return f"<class 'Service: {self._service_name}>"

    def listMethods(self):
        return list(self._actions.keys())

    def methodHelp(self, name):
        if name in self._actions:
            s = f"{name}\n\n"
            for x in self._actions[name]['arguments']:
                s += f":param {x}\n"
            rets = self._actions[name]['returnvalues']
            s += f":return {{{', '.join(rets)}}}"

            return s

        raise ValueError('bad method')

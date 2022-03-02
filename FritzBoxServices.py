from pathlib import Path
from bs4 import BeautifulSoup, Tag
import requests
from requests.auth import HTTPDigestAuth


class Services:
    def __init__(self,
                 user,
                 password,
                 certificate=None,
                 fritzboxUrl="https://fritz.box"):
        self._baseURL = fritzboxUrl.rstrip('/')+"/tr064"
        self._session = requests.Session()

        self._session.auth = HTTPDigestAuth(user, password)
        self._session.verify = certificate

        p = Path("./SCPD_Files/tr64desc.xml")
        if not p.exists():
            print("downloading scpd files")
            self._dump_SCPD()

        with p.open("r") as fp:
            soup = BeautifulSoup(fp.read(), "lxml-xml")

        d = {}
        for service in soup.findAll('service'):
            if isinstance(service, Tag):
                name = service.serviceType.text.split(':')[-2]
                friendlyName = name.replace('X_AVM-DE_', '')
                d[friendlyName] = {x.name: x.text.strip()
                                   for x in service if isinstance(x, Tag)}
        self._services = d

    def _dump_SCPD(self):
        resp = self._session.get(self._baseURL+"/tr64desc.xml")
        soup = BeautifulSoup(resp.text, "lxml-xml")

        p = Path("./SCPD_Files")
        if not p.exists():
            p.mkdir()
        open("./SCPD_Files/tr64desc.xml", "w").write(soup.prettify())

        for x in soup.findAll("SCPDURL"):
            resp = self._session.get("https://fritz.box/tr064"+x.text)
            soup = BeautifulSoup(resp.text, "lxml-xml")
            open("./SCPD_Files"+x.text, "w").write(soup.prettify())

    def __getattr__(self, name):
        if name in self._services.keys():
            return _Service(self, name)
        raise AttributeError(f"'Services' object has no attribute '{name}'")

    def listServices(self):
        return list(self._services.keys())

    def serviceInfo(self, name):
        if name in self._services.keys():
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
    def __init__(self, parent, name):
        self._serviceName = name
        # self._parent = parent
        self._session = parent._session
        self._baseUrl = parent._baseURL

        s = parent._services[name]
        self._serviceType = s['serviceType']
        self._controlURL = self._baseUrl+s['controlURL']

        with Path("./SCPD_Files"+s['SCPDURL']).open('r') as fp:
            soup = BeautifulSoup(fp.read(), "lxml-xml")

        self._actions = {}
        for action in soup.findAll('action'):
            name = action.findChild('name').text.strip()
            friendlyName = name.replace('X_AVM-DE_', '')
            args = []
            returnvalues = []
            for argument in action.findAll('argument'):
                argname = argument.findChild('name').text.strip()
                if argument.direction.text.strip() == 'out':
                    returnvalues.append(argname)
                else:
                    args.append(argname)
            self._actions[friendlyName] = {
                'name': name, 'arguments': args, 'returnvalues': returnvalues}

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
        if name in self._actions.keys():
            action = self._actions[name]

            def f(**kwargs):
                status, soup = self._soap_action(self._controlURL,
                                                 self._serviceType,
                                                 action['name'],
                                                 kwargs)
                if status >= 500:
                    code = soup.find("errorCode").text
                    desc = soup.find("errorDescription").text
                    raise Exception(f"UPnPError({code}): {desc}")

                response = soup.find(f"u:{action['name']}Response")
                retVals = {}
                for x in response.children:
                    if isinstance(x, Tag):
                        if x.text.isnumeric():
                            retVals[x.name] = int(x.text)
                        else:
                            retVals[x.name] = x.text

                if len(retVals) == 1:
                    return list(retVals.values())[0]

                return retVals

            return f

        s = f"'{self._serviceName}-Service' object has no attribute '{name}'"
        raise AttributeError(s)

    def getList(self, listPath):
        hostlistUrl = self._baseUrl+listPath
        response = self._session.get(hostlistUrl)
        soup = BeautifulSoup(response.text, "lxml-xml")

        items = []
        for item in soup.List:
            if isinstance(item, Tag):
                items.append(
                    {child.name: child.text
                        for child in item if isinstance(child, Tag)}
                )
        return items

    def __repr__(self):
        return f"<class 'Service: {self._serviceName}>"

    def listMethods(self):
        return list(self._actions.keys())

    def methodHelp(self, name):
        if name in self._actions.keys():
            s = f"{name}\n\n"
            for x in self._actions[name]['arguments']:
                s += f":param {x}\n"
            rets = self._actions[name]['returnvalues']
            s += f":return {{{', '.join(rets)}}}"

            return s

        raise ValueError('bad method')
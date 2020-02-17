from pathlib import Path
from bs4 import BeautifulSoup, Tag
from fritzbox_soap import soap_action
from discover_services import dump_SCPD


class Services:
    def __init__(self):
        self._baseURL = "https://fritz.box:40888/tr064"
        p = Path("./SCPD_Files/tr64desc.xml")
        if not p.exists():
            print("downloading scpd files")
            dump_SCPD()
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

    def __getattr__(self, name):
        if name in self._services.keys():
            service = self._services[name]
            return _Service(name,
                            service['serviceType'],
                            self._baseURL+service['controlURL'],
                            service['SCPDURL'])
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
    def __init__(self, name, serviceType, controlURL, scpdUrl):
        self._serviceName = name
        self._serviceType = serviceType
        self._controlURL = controlURL
        with Path("./SCPD_Files"+scpdUrl).open('r') as fp:
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

    def __getattr__(self, name):
        if name in self._actions.keys():
            action = self._actions[name]

            def f(**kwargs):

                # check args before request or not ?
                status, soup = soap_action(self._controlURL,
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

                return retVals

            return f

        s = f"'{self._serviceName}-Service' object has no attribute '{name}'"
        raise AttributeError(s)

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


if __name__ == "__main__":
    services = Services()
    # print(services.listServices())
    # print(services.serviceInfo('Homeauto'))
    # print(services.Homeauto.listMethods())
    print(services.Homeauto.methodHelp('GetGenericDeviceInfos'))
    print()
    print(services.Homeauto.GetGenericDeviceInfos(NewIndex=0))

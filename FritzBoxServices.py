from pathlib import Path
from bs4 import BeautifulSoup, Tag


class Services:
    def __init__(self):
        with Path("./SCPD_Files/tr64desc.xml").open("r") as fp:
            soup = BeautifulSoup(fp.read(), "lxml-xml")

        self._services = {}
        for service in soup.findAll('service'):
            if isinstance(service, Tag):
                name = service.serviceType.text.split(':')[-2]
                friendlyName = name.replace('X_AVM-DE_', '')
                self._services[friendlyName] = {x.name: x.text.strip()
                                        for x in service if isinstance(x, Tag)}

    def __getattr__(self, name):
        if name in self._services.keys():
            return Service(name, self._services[name]['SCPDURL'])
        raise AttributeError(f"'Services' object has no attribute '{name}'")

    def listServices(self):
        return list(self._services.keys())

    def serviceInfo(self, name):
        # TODO error handling
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
        else:
            raise ValueError('bad method')



class Service:
    def __init__(self, serviceType, scpd_url):
        self._serviceType = serviceType
        with Path("./SCPD_Files"+scpd_url).open('r') as fp:
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
            self._actions[friendlyName] = {'name': name, 'arguments': args, 'returnvalues':returnvalues}

        # TODO parse SCPD file

    def __getattr__(self, name):
        if name in self._actions.keys():
            return lambda: print(name)
        raise AttributeError(f"'Service' object has no attribute '{name}'")

    def __repr__(self):
        return f"<class 'Service: {self._serviceType}>"

    def listMethods(self):
        return list(self._actions.keys())

    # wie in https://docs.python.org/3/library/xmlrpc.client.html#serverproxy-objects
    def methodSignature(self, name):
        raise NotImplementedError

    def methodHelp(self, name):
        if name in self._actions.keys():
            s = f"{name}\n\n"
            for x in self._actions[name]['arguments']:
                s += f":param {x}\n"
            rets = self._actions[name]['returnvalues']
            s += f":return {{{', '.join(rets)}}}"

            return s
        else:
            raise ValueError('bad method')


if __name__ == "__main__":
    services = Services()
    print(services.listServices())
    print(services.serviceInfo('Homeplug'))
    print(services.Homeplug.listMethods())
    print(services.Homeplug.methodHelp('GetGenericDeviceEntry'))
    # print(services.Hosts.SetHostNameByMACAddress)

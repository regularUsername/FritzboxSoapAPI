import argparse
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from bs4 import BeautifulSoup, Tag
import requests
from requests.auth import HTTPDigestAuth


def parseSCPD(markup):
    soup = BeautifulSoup(markup, "lxml-xml")
    actions = {}
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
        actions[friendlyName] = {
            'name': name, 'arguments': args, 'returnvalues': returnvalues}
    return actions


def parse_tr64desc(markup):
    soup = BeautifulSoup(markup, "lxml-xml")

    d = {}
    for service in soup.findAll('service'):
        if isinstance(service, Tag):
            name = service.serviceType.text.split(':')[-2]
            friendlyName = name.replace('X_AVM-DE_', '')
            d[friendlyName] = {x.name: x.text.strip()
                               for x in service if isinstance(x, Tag)}
    return d


def stub_generator(user: str,
                   password: str,
                   certificate: str = None,
                   output_path: str = "./",
                   fritzbox_url: str = "https://fritz.box"):

    base_url = fritzbox_url.rstrip("/")+"/tr064"
    session = requests.Session()
    session.auth = HTTPDigestAuth(user, password)
    session.verify = certificate
    resp = session.get(base_url+"/tr64desc.xml")
    resp.raise_for_status()
    services = parse_tr64desc(resp.text)
    for _, v in services.items():
        resp = session.get(base_url+v['SCPDURL'])
        resp.raise_for_status()
        v['actions'] = parseSCPD(resp.text)

    env = Environment(
        loader=FileSystemLoader(Path(__file__).parent.joinpath("template"))
    )

    template = env.get_template('ServiceTemplate.py')

    p = Path(output_path, encoding="utf-8")
    if p.is_dir():
        p = p.joinpath("Services.py")
    with p.open('w') as fp:
        fp.write(template.render(services=services))


def run():
    parser = argparse.ArgumentParser(
        description='Generate stubs for the FritzBox SOAP API')
    parser.add_argument('-u', '--user', required=True, help="Admin Username")
    parser.add_argument('-p', '--password', required=True,
                        help="Admin Password")
    parser.add_argument('--cert', dest='certificate',
                        help="Path to public key of the FritzBox for verification (optional)")
    parser.add_argument('--output', dest='output_path', default='./',
                        help="Output Directory or File, default name is Services.py (optional)")
    parser.add_argument('--url', dest='fritzbox_url', default='https://fritz.box',
                        help='Url to the FritzBox, default is "https://fritz.box" (optional)')
    args = parser.parse_args()
    p = Path(args.output_path)
    if not p.is_dir() and p.suffix != '.py':
        print("invalid output_path, must be a valid directory or filename ending with .py")
        return
    stub_generator(**vars(args))


if __name__ == "__main__":
    run()

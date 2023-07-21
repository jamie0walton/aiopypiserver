"""Provide a basic pypi server."""
import asyncio
import argparse
import logging
from aiohttp import web, MultipartReader
from pathlib import Path
import importlib.resources
from importlib.abc import Traversable
import tarfile
from zipfile import ZipFile
from base64 import b64decode
from . import assets


def args():
    """Configure command-line switches."""
    parser = argparse.ArgumentParser(
        prog='aiopypiserver',
        description='Private PyPi server.',
        epilog='Browse index at http://localhost:8080/.'
    )
    parser.add_argument('package_path', type=str, nargs='?',
                        default='packages', help='path to packages')
    parser.add_argument('-p', '--port', metavar='port', type=int,
                        nargs='?', default=8080, help='Listen on port')
    parser.add_argument('-i', '--interface', metavar='address', type=str,
                        nargs='?', default='localhost',
                        help='Listen on address')
    parser.add_argument('-u', '--username', metavar='username', type=str,
                        nargs='?', help='For uploading packages')
    parser.add_argument('-P', '--password', metavar='password', type=str,
                        nargs='?', help='...')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='set debug level')
    parser.add_argument('-q', '--quiet', action='store_true',
                        help='turn off access logging')
    return parser.parse_args()


def get(filename) -> Traversable:
    """Provide file resources to package."""
    fh = importlib.resources.files(assets).joinpath(filename)
    if fh.is_file():
        return fh
    else:
        raise FileNotFoundError(filename)


def name_version(lines):
    """Find name and version from file."""
    for line in lines.splitlines():
        if line.startswith(b'Name: '):
            pkgname = line[6:].decode()
        elif line.startswith(b'Version: '):
            version = line[9:].decode()
    pkgname = pkgname.replace('_', '-').replace('.', '-')
    return pkgname, version


def name_version_from_zip(pkg):
    """Find name and version from METADATA file in tar.gz package."""
    lines = None
    with ZipFile(pkg) as zf:
        for name in zf.namelist():
            if name.endswith('/METADATA'):
                with zf.open(name) as mdf:
                    lines = mdf.read()
                    break
    if lines is None:
        return None, None
    return name_version(lines)


def name_version_from_tar(pkg):
    """Find name and version from PKG-INFO file in wheel."""
    lines = None
    with tarfile.open(pkg, 'r') as tf:
        for member in tf.getmembers():
            if member.name.endswith('/PKG-INFO'):
                with tf.extractfile(member) as mdf:
                    lines = mdf.read()
                    break
    if lines is None:
        return None, None
    return name_version(lines)


def add_file_name_version(info, file, name, version):
    """Build dictionary of files, module names and versions."""
    info['files'][file] = {'name': name, 'version': version}
    try:
        info['names'][name].append({'file': file, 'version': version})
    except KeyError:
        info['names'][name] = [{'file': file, 'version': version}]


def get_package_details(pkg_path):
    """Build a dict of files, names and versions."""
    info = {'files': {}, 'names': {}}
    for pkg in pkg_path.iterdir():
        name, version = None, None
        if pkg.name.endswith('.whl'):
            name, version = name_version_from_zip(pkg)
        elif pkg.name.endswith('.tar') or pkg.name.endswith('.tar.gz'):
            name, version = name_version_from_tar(pkg)
        add_file_name_version(info, pkg.name, name, version)
    return info


async def on_prepare(request, response):
    """Hack header to stop client uncompressing tar.gz files."""
    if 'prunecontent' in response.headers:
        del response.headers['prunecontent']
        try:
            del response.headers['Content-Encoding']
        except KeyError:
            pass


class WebServer():
    """Serve PyPi web pages."""

    def __init__(self, config):
        """Initialise with an argparse NameSpace."""
        self.ip = config.interface
        self.port = config.port
        self.packages = config.package_path
        self.pkg_path = Path('.').joinpath(self.packages).resolve()
        self.username = config.username
        self.password = config.password
        logging.info(f"Running on {self.ip}:{self.port} "
                     f"serving {self.packages}")
        self.info = get_package_details(self.pkg_path)
        if not self.pkg_path.is_dir():
            raise RuntimeError(f"{self.pkg_path} bad package directory")
        self.webapp = web.Application()
        routes = [web.get('/', self.index_handler),
                  web.get('/index.html', self.index_handler),
                  web.get('/packages/', self.packages_handler),
                  web.get('/simple/', self.simple_handler),
                  web.get('/simple/{package}/', self.simple_package_handler),
                  web.get('/packages/{file}', self.packages_file_handler),
                  web.post('', self.post_handler),
                  web.get('/{file}', self.file_handler)]
        self.webapp.add_routes(routes)
        self.webapp.on_response_prepare.append(on_prepare)
        self.runner = web.AppRunner(self.webapp)

    def index_handler(self, request: web.Request):
        """Provide the base index.html file."""
        html = open(get('index.html')).read()
        for k, v in [('ip', self.ip),
                     ('port', str(self.port))]:
            html = html.replace(r'{{' + k + r'}}', v)
        return web.Response(body=html, content_type='text/html')

    def file_handler(self, request: web.Request):
        """Provide the any pages that might be in assets."""
        try:
            return web.FileResponse(get(request.match_info['file']))
        except FileNotFoundError:
            raise web.HTTPNotFound

    def packages_handler(self, request: web.Request):
        """Provide a list of modules or all packages."""
        dirlist = ''
        for file in self.pkg_path.iterdir():
            dirlist += f'\n<a href="{file.name}">{file.name}</a><br>'
        html = open(get('list.html')).read()
        html = html.replace(r'{{title}}', 'Package Index')
        html = html.replace(r'{{dirlist}}', dirlist)
        return web.Response(body=html, content_type='text/html')

    def simple_handler(self, request: web.Request):
        """Provide a list of modules or all packages."""
        dirlist = ''
        title = 'Simple Index'
        for pkg in self.info['names'].items():
            dirlist += f'\n<a href="{pkg[0]}/">{pkg[0]}</a><br>'
        html = open(get('list.html')).read()
        html = html.replace(r'{{title}}', title)
        html = html.replace(r'{{dirlist}}', dirlist)
        return web.Response(body=html, content_type='text/html')

    def simple_package_handler(self, request: web.Request):
        """Provide a list of links for a specific module."""
        pkg = request.match_info['package']
        dirlist = ''
        if pkg not in self.info['names']:
            raise web.HTTPNotFound
        if pkg in self.info['names']:
            for fileinfo in self.info['names'][pkg]:
                file = fileinfo['file']
                dirlist += f'\n<a href="../../{self.packages}/{file}">{file}' \
                           '</a><br>'
        html = open(get('list.html')).read()
        html = html.replace(r'{{title}}', f"Links for {pkg}")
        html = html.replace(r'{{dirlist}}', dirlist)
        return web.Response(body=html, content_type='text/html')

    def packages_file_handler(self, request: web.Request):
        """Provide the zipped package file, prunecontent for later."""
        file = request.match_info['file']
        filepath = self.pkg_path.joinpath(file)
        if filepath.is_file():
            # response = web.FileResponse(filepath)
            # response.enable_compression
            return web.FileResponse(filepath, headers={'prunecontent': True})
        else:
            raise web.HTTPNotFound

    async def post_handler(self, request: web.Request):
        """Receive uploaded packages."""
        if 'Authorization' not in request.headers or self.username is None \
                or self.password is None:
            raise web.HTTPNotAcceptable
        auth = request.headers['Authorization'].split(' ')
        username, password = b64decode(auth[1]).decode().split(':')
        if self.username != username or self.password != password:
            raise web.HTTPForbidden
        reader = MultipartReader.from_response(request)
        name = None
        version = None
        while True:
            part = await reader.next()
            if part is None:
                break
            if part.name == 'name':
                name = await part.text()
            elif part.name == 'version':
                version = await part.text()
                if name in self.info and version in self.info['name']:
                    raise web.HTTPForbidden
            elif part.name == 'content':
                filename = part.filename
                dst_path = self.pkg_path.joinpath(filename)
                if dst_path.exists():
                    raise web.HTTPForbidden
                else:
                    try:
                        with open(dst_path, 'wb') as fh:
                            fh.write(await part.read())
                        add_file_name_version(self.info, dst_path.name, name,
                                              version)
                    except Exception:
                        if dst_path.exists():
                            dst_path.unlink()
        return web.Response()

    async def run(self):
        """Start the pypi webserver and return."""
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, self.ip, self.port)
        await self.site.start()


async def main():
    """Read config and run the server."""
    config = args()
    if config.username is None or config.password is None:
        logging.warn('empty password/username, uploading disabled')
    ws = WebServer(config)
    if config.verbose:
        logging.basicConfig(level=logging.INFO)
    await ws.run()
    await asyncio.get_running_loop().create_future()


def run():
    """Run from __main__.py for debugging."""
    asyncio.run(main())

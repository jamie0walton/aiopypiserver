from aiohttp import web, MultipartReader
from pathlib import Path
import importlib.resources
from importlib.abc import Traversable
import tarfile
from zipfile import ZipFile
from base64 import b64decode
from . import assets


def get(filename) -> Traversable:
    fh = importlib.resources.files(assets).joinpath(filename)
    if fh.is_file():
        return fh
    else:
        raise FileNotFoundError(filename)


def name_version(lines):
    for line in lines.splitlines():
        if line.startswith(b'Name: '):
            pkgname = line[6:].decode()
        elif line.startswith(b'Version: '):
            version = line[9:].decode()
    pkgname = pkgname.replace('_', '-').replace('.', '-')
    return pkgname, version


def name_version_from_zip(pkg):
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


def get_package_details(pkg_path):
    """Assume a tarfile."""
    info = {'files': {}, 'names': {}}
    for pkg in pkg_path.iterdir():
        name, version = None, None
        if pkg.name.endswith('.whl'):
            name, version = name_version_from_zip(pkg)
        elif pkg.name.endswith('.tar') or pkg.name.endswith('.tar.gz'):
            name, version = name_version_from_tar(pkg)
        info['files'][pkg.name] = {'name': name, 'version': version}
        try:
            info['names'][name].append({'file': pkg.name, 'version': version})
        except KeyError:
            info['names'][name] = [{'file': pkg.name, 'version': version}]
    return info


async def on_prepare(request, response):
    """Set the cache headers. Angular builds apps with a hash."""
    if 'prunecontent' in response.headers:
        del response.headers['prunecontent']
        try:
            del response.headers['Content-Encoding']
        except KeyError:
            pass


class WebServer():
    """Serve PyPi web pages."""

    def __init__(self, bind: str = '127.0.0.1:8080',
                 packages: str = 'packages'):
        self.ip, self.port = bind.split(':')
        self.packages = packages
        self.pkg_path = Path('.').joinpath(packages).resolve()
        self.info = get_package_details(self.pkg_path)
        if not self.pkg_path.is_dir():
            raise RuntimeError(f"{self.pkg_path} bad package directory")
        self.webapp = web.Application()
        routes = [web.get('/', self.redirect_handler),
                  web.get('/{file}', self.file_handler),
                  web.get('/{dir}/', self.dir_handler),
                  web.get('/{dir}/{file}', self.pkgfile_handler),
                  web.get('/{dir}/{file}/', self.package_handler),
                  web.post('', self.post_handler)]
        self.webapp.add_routes(routes)
        self.webapp.on_response_prepare.append(on_prepare)
        self.runner = web.AppRunner(self.webapp)

    async def post_handler(self, request: web.Request):
        auth = request.headers['Authorization'].split(' ')
        username, password = b64decode(auth[1]).decode().split(':')
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
                if name in self.info and version in self.info:
                    raise web.HTTPForbidden
            elif part.name == 'content':
                filename = part.filename
                dst_path = self.pkg_path.joinpath(filename)
                if not dst_path.exists():
                    with open(dst_path, 'wb') as fh:
                        fh.write(await part.read())
            pass
        return web.Response()

    def package_handler(self, request: web.Request):
        dir = request.match_info['dir']
        pkg = request.match_info['file']
        dirlist = ''
        if pkg not in self.info['names']:
            raise web.HTTPNotFound
        title = f"Links for {pkg}"
        if dir == 'simple':
            if pkg in self.info['names']:
                for fileinfo in self.info['names'][pkg]:
                    file = fileinfo['file']
                    dirlist += f'\n    <a href="{self.packages}/' \
                               f'{file}">{file}</a><br>'
            else:
                raise web.HTTPNotFound
        else:
            raise web.HTTPForbidden
        html = open(get('list.html')).read()
        html = html.replace(r'{{title}}', title)
        html = html.replace(r'{{dirlist}}', dirlist)
        return web.Response(body=html, content_type='text/html')

    def dir_handler(self, request: web.Request):
        dir = request.match_info['dir']
        dirlist = ''
        if dir == 'packages':
            title = 'Index of packages'
            for file in self.pkg_path.iterdir():
                dirlist += f'\n    <a href="{file.name}">' \
                           f'{file.name}</a><br>'
        elif dir == 'simple':
            title = 'Simple Index'
            for pkg in self.info['names'].items():
                dirlist += f'\n    <a href="{pkg[0]}/">' \
                           f'{pkg[0]}</a><br>'
        else:
            raise web.HTTPForbidden
        html = open(get('list.html')).read()
        html = html.replace(r'{{title}}', title)
        html = html.replace(r'{{dirlist}}', dirlist)
        return web.Response(body=html, content_type='text/html')

    def return_index(self):
        html = open(get('index.html')).read()
        for k, v in [('ip', self.ip),
                     ('port', self.port)]:
            html = html.replace(r'{{' + k + r'}}', v)
        return web.Response(body=html, content_type='text/html')

    def redirect_handler(self, request: web.Request):
        return self.return_index()

    def pkgfile_handler(self, request: web.Request):
        file = request.match_info['file']
        filepath = self.pkg_path.joinpath(file)
        if filepath.is_file():
            # response = web.FileResponse(filepath)
            # response.enable_compression
            return web.FileResponse(filepath, headers={'prunecontent': True})
        else:
            raise web.HTTPNotFound

    def file_handler(self, request: web.Request):
        file = request.match_info['file']
        if file == 'index.html':
            return self.return_index()
        else:
            try:
                return web.FileResponse(get(file))
            except FileNotFoundError:
                raise web.HTTPNotFound

    async def run(self):
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, self.ip, self.port)
        await self.site.start()

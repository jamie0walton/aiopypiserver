from io import BytesIO
from aiohttp import web
from pathlib import Path
from . import assets
import importlib.resources
from importlib.abc import Traversable


def get(filename) -> Traversable:
    fh = importlib.resources.files(assets).joinpath(filename)
    if fh.is_file():
        return fh
    else:
        raise FileNotFoundError(filename)


class WebServer():
    """Serve PyPi web pages."""

    def __init__(self, bind: str = '127.0.0.1:8080',
                 packages: str = 'packages'):
        self.ip, self.port = bind.split(':')
        self.pkg_path = Path('.').joinpath(packages).resolve()
        if not self.pkg_path.is_dir():
            raise RuntimeError(f"{self.pkg_path} bad package directory")

    def file_handler(self, request: web.Request):
        file = request.match_info['file']
        if file in ('', 'index.html'):
            html = open(get('index.html')).read()
            for k, v in [('ip', self.ip),
                         ('port', self.port)]:
                html = html.replace(r'{{' + k + r'}}', v)
            return web.Response(text=html)
        else:
            return web.FileResponse(get(file))

    def prepare(self):
        self.webapp = web.Application()
        routes = [web.get('/{file}', self.file_handler)]
        self.webapp.add_routes(routes)
        self.runner = web.AppRunner(self.webapp, access_log=None)

    async def run(self):
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, self.ip, self.port)
        await self.site.start()

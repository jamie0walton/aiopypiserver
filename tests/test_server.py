import pytest
import pytest_asyncio
import asyncio
from pathlib import Path
import logging
from aiopypiserver.webserver import get, WebServer, get_package_details


def test_file():
    with open(get('index.html'), 'r') as fh:
        html = fh.read()
        lines = html.splitlines()
        assert lines[0] == '<!DOCTYPE html>'


def test_get_package_info():
    info = get_package_details(Path('.').joinpath('packages').resolve())
    assert True


@pytest.fixture(scope='module')
def event_loop():
    """Override default scope from function to module."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope='module')
async def webserver():
    ws = WebServer()
    await ws.run()
    yield


@pytest.mark.asyncio
async def test_webserver(webserver):
    logging.basicConfig(level=logging.INFO)
    await asyncio.sleep(1000000)
    assert True

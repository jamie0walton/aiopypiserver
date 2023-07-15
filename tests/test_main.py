import pytest
import aiopypiserver


def test_run():
    assert aiopypiserver.run() == 'hi'


@pytest.mark.asyncio
async def test_run_ws():
    ws = aiopypiserver.WebServer()
    await ws.run()
    assert True

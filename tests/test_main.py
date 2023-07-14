import aiopypiserver


def test_run():
    assert aiopypiserver.run() == 'hi'

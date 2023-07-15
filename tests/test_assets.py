from aiopypiserver.webserver import get, file_handler


def test_file():
    with open(get('index.html'), 'r') as fh:
        html = fh.read()
        lines = html.splitlines()
        assert lines[0] == '<!DOCTYPE html>'
        assert lines[8] == '    <p>{{var}}</p>'


def test_file_handler():
    class Request():
        match_info = {
            'file': ''
        }

    res = file_handler(Request())
    assert True

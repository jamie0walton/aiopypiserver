# aiopypiserver

A basic PyPi server using aiohttp to serve web pages. Intended to work behind
an Apache proxy with relative href accessing.

# Motivation

This is intended to work behind an Apache proxy. This means providing
href links in the pages as relative links. i.e. ./packages/pkg_name.tar.gz
and not /packages... .

This is addressed as provided by [WSGI](https://github.com/pypiserver/pypiserver/issues/155).
Looking at the code I liked the idea of implementing with ```asyncio``` and ```aiohttp```
in preference to forking the ```pypiserver``` code.

# Usage

```
usage: aiopypiserver [-h] [-p port] [-i address] [-u username] [-P password] [-v] [-q] [package_path]                                                   
Private PyPi  server.

positional arguments:
  package_path                       path to packages

options:
  -h, --help                         show this help message and exit
  -p port, --port port               Listen on port
  -i address, --interface address    Listen on address
  -u username, --username username   For uploading packages
  -P password, --password password   ...
  -v, --verbose                      set debug level
  -q, --quiet                        turn off access logging

Browse index at http://localhost:8080/.
```

Can also be run as a module as ```python -m aiopypiserver -h```. Using the internal class is probably a bad idea ATM as the API is likely to change.

By default access logs are generated, as I find it useful to see these.

# Thanks

Please let me know how you get on through the github page.

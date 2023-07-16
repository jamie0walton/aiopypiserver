import asyncio
import argparse
import logging
from aiopypiserver import WebServer


def args():
    parser = argparse.ArgumentParser(
        prog='aiopypiserver',
        description='Private PyPi server.',
        epilog='Browse index at http://localhost:8080/.'
    )
    parser.add_argument('package_path', type=str, nargs='?',
                        default='packages', help='path to packages')
    parser.add_argument('-p', metavar='port', type=int, nargs=1,
                        default=8080, help='Listen on port')
    parser.add_argument('-i', metavar='address', type=str, nargs=1,
                        default='localhost', help='Listen on address')
    parser.add_argument('-u', metavar='username', type=str, nargs=1,
                        help='For uploading packages')
    parser.add_argument('-P', metavar='password', type=str, nargs=1,
                        help='...')
    return parser.parse_args()


async def main():
    config = args()
    print(config)
    ws = WebServer()
    logging.basicConfig(level=logging.INFO)
    await ws.run()
    await asyncio.get_running_loop().create_future()


if __name__ == '__main__':
    asyncio.run(main())

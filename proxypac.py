#!/usr/bin/env python3

import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer


class ProxyPacHandler(BaseHTTPRequestHandler):
    def __init__(self, pac, *args):
        self._pac = pac
        BaseHTTPRequestHandler.__init__(self, *args)

    def do_GET(self):
        print(f'Request header: {self.headers["Host"]} {self.headers["User-Agent"]}')

        self.send_response(200)
        self.send_header('Content-type', 'application/x-ns-proxy-autoconfig')
        self.end_headers()

        self.wfile.write(self._pac)


class PACServer(object):
    def __init__(self, proxy_ip: str, proxy_port: int, pac_port: int, type: str, verbose=False):
        self._ip = proxy_ip
        self._port = proxy_port
        self._pac_port = pac_port
        self._type = type.upper()
        self._verbose = verbose
        self._pac = self.proxy_pac()

        def pac_handler(*args):
            ProxyPacHandler(self._pac, *args)

        self._server = HTTPServer((self._ip, self._pac_port), pac_handler)

    def start(self):
        print(f'Server start at {self._ip}:{self._pac_port}. Happy hunting!\n')
        if self._verbose:
            print(self._pac.decode('utf-8'))

        print('Use this address for your device proxy settings:')
        print(f'http://{self._ip}:{self._pac_port}')

        try:
            self._server.serve_forever()
        except KeyboardInterrupt:
            self._server.server_close()

        if self._verbose:
            print('\nServer shutdown')

    def proxy_pac(self):
        return f'''\
function FindProxyForURL(url, host) {{
    url = url.toLowerCase();
    host = host.toLowerCase();
    if (isInNet(host, "10.0.0.0", "255.0.0.0") ||
        isInNet(host, "172.16.0.0", "255.240.0.0") ||
        isInNet(host, "192.168.0.0", "255.255.0.0") ||
        isInNet(host, "127.0.0.0", "255.255.255.0")) {{
        return "DIRECT";
    }}

    return "{self._type} {self._ip}:{self._port}";
}}'''.encode('utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='A little Proxy PAC server')
    parser.add_argument('proxy_ip', metavar='IP_ADDRESS')
    parser.add_argument('proxy_port', metavar='PORT')
    parser.add_argument('proxy_type', metavar='TYPE', type=str.upper,
                        choices=['SOCKS', 'SOCKS4', 'SOCKS5', 'HTTP', 'HTTPS'])
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()

    PACServer(args.proxy_ip, args.proxy_port, 9010, args.proxy_type,
              verbose=args.verbose).start()

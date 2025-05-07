#!/usr/bin/env python
# This script uploads a plugin package on the server
#
# Author: A. Pasotti, V. Picavet

import xmlrpc.client, sys
import getpass
from optparse import OptionParser

# Configuration
PROTOCOL = 'http'
SERVER = 'plugins.qgis.org'
PORT = '80'
ENDPOINT = '/plugins/RPC2/'
VERBOSE = False

def main(options, args):
    address = f"{PROTOCOL}://{options.username}:{options.password}@{options.server}:{options.port}{ENDPOINT}"
    print("Connecting to:", hidepassword(address))

    server = xmlrpc.client.ServerProxy(address, verbose=VERBOSE)

    try:
        with open(args[0], 'rb') as plugin_file:
            plugin_id, version_id = server.plugin.upload(xmlrpc.client.Binary(plugin_file.read()))
        print("Plugin ID:", plugin_id)
        print("Version ID:", version_id)
    except xmlrpc.client.ProtocolError as err:
        print("A protocol error occurred")
        print("URL:", hidepassword(err.url, 0))
        print("HTTP/HTTPS headers:", err.headers)
        print("Error code:", err.errcode)
        print("Error message:", err.errmsg)
    except xmlrpc.client.Fault as err:
        print("A fault occurred")
        print("Fault code:", err.faultCode)
        print("Fault string:", err.faultString)

def hidepassword(url, start=6):
    """Returns the http url with password part replaced with '*'."""
    passdeb = url.find(':', start) + 1
    passend = url.find('@')
    return f"{url[:passdeb]}{'*' * (passend - passdeb)}{url[passend:]}"


if __name__ == "__main__":
    parser = OptionParser(usage="%prog [options] plugin.zip")
    parser.add_option("-w", "--password", dest="password",
            help="Password for plugin site", metavar="******")
    parser.add_option("-u", "--username", dest="username",
            help="Username of plugin site", metavar="user")
    parser.add_option("-p", "--port", dest="port",
            help="Server port to connect to", metavar="80")
    parser.add_option("-s", "--server", dest="server",
            help="Specify server name", metavar="plugins.qgis.org")
    (options, args) = parser.parse_args()
    if len(args) != 1:
        # fix_print_with_import
        print("Please specify zip file.\n")
        parser.print_help()
        sys.exit(1)
    if not options.server:
        options.server = SERVER
    if not options.port:
        options.port = PORT
    if not options.username:
        # interactive mode
        username = getpass.getuser()
        # fix_print_with_import
        # fix_print_with_import
        print(f"Please enter user name [{username}] : ", end=' ')
        res = input()
        if res != "":
            options.username = res
        else:
            options.username = username
    if not options.password:
        # interactive mode
        options.password = getpass.getpass()
    main(options, args)

#!/usr/bin/env python
"""
Find VM's uuid by name
"""

import atexit
import argparse
import getpass
import sys
import time
import pprint

from pyVim import connect
from pyVmomi import vim, vmodl
from pyVim.connect import SmartConnectNoSSL, Disconnect


def get_args():
    """ Get arguments from CLI """
    parser = argparse.ArgumentParser(
        description='Arguments for talking to vCenter')

    parser.add_argument('-s', '--host',
                        required=True,
                        action='store',
                        help='vSpehre service to connect to')

    parser.add_argument('-o', '--port',
                        type=int,
                        default=443,
                        action='store',
                        help='Port to connect on')

    parser.add_argument('-u', '--user',
                        required=True,
                        action='store',
                        help='Username to use')

    parser.add_argument('-p', '--password',
                        required=False,
                        action='store',
                        help='Password to use')

    parser.add_argument('-v', '--vm-name',
                        required=True,
                        action='store',
                        help='Name of the VM you wish to find')

    args = parser.parse_args()

    if not args.password:
        args.password = getpass.getpass(
            prompt='Enter password')

    return args

def get_vm(content, name):
    """ Gets a named virtual machine. """
    virtual_machine = None
    container = content.viewManager.CreateContainerView(content.rootFolder,
                                                        [vim.VirtualMachine],
                                                        True)
    for item in container.view:
        if item.name == name:
            virtual_machine = item
            break
    container.Destroy()  # Best practice. Frees up resources on host.
    return virtual_machine


def main():
    """
    Let this thing fly
    """
    args = get_args()

    # connect this thing
    si = connect.SmartConnectNoSSL(
        host=args.host,
        user=args.user,
        pwd=args.password,
        port=args.port
    )
    # disconnect this thing
    atexit.register(Disconnect, si)

    content = si.RetrieveContent()

    virtual_machine = get_vm(content, args.vm_name)

    vm_uuid = virtual_machine.config.instanceUuid

    print "VM name: " + virtual_machine.name + "\nuuid is: " + vm_uuid

    # find VM name by uuid (reverse lookup check) 
    """
    search_index = si.content.searchIndex
    vm = search_index.FindByUuid(None, vm_uuid, True, True)
    print vm.name
    """

# start this thing
if __name__ == "__main__":
    main()
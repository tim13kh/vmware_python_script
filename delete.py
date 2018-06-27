#!/usr/bin/env python
# Copyright 2015 Michael Rice <michael@michaelrice.org>
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""
/usr/bin/python2.7 /opt/jenkins-files/delete.py \
     -s 'Vcenter.domain.com' \
     -u 'user' \
     -p 'password' \
     -v 'vm-delete-01' \
     -o '443' \
     -t 'https'
"""

from __future__ import print_function

import atexit
import argparse
import getpass
import sys
import time

from pyVim import connect

from pyVmomi import vim

from tools import tasks


def setup_args():

    parser = argparse.ArgumentParser()
    """Adds additional ARGS to allow the vm name or uuid to
    be set.
    """
    parser.add_argument('-s', '--host',
                        required=True,
                        action='store',
                        help='Remote host to connect to example my-lab-01.domain.com without http URL')

    parser.add_argument('-u', '--user',
                        required=True,
                        action='store',
                        help='User name to use when connecting to host')

    parser.add_argument('-p', '--password',
                        required=False,
                        action='store',
                        help='Password to use when connecting to host')

    parser.add_argument('-t', '--protocol',
                        required=False,
                        action='store',
                        help='Protocol to use when connecting to host, can be https or http')

    parser.add_argument('-o', '--port',
                        required=False,
                        action='store',
                        help="port to use, default 443", default=443)

    parser.add_argument('-j', '--uuid',
                        help='BIOS UUID of the VirtualMachine you want '
                             'to destroy.')
    parser.add_argument('-n', '--name',
                        help='DNS Name of the VirtualMachine you want to '
                             'destroy.')
    parser.add_argument('-i', '--ip',
                        help='IP Address of the VirtualMachine you want to '
                             'destroy')
    parser.add_argument('-v', '--vm',
                        help='VM name of the VirtualMachine you want '
                             'to destroy.')

    args = parser.parse_args()
    if args.password is None:
        args.password = getpass.getpass(
            prompt='Enter password for host %s and user %s: ' %
                   (args.host, args.user))

    args = parser.parse_args()

    return args

def get_obj(content, vimtype, name):

    """Create contrainer view and search for object in it"""
    obj = None
    container = content.viewManager.CreateContainerView(
        content.rootFolder, vimtype, True)
    for c in container.view:
        if name:
            if c.name == name:
                obj = c
                break
        else:
            obj = c
            break

    container.Destroy()
    return obj

ARGS = setup_args()
# form a connection...
SI = connect.SmartConnectNoSSL(
        protocol = ARGS.protocol,
        host = ARGS.host,
        user = ARGS.user,
        pwd = ARGS.password,
        port = ARGS.port
    )

# doing this means you don't need to remember to disconnect your script/objects
atexit.register(connect.Disconnect, SI)

VM = None
if ARGS.vm:
    VM = get_obj(SI.content, [vim.VirtualMachine], ARGS.vm)
elif ARGS.uuid:
    VM = SI.content.searchIndex.FindByUuid(None, ARGS.uuid,
                                           True,
                                           False)
elif ARGS.name:
    VM = SI.content.searchIndex.FindByDnsName(None, ARGS.name,
                                              True)
elif ARGS.ip:
    VM = SI.content.searchIndex.FindByIp(None, ARGS.ip, True)

if VM is None:
    raise SystemExit(
        "Unable to locate VirtualMachine. Arguments given: "
        "vm - {0} , uuid - {1} , name - {2} , ip - {3}"
        .format(ARGS.vm, ARGS.uuid, ARGS.name, ARGS.ip)
        )

print("Found: {0}".format(VM.name))
print("The current powerState is: {0}".format(VM.runtime.powerState))
if format(VM.runtime.powerState) == "poweredOn":
    print("Attempting to power off {0}".format(VM.name))
    TASK = VM.PowerOffVM_Task()
    tasks.wait_for_tasks(SI, [TASK])
    print("{0}".format(TASK.info.state))

print("Destroying VM from vSphere.")
TASK = VM.Destroy_Task()
tasks.wait_for_tasks(SI, [TASK])
print("Done.")


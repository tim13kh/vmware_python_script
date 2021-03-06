#!/usr/bin/env python
"""
Written by Reubenur Rahman
Github: https://github.com/rreubenur/

This code is released under the terms of the Apache 2
http://www.apache.org/licenses/LICENSE-2.0.html

Example script to upload a file from host to guest

python /opt/jenkins-files/upload_file_to_vm.py 
-s host.vsphere.com \
-u User \
-p Password \
-o 443 \
-v UUID \
-n VM_NAME \
-r Vm-user \
-w VM-passwd' \
-l path/in/destination/host \
-f local/path \


"""

from __future__ import with_statement
import atexit
import requests
from tools import cli
from tools import tasks
from pyVim import connect
from pyVmomi import vim, vmodl
import re
from pyVim.connect import SmartConnectNoSSL, Disconnect

def get_args():
    """Get command line args from the user.
    """

    parser = cli.build_arg_parser()

    parser.add_argument('-v', '--vm_uuid',
                        required=False,
                        action='store',
                        help='Virtual machine uuid')

    parser.add_argument('-n', '--vm_name',
                        required=False,
                        action='store',
                        help='Virtual machine Name')

    parser.add_argument('-r', '--vm_user',
                        required=False,
                        action='store',
                        help='virtual machine user name')

    parser.add_argument('-w', '--vm_pwd',
                        required=False,
                        action='store',
                        help='virtual machine password')

    parser.add_argument('-l', '--path_inside_vm',
                        required=False,
                        action='store',
                        help='Path inside VM for upload')

    parser.add_argument('-f', '--upload_file',
                        required=False,
                        action='store',
                        help='Path of the file to be uploaded from host')

    args = parser.parse_args()

    cli.prompt_for_password(args)
    return args


def get_obj(content, vimtype, name):
    """
    This function takes three parameters (ie) content , type of the
    object and the name &searches for the object in the content and
    returns it.In this program,we are using it to get VM by its name.
    """
    obj = None
    container = content.viewManager.CreateContainerView(
        content.rootFolder, vimtype, True)
    for c in container.view:
        if c.name == name:
            obj = c
            break
    return obj


def main():
    """
    Simple command-line program for Uploading a file from host to guest
    """

    args = get_args()
    vm_path = args.path_inside_vm
    try:
        service_instance = connect.SmartConnectNoSSL(host=args.host,
                                                    user=args.user,
                                                    pwd=args.password,
                                                    port=int(args.port))

        atexit.register(connect.Disconnect, service_instance)
        content = service_instance.RetrieveContent()

        if args.vm_uuid:
            vm = content.searchIndex.FindByUuid(None, args.vm_uuid, True)
        elif args.vm_name:
            vm = get_obj(content, [vim.VirtualMachine], args.vm_name)

        if vm is None:
            raise SystemExit("VM not found,verify the UUID or the \
                name of the VM provided")

        creds = vim.vm.guest.NamePasswordAuthentication(
            username=args.vm_user, password=args.vm_pwd)
        with open(args.upload_file, 'rb') as myfile:
            args = myfile.read()

        try:
            file_attribute = vim.vm.guest.FileManager.FileAttributes()
            url = content.guestOperationsManager.fileManager. \
                InitiateFileTransferToGuest(vm, creds, vm_path,
                                            file_attribute,
                                            len(args), True)
            # When : host argument becomes https://*:443/guestFile?
            # Ref: https://github.com/vmware/pyvmomi/blob/master/docs/ \
            #            vim/vm/guest/FileManager.rst
            # Script fails in that case, saying URL has an invalid label.
            # By having hostname in place will take take care of this.
            #url = re.sub(r"^https://\*:", "https://"+str(args.host)+":", url)
            resp = requests.put(url, data=args, verify=False)
            if not resp.status_code == 200:
                print "Error while uploading file"
            else:
                print "Successfully uploaded file"
        except IOError, e:
            print e
    except vmodl.MethodFault as error:
        print "Caught vmodl fault : " + error.msg
        return exit(-1)

    return 0

# Start program
if __name__ == "__main__":
    main()

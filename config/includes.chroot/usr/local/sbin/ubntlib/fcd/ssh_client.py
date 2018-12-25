#!/usr/bin/python3
import paramiko
from scp import SCPClient


class SSHClient(object):
    def __init__(self, host=None, port=22, username=None, password=None, pkey_path=None, timeout=10):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        if password is not None:
            self.client.connect(hostname=host, port=port, username=username, password=password, timeout=timeout)
        elif pkey_path is not None:
            self.pkey = paramiko.RSAKey.from_private_key_file(pkey_path)
            self.client.connect(hostname=host, username=username, port=port, pkey=self.pkey, timeout=timeout)

    def execmd(self, cmd):
        return self._exec_command(cmd=cmd)

    def execmd_getmsg(self, cmd, stderr=False, all=False):
        return self._exec_command(cmd=cmd, get_stdout=True, get_stderr=stderr, get_all=all)

    def _exec_command(self, cmd, get_stdout=False, get_stderr=False, get_all=False):
        try:
            stdin, stdout, stderror = self.client.exec_command(cmd)
        except Exception as e:
            print(str(e))
            return False
        if get_stderr is True:
            return stdout.read(), stderror.read()
        elif get_all is True:
            return stdin, stdout.read(), stderror.read()
        elif get_stdout is True:
            return stdout.read()
        else:
            return True

    def put_file(self, local, remote):
        scp_obj = SCPClient(self.client.get_transport())
        scp_obj.put(files=local, remote_path=remote)

    def get_file(self, remote, local):
        scp_obj = SCPClient(self.client.get_transport())
        scp_obj.get(local_path=local, remote_path=remote)

    def close(self):
        self.client.close()


#!/usr/bin/python3
import paramiko


class SSHClient():
    def __init__(self, host=None, port=22, username=None, password=None, pkey_path=None, timeout=10):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        if password is not None:
            self.client.connect(hostname=host, port=port, username=username, password=password, timeout=timeout)
        elif pkey_path is not None:
            self.pkey = paramiko.RSAKey.from_private_key_file(pkey_path)
            self.client.connect(hostname=host, username=username, port=port, pkey=self.pkey, timeout=timeout)

    def run_cmd_get_out(self, cmd, need_stderr=False):
        _, _out, _error = self.client.exec_command(cmd)
        if need_stderr is True:
            return _out.read(), _error.read()
        else:
            return _out.read()

    def close(self):
        self.client.close()


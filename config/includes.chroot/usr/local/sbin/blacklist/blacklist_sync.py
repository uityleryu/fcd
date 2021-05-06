import sys
import os
import requests
import json
import shutil
import hashlib
import datetime
import tarfile
import traceback
import logging

class blacklist():

    def __init__(self):
        self.url_blacklist_json_checksum = "http://factory.dev.svc.ui.com:9998/api/v1/get/blacklist_json_checksum"
        self.url_blacklist_json = "http://factory.dev.svc.ui.com:9998/api/v1/get/blacklist_json"
        self.url_blacklist_json_checksum_backup = "http://factory.dev.svc.ui.com:9999/api/v1/get/blacklist_json_checksum"
        self.url_blacklist_json_backup = "http://factory.dev.svc.ui.com:9999/api/v1/get/blacklist_json"
        self.blacklist_folder_path = '/usr/local/sbin/blacklist'
        self.local_json_path = os.path.join(self.blacklist_folder_path, 'blacklist.json')
        self.remote_json_path = os.path.join(self.blacklist_folder_path, 'cloud-blacklist.json')
        self.local_json_checksum = ''
        self.remote_json_checksum = ''

        logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s][%(levelname)s] [%(threadName)s] %(message)s',
            handlers=[
                logging.FileHandler("/usr/local/sbin/blacklist/blacklist_sync.log"),
                logging.StreamHandler()
            ]
        )
        logging.info('')


    def sync_cloud(self):
        try :
            if not self._checksum():
                logging.info('Syncing Cloud')
                self._download_json()
            else:
                logging.info('No need to Sync Cloud')

        except Exception as e:
            logging.info('Skip Sync, {}'.format(e))
            traceback.print_exc()

    def _checksum(self):
        r = requests.get(self.url_blacklist_json_checksum)
        if not r :
            r = requests.get(self.url_blacklist_json_checksum_backup)

        self.local_json_checksum = self._md5checksum(self.local_json_path)
        self.remote_json_checksum = r.text
        logging.info("checksum_local blacklist.json:{}".format(self.local_json_checksum))
        logging.info("checksum_cloud blacklist.json:{}".format(self.remote_json_checksum))

        if self.local_json_checksum == self.remote_json_checksum: return True
        return False

    def _download_json(self):
        r = requests.get(self.url_blacklist_json)
        if not r :
            r = requests.get(self.url_blacklist_json_backup)

        with open(self.remote_json_path, 'wb') as f:
            json_object = r.json()
            assert ('a620' == json_object['UniFiAP6']['U6-LR']['BOARDID'])
            f.write(r.content)

        logging.info("checksum_cloud blacklist.json:{}".format(self.remote_json_checksum))
        logging.info("checksum_download blacklist.json:{}".format(self._md5checksum(self.remote_json_path)))
        if self.remote_json_checksum == self._md5checksum(self.remote_json_path):
            if os.path.exists(self.local_json_path): shutil.move(self.local_json_path, self.local_json_path + '.backup')
            if os.path.exists(self.remote_json_path): shutil.move(self.remote_json_path, self.local_json_path)
            logging.info('replace {} to {}'.format(self.remote_json_path, self.local_json_path))

    def _md5checksum(self, filePath, url=None):
        m = hashlib.md5()
        if not os.path.exists(filePath): return 'File not exist'
        if url==None:
            with open(filePath, 'rb') as fh:
                m = hashlib.md5()
                while True:
                    data = fh.read(8192)
                    if not data:
                        break
                    m.update(data)
                return m.hexdigest()
        else:
            r = requests.get(url)
            for data in r.iter_content(8192):
                 m.update(data)
            return m.hexdigest()

if __name__ == '__main__':

    blacklist_obj = blacklist()
    blacklist_obj.sync_cloud()




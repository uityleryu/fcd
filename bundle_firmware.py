#!/usr/bin/python

import ConfigParser
import urllib
import os

image_dir = 'config/includes.chroot/srv/tftp/images/'
Config = ConfigParser.SafeConfigParser()
Config.read('bundle_firmware.ini')
for section in Config.sections():
    # parsing
    symlink = Config.get(section, 'symlink_name')
    appendix = Config.get(section, 'appendix')
    url_prefix = Config.get(section, 'url_prefix')

    # get version
    version_url = url_prefix + '/latest_firmware.ubnt_version'
    version_file = section + '.version'
    urllib.urlretrieve(version_url, version_file)
    version = open(version_file, 'r').readline().strip()
    os.remove(version_file)

    # remove old firmware
    for f in [image_dir + symlink, os.path.realpath(image_dir + symlink)]:
        if os.path.exists(f):
            print 'removing', f
            os.remove(f)

    # download new firmware
    fw = version + appendix
    urllib.urlretrieve(url_prefix + '/' + fw, image_dir + fw)
    print 'symlinking', image_dir + symlink , '->', fw
    os.symlink(fw, image_dir + symlink)

    if Config.has_option(section, 'trx_symlink'):
        trx_symlink = Config.get(section, 'trx_symlink')
        trx_name = Config.get(section, 'trx_name')

        # remove old trx
        for f in [image_dir + trx_symlink, os.path.realpath(image_dir + trx_symlink)]:
            if os.path.exists(f):
                print 'removing', f
                os.remove(f)

        # download new trx
        trx = version + '_' + trx_name
        urllib.urlretrieve(url_prefix + '/' + trx_name, image_dir + trx)
        print 'symlinking', image_dir + trx_symlink , '->', trx
        os.symlink(trx, image_dir + trx_symlink)

        print trx_symlink, trx_name

    print section, version 





* How to build ISO file basing on the FCD-base.iso
FCD-base.iso: 
    it is just a FCD host ISO file which is a debian stretch version.
    It includes the following packages.
    # GTK3 packages
    apt-get -y install gtk+3.0
    apt-get -y install libgtk-3-dev
    apt-get -y install gir1.2-gtk-3.0
    
    # Network tools
    apt-get -y install net-tools
    apt-get -y install atftp

    # packages install checking
    apt-get -y install pkg-config
    
    # python2 required packages
    apt-get -y install python-gi
    apt-get -y install python-gi-cairo
    apt-get -y install python-serial
    apt-get -y install python-pexpect
    
    # python3 required packages
    apt-get -y install python3-pip
    apt-get -y install python3-gi
    apt-get -y install python3-gi-cairo
    apt-get -y install python3-serial
    apt-get -y install python3-pexpect
    pip3 install setuptools
    pip3 install wheel
    pip3 install lazy
    
    # serial console packages
    apt-get -y install picocom
    apt-get -y install minicom
    apt-get -y install lrzsz
    
    # text editor
    apt-get -y install vim
    apt-get -y install gedit
    
    # security key packages
    apt-get -y install dropbear
    
    # mkdir /media/FCDUSB
    # usbdv="/dev/sdb1 /media/FCDUSB auto rw,user,noauto 0 0"
    # echo $usbdv >> /etc/fstab
    
    apt-get -y install imagemagick

Generating FCD ISO file procedure
Step_1: copy the FCD-base.iso to /export
Step_2: go to the fcd folder where you cloned
Step_3: typing "make -f fcdmaker32.mk create_live_cd"
Step_4: you will find the new FCD in the /export

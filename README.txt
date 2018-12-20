
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

========================================================================================================

* Clone a FCD source code
FCD repository: https://drive.google.com/open?id=14IOj5Z_bl-u18Skrly_BwEUNeRxT-jnQ

    git clone git@10.2.128.30:Ubiquiti-BSP/fcd.git


========================================================================================================

* Generating FCD ISO file procedure based on develop branch
Description:
    The following instructions is used to create a whole new FCD ISO file
    It means that it will delete the previous stage folders.


Step_1: create a folder, output, under the folder where the fcdmaker32.mk is
Step_2: make a symbolic to the latest FCD base ISO file to the output

    Google drive: https://drive.google.com/open?id=14IOj5Z_bl-u18Skrly_BwEUNeRxT-jnQ

    example:

        ln -s ~/Downloads/FCD-BASE-20181220.iso FCD-base.iso

Step_3: go to the path where the fcdmaker32.mk is

    command:

        sudo make VER=<version> PRD=<product> -f fcdmaker32.mk <product>

    example:

        sudo make VER=0.9.2-aabbccdd PRD=UDM -f fcdmaker32.mk UDM

Step_4: you will find the new FCD under the output folder

========================================================================================================

* Modify the existed FCD ISO file
Description:
    It will decompress the existed FCD ISO file and you just modify some files under the stage folder
    And then compress back the ISO file.

Step_1: make a symbolic to an existed FCD base ISO file to the output

    example:

        ln -s ~/Downloads/FCD-UDM-0.9.1-d9e5388-3.iso FCD-base.iso

Step_2: decompress the existed FCD ISO file

    command:

        sudo make VER=<version> PRD=<product> -f fcdmaker32.mk new-rootfs

    example:

        sudo make VER=0.9.1-d9e5388-3 PRD=UDM -f fcdmaker32.mk new-rootfs

Step_3: modify the file in /home/djc/fcdsrc/bspfcd3/output/stage/NewSquashfs/

Step_4: pack the modifying file to ISO file

    command:

        sudo make VER=<version> PRD=<product> -f fcdmaker32.mk packiso-<product>

    example:

        sudo make VER=0.9.1-d9e5388-4 PRD=UDM -f fcdmaker32.mk packiso-UDM


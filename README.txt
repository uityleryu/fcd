
========================================================================================================

* Clone a FCD source code
FCD repository: https://drive.google.com/open?id=14IOj5Z_bl-u18Skrly_BwEUNeRxT-jnQ

    git clone git@10.2.128.30:Ubiquiti-BSP/fcd.git


========================================================================================================
!!! IMPORTANT !!!
!!! IMPORTANT !!!
!!! IMPORTANT !!!
* please clone the fcd-image and UPyFCD repository in advance

    make PRD=UDM -f fcdmaker32.mk gitrepo


========================================================================================================

* General use case

most used case:
    To build a whole new FCD ISO

Example:
    sudo make VER=[master] PRD=UDM -f fcdmaker32.mk UDM


developing case:
    To just modify the UPyFCD or fcd-img and update the FCD.

    sudo make PRD=UDM -f fcdmaker32.mk clean
    make PRD=UDM -f fcdmaker32.mk clean-repo
    sudo make VER=[master] PRD=UDM -f fcdmaker32.mk UDM

    fcd-image or UPyFCD update
    sudo make VER=[master] PRD=UDM -f fcdmaker32.mk UDM-upddate

You can see more details in the following explainantion

========================================================================================================

* Alternative use case from Lucian

1. Load FCD-BASE.iso on VM and boot.
2. On Working PC, clone fcd/ftu ...
3. Edit on Working PC
4. rsync -avh include.chroot/usr/local/sbin/. user@192.168.1.19:/usr/local/sbin/
5. Goto step 3


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

========================================================================================================

* How to build the ISO file with "<product-name>-update"
Description:
    There are two merits to use this way to build the ISO file.

    merit-1:
    The purpose of using the "<product-name>-update" is that we could reduce the ISO genrating time.

    merit-2:
    In addition, if you modify some codes to the fcd-image or UPyFCD repositories, you don't have to change the
    hash number in the include/UDM.mk. As well as you needn't to deliver the changed commit to the gitlab.

        UPYFCD_VER=49250ead9440898ef66a569ee4ff042e69b9175e
        FCDIMG_VER=af4719c10ef69a3109dbe2d859bb94c9f5f05abc

    reqirement:
    It must do the full build once at the very beginning.

        command:

        sudo make VER=<version> PRD=<product> -f fcdmaker32.mk <product>

    example:

        sudo make VER=0.9.1-d9e5388-4 PRD=UDM -f fcdmaker32.mk UDM


Step_1:
    command:

        sudo make VER=<version> PRD=<product> -f fcdmaker32.mk <product>-update

    example:

        sudo make VER=0.9.1-d9e5388-3 PRD=UDM -f fcdmaker32.mk UDM-update

import sys,os,requests,json
from requests.adapters import HTTPAdapter
import datetime,tarfile
import argparse
from argparse import RawTextHelpFormatter
import shutil

def uploadlog ( inputpath, stage, bom, mac  ):
    urldict = {
        'AWS-1': 'http://ec2-18-162-120-142.ap-east-1.compute.amazonaws.com:9999/api/v1/uploadlog',
        'G-1': 'http://35.220.228.220:9999/api/v1/uploadlog'
    }
    url = urldict['AWS-1']

    timestampstr = '%Y-%m-%d_%H_%M_%S_%f'
    tpe_tz = datetime.timezone(datetime.timedelta(hours=8))
    start_time = datetime.datetime.now(tpe_tz)
    start_timestr = start_time.strftime(timestampstr)
    uploadpath = os.path.join( os.path.dirname(inputpath), '{}_{}{}'.format(start_timestr, mac, ".tar.gz"))

    # Create Send Parameter
    info = {
            'request_targetpath': inputpath,
            'request_gzpath': uploadpath ,
            'request_type': stage,
            'request_uploadtime': start_timestr,
            'request_bom' : bom,
            'request_mac' : mac
           }

    try:
        # Tar Folder/File to upload
        with tarfile.open(uploadpath, mode="w:gz") as tf:
            if os.path.isdir(inputpath):
                tar_dir = os.path.join(stage, bom, start_timestr +'_' + mac)
                tf.add(inputpath, tar_dir)

            elif os.path.isfile(inputpath):
                tar_dir = os.path.join(stage, bom, start_timestr +'_'+ mac, os.path.basename(inputpath) )
                tf.add(inputpath , tar_dir)

        # Send http Request
        files = {'file': open(uploadpath, 'rb')}
        s = requests.Session()
        s.mount('http://', HTTPAdapter(max_retries=3))
        r= s.post(url, files=files, params=info , timeout=5)

        print("\n[Uploading] Send {} To {}".format( uploadpath , url ) )

        json_res= r.json()
        json_res['uploadpath']=uploadpath
        return json_res

    except requests.exceptions.RequestException as e:
        print (e)
        return e


def TradArg():
    Version = "Logupload_client_v1.0"
    ap = argparse.ArgumentParser( description='[{}]\n eg: --path /media/usbdisk/upload --mac 788a20f039e8 --bom 113-00391 --stage FCD'.format(Version),formatter_class=RawTextHelpFormatter )
    ap.add_argument('-a', '--scan', action='store_true', help="Scan folder for batch upload", default=False,required=False)
    ap.add_argument('-p', '--path',  metavar='\b', help="[Folder/Path] eg, /media/usbdisk/2020-02-25_15", required=True)
    ap.add_argument('-b', '--bom',  metavar='\b', help="[bom] eg, 113-00391 ", required=True)
    ap.add_argument('-m', '--mac',  metavar='\b', help="[mac] eg, 788a20f039e8" , required=True)
    ap.add_argument('-s', '--stage',  metavar='\b', choices=['FCD','BackToArt', 'FTU'], help="[Stage] FCD or BackToArt or FTU" , required=True)

    return ap

if __name__ == '__main__':

    ap = TradArg()
    args = vars(ap.parse_args())
    if len(sys.argv[1:])== 0:
        ap.print_help(sys.stderr)
        sys.exit()

    if not os.path.exists(args["path"]):
        print ('{} is not exist'.format(args["path"]))
        sys.exit()

    if not args["scan"]:
        print ("\n[Input para] inputpath={}, stage={}, bom={} mac={}".format(args["path"], args["stage"], args["bom"], args["mac"]))
        json_res = uploadlog(inputpath=args["path"], stage=args["stage"], bom=args["bom"], mac=args["mac"])
        print ("\n[JSON Result] {}".format( json_res ) )

        if json_res['result'] == 'success' and os.path.exists(json_res['uploadpath'] ):
            uploadfile = json_res['uploadpath']
            uploadfilename = os.path.basename(json_res['uploadpath'])
            backupfolder = os.path.join(os.path.dirname(uploadfile), 'backup')
            if not os.path.exists(backupfolder): os.makedirs(backupfolder)
            shutil.move(uploadfile, os.path.join(backupfolder, uploadfilename))
    else:
        pass




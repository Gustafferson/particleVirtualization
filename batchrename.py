import os
import sys

try:
    pathName = sys.argv[1] #gets second argv in script call , i.e. python3 /home/guswsk/Projects/particleScanning/Arrangement_Binarisation.py /mnt/e/210113142910/
    if os.path.exists(pathName):
        print('%s exists, pulling images' % pathName)
    else:
        print('Path name %s does not exist, exiting...' % (pathName))
except:
    print('no path given in script call, exiting...')
    sys.exit(1)

filelist = [file for file in os.listdir(pathName) if file.endswith('.png')] #generate the file list of png images

for filename in filelist:
    prefix, num = filename[:-4].split('_')
    num = num.zfill(4)
    new_filename = prefix + "_" + num + ".png"
    os.rename(os.path.join(pathName, filename), os.path.join(pathName, new_filename))
import os 
import sys
import glob
import matplotlib
from matplotlib import pyplot as plt
import cv2
import numpy as np
import pandas as pd 
from tqdm import tqdm
import pickle

# Initial directory handling, path to folder should be nominated in the script call
try:
    pathName = sys.argv[1] #gets second argv in script call , i.e. python3 /home/guswsk/Projects/particleScanning/Arrangement_Binarisation.py /mnt/e/210113142910/
    if os.path.exists(pathName):
        print('%s exists, pulling images' % pathName)
        imageFiles = glob.glob(pathName+'*.png')
    else:
        print('Path name %s does not exist, exiting...' % (pathName))
except:
    print('no path given in script call, exiting...')
    sys.exit(1)


BinData={}

#TODO Add detection of number of files and hence angle of image

# START LOOP FOR EACH FILE IN FOLDER
for file in tqdm(os.listdir(pathName)):
     filename = os.fsdecode(file)
     if filename.endswith(".png"):
        img = cv2.imread(os.path.join(pathName,file)) #read the image
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) #convert x,y,3 array to x,y,1
        
        thresh_val, thresh_img = cv2.threshold(gray,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU) #otsu thresholding on the grayscale
        midpoint = int(thresh_img.shape[1] / 2)

        #separate the image into left and right sides
        left, right = np.fliplr(thresh_img[::,0:midpoint]), thresh_img[::,midpoint:-1] #left side has been flipped to allow for same op on each side
        #scan down rows for 255 values, remove all but first 
        right_occurance_of_255  = pd.DataFrame(data=np.vstack(np.where(right==255)).T,columns=["rows","columns"]).drop_duplicates(subset="rows", keep='first')
        left_occurance_of_255   = pd.DataFrame(data=np.vstack(np.where(left==255)).T,columns=["rows","columns"]).drop_duplicates(subset="rows", keep='first')
        #scan down rows for 0 values, remove all but first 
        right_occurance_of_0    = pd.DataFrame(data=np.vstack(np.where(right==0)).T,columns=["rows","columns"]).drop_duplicates(subset="rows", keep='first')
        left_occurance_of_0     = pd.DataFrame(data=np.vstack(np.where(left==0)).T,columns=["rows","columns"]).drop_duplicates(subset="rows", keep='first')

        #use arrays to find the cropping regions for the image
        outer_bound_left, outer_bound_right = (left.shape[1]-max(left_occurance_of_255['columns'])), max(right_occurance_of_255['columns'])+right.shape[1]

        #find the max point at which there is a large change in occurance_of_0, this represents the tip of the particle
        change_right_occurance_of_0, change_left_occurance_of_0 = right_occurance_of_0.diff(), left_occurance_of_0.diff()
        outer_bound_top = max(right_occurance_of_0.loc[change_right_occurance_of_0['columns'].idxmax(axis=0),'rows'],left_occurance_of_0.loc[change_left_occurance_of_0['columns'].idxmax(axis=0),'rows'])
        #find the base point of particle which occurs in the last value (idxmax) of 255
        outer_bound_bottom = min(right_occurance_of_255.loc[right_occurance_of_255['columns'].idxmax(axis=0),'rows'],left_occurance_of_255.loc[left_occurance_of_255['columns'].idxmax(axis=0),'rows'])

        thresh_img = thresh_img[outer_bound_bottom:outer_bound_top:,outer_bound_left:outer_bound_right:] #cropped thresh_img using bounds

        BinData[filename] = [thresh_img.shape,thresh_img]

        # print(os.path.join(directory, filename))
        continue
     else:
        continue

print('Images processed, pickling outcome...')
pickle.dump(BinData,open(os.path.join(pathName, 'data.pkl'),'wb'))
print('Done!')

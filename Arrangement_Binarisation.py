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
from skimage.measure import label, regionprops, marching_cubes_lewiner
from scipy.ndimage import  rotate
from stl import mesh



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
index=0

numStops = len(imageFiles)
angleIncrement = 360/numStops
angle =range(0, 360, int(angleIncrement)) #list of angle coordinates

BinData['angles'] = angle

downsampleFactor = 1 # adding downsampling factor to increase performance

mask = np.zeros([1500,3000],dtype='uint8')
intersection = np.ones([round(1500/downsampleFactor),round(3000/downsampleFactor),round(3000/downsampleFactor)],dtype='uint8')


# START LOOP FOR EACH FILE IN FOLDER
for file in tqdm(os.listdir(pathName)):
     filename = os.fsdecode(file)
     if filename.endswith(".png"):

        standardised = mask.copy()

        img = cv2.imread(os.path.join(pathName,file),0).astype('uint8')#read the image, 0 for grayscale
        
        thresh_val, img = cv2.threshold(img,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU) #otsu thresholding on the grayscale
        midpoint = int(img.shape[1] / 2)

        #separate the image into left and right sides
        left, right = np.fliplr(img[::,0:midpoint]), img[::,midpoint:-1] #left side has been flipped to allow for same op on each side
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

        thresh_img = img[outer_bound_bottom:outer_bound_top:,outer_bound_left:outer_bound_right:] #cropped thresh_img using bounds
        thresh_img = np.invert(thresh_img).astype('uint8')

        #Find the centriod coordinates of the binary particle area
        props = regionprops(thresh_img)
        y,x = props[0]['centroid']

        #Use y,x coordinates to offset thresh_img inside a 3000x3000 frame centre_y = 1500-(y-thresh_img.shape[0]/2)
        frame_diff_y = round((mask.shape[0]-thresh_img.shape[0])/2) # difference in y of top left corner of mask and thresh_img
        frame_diff_x = round((mask.shape[1]-thresh_img.shape[1])/2) # difference in x of top left corner of mask and thresh_img
        
        off_y = round(-y+thresh_img.shape[0]/2) # y offset of centroid from centre of thresh_img
        off_x = round(-x+thresh_img.shape[1]/2) # x offset of centroid from centre of thresh_img

        frame_diff_y+=off_y # actual difference in top left corner coordinate
        frame_diff_x+=off_x

        
        standardised[frame_diff_y:frame_diff_y+thresh_img.shape[0], frame_diff_x:frame_diff_x+thresh_img.shape[1]] = thresh_img/255 # adding thresh_img to centre of mask.copy(), dividing values to give 0 and 1
        standardised = standardised.astype('uint8') # ensuring array is a uint8 to save space

        
        standardised = standardised[0::downsampleFactor,0::downsampleFactor]
       
        standardised = np.repeat(standardised[:, :, np.newaxis], max(standardised.shape[0],standardised.shape[1]), axis=2).astype('uint8') # extruding the array through the max array shape to create a polyhedron
        standardised = rotate(standardised, angle[index], axes=(1,2),output='uint8', reshape=False, order=0, mode='constant', cval=0.0, prefilter=False) # rotating the array by 'slice' (y-axis)

        #Add matrix multiplication to give final array
        intersection = intersection*standardised # multiplies the constant np.ones array by the current rotated polyhedron 1*1 -> 1; 1*0 -> 0 etc.


        # BinData[int(angle[index])] = polyhedron # Adding dict entry where key is cumulative angle of rotation
        index += 1
        # print(os.path.join(directory, filename))
        continue
     else:
        continue

print('Images processed, volume reconstructed, meshing with marching cubes...')
verts, faces, normals, values = marching_cubes(intersection,spacing=(1.0, 1.0, 1.0),gradient_direction='descent',step_size=1)

particleMesh = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
for i, f in enumerate(faces):
    for j in range(3):
        particleMesh.vectors[i][j] = verts[f[j],:]

particleMesh.save(os.path.join(pathName, 'particleMesh.stl'))


pickle.dump(intersection,open(os.path.join(pathName, 'data.pkl'),'wb'))
print('Done!')

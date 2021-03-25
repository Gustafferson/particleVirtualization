import os 
import sys
import cv2
import numpy as np
import pandas as pd 
from tqdm import tqdm
from skimage.measure import label, regionprops, marching_cubes_lewiner
from scipy.ndimage import  rotate
from stl import mesh
import math

def binarise(image):
    thresh_val, thresh_img = cv2.threshold(cv2.imread(image,0).astype('uint8'),0,255,cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU) #otsu thresholding on the grayscale
    return thresh_img

def crop_to_roi(image_arr):
    #separate the image into left and right sides
    midpoint = int(image.shape[1] / 2)
    left, right = np.fliplr(image[::,0:midpoint]), image[::,midpoint:-1] #left side has been flipped to allow for same op on each side

    #scan down rows for 255 and 0 values, remove all but first with drop_duplicates
    right_bins  = [pd.DataFrame(data=np.vstack(np.where(right==255)).T,columns=["rows","columns"]).drop_duplicates(subset="rows", keep='first'),pd.DataFrame(data=np.vstack(np.where(right==0)).T,columns=["rows","columns"]).drop_duplicates(subset="rows", keep='first')]
    left_bins   = [pd.DataFrame(data=np.vstack(np.where(left==255)).T,columns=["rows","columns"]).drop_duplicates(subset="rows", keep='first'),pd.DataFrame(data=np.vstack(np.where(left==0)).T,columns=["rows","columns"]).drop_duplicates(subset="rows", keep='first')]

    #use arrays to find the cropping regions for the image
    outer_bound_left, outer_bound_right = (left.shape[1]-max(left_bins[1]['columns'])), max(right_bins[1]['columns'])+right.shape[1]

    #find the max point at which there is a large change in occurance_of_0, this represents the tip of the particle       
    change_right_occurance_of_0, change_left_occurance_of_0 = right_bins[1].diff(), left_bins[1].diff()
    outer_bound_top = max(right_bins[1].loc[change_right_occurance_of_0['columns'].idxmax(axis=0),'rows'],left_bins[1].loc[change_left_occurance_of_0['columns'].idxmax(axis=0),'rows'])

    #find the base point of particle which occurs in the last value (idxmax) of 255
    outer_bound_bottom = min(right_bins[0].loc[right_bins[0]['columns'].idxmax(axis=0),'rows'],left_bins[0].loc[left_bins[0]['columns'].idxmax(axis=0),'rows'])

    cropped = image[outer_bound_bottom:outer_bound_top:,outer_bound_left:outer_bound_right:] #cropped thresh_img using bounds

    return cropped.astype('uint8'), cropped.shape

def centre_by_centroid(shape_list, img_list):
    frame_dims = [max([dim[0] for dim in shape_list]),max([dim[1] for dim in shape_list])]
    
    mask = np.zeros(frame_dims,dtype='uint8')

    centred_list = []

    for img in img_list:
        props = regionprops(img)
        y,x = props[0]['centroid']

        #Use y,x coordinates to offset img inside a frame at its centre
        frame_diff_y = math.ceil((mask.shape[0]-img.shape[0])/2) # difference in y of top left corner of mask and thresh_img
        frame_diff_x = math.ceil((mask.shape[1]-img.shape[1])/2) # difference in x of top left corner of mask and thresh_img
        
        off_y = math.ceil(-y+img.shape[0]/2) # y offset of centroid from centre of thresh_img
        off_x = math.ceil(-x+img.shape[1]/2) # x offset of centroid from centre of thresh_img

        frame_diff_y+=off_y # actual difference in top left corner coordinate
        frame_diff_x+=off_x

        centred[frame_diff_y:frame_diff_y+img.shape[0], frame_diff_x:frame_diff_x+img.shape[1]] = img/255 # adding thresh_img to centre of mask.copy(), dividing values to give 0 and 1
        centred = centred.astype('uint8') # ensuring array is a uint8 to save space

        centred_list.append(centred)

    return centred_list

def find_centre_of_rotation(imageA, imageB):
    """
    This function finds the centre of rotation of a particle by comparing two opposite binary images and finding the same common point.
    With this point, the average x coordinate can be established, this is the centre of rotation.

    Each image can then be centred around the centre of rotation through a transformation in polar coordinate space.

    Images are required to be cropped to ROI, best way is using image sequence in imageJ, this could be integrated into a python gui call.
    
    """
    imageA = imageA.astype('uint8')
    imageB = imageB.astype('uint8')

    loc_maxA_x = max(np.argmax(imageA, axis=0))
    loc_maxB_x = max(np.argmax(imageB, axis=0))

    cor = np.mean([loc_maxA_x,loc_maxB_x])

    return cor

def adjust_to_cor(imgDirectory, centre_of_rotation, cor_ref_img)
    """ 
    This function uses the trailing organisation number in the filename (XXXXXXX_01.img) 
    to align all images with the centre of rotation.
    centre_of_rotation: a single int representing an x coordinate.
    cor_ref_img: the image number associated with the centre_of_rotation, passed as a string
    """
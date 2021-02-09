import os 
import sys
import cv2
import numpy as np
import pandas as pd 
from tqdm import tqdm
from skimage.measure import label, regionprops, marching_cubes_lewiner
from scipy.ndimage import  rotate
from stl import mesh

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

def centre_in_frame(shape_list, img_list):
    frame_dims = [max([dim[0] for dim in shape_list]),max([dim[1] for dim in shape_list])]
    
    mask = np.zeros(frame_dims,dtype='uint8')

    for img in img_list:
        props = regionprops(img)
        y,x = props[0]['centroid']

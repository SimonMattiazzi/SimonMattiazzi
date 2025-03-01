# -*- coding: utf-8 -*-
"""
Created on Mon Jul  1 17:40:35 2024

This module contains all functions needed for
mapping the desired angles input to SLM inputs.
This module is used by other python files.



@author: Simon
"""
import numpy as np
import matplotlib.pyplot as plt
from skimage.transform import resize
from skimage.filters import gaussian
import csv
import time
import os

# final dimensions:
dimX_final, dimY_final = 1920, 1200 # final output

#--------------DO NOT CHANGE ANYTHING IN THIS SECTION!!!----------------------#

def transform_input(input_array, transform_mode="2pi"):
    """
    Input is in angles [0, pi] or [0, 2pi], measured from cartesian point (1,0) in counter-clockwise direction.
    Transform to graylevel values [0, 255].
    polarizations: H = 0 or 255, V = 127
    
    """
    if transform_mode == "2pi":
        factor = 255 / np.pi
        shift = 127*0
        
    if transform_mode == "4pi":
        factor = 255 / (2* np.pi)
        shift = 127*0
        
    return factor * (input_array) + shift


def transform_input_inv(input_array, transform_mode="2pi"):
    """
    Input is in graylevel values [0, 255].
    Transform to angles [0, pi] or [0,2 pi], measured from cartesian point (1,0) in counter-clockwise direction
    polarizations: H = 0 or 255, V = 127
    
    """
    if transform_mode == "2pi":
        factor = 255 / np.pi
        shift = 127*0
        
    if transform_mode == "4pi":
        factor = 255 / (2* np.pi)
        shift = 127*0
        
    return (input_array - shift) / factor


def nparray_to_csv(array, filename):
    """
    Input the desired array. Writes and saves a CSV file that can be used as a SLM input.
    (coordinate axes are added, number format is taken care of etc.)
    Overwrite prevention.
    
    array: input array
    filename: desired output filename
    """
    
    # initiate array: 
    array = resize(array, (dimY_final, dimX_final), preserve_range=True, order=1)
    csv_arr = list(np.zeros((dimY_final+1, dimX_final+1))) # Y, X!
    
    # first line:
    csv_arr[0] = list(np.arange(-1, dimX_final))
    csv_arr[0][0] = "Y/X"
    
    # all other lines:
    for y in range(dimY_final):
        line = list(np.concatenate(([y], array[y])))
        line = [int(item) for item in line]
        csv_arr[y+1] = line
    
    # writing to csv file:
    if not os.path.exists(filename):
        with open(filename, 'w', newline="") as csvfile:
            csvwriter = csv.writer(csvfile,delimiter=',')
            csvwriter.writerows(csv_arr)
    else:
        i = 1
        base, ext = os.path.splitext(filename)
        while os.path.exists(filename):
            filename = base + "_" + str(i) + ext
            print("Filename already exists, saving as ", filename)
            i+=1    


def mapping(input_array, map_dict_3d, avg_res=4):
    
    """
    Transforms an input array of graylevel values (AOLP) into phase data (0-1023) 
    using a provided calibration map. The transformation can be performed using an 
    average map or a pixel-by-pixel map.

    Parameters:
    -----------
    input_array : numpy.ndarray (the GUI converts a CSV as well)
        The array of graylevel values to be converted. If the dimensions of the 
        input array do not match the expected dimensions of the calibration map, 
        it will be resized accordingly.
    
    map_dict_3d : dict or 2D array of dicts
        The calibration map used for the conversion. If a single dictionary is provided, 
        the function operates in "average mode", where the same calibration map 
        is applied to all pixels. If a list of dictionaries (3D map) is provided, 
        the function operates in "pixel-by-pixel mode", where each pixel has its 
        own calibration map.
    
    avg_res : int, optional
        A parameter for downscaling the dimensions of the input array in both 
        directions to speed up calculations when using the average map. The default 
        value is 4. For the pixel-by-pixel mode, the resolution is given with
        the map itself.

    Returns:
    --------
    numpy.ndarray
        The transformed array with phase data (0-1023).
        

    Notes:
    -------------
    - The input array is resized and each pixel's graylevel is mapped to
      phase data using the closest calibration values in `map_dict_3d`.
      If the exact graylevel is not found, the function interpolates 
      between the nearest available values. Special cases where there are 
      no upper or lower neighbours.
      
    - The resizing operations may introduce slight inaccuracies. Be careful
      about interpolation in resizing, as black + white must not be grey!
     
    """
    
    if type(map_dict_3d) is dict: #if we use the average map
        
        # resizing the input:
        dimX_avg, dimY_avg = int(dimX_final/avg_res), int(dimY_final/avg_res)
        if len(input_array) != dimY_avg and len(input_array[0]) != dimX_avg:
            input_array = resize(input_array,(dimY_avg, dimX_avg), preserve_range=True, order=1)
            
        out = np.zeros((dimY_avg, dimX_avg))
        
        print("Calculating (avg mode) ...")
        for i, row in enumerate(input_array):
            for j, pixel in enumerate(row):
                graylevel = input_array[i][j]
               
                # the key is not necessarily in the dictionary, so we look for the closest ones and interpolate:               
                upper_keys = [key for key in map_dict_3d.keys() if key > graylevel]
                lower_keys = [key for key in map_dict_3d.keys() if key < graylevel]
                
                if len(upper_keys) != 0 and len(lower_keys) != 0: 
                    closest_key_up = min(upper_keys, key = lambda key: abs(key-graylevel))
                    closest_key_down = min(lower_keys, key = lambda key: abs(key-graylevel))
                    
                    closest_value_up = map_dict_3d[closest_key_up]
                    closest_value_down = map_dict_3d[closest_key_down]
                    
                    d_up = closest_key_up - graylevel
                    d_down = graylevel - closest_key_down
                    
                    interpolated_value = int(d_up/(d_up+d_down) * closest_value_down + d_down/(d_up+d_down) * closest_value_up)
                    out[i][j] = interpolated_value #map_dict_3d[interpolated_key]
                else:
                    closest_key = min(map_dict_3d.keys(), key = lambda key: abs(key-graylevel))
                    out[i][j] = map_dict_3d[closest_key]
                    #print(i, j, graylevel, "empty array")       
                
        return resize(out, (dimY_final, dimX_final), preserve_range=True, order=1)
    
    
    else: # if pixel-by-pixel map
        
        # resizing the input:
        if len(input_array) != len(map_dict_3d) and len(input_array[0]) != len(map_dict_3d[0]):
            input_array = resize(input_array,(len(map_dict_3d), len(map_dict_3d[0])), preserve_range=True, order=1)
            
        out = np.zeros((len(map_dict_3d), len(map_dict_3d[0])))
            
        print("Calculating (pixel-by-pixel mode) ...") 
        for i, row in enumerate(input_array):
            for j, pixel in enumerate(row):
                graylevel = input_array[i][j]
                
                # the key is not necessarily in the dictionary, so we look for the closest one:               
                upper_keys = [key for key in map_dict_3d[i][j].keys() if key > graylevel]
                lower_keys = [key for key in map_dict_3d[i][j].keys() if key < graylevel]
                                
                if len(upper_keys) != 0 and len(lower_keys) != 0: 
                    closest_key_up = min(upper_keys, key = lambda key: abs(key-graylevel))
                    closest_key_down = min(lower_keys, key = lambda key: abs(key-graylevel))
                    
                    closest_value_up = map_dict_3d[i][j][closest_key_up]
                    closest_value_down = map_dict_3d[i][j][closest_key_down]
                    
                    d_up = closest_key_up - graylevel
                    d_down = graylevel - closest_key_down
                    
                    interpolated_value = int(d_up/(d_up+d_down) * closest_value_down + d_down/(d_up+d_down) * closest_value_up)
                    out[i][j] = interpolated_value#map_dict_3d[i][j][interpolated_key]
                                   
                else:
                    closest_key = min(map_dict_3d[i][j].keys(), key = lambda key: abs(key-graylevel))
                    out[i][j] = map_dict_3d[i][j][closest_key]
                    #print(i, j, graylevel, len(lower_keys), len(upper_keys), "empty array")       
                    
        return resize(out, (dimY_final, dimX_final), preserve_range=True, order=1)
    
    

#-----------------obsolete functions (moved to new file)-----------------------#

#def calculate_dictionary():
#    """
#    Calculate the dictionary by comparing all the images in all the pixels
#    with all the 1024 phase values. 
#    You need to have all the mono-polarization images already taken.
#    The end result is a 2D array, where each element contains a dictionary
#    which maps between graylevels on the camera and SLM inputs.
#
#    """
#    
#    # initialize empty arrays of dictionaries:
#    array_dict = [[{} for _ in range(dimX)] for _ in range(dimY)]
#    array_dict_inv = [[{} for _ in range(dimX)] for _ in range(dimY)]
#    
#    # vsako N-to sliko posebej:
#    for phase in range(300, 1024, 10):
#        print(phase)
#        phasestr = f"{phase:04d}"
#        raw = plt.imread(f"D:\\UsersData\\Simon\\calibration2\\{phasestr}.png", format="png")
#            
##        if phase < 651:
##            Imin, Imax, Jmin, Jmax = Imin1, Imax1, Jmin1, Jmax1 
##        elif 650 < phase < 951:
##            Imin, Imax, Jmin, Jmax = Imin2, Imax2, Jmin2, Jmax2 
##        elif phase > 950:
##            Imin, Imax, Jmin, Jmax = Imin3, Imax3, Jmin3, Jmax3    
#            
#        # calibration 2:
#        Imin, Imax, Jmin, Jmax = Imin4, Imax4, Jmin4, Jmax4
#    
#        cropped = raw[Imin:Imax, Jmin:Jmax]
#        
#        #cropped = cropped * np.pi
#        #cropped = np.exp(cropped*1j)
#        #filteredR = gaussian(cropped.real, sigma=20, preserve_range=True)
#        #filteredI = gaussian(cropped.imag, sigma=20, preserve_range=True)
#        #filtered = (np.arctan2(filteredI, filteredR) + np.pi) / 2 /np.pi
#        
#        filtered = gaussian(cropped, sigma=20, preserve_range=True)
#
#        resized = resize(filtered,(dimY, dimX), preserve_range=True, order=1) # order 0!!!
#    
#        for i, row in enumerate(array_dict):
#            for j, pixel in enumerate(row):
#                graylevel = int(255 * resized[i][j][0])
#                array_dict[i][j][graylevel] = phase 
#                array_dict_inv[i][j][phase] = graylevel
#    
#    plt.plot(array_dict[200][210].keys(), array_dict[200][210].values())
#    plt.plot(array_dict[210][200].keys(), array_dict[210][200].values())
#    plt.plot(array_dict[210][210].keys(), array_dict[210][210].values())
#    plt.plot(array_dict[200][200].keys(), array_dict[200][200].values())
#    plt.show()
#    
#    np.save(f"map_pix_res{resolution}_filt_20.npy", array_dict)
#    np.save(f"map_pix_inv_res{resolution}_filt_20.npy", array_dict_inv)
#    
#    
#def calculate_dictionary_average():
#    """
#    Calculate the dictionary by comparing all the images
#    with all the 1024 phase values. Just looking at average value.
#    You need to have all the mono-polarization images already taken.
#    The end output is a simple dictionary between graylevels and SLM
#    input values.
#    """
#    
#    # initialize empty arrays of dictionaries:
#    array_dict = {} 
#    array_dict_inv = {}
#    
#    # vsako sliko posebej:
#    for phase in range(300, 1024, 10):
#        print(phase)
#        phasestr = f"{phase:04d}"
#        raw = plt.imread(f"D:\\UsersData\\Simon\\calibration2\\{phasestr}.png", format="png")
#            
##        if phase < 651:
##            Imin, Imax, Jmin, Jmax = Imin1, Imax1, Jmin1, Jmax1 
##        elif 650 < phase < 951:
##            Imin, Imax, Jmin, Jmax = Imin2, Imax2, Jmin2, Jmax2 
##        elif phase > 950:
##            Imin, Imax, Jmin, Jmax = Imin3, Imax3, Jmin3, Jmax3    
#        
#        # calibration 2:
#        Imin, Imax, Jmin, Jmax = Imin4, Imax4, Jmin4, Jmax4
#            
#        cropped = raw[Imin:Imax, Jmin:Jmax]
#        #filtered = gaussian(cropped, sigma=20, preserve_range=True)
#        resized = resize(cropped,(dimY, dimX), preserve_range=True, order=1)
#    
#        graylevel = int(255 * np.mean(resized))
#        array_dict[graylevel] = phase 
#        array_dict_inv[phase] = graylevel
#        
#    plt.plot(array_dict.keys(), array_dict.values())
#    plt.show()
#    
#    
#    np.save(f"map_avg_res{resolution}.npy", array_dict)
#    np.save(f"map_avg_inv_res{resolution}.npy", array_dict_inv)








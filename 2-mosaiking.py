#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun  9 15:25:24 2022

@author: queunet
"""

import os
from pathlib import Path
import re
import datetime
import numpy as np

#====== Inputs for mosaiking SENTINEL2

# Specify the tiles, the path were the images mosaiked will be

listOfS2Tiles = ['44QKE', '44QKF']
pathMain = Path('/media/queunet/WD/')
pathToOutputDir = pathMain / 'dir_MOS_S2_r_2020_dir_3_QKE_dir_4_QKF'
pathToInputListFile = pathToOutputDir / 'list_input_tif_images.txt'
iTile = 3 
listOfTifs = []

for s2Tile in listOfS2Tiles:
    # name of the directory where it searchs the both tiles:
    pathToDirWithTifs = pathMain / f'dir_{iTile}_S2_r_2019_{s2Tile}' / f'T{s2Tile}'
    # possibility to choose NDWI:
    localListOfTifs = list(pathToDirWithTifs.glob('*NDWI.tif'))
    listOfTifs = listOfTifs + localListOfTifs
    iTile+=1
    
listOfDates = []

#===== Extract time series


for path in listOfTifs:
    reRes = re.search('^SENTINEL.*_([0-9]{8})-',path.name)
    if reRes is None:
        listOfDates.append(None)
    else:
        dateStr = reRes.group(1)
        dateAsDatetime = datetime.datetime.strptime(dateStr, "%Y%m%d").date()
        listOfDates.append(dateAsDatetime)

for iEntry in range(len(listOfDates)-1,-1,-1):
    if listOfDates[iEntry] is None:
        del listOfDates[iEntry]
        del listOfTifs[iEntry]
        
listOfDates = np.array(listOfDates)
listOfTifs = np.array(listOfTifs)
listOfUniqueDates = np.unique(listOfDates)

#====== Compute the mosaiking

for dateAsDatetime in listOfUniqueDates:
    print(dateAsDatetime)
    indForThisDate = np.where(listOfDates==dateAsDatetime,True,False)
    nImagesForThisDate = np.count_nonzero(indForThisDate)
    if nImagesForThisDate != 2 and 1:
        continue
    listOfTifsToMos = listOfTifs[indForThisDate]
    with open(pathToInputListFile, 'w+') as file:
        for path in listOfTifsToMos:
            file.write(path.absolute().as_posix() + '\n')
            # Name of the output file in vrt
    cmd = "gdalbuildvrt -input_file_list {} {}/MOS_{}_NDWI.vrt".format(pathToInputListFile.absolute().as_posix(), pathToOutputDir.absolute().as_posix(),dateAsDatetime.strftime('%Y%m%d'))
    os.system(cmd)

# Then to translate in tif from vrt write directly in the terminal:
#     for file in *.vrt; do gdal_translate $file ${file%.*}.tif; done
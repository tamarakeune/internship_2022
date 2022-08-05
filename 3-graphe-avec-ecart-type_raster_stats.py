#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 28 09:56:26 2022

@author: queunet
"""

#============== Imports
import os

os.environ['PROJ_LIB'] = "/home/queunet/anaconda3/share/proj"
os.environ['GDAL_DATA'] = "/home/queunet/anaconda3/share/gdal"

import sys
from osgeo import gdal
from glob import glob
import math
import numpy as np
import pandas as pd
import datetime as dt
from osgeo import gdal
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import csv
import pytz
import geopandas as gpd

import shapefile
import re
from pyproj import Proj, transform

from rasterstats import zonal_stats



#====== Inputs NDVI VENUS
shp = "/media/queunet/WD/polygones/R2020.shp"
dir_data = "/media/queunet/WD/dir_3_venus_r_2020/KUDALIAR"
df = pd.DataFrame()



#===== Extract time series
for raster in glob(os.path.join(dir_data, "VENUS*NDVI.tif")):
    # Find date in file name
    date_string = os.path.basename(raster).split("_")[1][:8]
    date = dt.datetime.strptime(date_string, "%Y%m%d").date()
    
    print(date)
    nodata = 0
    
    # Extract stats
    # categorical = True makes pixels count as values and raster values as keys
    my_stats = zonal_stats(shp, raster, stats = ['mean', "std"],
                               categorical = False, nodata = nodata, geojson_out = True, all_touched = True)
    
    for elt in my_stats:
        mu, std = elt["properties"]["mean"], elt["properties"]["std"]
        if mu is not None:
            df = df.append({
                    "date": date,
                    "id_unique":elt["properties"]["id_unique"],
                    "type":elt["properties"]["id"],
                    "ndvi": mu,
                    "ecart-type-min": mu - std/2,
                    "ecart-type-max": mu + std/2,
                }, ignore_index = True)
    

df = df.sort_values(["id_unique", "date"]).reset_index(drop=True)
df.dropna(inplace = True)

#====== Inputs NDVI SENTINEL2
dir_data_sent = "/media/queunet/WD/dir_MOS_S2_r_2020_dir_3_QKE_dir_4_QKF"
df_sent = pd.DataFrame()
shp = "/media/queunet/WD/polygones/R2020.shp"



#===== Extract time series
for raster in glob(os.path.join(dir_data_sent, "MOS*NDVI.tif")):
    # Find date in file name
    date_string = os.path.basename(raster).split("_")[1][:8]
    date = dt.datetime.strptime(date_string, "%Y%m%d").date()
    
    print(date)
    
    nodata = 0
    # Extract stats
    # categorical = True makes pixels count as values and raster values as keys
    my_stats = zonal_stats(shp, raster, stats = ['mean', "std"],
                               categorical = False, nodata = nodata, geojson_out = True, all_touched = True)
    
    for elt in my_stats:
        mu, std = elt["properties"]["mean"], elt["properties"]["std"]
        if mu is not None:
            df_sent = df_sent.append({
                    "date": date,
                    "id_unique":elt["properties"]["id_unique"],
                    "type":elt["properties"]["id"],
                    "ndvi": mu,
                    "ecart-type-min": mu - std/2,
                    "ecart-type-max": mu + std/2,
                }, ignore_index = True)
    

df_sent = df_sent.sort_values(["id_unique", "date"]).reset_index(drop=True)
df_sent.dropna(inplace = True)



for c in ["type", "id_unique"]:
    df[c] = df[c].astype("int32")
    df_sent[c] = df_sent[c].astype("int32")


# Select lines
df_tmp = pd.DataFrame.copy(df)
df_tmp.index = pd.MultiIndex.from_arrays([df_tmp.type, df_tmp.id_unique], names = ["type", "id_unique"])
df_tmp

df_tmp = pd.DataFrame.copy(df)
df_tmp.index = df_tmp.type

df.query("type==1")

#%% Graphe
df_tmp = pd.DataFrame.copy(df)
df_tmp.index = pd.MultiIndex.from_arrays([df_tmp.type, df_tmp.id_unique], names = ["type", "id_unique"])

df_sent_tmp= pd.DataFrame.copy(df_sent)
df_sent_tmp.index = pd.MultiIndex.from_arrays([df_sent_tmp.type, df_sent_tmp.id_unique], names = ["type", "id_unique"])

# Dictionnaire pour les labels
dict_labels = {
    1: "RICE",
    2: "VEGETABLES",
    3: "MAIZE",
    4: "ORCHARDS",
    5: "FOREST",
    6: "BAR SOIL",
    7: "URBAN",
    8: "WATER"
    }

plt.close()



for classe in df.type.unique():    
    list_polygones = df_tmp.loc[classe, "id_unique"].unique()
    lines = []
    
    plt.figure()
    
    dummy, = plt.plot(df_tmp.loc[(classe, list_polygones[0]), "date"].values[0],
                      df_tmp.loc[(classe, list_polygones[0]), "ndvi"].values[0], marker='None',
           linestyle='None', label='dummy-tophead')

    for id_unique in list_polygones:
        plt.ylim(0,110)
        plt.xticks(fontsize=20)
        plt.yticks(fontsize=20)
        plt.gcf().autofmt_xdate()
        plt.xlabel("Dates",fontsize=20)
        plt.ylabel("NDVI",fontsize=20)
    
    
        line, = plt.plot(df_tmp.loc[(classe, id_unique), "date"],
                 df_tmp.loc[(classe, id_unique), "ndvi"],  
                 label="polygone : {}".format(id_unique), 
                 marker = "o" )
        plt.fill_between(df_tmp.loc[(classe, id_unique), "date"],
                 df_tmp.loc[(classe, id_unique), "ecart-type-min"],  
                 df_tmp.loc[(classe, id_unique), "ecart-type-max"],  
                 alpha=0.3, color = line.get_color())
        
        plt.plot(df_sent_tmp.loc[(classe, id_unique), "date"],
                 df_sent_tmp.loc[(classe, id_unique), "ndvi"], 
                 label="polygone : {} S2".format(id_unique), 
                 linestyle='dotted',
                 marker = "o", color = line.get_color())
        plt.fill_between(df_sent_tmp.loc[(classe, id_unique), "date"],
                 df_sent_tmp.loc[(classe, id_unique), "ecart-type-min"],  
                 df_sent_tmp.loc[(classe, id_unique), "ecart-type-max"],  
                 alpha=0.3, color = line.get_color())
        
        lines.append(line)
        
 
    plt.title("NDVI " + dict_labels[classe],fontsize=20)
    
    
    
    # Create legend from scratch
    lines = [dummy, dummy] + [dummy]*len(list_polygones) + lines

    lines = lines + [Line2D([0], [0], linestyle = '-', color = "black"),
                     Line2D([0], [0],linestyle = 'dotted', color = "black")]
    
    leg = plt.legend(lines,
              [r'Polygones'] + [' ']*(len(list_polygones)-1) + [r'Satellites', ''] + [str(i) for i in list_polygones] + ["Venus", "Sentinel-2"],
              ncol=2, fontsize=15)
    #https://stackoverflow.com/questions/21570007/subheadings-for-categories-within-matplotlib-custom-legend
    plt.gca().add_artist(leg)
    plt.savefig("/media/queunet/WD/png/NDVI VENUS vs SENTINEL 2 " + dict_labels[classe])
    plt.show()




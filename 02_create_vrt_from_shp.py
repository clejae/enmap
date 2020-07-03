# This script creates a virtual raster based on a polygon-shapefile that represent a subset area and a raster mosaic.

# !!!! DEPENDING ON THE INPUT, YOU HAVE TO CHANGE THE x_min AND x_max CALCULATION.
# SOMETIMES THERE IS A SHIFT OF 20cm IN THE LANDSAT DATA.

import gdal
import ogr
import glob
import os
import numpy as np

sub = 'ba'
# for m in range(2,13, 2):
for abr in ['spectemp_metr_QT2','spectemp_metr_QT3']:

    for s in range(1,7):
        # Define Input
        shp_path = 'N:/temp/temp_akpona/x_calieco/02_subsets_img/shape/{0}_subset{1}.shp'.format(sub,s)
        ras_path = r'Y:\california\level3_{0}\mosaic\2013_{1}.tif'.format(sub,abr)

        # Define Output
        vrt_path = r'N:\temp\temp_akpona\x_calieco\02_subsets_img\landsat_spectemp_metr\landsat_{0}_{1}_subset{2}.vrt'.format(abr, sub, s)

        try:
            os.mkdir(os.path.dirname(vrt_path))
        except FileExistsError:
            print("Directory " + os.path.dirname(vrt_path) + " already exists")

        # Open input datasets
        shp = ogr.Open(shp_path)
        lyr = shp.GetLayer()

        # ras = gdal.Open(ras_path)

        # get extent of subset site from shp
        feat = lyr.GetNextFeature()
        geom = feat.geometry().Clone()
        ring = geom.GetGeometryRef(0)
        num_pt = ring.GetPointCount()
        x_lst, y_lst = [], []
        for pt_i in range(num_pt):
            pt = ring.GetPoint(pt_i)
            x_lst.append(pt[0])
            y_lst.append(pt[1])
        x_min = min(x_lst)  + 0.3 # because the big mosaic vrt is shifted by around 0.21875 m
        x_max = max(x_lst)  + 0.3 # because the big mosaic vrt is shifted by around 0.21875 m
        y_min = min(y_lst)
        y_max = max(y_lst)

        # band_lst = list(range(36, 58))

        # define VRT Options
        vrt_options = gdal.BuildVRTOptions(outputBounds=(x_min, y_min, x_max, y_max)) # , bandList = band_lst
        vrt = gdal.BuildVRT(vrt_path, ras_path, options = vrt_options)

        del(vrt)

print("done")
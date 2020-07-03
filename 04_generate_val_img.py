# This script creates a validation image, i.e. only pixels that are covered by validation polygons are extracted and saved.
# The validation image can be used for fast processing of the validation areas.

# !!!! ADAPT THE MIN MAX DATA RANGES !!!!!

from osgeo import gdal
import numpy as np
import ogr
import os

sub = 'ba'

for s in range(1,7):
    for abr in ['spectemp_metr_QT2','spectemp_metr_QT3']:
        # Define Input
        ras_path = r'N:\temp\temp_akpona\x_calieco\02_subsets_img\landsat_spectemp_metr\landsat_{0}_{1}_subset{2}.vrt'.format(
            abr, sub, s)

        if sub == 'ba':
            val_shp_path = r'N:\temp\temp_akpona\x_calieco\01_data\validation\00_validation_pixelwise_ba.shp'
        else:
            val_shp_path = r'N:\temp\temp_akpona\x_calieco\01_data\validation\validation_pixelwise_{0}_subset{1}_frac.shp'.format(sub, s)

        # Define Output
        out_path = r'N:\temp\temp_akpona\x_calieco\04_vali_img\landsat_spectemp_metr\landsat_{0}_{1}_subset{2}_valimg.bsq'.format(abr, sub, s)

        # Define data ranges:
        # Reflectance
        min_val = 0
        max_val = 10000

        # Indices
        # min_val = -10000
        # max_val = 10000

        # Tasseled cap
        # min_val = -32766
        # max_val = 80000

        ## PROCESSING
        # create output folder
        try:
            os.mkdir(os.path.dirname(out_path))
        except FileExistsError:
            print("Directory " + os.path.dirname(out_path) + " already exists")

        # Open input datasets
        ras = gdal.Open(ras_path)
        gt = ras.GetGeoTransform()
        pr = ras.GetProjection()

        in_arr = ras.ReadAsArray()

        val_shp = ogr.Open(val_shp_path)
        val_lyr = val_shp.GetLayer()

        # filter validation sites by extent of input raster
        minx = gt[0]
        maxx = gt[0] + gt[1] * ras.RasterXSize
        miny = gt[3] + gt[5] * ras.RasterYSize
        maxy = gt[3]

        val_lyr.SetSpatialFilterRect(minx, miny, maxx, maxy)

        # create empty array that will be filled
        num_feat = val_lyr.GetFeatureCount()
        num_bands = ras.RasterCount
        fill_arr = np.zeros((num_bands, num_feat), dtype=float)

        # loop over all pixel-polygons and extract raster values at polygon centroid location
        i = 0
        for feat in val_lyr:

            # calculate centroid
            centroid = feat.geometry().Centroid()
            mx = centroid.GetX()
            my = centroid.GetY()

            # transform centroid coordinates to row and column values
            px = int((mx - gt[0]) / gt[1])
            py = int((my - gt[3]) / gt[5])

            # extract raster values and fill into array
            extract = in_arr[:, py, px]
            if np.min(extract) >= min_val and np.max(extract) <= max_val:
                fill_arr[:, i] = extract
            else:
                fill_arr[:, i] = -9999

            # print information on pixel polygon
            if sub == 'ba':
                name = feat.GetField('NewName')
            else:
                name = feat.GetField('UniqueID')
            print(name)
            print(px,py)

            i += 1
        val_lyr.ResetReading()

        # reshape fill array into desired output shape
        out_arr = np.reshape(fill_arr, (num_bands, int(num_feat / 9), 9))
       # out_arr = out_arr * 10000
        out_arr = out_arr.astype(int)

        # create output raster
        rows = out_arr.shape[1]
        cols = out_arr.shape[2]
        target_ds = gdal.GetDriverByName('ENVI').Create(out_path, cols, rows, num_bands, gdal.GDT_Int32)
        target_ds.SetGeoTransform([gt[0], 30, 0, gt[3], -30, 0])
        target_ds.SetProjection(ras.GetProjection())

        # fill output raster with output array
        for i in range(1,num_bands+1):
            band = target_ds.GetRasterBand(i)
            band.WriteArray(out_arr[i - 1])
            band.SetNoDataValue(-9999)
            band.FlushCache()

        # close variables in python
        del(target_ds)
        del(ras)
        del(val_shp)

        # Map info comes with rotation - it needs to be deleted
        # has to be done after the target_ds is deleted, because only then the header is created
        hdr = open(out_path[:-3] + "hdr").read()
        hdr = hdr.replace(', rotation=-45', '')
        with open(out_path[:-3] + "hdr", 'w') as out_file:
            out_file.write(hdr)
        out_file.close
        del (out_file)

print("done")
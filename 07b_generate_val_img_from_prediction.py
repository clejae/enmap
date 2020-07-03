# This script extracts all predicted fractions covered by validation areas, so that a validation image is created for later validation with script "07_validation.py"

from osgeo import gdal
import numpy as np
import ogr

# define output name
output = r'N:\temp\temp_akpona\x_calieco\04_vali_img\enmap_su\enmap_su_lt_subset3_valimg_from_pred.bsq'
raster_path = r'N:\temp\temp_akpona\x_calieco\06_predictions\enmap_su_lt_subset3_fullimg_mean\aggregations\mean.bsq'
val_shape_path = r'N:\temp\temp_akpona\x_calieco\01_data\validation\validation_pixelwise_lt_subset3_frac.shp'

min_val = 0
max_val = 1

# load data
raster = gdal.Open(raster_path)
gt = raster.GetGeoTransform()
pr = raster.GetProjection()

input_array = raster.ReadAsArray()

validation_shape = ogr.Open(val_shape_path)
validation_lyr = validation_shape.GetLayer()

# filter validation sites by extent of input raster
minx = gt[0]
maxx = gt[0] + gt[1]*raster.RasterXSize
miny = gt[3] + gt[5]*raster.RasterYSize
maxy = gt[3]

validation_lyr.SetSpatialFilterRect(minx, miny, maxx, maxy)

# create empty array that will be filled
num_feat = validation_lyr.GetFeatureCount()
num_bands = raster.RasterCount
fill_array = np.zeros((num_bands, num_feat), dtype=float)

# loop over all pixel-polygons and extract raster values at polygon centroid location
i = 0
for feat in validation_lyr:

    # calculate centroid
    centroid = feat.geometry().Centroid()
    mx = centroid.GetX()
    my = centroid.GetY()

    # transform centroid coordinates to row and column values
    px = int((mx - gt[0]) / gt[1])
    py = int((my - gt[3]) / gt[5])

    # extract raster values and fill into array
    extract = input_array[:,py,px]
    if np.min(extract) >= min_val and np.max(extract) <= max_val:
        fill_array[:, i] = extract
    else:
        fill_array[:, i] = -9999

    # print information on pixel polygon
    # name = feat.GetField('NewName')
    name = feat.GetField('UniqueID')
    print(name)
    print(px,py)

    i += 1
validation_lyr.ResetReading()

# reshape fill array into desired output shape
output_array = np.reshape(fill_array, (num_bands, int(num_feat/9), 9))
# output_array = output_array * 10000
# output_array = output_array.astype(int)

# create output raster
# !! map info comes with rotation - if not wanted it needs to be manually deleted !!
rows = output_array.shape[1]
columns = output_array.shape[2]
target_ds = gdal.GetDriverByName('ENVI').Create(output, columns, rows, num_bands, gdal.GDT_Float32)
target_ds.SetGeoTransform([gt[0], 30, 0, gt[3], -30, 0])
target_ds.SetProjection(raster.GetProjection())

# fill output raster with output array
for i in range(1,num_bands+1):
    band = target_ds.GetRasterBand(i)
    band.WriteArray(output_array[i-1])
    band.SetNoDataValue(-9999)
    band.FlushCache()

# close variables in python
del(target_ds)
del(raster)
del(validation_shape)

print("done")
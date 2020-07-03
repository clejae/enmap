# This script creates a reference image based on a shapefile containing the reference fractions.
# The reference image has the same dimension as the corresponding validation image.
# The reference fractions are saved at the same locations as the spectra that will be unmixed and compared with the reference fractions.


from osgeo import gdal
import numpy as np
import ogr


level = "level3_lab"
sub = 'ba'

for i in range(1,7):
    # Define Input
    ras_path = r'N:\temp\temp_akpona\x_calieco\02_subsets_img\enmap_su\enmap_su_{0}_subset{1}.vrt'.format(sub, i) # only used to extract gt and pr
    if sub == 'ba':
        val_shp_path = r'N:\temp\temp_akpona\x_calieco\01_data\validation\00_validation_pixelwise_ba.shp'
    else:
        val_shp_path = r'N:\temp\temp_akpona\x_calieco\01_data\validation\validation_pixelwise_{0}_subset{1}_frac.shp'.format(
        sub, i)

    # Define Output
    out_path = 'N:/temp/temp_akpona/x_calieco/05_ref_img/{0}/{0}_subset{1}_refimg_{2}.bsq'.format(sub, i, level)
    # Open input datasets
    ras = gdal.Open(ras_path)
    gt = ras.GetGeoTransform()
    pr = ras.GetProjection()

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
    fill_arr = np.zeros((4 , int(num_feat/9), 9), dtype=float) # 4 classes, num_feat equals rows, 9 pixels in each pixel block

    tre_list, shr_list, gra_list, bac_list = [], [], [], []

    name_list = []

    # loop over all pixel-polygons and extract raster values at polygon centroid location
    i = 0
    for feat in val_lyr:
        if sub == 'ba':
            name = feat.GetField('NewName')
        else:
            name = feat.GetField('UniqueID')
        name_list.append(name)
        print(name)

        tre_frac = feat.GetField('l3_tre')
        shr_frac = feat.GetField('l3_shr')
        gra_frac = feat.GetField('l3_gra')
        bac_frac = feat.GetField('l3_bac')

        tre_list.append(tre_frac)
        shr_list.append(shr_frac)
        gra_list.append(gra_frac)
        bac_list.append(bac_frac)
    val_lyr.SetSpatialFilter(None)
    val_lyr.ResetReading()

    tre_arr = np.asarray(tre_list)
    shr_arr = np.asarray(shr_list)
    gra_arr = np.asarray(gra_list)
    bac_arr = np.asarray(bac_list)

    tre_arr_r = np.reshape(tre_arr, (int(num_feat/9), 9))
    shr_arr_r = np.reshape(shr_arr, (int(num_feat/9), 9))
    gra_arr_r = np.reshape(gra_arr, (int(num_feat/9), 9))
    bac_arr_r = np.reshape(bac_arr, (int(num_feat/9), 9))

    fill_arr[0,:,:] = tre_arr_r
    fill_arr[1,:,:] = shr_arr_r
    fill_arr[2,:,:] = gra_arr_r
    fill_arr[3,:,:] = bac_arr_r

    fill_arr = fill_arr/100

    rows = fill_arr.shape[1]
    columns = fill_arr.shape[2]
    num_bands = fill_arr.shape[0]
    target_ds = gdal.GetDriverByName('ENVI').Create(out_path, columns, rows, num_bands, gdal.GDT_Float32)
    target_ds.SetGeoTransform([gt[0], 30, 0, gt[3], -30, 0])
    target_ds.SetProjection(pr)

    # fill output raster with output array
    for i in range(1,num_bands+1):
        band = target_ds.GetRasterBand(i)
        band.WriteArray(fill_arr[i-1])
        band.SetNoDataValue(-9999)
        band.FlushCache()

    # close variables in python
    del(target_ds)

    # Map info comes with rotation - it needs to be  deleted
    # has to be done after the target_ds is deleted, because only then the header is created
    hdr = open(out_path[:-3] + "hdr").read()
    hdr = hdr.replace(', rotation=-45', '')
    with open(out_path[:-3] + "hdr", 'w') as out_file:
        out_file.write(hdr)
    out_file.close
    del (out_file)

    # needed for validation
    with open(out_path[:-3] + "txt", "w") as f:
        for name in name_list:
            f.write(name + "\n")
    f.close

print('done')
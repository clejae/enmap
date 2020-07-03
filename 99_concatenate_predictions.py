import gdal
import numpy as np
import os

def writeArrayToRaster(in_array, out_path, gt, pr, no_data_value):

    import gdal
    from osgeo import gdal_array

    type_code = gdal_array.NumericTypeCodeToGDALTypeCode(in_array.dtype)

    if len(in_array.shape) == 3:
        nbands_out = in_array.shape[0]
        x_res = in_array.shape[2]
        y_res = in_array.shape[1]

        out_ras = gdal.GetDriverByName('GTiff').Create(out_path, x_res, y_res, nbands_out, type_code)
        out_ras.SetGeoTransform(gt)
        out_ras.SetProjection(pr)

        for b in range(0, nbands_out):
            band = out_ras.GetRasterBand(b + 1)
            arr_out = in_array[b, :, :]
            band.WriteArray(arr_out)
            band.SetNoDataValue(no_data_value)
            band.FlushCache()

        del (out_ras)

    if len(in_array.shape) == 2:
        nbands_out = 1
        x_res = in_array.shape[1]
        y_res = in_array.shape[0]

        out_ras = gdal.GetDriverByName('GTiff').Create(out_path, x_res, y_res, nbands_out, gdal.GDT_Float32)
        out_ras.SetGeoTransform(gt)
        out_ras.SetProjection(pr)

        band = out_ras.GetRasterBand( 1)
        band.WriteArray(in_array)
        band.SetNoDataValue(no_data_value)
        band.FlushCache()

        del (out_ras)

level = "level4_lab"
wd = r'N:\temp\temp_akpona\x_calieco\06_predictions\landsat_single_month'

for abr in ['06']:

    # pre = '{0}_ba'.format(abr)
    # pre = 'landsat_{0}_ba'.format(abr)
    pre = 'landsat_2013{0}15_bap_ba'.format(abr)

    # out_pth = r'{0}\{1}\{1}_predictions_concatenated_{2}.tif'.format(wd, pre, level )
    out_pth = r'{0}\{2}\{1}\{1}_predictions_concatenated_{3}.tif'.format(wd, pre,abr, level)

    arr_lst = []
    for s in range(1, 7):
        # ras = gdal.Open(r'{0}\{1}_subset{2}_valimg_mean_{3}\aggregations\mean.bsq'.format(wd, pre,s,level))
        ras = gdal.Open(r'{0}\{4}\{1}_subset{2}_valimg_mean_{3}\aggregations\mean.bsq'.format(wd, pre, s, level, abr))
        arr = ras.ReadAsArray()
        arr_lst.append(arr)

    try:
        os.mkdir(os.path.dirname(out_pth))
    except FileExistsError:
        print("Directory " + os.path.dirname(out_pth) + " already exists")

    arr_conc = np.concatenate(arr_lst,1)

    gt = ras.GetGeoTransform()
    pr = ras.GetProjection()
    no_data_value = -32767

    writeArrayToRaster(arr_conc, out_pth, gt, pr, no_data_value)




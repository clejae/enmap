import gdal

#### ------------------------------ FUNCTIONS ----------------------------- ####

def stackMultibandRasters(ras_lst, out_path):
    '''

    Creates a stack of rasters with the same x and y dimensions.
    The datatype of the output raster is based on the datatype of the first raster in the list.

    :param ras_lst: List of raster objects. Rasters must have the same x and y dimensions.
    :param out_path: Full path and name of output file.
    :return: A Geotiff raster.
    '''

    n = len(ras_lst)
    bands = ras_lst[0].RasterCount
    x_res = ras_lst[0].RasterXSize
    y_res = ras_lst[0].RasterYSize

    nbands_out = 0
    for ras in ras_lst:
        num_bands = ras.RasterCount
        nbands_out = nbands_out + num_bands

    # nbands_out  = n * bands

    data_type = ras_lst[0].GetRasterBand(1).DataType
    # data_type = gdal.GetDataTypeName(data_type)

    no_data_value = ras_lst[0].GetRasterBand(1).GetNoDataValue()
    gt = ras_lst[0].GetGeoTransform()
    pr = ras_lst[0].GetProjection()

    print(
        'Create raster stack with {0} bands, {1} columns and {2} rows of datatype {3}.'.format(nbands_out, x_res, y_res,
                                                                                               data_type))

    out_ras = gdal.GetDriverByName('GTiff').Create(out_path, x_res, y_res, nbands_out, data_type)
    out_ras.SetGeoTransform(gt)
    out_ras.SetProjection(pr)

    # Iterate over all rasters in the input list. For each raster, loop over the bands.

    curr_i = 0
    for r, ras in enumerate(ras_lst):
        print('Band {0}/{1}'.format(r + 1, n))
        for b in range(1, bands + 1):
            curr_i += 1
            # print(curr_i)

            # Get the current band and its array.
            curr_band = ras.GetRasterBand(b)
            curr_arr = curr_band.ReadAsArray()

            # Create an index for the output raster. Get band i of output raster. Write the array to band i.

            out_band = out_ras.GetRasterBand(curr_i)
            out_band.WriteArray(curr_arr)
            out_band.SetNoDataValue(no_data_value)
            out_band.FlushCache()
        print('done')

    del (out_ras)

#### ------------------------------ PROCESSING ----------------------------- ####


# wd = r'Y:\california\level3_ba\mosaic\\'
# sptmp_lst = ['Q50', 'Q25', 'Q75', 'MIN', 'MAX', 'STD']
# ras_pths = [wd + '20131001_LEVEL3_LNDLG_{0}.vrt'.format(ind) for ind in sptmp_lst]
# ras_lst = [gdal.Open(pth) for pth in ras_pths]
# out_path = wd + '2013_QT2_spec-temp-metr.tif'
# stackMultibandRasters(ras_lst, out_path)
#
# wd = r'Y:\california\level3_ba\mosaic\\'
# sptmp_lst = ['Q50', 'Q25', 'Q75', 'MIN', 'MAX', 'STD']
# ras_pths = [wd + '20140101_LEVEL3_LNDLG_{0}.vrt'.format(ind) for ind in sptmp_lst]
# ras_lst = [gdal.Open(pth) for pth in ras_pths]
# out_path = wd + '2013_QT3_spec-temp-metr.tif'
# stackMultibandRasters(ras_lst, out_path)


# ['TCB','TCG','TCW']
# ['BLU','GRN','RED','NIR','SW1','SW2']
# ['NDV','EVI']
wd = r'N:\temp\temp_akpona\x_calieco\02_subsets_img\landsat_bands_tsi\\'
for s in range(1,7):
    print('SubsetArea',s)
    ras_pths = [wd + 'landsat_{0}_ba_subset{1}.vrt'.format(ind, s) for ind in ['BLU_QT3','GRN_QT3','RED_QT3','NIR_QT3','SW1_QT3','SW2_QT3']]
    ras_lst = [gdal.Open(pth) for pth in ras_pths]

    out_path = wd + 'landsat_bands_stack_QT3_ba_subset{0}.tif'.format(s)

    stackMultibandRasters(ras_lst, out_path)

    print('SubsetArea', s, 'done.')



# arr_lst = [ras.ReadAsArray() for ras in ras_lst]
# arr_out = np.concatenate(arr_lst)
#
# gt = ras_lst[0].GetGeoTransform()
# pr = ras_lst[0].GetProjection()
#
# writeRaster(arr_out, wd + '2013_spec-temp-metr.tif', gt, pr, -9999)
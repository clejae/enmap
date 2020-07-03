# This script creates an ENVI-speclib based on a (virtual) raster and a polygon-shapefile representing areas of pure LC.
# If a polygon covers multiple pixels, all pixels are averaged and the mean is saved as an endmember.
# Additionally, a library with all separate spectra of the pixels is created.
# In the csv-file of the pixel-wise library the coordinates of the pixel centres are stored.

# !!!! ADAPT THE MIN MAX DATA RANGES !!!!!

# load packages
import ogr
import gdal
import numpy as np
import pandas as pd
import os
import math

sub = 'ba'
# sub = lt;

#'BLU_QT2', 'GRN_QT2', 'RED_QT2', 'NIR_QT2', 'SW1_QT2', 'SW_QT2'

# index of subset site, also possible with loop
for s in range(1,7):
    for abr in ['spectemp_metr_QT2','spectemp_metr_QT3']:
        print(s, abr)
        ## USER DEFINITIONS
        ## Input:
        raster_path = r'N:\temp\temp_akpona\x_calieco\02_subsets_img\landsat_spectemp_metr\landsat_{0}_{1}_subset{2}.vrt'.format(abr, sub, s)

        if sub == 'ba':
            lib_shape_path = r'N:\temp\temp_akpona\x_calieco\01_data\library\shape_all_final_cleaned_v1_ba.shp'
        else:
            lib_shape_path = r'N:\temp\temp_akpona\x_calieco\01_data\library\{0}_subset{1}_training.shp'.format(sub, s)

        ## Output:
        # will be appended by "mean" or "pix"
        output_name = r'N:\temp\temp_akpona\x_calieco\03_subsets_lib\landsat_spectemp_metr\landsat_{0}_{1}_subset{2}.sli'.format(abr, sub, s)

        # Data ranges
        # Reflectance
        min_val = 0
        max_val = 10000

        # Indices
        # min_val = -10000
        # max_val = 10000

        # Tasseled Cap
        # min_val = -32766
        # max_val = 80000

        # oversampling factor
        os_factor = 100

        # the proportion of a pixel that needs to be covered by the polygons
        min_coverage = 0.8

        ## PROCESSING
        # create output folder
        try:
            os.mkdir(os.path.dirname(output_name))
        except FileExistsError:
            print("Directory " + os.path.dirname(output_name) + " already exists")

        # load data
        print('Loading data')
        raster = gdal.Open(raster_path)
        gt = raster.GetGeoTransform()
        pr = raster.GetProjection()
        input_arr = raster.ReadAsArray()

        library_shape = ogr.Open(lib_shape_path)
        library_lyr = library_shape.GetLayer()
        sr = library_lyr.GetSpatialRef()

        # filter validation sites by extent of input raster
        print('Filter polygons by extent of input raster')
        col = raster.RasterXSize
        row = raster.RasterYSize

        minx = gt[0] + 0.4
        maxx = gt[0] + gt[1]* col - 0.4
        miny = gt[3] + gt[5]* row + 0.4
        maxy = gt[3] - 0.4

        library_lyr.SetSpatialFilterRect(minx, miny, maxx, maxy)

        x_ref = gt[0]
        y_ref = gt[3]

        # create empty array that will be filled
        num_feat = library_lyr.GetFeatureCount()
        num_bands = raster.RasterCount

        # initialize string of spectra names for metadata file
        spectra_names = "{"

        attr_out_list = []
        value_out_list = []

        spectra_names_pix = "{"
        value_out_list_pix = []
        attr_out_list_pix = []

        # loop over features for rasterization
        i = 0

        for feat in library_lyr:

            # extract feature attribute from dbf
            name = feat.GetField('Full_ID') # is actually the spectrum ID

            print('\nPolygon', name, "subset", s)

            # get polygon definition of feat
            geom = feat.GetGeometryRef()
            geom_wkt = geom.ExportToWkt()

            extent = geom.GetEnvelope()

            x_min_ext = extent[0]
            x_max_ext = extent[1]
            y_min_ext = extent[2]
            y_max_ext = extent[3]

            # # align coordinates to enmap raster
            dist_x = x_ref - x_min_ext
            steps_x = -(math.floor(dist_x / 30))
            x_min_ali = x_ref + steps_x * 30 #- 30

            dist_x = x_ref - x_max_ext
            steps_x = -(math.floor(dist_x / 30))
            x_max_ali = x_ref + steps_x * 30 #+ 30

            dist_y = y_ref - y_min_ext
            steps_y = -(math.floor(dist_y / 30))
            y_min_ali = y_ref + steps_y * 30 #- 30

            dist_y = y_ref - y_max_ext
            steps_y = -(math.floor(dist_y / 30))
            y_max_ali = y_ref + steps_y * 30 #+ 30

            # slice input raster array to common dimensions
            px_min = int((x_min_ali - gt[0]) / gt[1])
            px_max = int((x_max_ali - gt[0]) / gt[1])

            py_max = int((y_min_ali - gt[3]) / gt[5])# raster coordinates count from S to N, but array count from Top to Bottum, thus pymax = ymin
            py_min = int((y_max_ali - gt[3]) / gt[5])

            geom_arr = input_arr[:, py_min : py_max, px_min : px_max]
			# geom_arr = raster.ReadAsArray()[:, py_min : py_max, px_min : px_max] #input_arr[:, py_min : py_max, px_min : px_max]


            # create memory layer for rasterization
            driver_mem = ogr.GetDriverByName('Memory')
            ogr_ds = driver_mem.CreateDataSource('wrk')
            ogr_lyr = ogr_ds.CreateLayer('poly', srs=sr)

            feat_mem = ogr.Feature(ogr_lyr.GetLayerDefn())
            feat_mem.SetGeometryDirectly(ogr.Geometry(wkt = geom_wkt))

            ogr_lyr.CreateFeature(feat_mem)

            # rasterize geom with provided oversampling factor
            col_sub = px_max - px_min
            row_sub = py_max - py_min

            col_os = col_sub * os_factor
            row_os = row_sub * os_factor

            step_size_x = gt[1] / os_factor
            step_size_y = gt[5] / os_factor

            gt_os = (x_min_ali, step_size_x, 0, y_max_ali, 0, step_size_y)

            target_ds = gdal.GetDriverByName('MEM').Create('', col_os, row_os, 1, gdal.GDT_Byte)
            target_ds.SetGeoTransform(gt_os)

            band = target_ds.GetRasterBand(1)
            band.SetNoDataValue(-9999)

            # Calculate polygon coverage of pixels
            gdal.RasterizeLayer(target_ds, [1], ogr_lyr, burn_values=[1])

            os_arr = band.ReadAsArray()

            win_size = (os_factor, os_factor)
            slices_list = []
            step_y = 0

            while step_y < row_os:
                step_x = 0
                while step_x < col_os:
                    slice = os_arr[step_y : step_y + win_size[0], step_x : step_x + win_size[1]]
                    slice_mean = np.mean(slice)
                    slices_list.append(slice_mean)
                    step_x += os_factor
                step_y += os_factor

            aggr_arr = np.array(slices_list)
            aggr_arr_r = np.reshape(aggr_arr, (row_sub , col_sub), order = 'C')

            # create a mask array, which indicates all pixels with a minimum coverage of the provided treshold
            mask_array = np.where(aggr_arr_r > min_coverage, 1, 0)

            ## ----------------------- pixelwise -----------------------
            count = 0
            pix_count = 0
            road_list = np.where(mask_array == 1)
            for index_y in road_list[0]:
                index_x = road_list[1][count]
                extr_arr = geom_arr[:, index_y, index_x]

                pix_count += 1
                # check if invalid values are in data range, if yes do not include
                if np.min(extr_arr) >= min_val and np.max(extr_arr) <= max_val:
                    extr_list = extr_arr.tolist()
                    count += 1

                    # save values to list
                    value_out_list_pix.append(extr_list)

                    # extract feature attribute from dbf
                    attr_sub_list_pix = []
                    attr_sub_list_pix.append(name + '_' + str(count))
                    if sub == 'ba':
                        attr_sub_list_pix.append(feat.GetField('OrigCla'))         # is actually the class description
                    else:
                        attr_sub_list_pix.append(feat.GetField('Name'))
                    attr_sub_list_pix.append(feat.GetField('level3_lab'))
                    attr_sub_list_pix.append(feat.GetField('level4_lab'))
                    attr_sub_list_pix.append(feat.GetField('level5_lab'))
                    attr_sub_list_pix.append(name)

                    # get coordinate of pixel centre
                    x_coord = gt_os[0] + (index_x * gt_os[1] * os_factor) + (gt_os[1] * os_factor) / 2
                    y_coord = gt_os[3] + (index_y * gt_os[5] * os_factor) + (gt_os[5] * os_factor) / 2

                    attr_sub_list_pix.append(x_coord)
                    attr_sub_list_pix.append(y_coord)

                    # expand spectra names str
                    spectra_names_pix = spectra_names_pix + name + '-' + str(count) + ","

                    # save attributes to list
                    attr_out_list_pix.append(attr_sub_list_pix)

                    #pix_count += 1
                else:
                    print(str(s) +": For pixel", name + '-' + str(count) , " the maximum reflectances of ", np.max(extr_arr), "is above", max_val, "or the minimum reflectance of",
                          np.min(extr_arr), "is below", min_val)

            print("Number of pixels in polygon", name, ":", pix_count)

            # ## ----------------------- aggregated -----------------------
            # if at least one cell (i.e. pixel) is remaining:
            if np.sum(mask_array) >= 1:
                # loop over bands to calculate band mean
                band_mean_list = []

                for j in range(num_bands):
                    band_array = geom_arr[j, :, :]

                    # mask all values that are not in the data range
                    #band_array_m = np.ma.masked_where(np.logical_or(band_array < min_val, band_array > max_val), band_array)
                    #band_mean = np.mean(band_array_m[mask_array == 1])
                    band_mean = np.mean(band_array[mask_array == 1])

                    band_mean_list.append(band_mean)

                    #fill_array[i,j] = band_mean
                if max(band_mean_list) <= max_val and min(band_mean_list) >= min_val:
                    value_out_list.append(band_mean_list)
                    attr_sub_list = []
                    attr_sub_list.append(name)
                    if sub == 'ba':
                        attr_sub_list.append(feat.GetField('OrigCla'))  # is actually the class description
                    else:
                        attr_sub_list.append(feat.GetField('Name'))       # is actually the class description
                    #attr_sub_list.append(feat.GetField('level2_lab'))
                    attr_sub_list.append(feat.GetField('level3_lab'))
                    attr_sub_list.append(feat.GetField('level4_lab'))
                    attr_sub_list.append(feat.GetField('level5_lab'))

                    ## other optional attributes that come with the Bay Area Shapefile
                    # attr_sub_list.append(feat.GetField('OrigCla'))
                    # attr_sub_list.append(feat.GetField('Level5'))
                    # attr_sub_list.append(feat.GetField('Level4'))
                    # attr_sub_list.append(feat.GetField('Level3'))
                    # attr_sub_list.append(feat.GetField('Level2'))
                    # attr_sub_list.append(feat.GetField('Level1'))
                    # attr_sub_list.append(feat.GetField('level5_lab'))
                    # attr_sub_list.append(feat.GetField('level4_lab'))
                    # attr_sub_list.append(feat.GetField('level2_lab'))
                    # attr_sub_list.append(feat.GetField('level1_lab'))

                    attr_out_list.append(attr_sub_list)

                    # expand spectra names str
                    spectra_names = spectra_names + name + ","

                else:
                    print(str(s) +": For polygon", name ,"Maximum reflectances of ", max(band_mean_list) ,"is above", max_val, "or minimum reflectance of", min(band_mean_list) ,"is below", min_val)
                    feat.GetField('level3_lab')

            # otherwise print warning.
            else:
                print("No pixel covered by at least", min_coverage, "coverage!")
                print(feat.GetField('level3_lab'))

            i += 1

            del(target_ds)
            del(ogr_lyr)
            del(ogr_ds)
        library_lyr.ResetReading()

        ## ----------------------- pixelwise -----------------------
        spectra_names_pix = spectra_names_pix[:-1]  # delete last added comma
        spectra_names_pix = spectra_names_pix + "}" # close string with curved brackets

        value_out_array_pix = np.array(value_out_list_pix)

        output_name_pix = output_name[:-4] + "_pix.sli"
        # write val img to disc
        output_ds_pix = gdal.GetDriverByName('ENVI').Create(output_name_pix, value_out_array_pix.shape[1], value_out_array_pix.shape[0], 1, gdal.GDT_Float64) # important: data type = gdal.GDT_FLoat64
        band_pix = output_ds_pix.GetRasterBand(1)
        band_pix.WriteArray(value_out_array_pix)
        band_pix.SetNoDataValue(-9999)
        band_pix.FlushCache()

        output_ds_pix.SetMetadataItem('wavelength units', 'Nanometers', 'ENVI')
        output_ds_pix.SetMetadataItem('spectra_names', spectra_names_pix, 'ENVI')

        # write csv
        #attr_out_df = pd.DataFrame(attr_out_list, columns=['Full_ID','OrigCla','Level5','Level4','Level3','Level2','Level1','level5_lab','level4_lab','level3_lab','level2_lab','level1_lab'])
        attr_out_df_pix = pd.DataFrame(attr_out_list_pix, columns=['Full_ID','Name','level3_lab','level4_lab','level5_lab','plot_name','x_coord','y_coord'])
        attr_out_df_pix.to_csv(output_name[:-4] + "_pix.csv",index=False)

        del(output_ds_pix)

        # set metadata values that could not be changed before
        file_pix = open(output_name[:-4] + "_pix.hdr").read()
        file_pix = file_pix.replace('file type = ENVI Standard', 'file type = ENVI Spectral Library')
        out_file_pix = open(output_name[:-4] + "_pix.hdr", 'w')
        out_file_pix.write(file_pix)
        out_file_pix.close
        del out_file_pix
        # ## ----------------------- aggregated -----------------------

        spectra_names = spectra_names[:-1]  # delete last added comma
        spectra_names = spectra_names + "}" # close string with curved brackets

        value_out_array = np.array(value_out_list)

        output_name_plot = output_name[:-4] + "_mean.sli"
        # write val img to disc
        output_ds = gdal.GetDriverByName('ENVI').Create(output_name_plot, value_out_array.shape[1], value_out_array.shape[0], 1, gdal.GDT_Float64) # important: data type = gdal.GDT_FLoat64
        band = output_ds.GetRasterBand(1)
        band.WriteArray(value_out_array)
        band.SetNoDataValue(-9999)
        band.FlushCache()

        # set metadata values
        output_ds.SetMetadataItem('wavelength units', 'Nanometers', 'ENVI')
        output_ds.SetMetadataItem('spectra_names', spectra_names, 'ENVI')


        # write csv
        #attr_out_df = pd.DataFrame(attr_out_list, columns=['Full_ID','OrigCla','Level5','Level4','Level3','Level2','Level1','level5_lab','level4_lab','level3_lab','level2_lab','level1_lab'])
        attr_out_df = pd.DataFrame(attr_out_list, columns=['Full_ID','Name','level3_lab','level4_lab','level5_lab'])
        attr_out_df.to_csv(output_name[:-4] + "_mean.csv",index=False)

        del(output_ds)


        # set metadata values that could not be changed before
        file = open(output_name[:-4] + "_mean.hdr").read()
        file = file.replace('file type = ENVI Standard', 'file type = ENVI Spectral Library')
        out_file = open(output_name[:-4] + "_mean.hdr", 'w')
        out_file.write(file)
        out_file.close
        del out_file

        del(library_shape)
        del(raster)
print("\nDone!!")


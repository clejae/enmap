import gdal
import glob
import os

def createFolder(directory):
    import os
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError:
        print ('Error: Creating directory. ' + directory)

def getCorners(path):
    ds = gdal.Open(path)
    gt = ds.GetGeoTransform()
    width = ds.RasterXSize
    height = ds.RasterYSize
    minx = gt[0]
    miny = gt[3] + width * gt[4] + height * gt[5]
    maxx = gt[0] + width * gt[1] + height * gt[2]
    maxy = gt[3]
    return [minx, miny, maxx, maxy]

print("Start slicing to FORCE grid")

wd = r'Y:\california\level2_ba'

lst = glob.glob(wd + r"\*")
lst = [name for name in os.listdir(wd) if os.path.isdir(os.path.join(wd, name))]

dst_filename = r"N:\Project_California\99_temp\bcor\03_temp_mosaic\E_L2A_suBA_mosaic_crco_long.bsq"
ras = gdal.Open(dst_filename)

for tile_name in lst:
    print(tile_name)

    # get a reference raster --> take the first raster that is in the folder with the target tile name
    sub_lst = glob.glob(wd + r"\\" + tile_name + r"\*.tif")
    ref_ras = sub_lst[0]

    # extract the corners of the reference raster, which will be used to cut the enmap mosaic
    print(ref_ras)
    corners = getCorners(ref_ras)

    x_min_ext = corners[0]
    x_max_ext = corners[2]
    y_min_ext = corners[1]
    y_max_ext = corners[3]

    # create output name and create destination folder, if it does not exist alreay
    output_path =  r'N:\Project_California\00_Data\01_EnMAP\02_mosaics\BA_force\{0}\\'.format(tile_name)
    createFolder(output_path)
    output_name_full = output_path + 'E_L2A_suBA_mosaic_crco_long.bsq'

    # start the cropping
    print("Start cropping")
    ## I tested gdal.Warp, it does not produce the shift, but it alters the spectra considerably!!
    ## I would suggest using gdal Translate and then deal afterwards with the shift
    # ras_cut = gdal.Warp(output_name_full, ras, outputBounds=[x_min_ext, y_max_ext, x_max_ext, y_min_ext], format="ENVI")
    ras_cut = gdal.Translate(output_name_full, ras, projWin=[x_min_ext, y_max_ext, x_max_ext, y_min_ext], format="ENVI")
    ras_cut = None

    # reopen the cropped raster in Update mode to correct the small shift
    ras_tra = gdal.Open(output_name_full,
        gdal.GA_Update)

    # use the gt from the reference raster to update the gt of the cropped raster
    gt_ref = gdal.Open(ref_ras).GetGeoTransform()
    ras_tra.SetGeoTransform(gt_ref)
    ras_tra = None

    print(tile_name, 'done')
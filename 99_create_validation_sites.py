import ogr, osr
import gdal
import math
import os
import random

# #### FUNCTIONS
def SpatialReferenceFromRaster(ds):
    '''Returns SpatialReference from raster dataset'''
    pr = ds.GetProjection()
    sr = osr.SpatialReference()
    sr.ImportFromWkt(pr)
    return sr


# #### PROCESSING
# Define Input
box = 'lt'

shp_path = r'N:\temp\temp_akpona\x_viewit\viewit_original\tahoe.shp'



for i in range(1,4):
    sub_area = box + '_subset' + str(i)
    print(sub_area)
    out_wd = r'N:\temp\temp_akpona\x_calieco\01_data\validation'

    ras_path = r'N:\temp\temp_akpona\x_calieco\02_subsets_img\enmap_su\enmap_su_' + sub_area + '.vrt'


    # Open input datasets
    ras = gdal.Open(ras_path)
    gt = ras.GetGeoTransform()
    pr = ras.GetProjection()
    sr_ras = SpatialReferenceFromRaster(ras)

    shp = ogr.Open(shp_path)
    lyr = shp.GetLayer()
    sr_lyr = lyr.GetSpatialRef()

    # input data come in different projections.
    # Therefore, transformations in both ways are defined
    coord_trans = osr.CoordinateTransformation(sr_ras, sr_lyr) # for the filter process
    coord_trans_out = osr.CoordinateTransformation(sr_lyr, sr_ras) # for the output

    drv_mem = ogr.GetDriverByName('Memory')
    mem_ds = drv_mem.CreateDataSource("")
    repr_lyr = mem_ds.CreateLayer('', sr_ras, ogr.wkbPolygon)
    repr_lyr.CreateFields(lyr.schema)

    out_feat = ogr.Feature(lyr.GetLayerDefn())
    for feat in lyr:
        geom = feat.geometry().Clone()
        geom.TransformTo(sr_ras)
        out_feat.SetGeometry(geom)
        for i in range(feat.GetFieldCount()):
            out_feat.SetField(i, feat.GetField(i))
        repr_lyr.CreateFeature(out_feat)
    lyr.ResetReading
    out_feat = None
    repr_lyr_cs = repr_lyr.GetSpatialRef()


    # filter viewit polygons by extent of input raster
    minx_ras = gt[0]
    maxx_ras = gt[0] + gt[1] * ras.RasterXSize
    miny_ras = gt[3] + gt[5] * ras.RasterYSize
    maxy_ras = gt[3]

    repr_lyr.SetSpatialFilterRect(minx_ras, miny_ras, maxx_ras, maxy_ras)

    # filter all polygons that are 100x100m large and have a maximum coverage of a single class >= 80%
    repr_lyr.SetAttributeFilter("Shape_Leng < '401'") # optional: #  and MaximumPer > '79'

    # derive number of filtered viewit polygons
    # 50 validation blocks are desired, thus, the number of missing features is calculated
    num_feat = repr_lyr.GetFeatureCount()
    miss_feat = 50 - num_feat

    # derive reference coordinate from raster for grid alignment
    # in this case the top left corner
    # no transformation needed since raster projection is the desired output projection
    x_ref = minx_ras
    y_ref = maxy_ras

    # Create Output Shapefile
    out_shp = "/validation_pixelwise_" + sub_area + ".shp"
    out_drv = ogr.GetDriverByName("ESRI Shapefile")
    # Remove output shapefile if it already exists
    if os.path.exists(out_wd + out_shp):
        out_drv.DeleteDataSource(out_wd + out_shp)
    # Create the output shapefile
    out_ds = out_drv.CreateDataSource(out_wd + out_shp)
    out_name = "validation_pixelwise_" + sub_area
    out_poly = out_ds.CreateLayer(out_name, sr_ras, geom_type=ogr.wkbPolygon) # raster projection is desired projection
    # Add Fields
    out_poly.CreateField(ogr.FieldDefn("PolyID", ogr.OFTString))
    out_poly.CreateField(ogr.FieldDefn("PixelID", ogr.OFTString))
    out_poly.CreateField(ogr.FieldDefn("SubsetArea", ogr.OFTString))
    out_poly.CreateField(ogr.FieldDefn("UniqueID", ogr.OFTString))

    # create two empty lists for all x and y coordinates
    # will be later used to check if random created validation block fullfill minimum distance criterion
    x_coord_list = []
    y_coord_list = []

    class_id = 0

    for feat in repr_lyr:

        geom = feat.geometry().Clone()
        centre = geom.Centroid()
        mx_old, my_old = centre.GetX(), centre.GetY()



        # align coordinates to raster grid
        dist_x = x_ref - mx_old
        steps_x = -(math.floor(dist_x / 30))
        mx = x_ref + steps_x * 30

        dist_y = y_ref - my_old
        steps_y = -(math.floor(dist_y / 30))
        my = y_ref + steps_y * 30

        # indication where we are
        name = feat.GetField('POINT_ID')
        print(name)

        class_id += 1
        if len(x_coord_list) < 50:
            # Create 9x9 pixel grid and save it to shapefile
            x_list = [mx - 60, mx - 30, mx, mx + 30]  # for santabarbara
            #x_list = [mx - 45, mx - 15, mx + 15, mx + 45]  # for lake tahoe and yosemite
            y_list = [my + 30, my , my - 30, my - 60]
            for y in range(0, 3):
                for x in range(0, 3):
                    ring = ogr.Geometry(ogr.wkbLinearRing)
                    ring.AddPoint(x_list[x], y_list[y])
                    ring.AddPoint(x_list[x + 1], y_list[y])
                    ring.AddPoint(x_list[x + 1], y_list[y + 1])
                    ring.AddPoint(x_list[x], y_list[y + 1])
                    ring.AddPoint(x_list[x], y_list[y])
                    poly = ogr.Geometry(ogr.wkbPolygon)
                    poly.AddGeometry(ring)
                    poly.CloseRings()

                    out_defn = out_poly.GetLayerDefn()  # get the layer definition
                    out_feat = ogr.Feature(out_defn)  # creates an empty dummy-feature
                    out_feat.SetGeometry(poly)  # puts the polygons in the dummy feature
                    out_poly.CreateFeature(out_feat)  # adds the feature to the layer

                    pixel_id = (y * 3) + x + 1

                    out_feat.SetField(0, str(class_id))
                    out_feat.SetField(1, str(pixel_id))
                    out_feat.SetField(2, sub_area)
                    out_feat.SetField(3, sub_area + '_' + str(class_id) + '_' + str(pixel_id))
                    out_poly.SetFeature(out_feat)
                    # save coordinate to lists
            x_coord_list.append(mx_old)
            y_coord_list.append(my_old)
        else:
            print("Reached already fifty 100x100m viewit polygons. Skipping the rest.")
    repr_lyr.ResetReading


    print("Number of 100x100m viewit polygons:", len(x_coord_list), "\nNumber of missing validation blocks", miss_feat)

    num_rand_feat = 0
    while num_rand_feat < miss_feat and miss_feat > 0:
        rand_x = random.randint(minx_ras, maxx_ras)
        rand_y = random.randint(miny_ras, maxy_ras)
        check_xdist_list, check_ydist_list = [], []

        for x_coord in x_coord_list:
            check_dist = abs(x_coord - rand_x)
            check_xdist_list.append(check_dist)

        for y_coord in y_coord_list:
            check_dist = abs(y_coord - rand_y)
            check_ydist_list.append(check_dist)

        #print("Minimum X-Distance:", round(min(check_xdist_list),2), "Minimum Y-Distance:", round(min(check_ydist_list),2))
        if min(check_xdist_list) > 500 or min(check_ydist_list) > 500:
            print("x-range:",minx_ras,"-",maxx_ras)
            print("x:", rand_x)
            print("y-range:",miny_ras,"-",maxx_ras)
            print("y:", rand_y)

            num_rand_feat += 1
            #print("Distance criterion fullfilled. Number of random points:",num_rand_feat)
            mx_old = rand_x
            my_old = rand_y

            # save coordinate to lists
            x_coord_list.append(mx_old)
            y_coord_list.append(my_old)

            # align coordinates to raster grid
            dist_x = x_ref - mx_old
            steps_x = -(math.floor(dist_x / 30))
            mx = x_ref + steps_x * 30

            dist_y = y_ref - my_old
            steps_y = -(math.floor(dist_y / 30))
            my = y_ref + steps_y * 30

            # indication where we are
            name = num_rand_feat
            print("ID:", name, "\n")

            class_id += 1

            # Create 9x9 pixel grid and save it to shapefile
            x_list = [mx - 60, mx - 30, mx, mx + 30]  # for santabarbara
            #x_list = [mx - 45, mx - 15, mx + 15, mx + 45]  # for lake tahoe and yosemite
            y_list = [my + 30, my, my - 30, my - 60]
            for y in range(0, 3):
                for x in range(0, 3):
                    ring = ogr.Geometry(ogr.wkbLinearRing)
                    ring.AddPoint(x_list[x], y_list[y])
                    ring.AddPoint(x_list[x + 1], y_list[y])
                    ring.AddPoint(x_list[x + 1], y_list[y + 1])
                    ring.AddPoint(x_list[x], y_list[y + 1])
                    ring.AddPoint(x_list[x], y_list[y])
                    poly = ogr.Geometry(ogr.wkbPolygon)
                    poly.AddGeometry(ring)
                    poly.CloseRings()

                    out_defn = out_poly.GetLayerDefn()  # get the layer definition
                    out_feat = ogr.Feature(out_defn)  # creates an empty dummy-feature
                    out_feat.SetGeometry(poly)  # puts the polygons in the dummy feature
                    out_poly.CreateFeature(out_feat)  # adds the feature to the layer

                    pixel_id = (y * 3) + x + 1

                    out_feat.SetField(0, str(class_id))
                    out_feat.SetField(1, str(pixel_id))
                    out_feat.SetField(2, sub_area)
                    out_feat.SetField(3, sub_area + '_' + str(class_id) + '_' + str(pixel_id))
                    out_poly.SetFeature(out_feat)
        #else:
                #print("Random coordinate too close!")
               #print("----------")
    del(repr_lyr)

del(out_ds)
del(mem_ds)
del(ras)
del(shp)
print("done")
#for feat in lyr:

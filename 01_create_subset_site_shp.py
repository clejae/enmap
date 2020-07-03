# This script creates several shapefiles, each with one polygon inside marking the boundaries of a subset area.
# As a input it takes a point-shapefile in which each point represents the lower bottom corner the subset area.
# Defaul subset area size is 30x30km.


import ogr, osr
import math
import gdal

def SpatialReferenceFromRaster(ds):
    '''Returns SpatialReference from raster dataset'''
    pr = ds.GetProjection()
    sr = osr.SpatialReference()
    sr.ImportFromWkt(pr)
    return sr

wd = r"N:\temp\temp_akpona\x_calieco\02_subsets_img\shape\\"

#point_shape = ogr.Open("B:/temp/temp_clemens/temporal_em/preselection_bayarea_points.shp")
point_shape = ogr.Open(r"N:\temp\temp_akpona\x_calieco\02_subsets_img\shape\site_selection\preselection_sb_yn_points.shp")

point_lyr = point_shape.GetLayer()


#enmapCentroid_shape = ogr.Open('B:/temp/temp_clemens/Validation/single_EnMAP_pixel_centroid.shp')
#enmapCentroid_lyr = enmapCentroid_shape.GetLayer()

#gt = enmapCentroid_lyr.GetExtent()
#x_eM, y_eM = gt[0], gt[2]

#out_name_pre = 'preselection_site_polygons'

# ds = ogr.Open(wd,1)
# if ds.GetLayer(out_name):
#     ds.DeleteLayer(out_name)
#     out_polygons = ds.CreateLayer(out_name, point_lyr.GetSpatialRef(), ogr.wkbPolygon)
# else:
#     out_polygons = ds.CreateLayer(out_name, point_lyr.GetSpatialRef(), ogr.wkbPolygon)
#
# #add fields
# lyr_def = point_lyr.GetLayerDefn()
# for i in range(lyr_def.GetFieldCount()):
#     out_polygons.CreateField(lyr_def.GetFieldDefn(i))

for feature in point_lyr:
    geom = feature.GetGeometryRef()

    box_name = feature.GetField("camp_box")
    sub_name = feature.GetField("Site")

    ras = gdal.Open(r'N:\Project_California\99_temp\bcor\\' + box_name + r'_temp\\' +  box_name + r'_mosaic\\' + box_name + r'_mosaic_temp.bsq')
    gt = ras.GetGeoTransform()

    sr = SpatialReferenceFromRaster(ras)

    x_eM, y_eM = gt[0], gt[3]

    pt = geom.GetPoint()
    xref, yref = pt[0], pt[1]

    # align coordinates to enmap raster
    distX = x_eM-xref
    stepsX = -(math.floor(distX/30))
    mx = x_eM + stepsX*30

    distY = y_eM-yref
    stepsY = -(math.floor(distY/30))
    my = y_eM + stepsY*30

    print( xref, yref)
    print(mx, my)
    id = str(feature.GetField(0))

    ring = ogr.Geometry(ogr.wkbLinearRing)
    ring.AddPoint(mx, my)
    ring.AddPoint(mx + 30000, my)
    ring.AddPoint(mx + 30000, my + 30000)
    ring.AddPoint(mx, my + 30000)
    ring.AddPoint(mx, my)
    poly = ogr.Geometry(ogr.wkbPolygon)
    poly.AddGeometry(ring)
    poly.CloseRings()

    #out_name = out_name_pre + id
    out_name = sub_name

    ds = ogr.Open(wd, 1)
    if ds.GetLayer(out_name):
        ds.DeleteLayer(out_name)
        out_polygons = ds.CreateLayer(out_name, sr, ogr.wkbPolygon)
    else:
        out_polygons = ds.CreateLayer(out_name, sr, ogr.wkbPolygon)

    # add fields
    lyr_def = point_lyr.GetLayerDefn()
    for i in range(lyr_def.GetFieldCount()):
        out_polygons.CreateField(lyr_def.GetFieldDefn(i))

    out_defn = out_polygons.GetLayerDefn()  # get the layer definition
    out_feat = ogr.Feature(out_defn)  # erzeugt ein leeres dummy-feature
    out_feat.SetGeometry(poly)  # packt die polygone in das dummy feature
    out_polygons.CreateFeature(out_feat)  # fügt das feature zum layer hinzu

    for i in range(0, lyr_def.GetFieldCount()):
            out_feat.SetField(out_defn.GetFieldDefn(i).GetNameRef(), feature.GetField(i))
    out_polygons.SetFeature(out_feat)

    del out_polygons

point_lyr.ResetReading
del point_shape
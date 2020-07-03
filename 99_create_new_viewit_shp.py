# This script creates new 100x100m viewit polygons based on a point-shapefile

import ogr

# directory for output
wd = r"B:\temp\temp_akpona\viewit\classification\4Clemens\\"

# shape with point locations
point_shape = ogr.Open(r"B:\temp\temp_akpona\viewit\classification\4Clemens/locations_additional_viewit_LT.shp")

# viewit shapefile with attribute table definition
viewit_shape = ogr.Open(r'B:\temp\temp_akpona\viewit\classification\laketahoe\laketahoe_viewit_utm_maxclassge80_inmask_relab.shp')

# name of output
out_name = 'new_viewit_polygons_LT'

# Open layers
point_lyr = point_shape.GetLayer()
viewit_lyr = viewit_shape.GetLayer()

# create output shapefile
ds = ogr.Open(wd,1)
if ds.GetLayer(out_name):
    ds.DeleteLayer(out_name)
    out_polygons = ds.CreateLayer(out_name, viewit_lyr.GetSpatialRef(), ogr.wkbPolygon)
else:
    out_polygons = ds.CreateLayer(out_name, viewit_lyr.GetSpatialRef(), ogr.wkbPolygon)

# add attribute fields
lyr_def = viewit_lyr.GetLayerDefn()
for i in range(lyr_def.GetFieldCount()):
    out_polygons.CreateField(lyr_def.GetFieldDefn(i))

# loop through points and create polygons
for feature in point_lyr:
    geom = feature.GetGeometryRef()
    pt = geom.GetPoint()
    mx, my = pt[0], pt[1]

    print(mx, my)
    id = str(feature.GetField(0))

    ring = ogr.Geometry(ogr.wkbLinearRing)
    ring.AddPoint(mx, my)
    ring.AddPoint(mx + 100, my)
    ring.AddPoint(mx + 100, my - 100)
    ring.AddPoint(mx, my - 100)
    ring.AddPoint(mx, my)
    poly = ogr.Geometry(ogr.wkbPolygon)
    poly.AddGeometry(ring)
    poly.CloseRings()

    out_defn = out_polygons.GetLayerDefn()  # get the layer definition
    out_feat = ogr.Feature(out_defn)  # erzeugt ein leeres dummy-feature
    out_feat.SetGeometry(poly)  # packt die polygone in das dummy feature
    out_polygons.CreateFeature(out_feat)  # fügt das feature zum layer hinzu


point_lyr.ResetReading
del point_shape
del out_polygons
#-------------------------------------------------------------------------------
# Name:       Jamie Kim
# Purpose: GEOS456 - Final Assignment
# Created:     24/04/2022
#-------------------------------------------------------------------------------

#import arcpy and os
import arcpy,os
from arcpy import env
from arcpy.sa import *
import arcpy.mp as MAP
print("Imported python modules")
print("")
#check out the spatial extension
arcpy.CheckOutExtension("Spatial")
print("Checked out the spatial extension")
print("")
#set workspace environment and overwrites
ws=r"C:\GEOS456\FinalProject"
Base = ws+"\\Base_72E09"
dem72E09 = ws+"\DEM_72E09"
landCover = ws+"\Land_Cover"
NTS = ws+"\\NTS"
oilgas = ws +"\\Oil_Gas"

env.workspace = ws
env.overwriteOutput = True

print("Successfully set workspace environment and overwrites")
print("")

#Check if assignment geodatabase already exists or not, and if the geodatabase exists, delete it
if arcpy.Exists("CypressHills.gdb"):
    arcpy.Delete_management("CypressHills.gdb")
print("Completed checking geodatabase exists")
print("")

#Create Geodatabase "CypressHills"
gdb = str(arcpy.CreateFileGDB_management(ws, "CypressHills"))
print("Created CypressHills geodatabase")
print("")

#spatial reference
sr = arcpy.SpatialReference(26912)

#Mosaic multiple DEM data
env.workspace = dem72E09
arcpy.management.MosaicToNewRaster("072e09_0201_deme.dem;072e09_0201_demw.dem",gdb, "DEM_Mosaic", "", "16_BIT_UNSIGNED", "", 1)
arcpy.management.ProjectRaster(gdb+"\DEM_Mosaic",gdb+"\DEM_Mosaic_Proj", sr )
arcpy.management.Resample(gdb+"\DEM_Mosaic_Proj", gdb+"\DEM", "25")
print("Merged multiple DEM dataset")
print("")

#Create feature class of Start and End Points
env.workspace = oilgas
EP = arcpy.management.SelectLayerByAttribute("wells","", "UWID = '0074013407000'")
arcpy.CopyFeatures_management(EP, gdb+"\endLocation")
SP = arcpy.management.SelectLayerByAttribute("facilities", "", "UFI = 'A21605053'")
arcpy.CopyFeatures_management(SP, gdb+"\startLocation")
print("The start and end points was successfully created")
print("")

#create slope using dem and save in geodatabase
slope = Slope(gdb+"\DEM")
slope.save(gdb+"\Slope")
print("The Slope raster was successfully created")
print("")

#Reclassify Slope
env.workspace = gdb
inRaster = "Slope"
reclassField = "VALUE"
remap = RemapValue([[0,4,"1"],[4.000001, 10, "2"], [10.0000001, 40, "1"]])
outReclassify = Reclassify(inRaster, reclassField, remap)
outReclassify.save("recl_Slope")
print("The reclassification of slope was successfully completed")
print("")

#Euclidean Distance for River
inSourceData = Base+"\\river"
outEucDistance = EucDistance(inSourceData, "", "25")
outEucDistance.save(gdb+"\\river_eu")
print("The Euculidean Distance for River was succesfully generated")
print("")

#Reclassify River
inRaster = "river_eu"
reclassField = "VALUE"
remap = RemapValue([[0,50,"3"],[50.000001, 250, "2"], [250.00001, 2500, "1"]])
outReclassify = Reclassify(inRaster, reclassField, remap)
outReclassify.save("recl_River")
print("The reclassification of river was successfully completed")
print("")

#Euclidean Distance for Roads
inSourceData = Base+"\\roads"
outEucDistance = EucDistance(inSourceData, "", "25")
outEucDistance.save(gdb+"\\roads_eu")
print("The Euculidean Distance for Roads was succesfully generated")
print("")

#Reclassify Roads
inRaster = "roads_eu"
reclassField = "VALUE"
remap = RemapValue([[0,30,"1"],[30.000001, 250, "2"], [250.00001, 7000 , "1"]])
outReclassify = Reclassify(inRaster, reclassField, remap)
outReclassify.save("recl_Roads")
print("The reclassification of roads was successfully completed")
print("")

#Reclassify LandCover
inRaster = landCover+"\landcov"
reclassField = "VALUE"
remap = RemapValue([[1,"3"],[2, "1"], [3, "1"],[4, "1"],[5, "2"], [7, "3"]])
outReclassify = Reclassify(inRaster, reclassField, remap)
outReclassify.save("recl_LandCover")
print("The reclassification of landcover was successfully completed")
print("")

#Weighted Overlay

inRaster1 = gdb+"\\recl_Slope"
inRaster2 = gdb+"\\recl_Roads"
inRaster3 = gdb+"\\recl_River"
inRaster4 = gdb+"\\recl_LandCover"

remapSlope = RemapValue([[1, 1],[2, 2], [1, 1]])
remapRoads = RemapValue([[1, 1],[2, 2], [1, 1]])
remapRiver = RemapValue([[3, 3],[2, 2], [1, 1]])
remapLandCover = RemapValue([[3,3],[1,1], [1,1],[1,1],[2,2], [3,3]])

myWOTable = WOTable([[inRaster1, 15, "VALUE", remapSlope],[inRaster2, 15,"VALUE", remapRoads],[inRaster3, 40, "VALUE", remapRiver],[inRaster4, 30,"VALUE", remapLandCover]],[1,3,1])
costSurface=WeightedOverlay(myWOTable)
costSurface.save(gdb+"\costSurface")

print("The cost surface was successfully created")
print("")

#Cost Distance
inSourceData = "startLocation"
inCostRaster = "costSurface"
outBacklinkRaster = gdb+"\\outbklink"
outCostDist = CostDistance(inSourceData, inCostRaster, "", outBacklinkRaster)
outCostDist.save(gdb+"\costDist")

print("The cost distance was successfully created")
print("")

#Cost Path As Polyline
inDestinate = "endLocation"
inCostDistRaster = "costDist"
inBacklink = "outbklink"
outCostpath = gdb+"\PipelineRoute"
CostPathAsPolyline(inDestinate, inCostDistRaster, inBacklink, outCostpath)
print("The cost path was successfully created as polyline")
print("")

#Clip Feature
inFeature = Base+"\\roads.shp"
clipFeature = Base + "\\rec_park.shp"
outFeatureClass = gdb + "\Roads"
arcpy.analysis.Clip(inFeature, clipFeature, outFeatureClass)

inFeature = Base+"\\river.shp"
clipFeature = Base + "\\rec_park.shp"
outFeatureClass = gdb + "\Rivers"
arcpy.analysis.Clip(inFeature, clipFeature, outFeatureClass)
print("Successfully clipped roads and rivers by study area")
print("")

#Add Park Boundary into gdb
arcpy.conversion.FeatureClassToGeodatabase(Base+"\\rec_park", gdb)
print("Successfully added park boundary into geodatabase")
print("")

#Add LandCover into gdb
arcpy.conversion.RasterToGeodatabase(landCover+"\\landcov", gdb)
print("Successfully added landcover into geodatabase")
print("")

#Add NTS50 into gdb
NTS50 = arcpy.SelectLayerByLocation_management(ws+"\\NTS\\NTS-50\\NTS50.shp", "INTERSECT", Base+"\\rec_park.shp")
arcpy.CopyFeatures_management(NTS50, gdb+"\\NTS50")
print("Successfully added NTS50(covering the park) into geodatabase")
print("")



#Remove intermediate data
List=["costDist", "costSurface","DEM_Mosaic", "DEM_Mosaic_Proj","outbklink","recl_LandCover","recl_River","recl_Roads","recl_Slope","river_eu","roads_eu"]
for list in List:
    arcpy.management.Delete(list)

print("Completely removed intermediate data")
print("")

#List and Descirbes All Final features, rasters, and tables
print("[List Final Features]")
fcs = arcpy.ListFeatureClasses("*")
for fc in fcs:
    desc = arcpy.Describe(fc)
    print("Name: " + desc.Name)
    print("Geometry: " + desc.shapeType)
    print("Spatial Reference: " + desc.spatialReference.name)
    print("")

print("[List Final raster datasets]")
rasterList = arcpy.ListRasters("*")
for raster in rasterList:
    desc = arcpy.Describe(raster)
    print("Name: " + desc.Name)
    print("Cell Size: " + str(desc.meanCellWidth))
    print("Coordinate System: " +desc.spatialReference.name)
    print("")

#Average elevation of the Provincial Park
zonalStats = arcpy.sa.ZonalStatisticsAsTable("rec_park", "Name", "DEM", "zonalStats", "", "MEAN")
Scursor = arcpy.da.SearchCursor(zonalStats, ["MEAN"])
for row in Scursor:
    print("Average Elevation : %.2f m" % row[0])
    print("")
#Average Slope of the Provincial Park
zonalStats = arcpy.sa.ZonalStatisticsAsTable("rec_park", "Name", "Slope", "zonalStats1", "", "MEAN")
Scursor = arcpy.da.SearchCursor(zonalStats, ["MEAN"])
for row in Scursor:
    print("Mean Slope in Degrees: %.4f degrees" % row[0])
    print("")

#The area of each landcover Type within the park boundary
print("Calculate area of each landcover type ")
desc = arcpy.Describe("landcov")
cellheight = desc.meanCellHeight
cellwidth = desc.meanCellWidth
Scursor = arcpy.da.SearchCursor("landcov", ["VALUE", "COUNT"])
for row in Scursor:
    area = int(row[1] * cellheight * cellwidth)
    print("Value: "+ str(row[0]))
    print("Area: %.2f m2" % area)
print("")

#Length of pipeline using geometry token
scursor = arcpy.da.SearchCursor("PipelineRoute",["SHAPE@LENGTH"])
for row in scursor:
    print("Length of Pipeline: "+ str(row[0]))
    print("")
#Identify 1:50,000 NTS map
print("Identify NTS Sheets")
SCursor = arcpy.da.SearchCursor(NTS50, ["NAME"])
for row in SCursor:
    print("NTS Sheets Name: "+row[0])
print("")
print(arcpy.GetMessages())

#check out the spatial extension
arcpy.CheckInExtension("Spatial")
print("Checked in the spatial extension")
print("")





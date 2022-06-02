# Create_GeopackageSoilRaster0.py
#
# 2021-04-22

# Convert geopackage mupolygon to a geopackage raster
#
# ArcGIS Pro 2.7 which uses Python library: sqlite3 version 2.6;  GDAL version 2030366
#
# This version of the script will successfully create a 32-bit integer TIFF file with mukey values. Very painful.
#
# To do: create RAT (.dbf) and create geopackage raster that can be joined to SDV_ attribute tables.
# Currently in the RAT, Value is mukey equivalent.
#
# To do: research compression options for the 32 bit unigned integer raster.
# I found that compression options can be applied at two different stages:
#    Create() and Translate()
#    Done. I was able to create a 32-bit unsigned integer GeoTIFF.
#
# This version of the script now will create an attribute table and statistics as part of the aux.xml file.
# Still needs raster cell COUNT added to the table. At this point I'm not sure how to get that information
# from the histogram
#
# GDAL Drivers: https://gdal.org/drivers/raster/index.html#raster-drivers
# GTiff driver: https://gdal.org/drivers/raster/gtiff.html#raster-gtiff
#
#
# At this point I do not know much about the geopackage raster. It appears that there is
# a significant blocker in that the current spec does not appear to allow the 32-bit unsigned
# integer datatype needed to store mukey values.

# Still have issues with the GeoTIFF I am generating. The Identify Tool in Pro does not return any values.
# I noticed that if I use ArcGIS ProjectRaster tool, the output TIFF does work properly. Need to
# compare the inputs and outputs to see what the difference is. It may simply be due to the fact
# that the input used a join to the tif.vat.dpg and in the output there is no join.
#
# Do I need to look at the properties of the input soil polygon layer to capture
# potential selected sets or whereclauses and pass those on to the OGR layer?
#
# Don't forget metadata for the raster. As a TIFF, the metadata is in an xml file (same filename as TIFF)
#
# For future reference; NASS documents that CropScape uses EPSG:5070 (CONUS Albers) for the CDL native projection.
# https://www.nass.usda.gov/Research_and_Science/Cropland/sarsfaqs2.php#Section2_5.0
#
# Rasterlite references for Spatialite database:
# 1. https://grasswiki.osgeo.org/wiki/SpatiaLite
# 2. https://gdal.org/drivers/raster/rasterlite.html
# 
#
## Below is an example of using an 'adapter' to convert Python datatype to a sqlite datatype.
## There are both sqlite3.register_converter and sqlite3.register_adapter methods available.
## https://docs.python.org/3/library/sqlite3.html#using-adapters-to-store-additional-python-types-in-sqlite-databases
## import sqlite3
## import datetime
## import time
##
## def adapt_datetime(ts):
##     return time.mktime(ts.timetuple())
##
## sqlite3.register_adapter(datetime.datetime, adapt_datetime)
##
## con = sqlite3.connect(":memory:")
## cur = con.cursor()
##
## now = datetime.datetime.now()
## cur.execute("select ?", (now,))
## print(cur.fetchone()[0])
##
## con.close()

#
# Steve Peaslee, National Soil Survey Center, Lincoln, Nebraska
#
## ===================================================================================
class MyError(Exception):
    # Custom error

    def __init__(self, *args):

        if args:
            self.message = args[0]

        else:
            self.message = None

    def __str__(self):

        if self.message:
            return self.message
            #return 'Message passed through MyError: {0}'.format(self.message)

        else:
            return 'MyError has been raised'

## ===================================================================================
def MyWarning(msg):
    # If I use sys.exit(1), the script will drop down to the exception clause where usually errorMsg is called.
    # Do I need to clear the traceback when MyError is called?
    PrintMsg(msg, 1)
    return

## ===================================================================================
def errorMsg(excInfo):
    # Capture system error from traceback and then exit
    # Should I be passing in the value for sys.exc_info()?
    try:
        # sys.tracebacklimit = 1

        # excInfo object is a tuple that should contain 3 values
        # 0: type gets the type of the exception being handled (a subclass of BaseException)
        # 1: value gets the exception instance (an instance of the exception type)
        # 2: traceback gets a traceback object which encapsulates the call stack at the point where the exception originally occurred

        if not excInfo is None:

            PrintMsg(70 * "=", 2)
            exc_type, exc_value, exc_tb = sys.exc_info()

            for tb_info in traceback.extract_tb(exc_tb):
                filename, linenum, funcname, source = tb_info
                errInfo = str(sys.exc_info()[1])

                if funcname != '<module>':
                    funcname = funcname + '()'

                if source.strip().startswith("raise MyError"):
                    # raised error
                    PrintMsg(errInfo + " (function " + sys._getframe().f_code.co_name + ")", 2)

                else:
                    # arcpy.Execute error
                    PrintMsg("Error '" + errInfo + "' in " + os.path.basename(filename) + \
                         " at line number " + str(linenum) + ":" + "\n" + source, 2)

            PrintMsg(70 * "=", 2)

            return

    except MyError as e:
        PrintMsg(str(e), 2)

    except:
        errorMsg(sys.exc_info())

## ===================================================================================

def PrintMsg(msg, severity=0):
    # Adds tool message to the geoprocessor
    #
    #Split the message on \n first, so that if it's multiple lines, a GPMessage will be added for each line
    try:
        for string in msg.split('\n'):
            #Add a geoprocessing message (in case this is run as a tool)
            if severity == 0:
                arcpy.AddMessage(string)

            elif severity == 1:
                arcpy.AddWarning(string)

            elif severity == 2:
                arcpy.AddError(" \n" + string)

    except MyError as e:
        PrintMsg(str(e), 2)
        return False

    except:
        errorMsg(sys.exc_info())
        return False

## ===================================================================================
def Number_Format(num, places=0, bCommas=True):
    try:
    # Format a number according to locality and given places
        locale.setlocale(locale.LC_ALL, "")
        if bCommas:
            theNumber = locale.format("%.*f", (places, num), True)

        else:
            theNumber = locale.format("%.*f", (places, num), False)

        return theNumber

    except MyError as e:
        PrintMsg(str(e), 2)
        return "???"

    except:
        errorMsg(sys.exc_info())
        return "???"


## ===================================================================================
def elapsedTime(start):
    # Calculate amount of time since "start" and return time string

    #
    # Usage:
    #    start = time.time()   # start clock to measure total processing time
    #    Do stuff...
    #    theMsg = " \nProcessing time for " + outputRaster + ": " + elapsedTime(start) + " \n "
    #    PrintMsg(theMsg, 0)

    try:
        # Stop timer
        #
        end = time.time()

        # Calculate total elapsed seconds
        eTotal = end - start

        # day = 86400 seconds
        # hour = 3600 seconds
        # minute = 60 seconds

        eMsg = ""

        # calculate elapsed days
        eDay1 = eTotal / 86400
        eDay2 = math.modf(eDay1)
        eDay = int(eDay2[1])
        eDayR = eDay2[0]

        if eDay > 1:
          eMsg = eMsg + str(eDay) + " days "
        elif eDay == 1:
          eMsg = eMsg + str(eDay) + " day "

        # Calculated elapsed hours
        eHour1 = eDayR * 24
        eHour2 = math.modf(eHour1)
        eHour = int(eHour2[1])
        eHourR = eHour2[0]

        if eDay > 0 or eHour > 0:
            if eHour > 1:
                eMsg = eMsg + str(eHour) + " hours "
            else:
                eMsg = eMsg + str(eHour) + " hour "

        # Calculate elapsed minutes
        eMinute1 = eHourR * 60
        eMinute2 = math.modf(eMinute1)
        eMinute = int(eMinute2[1])
        eMinuteR = eMinute2[0]

        if eDay > 0 or eHour > 0 or eMinute > 0:
            if eMinute > 1:
                eMsg = eMsg + str(eMinute) + " minutes "
            else:
                eMsg = eMsg + str(eMinute) + " minute "

        # Calculate elapsed secons
        eSeconds = "%.1f" % (eMinuteR * 60)

        if eSeconds == "1.00":
            eMsg = eMsg + eSeconds + " second "
        else:
            eMsg = eMsg + eSeconds + " seconds "

        return eMsg

    except:
        errorMsg()
        return ""

## ===================================================================================
def SetScratch():
    # try to set scratchWorkspace and scratchGDB if null
    #        SYSTEMDRIVE
    #        APPDATA C:\Users\adolfo.diaz\AppData\Roaming
    #        USERPROFILE C:\Users\adolfo.diaz
    try:
        #envVariables = os.environ

        #for var, val in envVariables.items():
        #    PrintMsg("\t" + str(var) + ": " + str(val), 1)

        if env.scratchWorkspace is None:
            #PrintMsg("\tWarning. Scratchworkspace has not been set for the geoprocessing environment", 1)
            env.scratchWorkspace = env.scratchFolder
            #PrintMsg("\nThe scratch geodatabase has been set to: " + str(env.scratchGDB), 1)

        elif str(env.scratchWorkspace).lower().endswith("default.gdb"):
            #PrintMsg("\tChanging scratch geodatabase from Default.gdb", 1)
            env.scratchWorkspace = env.scratchFolder
            #PrintMsg("\tTo: " + str(env.scratchGDB), 1)

        #else:
        #    PrintMsg(" \nOriginal Scratch Geodatabase is OK: " + env.scratchGDB, 1)

        if env.scratchGDB:
            return True

        else:
            return False

    except MyError as e:
        PrintMsg(str(e), 2)
        return False

    except:
        errorMsg(sys.exc_info())
        return False

## ===================================================================================
def GetTableList(newDB, conn, liteCur):
    # Query sqlite database and return a list of tables
    #
    try:
        tblList = list()

        queryListTables = "SELECT name FROM sqlite_master WHERE type = 'table' AND NOT name LIKE 'gpkg%' AND NOT name LIKE 'rtree%'; "

        liteCur.execute(queryListTables)

        rows = liteCur.fetchall()

        tableNames = [row[0] for row in rows]

        #PrintMsg("\n".join(tableNames), 0)

        return tableNames

    except MyError as e:
        PrintMsg(str(e), 2)
        return []

    except:
        errorMsg(sys.exc_info())
        return []

## ===================================================================================
def GetAttributes(newDB, fcName, fieldName):
    # Get a distinct list of attributes from the mapunit table
    # Probably should look at getting mukeys from the soilLayer as well.
    #
    # Do I need to worry about already having an ogr connection to the same db?
    try:
        import sqlite3
        conn = sqlite3.connect(newDB)
        liteCur = conn.cursor()
        queryAttributes = "SELECT DISTINCT " + fieldName + " FROM " + fcName
        liteCur.execute(queryAttributes)
        rows = liteCur.fetchall()
        attList = [row[0] for row in rows]
        del liteCur, conn, rows

        PrintMsg(".\tFound " + Number_Format(len(attList), 0, True) + " values for '" + fieldName  + "', ", 0)
        #PrintMsg(".\tincluding: " + str(attList[0]) + ", " + str(attList[1]), 0)

        return attList

    except:
        errorMsg(sys.exc_info())
        return []

## ===================================================================================
def CompactDatabase(newDB):
    # Query sqlite database and return a list of tables
    #
    # I need to check filesize of database and make sure there is adequate diskspace before
    # executing VACUUM. conus db before vac: 178.392500 GB and after vac: 171.5 GB
    # fileSizeMB = (os.stat(newDB).st_size / (1024.0 * 1024.0))
    # Having some problems getting disk free space with shutil.disk_usage(path)
    # Need to triple quote path and use \\
    # shutil.disk_usage(path) returns a tuple: (total, used, free) in bytes
    # To change the temp directory, use either TMPDIR setting or for
    # For older verions of sqlite3 library use: PRAGMA temp_store_directory = 'directory-name';

    # Looks like most of the TEMP space will be reclaimed after the VACUUM is complete.
    #
    try:
        arcpy.SetProgressorLabel("Compacting new database...")
        PrintMsg("Compacting new database...")

        dbSize = (os.stat(newDB).st_size / (1024.0 * 1024.0))  # units are MB
        tmpFolder = os.environ["TEMP"]

        t, u, f = shutil.disk_usage(tmpFolder)
        tmpFree = f / (1024.0 * 1024.0)         # how much space is currently available on the file system for TEMP
        minimumFree = t / (1024.0 * 1024.0 * 10.0)     # minimum amount of free space we should allow is 10% of the total disk space.

        PrintMsg(".\tDatabase size before:\t" + Number_Format(dbSize, 0, True) + " MB", 0)
        PrintMsg(".\tFree temp space: " + Number_Format(tmpFree, 0, True) + " MB", 0)

        requiredSpace = 2.0 * dbSize    # amount of potential disk space that might be used by VACUUM.
        PrintMsg(".\tMinimum free disk space required: " + Number_Format(requiredSpace, 0, True) + " MB", 0)

        # if requiredSpace > minimumFree:
        if requiredSpace > tmpFree:
            PrintMsg(".\t", 0)
            PrintMsg(".\tUsing TEMP folder (" + tmpFolder + ") ...", 1)
            raise MyError("Compacting the new database will require more temp space than is currently available: " + Number_Format(requiredSpace, 0, True))


        conn = sqlite3.connect(newDB)
        conn.execute("VACUUM;")
        conn.close()

        del conn
        dbSize = (os.stat(newDB).st_size / (1024.0 * 1024.0))  # units are MB
        PrintMsg(".\tDatabase size after:\t" + Number_Format(dbSize, 0, True) + " MB", 0)
        PrintMsg(".\tFinished compacting database...")

        return True

    except MyError as e:
        PrintMsg(str(e), 2)
        return False

    except:
        errorMsg(sys.exc_info())
        return False

## ===================================================================================
def GetFieldInfo(tblName, liteCur):
    # Get list of (fieldname, type) for this table
    try:
        fldNames = list()

        queryFieldNames = "SELECT name, type FROM PRAGMA_TABLE_INFO('" + tblName + "');"
        liteCur.execute(queryFieldNames)
        rows = liteCur.fetchall()
        fldInfo= [row for row in rows]

        #for fld in fldInfo:
        #    fldName = fld[0]
        #    PrintMsg(tblName + ":\t" + fldName, 0)

        return fldInfo

    except:
        errorMsg(sys.exc_info())
        return []

## ===================================================================================
def GetNewExtentsGpkg(newDB, layerList, conn, liteCur):
    # For geopackage (.gpkg) database only.
    # Might be able to adapt this to calculating new raster extents, etc.
    #
    # Use OGR to get extents for each spatial layer in the new database
    # Return information as a dictionary,
    # where key = layer name; value = tuple of extents (MinX, MinY, MaxX, MaxY)

    # For some reason this isn't working for Geopackage. Possible file lock?

    try:
        #from osgeo import ogr
        arcpy.SetProgressorLabel("Registering spatial extents...")
        #PrintMsg(".\tUsing osgeo.ogr to get spatial extents", 0)

        spatialExtents = list()
        driver = ogr.GetDriverByName("GPKG")

        if driver is None:
            err = "Failed to get OGR inputDriver for " + newDB
            raise MyError(err)

        gdal.SetConfigOption('OGR_GPKG_FOREIGN_KEY_CHECK', 'NO')
        ds = driver.Open(newDB, 0)

        if ds is None:
            err = "Failed to open " + newDB + " using ogr with " + driver.name + " driver"
            raise MyError(err)

        # Try getting extent from sapolygon first
        layer = ds.GetLayer("sapolygon")

        featCnt = layer.GetFeatureCount()
        min_x, max_x, min_y, max_y = layer.GetExtent()

        spatialExtents = list()
        #featCnt = saCounts[0]      # sapolygon feature count
        #vals = saExtents[0]   #
        #min_x, max_x, min_y, max_y = saExtents

        for layerName in layerList:
            layer = ds.GetLayer(layerName)

            if layer is None:
               err = "Failed to find " + layerName + " table using ogr"
               raise MyError(err)

            #featCnt = saCounts[i]
            featCnt = layer.GetFeatureCount()

            if featCnt > 0:
                # Cheating a little by setting extents for all layers (with data) to same as sapolygon
                spatialExtents.append([min_x, min_y, max_x, max_y, layerName])

            else:
                # See if geopackage will accept zeros for the extent?
                # Currently I am assigning the extent values from sapolygon layer
                #vals = [0, 0, 0, 0, layerName]
                #PrintMsg(".\tSpatial extent for " + layerName + ": " + str(vals), 1)
                spatialExtents.append([0, 0, 0, 0, layerName])

            del layer

        del ds
        del driver

        # If this is a geopackage, use sqlite3 to update gpkg_contents with the spatial extents

        if len(spatialExtents) > 0:
            # ["sapolygon", "mupolygon", "muline", "mupoint", "featline", "featpoint"]
            PrintMsg(".\tRegistering spatial layers to the database", 0)

            # Update existing records
            sqlUpdate = "UPDATE gpkg_contents SET min_x=?, min_y=?, max_x=?, max_y=? WHERE table_name=?"
            liteCur.executemany(sqlUpdate, spatialExtents)

            conn.commit()
            #conn.close()
            #del liteCur, conn

            return True

        else:
            PrintMsg(".\tFailed to update extents for spatial layers", 0)
            return False

    except MyError as e:
        PrintMsg(str(e), 2)
        return False

    except:
        errorMsg(sys.exc_info())
        return False

## ===================================================================================
def CalcRasterExtent(soilLayer, xRes, yRes):
    # Calculate raster extents along with the number of columns
    #
    # Snap raster functionality to be developed...
    # NLCD CONUS Corner Coordinates (center of pixel, projection meters)
    # Upper Left Corner: -2493045 meters(X), 3310005 meters(Y)
    # Lower Right Corner: 2342655 meters(X), 177285 meters(Y)
    #
    try:
        # Get extent of the soil polygon layer
        xMin, xMax, yMin, yMax = soilLayer.GetExtent()
        soilSRS = soilLayer.GetSpatialRef()


        #PrintMsg(".\tSoil Polygon Layer Extent:\t" + str(xMin) + ", " + str(yMin) + "; " + str(xMax) + ", " + str(yMax), 0)
        #soilSRS = osr.SpatialReference()
        #soilSRS.ImportFromEPSG(4326)       # temporary solution. Assuming input coordinate system is WGS 1984
        #PrintMsg("Value of soilSRS:\t" + str(soilSRS), 0)

        # Calculate the NW coordinates rounded up to the nearest xRes, yRes
        # Please note, for geographic coordinates I need to round up the westing
        a = round(((xMin - xRes) / xRes), 0) * xRes
        #PrintMsg(".\txMin " + str(xMin) + " becomes " + str(a), 0)

        b = round(((yMax + yRes) / yRes), 0) * yRes
        #PrintMsg(".\tyMax " + str(yMax) + " becomes " + str(b), 0)

        c = round(((xMax + xRes) / xRes), 0) * xRes
        #PrintMsg(".\txMax " + str(xMax) + " becomes " + str(c), 0)

        d = round(((yMin - yRes) / xRes), 0) * xRes
        #PrintMsg(".\tyMin " + str(yMin) + " becomes " + str(d), 0)

        layerWidth = c - a
        layerHeight = b - d

        # Calculate columns and rows based upon xRes and yRes
        layerColumns = int(layerWidth // xRes)
        layerColM = layerWidth % xRes

        if layerColM > 0:
            layerColumns += 1

        layerRows = int(layerHeight // yRes)
        layerRowM = layerHeight % yRes

        if layerRowM > 0:
            layerRows += 1

        geoTransform = [a, xRes, 0, b, 0, (-1.0 * yRes)]

        # Geotransformation object is a list with the following format.
        # We are assuming in all of this that the output raster will have the same
        # coordinate system as the input soil polygons.
        #
        # geotransform[0] = top left x
        # geotransform[1] = X pixel resolution
        # geotransform[2] = 0
        # geotransform[3] = top left y
        # geotransform[4] = 0
        # geotransform[5] = Y pixel resolution (negative value)

        layerDimensions = (layerColumns, layerRows, geoTransform)
        #PrintMsg(".\tlayerDimensions object: " + str(layerDimensions), 0)

        return layerDimensions

    except MyError as e:
        PrintMsg(str(e), 2)
        return []

    except:
        errorMsg(sys.exc_info())
        return []


## ===================================================================================
def AddRAT(rasterBand, rasterDimension, attributeValues, valueCount, geoTransform, newDB, newDBF):
    # Add raster attribute table (RAT) to new map unit raster
    # Start with making it work with a GeoTIFF.
    # Now trying to build a DBF and mukey index to make it ArcGIS friendly
    #
    # Rasterband properties:
    #     ds = rasterBand.GetDataset()
    #     source files: ds.GetFileList()  # should return .tif filepath and .tif.aux.xml filepath. Any others not recognized.

    try:
        ## ComputeStatistics
        ## bApproxOK	If TRUE statistics may be computed based on overviews or a subset of all tiles.
        ## pdfMin	Location into which to load image minimum (may be NULL).
        ## pdfMax	Location into which to load image maximum (may be NULL).-
        ## pdfMean	Location into which to load image mean (may be NULL).
        ## pdfStdDev	Location into which to load image standard deviation (may be NULL).
        ## pfnProgress	a function to call to report progress, or NULL.
        ## pProgressData	application data to pass to the progress function.

        # This appears to calculate the internal statistics, not the xml file.
        # Found this reference for xml: gdalinfo test.tif -stats --config GDAL_PAM_ENABLED TRUE
        # See if there is python way to set this option.
        #

        # Attempt to enable creation of the statistics XML file
        # os.environ['GDAL_PAM_ENABLED'] = 'YES' # this did not seem to work with the python gdal library
        start = time.time()   # start clock to measure total processing time

        PrintMsg("Running ComputeStatistics", 0)
        PrintMsg("Need to find out if there is a default skip setting being used", 0)
        (newmin, newmax, newmean, newstdv) = rasterBand.ComputeStatistics(0)

        PrintMsg(".\tNew statistics: " + str((newmin, newmax, newmean, newstdv)), 0)
        PrintMsg(".\tMin value: " + str(newmin), 0)
        PrintMsg(".\tMax value: " + str(newmax), 0)
        PrintMsg(".\tMean value: " + str(newmean), 0)
        PrintMsg(".\tStd deviation: " + str(newstdv), 0)
        rasterBand.SetStatistics(newmin, newmax, newmean, newstdv)
        time.sleep(1)
        rasterBand.FlushCache()
        time.sleep(1)

        numColumns, numRows = rasterDimension

        # Read raster band values and counts into a numpy array and then conver
        # to lists. Use these lists to populate raster attribute tables
        #
        # Error 'Unable to allocate 52.2 GiB for an array with shape (14010896400,)
        # and data type uint32' in Create_GeopackageSoilRaster0.py at line number 651:
        #
        # values, counts = np.unique(rasterBand.ReadAsArray(), return_counts=True)  # works for smaller rasters
        #
        # ma.masked_equal allows me to skip processing the NoData cells
        # rasterData = np.ma.masked_equal(rasterBand.ReadAsArray(), 0)  # Try excluding NoData to see if that helps with memory usage.
        #
        PrintMsg(".\tCreating dictionary using mukey values...")
        dCounts = dict()

        # Create 10 subsets of the raster array and save results of each to a dictionary
        # rasterSubsets = np.array_split(np.ma.masked_equal(rasterBand.ReadAsArray(), 0), 25)

        # Another attempt to get cell counts...
        dType = rasterBand.DataType
        #pyType = str(type(rasterBand))
        #PrintMsg(".\tRaster band is a python data type of: " + pyType, 0)

        #rasterMasked = np.ma.masked_equal(rasterBand.ReadAsArray(), 0)  # masking changes cell values to "--"
        # rasterArray = rasterBand.ReadAsArray() # still too much memory for TX. Try ReadRaster instead of ReadAsArray.

        # An 2-dimension array has a shape property: number of (rows, columns)
        #PrintMsg(".\tMasked raster shape: " + str(rasterMasked.shape) + "; number of dimensions:" + str(rasterMasked.ndim), 0)
        #PrintMsg(".\tRaster array shape (rows: " + str(rasterArray.shape[0]) + ", columns: " + str(rasterArray.shape[1]) + "): " + "; " + str(rasterArray.ndim) + " dimensional" , 0)

        PrintMsg(".\tGetting cell counts for " + str(len(attributeValues)) + " map units...", 0)

        for val in attributeValues:
            dCounts[val] = 0

        noData = rasterBand.GetNoDataValue()

        for rowNum in range(numRows):

            # processing 2-dimensional array one row at a time
            valueBytes = rasterBand.ReadRaster(0, rowNum, numColumns, 1, numColumns, 1, dType)
            valueArray = np.array(struct.unpack('I' * numColumns, valueBytes))
            # PrintMsg(".\tvalueArray has " + str(valueArray.shape) + " rows, columns", 0)

            # Tracking cell counts one cell at a time
            cellValues, counts = np.unique(valueArray, return_counts=True)

            for i, cellVal in enumerate(cellValues):
            #    #PrintMsg(".\t" + str(cellVal) + ":\t" + str(counts[i]), 0)

                if cellVal != noData:
                    #if cellVal in dCounts:
                    dCounts[cellVal] += counts[i]

        PrintMsg(".", 0)
        PrintMsg(".\tGot cell counts for " + str(len(attributeValues)) + " map units", 0)

        PrintMsg(".", 0)
        PrintMsg(".\tBuilding raster attribute table...", 0)

        # Create aux.xml raster attribute table. ArcGIS can read this, but joins don't seem to work
        rat = gdal.RasterAttributeTable()

        rat.CreateColumn('VALUE', gdal.GFT_Integer, gdal.GFU_Generic) # GFU_Integer or gdal.GDT_UInt32
        rat.CreateColumn('Count', gdal.GFT_Integer, gdal.GFU_Generic)
        rat.CreateColumn('mukey', gdal.GFT_Integer, gdal.GFU_Generic)

        # End of aux.xml RAT

        ratName = "raster_vat"
        outputRAT = os.path.join(env.scratchFolder, ratName)    # Output DBF dataset folder
        tmpDBF = os.path.join(outputRAT, ratName + ".dbf")

        if os.path.isdir(outputRAT):
            shutil.rmtree(outputRAT, ignore_errors=True)

        #PrintMsg(".\tPreparing container for new output raster (" + outputFile + ")", 0)
        rasDriver = gdal.GetDriverByName("GTiff")

        if rasDriver is None:
            raise MyError("Failed to get raster driver for creating new geotiff")

        # Create an ESRI-friendly DBaseIV table as an alternative RAT.
        #PrintMsg(".\tCreating shapefile or DBF for an alternate RAT", 0)
        dbfDriver = ogr.GetDriverByName("ESRI Shapefile")

        outputRAT = os.path.join(env.scratchFolder, ratName)
        ratDS = dbfDriver.CreateDataSource(outputRAT)
        ratLayer = ratDS.CreateLayer(ratName, geom_type=ogr.wkbNone)

        valueField = ogr.FieldDefn("value", ogr.OFTInteger64)
        ratLayer.CreateField(valueField)
        countField = ogr.FieldDefn("count", ogr.OFTInteger)
        ratLayer.CreateField(countField)
        mukeyField = ogr.FieldDefn("mukey", ogr.OFTInteger64)
        ratLayer.CreateField(mukeyField)
        #PrintMsg(".\tFinished creating shapefile or DBF for an alternate RAT", 0)
        ratDef = ratLayer.GetLayerDefn()
        # End of .dbf

        # Write both attribute tables (.tif.aux.xml and .dbf)
        for i, val in enumerate(dCounts.keys()):

            # if val != '--':
            # populate gdal RAT
            cnt = int(dCounts[val])
            #PrintMsg(".\t" + str(i) + ". Raster cell value: '" + str(val) + "'", 0)
            rat.SetValueAsInt(i, 0, int(val))
            rat.SetValueAsInt(i, 1, cnt)
            rat.SetValueAsInt(i, 2, int(val))

            # populate DBF for ArcGIS
            newFeature = ogr.Feature(ratDef)
            newFeature.SetField("Value", int(val))
            newFeature.SetField("count", cnt)
            newFeature.SetField("mukey", int(val))
            ratLayer.CreateFeature(newFeature)

        # Associate with the band. Not sure if this is working
        rasterBand.SetDefaultRAT(rat)

        rasterBand = None
        #ratLayer = None

        # Rename output DBF. Problem with new copy.
        if os.path.isfile(tmpDBF):
            newDS = dbfDriver.CopyDataSource(ratDS, newDBF)

        newCPG = newDBF.replace(".dbf", ".cpg")

        with open(newCPG, "w") as fh:
            fh.write("UTF-8")

        newCPG = None
        newDBF = None
        ratLayer = None
        ratDS = None

        ## Seems like the pyramids or overviews do not have a standard. Best to build them in your GIS.
        ## rasterBand.BuildOverViews
        ## pszResampling	one of "NEAREST", "GAUSS", "CUBIC", "AVERAGE", "MODE", "AVERAGE_MAGPHASE" "RMS" or "NONE" controlling the downsampling method applied.
        ## nOverviews	number of overviews to build.
        ## panOverviewList	the list of overview decimation factors to build.
        ## pfnProgress	a function to call to report progress, or NULL.
        ## pProgressData	application data to pass to the progress function.

        theMsg = ".\tTime to build raster attribute tables: " + elapsedTime(start)
        PrintMsg(theMsg, 0)

        return True

    except MyError as e:
        PrintMsg(str(e), 2)
        return False

    except:
        errorMsg(sys.exc_info())
        return False

## ===================================================================================
def ModifyAuxillaryFiles(rasterFN, geoTransform, rasterStatistics):
    # Given a list of SSURGO downloads, sort through all of the soilsa_a*.shp files,
    # sorting extents from upper-left down to lower-right. This will become the order
    # that the shapefiles are imported into the SQLite database tables. Also need
    # to save the overall extent of the new spatial layer. Should I calculate it here
    # in this function or can I get it after the data are all imported?

    try:
        # Try reading the .tif.aux.xml file here

        #rasterDS = rasterBand.GetDataset()
        #rasterFiles = finalRaster.GetFileList()
        #rasterFN = rasterFiles[0]
        #PrintMsg(".\tNew raster:\t" + rasterFN, 0)
        rasterAUX = rasterFN + ".aux.xml"
        newmin, newmax, newmean, newstdv = rasterStatistics

        # The RAT information doesn't actually get written to the .tif.aux.xml file
        # until the raster objects are set to None. Do I need to do this in main()????
        #time.sleep(8)


        if os.path.isfile(rasterAUX):

            PrintMsg(".\t\tAux file:\t" + rasterAUX, 0)

            auxRows = []

            if os.path.isfile(rasterAUX):
                # Open aux.xml file and read it into a list
                with open(rasterAUX, 'r') as fh:
                    auxRows = fh.readlines()

            #for row in auxRows:
            #    PrintMsg(".\t\t" + row, 0)

            # Create tif.aux.xml records for ArcGIS compatibility
            # First line in tif.aux.xml should be '<PAMDataset>'. Skip this line and then insert
            # Between second and third line insert all records in esriMD list.

            # Create a temporary txt file to act as replacement .tif.aux.xml
            tmpAUX = rasterAUX.replace(".xml", ".txt")

            esriMD = list()
            esriMD.append('  <Metadata>')
            esriMD.append('    <MDI key="DataType">Generic</MDI>')
            esriMD.append('  <Metadata>')
            esriMD.append('  <Metadata domain="Esri">')
            esriMD.append('    <MDI key="PyramidResamplingType">NEAREST</MDI>')
            esriMD.append('  </Metadata>')
            esriMD.append('    <MDI key="Source">' + os.path.basename(newDB) + '</MDI>')
            esriMD.append('  </Metadata>')
            esriMD.append('  <PAMRasterBand band="1">')
            esriMD.append('    <Metadata>')
            esriMD.append('      <MDI key="RepresentationType">THEMATIC</MDI>')
            esriMD.append('      <MDI key="STATISTICS_EXCLUDEDVALUES"></MDI>')
            esriMD.append('      <MDI key="STATISTICS_MAXIMUM">' + str(newmax) + '</MDI>')
            esriMD.append('      <MDI key="STATISTICS_MEAN">' + str(newmean) + '</MDI>')
            esriMD.append('      <MDI key="STATISTICS_MINIMUM">' + str(newmean) + '</MDI>')
            esriMD.append('      <MDI key="STATISTICS_SKIPFACTORX">1</MDI>')
            esriMD.append('      <MDI key="STATISTICS_SKIPFACTORY">1</MDI>')
            esriMD.append('      <MDI key="STATISTICS_STDDEV">' + str(newstdv) + '</MDI>')
            esriMD.append('    <Metadata>')


            # Open temporary tif.aux.xml file and write both the original data plus that from esriMD
            with open(tmpAUX, 'w') as fh:
                firstLine = auxRows.pop(0)   # <PAMDataset>

                fh.write(firstLine)

                for md in esriMD:
                    fh.write(md + "\n")

                for row in auxRows:
                    fh.write(row)

            del auxRows

            PrintMsg(".\tFinished writing metadata and attributes to " + tmpAUX, 0)

        # Indexes needed to write information in geoTransform list to the '.tfw' file

        worldFile = rasterFN.replace(".tif", ".tfw")
        PrintMsg(".\tWriting world file for ArcGIS as " + worldFile, 0)
        tfwOrder = [1, 2, 4, 5, 0, 3]

        with open(worldFile, 'w') as fh:
            for indx in tfwOrder:
                val = str(geoTransform[indx]) + "\n"
                #PrintMsg()
                fh.write(val)


        if os.path.isfile(tmpAUX):
            # rename original file
            backupAUX = rasterAUX.replace(".xml", ".bak")
            shutil.move(rasterAUX, backupAUX)

            if os.path.isfile(backupAUX):
                shutil.move(tmpAUX, rasterAUX)

            if os.path.isfile(rasterAUX):
                PrintMsg(".\tSwapped files successfully")
        # Information used to create '.tif.vat.cpg' file
        #cpg = "UTF-8"  # probably should find the actual encoding and return that instead. Not sure if this ever varies or what it is used for in an integer tif.

        return True

    except MyError as e:
        PrintMsg(str(e), 2)
        return False

    except:
        errorMsg(sys.exc_info())
        return False

## ===================================================================================
def main(newDB, inputLayer, newRasterFN, scriptFolder):
    # main function that handles the data processing.

    try:
        # import gdal and other libraries

##        # Get list of attribute values that will be used to generate the raster
##        # worked fieldName = "spatialver"
##        fieldName = "mukey"
##        attributeValues = str(GetAttributes(newDB, fieldName))
##        valueCount = len(attributeValues)

        # Set options for raster to polygon conversion
        rasterStorage = gdal.GDT_UInt32

        # Compression section. Uncompressed GeoTIFF was 769.7 MB.
        compressionOption = "compress=DEFLATE"  # Other options for GeoTIFF are LZW, DEFLATE, PACKBITS. Packbits was REALLY slow to compress.
        nodataOption = "nodata=np.nan"  # This didn't seem to work

        #PrintMsg(".\tUInt32 code: " + str(rasterStorage), 1)


        # Get source for inputLayer
        inputDesc = arcpy.Describe(inputLayer)
        inputFC = inputDesc.featureClass

        if inputFC.name.find(".") >= 0:
            fcName = inputFC.name.split(".")[1]

        else:
            fcName = inputFC.name
            
        # PrintMsg(".\tInput featureclass: " + inputFC.name, 0)

        if newDB.endswith(".gpkg"):
            driver = ogr.GetDriverByName("GPKG")
            soilDS = driver.Open(newDB)

        elif newDB.endswith(".sqlite"):
            driver = ogr.GetDriverByName("SQLite")
            soilDS = driver.Open(newDB)

        elif newDB.endswith(".gdb"):
            #driver = ogr.GetDriverByName("FileGDB")
            #soilDS = driver.Open(newDB, 0)
            soilDS = ogr.Open(newDB)

        
        #soilLayer = soilDS.GetLayer("mupolygon")  # main.mupolygon doesn't seem to work

        PrintMsg(".\tsoilLayer is derived from '" + fcName + "'", 0)
        soilLayer = soilDS.GetLayer(fcName)  # main.mupolygon doesn't seem to work

        # Get list of attribute values that will be used to generate the raster
        # worked fieldName = "spatialver"
        fieldName = "mukey"
        attributeValues = GetAttributes(newDB, inputFC.name, fieldName)
        valueCount = len(attributeValues)

        if len(attributeValues) == 0:
            raise MyError("Failed to get list of attribute values")

        #
        #soilSRS = osr.SpatialReference()
        #soilSRS.ImportFromEPSG(4326)
        csrString = str(soilLayer.GetSpatialRef())
        # PrintMsg(".\tcsrString: " + csrString, 0)
        soilSRS = osr.SpatialReference(csrString)
        srUnitName = soilSRS.GetLinearUnitsName()
        PrintMsg(".\tLinearUnit: " + str(srUnitName), 0)

        # These cell sizes are assuming geographic coordinate system (units: decimal degrees)
        #cellWidth = 0.0001
        #cellHeight = 0.0001

        if csrString.startswith("PROJCS"):
            # Assuming units are meters, need to add a check for this
            PrintMsg(".\tProjected CS", 0)
            cellWidth = 10.0
            cellHeight = 10.0

        elif csrString.startswith("GEOGCS"):
            # Assuming units are DD...
            PrintMsg(".\tGeographic CS", 0)
            cellWidth = 0.0001
            cellHeight = 0.0001

        columns, rows, geoTransform = CalcRasterExtent(soilLayer, cellWidth, cellHeight)
        cellCount = columns * rows

        start = time.time()   # start clock to measure total processing time


        # name of output raster and a hardcoded geotransformation coordinate and resolution

        outputFile = os.path.join(os.path.dirname(newDB), newRasterFN)  # Output raster (TIFF)

        if os.path.isfile(outputFile):
            os.remove(outputFile)

        PrintMsg(".\tPreparing container for new output raster:", 0)
        PrintMsg(".  \t" + outputFile, 0)
        rasDriver = gdal.GetDriverByName("GTiff")

        if rasDriver is None:
            raise MyError("Failed to get raster driver for creating new geotiff")

        # Create memory target raster
        # target_ds = gdal.GetDriverByName('MEM').Create('', xcount, ycount, 1, gdal.GDT_Byte)
        # target_ds.SetGeoTransform((
        #   xmin, pixelWidth, 0,
        #    ymax, 0, pixelHeight,
        # ))
        # NOTE compression option in Create! target_ds = gdal.GetDriverByName('GTiff').Create(Dir_Raster_end, x_res, y_res, 1, gdal.GDT_Float32, ['COMPRESS=LZW'])
        # works, but no compression: emptyRaster = rasDriver.Create(outputFile, xsize=columns, ysize=rows, bands=1, eType=gdal.GDT_UInt32)
        # Compression option in options list actually works.
        # gdal.SetConfigOption('COMPRESS_OVERVIEW', 'LZW') # another method to test with GDAL_PAM_ENABLED TRUE
        # LZW filesize (test_raster35.tif): 119.7MB ; DEFLATE test_raster37.tif: 27.8MB ; PACKBITS test_raster39.tif: 2,194 MB!!!!
        PrintMsg(".\tRaster will be created using '" + compressionOption + "' option", 0)

        emptyRaster = rasDriver.Create(outputFile, xsize=columns, ysize=rows, bands=1, eType=gdal.GDT_UInt32, options=[compressionOption, nodataOption])

        emptyRaster.SetProjection(soilSRS.ExportToWkt())

        emptyRaster.SetGeoTransform(geoTransform)

        PrintMsg(".\tConverting soil polygons to raster...", 0)
        # Pro commandline syntax for RasterizeLayer:
        # RasterizeLayer(Dataset dataset, int bands, Layer layer, void * pfnTransformer=None,
        # void * pTransformArg=None, int burn_values=0, char ** options=None,
        # GDALProgressFunc callback=0, void * callback_data=None) -> int

        #outputRaster = gdal.RasterizeLayer(emptyRaster, soilDS, options=rasterOptions)

        #outputRaster = gdal.RasterizeLayer(str(emptyRaster), 1, str(soilLayer), options=rasterOptions)
        #bands = [1]
        #optionList = {'format':'GTIFF', 'outputType':rasterStorage, 'outputSRS':'EPSG:4326', 'attribute':'mukey', 'width':columns, 'height':rows, 'targetAlignedPixels':True, 'allTouched':True}

        # worked optionList = ['format = GTIFF', 'outputType = 5', 'outputSRS = EPSG:4326', 'attribute = mukey', 'width = 4113', 'height = 1916', 'targetAlignedPixels = TRUE', 'allTouched = TRUE']
        # worked outputRaster = gdal.RasterizeLayer(emptyRaster, [1], soilLayer, options=optionList)
        # worked well, but no null, or compression: optionList = ['format=GTIFF', 'outputType=4', 'outputSRS=EPSG:4326', 'attribute=' + fieldName, 'initValues = ' + attributeValues, 'width=4113', 'height=1916', 'xRes=0.001', 'yRes=0.001', 'targetAlignedPixels=TRUE', 'allTouched=TRUE']

        # Here I'm trying to add compression using "compress=LZW'. Not sure if it actually is a RasterizeLayer option.
        # found this method for building options:
        # translateoptions = gdal.TranslateOptions(gdal.ParseCommandLine("-of Gtiff -co COMPRESS=LZW"))
        # gdal.Translate(gdaloutput, gdalinput, options=translateoptions)
        #optionList = ['format=GTIFF', 'outputType=4', 'outputSRS=EPSG:4326', 'attribute=' + fieldName, 'initValues = ' + str(attributeValues), 'width=4113', 'height=1916', 'xRes=0.001', 'yRes=0.001', 'targetAlignedPixels=TRUE', 'allTouched=TRUE']
        optionList = ['format=GTIFF', 'outputType=4', 'outputSRS=EPSG:4326', 'attribute=' + fieldName, 'width=4113', 'height=1916', 'xRes=0.001', 'yRes=0.001', 'targetAlignedPixels=TRUE', 'allTouched=TRUE']

        # Perform polygon to raster conversion
        bRaster = gdal.RasterizeLayer(emptyRaster, [1], soilLayer, options=optionList)

        if bRaster:
            PrintMsg(".\tbRaster = " + str(bRaster), 0)

        PrintMsg(".\tRaster dimensions: " + str(emptyRaster.RasterXSize) + " X " + str(emptyRaster.RasterYSize), 0)
        rasterDimension = (emptyRaster.RasterXSize, emptyRaster.RasterYSize)

        theMsg = ".\tTime for raster conversion: " + elapsedTime(start)
        PrintMsg(theMsg, 0)


        # ******************************************************************************************
        # Generate XML metadata
        # This method generates the XML file with histogram and statistics, but there are issues:
        # The approximate mode for histogram is set to YES, number of buckets is 256, statistics are not
        # included even though the Geotiff has stastistics calculated at this point.
        # keywords for infoOptions:
        # options=None, format='text', deserialize=True, computeMinMax=False,
        # reportHistograms=False, reportProj4=False, stats=False, approxStats=False,
        # computeChecksum=False, showGCPs=True, showMetadata=True, showRAT=True,
        # showColorTable=True, listMDD=False, showFileList=True, allMetadata=False,
        # extraMDDomains=None, wktFormat=None)
        #
        # infoOptions = gdal.InfoOptions()

        infoOptions = gdal.InfoOptions(reportHistograms=True, approxStats=False, computeMinMax=True, stats=True, allMetadata=True, showMetadata=True, showRAT=True)
        #infoOptions = gdal.InfoOptions(reportHistograms=True, approxStats=False, showMetadata=True, showRAT=True)


        #info = gdal.Info(outputFile, reportHistograms=True)
        # Lost my statistics, try turning off this command:
        info = gdal.Info(outputFile, options=infoOptions)

        # PrintMsg(".\tInfo: " + str(info), 0)
        # Generate XML metadata
        # ******************************************************************************************

        #PrintMsg(".\tSetting no data value before loading data", 0)
        rasterBand = emptyRaster.GetRasterBand(1)
        rasterBand.SetNoDataValue(0)


        PrintMsg(".\tNo Data Value: " + str(rasterBand.GetNoDataValue()), 0)
        dbf = outputFile + ".vat.dbf"




        if AddRAT(rasterBand, rasterDimension, attributeValues, valueCount, geoTransform, newDB, dbf):
            # Successfully created statistics, etc for the new raster

            # The gdal.Info was here
            PrintMsg(".", 0)
            PrintMsg("Output raster: " + outputFile, 0)

            # Make the auxillary files compatible with ArcGIS
            #newmin, newmax, newmean, newstdv = rasterBand.GetStatistics(0, 1)
            rasterStatistics = rasterBand.GetStatistics(0, 1)

            # Add pyramids or overviews
            # Needs more research. The following generated no errors but also no PYRAMIDs that I see.
##            PrintMsg(".\Building pyramids...")
##            gdal.SetConfigOption("COMPRESS_OVERVIEW", "DEFLATE")
##            emptyRaster.BuildOverviews("AVERAGE", [2,4,8,16,32,64, 128, 256])
##            PrintMsg(".\Finished building pyramids...")

            PrintMsg(".\tClearing references to raster object...", 0)
            time.sleep(5)
            rasterBand = None
            emptyRaster = None

            bModified = ModifyAuxillaryFiles(outputFile, geoTransform, rasterStatistics)

            # End of reading .tif.aux.xml file

            return True

        else:
            return False

    except MyError as e:
        PrintMsg(str(e), 2)
        return False

    except:
        errorMsg(sys.exc_info())
        return False

## ===================================================================================
def SpatialSort(inputFolder, ssaList):
    # Given a list of SSURGO downloads, sort through all of the soilsa_a*.shp files,
    # sorting extents from upper-left down to lower-right. This will become the order
    # that the shapefiles are imported into the SQLite database tables. Also need
    # to save the overall extent of the new spatial layer. Should I calculate it here
    # in this function or can I get it after the data are all imported?

    try:
        pass

    except MyError as e:
        PrintMsg(str(e), 2)

    except:
        errorMsg(sys.exc_info())

## ===================================================================================
## ===================================================================================

# Import system modules
import arcpy, sys, string, os, traceback, locale, time, datetime, shutil, struct

from osgeo import ogr
from osgeo import gdal
from osgeo import osr
from gdalconst import *
ogr.UseExceptions()
import numpy as np
from arcpy import env
#from operator import itemgetter, attrgetter

# import xml.etree.cElementTree as ET
#from xml.dom import minidom
#from arcpy import env
#import sqlite3  # I've added the sqlite3.dll to the script folder, but not sure it is working.Sometimes see 'not authorized' error.

#x = gdal.TranslateOptions()


try:
    if __name__ == "__main__":
        inputLayer = arcpy.GetParameterAsText(0)       # Input soil polygon layer (geopackage for now)
        newDB = arcpy.GetParameterAsText(1)            # Test to see if I can sort the ssaLayer when using the 'Create gSSURGO DB by Map' tool
        newRasterFN = arcpy.GetParameterAsText(2)    # Output raster name. Location will be same folder where newDB is located

        scriptPath = __file__
        scriptFolder = os.path.dirname(scriptPath)
        basePath = os.path.dirname(scriptFolder)
        # templatePath = os.path.join(basePath, "TemplateDatabases")
        # templateDB = os.path.join(templatePath, templateName)

        newPaths = list()
        newPaths.append(scriptFolder)  # add Script subfolder to system path

        if len(newPaths) > 0:
            myPath = os.environ['PATH']
            pathList = myPath.split(";")
            addList = list()

            for p in newPaths:
                if not p in pathList:
                    os.environ['PATH'] += ";" + p

        bGood = main(newDB, inputLayer, newRasterFN, scriptFolder)

        PrintMsg(".", 0)
        PrintMsg(".\tProcessing complete", 0)


except MyError as e:
    PrintMsg(str(e), 2)

except:
    errorMsg(sys.exc_info())

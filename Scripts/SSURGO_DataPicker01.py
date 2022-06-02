# SSURGO_DataLoader01.py
#
# Modifying this script to run independently of ArcPy
#
# SSURGO_Convert_to_SQLiteDB9.py

# Import data from WSS-SSURGO downloads (.txt and .shp) to an SQLite database.
#
# Using a template database with attribute table schema. Month table is pre-populated.
#
# Tabular import is sequential by table iterating through all survey areas.
#
# This script has functions that can handle OGR spatial import or arcpy spatial import.
#
# July 1. Added spatialite commandline scripting to the AppendFeatures_Spatialite function.
#
# Dec 10. Trying to update version-checking functions and remove more arcpy library references
#
# To try: PRAGMA foreign_keys = OFF; This should work. Needs to be a script parameter
# To try: Look at version numbers for database, tabular, spatial and a method for validating those.
# To try: find some way of importing shapefiles without arcpy.
#
# Options for compacting new database...
# sqlite3 can use conn.execute("VACUUM") but needs a lot of diskspace to make a copy.
# a PRAGMA command can be used in older versions of sqlite3:
#    conn.execute("PRAGMA temp_store_directory = '<temp directory>';)
# I did not have any luck with sqlite3 version 2.6 using os.environ['TMPDIR'] or os.environ['TEMP'] settings.
#
#
## Cascading deletes are not setup correctly. Not sure why. Seems to want the primary and foreign keys to be autoincrement.
## Perhaps I need to use:  PRAGMA foreign_keys = ON;
## Error deleting record: FOREIGN KEY constraint failed (DELETE FROM "main"."sacatalog" WHERE _rowid_ IN ('11614'); )

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

# Metadata reference for SSURGO_SQLite databases: https://www.gaia-gis.it/fossil/libspatialite/wiki?name=ISO+Metadata

# Intersting discussion of slimmed-down databases: https://groups.google.com/g/spatialite-users/c/v5WmNfvb7Cw

# ? What is RasterLite2 support?

# Graphics storage: https://www.gaia-gis.it/fossil/libspatialite/wiki?name=GraphicResources
#
# Loadable spatialite modules v5.0  https://www.gaia-gis.it/fossil/libspatialite/wiki?name=Lodable+Modules+in+5.0
#
# NASIS or STAGING SERVER with no mukey for soil polygon shapefile...
# Use this query after the data has been imported to add mukey. It is only designed to work with single SSA exports!:
#
# UPDATE mupolygon
# SET mukey = coalesce(( SELECT mukey FROM mapunit WHERE mapunit.musym = mupolygon.musym and mapunit.mukey IS NOT NULL), mukey);
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

        #else:
        #    return 'MyError has been raised'

## ===================================================================================
def errorMsg():
    # Capture system error from traceback and then exit
    # Should I be passing in the value for sys.exc_info()?
    try:

        # Catch python errors here
        # tbInfo contains the script, function and error line number

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
        sys.exit("Stopping program due to unhandled error")

        return

    except:
        PrintMsg(".", 0)
        PrintMsg(".\tFailure to handle error condition", 0)

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

    except:
        errorMsg()
        return False

## ===================================================================================
def Number_Format(num, places=0, bCommas=True):
    try:
    # Format a number according to locality and given places
        locale.setlocale(locale.LC_ALL, "")
        if bCommas:
            theNumber = locale.format_string("%.*f", (places, num), True)

        else:
            theNumber = locale.format_string("%.*f", (places, num), False)

        return theNumber

    except MyError as e:
        PrintMsg(str(e), 2)
        return "???"

    except:
        errorMsg()
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
def CopyTemplateDB(templateDB, newDB):
    # Copy the appropriate version of SQLite database from the scripts folder to the new location and rename.
    #
    # Seem to be having a problem with the featureclasses disappearing after the name of the new database is changed
    # during the copy. Try using arcpy instead of shutil for mobile geodatabase option.

    try:

        outputFolder = os.path.dirname(newDB)
        newName = os.path.basename(newDB)
        dbExt = os.path.splitext(newName)

        if not os.path.exists(templateDB):
            err = "Input template database not found (" + templateDB + ")"
            raise MyError(err)

        PrintMsg(".", 0)
        PrintMsg("Copying '" + os.path.basename(templateDB) + "' to new database: '" + newDB + "'", 0)

        if os.path.exists(newDB):
            try:
                os.remove(newDB)

            except:
                raise MyError("Failed to remove existing database (" + newDB + ")" )

        time.sleep(1)

        shutil.copy2(templateDB, newDB)

        if not os.path.exists(newDB):
            err = "Failed to create new database (" + newDB + ")"
            raise MyError(err)

        return True

    except MyError as e:
        PrintMsg(str(e), 2)
        return False

    except:
        errorMsg()
        return False

## ===================================================================================
## ===================================================================================

# Import system modules
import arcpy, sys, string, os, traceback, locale, time, datetime, shutil

# from imp import reload

##from osgeo import ogr
##from osgeo import gdal
##ogr.UseExceptions()
##
##import subprocess
##import sqlite3
##sqlite3.enable_callback_tracebacks(True)


try:
    if __name__ == "__main__":

        inputFolder = arcpy.GetParameterAsText(0)     # location of SSURGO datasets containing spatial folders
        ssaLayer = arcpy.GetParameterAsText(1)        # Test to see if I can sort the ssaLayer when using the 'Create SSURGO-Lite DB by Map' tool
        templateName = arcpy.GetParameterAsText(2)    # empty SQLite database with SSSURGO schema
        newDB = arcpy.GetParameterAsText(3)           # fullpath for the new output geodatabase
        geogRegion = arcpy.GetParameterAsText(4)      # Geographic Region used to set output coordinate system
        surveyList = arcpy.GetParameter(5)            # list of SSURGO dataset folder names to be proccessed (e.g. 'soil_ne109')
        tmpFolder = arcpy.GetParameterAsText(6)       # Folder where vacuum will take place
        bSpatialDiet = arcpy.GetParameter(7)          # Do not compress polygon geometries on import
        bAppend = arcpy.GetParameter(8)               # Use arcpy.Append command to import spatial data. Default = False.

        args = [inputFolder, ssaLayer, templateName, newDB, geogRegion, surveyList, tmpFolder, bSpatialDiet, bAppend]

        for arg in args:
            if arg is None or arg == '':
                raise MyError (os.path.basename(sys.argv[0]) + " is missing one or more input arguments")

            #else:
            #    PrintMsg(".\t" + str(arg), 0)

        import SSURGO_DataLoader01  # For production version of tool, change this back to 'import'

        PrintMsg(".", 0)

        scriptPath = __file__  # should be the same as sys.argv[0] where sys.argv is a list.
        scriptFolder = os.path.dirname(scriptPath)
        basePath = os.path.dirname(scriptFolder)

        PrintMsg(".", 0)
        PrintMsg("Setting up environment for import process...", 0)

        # This version of script combines some of the 'Data Picker' as well as 'Data Loader' functions.
        # Ideally in the future, there will be no templateDB referenced here, only 'newDB'
        # Here it is assumed that all Template databases will be stored in a set location relative to this script.
        templatePath = os.path.join(basePath, "TemplateDatabases")
        templateDB = os.path.join(templatePath, templateName)

        # Using MyDocuments\GIS\Python
        # PrintMsg(".", 0)
        # PrintMsg(".\tBase folder: " + basePath, 0)
        # PrintMsg(".", 0)

        bDB = CopyTemplateDB(templateDB, newDB)

        if bDB:
            bGood = SSURGO_DataLoader01.main(inputFolder, surveyList, newDB, geogRegion, tmpFolder, bSpatialDiet, bAppend)

        else:
            bGood = False

        if bGood == False:
            PrintMsg("Processing new database failed...", 2)
            PrintMsg(".", 0)

        else:
            PrintMsg("Successfully created new database: " + newDB, 0)
            PrintMsg(".", 0)

except MyError as e:
    PrintMsg(str(e), 2)

except:
    PrintMsg(".\tExiting main with an error...", 0)
    errorMsg()

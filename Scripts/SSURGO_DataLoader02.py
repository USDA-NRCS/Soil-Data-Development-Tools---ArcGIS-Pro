# SSURGO_DataLoader02.py
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
def errorMsg0():
    # Capture system error from traceback and then exit
    # Should I be passing in the value for sys.exc_info()?
    try:
        # sys.tracebacklimit = 1
        # PrintMsg("Function: " + sys._getframe().f_code.co_name, 1)

        excInfo = sys.exc_info()

        # PrintMsg("Got excInfo object which is a tuple that should contain 3 values", 0)
        # 0: type gets the type of the exception being handled (a subclass of BaseException)
        # 1: value gets the exception instance (an instance of the exception type)
        # 2: traceback gets a traceback object which encapsulates the call stack at the point where the exception originally occurred

        errMsg = "Unknown error"
        PrintMsg(".\texcInfo: " + str(excInfo), 0)

        if not excInfo is None:

            errType = ""
            errValue = ""
            errTB = None
            #errTB = sys.last_traceback

            if len(excInfo) > 0:
                errType = str(excInfo[0])

                if len(excInfo) > 1:
                    errValue = str(excInfo[1])

                    if len(excInfo) > 2:
                        errTB = str(excInfo[2])

                errMsg = errType + ":\t" + str(errValue)
                PrintMsg(errMsg, 2)

            else:
                PrintMsg("excInfo has no data", 2)

        else:
            PrintMsg("excInfo is None", 2)

        del excInfo

        #sys.exit("Exit error. " + errMsg)
        return


    except Exception as err:
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

## ===================================================================================

def PrintMsg(msg, severity=0):
    # Adds tool message to the geoprocessor
    #
    #Split the message on \n first, so that if it's multiple lines, a GPMessage will be added for each line

    try:
        if bArcPy:
            for string in msg.split('\n'):
                #Add a geoprocessing message (in case this is run as a tool)
                if severity == 0:
                    arcpy.AddMessage(string)

                elif severity == 1:
                    arcpy.AddWarning(string)

                elif severity == 2:
                    arcpy.AddError(" \n" + string)

        else:
            print(msg)

    except MyError as e:
        print(str(e))
        return False

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
def CreateSSURGO_DB(newDB, areasymbolList, aliasName, templateDB):
    # Copy the appropriate version of SQLite database from the scripts folder to the new location and rename.
    #
    # Seem to be having a problem with the featureclasses disappearing after the name of the new database is changed
    # during the copy. Try using arcpy instead of shutil for mobile geodatabase option.

    try:

        outputFolder = os.path.dirname(newDB)
        gdbName = os.path.basename(newDB)
        dbExt = os.path.splitext(gdbName)
        PrintMsg(".", 0)
        PrintMsg("Creating new database: " + newDB, 0)

        if os.path.exists(newDB):
            try:
                os.remove(newDB)

            except:
                raise MyError("Failed to remove existing database (" + newDB + ")" )

        time.sleep(1)


        if not os.path.exists(templateDB):
            err = "Failed to create new geodatabase"
            raise MyError(err)

        # PrintMsg(".\tUsing shutil to copy template to new database", 0)
        shutil.copy2(templateDB, newDB)

        if not os.path.exists(newDB):
            err = "Failed to create new geodatabase"
            raise MyError(err)

        # Another option to check tables would be the following query. Need to confirm for sqlite and mobile geodatabase:
        #"""SELECT name FROM sqlite_master WHERE type = 'table' AND NOT name LIKE 'gpkg%' AND NOT name LIKE 'rtree%'; """


        return True

    except MyError as e:
        PrintMsg(str(e), 2)
        return False

    except:
        errorMsg()
        return False

## ===================================================================================
def GetTableList(liteCur):
    # Query sqlite database and return a list of tables
    #
    try:
        tblList = list()

        #queryListTables = "SELECT name FROM sqlite_master WHERE type = 'table' AND NOT name LIKE 'gpkg%' AND NOT name LIKE 'geometry_%' AND NOT name LIKE 'rtree%'; "
        queryListTables = "SELECT name FROM sqlite_master WHERE type = 'table' AND NOT name LIKE 'idx_%' AND NOT name LIKE 'rtree%'; "

        liteCur.execute(queryListTables)

        rows = liteCur.fetchall()

        tableNames = [row[0] for row in rows]

        #PrintMsg("\n".join(tableNames), 0)

        return tableNames

    except MyError as e:
        PrintMsg(str(e), 2)
        return []

    except:
        errorMsg()
        return []

## ===================================================================================
def GetCount(newDB, tbl):
    # Query sqlite database and return the record count for the specified table
    #
    try:
        recordCount = -1

        tblList = list()

        queryCount = "SELECT COUNT(*) FROM " + tbl + "; "
        conn = sqlite3.connect(newDB)
        liteCur = conn.cursor()
        liteCur.execute(queryCount)
        row = liteCur.fetchone()
        recordCount = row[0]

        #PrintMsg("\n".join(tableNames), 0)

        return recordCount

    except MyError as e:
        PrintMsg(str(e), 2)
        return recordCount

    except sqlite3.IntegrityError as err:
        PrintMsg(".\tSQLite IntegrityError: ", 2)
        time.sleep(5)
        PrintMsg(".\t" + err.args[0], 2)
        time.sleep(5)
        return recordCount

    except sqlite3.OperationalError as err:
        # Even after a 5 second pause, I'm getting an error from SELECT COUNT.
        # no such table: xx_mupolygon
        PrintMsg(".\tSQLite OperationalError: ", 2)
        time.sleep(5)
        PrintMsg(".\t" + err.args[0], 2)
        time.sleep(5)
        return recordCount

    except sqlite3.Error as err:
        PrintMsg(".\tSQLite Error: ", 2)
        time.sleep(5)
        msg = err.args[0]
        PrintMsg(".\t" + msg, 2)
        time.sleep(5)
        return recordCount

    except:
        errorMsg()
        return recordCount

    finally:
        try:
            PrintMsg(".\tFinally closing database")
            time.sleep(2)
            conn.close()
            del conn

        except:
            pass

        return recordCount

## ===================================================================================
def GetCountShp(driver, shpFile):
    # Get featurecount for specified shapefile (fullpath), using ogr
    #
    try:
        featCnt = -1

        ds = driver.Open(shpFile, 0)

        if ds is None:
            err = "Failed to open " + shpFile + " using ogr with ESRI shapefile driver"
            raise MyError(err)

        layer = ds.GetLayerByIndex(0)
        featCnt = layer.GetFeatureCount()

        #return featCnt

    except MyError as e:
        PrintMsg(str(e), 2)
        return featCnt

    except:
        errorMsg()
        return featCnt

    finally:
        try:
            del ds

        except:
            pass

        return featCnt

## ===================================================================================
def GetExtentShp(driver, shpFile):
    # Get featurecount for specified shapefile (fullpath), using ogr
    #
    try:
        featCnt = -1
        ul = [0, 0]

        ds = driver.Open(shpFile, 0)

        if ds is None:
            err = "Failed to open " + shpFile + " using ESRI shapefile driver"
            raise MyError(err)

        layer = ds.GetLayerByIndex(0)
        featCnt = layer.GetFeatureCount()

        if featCnt > 0:
            XMin, xMax, YMin, YMax = layer.GetExtent()  # ogr extents are not in the same order as arcpy

            ulX = round(XMin, 5)
            ulY = round(YMax, 5)

    except MyError as e:
        PrintMsg(str(e), 2)
        return -1, 0, 0

    except:
        errorMsg()
        return -1, 0, 0

    finally:
        try:
            del ds

        except:
            pass

        return featCnt, ulX, ulY

## ===================================================================================
def CompactDatabase(newDB, tmpFolder):
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
        if bArcPy:
            arcpy.SetProgressorLabel("Compacting new database...")

        PrintMsg(".", 0)
        PrintMsg("Compacting new database using " + tmpFolder + "...")
        start = time.time()

        dbSize = (os.stat(newDB).st_size / (1024.0 * 1024.0))  # units are MB
        os.environ["TEMP"] = tmpFolder

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
        theMsg = ".\tFinished compacting database in: " + elapsedTime(start)
        PrintMsg(theMsg, 0)

        return True

    except MyError as e:
        PrintMsg(str(e), 2)
        return False

    except:
        errorMsg()
        return False

# ===================================================================================
def GetSaveRestDate(liteCur, areaSym):
    # Get SAVEREST date from an existing record in the database
    #
    try:

        dbDate = 0
        PrintMsg(".\tRunning GetSaveRestDate", 0)
        querySaverest = "SELECT saverest FROM sacatalog WHERE areasymbol = ?"
        liteCur.execute(querySaverest, areaSym)
        row = liteCur.fetchone()
        dbDate = str(row[0]).split(" ")[0]

        return dbDate

    except:
        errorMsg()
        return dbDate


# ===================================================================================
def SaveRestTxt(tabularFolder):
    # For future use. Needs more work.
    # Should really update system_templatedatabaseinformation table in order to properly implement.
    # Probably need another function that compares the version.txt versions to
    # the system_templatedatabaseinformation table versions.
    # 'SSURGO Version'.'Import Data Model Version'.'Base Metadata Version'
    #

    #
    # Get SSURGO version from the Template database "SYSTEM Template Database Information" table
    # or from the tabular/version.txt file, depending upon which is being imported.
    # Compare the version number (first digit) to a hardcoded version number which should
    # be theoretically tied to the XML workspace document that accompanies the scripts.
    #
    # Need to research NASIS-SSURGO export and Staging Server export.
    # Downloads should include a version.txt in both spatial and tabular folders.
    #
    # WSS download:
    # spatial\version.txt contains one line: 2.3.3
    # tabular\version.txt contains one line: 2.3.3
    #

    try:

        # Get areasymbol, tabular version, saverest date from SSURGO download(sacatlog.txt)
        catalogFile = os.path.join(tabularFolder, "sacatlog.txt")
        dVersions = dict()

        if os.path.isfile(catalogFile):
            # read just the first line of the sacatlog.txt file
            fh = open(catalogFile, "r")
            saVersion = fh.readline().strip()
            fh.close()
            del fh

            catList = saVersion.split("|")

            dVersions["areasymbol"] = catList[0]
            dVersions["saversion"] = int(catList[2])
            dVersions["saverest"] = catList[3]
            dVersions["tabularversion"] = catList[4]
            dVersions["tabularverest"] = catList[5]
            #PrintMsg(".\tsacatlog.txt: " + str(dVersions), 0)

            return dVersions

        else:
            # Unable to compare vesions. Warn user but continue
            PrintMsg("Unable to find tabular file: version.txt", 1)
            return dict()

    except MyError as e:
        # Example: raise MyError("This is an error message")
        PrintMsg(str(e), 2)
        return dict()

    except:
        errorMsg()
        return dict()

# ===================================================================================
def SSURGOVersionTxt(tabularFolder):
    # For future use. Needs more work.
    # Should really update system_templatedatabaseinformation table in order to properly implement.
    # Probably need another function that compares the version.txt versions to
    # the system_templatedatabaseinformation table versions.
    # 'SSURGO Version'.'Import Data Model Version'.'Base Metadata Version'
    #

    #
    # Get SSURGO version from the Template database "SYSTEM Template Database Information" table
    # or from the tabular/version.txt file, depending upon which is being imported.
    # Compare the version number (first digit) to a hardcoded version number which should
    # be theoretically tied to the XML workspace document that accompanies the scripts.
    #
    # Need to research NASIS-SSURGO export and Staging Server export.
    # Downloads should include a version.txt in both spatial and tabular folders.
    #
    # WSS download:
    # spatial\version.txt contains one line: 2.3.3
    # tabular\version.txt contains one line: 2.3.3
    #

    try:
        #PrintMsg(".\tRunning SSURGOVersionTxt", 0)
        # Get version numbers from SSURGO download(version.txt)
        versionTxt = os.path.join(tabularFolder, "version.txt")

        if os.path.isfile(versionTxt):
            # read just the first line of the version.txt file
            fh = open(versionTxt, "r")
            #txtVersion = int(fh.readline().split(".")[0])
            txtVersion = fh.readline().strip()
            fh.close()
            del fh
            #PrintMsg(".\tversion.txt: " + txtVersion, 0)
            return txtVersion

        else:
            # Unable to compare vesions. Warn user but continue
            PrintMsg("Unable to find tabular file: version.txt", 1)
            return 0

    except MyError as e:
        # Example: raise MyError("This is an error message")
        PrintMsg(str(e), 2)
        return 0

    except:
        errorMsg()
        return 0

# ===================================================================================
def SSURGOVersionDB(liteCur):
    # Get SSURGO version numbers from the "system_templatedatabaseinformation" table and
    # compare with version.txt file in tabular folder.
    #
    # Not yet implemented.
    #
    # Any soil data exported from Web Soil Survey includes a file named “version.txt”.
    # The contents of this file is used to determine if the data a user is about to import
    # into a SSURGO Template database is compatible with that database, and whether or
    # not any accompanying metadata should be imported.
    #
    # File “version.txt” contains a single line in the form number.number.number.
    #
    # The first number is the SSURGO Version.  See section “SSURGO Version” in this
    # same report for additional information. The MS Access database has a '2.2' for this element.
    #
    # The second number is the Import Data Model Version.  See section “Import Data Model Version”
    # in this same report for addition information.
    #
    # The third number is the Metadata Version.  This refers to the 'mdstat*' tables.
    # See record “Base Metadata Version” in the system_templatedatabaseinformation table for additional information.
    #
    # Every version of a SSURGO Template database where the SSURGO Template database
    # version is greater than or equal to 36 “knows” what SSURGO Version and Import
    # Data Model Version it is compatible with.
    #
    # No data will be imported unless both the SSURGO Version and the Import Data Model Version
    # in file “version.txt” match what is expected.
    #
    # Metadata will not be imported unless the Metadata Version in file version.txt is greater
    # than the Base Metadata Version of the SSURGO Template database in question.  This prevents
    # obsolete metadata from being imported.
    #
    # For those of you responsible for creating and/or updating MS Access - SSURGO Template databases,
    # ExpectedSSURGOVersion, ExpectedImportDataModelVersion and BaseMetadataVersion are
    # defined in the Declarations section of VBA Module “Import Procedures”.

    try:
        #PrintMsg(".\tRunning SSURGOVersionDB", 0)

        tblName = "system_templatedatabaseinformation"

        tableList = GetTableList(liteCur)

        if tblName in tableList:

            # Get SSURGO Version
            # This is the general version number of the SSURGO data. This probably won't change.
            querySSURGOVersion = "SELECT Item_Value FROM " + tblName + " WHERE Item_Name = 'SSURGO Version';"
            liteCur.execute(querySSURGOVersion)
            row = liteCur.fetchone()
            ssurgoVersion = str(row[0]).split(" ")[0]

            # Get Import Data Model Version
            # Currently any dataset with a value of '3' should be compatible with this DataLoader
            queryImportVersion = "SELECT Item_Value FROM " + tblName + " WHERE Item_Name = 'Import Data Model Version';"
            liteCur.execute(queryImportVersion)
            row = liteCur.fetchone()
            importVersion = str(row[0]).split(" ")[0]

            # Get Base Metadata Version
            # This should be used to determine whether the textfiles for the mdstat tables should be used to update the database
            # This functionality has not yet been incorporated into the DataLoader
            queryMetadataVersion = "SELECT Item_Value FROM " + tblName + " WHERE Item_Name = 'Base Metadata Version';"
            liteCur.execute(queryMetadataVersion)
            row = liteCur.fetchone()
            metadataVersion = str(row[0]).split(" ")[0]

            # Combine the three integer values to match the format of version.txt

            dbVersion = str(ssurgoVersion) + "." + str(importVersion) + "." + metadataVersion

            PrintMsg(".\tTemplate database version information: " + dbVersion, 0)

            return dbVersion

        else:
            # Unable to open SYSTEM table in existing dataset
            # Warn user but continue
            err = "Unable to open '" + tblName + "'"
            raise MyError(err)

    except:
        errorMsg()
        return ""

## ===================================================================================
def GetFieldInfo(tblName, liteCur):
    # Get list of existing fieldnames for this table
    try:

        queryFieldNames = "SELECT name, type FROM PRAGMA_TABLE_INFO('" + tblName + "');"
        liteCur.execute(queryFieldNames)
        rows = liteCur.fetchall()
        fldNames = [row for row in rows]

        #PrintMsg(".\tfldNames in GetFieldInfo: " + str(fldNames), 0)
        return fldNames

    except:
        errorMsg()
        return []

## ===================================================================================
def GetFieldInfo_MD(tblName, liteCur):
    # Get list of original, SSURGO-spec fieldnames for this table. Using mdstattabcols.
    try:

        queryFieldNames = "SELECT colphyname FROM mdstattabcols WHERE tabphyname = '" + tblName + "' ORDER BY colsequence ASC ;"
        liteCur.execute(queryFieldNames)
        rows = liteCur.fetchall()
        fldNames = [row[0] for row in rows]

        return fldNames

    except:
        errorMsg()
        return []


## ===================================================================================
def GetGeometryTypes(liteCur):
    # Get list of existing fieldnames for the Spatialite geometry_columns table in the output database
    try:
        # Dictionary containing the id's for the possible geometry types in a SSURGO Spatialite database
        # Need to consult with Adolfo on SSURGO standards. MULITPOLYGON, MULTILINESTRING and MULTIPOINT are illegal, correct?
        dGeometryTypes = dict()
        dGeometryIDS = {1:"POINT", 2:"LINESTRING", 3:"POLYGON", 6:"MULTIPOLYGON", 1000002:"COMPRESSED_LINESTRING", 1000003:"COMPRESSED_POLYGON"}


        queryGeometryTypes = "SELECT f_table_name, geometry_type FROM geometry_columns;"
        liteCur.execute(queryGeometryTypes)
        rows = liteCur.fetchall()

        for row in rows:
            dGeometryTypes[row[0]] = dGeometryIDS[row[1]]

        # PrintMsg(".\tdGeometryTypes: " + str(dGeometryTypes), 0)

        return dGeometryTypes

    except:
        errorMsg()
        return dGeometryTypes

## ===================================================================================
def GetRuleKey(liteCur, nasisrulename):
    # Get the rulekey for the specified nasis rulename.
    # Note! Only one rulekey is returned, even if the database has more than one. Normally
    # there should only be one.

    try:
        #bVerbose = True
        ruleKey = None

        attributeList = list()

        # Open initial table and get data
        tbl = "distinterpmd"
        querySearch = "SELECT rulekey FROM " + tbl + " WHERE rulename = ? LIMIT 1;"
        tblValues = (nasisrulename, )
        liteCur.execute(querySearch, tblValues)
        row = liteCur.fetchone()

        if not row is None:
            ruleKey = row[0]

        else:
            ruleKey = None

        return ruleKey

    except:
        errorMsg()
        return None

## ===============================================================================================================
def SetCacheSize(conn, liteCur):
    # Set size of memory cache for inserts, deletes
    # https://blog.devart.com/increasing-sqlite-performance.html

    try:
        # Restore original attribute indexes
        #PrintMsg(".", 0)
        #PrintMsg("Setting cache size for indexing performance...", 0)

        #queryCacheSize = "PRAGMA main.cache_size = -200000;"
        queryCacheSize = "PRAGMA main.cache_size = 500;"
        liteCur.execute(queryCacheSize)
        conn.commit()

        return True

    except MyError as e:
        # Example: raise MyError("This is an error message")
        PrintMsg(str(e), 2)
        return False

    except:
        errorMsg()
        return False

## ===============================================================================================================
def DropIndexes(conn, liteCur):
    # Retrieve physical and alias names from MDSTATTABS table and assigns them to a blank dictionary.
    # Stores tabular-text filename (key) tablename, table aliase (value) in a Python dictionary i.e. {chasshto:'Horizon AASHTO,chaashto'}

    try:

        # Delete all attribute indexes for faster database creation
        PrintMsg(".\tDropping attribute indexes from new database...", 0)

        vals = ('index', 'sqlite%')
        queryIndexes = "SELECT name, sql FROM sqlite_master WHERE type = ? AND NOT name LIKE ?;"
        liteCur.execute(queryIndexes, vals)
        indexes = liteCur.fetchall()

        if len(indexes) == 0:
            PrintMsg(".\tNo indexes found in template database", 1)
            return []

        names, createSQLs = zip(*indexes)

        if len(names) > 0:
            for name in names:
                liteCur.execute("DROP INDEX IF EXISTS " + name + ";")
                conn.commit()
                # PrintMsg(".\tDropped index: " + name, 0)

        # Confirm that the indexes were actually dropped. Probably don't need this in production.
        liteCur.execute(queryIndexes, vals)
        post_indexes = liteCur.fetchall()

        if len(post_indexes) > 0:
            PrintMsg(".\t" + str(len(post_indexes)) + " indexes still remain after 'drop'", 1)

        return createSQLs

    except MyError as e:
        # Example: raise MyError("This is an error message")
        PrintMsg(str(e), 2)
        return []

    except:
        errorMsg()
        return []

## ===============================================================================================================
def RestoreAttributeIndexes(conn, liteCur, createSQLs):
    # Restore previously existing attribute indexes

    try:
        # Restore original attribute indexes
        PrintMsg(".", 0)
        PrintMsg("Restoring previously existing attribute indexes for the new database...", 0)
        start = time.time()

        for createSQL in createSQLs:
            createSQL = createSQL.replace("CREATE INDEX", "CREATE INDEX IF NOT EXISTS")
            #PrintMsg(".\t" + createSQL, 0)
            liteCur.execute(createSQL)

        conn.commit()

        theMsg = ".\tTotal processing time for updating attribute indexes: " + elapsedTime(start) + " \n "
        PrintMsg(theMsg, 0)

        return True

    except MyError as e:
        # Example: raise MyError("This is an error message")
        PrintMsg(str(e), 2)
        return False

    except:
        errorMsg()
        return False

## ===============================================================================================================
def CreateNewIndexes(conn, liteCur):
    # Create attribute indexes using metadata from mdstat* tables
    #
    # Big question. Does this work for spatialite database?
    try:
        PrintMsg(".\tCreating new attribute indexes using metadata...", 0)

        # After all data has been imported, create indexes for soil attribute tables using mdstat* tables.
        #
        # At this point we're assuming that the mdstat tables are populated.
        #
        # For Mobile Geodatabases there are a couple of arcpy tools...
        # https://pro.arcgis.com/en/pro-app/latest/tool-reference/data-management/migrate-relationship-class-tool.htm
        # https://pro.arcgis.com/en/pro-app/latest/tool-reference/data-management/add-global-ids.htm

        #PrintMsg(".\tLoading ST_Geometry library", 0)
        #conn.load_extension('stgeometry_sqlite.dll')
        # conn.load_extension('mod_spatialite')  # Error 'The specified procedure could not be found.

        # idxcolsequence is important. Make sure that order is maintained in the dictionary objects.
        PrintMsg("Creating indexes for attribute tables...", 0)
        time.sleep(1)  # Sometimes none of the indexes are created for the sqlite databases. I don't understand this.

        sqlForeignKeys = """SELECT IM.tabphyname, ID.idxcolsequence, IM.idxphyname, ID.colphyname, RD.ltabphyname, RD.ltabcolphyname
        FROM mdstatidxmas AS IM
        LEFT OUTER JOIN mdstatidxdet AS ID ON (IM.idxphyname = ID.idxphyname) AND (IM.tabphyname = ID.tabphyname)
        LEFT OUTER JOIN mdstatrshipdet AS RD ON (ID.tabphyname = RD.rtabphyname AND ID.colphyname = RD.rtabcolphyname)
        -- WHERE IM.idxphyname LIKE 'DI%' AND RD.ltabphyname IS NOT NULL
        -- WHERE RD.ltabphyname IS NOT NULL
        ORDER BY IM.tabphyname, IM.idxphyname, ID.idxcolsequence ASC
        ;"""

        dIndexes = dict()      # Key value is idxphyname.
        infoList = list()
        cntr = 0

        # Get index parameters from mdstat tables...
        # It looks like there is a missing record for UC_mdstatdomdet_4565. Please confirm
        # that the second column
        liteCur.execute(sqlForeignKeys)
        rows = liteCur.fetchall()

        for row in rows:
            #
            cntr += 1
            tabphyname, idxcolsequence, idxphyname, colphyname, ltabphyname, ltabcolphyname = row
            #PrintMsg(str(cntr) + ".\t" + tabphyname + ": " + idxphyname + ", " + str(idxcolsequence) + ", " + str(colphyname) + ", " + str(ltabphyname) + ", " + str(ltabcolphyname) , 0)
            # chaashto: DI_chaashto_73, 1, chkey, chorizon, chkey

            if idxphyname != 'UC_sdvattribute_12302':  # only skipping this until we can resolve problem with Dep2ResLyr
                if not idxphyname in dIndexes:
                    # start new index
                    dIndexes[idxphyname] = tabphyname, [colphyname], ltabphyname, [ltabcolphyname]

                else:
                    # append additional columns to the existing information for this index
                    # PrintMsg(".\tConcatenated key for " + str(tabphyname) + ":" + idxphyname + " adds " + str(colphyname) + " and " + str(ltabcolphyname), 1)
                    dIndexes[idxphyname][1].append(colphyname)
                    dIndexes[idxphyname][3].append(ltabcolphyname)


        # Generate and execute SQL for indexes. Right now we're doing one-at-a-time.
        if len(dIndexes) > 0:
            PrintMsg(".\tShould I be creating indexes after closing the database and re-opening?", 0)

            for indexName in dIndexes.keys():
                try:
                    if indexName[0:2] == "UC":
                        sCreate = "CREATE UNIQUE INDEX  IF NOT EXISTS "

                    else:
                        sCreate = "CREATE INDEX IF NOT EXISTS "

                    #PrintMsg(".\tCreating index " + indexName, 0)

                    # tabphyname, [colphyname], ltabphyname, [ltabcolphyname] (updated dIndexes values)
                    tblName, colNames, parentTbl, parentColumns = dIndexes[indexName]

                    if len(colNames) == 1:
                        sCreateIndex = sCreate + indexName + " ON " + tblName + "(" + colNames[0] + ");"

                    else:
                        sCreateIndex = sCreate + indexName + " ON " + tblName + "(" + ", ".join(colNames) + ");"

                    #indexQuery += sIndex
                    PrintMsg(".\tIndex for " + tblName + " on " + ", ".join(colNames), 0)
                    liteCur.execute(sCreateIndex)
                    conn.commit

                except:
                    PrintMsg(".\tError while creating an attribute index", 1)
                    break

            if bArcPy:
                arcpy.SetProgressorLabel("Finished with attribute indexes")

        else:
            raise MyError("Failed to get information needed for indexes")

        time.sleep(1)  # Sometimes the indexes aren't being created. Don't understand this.
        if bArcPy:
            arcpy.SetProgressorLabel("Creation of attribute indexes from metadata is complete")

        # End of attribute indexes
        # *********************************************************************************************************
        # *********************************************************************************************************

        return True

    except MyError as e:
        # Example: raise MyError("This is an error message")
        PrintMsg(str(e), 2)
        return False

    except:
        errorMsg()
        return False

## ===============================================================================================================
def GetTableInfoSQL(liteCur):
    # Retrieve physical and alias names from MDSTATTABS table and assigns them to a blank dictionary.
    # Stores tabular-text filename (key) tablename, table aliase (value) in a Python dictionary i.e. {chasshto:'Horizon AASHTO,chaashto'}

    try:
        tblInfo = dict()

        # Query mdstattabs table containing information for other SSURGO tables
        #tbl = "main.mdstattabs"
        tbl = "mdstattabs"
        queryTableInfo = "SELECT tabphyname, tablabel, iefilename FROM " + tbl

        #PrintMsg("Using query to get table info:\t" + queryTableInfo, 0)


        for row in liteCur.execute(queryTableInfo):

            physicalName, aliasName, importFileName = row

            if not importFileName in tblInfo:
                #PrintMsg("\t" + importFileName + ": " + physicalName, 1)
                tblInfo[importFileName] = physicalName, aliasName

        if len(tblInfo) == 0:
            raise MyError("Failed to get required information from mdstattabs table. Is it empty?")

        return tblInfo

    except MyError as e:
        # Example: raise MyError("This is an error message")
        PrintMsg(str(e), 2)
        return dict()

    except:
        errorMsg()
        return dict()


## ===============================================================================================================
def GetImportOrder(liteCur):
    # Retrieve ordered list of information needed for tabular import.
    # daglevel tabphyname, iefilename, tablabel
    # Must check to see if daglevel exists in the mdstattabs table before calling

    try:
        importList = list()

        # Query mdstattabs table containing information for other SSURGO payload tables
        # tbl = "main.mdstattabs"
        tbl = "mdstattabs"
        queryTableInfo = "SELECT iefilename FROM " + tbl + \
        " WHERE daglevel >= 0 AND tabphyname NOT LIKE 'mdstat%' " + \
        " ORDER BY daglevel ASC, tabphyname ;"

        #PrintMsg("Using query to get tabular import specifications :\t" + queryTableInfo, 0)

        for row in liteCur.execute(queryTableInfo):
            #daglevel, tabphyname,  iefilename, tablabel = row
            importList.append(row)

        if len(importList) == 0:
            raise MyError("Failed to get required information from mdstattabs table. Is it empty?")

        return importList

    except MyError as e:
        # Example: raise MyError("This is an error message")
        PrintMsg(str(e), 2)
        return list()

    except:
        errorMsg()
        return list()

## ===================================================================================
def ImportTabularSQL(newDB, pathList, importVersion, tableList, conn, liteCur):

    # Handles cointerp table differently. If a SSURGO-standard column is missing, that tabular data element will be skipped
    # If ruledepth is not present in the database, then the rating reasons (rulename) will be skipped.

    # Use csv reader method of importing text files into geodatabase for those
    # that do not have a populated SSURGO database
    #
    # Encoding issues to be aware of....
    # WSS-SSURGO downloads are UTF-8, but NASIS-SSURGO exports are ISO-8859-1. CP1252 might work.
    #
    # Using unique constraint to prevent duplicate records in sdv* tables. Dupes will be skipped.
    # For any of the other data tables, a unique contraint violation will throw an error and stop the import.
    #
    try:
        result = False
        # new code from ImportTables
        #codePage = 'cp1252'

        #PrintMsg(".\tSetting csv - field size limit", 0)
        csv.field_size_limit(min(sys.maxsize, 2147483646))
        encoder = "UTF-8"
        #encoder = "ISO-8859-1"
        #encoder = "CP1252"

        PrintMsg(".", 0)
        PrintMsg("Importing tabular data using function 'ImportTabularSQL'...", 0)

        iCntr = 0
        tbl = "Unknown"

        # Create a list of textfiles to be imported using mdstattabs table. The import process MUST follow the
        # order in this list in order to maintain referential integrity. This list

        fldInfos = GetFieldInfo("mdstattabs", liteCur)
        fldNames = list()

        for fld in fldInfos:
            fldName, fldType = fld
            fldNames.append(fldName.lower())

        if "daglevel" in fldNames:
            # Get ordered list of tables to import
            PrintMsg(".\tUsing DAG Levels to define tabular import sequence", 0)
            importOrder = GetImportOrder(liteCur)
            txtFiles = [f[0] for f in importOrder]

        else:
            raise MyError("daglevel column not found in mdstattabs table")

        #PrintMsg(" \n" + str(txtFiles), 1)

        # Create a dictionary. Keys are tabular-textfile names with table information
        tblInfo = GetTableInfoSQL(liteCur)

        if len(tblInfo) == 0:
            raise MyError("")


        # Get the Template database version information from target database
        templateVersion = SSURGOVersionDB(liteCur)

        ## Begin Table Iteration

        # Need to import text files in a specific order or the MS Access database will
        # return an error due to table relationships and key violations
        if bArcPy:
            arcpy.SetProgressor("step", "Importing tabular data...", 0, len(txtFiles))

        start = time.time()

        for txtFile in txtFiles:

            # Get table name and alias from dictionary
            if txtFile in tblInfo:
                tbl, aliasName = tblInfo[txtFile]

            elif txtFile == "featdesc":
                tbl = "featdesc"
                aliasName = "Feature Description"

            else:
                err = "Textfile reference '" + txtFile + "' not found in 'mdstattabs table'"
                raise MyError(err)

            # continue if the target table exists
            if not tbl in tableList:
                err = "Output table '" + tbl + "' not found in " + newDB
                raise MyError(err)

            fldInfos = GetFieldInfo(tbl, liteCur)
            fldNames = list()
            fldLengths = list()

            for fld in fldInfos:
                fldName, fldType = fld
                fldNames.append(fldName.lower())

            if tbl == 'cointerp':

                if not "ruledepth" in fldNames or not "rulename" in fldNames or not "seqnum" in fldNames:
                    bDiet = True
                    PrintMsg(".\tDropping data for cointerp subrules (rating reasons)", 0)

                else:
                    bDiet = False
                    PrintMsg(".\tKeeping data for cointerp subrules (rating reasons)", 0)

                # Skip import of any csv-data not in the output table
                ssurgoFields = GetFieldInfo_MD(tbl, liteCur)
                #PrintMsg(".\tOriginal SSURGO fields (" + str(len(ssurgoFields)) + ") : " + str(ssurgoFields), 0)

                # Get indexes for all 'missing' fields in cointerp
                colIndexes = []

                for i, fld in enumerate(ssurgoFields):
                    if not fld in fldNames:
                        #PrintMsg(".\tExcluding " + tbl + "." + str(fld) + " from import list", 0)
                        colIndexes.append(ssurgoFields.index(fld))

                colIndexes.reverse()

                # Get csv position for two cointerp attributes
                # This is part of the method to exclude certain cointerp data from import
                ruleIndx = ssurgoFields.index("ruledepth")
                nameIndx = ssurgoFields.index("mrulename")
                #PrintMsg(".\tRuledepth index: " + str(ruleIndx), 0)
                #PrintMsg(".\t" + str(ssurgoFields), 0)

            if len(fldNames) == 0:
                err = "Failed to get field names for " + tbl
                raise MyError(err)

            src = len(fldNames) * ['?']  # this will be used below in executemany

            if bArcPy:
                arcpy.SetProgressorLabel("Importing tabular data for:  " + tbl)
            #time.sleep(2)

            # Begin iterating through the each of the input SSURGO dat
            iCntr += 1

            for tabularFolder in pathList:
                #newFolder = os.path.basename(os.path.dirname(tabularFolder))  # survey dataset folder

                # parse Areasymbol from SSURGO foldername
                soilsFolder = os.path.dirname(tabularFolder)
                spatialFolder = os.path.join(soilsFolder, "spatial")
                fnAreasymbol = soilsFolder[-5:].upper() # This won't work for any areasymbol that is not 5 characters (Mexico, STATSGO)


                # Make sure that input tabular data has the correct SSURGO version for this script
                #tabularVersion = SSURGOVersionTxt(tabularFolder)

                ## Get survey area version information from sacatlog.txt
                #dVersions = SaveRestTxt(tabularFolder)

                if txtFile == "sacatlog":
                    # Make sure that input tabular data has the correct SSURGO version for this script
                    tabularVersion = SSURGOVersionTxt(tabularFolder)

                    # Get survey area version information from sacatlog.txt
                    dVersions = SaveRestTxt(tabularFolder)

                # move to tabular folder. Not sure if this is necessary as long as I use full paths

                if tbl == "featdesc":
                    # this file is the only txt file in the spatial folder
                    txtFile = "soilsf_t_" + fnAreasymbol
                    txtPath = os.path.join(spatialFolder, txtFile + ".txt")

                else:
                    # Full path to SSURGO tabular folder
                    txtPath = os.path.join(tabularFolder, txtFile + ".txt")

                # if the tabular directory is empty return False
                if len(os.listdir(tabularFolder)) < 1:
                    err = "No text files found in the tabular folder"
                    raise MyError(err)


                #PrintMsg("\tImporting text file: " + txtPath, 1)

                # Make sure that input tabular data has the correct SSURGO version for this script
                # ssurgoVersion = SSURGOVersionTxt(tabularFolder)

                ##  NEED TO FIX THIS CHECK
                ##                if ssurgoVersion != dbVersion:
                ##                    err = "Tabular data in " + tabularFolder + " (SSURGO Version " + str(ssurgoVersion) + ") is not supported"
                ##                    raise MyError(err)

                ##  *********************************************************************************************************
                # Full path to SSURGO text file
                # txtPath = os.path.join(tabularFolder, txtFile + ".txt")

                curValues = list()  # list that will contain a single record from the tabular text file. Used by INSERT.

                if not tbl in ['cointerp', 'sdvfolderattribute', 'sdvattribute', 'sdvfolder', 'sdvalgorithm']:

                    iRows = 1  # input textfile line number

                    if os.path.isfile(txtPath):

                        # Use csv reader to read each line in the text file. Save the values to a list of lists.
                        # Write the contents of the entire text file to the table in one

                        with open(txtPath, 'r', encoding=encoder) as tabData:
                            rows = csv.reader(tabData, delimiter='|', quotechar='"')

                            for row in rows:
                                newrow = tuple([val if val else None for val in row])
                                curValues.append(newrow)
                                iRows += 1

                        insertQuery = "INSERT INTO " + tbl + " VALUES (" + ",".join(src) + ");"
                        liteCur.executemany(insertQuery, curValues)
                        #conn.commit()

                    else:
                        err = "Missing tabular data file (" + txtPath + ")"
                        PrintMsg("\t" + err, 1)
                        #raise MyError(err)

                elif tbl in ('sdvfolderattribute', 'sdvattribute', 'sdvfolder', 'sdvalgorithm'):
                    # Import SDV tables one record at a time, in case there are duplicate keys
                    # 'sdvfolderattribute', 'sdvattribute', 'sdvfolder', 'sdvalgorithm'
                    #
                    iRows = 1  # input textfile line number

                    if os.path.isfile(txtPath):

                        # Use csv reader to read each line in the text file
                        insertQuery = "INSERT INTO " + tbl + " VALUES (" + ",".join(src) + ");"

                        with open(txtPath, 'r', encoding=encoder) as tabData:
                        # with open(txtPath, 'r', encoding='iso-8859-1') as tabData:
                        # catching different encoding for NASIS export (esp. sdvattribute table) which as of 2020 uses ISO-8859-1
                            rows = csv.reader(tabData, delimiter='|', quotechar='"')

                            for row in rows:
                                try:
                                    #if tbl == "sdvattribute":
                                    #    PrintMsg("Row " + str(iRows) + ".\t" + str(row), 1)
                                    newrow = tuple([val if val else None for val in row])
                                    liteCur.execute(insertQuery, newrow)
                                    #conn.commit()
                                    iRows += 1

                                except sqlite3.IntegrityError:
                                    # Need to see if I can more narrowly define the error types I want to pass or throw an error
                                    # My intention here is to skip unique value constraint errors that would be expected
                                    #PrintMsg("IntegrityError on row: "  + str(row), 1)
                                    pass

                                except:
                                    PrintMsg("Error writing this row (" + str(iRows) + "): " + str(row), 1)
                                    errorMsg()

                    else:
                        err = "Missing tabular data file (" + txtPath + ")"
                        raise MyError(err)

                elif tbl == 'cointerp':
                    # Should only enter this if cointerp is excluded above
                    # SSURGO originally specified 19 columns for the cointerp table
                    # interpll is the name of the first deprecated column
                    #
                    cRows = 1  # input textfile line number

                    if os.path.isfile(txtPath):

                        try:
                            if bDiet:
                                # Except for NCCPI, exclude all records containing reasons
                                with open(txtPath, 'r', encoding=encoder) as tabData:
                                    rows = csv.reader(tabData, delimiter='|', quotechar='"')

                                    for row in rows:

                                        if int(row[ruleIndx]) == 0:
                                        #if int(row[ruleIndx]) == 0 or row[nameIndx] == "NCCPI - National Commodity Crop Productivity Index (Ver 3.0)":
                                            # Skipping import of cointerp reasons, but keep all NCCPI records for use in Valu1 table.

                                            for i in colIndexes:
                                                del row[i]

                                            newRow = [val if val else None for val in row]

                                            curValues.append(tuple(newRow))

                                    cRows += 1

                            else:
                                # Import all records for cointerp
                                with open(txtPath, 'r', encoding=encoder) as tabData:
                                    rows = csv.reader(tabData, delimiter='|', quotechar='"')

                                    for row in rows:

                                        # Keep all records for cointerp table

                                        for i in colIndexes:
                                            del row[i]

                                        newRow = [val if val else None for val in row]

                                        curValues.append(tuple(newRow))

                                        cRows += 1





                            if len(curValues) > 0:
                                insertQuery = "INSERT INTO " + tbl + " " + str(tuple(fldNames)) +  " VALUES (" + ",".join(src) + ");"
                                liteCur.executemany(insertQuery, curValues)

                        except:
                            #PrintMsg(" \n" + str(row), 1)
                            errorMsg()
                            err = "Error writing line " + Number_Format(iRows, 0, True) + " from " + txtPath
                            raise MyError(err)

                    else:
                        err = "Missing tabular data file (" + txtPath + ")"
                        raise MyError(err)

            conn.commit()

            # End of table iteration
            if bArcPy:
                arcpy.SetProgressorPosition()

        theMsg = ".\tTotal processing time for tabular import: " + elapsedTime(start) + " \n "
        PrintMsg(theMsg, 0)

        time.sleep(1)

        if bArcPy:
            arcpy.ResetProgressor()
            arcpy.SetProgressorLabel("Tabular import complete")

        ##          End Table Iteration
        ##          *********************************************************************************************************
        ##          *********************************************************************************************************

        result = True

    except MyError as e:
        PrintMsg(str(e), 2)
        return result

    except sqlite3.IntegrityError as err:
        PrintMsg(".\tSQLite IntegrityError: ", 2)
        time.sleep(5)
        PrintMsg(".\t" + err.args[0], 2)
        time.sleep(5)
        return result
        #errorMsg()  # not sure if sys will report the appropriate information.

    except sqlite3.Error as err:
        PrintMsg(".\tSQLite Error: ", 2)
        time.sleep(5)
        msg = err.args[0]
        PrintMsg(".\t" + msg, 2)
        time.sleep(5)
        return result

    except:
        PrintMsg("Failed to import table: " + tbl, 1)
        errorMsg()
        return result

    finally:
        try:
            time.sleep(2)
            conn.close()
            del conn

        except:
            pass

        return result

## ===================================================================================
def DropSpatialIndex(ds, outLayerName):
    # Drop existing spatial index for layer
    # Uses OGR library for geopackage database

    try:
        PrintMsg(".\tDropping spatial index for " + outLayerName, 0)
        # Method of checking for spatial index
        time.sleep(5)
        sqlHasIndex = "SELECT HasSpatialIndex('" + outLayerName + "', 'shape')"
        results = ds.ExecuteSQL(sqlHasIndex)
        result = results[0]
        bSpatialIndex = result.GetField("HasSpatialIndex")
        #PrintMsg(".\tHasSpatialIndex: " + str(bSpatialIndex), 0)
        results = None
        #time.sleep(1)

        if bSpatialIndex:
            PrintMsg(".", 0)
            PrintMsg(".\tDisabling Spatial Index for " + outLayerName, 0)
            sqlDropIndex = "SELECT DisableSpatialIndex('" + outLayerName + "', 'shape')"
            bDropped = ds.ExecuteSQL(sqlDropIndex)
            time.sleep(0.5)

        else:
            PrintMsg(".", 0)
            PrintMsg(".\tThere is no spatial index on " + outLayerName, 0)
            #time.sleep(5)

        bSpatialIndex = None

        return True

    except MyError as e:
        # Example: raise MyError("This is an error message")
        PrintMsg(str(e), 2)
        return False

    except:
        errorMsg()
        return False

## ===================================================================================
def CreateSpatialIndex(ds, outLayerName):
    # Create spatial index on this spatial layer using Spatialite SQL
    #
    try:

        sqlCreateIndex = "SELECT CreateSpatialIndex('" + outLayerName + "', 'shape')"
        #PrintMsg(".", 0)
        PrintMsg(".", 0)
        PrintMsg(".\tBuilding spatial index for " + outLayerName, 0)
        #time.sleep(1)

        bSpatialIndex = ds.ExecuteSQL(sqlCreateIndex)
        time.sleep(0.5)

        PrintMsg(".\tFinished building spatial index for " + outLayerName, 0)

        return True

    except MyError as e:
        # Example: raise MyError("This is an error message")
        PrintMsg(str(e), 2)
        return False

    except:
        errorMsg()
        return False

## ===================================================================================
def AppendFeatures_STGeom(newDB, geogRegion, mupolyList, mulineList, mupointList, sflineList, sfpointList, sapolyList, featCnt):
    # Using combination of ESRI STGeometry library and OGR method of importing shapefiles into spatialite database.
    # Uses ESRI stgeometry_sqlite.dll that comes with ArcGIS Desktop (64-bit windows).
    #
    # Problem! sqlite3.OperationalError: no such function: GeometryConstraints
    # This appears to be a function that spatialite requires that is not included in the stgeometry_sqlite.dll
    #
    # Warning! The Python-GDAL method is extremely touchy. Any errors will usually crash Python and then ArcGIS Pro.
    #
    # Merge all spatial layers into a set of file geodatabase featureclasses
    # Compare shapefile feature count to GDB feature count
    # featCnt:  0 mupoly, 1 muline, 2 mupoint, 3 sfline, 4 sfpoint, 5 sapoly
    #
    # Using OGR to populate database with geometries requires .IsValid method and .MakeValid, at
    # least with POLYGON or MULTIPOLYGON
    #
    # --Load the ST_Geometry library on Windows.
    # SELECT load_extension(
    # 'c:\Program Files (x86)\ArcGIS\Desktop10.3\DatabaseSupport\SQLite\Windows32\stgeometry_sqlite.dll',
    # 'SDE_SQL_funcs_init'
    # );

    try:

        # Would like to figure out how to drop and create spatial indexes.
        # data_source.ExecuteSQL("SELECT CreateSpatialIndex('the_table', '{}')".format(layer.GetGeometryColumn()))
        # DisableSpatialIndex(table_name String, geom_column_name String)
        # HasSpatialIndex(‘table_name’,’geom_col_name’)

        if bArcPy:
            arcpy.ResetProgressor()

        PrintMsg(".\tBeginning spatial import using OGR driver and stgeometry_sqlite.dll", 0)

        # Open output database using ogr driver
        if newDB.endswith(".gpkg"):
            raise MyError("Currently the geopackage version is not compatible with AppendFeatures_STGeom function")
            #ogrDriver = ogr.GetDriverByName("GPKG")
            #gdal.SetConfigOption('OGR_GPKG_FOREIGN_KEY_CHECK', 'NO')  # is this still necessary?

        # Open output database using SQLite3 python library
        dbConn = sqlite3.connect(newDB)

        PrintMsg(".\tGot database connection...", 0)
        time.sleep(5)
        PrintMsg(".\tSpatialite Security setting: " + os.environ['SPATIALITE_SECURITY'], 0)

        dbConn.enable_load_extension(True)


        # with the stgeometry_sqlite dll and a spatialite5 db, I get a 'no such function, GeometryConstraints' error
        extension = "'" + os.path.join(extFolder, 'stgeometry_sqlite.dll') + "'"   # The specified procedure could not be found, but it worked with DB Braowser
        extension = "stgeometry_sqlite.dll"
        sqlExtension = "SELECT load_extension(" + extension + ");"

        #extension = os.path.join(extFolder, "spatialite400x.dll")
        #sqlExtension = "SELECT load_extension(" + extension + ");"

        #extFolder = r"C:\Program Files\Utilities\spatialite-loadable-modules-5.0.0-win-amd64"
        #extension = os.path.join(extFolder, "mod_spatialite")
        #os.environ['PATH'] = extFolder + ";" + os.environ['PATH']    # insert at beginning of path
        #sqlExtension = "SELECT load_extension(" + extension + ");"

        PrintMsg(".\tLoading extension: " + extension, 0)
        time.sleep(1)
        dbConn.execute(sqlExtension)
        #dbConn.commit()

        PrintMsg(".\tGot extension...", 0)
        #time.sleep(5)
        liteCur = dbConn.cursor()

        # Start timer to test performance of imports and spatial indexes
        start = time.time()   # start clock to measure total processing time for importing soil polygons

        # Get driver for all input shapefiles
        # Monday morning, I moved this back up to the top, before iterating through different feature types.
        shpDriver = ogr.GetDriverByName("ESRI Shapefile")

        if shpDriver is None:
            err = "Failed to get OGR inputDriver for shapefile"
            raise MyError(err)

        PrintMsg(".", 0)
        PrintMsg(".\tGot OGR shapefile driver, importing spatial data...", 0)
        time.sleep(5)
        # Currently assuming input featureclasses from Web Soil Survey are GCS WGS1984

        # Save record of soil polygon shapefiles with invalid geometry
        dBadGeometry = dict()

        # *********************************************************************
        # Merge process MUPOLYGON
        # *********************************************************************
        #
        # mupolgyon columns:     objectid, shape, areasymbol, spatialver, musym, mukey
        # soilmu_a.shp columns:  fid, shape, areasymbol, spatialver, musym, mukey
        # DropSpatialIndex function only works with OGR driver which I haven't figured out for spatialite databases.
        #
        if len(mupolyList) > 0:

            # Get information for the output layer
            #
            outLayerName = "mupolygon"

            # Drop spatial index first
            #bDropped = DropSpatialIndex(ds, outLayerName)

            #if bDropped == False:
            #    PrintMsg(".\tFailed to drop spatial index for " + outLayerName, 1)

            # Get field info from mupolygon (output layer) first
            PrintMsg(".", 0)
            PrintMsg("Appending " + str(len(mupolyList)) + " map unit polygon shapefiles to featureclass: " + outLayerName, 0)

            if bArcPy:
                arcpy.SetProgressor("step", "Appending features to " + outLayerName + " layer", 0, len(mupolyList), 1)

            #time.sleep(5)
            PrintMsg(".\tGetting " + outLayerName + " layer object from database", 0)
            #time.sleep(5)

            # Get ordered list of column names for the output featureclass
            fldInfo = GetFieldInfo(outLayerName, liteCur)
            fldNames = [fld[0] for fld in fldInfo]
            src =  len(fldNames) * ['?']       # all fields including geometry
            #src =  (len(fldNames) - 1) * ['?']  # all fields less geometry

            insertSQL = "INSERT INTO " + outLayerName + " (" + ",".join(fldNames) + ") VALUES (" +  ",".join(src) + "); "
            #insertSQL = "INSERT INTO " + outLayerName + " (" + ",".join(fldNames) + ") VALUES (" +  ",".join(src) + ", ST_MPolyFromWKB(?)); "
            #insertSQL = "INSERT INTO " + outLayerName + " (" + ",".join(fldNames) + ") VALUES (" +  ",".join(src) + ", CastToMultiPolygon(?)); "

            inputCnt = 0  # counter for total number of features processed
            layerCnt = 0  # counter for total number of shapefiles imported


            for shpFile in mupolyList:
                time.sleep(0.1)
                layerCnt += 1
                dsShape = shpDriver.Open(shpFile)
                inLayer = dsShape.GetLayer()
                tblValues = list()  # shapefile records to be writtten to mupolygon

                # Get count of input features
                featCnt = inLayer.GetFeatureCount()

                msg = ".\tAppending shapefile no. " + str(layerCnt) + " with " + Number_Format(featCnt, 0, True) + " features  (" + os.path.basename(shpFile) + ")"
                PrintMsg(msg, 0)

                if bArcPy:
                    arcpy.SetProgressorLabel(msg)
                #time.sleep(3)

                # Get input field information
                firstLayerDefn = inLayer.GetLayerDefn()
                inFldCount = firstLayerDefn.GetFieldCount()
                inFieldDefs = list()

                for i in range(inFldCount):
                    try:
                        #PrintMsg(".\tGetting input shapefile field definition for field #" + str(i))
                        #time.sleep(5)
                        inFieldDefs.append(firstLayerDefn.GetFieldDefn(i))

                    except:
                        PrintMsg("Problem getting info for field #" + str(i), 0)
                        #time.sleep(5)
                        raise MyError("Failed to get input shapefile field definition for #" + str(i))

                for inFeature in inLayer:
                    # iterate through all records in this input shapefile
                    #outFeature = ogr.Feature(outLayerDefn)
                    shpID = inFeature.GetFID()
                    geom = ogr.ForceToMultiPolygon(inFeature.GetGeometryRef())
                    #geomWKT = geom.ExportToWkt()
                    newRec = list()

                    for i, fldDef in enumerate(inFieldDefs):
                        try:
                            newRec.append(inFeature.GetField(i))

                            #fldName = outFieldNames[i]
                            #outFeature.SetField(fldName, inFeature.GetField(i))

                        except:
                            time.sleep(3)
                            raise MyError("Failed to update new record for field #" + str(i))

                    # Test geometry. SQLite database will not accept polygons that are self-intersecting
                    #
                    if geom.IsValid():
                        # Use polygon as-is
                        #outFeature.SetGeometry(geom)
                        #newRec.insert(0, geom)
                        newRec.insert(0, geom)

                    else:
                        # Buffer polygon at 0 before inserting it. Need to test MakeValid() again.
                        geomType = geom.GetGeometryName()
                        #shpID = inFeature.GetFID()
                        PrintMsg(".\t\tShapefile " + os.path.basename(shpFile) + " has invalid geometry for " + geomType.lower() + " #" + str(shpID), 0)
                        newRec.insert(0, geom.Buffer(0))
                        #outFeature.SetGeometry(geom.Buffer(0))  #
                        #outFeature.SetGeometry(geom.MakeValid())

                        if os.path.basename(shpFile) in dBadGeometry:
                            dBadGeometry[os.path.basename(shpFile)].append(shpID)

                        else:
                            dBadGeometry[os.path.basename(shpFile)] = [shpID]

                    if shpID < 10:
                        PrintMsg(str(shpID) + ". " + str(newRec), 0)

                    #tblValues.append(newRec)
                    liteCur.execute(insertSQL, newRec)

                    #outLayer.CreateFeature(outFeature)
                    #outFeature = None

                #PrintMsg(".\tInserting many records into " + outLayerName, 0)
                time.sleep(7)
                #liteCur.executemany(insertSQL, tblValues)
                conn.commit()
                # Calculate total number of input features read from all shapefiles
                # At completion, this should match final count in the output database.

                if bArcPy:
                    arcpy.SetProgressorPosition()

                inputCnt += featCnt  # add the shapefile feature count to the totalnumber processed
                inLayer = None
                dsShape = None

            #if bDropped:
                # Recreate spatial index
            #    newSpatialIndex = CreateSpatialIndex(ds, outLayerName)

            if bArcPy:
                arcpy.ResetProgressor()

            #PrintMsg(".\tGetting feature count from new " + outLayerName + " layer", 0)
            #mupolyCnt = outLayer.GetFeatureCount()
            #PrintMsg(".\tFinal output featurecount:\t" + str(mupolyCnt), 0)
            PrintMsg(".\tTotal input featurecount:\t" + str(inputCnt), 0)

            #outLayerDefn = None
            #outLayer =  None

            theMsg = ".\tTotal processing time for soil polygons " + outLayerName + ": " + elapsedTime(start)
            PrintMsg(theMsg, 0)
            PrintMsg(".\tNo spatial import actually took place. Test only", 0)

            return True


        # *********************************************************************
        # Merge process MULINE
        # *********************************************************************
        #
        if len(mulineList) > 0:

            # Get information for the output layer
            #
            # Get field info from mupolygon (output layer) first
            time.sleep(1)
            outLayerName = "muline"
            PrintMsg(".", 0)
            PrintMsg("Appending " + str(len(mulineList)) + " map unit line shapefiles to featureclass: " + outLayerName, 0)

            if bArcPy:
                arcpy.SetProgressor("step", "Appending features to " + outLayerName + " layer", 0, len(mulineList), 1)

            # Drop spatial index first
            bDropped = DropSpatialIndex(ds, outLayerName)

            outLayer = ds.GetLayerByName(outLayerName)
            outLayerDefn =  outLayer.GetLayerDefn()  #outLayer.GetFieldDefn()
            outFldCount = outLayerDefn.GetFieldCount()
            #PrintMsg(".\tCreating list of field definitions for " + outLayerName, 0)
            outFieldDefs = list()
            outFieldNames = list()

            for i in range(outFldCount):
                try:
                    outFieldDef = outLayerDefn.GetFieldDefn(i)
                    outFieldDefs.append(outFieldDef)
                    outFieldNames.append(outFieldDef.GetName())

                except:
                    time.sleep(5)
                    outLayer = None
                    ds = None
                    raise MyError("Failed to get definition for field #" + str(i))

            if len(outFieldDefs) == 0:
                raise MyError("Failed to get output field definitions")

            inputCnt = 0  # counter for total number of features processed
            layerCnt = 0  # counter for total number of shapefiles imported

            for shpFile in mulineList:
                time.sleep(1)        # crashed on shapefile number 5 or 6. No idea why. Putting in a pause.
                layerCnt += 1
                dsShape = shpDriver.Open(shpFile)
                inLayer = dsShape.GetLayer()

                # Get count of input features
                featCnt = inLayer.GetFeatureCount()

                msg = ".\tAppending shapefile no. " + str(layerCnt) + " with " + Number_Format(featCnt, 0, True) + " features  (" + os.path.basename(shpFile) + ")"
                PrintMsg(msg, 0)

                if bArcPy:
                    arcpy.SetProgressorLabel(msg)

                # Get input field information
                firstLayerDefn = inLayer.GetLayerDefn()
                inFldCount = firstLayerDefn.GetFieldCount()
                #if inFldCount != outFldCount:
                #    raise MyError("Discrepancy in field counts, input shapefile has " + str(outFldCount))
                inFieldDefs = list()

                for i in range(inFldCount):
                    try:
                        #PrintMsg(".\tGetting input shapefile field definition for field #" + str(i))
                        #time.sleep(5)
                        inFieldDefs.append(firstLayerDefn.GetFieldDefn(i))

                    except:
                        PrintMsg("Problem getting info for field #" + str(i), 0)
                        #time.sleep(5)
                        raise MyError("Failed to get input shapefile field definition for #" + str(i))

                for inFeature in inLayer:
                    # iterate through all records in this input shapefile
                    outFeature = ogr.Feature(outLayerDefn)
                    geom = inFeature.GetGeometryRef()

                    for i, fldDef in enumerate(inFieldDefs):
                        try:
                            fldName = outFieldNames[i]
                            outFeature.SetField(fldName, inFeature.GetField(i))

                        except:
                            time.sleep(3)
                            raise MyError("Failed to update new record for field #" + str(i))

                    # Test geometry. SQLite database will not accept polygons that are self-intersecting
                    #
                    if geom.IsValid():
                        # Use line geometry as-is
                        outFeature.SetGeometry(geom)
                        outLayer.CreateFeature(outFeature)
                        out

                    else:
                        # Skip invalid line geometry for now. Needs further research and testing.
                        geomType = geom.GetGeometryName()
                        shpID = inFeature.GetFID()
                        PrintMsg(".\t\tShapefile " + os.path.basename(shpFile) + " has invalid geometry for " + geomType.lower() + " #" + str(shpID), 0)
                        #outFeature.SetGeometry(geom.Buffer(0))  # outFeature.SetGeometry(geom.MakeValid())
                        #if os.path.basename(shpFile) in dBadGeometry:
                        #    dBadGeometry[os.path.basename(shpFile)].append(shpID)
                        #else:
                        #    dBadGeometry[os.path.basename(shpFile)] = [shpID]

                    # outLayer.CreateFeature(outFeature)
                    outFeature = None

                # Calculate total number of input features read from all shapefiles
                # At completion, this should match final count in the output database.

                if bArcPy:
                    arcpy.SetProgressorPosition()

                inputCnt += featCnt
                inLayer = None
                dsShape = None

            if bDropped:
                # Recreate spatial index
                newSpatialIndex = CreateSpatialIndex(ds, outLayerName)

            mulineCnt = outLayer.GetFeatureCount()
            PrintMsg(".\tFinal output featurecount:\t" + str(mulineCnt), 0)
            PrintMsg(".\tTotal input featurecount:\t" + str(inputCnt), 0)
            outLayerDefn = None
            outLayer =  None

            if bArcPy:
                arcpy.ResetProgressor()

        else:
            PrintMsg(".", 0)
            PrintMsg("Skipping mapunit lines, nothing to do...", 0)

        # *********************************************************************
        # Merge process MUPOINT
        # *********************************************************************
        #
        if len(mupointList) > 0:

            # Get information for the output layer
            #
            # Get field info from mupoint (output layer) first
            time.sleep(1)
            outLayerName = "mupoint"
            PrintMsg(".", 0)
            PrintMsg("Appending " + str(len(mupointList)) + " map unit point shapefiles to featureclass: " + outLayerName, 0)

            if bArcPy:
                arcpy.SetProgressor("step", "Appending features to " + outLayerName + " layer", 0, len(mupointList), 1)

            # Drop spatial index first
            bDropped = DropSpatialIndex(ds, outLayerName)

            outLayer = ds.GetLayerByName(outLayerName)
            outLayerDefn =  outLayer.GetLayerDefn()  #outLayer.GetFieldDefn()
            outFldCount = outLayerDefn.GetFieldCount()
            #PrintMsg(".\tCreating list of field definitions for " + outLayerName, 0)
            outFieldDefs = list()
            outFieldNames = list()

            for i in range(outFldCount):
                try:
                    outFieldDef = outLayerDefn.GetFieldDefn(i)
                    outFieldDefs.append(outFieldDef)
                    outFieldNames.append(outFieldDef.GetName())

                except:
                    time.sleep(5)
                    outLayer = None
                    ds = None
                    raise MyError("Failed to get definition for field #" + str(i))

            if len(outFieldDefs) == 0:
                raise MyError("Failed to get output field definitions")

            inputCnt = 0  # counter for total number of features processed
            layerCnt = 0  # counter for total number of shapefiles imported

            for shpFile in mupointList:
                layerCnt += 1
                dsShape = shpDriver.Open(shpFile)
                inLayer = dsShape.GetLayer()

                # Get count of input features
                featCnt = inLayer.GetFeatureCount()

                msg = ".\tAppending shapefile no. " + str(layerCnt) + " with " + Number_Format(featCnt, 0, True) + " features  (" + os.path.basename(shpFile) + ")"
                PrintMsg(msg, 0)

                if bArcPy:
                    arcpy.SetProgressorLabel(msg)

                # Get input field information
                firstLayerDefn = inLayer.GetLayerDefn()
                inFldCount = firstLayerDefn.GetFieldCount()
                #if inFldCount != outFldCount:
                #    raise MyError("Discrepancy in field counts, input shapefile has " + str(outFldCount))
                inFieldDefs = list()

                for i in range(inFldCount):
                    try:
                        #PrintMsg(".\tGetting input shapefile field definition for field #" + str(i))
                        #time.sleep(5)
                        inFieldDefs.append(firstLayerDefn.GetFieldDefn(i))

                    except:
                        PrintMsg("Problem getting info for field #" + str(i), 0)
                        #time.sleep(5)
                        raise MyError("Failed to get input shapefile field definition for #" + str(i))

                for inFeature in inLayer:
                    # iterate through all records in this input shapefile
                    outFeature = ogr.Feature(outLayerDefn)
                    geom = inFeature.GetGeometryRef()

                    for i, fldDef in enumerate(inFieldDefs):
                        try:
                            fldName = outFieldNames[i]
                            outFeature.SetField(fldName, inFeature.GetField(i))

                        except:
                            time.sleep(3)
                            raise MyError("Failed to update new record for field #" + str(i))

                    # Use point as-is
                    outFeature.SetGeometry(geom)
                    outLayer.CreateFeature(outFeature)
                    outFeature = None

                # Calculate total number of input features read from all shapefiles
                # At completion, this should match final count in the output database.
                if bArcPy:
                    arcpy.SetProgressorPosition()

                inputCnt += featCnt

                inLayer = None
                dsShape = None

            time.sleep(1)

            if bDropped:
                # Recreate spatial index
                newSpatialIndex = CreateSpatialIndex(ds, outLayerName)

            mupointCnt = outLayer.GetFeatureCount()
            PrintMsg(".\tFinal output featurecount:\t" + str(mupointCnt), 0)
            PrintMsg(".\tTotal input featurecount:\t" + str(inputCnt), 0)
            outLayerDefn = None
            outLayer =  None

            if bArcPy:
                arcpy.ResetProgressor()

        else:
            PrintMsg(".", 0)
            PrintMsg("Skipping mapunit points, nothing to do", 0)
            time.sleep(1)

        # *********************************************************************
        # Merge process FEATLINE
        # *********************************************************************
        #
        if len(sflineList) > 0:

            # Get information for the output layer
            #
            # Get field info from featline (output layer) first
            time.sleep(1)
            outLayerName = "featline"
            PrintMsg(".", 0)
            PrintMsg("Appending " + str(len(sflineList)) + " special feature line shapefiles to featureclass: " + outLayerName, 0)

            if bArcPy:
                arcpy.SetProgressor("step", "Appending features to " + outLayerName + " layer", 0, len(sflineList), 1)

            # Drop spatial index first
            bDropped = DropSpatialIndex(ds, outLayerName)

            outLayer = ds.GetLayerByName(outLayerName)
            outLayerDefn =  outLayer.GetLayerDefn()  #outLayer.GetFieldDefn()
            outFldCount = outLayerDefn.GetFieldCount()
            #PrintMsg(".\tCreating list of field definitions for " + outLayerName, 0)
            outFieldDefs = list()
            outFieldNames = list()

            for i in range(outFldCount):
                try:
                    outFieldDef = outLayerDefn.GetFieldDefn(i)
                    outFieldDefs.append(outFieldDef)
                    outFieldNames.append(outFieldDef.GetName())

                except:
                    time.sleep(5)
                    outLayer = None
                    ds = None
                    raise MyError("Failed to get definition for field #" + str(i))

            if len(outFieldDefs) == 0:
                raise MyError("Failed to get output field definitions")

            inputCnt = 0  # counter for total number of features processed
            layerCnt = 0  # counter for total number of shapefiles imported

            for shpFile in sflineList:
                layerCnt += 1
                dsShape = shpDriver.Open(shpFile)
                inLayer = dsShape.GetLayer()

                # Get count of input features
                featCnt = inLayer.GetFeatureCount()

                msg = ".\tAppending shapefile no. " + str(layerCnt) + " with " + Number_Format(featCnt, 0, True) + " features  (" + os.path.basename(shpFile) + ")"
                PrintMsg(msg, 0)

                if bArcPy:
                    arcpy.SetProgressorLabel(msg)

                # Get input field information
                firstLayerDefn = inLayer.GetLayerDefn()
                inFldCount = firstLayerDefn.GetFieldCount()
                #if inFldCount != outFldCount:
                #    raise MyError("Discrepancy in field counts, input shapefile has " + str(outFldCount))
                inFieldDefs = list()

                for i in range(inFldCount):
                    try:
                        #PrintMsg(".\tGetting input shapefile field definition for field #" + str(i))
                        #time.sleep(5)
                        inFieldDefs.append(firstLayerDefn.GetFieldDefn(i))

                    except:
                        PrintMsg("Problem getting info for field #" + str(i), 0)
                        #time.sleep(5)
                        raise MyError("Failed to get input shapefile field definition for #" + str(i))

                for inFeature in inLayer:
                    # iterate through all records in this input shapefile
                    outFeature = ogr.Feature(outLayerDefn)
                    geom = inFeature.GetGeometryRef()

                    for i, fldDef in enumerate(inFieldDefs):
                        try:
                            fldName = outFieldNames[i]
                            outFeature.SetField(fldName, inFeature.GetField(i))

                        except:
                            time.sleep(3)
                            raise MyError("Failed to update new record for field #" + str(i))

                    # Test geometry. SQLite database will not accept polygons that are self-intersecting
                    #
                    if geom.IsValid():
                        # Use line geometry as-is
                        outFeature.SetGeometry(geom)
                        outLayer.CreateFeature(outFeature)

                    else:
                        # Skip lines with bad geometry for now. Needs more testing and research.
                        geomType = geom.GetGeometryName()
                        shpID = inFeature.GetFID()
                        PrintMsg(".\t\tShapefile " + os.path.basename(shpFile) + " has invalid geometry for " + geomType.lower() + " #" + str(shpID), 0)
                        #outFeature.SetGeometry(geom.Buffer(0))  # outFeature.SetGeometry(geom.MakeValid())
                        #if os.path.basename(shpFile) in dBadGeometry:
                        #    dBadGeometry[os.path.basename(shpFile)].append(shpID)
                        #else:
                        #    dBadGeometry[os.path.basename(shpFile)] = [shpID]

                    # outLayer.CreateFeature(outFeature)
                    outFeature = None

                # Calculate total number of input features read from all shapefiles
                # At completion, this should match final count in the output database.

                if bArcPy:
                    arcpy.SetProgressorPosition()

                inputCnt += featCnt
                inLayer = None
                dsShape = None

            time.sleep(1)

            if bDropped:
                # Recreate spatial index
                newSpatialIndex = CreateSpatialIndex(ds, outLayerName)

            featlineCnt = outLayer.GetFeatureCount()
            PrintMsg(".\tFinal output featurecount:\t" + str(featlineCnt), 0)
            PrintMsg(".\tTotal input featurecount:\t" + str(inputCnt), 0)
            outLayerDefn = None
            outLayer =  None

            if bArcPy:
                arcpy.ResetProgressor()

        else:
            PrintMsg(".", 0)
            PrintMsg("Skipping special feature lines, nothing to do", 0)
            time.sleep(1)

        # *********************************************************************
        # Merge process FEATPOINT
        # *********************************************************************
        #

        if len(sfpointList) > 0:

            # Get information for the output layer
            #
            # Get field info from featpoint (output layer) first
            time.sleep(1)
            outLayerName = "featpoint"
            PrintMsg(".", 0)
            PrintMsg("Appending " + str(len(sfpointList)) + " special feature point shapefiles to featureclass: " + outLayerName, 0)

            if bArcPy:
                arcpy.SetProgressor("step", "Appending features to " + outLayerName + " layer", 0, len(sfpointList), 1)

            # Drop spatial index first
            bDropped = DropSpatialIndex(ds, outLayerName)

            #PrintMsg(".\tGetting " + outLayerName + " layer object from database", 0)
            outLayer = ds.GetLayerByName(outLayerName)
            outLayerDefn =  outLayer.GetLayerDefn()  #outLayer.GetFieldDefn()
            outFldCount = outLayerDefn.GetFieldCount()
            #PrintMsg(".\tCreating list of field definitions for " + outLayerName, 0)
            outFieldDefs = list()
            outFieldNames = list()

            for i in range(outFldCount):
                try:
                    outFieldDef = outLayerDefn.GetFieldDefn(i)
                    outFieldDefs.append(outFieldDef)
                    outFieldNames.append(outFieldDef.GetName())

                except:
                    time.sleep(5)
                    outLayer = None
                    ds = None
                    raise MyError("Failed to get definition for field #" + str(i))

            if len(outFieldDefs) == 0:
                raise MyError("Failed to get output field definitions")

            inputCnt = 0  # counter for total number of features processed
            layerCnt = 0  # counter for total number of shapefiles imported

            for shpFile in sfpointList:
                layerCnt += 1
                dsShape = shpDriver.Open(shpFile)
                inLayer = dsShape.GetLayer()

                # Get count of input features
                featCnt = inLayer.GetFeatureCount()

                msg = ".\tAppending shapefile number " + str(layerCnt) + " with " + Number_Format(featCnt, 0, True) + " features  (" + os.path.basename(shpFile) + ")"
                PrintMsg(msg, 0)

                if bArcPy:
                    arcpy.SetProgressorLabel(msg)

                # Get input field information
                firstLayerDefn = inLayer.GetLayerDefn()
                inFldCount = firstLayerDefn.GetFieldCount()
                #if inFldCount != outFldCount:
                #    raise MyError("Discrepancy in field counts, input shapefile has " + str(outFldCount))
                inFieldDefs = list()

                for i in range(inFldCount):
                    try:
                        #PrintMsg(".\tGetting input shapefile field definition for field #" + str(i))
                        #time.sleep(5)
                        inFieldDefs.append(firstLayerDefn.GetFieldDefn(i))

                    except:
                        PrintMsg("Problem getting info for field #" + str(i), 0)
                        #time.sleep(5)
                        raise MyError("Failed to get input shapefile field definition for #" + str(i))

                for inFeature in inLayer:
                    # iterate through all records in this input shapefile
                    outFeature = ogr.Feature(outLayerDefn)
                    geom = inFeature.GetGeometryRef()

                    for i, fldDef in enumerate(inFieldDefs):
                        try:
                            fldName = outFieldNames[i]
                            outFeature.SetField(fldName, inFeature.GetField(i))

                        except:
                            time.sleep(3)
                            raise MyError("Failed to update new record for field #" + str(i))

                    # I don't think point geometry needs testing?  Use feature as-is'
                    outFeature.SetGeometry(geom)
                    outLayer.CreateFeature(outFeature)
                    outFeature = None

                # Calculate total number of input features read from all shapefiles
                # At completion, this should match final count in the output database.

                if bArcPy:
                    arcpy.SetProgressorPosition()

                inputCnt += featCnt

                inLayer = None
                dsShape = None

            if bDropped:
                # Recreate spatial index
                newSpatialIndex = CreateSpatialIndex(ds, outLayerName)

            featpointCnt = outLayer.GetFeatureCount()
            PrintMsg(".\tFinal output featurecount:\t" + str(featpointCnt), 0)
            PrintMsg(".\tTotal input featurecount:\t" + str(inputCnt), 0)
            outLayerDefn = None
            outLayer =  None

            if bArcPy:
                arcpy.ResetProgressor()

        else:
            PrintMsg(".", 0)
            PrintMsg("Skipping special feature points, nothing to do", 0)


        # *********************************************************************
        # Merge process SAPOLYGON
        # *********************************************************************
        #

        if len(sapolyList) > 0:

            # Get information for the output layer
            #
            # Get field info from mupolygon (output layer) first
            time.sleep(1)
            outLayerName = "sapolygon"
            PrintMsg(".", 0)
            PrintMsg("Appending " + str(len(sapolyList)) + " survey boundary polygon shapefiles to featureclass: " + outLayerName, 0)

            if bArcPy:
                arcpy.SetProgressor("step", "Appending features to " + outLayerName + " layer", 0, len(sapolyList), 1)

            # Drop spatial index first
            bDropped = DropSpatialIndex(ds, outLayerName)

            #PrintMsg(".\tGetting " + outLayerName + " layer object from database", 0)
            outLayer = ds.GetLayerByName(outLayerName)
            outLayerDefn =  outLayer.GetLayerDefn()  #outLayer.GetFieldDefn()
            outFldCount = outLayerDefn.GetFieldCount()
            #PrintMsg(".\tCreating list of field definitions for " + outLayerName, 0)
            outFieldDefs = list()
            outFieldNames = list()

            for i in range(outFldCount):
                try:
                    outFieldDef = outLayerDefn.GetFieldDefn(i)
                    outFieldDefs.append(outFieldDef)
                    outFieldNames.append(outFieldDef.GetName())

                except:
                    time.sleep(5)
                    outLayer = None
                    ds = None
                    raise MyError("Failed to get definition for field #" + str(i))

            if len(outFieldDefs) == 0:
                raise MyError("Failed to get output field definitions")

            inputCnt = 0  # counter for total number of features processed
            layerCnt = 0  # counter for total number of shapefiles imported

            for shpFile in sapolyList:
                layerCnt += 1
                dsShape = shpDriver.Open(shpFile)
                #if dsShape is None:
                #    raise MyError("Failed to get dataset for input shapefile", 0)
                inLayer = dsShape.GetLayer()
                #if inLayer is None:
                #    raise MyError("Failed to get layer object for input shapefile", 0)
                # Get count of input features
                featCnt = inLayer.GetFeatureCount()

                msg = ".\tAppending shapefile no. " + str(layerCnt) + " with " + Number_Format(featCnt, 0, True) + " features  (" + os.path.basename(shpFile) + ")"
                PrintMsg(msg, 0)

                if bArcPy:
                    arcpy.SetProgressorLabel(msg)

                # Get input field information
                firstLayerDefn = inLayer.GetLayerDefn()
                inFldCount = firstLayerDefn.GetFieldCount()
                #if inFldCount != outFldCount:
                #    raise MyError("Discrepancy in field counts, input shapefile has " + str(outFldCount))
                inFieldDefs = list()

                for i in range(inFldCount):
                    try:
                        #PrintMsg(".\tGetting input shapefile field definition for field #" + str(i))
                        inFieldDefs.append(firstLayerDefn.GetFieldDefn(i))

                    except:
                        #PrintMsg("Problem getting info for field #" + str(i), 0)
                        raise MyError("Failed to get input shapefile field definition for #" + str(i))

                # End of input field info

                for inFeature in inLayer:
                    # iterate through all records in this input shapefile
                    #PrintMsg(".\tCreating new output record for geopackage layer", 0)
                    outFeature = ogr.Feature(outLayerDefn)
                    geom = inFeature.GetGeometryRef()

                    for i, fldDef in enumerate(inFieldDefs):
                        try:
                            fldName = outFieldNames[i]
                            outFeature.SetField(fldName, inFeature.GetField(i))

                        except:
                            time.sleep(3)
                            raise MyError("Failed to update new record for field #" + str(i))

                    # Test geometry. SQLite database will not accept polygons that are self-intersecting
                    #
                    if geom.IsValid():
                        # Use polygon as-is
                        outFeature.SetGeometry(geom)

                    else:
                        # Buffer polygon at 0 before inserting it. Need to test MakeValid() again.
                        geomType = geom.GetGeometryName()
                        shpID = inFeature.GetFID()
                        PrintMsg(".\t\tShapefile " + os.path.basename(shpFile) + " has invalid geometry for " + geomType.lower() + " #" + str(shpID), 0)
                        outFeature.SetGeometry(geom.Buffer(0))
                        # outFeature.SetGeometry(geom.MakeValid())

                        if os.path.basename(shpFile) in dBadGeometry:
                            dBadGeometry[os.path.basename(shpFile)].append(shpID)

                        else:
                            dBadGeometry[os.path.basename(shpFile)] = [shpID]


                    #outLayer.CreateFeature(outFeature)
                    #outFeature = None
                    #geom = None

                # Calculate total number of input features read from all shapefiles
                # At completion, this should match final count in the output database.

                if bArcPy:
                    arcpy.SetProgressorPosition()

                inputCnt += featCnt
                inLayer = None
                dsShape = None

            if bDropped:
                # Recreate spatial index
                newSpatialIndex = CreateSpatialIndex(ds, outLayerName)

            sapolyCnt = outLayer.GetFeatureCount()
            featpointCnt = outLayer.GetFeatureCount()
            PrintMsg(".\tFinal output featurecount:\t" + str(featpointCnt), 0)
            PrintMsg(".\tTotal input featurecount:\t" + str(inputCnt), 0)
            outLayerDefn = None
            outLayer = None

            if bArcPy:
                arcpy.ResetProgressor()

        else:
            PrintMsg("Failed to import any survey boundary shapefiles. List was empty", 1)

        ds = None

        if len(dBadGeometry) > 0:
            PrintMsg(".", 0)
            PrintMsg("Listing shapefiles with invalid geometries", 0)

            for shpFile, shpIDs in dBadGeometry.items():
                PrintMsg(".\tShapefile " + shpFile + " has " + str(len(shpIDs)) + " polygons with invalid geometry: " + str(tuple(shpIDs)), 0)

            PrintMsg(".", 0)

        return True

    except MyError as e:
        PrintMsg(str(e), 2)
        return False

    except:
        try:
            del outLayer

        except:
            pass

        #errorMsg()
        errorMsg()
        return False

## ===================================================================================
def AppendFeatures_Spatialite(newDB, geogRegion, aoiWKT, mupolyList, mulineList, mupointList, sflineList, sfpointList, sapolyList, bCompressed, dGeometryTypes):
    # Using spatialite.exe commandline to perform all spatial imports.
    # This seems to be one option for avoiding DLL Hell.
    #
    # Spatial indexes and extents are updated after all shapefiles have been imported by 'ImportShapefiles' function.

    # Here is a thread that talks about the spatialite DLL problem:
    # https://github.com/ContinuumIO/anaconda-issues/issues/10926
    #
    # SQLite Binaries: https://sqlite.org/download.html
    #
    # Spatialite drivers web page: https://gdal.org/drivers/vector/sqlite.html
    #
    # Spatialite cookbook and other documentation: http://www.gaia-gis.it/gaia-sins/spatialite-cookbook/index.html

    ## M Kennedy ESRI transformation: WGS_1984_(ITRF00)_To_NAD_1983 (approx. CORS96 version)
    ## method: coordinate frame
    ## dx = 0.9956
    ## dy = -1.9013
    ## dz = -0.5215
    ## rx = 0.025915
    ## ry = 0.009426
    ## rz = 0.0011599
    ## ds = 0.00062
    ##
    ##
    ## SELECT AsEWKT ( ST_Transform( MakePoint( 11.878056 , 43.463056, 4326 ) , 3003 , NULL ,
    ## '+proj=pipeline
    ## +step +proj=unitconvert +xy_in=deg +xy_out=rad
    ## +step +proj=push +v_3
    ## +step +proj=cart +ellps=WGS84
    ## +step +inv +proj=helmert +x=-104.1 +y=-49.1 +z=-9.9 +rx=0.971 +ry=-2.917 +rz=0.714 +s=-11.68 +convention=position_vector
    ## +step +inv +proj=cart +ellps=intl
    ## +step +proj=pop +v_3
    ## +step +proj=tmerc +lat_0=0 +lon_0=9 +k=0.9996 +x_0=1500000 +y_0=0 +ellps=intl' ));

    ### method: coordinate frame
    ##p1cf = Proj(proj='latlong', ellps='GRS80', datum='NAD83', towgs84='-0.9956,1.9013,0.5215,-0.025915,-0.009426,-0.0011599,-0.00062')
    ##
    ### method: position vector
    ##p1pv = Proj(proj='latlong', ellps='GRS80', datum='NAD83', towgs84='-0.9956,1.9013,0.5215,0.025915,0.009426,0.0011599,-0.00062')

    ## For pyproj
    ## p1pv = Proj(towgs84='-0.9956,1.9013,0.5215,0.025915,0.009426,0.0011599,-0.00062')

    try:
        result = False

        PrintMsg(".", 0)
        PrintMsg("\tImporting spatial data using function: AppendFeatures_Spatialite...", 0)

        outputSRID, outputCSR = SetOutputSRID(geogRegion, newDB)  # EPSG CODE (integer)


        if bArcPy:
            arcpy.ResetProgressor()
            arcpy.SetProgressor("step", "Importing shapefiles...", 1, 5)

        # Start timer to test performance of imports and spatial indexes
        start = time.time()   # start clock to measure total processing time for importing spatial data

        # Save record of soil polygon shapefiles with invalid geometry
        #dBadGeometry = dict()

        # Create file to contain sql for spatial indexes
        indexFile = str(os.path.join(tmpFolder, "spatial_indexes.sql"))
        fh = open(indexFile, 'w')
        fh.write("-- Creating spatial indexes for " + newDB)
        fh.close()


        # *********************************************************************
        # Merge process MUPOLYGON
        # *********************************************************************
        #
        fldList = ["areasymbol", "spatialver", "musym", "mukey"]

        if len(mupolyList) > 0:

            # Get information for the output layer
            #
            outLayerName = "mupolygon"
            geomType = dGeometryTypes[outLayerName]

            if bArcPy:
                arcpy.SetProgressorLabel("Importing " + Number_Format(len(mupolyList), 0, True) + " shapefiles into " + outLayerName)

            bImported = ImportShapefiles_Valid(newDB, outputSRID, aoiWKT, outLayerName, mupolyList, fldList, geomType, bCompressed)

            if bImported:
                if bArcPy:
                    arcpy.SetProgressorPosition(1)

            else:
                raise MyError("Failure during '" + outLayerName + "' spatial import")

        # *********************************************************************
        # Merge process MULINE
        # *********************************************************************
        # mupolyList, mulineList, mupointList, sflineList, sfpointList, sapolyList
        if len(mulineList) > 0:

            # Get information for the output layer
            #
            outLayerName = "muline"
            geomType = dGeometryTypes[outLayerName]

            if bArcPy:
                arcpy.SetProgressorLabel("Importing " + Number_Format(len(mulineList), 0, True) + " shapefiles into " + outLayerName)

            bImported = ImportShapefiles_Valid(newDB, outputSRID, aoiWKT, outLayerName, mulineList, fldList, geomType, bCompressed)

            if bImported:
                if bArcPy:
                    arcpy.SetProgressorPosition(2)

            else:
                raise MyError("Failure during '" + outLayerName + "' spatial import")

        # *********************************************************************
        # Merge process MUPOINT
        # *********************************************************************
        # mupolyList, mulineList, mupointList, sflineList, sfpointList, sapolyList
        if len(mupointList) > 0:

            # Get information for the output layer
            #
            outLayerName = "mupoint"
            geomType = dGeometryTypes[outLayerName]

            if bArcPy:
                arcpy.SetProgressorLabel("Importing " + Number_Format(len(mupointList), 0, True) + " shapefiles to build " + outLayerName)

            bImported = ImportShapefiles_Valid(newDB, outputSRID, aoiWKT, outLayerName, mupointList, fldList, geomType, bCompressed)

            if bImported:
                if bArcPy:
                    arcpy.SetProgressorPosition(2)

            else:
                raise MyError("Failure during '" + outLayerName + "' spatial import")

        # *********************************************************************
        # Merge process FEATLINE
        # *********************************************************************
        # mupolyList, mulineList, mupointList, sflineList, sfpointList, sapolyList
        fldList = ["areasymbol", "spatialver", "featsym", "featkey"]

        if len(sflineList) > 0:

            # Get information for the output layer
            #
            outLayerName = "featline"
            geomType = dGeometryTypes[outLayerName]

            if bArcPy:
                arcpy.SetProgressorLabel("Importing " + Number_Format(len(sflineList), 0, True) + " shapefiles into " + outLayerName)

            bImported = ImportShapefiles_Valid(newDB, outputSRID, aoiWKT, outLayerName, sflineList, fldList, geomType, bCompressed)

            if bImported:
                if bArcPy:
                    arcpy.SetProgressorPosition(3)

            else:
                raise MyError("Failure during '" + outLayerName + "' spatial import")

        # *********************************************************************
        # Merge process FEATPOINT
        # *********************************************************************
        # mupolyList, mulineList, mupointList, sflineList, sfpointList, sapolyList
        if len(sfpointList) > 0:

            # Get information for the output layer
            #
            outLayerName = "featpoint"
            geomType = dGeometryTypes[outLayerName]

            if bArcPy:
                arcpy.SetProgressorLabel("Importing " + Number_Format(len(sfpointList), 0, True) + " shapefiles into " + outLayerName)

            bImported = ImportShapefiles_Valid(newDB, outputSRID, aoiWKT, outLayerName, sfpointList, fldList, geomType, bCompressed)

            if bImported:
                if bArcPy:
                    arcpy.SetProgressorPosition(4)

            else:
                raise MyError("Failure during '" + outLayerName + "' spatial import")

        # *********************************************************************
        # Merge process SAPOLYGON
        # *********************************************************************
        # mupolyList, mulineList, mupointList, sflineList, sfpointList, sapolyList
        fldList = ["areasymbol", "spatialver", "lkey"]

        if len(sapolyList) > 0:

            # Get information for the output layer
            #
            outLayerName = "sapolygon"
            geomType = dGeometryTypes[outLayerName]

            if bArcPy:
                arcpy.SetProgressorLabel("Importing " + Number_Format(len(sapolyList), 0, True) + " shapefiles into " + outLayerName)

            bImported = ImportShapefiles_Valid(newDB, outputSRID, aoiWKT, outLayerName, sapolyList, fldList, geomType, bCompressed)

            if bImported:
                if bArcPy:
                    arcpy.SetProgressorPosition(5)

            else:
                raise MyError("Failure during '" + outLayerName + "' spatial import")

        # PrintMsg(".", 0)
        # PrintMsg(".\tSpatial import process complete...", 0)
        theMsg = ".\tProcessing time for spatial import using Spatialite scripts: " + elapsedTime(start)

        if bArcPy:
            arcpy.SetProgressorLabel("Finished importing spatial layers")

        PrintMsg(theMsg, 0)

        result = True
        return result

    except MyError as e:
        PrintMsg(str(e), 2)
        return result

    except:
        errorMsg()
        return result

## ===================================================================================
def AppendFeatures_OGR(newDB, dbType, geogRegion, mupolyList, mulineList, mupointList, sflineList, sfpointList, sapolyList, featCnt):
    # Using ogr2ogr.exe commandline to perform all spatial imports. Hardcode path in this implementation,
    # similar to how I'm using spatialite.exe.

    try:
        result = False

        PrintMsg(".", 0)
        PrintMsg("\tImporting spatial data using function: AppendFeatures_OGR...", 0)
        PrintMsg(".", 0)
        PrintMsg("\tWarning! Spatial indexes not being dropped when using function: AppendFeatures_OGR...", 0)

        outputSRID, outputCSR = SetOutputSRID(geogRegion, newDB)  # EPSG CODE (integer)

        if bArcPy:
            arcpy.ResetProgressor()
            arcpy.SetProgressor("step", "Importing shapefiles...", 1, 5)

        # Start timer to test performance of imports and spatial indexes
        start = time.time()   # start clock to measure total processing time for importing spatial data

        # *********************************************************************
        # Merge process MUPOLYGON
        # *********************************************************************
        #
        fldList = ["areasymbol", "spatialver", "musym", "mukey"]

        if len(mupolyList) > 0:

            # Get information for the output layer
            #
            outLayerName = "mupolygon"
            geomType = "POLYGON"

            if bArcPy:
                arcpy.SetProgressorLabel("Importing " + Number_Format(len(mupolyList), 0, True) + " shapefiles to build " + outLayerName)

            #PrintMsg(".\tGeometry is being validated...", 0)

            if dbType == 'gpkg':
                bImported = ImportShapefiles_OgrGP(newDB, outputSRID, outLayerName, mupolyList, fldList, geomType)

            elif dbType == 'spatialite':
                bImported = ImportShapefiles_OgrSL(newDB, outputSRID, aoiWKT, outLayerName, mupolyList, fldList, geomType)

            else:
                bImported = False

            if bImported:
                if bArcPy:
                    arcpy.SetProgressorPosition(1)

            else:
                raise MyError("Failure during '" + outLayerName + "' spatial import")

        # *********************************************************************
        # Merge process MULINE
        # *********************************************************************
        # mupolyList, mulineList, mupointList, sflineList, sfpointList, sapolyList
        if len(mulineList) > 0:

            # Get information for the output layer
            #
            outLayerName = "muline"
            geomType = "LINE"

            if bArcPy:
                arcpy.SetProgressorLabel("Importing " + Number_Format(len(mulineList), 0, True) + " shapefiles to build " + outLayerName)

            if dbType == 'gpkg':
                bImported = ImportShapefiles_OgrGP(newDB, outputSRID, outLayerName, mulineList, fldList, geomType)

            elif dbType == 'spatialite':
                bImported = ImportShapefiles_OgrSL(newDB, outputSRID, aoiWKT, outLayerName, mulineList, fldList, geomType)

            else:
                bImported = False

            if bImported:
                if bArcPy:
                    arcpy.SetProgressorPosition(2)

            else:
                raise MyError("Failure during '" + outLayerName + "' spatial import")

        # *********************************************************************
        # Merge process MUPOINT
        # *********************************************************************
        # mupolyList, mulineList, mupointList, sflineList, sfpointList, sapolyList
        if len(mupointList) > 0:

            # Get information for the output layer
            #
            outLayerName = "mupoint"
            geomType = "LINE"
            #arcpy.SetProgressorLabel("Importing shapefiles to " + outputLayerName)

            if bArcPy:
                arcpy.SetProgressorLabel("Importing " + Number_Format(len(mupointList), 0, True) + " shapefiles to build " + outLayerName)

            if dbType == 'gpkg':
                bImported = ImportShapefiles_OgrGP(newDB, outputSRID, outLayerName, mupointList, fldList, geomType)

            elif dbType == 'spatialite':
                bImported = ImportShapefiles_OgrSL(newDB, outputSRID, aoiWKT, outLayerName, mupointList, fldList, geomType)

            else:
                bImported = False

            if bImported:
                if bArcPy:
                    arcpy.SetProgressorPosition(2)

            else:
                raise MyError("Failure during '" + outLayerName + "' spatial import")

        # *********************************************************************
        # Merge process FEATLINE
        # *********************************************************************
        # mupolyList, mulineList, mupointList, sflineList, sfpointList, sapolyList
        fldList = ["areasymbol", "spatialver", "featsym", "featkey"]

        if len(sflineList) > 0:

            # Get information for the output layer
            #
            outLayerName = "featline"
            geomType = "LINE"

            if bArcPy:
                arcpy.SetProgressorLabel("Importing " + Number_Format(len(sflineList), 0, True) + " shapefiles to build " + outLayerName)

            if dbType == 'gpkg':
                bImported = ImportShapefiles_OgrGP(newDB, outputSRID, outLayerName,sflineList , fldList, geomType)

            elif dbType == 'spatialite':
                bImported = ImportShapefiles_OgrSL(newDB, outputSRID, aoiWKT, outLayerName, sflineList, fldList, geomType)

            else:
                bImported = False

            if bImported:
                if bArcPy:
                    arcpy.SetProgressorPosition(3)

            else:
                raise MyError("Failure during '" + outLayerName + "' spatial import")

        # *********************************************************************
        # Merge process FEATPOINT
        # *********************************************************************
        # mupolyList, mulineList, mupointList, sflineList, sfpointList, sapolyList
        if len(sfpointList) > 0:

            # Get information for the output layer
            #
            outLayerName = "featpoint"
            geomType = "POINT"

            if bArcPy:
                arcpy.SetProgressorLabel("Importing " + Number_Format(len(sfpointList), 0, True) + " shapefiles to build " + outLayerName)

            if dbType == 'gpkg':
                bImported = ImportShapefiles_OgrGP(newDB, outputSRID, outLayerName, sfpointList, fldList, geomType)

            elif dbType == 'spatialite':
                bImported = ImportShapefiles_OgrSL(newDB, outputSRID, aoiWKT, outLayerName, sfpointList, fldList, geomType)

            else:
                bImported = False

            if bImported:
                if bArcPy:
                    arcpy.SetProgressorPosition(4)

            else:
                raise MyError("Failure during '" + outLayerName + "' spatial import")

        # *********************************************************************
        # Merge process SAPOLYGON
        # *********************************************************************
        # mupolyList, mulineList, mupointList, sflineList, sfpointList, sapolyList
        fldList = ["areasymbol", "spatialver", "lkey"]

        if len(sapolyList) > 0:

            # Get information for the output layer
            #
            outLayerName = "sapolygon"
            geomType = "POLYGON"

            if bArcPy:
                arcpy.SetProgressorLabel("Importing " + Number_Format(len(sapolyList), 0, True) + " shapefiles to build " + outLayerName)

            if dbType == 'gpkg':
                bImported = ImportShapefiles_OgrGP(newDB, outputSRID, outLayerName, sapolyList, fldList, geomType)

            elif dbType == 'spatialite':
                bImported = ImportShapefiles_OgrSL(newDB, outputSRID, aoiWKT, outLayerName, sapolyList, fldList, geomType)

            else:
                bImported = False

            if bImported:
                if bArcPy:
                    arcpy.SetProgressorPosition(5)

            else:
                raise MyError("Failure during '" + outLayerName + "' spatial import")

        # PrintMsg(".", 0)
        #PrintMsg("Spatial import process complete...", 0)
        theMsg = ".\tProcessing time for spatial import using ogr2ogr scripts: " + elapsedTime(start)
        PrintMsg(theMsg, 0)

        result = True
        return result

    except MyError as e:
        PrintMsg(str(e), 2)
        return result

    except:
        errorMsg()
        return result

## ===================================================================================
def AppendFeatures_ArcPy(newDB, geogRegion, mupolyList, mulineList, mupointList, sflineList, sfpointList, sapolyList, featCnt):
    # Purely arcpy (Append_management) method for importing shapefiles. Works well in the ArcGIS Pro environment
    #
    # Merge all spatial layers into a set of file geodatabase featureclasses
    # Compare shapefile feature count to GDB feature count
    # featCnt:  0 mupoly, 1 muline, 2 mupoint, 3 sfline, 4 sfpoint, 5 sapoly

    # BIG QUESTION FOR spatialite/st_geometry databases. Do I need to build RTree spatial indexes here?
    # If so, what tool or command. ESRI or the ST_Geometry library?
    #
    # Another big question. Can I get rid of arcpy and use open source to replace the Append Tool?
    #
    # The gpkg version of my template databases need updated constraints.
    # The spatialite version of template that still works is the template_spatialiteguid_06.sqlite.
    #
    try:

        # Set output workspace

        # Put datum transformation methods in place
        #geogRegion = "CONUS"
        PrintMsg(".", 0)
        PrintMsg(".\tImporting spatial data using AppendFeatures_ArcPy function...", 0)
        time.sleep(1)

        if bArcPy:
            arcpy.ResetProgressor()

        start = time.time()   # start clock to measure total processing time for importing

        # Assuming input featureclasses from Web Soil Survey are GCS WGS1984 and that
        # output datum is either NAD 1983 or WGS 1984. Output coordinate system will be
        # defined by the existing output featureclass.

        #if not arcpy.Exists(os.path.join(newDB, "mupolygon")):
        #    raise MyError(".\tOutput not found (" + os.path.join(newDB, "mupolygon") + ")")

        # Merge process MUPOLYGON
        if len(mupolyList) > 0:
            PrintMsg(".", 0)
            PrintMsg(".\tAppending " + str(len(mupolyList)) + " soil mapunit polygon shapefiles to featureclass: " + "MUPOLYGON", 0)

            arcpy.SetProgressorLabel("Appending features to MUPOLYGON layer")

            arcpy.Append_management(mupolyList,  os.path.join(newDB, "mupolygon"), "NO_TEST")
            mupolyCnt = int(arcpy.GetCount_management(os.path.join(newDB, "mupolygon")).getOutput(0))
            time.sleep(1)

            if mupolyCnt != featCnt[0]:
                time.sleep(5)
                err = "MUPOLYGON short count"
                raise MyError(err)

            # PrintMsg(".\tAppend completed...", 0)
            time.sleep(1)

        # Merge process MULINE
        if len(mulineList) > 0:
            PrintMsg(".", 0)
            PrintMsg(".\tAppending " + str(len(mulineList)) + " soil mapunit line shapefiles to featureclass: " + "MULINE", 0)
            arcpy.SetProgressorLabel("Appending features to MULINE layer")
            arcpy.Append_management(mulineList,  os.path.join(newDB, "muline"), "NO_TEST")
            mulineCnt = int(arcpy.GetCount_management(os.path.join(newDB, "muline")).getOutput(0))

            if mulineCnt != featCnt[1]:
                time.sleep(1)
                err = "MULINE short count"
                raise MyError(err)

        # Merge process MUPOINT
        if len(mupointList) > 0:
            PrintMsg(".", 0)
            PrintMsg(".\tAppending " + str(len(mupointList)) + " soil mapunit point shapefiles to featureclass: " + "MUPOINT", 0)
            arcpy.SetProgressorLabel("Appending features to MUPOINT layer")
            arcpy.Append_management(mupointList,  os.path.join(newDB, "mupoint"), "NO_TEST")
            mupointCnt = int(arcpy.GetCount_management(os.path.join(newDB, "mupoint")).getOutput(0))

            if mupointCnt != featCnt[2]:
                time.sleep(1)
                err = "MUPOINT short count"
                raise MyError(err)

            # Add indexes
            arcpy.AddSpatialIndex_management (os.path.join(newDB, "MUPOINT"))
            #arcpy.AddIndex_management(os.path.join(newDB, "MUPOINT"), "AREASYMBOL", "Indx_MupointAreasymbol")

        # Merge process FEATLINE
        if len(sflineList) > 0:
            PrintMsg(".", 0)
            PrintMsg(".\tAppending " + str(len(sflineList)) + " special feature line shapefiles to featureclass: " + "FEATLINE", 0)
            arcpy.SetProgressorLabel("Appending features to FEATLINE layer")
            arcpy.Append_management(sflineList,  os.path.join(newDB, "featline"), "NO_TEST")
            sflineCnt = int(arcpy.GetCount_management(os.path.join(newDB, "featline")).getOutput(0))

            if sflineCnt != featCnt[3]:
                time.sleep(1)
                err = "FEATLINE short count"
                raise MyError(err)

        # Merge process FEATPOINT
        if len(sfpointList) > 0:
            PrintMsg(".", 0)
            PrintMsg(".\tAppending " + str(len(sfpointList)) + " special feature point shapefiles to featureclass: " + "FEATPOINT", 0)
            arcpy.SetProgressorLabel("Appending features to FEATPOINT layer")
            arcpy.Append_management(sfpointList,  os.path.join(newDB, "featpoint"), "NO_TEST")
            sfpointCnt = int(arcpy.GetCount_management(os.path.join(newDB, "featpoint")).getOutput(0))

            if sfpointCnt != featCnt[4]:
                PrintMsg(" \nExported " + str(sfpointCnt) + " points to geodatabase", 1)
                time.sleep(1)
                err = "FEATPOINT short count"
                raise MyError(err)

        # Merge process SAPOLYGON
        if len(sapolyList) > 0:
            PrintMsg(".", 0)
            PrintMsg(".\tAppending " + str(len(sapolyList)) + " survey boundary shapefiles to featureclass: " + "SAPOLYGON", 0)
            #PrintMsg("sapolyList: " + str(sapolyList), 0)
            #time.sleep(3)
            arcpy.SetProgressorLabel("Appending features to SAPOLYGON layer")

            PrintMsg(".", 0)
            #time.sleep(10)

            arcpy.Append_management(sapolyList,  os.path.join(newDB, "sapolygon"), "NO_TEST")

            # PrintMsg(".\tSkipping sapolygon feature count", 0)
            #time.sleep(5)
            sapolyCnt = int(arcpy.GetCount_management(os.path.join(newDB, "sapolygon")).getOutput(0))

            if sapolyCnt != featCnt[5]:
                #PrintMsg("??? Imported " + Number_Format(sapolyCnt, 0, True) + " polygons from shapefile", 0)
                PrintMsg(".\tMismatch. Shapefiles had " + Number_Format(featCnt[5], 0, True) + " polygons and output SAPOLYGON has " + Number_Format(sapolyCnt, 0, True) + " polygons", 0)
                time.sleep(1)
                err = "SAPOLYGON short count"
                raise MyError(err)

        PrintMsg("Successfully imported all spatial data to new database", 0)
        theMsg = ".\tTotal processing time for all spatial data: " + elapsedTime(start)
        PrintMsg(theMsg, 0)

        return True

    except MyError as e:
        PrintMsg(str(e), 2)
        return False

    except:
        PrintMsg(".\tException condition in AppendFeatures_ArcPy", 2)
        time.sleep(2)
        errorMsg()
        return False

## ===================================================================================
def ImportShapefiles_OgrSL(newDB, outputSRID, aoiWKT, outLayerName, shapeList, fldList, geomType):
    # Testing ogr2ogr commandline for shapefile import into a spatialite database.
    #
    # Called by 'AppendFeatures_Spatialite'
    # https://gdal.org/programs/ogr2ogr.html

    #

    # How do I determine spatial storage method used for this database? Geopackage vs. Spatialite?
    # a. A geopackage database has a 'gpkg_contents' table
    # b. A spatialite database has a 'geometry_columns' table

    # ogr2ogr arguments:
    # -f "SQLite" ?
    # -append
    # -dialect "Spatialite" ?
    # -geomfield ?
    # -t_srs (reproject on import)
    # -s_srs (shapefile srs should not be needed)
    # target dataset and source shapefile (not sure
    # -nlt type|PROMOTE_TO_MULTI
    # -makevalid
    # -nln ? (new layer name, but will this work for an existing layer name?)
    # -lco SPATIALINDEX=yes ?
    # -dsco SPATIALITE=yes ?

    # Working example from command-line test:
    # C:\Program Files\Utilities\osgeo4w\bin>ogr2ogr.exe -f GPKG -append -makevalid -nln mupolygon -nlt PROMOTE_TO_MULTI C:/Geodata/SQLite_Tests/template_14.gpkg E:/Geodata_E/SSURGO_Downloads1/soil_al003/spatial/soilmu_a_al003.shp

    # ogrExe
    # "-f"
    # "GPKG"
    # "-append"
    # "-makevalid"
    # "-nln"
    # outLayerName
    # "-nlt"
    # "PROMOTE_TO_MULTI"
    # newDB (fix path delimiter?)
    # srcShp

    try:
        # Need to look at o4w_env.bat and possibly run that to set the environment.
        # Another likely problem is that running subprocess isn't able to find those environmental variable settings?
        #
        ogrExe = "C:/Program Files/Utilities/osgeo4w/bin/ogr2ogr.exe"
        os.environ["PROJ_LIB"] = "C:/Program Files/Utilities/osgeo4w\bin"

        # Create corresponding list of field names for the virtual shapefile.
        # These tables use pkuid and geometry instead of objectid and shape.
        # Get field info from mupolygon (output layer) first
        #PrintMsg(".", 0)
        PrintMsg("Assembling geopackage using ogr2ogr with Spatialite database: " + outLayerName, 0)

        CREATE_NO_WINDOW = 0x08000000 # for subprocess, don't show window
        subprocess.CREATE_NO_WINDOW

        shpEncoding = "CP1252"
        inputSRID = 4326
        geomFld = "shape"
        dbTxt = newDB.replace("\\", "/")

        # Unprojected vs. Projected shapefile import
        if outputSRID == inputSRID:

            # No projection required. Probably both are 4326 (GCS WGS1984)
            #PrintMsg(".\t\tNo projection required when output SRID = '" + str(outputSRID) + "'", 0)

            if geomType == "POLYGON":
                for shpFile in shapeList:
                    # create query used to import shapefile to virtual table, then copy to target geometry table
                    # assumes that the column names and sequence are the same for both
                    PrintMsg(".\tImporting " + shpFile, 0)
                    srcShp = shpFile.replace("\\", "/")
                    shpImport = [ogrExe, "-f", "SQLite", "-dialect", "Spatialite", "-append", "-makevalid", "-nln", outLayerName, "-nlt", "PROMOTE_TO_MULTI", newDB, srcShp]
                    result = subprocess.Popen(shpImport, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell=True)
                    stdout, stderr = result.communicate()
                    exit_code = result.wait(timeout=300)

                    if exit_code == 1:
                        PrintMsg(".\tSingle ogr2ogr exit_code: " + str(exit_code), 1)
                        PrintMsg(str(stderr.decode('ascii')), 1)
                        return False

            else:
                # Not polygon shapefile, so no casting to multipolygon or validating geometry
                for shpFile in shapeList:
                    # create query used to import shapefile to virtual table, then copy to target geometry table
                    # assumes that the column names and sequence are the same for both
                    srcShp = shpFile.replace("\\", "/")
                    PrintMsg(".\tImporting " + shpFile, 0)
                    shpImport = [ogrExe, "-f", "SQLite", "-dialect", "Spatialite", "-append", "-nln", outLayerName, newDB, srcShp]
                    result = subprocess.Popen(shpImport, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell=True)
                    stdout, stderr = result.communicate()
                    exit_code = result.wait(timeout=300)

                    if exit_code == 1:
                        PrintMsg(".\tSingle ogr2ogr exit_code: " + str(exit_code), 1)
                        PrintMsg(str(stderr.decode('ascii')), 1)
                        return False

        else:
            # Projection required, includes AOI for use in transformation
            #
            # Not yet implemented for ogr2ogr
            PrintMsg(".\tOgr2Ogr shapefile import has not yet implemented transformations", 0)


            if geomType == "POLYGON":
                for shpFile in shapeList:
                    # create query used to import shapefile to virtual table, then copy to target geometry table
                    # assumes that the column names and sequence are the same for both
                    PrintMsg(".\tImporting " + shpFile, 0)
                    srcShp = shpFile.replace("\\", "/")
                    shpImport = [ogrExe, "-f", "SQLite", "-dialect", "Spatialite", "-append", "-makevalid", "-nln", outLayerName, "-nlt", "PROMOTE_TO_MULTI", newDB, srcShp]
                    result = subprocess.Popen(shpImport, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell=True)
                    stdout, stderr = result.communicate()
                    exit_code = result.wait(timeout=300)

                    if exit_code == 1:
                        PrintMsg(".\tSingle ogr2ogr exit_code: " + str(exit_code), 1)
                        PrintMsg(str(stderr.decode('ascii')), 1)
                        return False

            else:
                # Not polygon shapefile, so no casting to multipolygon or validating geometry
                for shpFile in shapeList:
                    # create query used to import shapefile to virtual table, then copy to target geometry table
                    # assumes that the column names and sequence are the same for both
                    srcShp = shpFile.replace("\\", "/")
                    PrintMsg(".\tImporting " + shpFile, 0)
                    shpImport = [ogrExe, "-f", "SQLite", "-dialect", "Spatialite", "-append", "-nln", outLayerName, newDB, srcShp]
                    result = subprocess.Popen(shpImport, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell=True)
                    stdout, stderr = result.communicate()
                    exit_code = result.wait(timeout=300)

                    if exit_code == 1:
                        PrintMsg(".\tSingle ogr2ogr exit_code: " + str(exit_code), 1)
                        PrintMsg(str(stderr.decode('ascii')), 1)
                        return False

        return True

    except MyError as e:
        PrintMsg(str(e), 2)
        return False

    except:
        PrintMsg(".\tException condition in AppendFeatures_Ogr2Ogr", 2)
        time.sleep(2)
        errorMsg()
        return False

## ===================================================================================

def ImportShapefiles_OgrGP(newDB, outputSRID, outLayerName, shapeList, fldList, geomType):
    # Testing ogr2ogr commandline for shapefile import into a Geopackage database

    # https://gdal.org/programs/ogr2ogr.html

    # This function appears to work well with geopackage.
    #
    # ogr2ogr arguments:
    # -f "SQLite" ?
    # -append
    # -dialect "Spatialite" ?
    # -geomfield ?
    # -t_srs (reproject on import)
    # -s_srs (shapefile srs should not be needed)
    # target dataset and source shapefile (not sure
    # -nlt type|PROMOTE_TO_MULTI
    # -makevalid
    # -nln ? (new layer name, but will this work for an existing layer name?)
    # -lco SPATIALINDEX=yes ?
    # -dsco SPATIALITE=yes ?

    # Working example from command-line test:
    # C:\Program Files\Utilities\osgeo4w\bin>ogr2ogr.exe -f GPKG -append -makevalid -nln mupolygon -nlt PROMOTE_TO_MULTI C:/Geodata/SQLite_Tests/template_14.gpkg E:/Geodata_E/SSURGO_Downloads1/soil_al003/spatial/soilmu_a_al003.shp

    # ogrExe
    # "-f"
    # "GPKG"
    # "-append"
    # "-makevalid"
    # "-nln"
    # outLayerName
    # "-nlt"
    # "PROMOTE_TO_MULTI"
    # newDB (fix path delimiter?)
    # srcShp



    try:
        #ogrExe = "C:/Program Files/Utilities/osgeo4w/bin/ogr2ogr.exe" # works
        #ogrExe = r"C:\Users\Steve.Peaslee\Documents\GIS\Python\SSURGOLite_Tools\Osgeo4W\bin\ogr2ogr.exe" # works
        ogrExe = os.path.join(basePath, r"Osgeo4W\bin\ogr2ogr.exe")  # works with all of the Osgeo4w files from downloaded version

        #ogrExe = os.path.join(basePath, r"OGR\bin\ogr2ogr.exe")  # test reduced version


        # Create corresponding list of field names for the virtual shapefile.
        # These tables use pkuid and geometry instead of objectid and shape.
        # Get field info from mupolygon (output layer) first
        PrintMsg(".", 0)
        PrintMsg("Using ogr2ogr to import shapefiles for a Geopackage database: " + outLayerName, 0)

        CREATE_NO_WINDOW = 0x08000000 # for subprocess, don't show window
        subprocess.CREATE_NO_WINDOW

        shpEncoding = "CP1252"
        inputSRID = 4326
        geomFld = "shape"
        dbTxt = newDB.replace("\\", "/")
        PrintMsg(".\tTarget database: " + dbTxt, 0)

        # Unprojected vs. Projected shapefile import
        if outputSRID == inputSRID:

            # No projection required. Probably both are 4326 (GCS WGS1984)
            #PrintMsg(".\t\tNo projection required when output SRID = '" + str(outputSRID) + "'", 0)

            if geomType == "POLYGON":
                for shpFile in shapeList:
                    # create query used to import shapefile to virtual table, then copy to target geometry table
                    # assumes that the column names and sequence are the same for both

                    srcShp = shpFile.replace("\\", "/")
                    PrintMsg(".\tImporting " + srcShp, 0)
                    #shpImport = [ogrExe, "-f", "GPKG", "-append", "-makevalid", "-nln", outLayerName, "-nlt", "PROMOTE_TO_MULTI", newDB, srcShp]
                    shpImport = [ogrExe, "-f", "GPKG", "-append", "-makevalid", "-nln", outLayerName, "-nlt", "PROMOTE_TO_MULTI", dbTxt, srcShp]
                    result = subprocess.Popen(shpImport, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell=True)
                    stdout, stderr = result.communicate()
                    exit_code = result.wait(timeout=300)

                    if exit_code == 1:
                        PrintMsg(".\tSingle ogr2ogr exit_code: " + str(exit_code), 1)
                        PrintMsg(str(stderr.decode('ascii')), 1)
                        return False

            else:
                # Not polygon shapefile, so no casting to multipolygon or validating geometry
                for shpFile in shapeList:
                    # create query used to import shapefile to virtual table, then copy to target geometry table
                    # assumes that the column names and sequence are the same for both
                    srcShp = shpFile.replace("\\", "/")
                    PrintMsg(".\tImporting " + srcShp, 0)
                    #shpImport = [ogrExe, "-f", "GPKG", "-append", "-nln", outLayerName, newDB, srcShp]
                    shpImport = [ogrExe, "-f", "GPKG", "-append", "-nln", outLayerName, dbTxt, srcShp]
                    result = subprocess.Popen(shpImport, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell=True)
                    stdout, stderr = result.communicate()
                    exit_code = result.wait(timeout=300)

                    if exit_code == 1:
                        PrintMsg(".\tSingle ogr2ogr exit_code: " + str(exit_code), 1)
                        PrintMsg(str(stderr.decode('ascii')), 1)
                        return False

        else:
            # Projection required, includes AOI for use in transformation
            #
            # Not yet implemented for ogr2ogr

            for shpFile in shapeList:
                # create query used to import shapefile to virtual table, then copy to target geometry table
                # assumes that the column names and sequence are the same for both
                # Tries to add the AOI geometry as an argument to the ST_Transform, which is supposed to improve the datum transformation. Not seeing it though...
                srcShp = shpFile.replace("\\", "/")

        return True

    except MyError as e:
        PrintMsg(str(e), 2)
        return False

    except:
        PrintMsg(".\tException condition in AppendFeatures_Ogr2Ogr", 2)
        time.sleep(2)
        errorMsg()
        return False

## ===================================================================================
def ImportShapefiles(newDB, outputSRID, aoiWKT, outLayerName, shapeList, fldList, geomType):
    # Called by 'AppendFeatures_Spatialite'
    # Copy features from a list of shapefiles to a spatialite geometry table
    # Please Note! This function was developed using Spatialite 5.0.0 commandline which includes PROJ 7.1.0.
    # Need to look at newer methods for handling geographic transformations
    # Probably should incorporate a query that checks PROJ version
    #
    # Possible use for GeoJSON: https://datatracker.ietf.org/doc/html/rfc7946#section-3.1.6
    # GeomFromGeoJSON

    try:
        tmpShp = "xx_" + outLayerName

        slExe = os.path.join(os.path.join(basePath, "Support"), "spatialite.exe")
        # PrintMsg(".\tslExe: " + slExe, 0)

        # Create corresponding list of field names for the virtual shapefile.
        # These tables use pkuid and geometry instead of objectid and shape.
        # Get field info from mupolygon (output layer) first
        #PrintMsg(".", 0)
        #PrintMsg("Assembling Spatialite commands needed to create new featureclass: " + outLayerName, 0)

        CREATE_NO_WINDOW = 0x08000000 # for subprocess, don't show window
        subprocess.CREATE_NO_WINDOW
        tmpFolder = os.environ["TEMP"]

        #PrintMsg(" \nUsing TEMP folder: " + tmpFolder, 0)
        #slExe = r"C:\Program Files\Utilities\spatialite-tools-5.0.0-win-amd64\spatialite.exe"
        shpEncoding = "CP1252"
        inputSRID = 4326
        geomFld = "shape"
        dbTxt = newDB.replace("\\", "/")

        # Create new script file to run shapefile imports in batch mode
        scriptFile = str(os.path.join(tmpFolder, "append_" + outLayerName + ".sql"))
        # PrintMsg(".\tUsing Spatialite script: " + scriptFile, 0)
        fh = open(scriptFile, 'w')
        sqlIndex = "SELECT DisableSpatialIndex('" + outLayerName + "', '" + geomFld + "') ; \n"
        fh.write(sqlIndex)
        sqlDrop = "DROP TABLE IF EXISTS idx_" + outLayerName + "_" + geomFld + " ; \n"
        fh.write(sqlDrop)

        # Unprojected vs. Projected shapefile import
        if outputSRID == inputSRID:

            # No projection required. Probably both are 4326 (GCS WGS1984)
            # PrintMsg(".\t\tNo projection required when output SRID = '" + str(outputSRID) + "'", 0)

            if geomType == "POLYGON":
                for shpFile in shapeList:
                    # create query used to import shapefile to virtual table, then copy to target geometry table
                    # assumes that the column names and sequence are the same for both
                    shp = shpFile[0:-4]
                    sqlMu = "CREATE VIRTUAL TABLE " + tmpShp + " USING VirtualShape ( '" + shp + "', " + shpEncoding + ", " + str(inputSRID) + " ) ;\n" + \
                    "INSERT INTO " + outLayerName + "(" + geomFld + ", " + ", ".join(fldList) + ") \n" + \
                    "SELECT CastToMultiPolygon(geometry) AS " + geomFld + ", " + ", ".join(fldList) + "\n" + \
                    "FROM " + tmpShp + " \n" + \
                    "ORDER BY pkuid ; \n" + \
                    "DROP TABLE IF EXISTS " + tmpShp + " ; \n\r"

                    fh.write(sqlMu)

            else:
                # Other geometries types should not need to be CAST
                for shpFile in shapeList:
                    # create query used to import shapefile to virtual table, then copy to target geometry table
                    # assumes that the column names and sequence are the same for both
                    shp = shpFile[0:-4]
                    sqlMu = "CREATE VIRTUAL TABLE " + tmpShp + " USING VirtualShape ( '" + shp + "', " + shpEncoding + ", " + str(inputSRID) + " ) ;\n" + \
                    "INSERT INTO " + outLayerName + "(" + geomFld + ", " + ", ".join(fldList) + ") \n" + \
                    "SELECT geometry AS " + geomFld + ", " + ", ".join(fldList) + "\n" + \
                    "FROM " + tmpShp + " \n" + \
                    "ORDER BY pkuid ; \n" + \
                    "DROP TABLE IF EXISTS " + tmpShp + " ; \n\r"

                    fh.write(sqlMu)
                    #PrintMsg(".\tProcessing " + shpFile + "...", 0)

        else:
            # Projection required, includes AOI for use in transformation
            #
            if geomType == "POLYGON":
                for shpFile in shapeList:
                    # create query used to import shapefile to virtual table, then copy to target geometry table
                    # assumes that the column names and sequence are the same for both
                    # Tries to add the AOI geometry as an argument to the ST_Transform, which is supposed to improve the datum transformation. Not seeing it though...

                    shp = shpFile[0:-4]
                    sqlMu = "CREATE VIRTUAL TABLE " + tmpShp + " USING VirtualShape ( '" + shp + "', " + shpEncoding + ", " + str(inputSRID) + " ) ;\n" + \
                    "INSERT INTO " + outLayerName + "(" + geomFld + ", " + ", ".join(fldList) + ") \n" + \
                    "SELECT CastToMultiPolygon(ST_Transform(geometry, " + str(outputSRID) + ", ST_GeomFromText(" + aoiWKT + "))) AS " + geomFld + ", " + ", ".join(fldList) + "\n" + \
                    "FROM " + tmpShp + " \n" + \
                    "ORDER BY pkuid ; \n" + \
                    "DROP TABLE IF EXISTS " + tmpShp + " ; \n\r"

                    fh.write(sqlMu)

            else:
                for shpFile in shapeList:
                    # create query used to import shapefile to virtual table, then copy to target geometry table
                    # assumes that the column names and sequence are the same for both
                    # Tries to add the AOI geometry as an argument to the ST_Transform, which is supposed to improve the datum transformation. Not seeing it though...

                    shp = shpFile[0:-4]
                    sqlMu = "CREATE VIRTUAL TABLE " + tmpShp + " USING VirtualShape ( '" + shp + "', " + shpEncoding + ", " + str(inputSRID) + " ) ;\n" + \
                    "INSERT INTO " + outLayerName + "(" + geomFld + ", " + ", ".join(fldList) + ") \n" + \
                    "SELECT ST_Transform(geometry, " + str(outputSRID) + ", ST_GeomFromText(" + aoiWKT + ")) AS " + geomFld + ", " + ", ".join(fldList) + "\n" + \
                    "FROM " + tmpShp + " \n" + \
                    "ORDER BY pkuid ; \n" + \
                    "DROP TABLE IF EXISTS " + tmpShp + " ; \n\r"

                    fh.write(sqlMu)
                    #PrintMsg(".\tProcessing " + shpFile + "...", 0)
                    #PrintMsg(".\tsqlMu: " + sqlMu, 0)

        #sqlIndex = "SELECT CreateSpatialIndex('" + outLayerName + "', '" + geomFld + "'); \n"
        #fh.write(sqlIndex)
        #sqlStats = "SELECT UpdateLayerStatistics('" + outLayerName + "', '" + geomFld + "'); \n"
        #fh.write(sqlStats)
        fh.close()
        PrintMsg(".\tAppending " + Number_Format(len(shapeList), 0, True) + " soils shapefiles to featureclass: " + outLayerName, 0)

        readScript = '.read ' + scriptFile.replace('\\', '/')
        shpImport = [slExe, dbTxt, readScript]  # really need to watch the quotes on these arguments. Subprocess will add its own.
        result = subprocess.Popen(shpImport, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell=True)
        stdout, stderr = result.communicate()
        exit_code = result.wait(timeout=300)

        if exit_code == 1:
            PrintMsg(".\tSingle Spatialite exit_code: " + str(exit_code), 1)
            PrintMsg(str(stderr.decode('ascii')), 1)
            return False

        PrintMsg(".\tCreating spatial index and updating statistics for " + outLayerName, 0)
        indexFile = str(os.path.join(tmpFolder, "spatial_indexes.sql"))
        fh = open(indexFile, 'w')
        sqlIndex = "SELECT CreateSpatialIndex('" + outLayerName + "', '" + geomFld + "'); \n"
        fh.write(sqlIndex)
        sqlStats = "SELECT UpdateLayerStatistics('" + outLayerName + "', '" + geomFld + "'); \n"
        fh.write(sqlStats)
        fh.close()

        readScript = '.read ' + indexFile.replace('\\', '/')
        spatialIndexes = [slExe, dbTxt, readScript]  # Really need to watch the quotes on these arguments. Subprocess will add its own.
        result = subprocess.Popen(spatialIndexes, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell=True)
        stdout, stderr = result.communicate()
        exit_code = result.wait(timeout=300)

        if exit_code == 1:
            PrintMsg(".\tSingle Spatialite exit_code for spatial indexes: " + str(exit_code), 1)
            PrintMsg(str(stderr.decode('ascii')), 1)
            return False


        return True

    except MyError as e:
        PrintMsg(str(e), 2)
        return False

    except:
        PrintMsg(".\tException condtion in AppendFeatures_Spatialite", 2)
        time.sleep(2)
        errorMsg()
        return False

## ===================================================================================
def ImportShapefiles_Valid_withTransformation( newDB, outputSRID, aoiWKT, outLayerName, shapeList, fldList, geomType, bCompressed):
    #
    # 2021-1220. I tried to implement the projection pipeline option for the WGS1984 to NAD1983 transformation, but it isn't working yet.
    #
    # Called by 'AppendFeatures_Spatialite', only for mupolygon and sapolygon with COMPRESSED datatypes!!!
    # COMPRESSED_POLYGON, COMPRESSED_LINESTRING
    #
    # Added option to compress geometry from 64 to 32 bit
    #
    # Changed data type in one of the template databases for multipolygon and linestring to compressed_polygon and compressed_linestring
    #
    # ST_Transform ( geom Geometry , newSrid Integer , area Geometry , proj_string_from Text , proj_string_to Text )
    #
    # Copy features from a list of shapefiles to a spatialite geometry table
    # Please Note! This function was developed using Spatialite 5.0.0 commandline which includes PROJ 7.1.0.
    # Need to look at newer methods for handling geographic transformations
    # Probably should incorporate a query that checks PROJ version

    # Investigating Proj options for Geographic Transformation (WGS1984 to NAD1983)
    # Trying to duplicate ESRI's ITRF00 transformation using Proj6.x or greater
    #
    # This query ran successfully, but produced polygons that appeared to have the wrong units or something.
    # The transformation needs a lot more work.
    ##INSERT INTO mupolygon(shape, areasymbol, spatialver, musym, mukey)
    ##SELECT CastToMultiPolygon(ST_Transform(geometry, 5070, BuildMBR(-75.78877, 39.38759, -75.72276, 39.83953, 4326), '+proj=pipeline
    ##+step +proj=cart +ellps=GRS80 +step +proj=helmert +convention=coordinate_frame +x=-81.0703  +y=-89.3603  +z=-115.7526
    ##+rx=-0.48488 +ry=-0.02436 +rz=-0.41321  +s=-0.540645 +step
    ##+proj=cart +inv +ellps=GRS80', NULL)) AS shape, areasymbol, spatialver, musym, mukey
    ##FROM xx_mupolygon
    ##ORDER BY pkuid ;
    #

    try:
        #bCompressed = True  # Compress spatial geometry for spatialite polygon layers
        projPipeline = "+proj=pipeline +step +proj=cart +ellps=GRS80 +step +proj=helmert +convention=coordinate_frame +x=-81.0703  +y=-89.3603  +z=-115.7526 +rx=-0.48488 +ry=-0.02436 +rz=-0.41321  +s=-0.540645 +step +proj=cart +inv +ellps=GRS80"

        tmpShp = "xx_" + outLayerName

        slExe = os.path.join(os.path.join(basePath, "Support"), "spatialite.exe")

        # Create corresponding list of field names for the virtual shapefile.
        # These tables use pkuid and geometry instead of objectid and shape.
        # Get field info from mupolygon (output layer) first
        #PrintMsg(".", 0)
        #PrintMsg("Assembling Spatialite commands needed to create new featureclass: " + outLayerName, 0)

        CREATE_NO_WINDOW = 0x08000000 # for subprocess, don't show window
        subprocess.CREATE_NO_WINDOW
        tmpFolder = os.environ["TEMP"]

        #PrintMsg(" \nUsing TEMP folder: " + tmpFolder, 0)
        shpEncoding = "CP1252"
        inputSRID = 4326
        geomFld = "shape"
        dbTxt = newDB.replace("\\", "/")

        # Create new script file to run shapefile imports in batch mode
        scriptFile = str(os.path.join(tmpFolder, "append_" + outLayerName + ".sql"))

        PrintMsg(".\t\tUsing Spatialite script: " + scriptFile, 0)
        fh = open(scriptFile, 'w')
        sqlIndex = "SELECT DisableSpatialIndex('" + outLayerName + "', '" + geomFld + "') ; \n"
        fh.write(sqlIndex)
        sqlDrop = "DROP TABLE IF EXISTS idx_" + outLayerName + "_" + geomFld + " ; \n\r"
        fh.write(sqlDrop)


        # Factors controlling SELECT options:
        #     bCompressed user-setting
        #     output geometry_columns datatype:
        #         if 'MULTIPOLYGON' need to use 'CastToMultiPolygon'
        #         if bCompressed and not 'POINT' need to use 'CompressGeometry'
        #         if geomType startswith 'COMPRESSED_', need to use 'CompressGeometry'????
        #         if COMPRESSED_POLYGON, POLYGON or MULTIPOLYGON, need to use ST_MakeValid
        #
        # Unprojected vs. Projected shapefile import
        if outputSRID == inputSRID:

            # GEOGRAPHIC
            #
            # No projection required. Probably both are 4326 (GCS WGS1984)
            PrintMsg(".\t\tNo projection required when output SRID = '" + str(outputSRID) + "'", 0)

            if geomType == "POINT" or (bCompressed == False and geomType == 'LINESTRING'):
                # Nothing used
                PrintMsg(".\tNo spatial compression used on " + outLayerName, 0)

                for shpFile in shapeList:
                    # create query used to import shapefile to virtual table, then copy to target geometry table
                    # assumes that the column names and sequence are the same for both
                    shp = shpFile[0:-4]
                    sqlGeom = "CREATE VIRTUAL TABLE " + tmpShp + " USING VirtualShape ( '" + shp + "', " + shpEncoding + ", " + str(inputSRID) + " ) ;\n" + \
                    "INSERT INTO " + outLayerName + "(" + geomFld + ", " + ", ".join(fldList) + ") \n" + \
                    "SELECT geometry AS " + geomFld + ", " + ", ".join(fldList) + "\n" + \
                    "FROM " + tmpShp + " \n" + \
                    "ORDER BY pkuid ; \n" + \
                    "DROP TABLE IF EXISTS " + tmpShp + " ; \n\r"
                    fh.write(sqlGeom)

            elif (bCompressed and geomType == 'POLYGON') or geomType == 'COMPRESSED_POLYGON':
                # Compression and MakeValid used
                PrintMsg(".\tApplying spatial compression and MakeValid to " + outLayerName, 0)

                for shpFile in shapeList:
                    # create query used to import shapefile to virtual table, then copy to target geometry table
                    # assumes that the column names and sequence are the same for both
                    shp = shpFile[0:-4]
                    sqlGeom = "CREATE VIRTUAL TABLE " + tmpShp + " USING VirtualShape ( '" + shp + "', " + shpEncoding + ", " + str(inputSRID) + " ) ;\n" + \
                    "INSERT INTO " + outLayerName + "(" + geomFld + ", " + ", ".join(fldList) + ") \n" + \
                    "SELECT CompressGeometry(ST_MakeValid(geometry)) AS " + geomFld + ", " + ", ".join(fldList) + "\n" + \
                    "FROM " + tmpShp + " \n" + \
                    "ORDER BY pkuid ; \n" + \
                    "DROP TABLE IF EXISTS " + tmpShp + " ; \n\r"
                    fh.write(sqlGeom)

            elif bCompressed and geomType == 'MULTIPOLYGON':
                # Compression, MakeValid and CastToMultiPolygon used
                PrintMsg(".\tApplying spatial compression, MakeValid and CastToMultiPolygon to " + outLayerName, 0)

                for shpFile in shapeList:
                    # create query used to import shapefile to virtual table, then copy to target geometry table
                    # assumes that the column names and sequence are the same for both
                    shp = shpFile[0:-4]
                    sqlGeom = "CREATE VIRTUAL TABLE " + tmpShp + " USING VirtualShape ( '" + shp + "', " + shpEncoding + ", " + str(inputSRID) + " ) ;\n" + \
                    "INSERT INTO " + outLayerName + "(" + geomFld + ", " + ", ".join(fldList) + ") \n" + \
                    "SELECT CompressGeometry(CastToMultiPolygon(ST_MakeValid(geometry))) AS " + geomFld + ", " + ", ".join(fldList) + "\n" + \
                    "FROM " + tmpShp + " \n" + \
                    "ORDER BY pkuid ; \n" + \
                    "DROP TABLE IF EXISTS " + tmpShp + " ; \n\r"
                    fh.write(sqlGeom)

            elif bCompressed == False and geomType == 'MULTIPOLYGON':
                # CastToMultiPolygon and MakeValid used
                PrintMsg(".\tApplying CastToMultiPolygon and MakeValid to " + outLayerName, 0)

                for shpFile in shapeList:
                    # create query used to import shapefile to virtual table, then copy to target geometry table
                    # assumes that the column names and sequence are the same for both
                    shp = shpFile[0:-4]
                    sqlGeom = "CREATE VIRTUAL TABLE " + tmpShp + " USING VirtualShape ( '" + shp + "', " + shpEncoding + ", " + str(inputSRID) + " ) ;\n" + \
                    "INSERT INTO " + outLayerName + "(" + geomFld + ", " + ", ".join(fldList) + ") \n" + \
                    "SELECT CastToMultiPolygon(ST_MakeValid(geometry)) AS " + geomFld + ", " + ", ".join(fldList) + "\n" + \
                    "FROM " + tmpShp + " \n" + \
                    "ORDER BY pkuid ; \n" + \
                    "DROP TABLE IF EXISTS " + tmpShp + " ; \n\r"
                    fh.write(sqlGeom)

            elif bCompressed and geomType in ('LINESTRING', 'COMPRESSED_LINESTRING'):
                # Compression used
                PrintMsg(".\tSpatial compression used on " + outLayerName, 0)

                for shpFile in shapeList:
                    # create query used to import shapefile to virtual table, then copy to target geometry table
                    # assumes that the column names and sequence are the same for both
                    shp = shpFile[0:-4]
                    sqlGeom = "CREATE VIRTUAL TABLE " + tmpShp + " USING VirtualShape ( '" + shp + "', " + shpEncoding + ", " + str(inputSRID) + " ) ;\n" + \
                    "INSERT INTO " + outLayerName + "(" + geomFld + ", " + ", ".join(fldList) + ") \n" + \
                    "SELECT CompressGeometry(geometry) AS " + geomFld + ", " + ", ".join(fldList) + "\n" + \
                    "FROM " + tmpShp + " \n" + \
                    "ORDER BY pkuid ; \n" + \
                    "DROP TABLE IF EXISTS " + tmpShp + " ; \n\r"
                    fh.write(sqlGeom)

            else:
                raise MyError("Failure in case statement: " + outLayerName + "; " + str(bCompressed) + "; " + str(geomType))



        else:
            # PROJECTED
            #
            # Projection required, includes AOI for use in transformation
            # ST_Transform ( geom Geometry , newSrid Integer , area Geometry , proj_string_from Text , proj_string_to Text )

            PrintMsg(".\t\tProjection required when output SRID = '" + str(outputSRID) + "'", 0)

            if geomType == "POINT" or (bCompressed == False and geomType == 'LINESTRING'):
                # Nothing used
                PrintMsg(".\tNo spatial compression used on " + outLayerName, 0)

                for shpFile in shapeList:
                    # create query used to import shapefile to virtual table, then copy to target geometry table
                    # assumes that the column names and sequence are the same for both
                    shp = shpFile[0:-4]
                    sqlGeom = "CREATE VIRTUAL TABLE " + tmpShp + " USING VirtualShape ( '" + shp + "', " + shpEncoding + ", " + str(inputSRID) + " ) ;\n" + \
                    "INSERT INTO " + outLayerName + "(" + geomFld + ", " + ", ".join(fldList) + ") \n" + \
                    "SELECT ST_Transform(geometry, " + str(outputSRID) + ", " + aoiWKT + ", NULL, '" + projPipeline + "') AS " + geomFld + ", " + ", ".join(fldList) + "\n" + \
                    "FROM " + tmpShp + " \n" + \
                    "ORDER BY pkuid ; \n" + \
                    "DROP TABLE IF EXISTS " + tmpShp + " ; \n\r"
                    fh.write(sqlGeom)

            elif (bCompressed and geomType == 'POLYGON') or geomType == 'COMPRESSED_POLYGON':
                # Compression and MakeValid used
                PrintMsg(".\tApplying spatial compression and MakeValid to " + outLayerName, 0)

                for shpFile in shapeList:
                    # create query used to import shapefile to virtual table, then copy to target geometry table
                    # assumes that the column names and sequence are the same for both
                    shp = shpFile[0:-4]
                    sqlGeom = "CREATE VIRTUAL TABLE " + tmpShp + " USING VirtualShape ( '" + shp + "', " + shpEncoding + ", " + str(inputSRID) + " ) ;\n" + \
                    "INSERT INTO " + outLayerName + "(" + geomFld + ", " + ", ".join(fldList) + ") \n" + \
                    "SELECT CompressGeometry(ST_Transform(ST_MakeValid(geometry), " + str(inputSRID) + ", " + aoiWKT + ", NULL, '" + projPipeline + "')  ) AS " + geomFld + ", " + ", ".join(fldList) + "\n" + \
                    "FROM " + tmpShp + " \n" + \
                    "ORDER BY pkuid ; \n" + \
                    "DROP TABLE IF EXISTS " + tmpShp + " ; \n\r"
                    fh.write(sqlGeom)

            elif bCompressed and geomType == 'MULTIPOLYGON':
                # Compression, MakeValid and CastToMultiPolygon used
                PrintMsg(".\tApplying spatial compression, MakeValid and CastToMultiPolygon to " + outLayerName, 0)


                ##-- This test actually output data, but the unit conversion is wrong. Maybe I need the degrees to radians?
                ##--
                ##INSERT INTO mupolygon(shape, areasymbol, spatialver, musym, mukey)
                ##SELECT CastToMultiPolygon(ST_Transform(geometry, 5070, BuildMBR(-75.78877, 39.38759, -75.72276, 39.83953, 4326), '+proj=pipeline
                ##+step +proj=cart +ellps=GRS80 +step +proj=helmert +convention=coordinate_frame +x=-81.0703  +y=-89.3603  +z=-115.7526
                ##+rx=-0.48488 +ry=-0.02436 +rz=-0.41321  +s=-0.540645 +step
                ##+proj=cart +inv +ellps=GRS80', NULL)) AS shape, areasymbol, spatialver, musym, mukey
                ##FROM xx_mupolygon
                ##ORDER BY pkuid ;

                for shpFile in shapeList:
                    # create query used to import shapefile to virtual table, then copy to target geometry table
                    # assumes that the column names and sequence are the same for both
                    shp = shpFile[0:-4]
                    sqlGeom = "CREATE VIRTUAL TABLE " + tmpShp + " USING VirtualShape ( '" + shp + "', " + shpEncoding + ", " + str(inputSRID) + " ) ;\n" + \
                    "INSERT INTO " + outLayerName + "(" + geomFld + ", " + ", ".join(fldList) + ") \n" + \
                    "SELECT CompressGeometry(CastToMultiPolygon(ST_Transform(ST_MakeValid(geometry), " + str(inputSRID) + ", " + aoiWKT + ", NULL, '" + projPipeline + "' ))) AS " + geomFld + ", " + ", ".join(fldList) + "\n" + \
                    "FROM " + tmpShp + " \n" + \
                    "ORDER BY pkuid ; \n" + \
                    "DROP TABLE IF EXISTS " + tmpShp + " ; \n\r"
                    fh.write(sqlGeom)

            elif bCompressed == False and geomType == 'MULTIPOLYGON':
                # CastToMultiPolygon and MakeValid used
                PrintMsg(".\tApplying CastToMultiPolygon and MakeValid to " + outLayerName, 0)

                for shpFile in shapeList:
                    # create query used to import shapefile to virtual table, then copy to target geometry table
                    # assumes that the column names and sequence are the same for both
                    shp = shpFile[0:-4]
                    sqlGeom = "CREATE VIRTUAL TABLE " + tmpShp + " USING VirtualShape ( '" + shp + "', " + shpEncoding + ", " + str(inputSRID) + " ) ;\n" + \
                    "INSERT INTO " + outLayerName + "(" + geomFld + ", " + ", ".join(fldList) + ") \n" + \
                    "SELECT CastToMultiPolygon(ST_Transform(ST_MakeValid(geometry), " + str(inputSRID) + ", " + aoiWKT + ", NULL, '" + projPipeline + "') ) AS " + geomFld + ", " + ", ".join(fldList) + "\n" + \
                    "FROM " + tmpShp + " \n" + \
                    "ORDER BY pkuid ; \n" + \
                    "DROP TABLE IF EXISTS " + tmpShp + " ; \n\r"
                    fh.write(sqlGeom)

            elif bCompressed and geomType in ('LINESTRING', 'COMPRESSED_LINESTRING'):
                # Compression used
                PrintMsg(".\tSpatial compression used on " + outLayerName, 0)

                for shpFile in shapeList:
                    # create query used to import shapefile to virtual table, then copy to target geometry table
                    # assumes that the column names and sequence are the same for both
                    shp = shpFile[0:-4]
                    sqlGeom = "CREATE VIRTUAL TABLE " + tmpShp + " USING VirtualShape ( '" + shp + "', " + shpEncoding + ", " + str(inputSRID) + " ) ;\n" + \
                    "INSERT INTO " + outLayerName + "(" + geomFld + ", " + ", ".join(fldList) + ") \n" + \
                    "SELECT CompressGeometry(ST_Transform(geometry), " + str(inputSRID) + ", " + aoiWKT + ", NULL, '" + projPipeline + "' ) ) AS " + geomFld + ", " + ", ".join(fldList) + "\n" + \
                    "FROM " + tmpShp + " \n" + \
                    "ORDER BY pkuid ; \n" + \
                    "DROP TABLE IF EXISTS " + tmpShp + " ; \n\r"
                    fh.write(sqlGeom)

            else:
                raise MyError("Failure in case statement: " + outLayerName + "; " + str(bCompressed) + "; " + str(geomType))

        fh.close()

        # Note! I believe that these next two commands will always work, thus returning a '1' (success), regardless of whether the geometry inserts worked or not.
        #
        PrintMsg(".\tAppending " + Number_Format(len(shapeList), 0, True) + " soils shapefiles to featureclass: " + outLayerName, 0)
        readScript = '.read ' + scriptFile.replace('\\', '/')
        shpImport = [slExe, dbTxt, readScript]  # Really need to watch the quotes on these arguments. Subprocess will add its own.
        result = subprocess.Popen(shpImport, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell=True)
        stdout, stderr = result.communicate()
        exit_code = result.wait(timeout=300)

        if exit_code == 1:
            PrintMsg(".\tSingle Spatialite exit_code for shapefile import: " + str(exit_code), 1)
            PrintMsg(str(stderr.decode('ascii')), 1)
            return False

        # Update spatial index and metadata tables
        PrintMsg(".\tCreating spatial index and updating statistics for " + outLayerName, 0)
        indexFile = str(os.path.join(tmpFolder, "spatial_indexes.sql"))
        fh = open(indexFile, 'w')
        sqlIndex = "SELECT CreateSpatialIndex('" + outLayerName + "', '" + geomFld + "'); \n"
        fh.write(sqlIndex)
        sqlStats = "SELECT UpdateLayerStatistics('" + outLayerName + "', '" + geomFld + "'); \n"
        fh.write(sqlStats)
        fh.close()

        readScript = '.read ' + indexFile.replace('\\', '/')
        spatialIndexes = [slExe, dbTxt, readScript]  # Really need to watch the quotes on these arguments. Subprocess will add its own.
        result = subprocess.Popen(spatialIndexes, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell=True)
        stdout, stderr = result.communicate()
        exit_code = result.wait(timeout=300)

        if exit_code == 1:
            PrintMsg(".\tSingle Spatialite exit_code for spatial indexes: " + str(exit_code), 1)
            PrintMsg(str(stderr.decode('ascii')), 1)
            return False

        # For 'mupolygon', update statistics for 'view_muname' and 'view_mupolyextended'
        if outLayerName == "mupolygon":

            bViewExtents = UpdateViewExtents(newDB, "view_muname", outLayerName)

            if bViewExtents == False:
                PrintMsg(".\tFailed to update 'views_geometry_columns_statistics' for 'view_muname'", 0)

            bViewExtents = UpdateViewExtents(newDB, "view_mupolyextended", outLayerName)

            if bViewExtents == False:
                PrintMsg(".\tFailed to update 'views_geometry_columns_statistics' for 'view_mupolyextended'", 0)


        return True

    except MyError as e:
        PrintMsg(str(e), 2)
        return False

    except:
        PrintMsg(".\tException condtion in AppendFeatures_Spatialite", 2)
        time.sleep(2)
        errorMsg()
        return False

## ===================================================================================
def ImportShapefiles_Valid(newDB, outputSRID, aoiWKT, outLayerName, shapeList, fldList, geomType, bCompressed):
    # Original template databases with MULTIPOLYGON and LINESTRING datatypes.

    # Called by 'AppendFeatures_Spatialite', only for mupolygon and sapolygon.
    #
    # Added option to compress geometry from 64 to 32 bit
    #
    # Copy features from a list of shapefiles to a spatialite geometry table
    # Please Note! This function was developed using Spatialite 5.0.0 commandline which includes PROJ 7.1.0.
    # Need to look at newer methods for handling geographic transformations
    # Probably should incorporate a query that checks PROJ version
    #
    # Possible use for GeoJSON: https://datatracker.ietf.org/doc/html/rfc7946#section-3.1.6
    # GeomFromGeoJSON

    # Investigating Proj options for Geographic Transformation (WGS1984 to NAD1983)
    # Trying to duplicate ESRI's ITRF00 transformation using Proj6.x or greater
    #
    # proj=pipeline
    # step proj=cart ellps=GRS80
    # step proj=helmert convention=coordinate_frame
    #     x=-81.0703  y=-89.3603  z=-115.7526
    #    rx=-0.48488 ry=-0.02436 rz=-0.41321  s=-0.540645
    # step proj=cart inv ellps=GRS80
    #

    try:
        #bCompressed = True  # Compress spatial geometry for spatialite polygon layers

        tmpShp = "xx_" + outLayerName

        slExe = os.path.join(os.path.join(basePath, "Support"), "spatialite.exe")

        # Create corresponding list of field names for the virtual shapefile.
        # These tables use pkuid and geometry instead of objectid and shape.
        # Get field info from mupolygon (output layer) first
        #PrintMsg(".", 0)
        #PrintMsg("Assembling Spatialite commands needed to create new featureclass: " + outLayerName, 0)

        CREATE_NO_WINDOW = 0x08000000 # for subprocess, don't show window
        subprocess.CREATE_NO_WINDOW
        tmpFolder = os.environ["TEMP"]

        #PrintMsg(" \nUsing TEMP folder: " + tmpFolder, 0)
        shpEncoding = "CP1252"
        inputSRID = 4326
        geomFld = "shape"
        dbTxt = newDB.replace("\\", "/")

        # Create new script file to run shapefile imports in batch mode
        scriptFile = str(os.path.join(tmpFolder, "append_" + outLayerName + ".sql"))

        PrintMsg(".\t\tUsing Spatialite script: " + scriptFile, 0)
        fh = open(scriptFile, 'w')
        sqlIndex = "SELECT DisableSpatialIndex('" + outLayerName + "', '" + geomFld + "') ; \n"
        fh.write(sqlIndex)
        sqlDrop = "DROP TABLE IF EXISTS idx_" + outLayerName + "_" + geomFld + " ; \n\r"
        fh.write(sqlDrop)

        # Unprojected vs. Projected shapefile import
        if outputSRID == inputSRID:

            # No projection required. Probably both are 4326 (GCS WGS1984)
            PrintMsg(".\t\tNo projection required when output SRID = '" + str(outputSRID) + "'", 0)

            if bCompressed:
                # compression for geometry (64 -> 32 bit)
                PrintMsg(".\tApplying spatial compression to " + outLayerName, 0)

                if geomType == "POLYGON":
                    for shpFile in shapeList:
                        # create query used to import shapefile to virtual table, then copy to target geometry table
                        # assumes that the column names and sequence are the same for both
                        shp = shpFile[0:-4]
                        sqlMu = "CREATE VIRTUAL TABLE " + tmpShp + " USING VirtualShape ( '" + shp + "', " + shpEncoding + ", " + str(inputSRID) + " ) ;\n" + \
                        "INSERT INTO " + outLayerName + "(" + geomFld + ", " + ", ".join(fldList) + ") \n" + \
                        "SELECT CompressGeometry(ST_MakeValid(geometry)) AS " + geomFld + ", " + ", ".join(fldList) + "\n" + \
                        "FROM " + tmpShp + " \n" + \
                        "ORDER BY pkuid ; \n" + \
                        "DROP TABLE IF EXISTS " + tmpShp + " ; \n\r"
                        fh.write(sqlMu)

                else:
                    # Skip compression for LINESTRING
                    for shpFile in shapeList:
                        # create query used to import shapefile to virtual table, then copy to target geometry table
                        # assumes that the column names and sequence are the same for both
                        shp = shpFile[0:-4]
                        sqlMu = "CREATE VIRTUAL TABLE " + tmpShp + " USING VirtualShape ( '" + shp + "', " + shpEncoding + ", " + str(inputSRID) + " ) ;\n" + \
                        "INSERT INTO " + outLayerName + "(" + geomFld + ", " + ", ".join(fldList) + ") \n" + \
                        "SELECT geometry AS " + geomFld + ", " + ", ".join(fldList) + "\n" + \
                        "FROM " + tmpShp + " \n" + \
                        "ORDER BY pkuid ; \n" + \
                        "DROP TABLE IF EXISTS " + tmpShp + " ; \n\r"
                        fh.write(sqlMu)

            else:
                # no compression for geometry (64 -> 32 bit)
                PrintMsg(".\tNo spatial compression used on " + outLayerName, 0)

                if geomType == "POLYGON":
                    for shpFile in shapeList:
                        # create query used to import shapefile to virtual table, then copy to target geometry table
                        # assumes that the column names and sequence are the same for both
                        shp = shpFile[0:-4]

                        sqlMu = "CREATE VIRTUAL TABLE " + tmpShp + " USING VirtualShape ( '" + shp + "', " + shpEncoding + ", " + str(inputSRID) + " ) ;\n" + \
                        "INSERT INTO " + outLayerName + "(" + geomFld + ", " + ", ".join(fldList) + ") \n" + \
                        "SELECT ST_MakeValid(geometry) AS " + geomFld + ", " + ", ".join(fldList) + "\n" + \
                        "FROM " + tmpShp + " \n" + \
                        "ORDER BY pkuid ; \n" + \
                        "DROP TABLE IF EXISTS " + tmpShp + " ; \n\r"
                        fh.write(sqlMu)

                else:
                    # Skip MakeValid for LINESTRING and POINT
                    for shpFile in shapeList:
                        # create query used to import shapefile to virtual table, then copy to target geometry table
                        # assumes that the column names and sequence are the same for both
                        shp = shpFile[0:-4]

                        sqlMu = "CREATE VIRTUAL TABLE " + tmpShp + " USING VirtualShape ( '" + shp + "', " + shpEncoding + ", " + str(inputSRID) + " ) ;\n" + \
                        "INSERT INTO " + outLayerName + "(" + geomFld + ", " + ", ".join(fldList) + ") \n" + \
                        "SELECT geometry AS " + geomFld + ", " + ", ".join(fldList) + "\n" + \
                        "FROM " + tmpShp + " \n" + \
                        "ORDER BY pkuid ; \n" + \
                        "DROP TABLE IF EXISTS " + tmpShp + " ; \n\r"
                        fh.write(sqlMu)

        else:
            # Projection required, includes AOI for use in transformation
            #
            if bCompressed:
                PrintMsg(".\tApplying spatial compression to " + outLayerName, 0)

                if geomType == "POLYGON":
                    for shpFile in shapeList:
                        # create query used to import shapefile to virtual table, then copy to target geometry table
                        # assumes that the column names and sequence are the same for both
                        # Tries to add the AOI geometry as an argument to the ST_Transform, which is supposed to improve the datum transformation. Not seeing it though...

                        shp = shpFile[0:-4]
                        sqlMu = "CREATE VIRTUAL TABLE " + tmpShp + " USING VirtualShape ( '" + shp + "', " + shpEncoding + ", " + str(inputSRID) + " ) ;\n" + \
                        "INSERT INTO " + outLayerName + "(" + geomFld + ", " + ", ".join(fldList) + ") \n" + \
                        "SELECT CompressGeometry(ST_Transform(ST_MakeValid(geometry), " + str(outputSRID) + ", ST_GeomFromText(" + aoiWKT + "))) AS " + geomFld + ", " + ", ".join(fldList) + "\n" + \
                        "FROM " + tmpShp + " \n" + \
                        "ORDER BY pkuid ; \n" + \
                        "DROP TABLE IF EXISTS " + tmpShp + " ; \n\r"
                        fh.write(sqlMu)

                else:
                    # Skip compression for LINESTRING and POINT
                    for shpFile in shapeList:
                        # create query used to import shapefile to virtual table, then copy to target geometry table
                        # assumes that the column names and sequence are the same for both
                        # Tries to add the AOI geometry as an argument to the ST_Transform, which is supposed to improve the datum transformation. Not seeing it though...

                        shp = shpFile[0:-4]
                        sqlMu = "CREATE VIRTUAL TABLE " + tmpShp + " USING VirtualShape ( '" + shp + "', " + shpEncoding + ", " + str(inputSRID) + " ) ;\n" + \
                        "INSERT INTO " + outLayerName + "(" + geomFld + ", " + ", ".join(fldList) + ") \n" + \
                        "SELECT ST_Transform(geometry, " + str(outputSRID) + ", ST_GeomFromText(" + aoiWKT + ")) AS " + geomFld + ", " + ", ".join(fldList) + "\n" + \
                        "FROM " + tmpShp + " \n" + \
                        "ORDER BY pkuid ; \n" + \
                        "DROP TABLE IF EXISTS " + tmpShp + " ; \n\r"
                        fh.write(sqlMu)

            else:
                # no compression
                PrintMsg(".\tNo spatial compression used on " + outLayerName, 0)

                if geomType == "POLYGON":
                    for shpFile in shapeList:
                        # create query used to import shapefile to virtual table, then copy to target geometry table
                        # assumes that the column names and sequence are the same for both
                        # Putting compression at the end of the chain.
                        shp = shpFile[0:-4]

                        sqlMu = "CREATE VIRTUAL TABLE " + tmpShp + " USING VirtualShape ( '" + shp + "', " + shpEncoding + ", " + str(inputSRID) + " ) ;\n" + \
                        "INSERT INTO " + outLayerName + "(" + geomFld + ", " + ", ".join(fldList) + ") \n" + \
                        "SELECT ST_Transform(ST_MakeValid(geometry), " + str(outputSRID) + ", ST_GeomFromText(" + aoiWKT + ")) AS " + geomFld + ", " + ", ".join(fldList) + "\n" + \
                        "FROM " + tmpShp + " \n" + \
                        "ORDER BY pkuid ; \n" + \
                        "DROP TABLE IF EXISTS " + tmpShp + " ; \n\r"
                        fh.write(sqlMu)

                else:
                    # Skip MakeValid for LINESTRING and POINT
                    for shpFile in shapeList:
                        # create query used to import shapefile to virtual table, then copy to target geometry table
                        # assumes that the column names and sequence are the same for both
                        # Putting compression at the end of the chain.
                        shp = shpFile[0:-4]

                        sqlMu = "CREATE VIRTUAL TABLE " + tmpShp + " USING VirtualShape ( '" + shp + "', " + shpEncoding + ", " + str(inputSRID) + " ) ;\n" + \
                        "INSERT INTO " + outLayerName + "(" + geomFld + ", " + ", ".join(fldList) + ") \n" + \
                        "SELECT ST_Transform(geometry, " + str(outputSRID) + ", ST_GeomFromText(" + aoiWKT + ")) AS " + geomFld + ", " + ", ".join(fldList) + "\n" + \
                        "FROM " + tmpShp + " \n" + \
                        "ORDER BY pkuid ; \n" + \
                        "DROP TABLE IF EXISTS " + tmpShp + " ; \n\r"
                        fh.write(sqlMu)




        fh.close()

        # Note! I believe that these next two commands will always work, thus returning a '1' (success), regardless of whether the geometry inserts worked or not.
        #
        PrintMsg(".\tAppending " + Number_Format(len(shapeList), 0, True) + " soils shapefiles to featureclass: " + outLayerName, 0)
        readScript = '.read ' + scriptFile.replace('\\', '/')
        shpImport = [slExe, dbTxt, readScript]  # Really need to watch the quotes on these arguments. Subprocess will add its own.
        result = subprocess.Popen(shpImport, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell=True)
        stdout, stderr = result.communicate()
        exit_code = result.wait(timeout=300)

        if exit_code == 1:
            PrintMsg(".\tSingle Spatialite exit_code for shapefile import: " + str(exit_code), 1)
            PrintMsg(str(stderr.decode('ascii')), 1)
            return False

        # Update spatial index and metadata tables
        PrintMsg(".\tCreating spatial index and updating statistics for " + outLayerName, 0)
        indexFile = str(os.path.join(tmpFolder, "spatial_indexes.sql"))
        fh = open(indexFile, 'w')
        sqlIndex = "SELECT CreateSpatialIndex('" + outLayerName + "', '" + geomFld + "'); \n"
        fh.write(sqlIndex)
        sqlStats = "SELECT UpdateLayerStatistics('" + outLayerName + "', '" + geomFld + "'); \n"
        fh.write(sqlStats)
        fh.close()

        readScript = '.read ' + indexFile.replace('\\', '/')
        spatialIndexes = [slExe, dbTxt, readScript]  # Really need to watch the quotes on these arguments. Subprocess will add its own.
        result = subprocess.Popen(spatialIndexes, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell=True)
        stdout, stderr = result.communicate()
        exit_code = result.wait(timeout=300)

        if exit_code == 1:
            PrintMsg(".\tSingle Spatialite exit_code for spatial indexes: " + str(exit_code), 1)
            PrintMsg(str(stderr.decode('ascii')), 1)
            return False

        # For 'mupolygon', update statistics for 'view_muname' and 'view_mupolyextended'
        if outLayerName == "mupolygon":

            bViewExtents = UpdateViewExtents(newDB, "view_muname", outLayerName)

            if bViewExtents == False:
                PrintMsg(".\tFailed to update 'views_geometry_columns_statistics' for 'view_muname'", 0)

            bViewExtents = UpdateViewExtents(newDB, "view_mupolyextended", outLayerName)

            if bViewExtents == False:
                PrintMsg(".\tFailed to update 'views_geometry_columns_statistics' for 'view_mupolyextended'", 0)


        return True

    except MyError as e:
        PrintMsg(str(e), 2)
        return False

    except:
        PrintMsg(".\tException condtion in AppendFeatures_Spatialite", 2)
        time.sleep(2)
        errorMsg()
        return False

## ===================================================================================
def UpdateViewExtents(newDB, viewName, tableName):
    # Update the 'views_geometry_columns_statistics' table after the mupolygon table has been populated.
    # Currently there are two spatial views created with the database: 'view_muname' and 'view_mupolyextended'
    #
    # geometry_columns_statistics: f_table_name, f_geometry_column, last_verified, row_count, extent_min_x, extent_min_y, extent_max_x, extent_max_y
    # views_geometry_columns_statistics: view_name, view_geometry, last_verified, row_count, extent_min_x, extent_min_y, extent_max_x, extent_max_y

    try:
        dbConn = sqlite3.connect(newDB)
        liteCur = dbConn.cursor()
        tblValues = (tableName,)
        sqlExtents = """SELECT '""" + viewName + """' AS view_name, f_geometry_column, last_verified, row_count,
            extent_min_x, extent_min_y, extent_max_x, extent_max_y
            FROM geometry_columns_statistics WHERE f_table_name = '""" + tableName + "'; "

        liteCur.execute(sqlExtents)
        row = liteCur.fetchone()

        queryFindView = "DELETE FROM views_geometry_columns_statistics WHERE view_name = '""" + viewName + "';"
        liteCur.execute(queryFindView)
        del tblValues
        # PrintMsg("\tView Extents 2: " + str(row), 1)

        queryRegisterView = "INSERT INTO views_geometry_columns_statistics (view_name, view_geometry, last_verified, row_count, extent_min_x, extent_min_y, extent_max_x, extent_max_y) VALUES (?, ?, ?, ?, ?, ?, ?, ?); "
        liteCur.execute(queryRegisterView, row)

        dbConn.commit()
        del row
        del dbConn

        return True

    except:
        errorMsg()
        return False

## ===================================================================================
def SetOutputCoordinateSystem(AOI, newDB):
    # Define new output coordinate system
    #
    # Only used with AppendFeatures_ArcPy function (infested with arcpy)
    #
    # The original versions of gSSURGO used Albers WGS1984 coordinate systems for all but CONUS, PR-USVI
    # which were NAD 1983.
    #
    # arcpy.ListSpatialReferences(wildcard for name, "GCS" or "PCS" or "ALL") returns namestring
    # https://pro.arcgis.com/en/pro-app/latest/arcpy/functions/listspatialreferences.htm
    #
    # arcpy.ListTransformations(from_sr, to_sr, LL-UR extents using from_sr units) returns string of all valid methods
    # https://pro.arcgis.com/en/pro-app/latest/arcpy/functions/listtransformations.htm

    try:
        # At this time (2021), SSURGO download shapefiles are only available as GCS WGS 1984.

        PrintMsg(".\tArcpy is being used in the SetOutputCoordinateSystem function", 0)

        # AOI
        # Lower 48 States: 'NAD_1983_Contiguous_USA_Albers': EPSG:5070
        # Alaska: Alaska Albers                            : EPSG:3338
        # Hawaii: Hawaii Albers Equal Area Conic           : EPSG:102007
        #
        result = False
        e = 0
        dEPSG = dict()
        dEPSG['Lower 48 States'] = 5070  # 102039
        # dEPSG['Lower 48 States'] = 6350  # 102039
        # dEPSG['Lower 48 States'] = 102039
        dEPSG['Alaska'] = 3338
        #dEPSG['Hawaii (HI)'] = 102007 # ESRI Albers with apparent problem
        # dEPSG['Hawaii'] = 26963   # NAD_1983_StatePlane_Hawaii_3_FIPS_5103
        # dEPSG['Puerto Rico and U.S. Virgin Islands'] = 5070
        dEPSG['Pacific Islands Area'] = 900914  # This is the SRID I used when I created the Western Pacific Islands CSR in the template db.
        dEPSG['World'] = 4326
        #dEPSG['American Samoa'] = 2195
        dEPSG["GCS NAD1983"]= 4269  # default gt is WGS_1984_(ITRF00)_To_NAD_1983 for kansas.
        dEPSG["American Samoa (AS)"] = 32702
        dEPSG["Guam (GU)"] = 32655
        dEPSG["Hawaii (HI)"] = 32604
        # dEPSG["Hawaii (HI)"] = 4326
        dEPSG["Mariana Islands (MP)"] = 32655
        dEPSG["Marshall Islands (MH)"] = 32659
        # dEPSG["Micronesia (FM)"] = 32656  # UTM Zone 56 WGS 1984
        dEPSG["Micronesia (FM)"] = 3857   # Web Mercatur
        dEPSG["GCS NAD1983"] = 4269

        dEPSG["Palau Islands (PW)"] = 32653
        # dEPSG["Puerto Rico and U.S. Virgin Islands"] = 32619  # UTM Zone 19, WGS 1984
        dEPSG["Puerto Rico and U.S. Virgin Islands"] = 32161  # 'NAD_1983_StatePlane_Puerto_Rico_Virgin_Islands_FIPS_5200'


        # Options for using WGS 84, UTM meters for island coordinate systems
        # -------------------------------------------------------------------
        # American Samoa (AS) EPSG: 32702, WGS 84 UTM 2S
        # Guam (GU) EPSG: 32655, WGS 84 UTM 55N
        # Hawaii (HI) EPSG: 32604,  WGS 84 UTM Zone 4N
        # Mariana Islands (MP) EPSG: 32655. WGS 84 UTM Zone 55 N
        # Marshall Islands (MH) EPSG: 32659,  WGS 84 UTM Zone 59N
        # Micronesia (FM) EPSG: 32656, WGS 84 UTM Zone 56N
        # Palau Islands (PW) EPSG: 32653, WGS 84 UTM Zone 53N
        # Puerto Rico and U.S. Virgin Islands (PR, VI) EPSG: 32619


        # Puerto Rico EPSG 32619, WGS 84 UTM Zone 19N

        # Then to go on to 6350 use a 2-step.  WGS_1984_(ITRF00)_To_NAD_1983 + WGS_1984_(ITRF08)_To_NAD_1983_2011

        # Another more direct route for 4326 to 6350 would be ITRF_2000_To_WGS_1984 + ITRF_2000_To_NAD_1983_2011

        # Assuming that the inpu32604t coordinate system for SSURGO data and is GCS WGS1984 (4326)


        inputSR = arcpy.SpatialReference(4326)       # GCS WGS 1984
        inputDatum = inputSR.datumCode
        e = 1

        if not AOI in dEPSG:
            raise MyError(".\tAOI (" + AOI + ") not found", 0)

        outputSRID = dEPSG[AOI]
        PrintMsg(".\tOutput SRID: " + str(outputSRID), 0)

        if outputSRID == 900914:
            outputSR = arcpy.SpatialReference(os.path.join(scriptFolder, "Western_Pacific_Albers_Equal_Area_Conic.prj"))

        else:
            outputSR = arcpy.SpatialReference(outputSRID)

        if inputSR == outputSR:
            PrintMsg(".\tNo projection required", 0)
            env.outputCoordinateSystem = inputSR
            env.geographicTransformations = ""
            return True

        else:
            env.outputCoordinateSystem = outputSR

        e = 2
        #outputSRName = outputSR.name

        # Get list of valid geographic transformations when the input CSR and output CSR are different
        PrintMsg(".\Getting list of datum transformations...", 0)
        sGT = arcpy.ListTransformations(inputSR, outputSR )
        #PrintMsg(".\tGot transformations: " + str(sGT), 0)

        if not sGT is None and len(sGT) > 0:
            tm = sGT[0]
            PrintMsg(".\tApplying geographic transformation: " + tm, 0)

        else:
            tm = ""

        e = 3

        layerList = [["sapolygon"], ["mupolygon"], ["muline"], ["mupoint"], ["featline"], ["featpoint"]]
        conn = sqlite3.connect(newDB)
        liteCur = conn.cursor()

        if newDB.endswith(".sqlite"):
            # See if the spatialite database already has this coordinate system available to use
            sqlSRID = "SELECT COUNT(*) FROM spatial_ref_sys WHERE srid = " + str(outputSRID) + " ;"
            liteCur.execute(sqlSRID)
            bCSR = liteCur.fetchone()[0]
            #PrintMsg(".\tHere is bCSR: " + str(bCSR), 0)
            e = 4

            if bCSR:
                # database has the required outcoordinate system for each of the spatial layers.
                # I should make all these present in the template.
                e = 5
                PrintMsg(".\toutputSRID value: " + str(outputSRID), 0)
                sqlUpdate = "UPDATE geometry_columns SET srid = " + str(outputSRID) + " WHERE srid = 4326 AND (f_table_name =? OR f_table_name LIKE 'view_%');"
                #PrintMsg(".\tsqlUpdate: " + sqlUpdate, 0)
                liteCur.executemany(sqlUpdate, layerList)
                conn.commit()
                e = 6

                # only update the 'geometry_columns' table, the 'geom_cols_ref_sys' table should automatically update via trigger

                # These next two lines set the output coordinate system environment
                PrintMsg(".\tSetting output coordinate system...", 0)
                #PrintMsg(".\t1. Setting output coordinate system to " + str(outputSR.name) + "(" + + str(outputSRID) + ")", 0)
                #time.sleep(5)
                e = 7
                #env.outputCoordinateSystem = outputSR
                #env.geographicTransformations = tm

        elif newDB.endswith(".gpkg"):
            # update spatial references for each of the spatial tables

            # See if the spatialite database already has this coordinate system available to use
            sqlSRID = "SELECT COUNT(*) FROM gpkg_spatial_ref_sys WHERE srs_id = " + str(outputSRID) + " ;"
            liteCur.execute(sqlSRID)
            bCSR = liteCur.fetchone()[0]
            PrintMsg(".\tbCSR: " + str(bCSR), 0)
            e = 8

            if bCSR:
                # database has the required outcoordinate system for each of the spatial layers.
                # I should make all these present in the template.

                sqlUpdate = "UPDATE gpkg_geometry_columns SET srs_id = " + str(outputSRID) + " WHERE srs_id = 4326 AND table_name =?;"
                liteCur.executemany(sqlUpdate, layerList)
                conn.commit()
                e = 9

                # These next two lines set the output coordinate system environment
                PrintMsg(".\t2. Setting output coordinate system to " + str(outputSR), 0)
                #PrintMsg(".\t2. Setting output coordinate system to " + outputSR.name, 0)
                #time.sleep(5)
                env.outputCoordinateSystem = outputSR
                env.geographicTransformations = tm
                e = 10

        else:
            PrintMsg(".\tOutput database does not have the required coordinate system information needed to project the layers", 1)

        e = 99

        result = True

    except sqlite3.IntegrityError as err:
        PrintMsg(".\tSQLite IntegrityError: ", 2)
        time.sleep(1)
        PrintMsg(".\t" + err.args[0], 2)
        time.sleep(1)

    except sqlite3.OperationalError as err:
        PrintMsg(".\tSQLite OperationalError: ", 2)
        time.sleep(1)
        PrintMsg(".\t" + err.args[0], 2)
        time.sleep(1)

    except sqlite3.Error as err:
        PrintMsg(".\tSQLite Error: ", 2)
        time.sleep(1)
        msg = err.args[0]
        PrintMsg(".\t" + msg, 2)
        time.sleep(1)

    except:
        time.sleep(1)
        PrintMsg(" \nException raised at point: " + str(e), 2)
        #errorMsg()

    finally:
        try:
            conn.close()
            del conn

        except:
            pass

        return result

## ===================================================================================
def SetOutputSRID(geogRegion, newDB):
    # Define new output coordinate system SRID based upon geographic region selected by user
    #
    # Currently used only with AppendFeatures_Spatialite
    #
    # There is a potential issue with spatial updates....
    # With a new database, the database is updated so that all spatial columns use the specified SRID.
    # If spatial data is appended to an existing database, the output SRID must be transformed to match the existing data.
    # returns output SRID (integer)

    try:
        # At this time (2021), SSURGO download shapefiles are only available as GCS WGS 1984.
        # geogRegion
        # Lower 48 States: 'NAD_1983_Contiguous_USA_Albers': EPSG:5070
        # Alaska: Alaska Albers                            : EPSG:3338
        # Hawaii: Hawaii Albers Equal Area Conic           : EPSG:102007
        #
        #PrintMsg(".\tRunning SetOutputSRID function...", 0)
        result = 0, "Undefined - Geographic Long/Lat"  # default value for EPSG code

        #e = 0

        dEPSG = dict()
        dEPSG['Lower 48 States'] = 5070  # 102039
        dEPSG['Alaska (AK)'] = 3338
        dEPSG['Pacific Islands Area'] = 900914  # This is the SRID I used when I created the Western Pacific Islands CSR in the template db.
        dEPSG["GCS NAD1983"]= 4269  # default gt is WGS_1984_(ITRF00)_To_NAD_1983 for kansas.
        dEPSG["American Samoa (AS)"] = 32702
        dEPSG["Guam (GU)"] = 32655
        #dEPSG["Hawaii (HI)"] = 32604
        dEPSG["Hawaii (HI)"] = 4326
        dEPSG["Mariana Islands (MP)"] = 32655
        dEPSG["Marshall Islands (MH)"] = 32659
        dEPSG["Micronesia (FM)"] = 4326
        dEPSG["Palau Islands (PW)"] = 32653
        dEPSG["Puerto Rico and U.S. Virgin Islands"] = 32161  # NAD83 / Puerto Rico & Virgin Is. Lambert Conformal Conic

        dEPSG['World'] = 4326
        dEPSG['GCS NAD1983'] = 4269

        # Options for using WGS 84, UTM meters for island coordinate systems
        # -------------------------------------------------------------------
        # American Samoa (AS) EPSG: 32702, WGS 84 UTM 2S
        # Guam (GU) EPSG: 32655, WGS 84 UTM 55N
        # Hawaii (HI) EPSG: 32604,  WGS 84 UTM Zone 4N
        # Mariana Islands (MP) EPSG: 32655. WGS 84 UTM Zone 55 N
        # Marshall Islands (MH) EPSG: 32659,  WGS 84 UTM Zone 59N
        # Micronesia (FM) EPSG: 32656, WGS 84 UTM Zone 56N
        # Palau Islands (PW) EPSG: 32653, WGS 84 UTM Zone 53N
        # Puerto Rico and U.S. Virgin Islands (PR, VI) EPSG: 32619
        # Puerto Rico EPSG 32619, WGS 84 UTM Zone 19N
        # Then to go on to 6350 use a 2-step.  WGS_1984_(ITRF00)_To_NAD_1983 + WGS_1984_(ITRF08)_To_NAD_1983_2011

        # Another more direct route for 4326 to 6350 would be ITRF_2000_To_WGS_1984 + ITRF_2000_To_NAD_1983_2011

        # Assuming that the input coordinate system for SSURGO data and is GCS WGS1984 (4326)
        # inputSR = arcpy.SpatialReference(4326)       # GCS WGS 1984
        # inputDatum = inputSR.datumCode

        if not geogRegion in dEPSG:
            raise MyError(".\tgeogRegion (" + geogRegion + ") not found", 0)

        else:
            outputSRID = dEPSG[geogRegion]
            #PrintMsg(".\tOutput SRID: " + str(outputSRID), 0)

        #result = dEPSG[geogRegion]
        #PrintMsg(".\tOutput SRID: " + str(result), 0)

        layerList = [["sapolygon"], ["mupolygon"], ["muline"], ["mupoint"], ["featline"], ["featpoint"]]
        conn = sqlite3.connect(newDB)
        liteCur = conn.cursor()

        if newDB.endswith(".sqlite"):
            # See if the spatialite database already has this coordinate system available to use
            sqlCSName = "SELECT ref_sys_name FROM spatial_ref_sys WHERE srid = " + str(outputSRID)
            liteCur.execute(sqlCSName)
            bCSR = liteCur.fetchone()

            if bCSR:
                # database has the required outcoordinate system for each of the spatial layers.
                # I should make all these present in the template.
                csrName = bCSR[0]
                result = outputSRID, csrName
                sqlUpdate = "UPDATE geometry_columns SET srid = " + str(outputSRID) + " WHERE srid = 4326 AND (f_table_name =? OR f_table_name LIKE 'view_%');"
                #PrintMsg(".\tsqlUpdate: " + sqlUpdate, 0)
                liteCur.executemany(sqlUpdate, layerList)
                conn.commit()

                # the geom_cols_ref_sys table should automatically update via trigger
                PrintMsg(".\tSetting output coordinate system to: '" + csrName + "' (EPSG:" + str(outputSRID) + ")", 0)

        elif newDB.endswith(".gpkg"):
            # update spatial references for each of the spatial tables

            # See if the spatialite database already has this coordinate system available to use
            sqlSRID = "SELECT srs_name FROM gpkg_spatial_ref_sys WHERE srs_id = " + str(outputSRID) + " ;"
            liteCur.execute(sqlSRID)
            bCSR = liteCur.fetchone()

            if bCSR:
                # database has the required outcoordinate system for each of the spatial layers.
                # I should make all these present in the template.
                csrName = bCSR[0]
                result = outputSRID, csrName
                sqlUpdate = "UPDATE gpkg_geometry_columns SET srs_id = " + str(outputSRID) + " WHERE srs_id = 4326 AND table_name =?;"
                liteCur.executemany(sqlUpdate, layerList)
                conn.commit()

                # These next two lines set the output coordinate system environment
                PrintMsg(".\tSetting output coordinate system to: '" + csrName + "' (EPSG:" + str(outputSRID) + ")", 0)

        else:
            PrintMsg(".\tOutput database does not have the required coordinate system information needed to project the layers", 1)

    except sqlite3.IntegrityError as err:
        PrintMsg(".\tSQLite IntegrityError: ", 2)
        time.sleep(1)
        PrintMsg(".\t" + err.args[0], 2)
        time.sleep(1)

    except sqlite3.OperationalError as err:
        PrintMsg(".\tSQLite OperationalError: ", 2)
        time.sleep(1)
        PrintMsg(".\t" + err.args[0], 2)
        time.sleep(1)

    except sqlite3.Error as err:
        PrintMsg(".\tSQLite Error: ", 2)
        time.sleep(1)
        msg = err.args[0]
        PrintMsg(".\t" + msg, 2)
        time.sleep(1)

    except:
        time.sleep(1)
        PrintMsg(" \nException raised at point: " + str(e), 2)
        #errorMsg()

    finally:
        try:
            conn.close()
            del conn

        except:
            pass

        return result

## ===================================================================================
def GetNewExtentsGpkg(newDB, layerList, conn, liteCur):
    # For geopackage (.gpkg) database only.
    # Use OGR to get extents for each spatial layer in the new database
    # Return information as a dictionary,
    # where key = layer name; value = tuple of extents (MinX, MinY, MaxX, MaxY)

    # For some reason this isn't working for Geopackage. Possible file lock?

    try:

        if bArcPy:
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
        errorMsg()
        return False

## ===================================================================================
def GetNewExtentsSpatialite(newDB, layerList, conn, liteCur):
    # For Spatialite.
    # Use OGR to get extents for each spatial layer in the new database
    # Return information as a dictionary,
    # where key = layer name; value = tuple of extents (MinX, MinY, MaxX, MaxY)
    #
    # Spatialite database currently has a 'SpatialIndex' table that is empty.
    # geometry_columns is populated
    # geometry_columns_auth is populated
    # geometry_columns_field_infos is empty
    # geometry_columns_statistics was populated in this function
    # geometry_columns_time is populated
    # vector_layers table is populated, including for sdv views.
    # vector_layers_field_infos is empty
    # vector_layers_statistics is populated. Looks like the geometry_columns_statistics table.
    # views_geometry_columns has sdv views

    # Found this query, need to try
    # UPDATE geometry_columns_statistics set last_verified = 0;
    # UpdateLayerStatistics('geometry_table_name');

    # spatialite> SELECT id, AsText( PointN(ExteriorRing( Envelope(geom)), 2 ) ) AS ring0 FROM aa_extents;
    try:
        if bArcPy:
            arcpy.SetProgressorLabel("Registering spatial extents...")

        spatialExtents = list()

        driver = ogr.GetDriverByName("SQLite")

        if driver is None:
            err = "Failed to get OGR inputDriver for " + newDB
            raise MyError(err)

        ds = driver.Open(newDB, 0)

        if ds is None:
            err = "Failed to open " + newDB + " using ogr without driver"
            raise MyError(err)

        # Try getting extent from sapolygon first
        layer = ds.GetLayer("sapolygon")
        featCnt = layer.GetFeatureCount()
        vals = list(layer.GetExtent())
        min_x, max_x, min_y, max_y = vals

        for layerName in layerList:
            layer = ds.GetLayer(layerName)

            if layer is None:
                err = "Failed to find " + layerName + " table using ogr"
                raise MyError(err)

            featCnt = layer.GetFeatureCount()

            if featCnt > 0:
                # Cheating a little by setting extents for all layers (with data) to same as sapolygon
                spatialExtents.append([min_x, min_y, max_x, max_y, layerName])

            else:
                # See if geopackage will accept zeros for the extent?
                # Currently I am assigning the extent values from sapolygon layer
                vals = [0, 0, 0, 0, layerName]
                #PrintMsg(".\tSpatial extent for " + layerName + ": " + str(vals), 1)
                spatialExtents.append(vals)

            del layer

        del ds
        del driver

        #return False

        # If this is a geopackage, use sqlite3 to update gpkg_contents with the spatial extents
        #conn = sqlite3.connect(newDB)
        #liteCur = conn.cursor()

        if len(spatialExtents) > 0:
            # ["sapolygon", "mupolygon", "muline", "mupoint", "featline", "featpoint"]
            PrintMsg(".\tRegistering spatial layers to the database", 0)

            # Update existing records
            sqlUpdate = "UPDATE geometry_columns_statistics SET extent_min_x=?, extent_min_y=?, extent_max_x=?, extent_max_y=? WHERE f_table_name=?"
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
        errorMsg()
        return False

## ===================================================================================
def FindField(theInput, chkField, bVerbose = False):
    # Check table or featureclass to see if specified field exists
    # If fully qualified name is found, return that
    # Set workspace before calling FindField
    try:
        if arcpy.Exists(theInput):
            theDesc = arcpy.Describe(theInput)
            theFields = theDesc.Fields

            for theField in theFields:
                theNameList = arcpy.ParseFieldName(theField.Name)
                theCnt = len(theNameList.split(",")) - 1
                theFieldname = theNameList.split(",")[theCnt].strip()

                if theFieldname.upper() == chkField.upper():
                    return theField.Name

            if bVerbose:
                PrintMsg("Failed to find column " + chkField + " in " + theInput, 2)

            return ""

        else:
            PrintMsg("\tInput layer not found", 0)
            return ""

    except:
        errorMsg()
        return ""

## ===================================================================================
def GetFCType(fc):
    # Determine featureclass type  featuretype and table fields
    # Rename featureclasses from old shapefile-based name to new, shorter name
    # Returns new featureclass name using DSS convention for geodatabase
    #
    # The check for table fields is the absolute minimum

    featureType = ""

    # Look for minimum list of required fields
    #
    if FindField(fc, "MUSYM"):
        hasMusym = True

    else:
        hasMusym = False

    if FindField(fc, "LKEY"):
        hasLkey = True

    else:
        hasLkey = False

    if FindField(fc, "FEATSYM"):
        hasFeatsym = True

    else:
        hasFeatsym = False

    try:
        fcName = os.path.basename(fc)
        theDescription = arcpy.Describe(fc)
        featType = theDescription.ShapeType

        # Mapunit Features
        if hasMusym:
            if featType == "Polygon" and fcName.upper() != "MUPOINT":
                dataType = "Mapunit Polygon"

            elif featType == "Polyline":
                dataType = "Mapunit Line"

            elif featType == "Point" or featType == "Multipoint" or fcName.upper() == "MUPOINT":
                dataType = "Mapunit Point"

            else:
                PrintMsg(fcName + " is an unidentified " + featType + " featureclass with an MUSYM field (GetFCName)", 2)
                featureType = ""

        # Survey Area Boundary
        if hasLkey:
            if featType == "Polygon":
                dataType = "Survey Boundary"

            else:
                PrintMsg(fcName + " is an unidentified " + featType + " featureclass with an LKEY field (GetFCName)", 2)
                dataType = ""

        # Special Features
        if hasFeatsym:
            # Special Feature Line
            if featType == "Polyline":
                dataType = "Special Feature Line"

            # Special Feature Point
            elif featType == "Point" or featType == "Multipoint":
                dataType = "Special Feature Point"

            else:
                PrintMsg(fcName + " is an unidentified " + featType + " featureclass with an FEATSYM field (GetFCName)", 2)
                dataType = ""

        return dataType

    except:
        errorMsg()
        return ""

## ===================================================================================
def main(inputFolder, surveyList, newDB, geogRegion, tmpFolder, bCompressed, bAppend, bTabularOnly):
    #
    # main function that handles the data processing.
    # Note: the order of spatial import can be handled two ways:
    #    1. If a soil survey map layer is used to define the list of survey areas, then sort
    #       those polygons spatially and generate the list of areasymbols.
    #    2. If only a list of survey areas is provided, iterate through each of the SSURGO datasets,
    #       getting the extents for each soilsa_a*.shp file and saving to a table or array. Sort that by XY.

    try:
        bVerbose = False

        start = time.time()
        importVersion = 2  # This is the SSURGO Import process version for this script

        PrintMsg(".", 0)
        PrintMsg("Preparing to import data into " + newDB + " using Import Version " + str(importVersion) + "...", 0)

        scriptPath = __file__  # should be the same as sys.argv[0] where sys.argv is a list.
        scriptFolder = os.path.dirname(scriptPath)
        global basePath  # used to set executable filename in the ImportShapefile functions
        basePath = os.path.dirname(scriptFolder)

        PrintMsg(".", 0)
        PrintMsg("Setting up environment for import process (" + os.path.basename(scriptPath) + ")...", 0)

        args = [inputFolder, surveyList, newDB, geogRegion, tmpFolder, bCompressed, bAppend, bTabularOnly]

        for arg in args:
            if arg is None or arg == '':
                raise MyError (os.path.basename(sys.argv[0]) + " is missing one or more input arguments")

            else:
                if bVerbose:
                    PrintMsg(".\targ: " + str(arg), 0)

        # This is the first version of a script that is 'Data Loader' function only.

        sys.tracebacklimit = 1
        codePage = 'iso-8859-1'  # allow csv reader to handle non-ascii characters. Currently this variable is not being used.

        # According to Gary Spivak, SDM downloads are UTF-8 and NASIS downloads are iso-8859-1
        # cp1252 also seemed to work well
        #codePage = 'utf-16' this did not work
        #
        # http://stackoverflow.com/questions/6539881/python-converting-from-iso-8859-1-latin1-to-utf-8
        # Next need to try: string.decode('iso-8859-1').encode('utf8')


        ##  Begin processing input SSURGO datasets located in the 'inputFolder'

        # Need to move this 'inventory' section to its own function
        dSubFolder = dict() # store subfolder name on areasymbol
        pathList = list()

        if surveyList is not None and len(surveyList) == 0:
            err = "At least one soil survey area input is required"
            raise MyError(err)

        if bTabularOnly:
            PrintMsg(".\tsurveyList: " + str(surveyList), 0)

            for subFolder in surveyList:
                areaSym = subFolder[-5:].upper()                          # SQLite mod that is probably not STATSGO compatible
                dSubFolder[areaSym] = subFolder
                tabPath = os.path.join( inputFolder, os.path.join( subFolder, "tabular"))

                if not tabPath in pathList:
                    # PrintMsg(".\tAdding " + tabPath + " to pathList", 0)
                    pathList.append(tabPath)

            PrintMsg(".\t" + str(len(pathList)) + " survey areas will imported in tabular-only mode", 0)



        # Spatial stuff
        extentList = list()
        mupolyList = list()
        mupointList = list()
        mulineList = list()
        sflineList = list()
        sfpointList = list()
        sapolyList = list()


        dShapeCount = dict()  # store counts for each shapefile

        # Save the total featurecount for all input shapefiles
        mupolyCnt = 0
        mulineCnt = 0
        mupointCnt = 0
        sflineCnt = 0
        sfpointCnt = 0
        sapolyCnt = 0

        # The 'Create SSURGO-Lite DB by Map' tool will skip this section because the SortSurveyAreas function
        # has already generated a spatial sort using the input survey boundary layer.
        #
        if surveyList is None:
            raise MyError("No survey areas to process")

        if bTabularOnly == False:
            PrintMsg(".", 0)
            PrintMsg("Setting import order for " + str(len(surveyList)) + " selected surveys...", 0)
            PrintMsg(".", 0)

            driver = ogr.GetDriverByName("ESRI Shapefile")

            if driver is None:
                err = "Failed to get OGR inputDriver for ESRI shapefile"
                raise MyError(err)

            areasymbolList = list()


            for subFolder in surveyList:

                # Req: inputFolder, subFolder
                # build the input shapefilenames for each SSURGO featureclass type using the
                # AREASYMBOL then confirm shapefile existence for each survey and append to final input list
                # used for the Append command. Use a separate list for each featureclass type so
                # that missing or empty shapefiles will not be included. A separate Append process is used for each featureclass type.

                areaSym = subFolder[-5:].upper()                          # SQLite mod that is probably not STATSGO compatible
                dSubFolder[areaSym] = subFolder
                shpPath = os.path.join( inputFolder, os.path.join( subFolder, "spatial"))
                mupolyName = "soilmu_a_" + areaSym.lower() + ".shp"
                mulineName = "soilmu_l_" + areaSym.lower() + ".shp"
                mupointName = "soilmu_p_" + areaSym.lower() + ".shp"
                sflineName = "soilsf_l_" + areaSym.lower() + ".shp"
                sfpointName = "soilsf_p_" + areaSym.lower() + ".shp"
                sapolyName = "soilsa_a_" + areaSym.lower() + ".shp"

                shpList = [mupolyName, mulineName, mupointName, sflineName, sfpointName]
                shpInfo = list()

                # First get extent from the soilsa_a* shapefile
                shpFile = os.path.join(shpPath, sapolyName)
                featCnt, ulX, ulY = GetExtentShp(driver, shpFile)

                if featCnt < 1:
                    raise MyError ("Problem getting survey boundary feature count for: '" + areaSym + "'")

                shpInfo.append(featCnt)

                for shpName in shpList:
                    featCnt = GetCountShp(driver, os.path.join(shpPath, shpName))
                    shpInfo.append(featCnt)

                dShapeCount[areaSym] = shpInfo # store list of feature counts for each shapefile

                if bArcPy:
                    msg = "Getting extent for " + areaSym.upper() + " survey area"
                    # PrintMsg(msg, 0)
                    arcpy.SetProgressorLabel(msg)

                extentList.append((areaSym, round(ulX, 5), round(ulY, 5)))
                areasymbolList.append(areaSym)  # unsorted list of areasymbols

                # End of get extent from each soilsa_a* shapefiles


            if len(extentList) < len(surveyList):
                err = "Problem with survey extent sort key"
                raise MyError(err)

            if len(surveyList) > 1:
                # Sort the upper-left coordinate list so that the drawing order of the merged layer
                # is a little more efficient
                extentList.sort(key=itemgetter(1), reverse=False)
                extentList.sort(key=itemgetter(2), reverse=True)

                # May be able to use the overall extents as an option for ST_Transform to assist with
                # finding the most appropriate geographic transformation
                minX = extentList[0][1]
                minY = extentList[1][2]
                maxX = extentList[-1][1]
                maxY = extentList[0][2]

                # Use extentList to create a spatially sorted list of areasymbols. Use to control SSA import order
                # PrintMsg(".\tSkipping spatial sort for ssa import", 0)

                # PrintMsg(".\tExtent list has " + str(len(extentList)) + " items", 0)
                areasymbolList = [sortValu[0] for sortValu in extentList]

            else:
                ds = driver.Open(shpFile, 0)
                layer = ds.GetLayerByIndex(0)
                featCnt = layer.GetFeatureCount()

                if featCnt > 0:
                    minX, maxX, minY, maxY = layer.GetExtent()  # ogr extents are not in the same order as arcpy

            # use this AOI in WKT format to try and set the appropriate geographic transformation for ST_Transform
            aoiWKT = "BuildMBR(" + str(minX) + ", " + str(minY) + ", " + str(maxX) + ", " + str(maxY) + ", 4326)"
            # PrintMsg(".\taoiWKT: " + aoiWKT, 0)



            # Create a series of lists that contain the found shapefiles to be merged, along with feature counts.
            # Currently using arcpy and is slow.
            # Would osgeo be faster or slower?
            #
            # PrintMsg(".\tCreating list of shapefiles to be imported for each survey area...", 0)

            if bArcPy:
                arcpy.SetProgressor("step", "Adding surveys to merge list", 1, len(areasymbolList))

            for areaSym in areasymbolList:
                # modify shpList = [sapolyName, mupolyName, mulineName, mupointName, sflineName, sfpointName]
                shpList.insert(0, sapolyName)
                subFolder = dSubFolder[areaSym.upper()]
                shpPath = os.path.join( inputFolder, os.path.join( subFolder, "spatial"))
                sapoly, mupoly, muline, mupoint, sfline, sfpoint = dShapeCount[areaSym]

                # soil polygon shapefile
                if mupoly > 0:
                    mupolyName = "soilmu_a_" + areaSym.lower() + ".shp"
                    shpFile = os.path.join(shpPath, mupolyName)

                    if not shpFile in mupolyList:
                        mupolyCnt += mupoly
                        mupolyList.append(shpFile)

                        if bArcPy:
                            arcpy.SetProgressorLabel("Adding " + areaSym.upper() + " survey to merge list")

                else:
                    raise MyError ("Problem getting map unit polygon feature count for: '" + areaSym + "'")

                # soil polyline shapefile
                if muline > 0:
                    mulineName = "soilmu_l_" + areaSym.lower() + ".shp"
                    shpFile = os.path.join(shpPath, mulineName)

                    if not shpFile in mulineList:
                        mulineCnt += muline
                        mulineList.append(shpFile)

                # soil point shapefile
                if mupoint > 0:
                    mupointName = "soilmu_p_" + areaSym.lower() + ".shp"
                    shpFile = os.path.join(shpPath, mupointName)

                    if not shpFile in mupointList:
                        mupointCnt += mupoint
                        mupointList.append(shpFile)

                # special feature line shapefile
                if sfline > 0:
                    sflineName = "soilsf_l_" + areaSym.lower() + ".shp"
                    shpFile = os.path.join(shpPath, sflineName)

                    if not shpFile in sflineList:
                        sflineCnt += sfline
                        sflineList.append(shpFile)

                # special feature point shapefile
                if sfpoint > 0:
                    sfpointName = "soilsf_p" + areaSym.lower() + ".shp"
                    shpFile = os.path.join(shpPath, sflineName)

                    if not shpFile in sfpointList:
                        sfpointCnt += sfpoint
                        sfpointList.append(shpFile)

                # soil survey boundary shapefile
                if sapoly > 0:
                    sapolyName = "soilsa_a_" + areaSym.lower() + ".shp"
                    shpFile = os.path.join(shpPath, sapolyName)

                    if not shpFile in sapolyList:
                        sapolyCnt += sapoly
                        sapolyList.append(shpFile)

                # input soil survey Template database
                # use database path, even if it doesn't exist. It will be used
                # to actually define the location of the tabular folder and textfiles
                # probably need to fix this later
                #
                tabPath = os.path.join( inputFolder, os.path.join( subFolder, "tabular"))

                if not tabPath in pathList:
                    pathList.append(tabPath)

                arcpy.SetProgressorPosition()

            featCnt = (mupolyCnt, mulineCnt, mupointCnt, sflineCnt, sfpointCnt, sapolyCnt)  # 0 mupoly, 1 muline, 2 mupoint, 3 sfline, 4 sfpoint, 5 sapoly

            theMsg = ".\tTime for setup and prep: " + elapsedTime(start)
            PrintMsg(theMsg, 0)

            time.sleep(1)
            arcpy.ResetProgressor()

        if len(mupolyList) > 0 or bTabularOnly:
            # Convert all shapefiles to a single geometry table
            # PrintMsg(".\tmupolyList: " + str(mupolyList), 0)

            gdbName = os.path.basename(newDB)
            outFolder = os.path.dirname(newDB)
            newDB = os.path.join(outFolder, gdbName)

            # End of spatial import

            # Successfully created a new database
            # Merge all existing shapefiles to file geodatabase featureclasses
            #
            PrintMsg(".\tCreating new database connection...", 0)
            conn = sqlite3.connect(newDB)
            conn.enable_load_extension(True)
            liteCur = conn.cursor()
            PrintMsg(".\tTurning ON foreign key constraints and setting other database modes...", 0)
            conn.execute("PRAGMA foreign_keys = ON;") # PRAGMA foreign_key_check(table-name);
            conn.execute("PRAGMA journal_mode = OFF;")
            conn.execute("PRAGMA synchronous = OFF;")
            conn.execute("PRAGMA locking_mode = EXCLUSIVE;")
            conn.execute("PRAGMA temp_store = MEMORY")
            bSet = SetCacheSize(conn, liteCur)

            # Drop existing attribute indexes from new database
            createSQLs = DropIndexes(conn, liteCur)

            if len(createSQLs) == 0:
                PrintMsg(".\tNo attribute indexes exist in this new database", 0)
                raise MyError("")  # remove this when the drop is working correctly

            tableList = GetTableList(liteCur)

            if 'geometry_columns' in tableList:
                dbType = "spatialite"

            elif 'gpkg_contents' in tableList:
                dbType = 'gpkg'

            else:
                dbType = ""

            dbName, dbExt = os.path.splitext(os.path.basename(newDB))

            # Should probably open database connection here, and pass down liteCur to ImportMDTabular and ImportTabular functions.
            #if not arcpy.Exists(newDB):
            if not os.path.exists(newDB):
                err = "Could not find " + newDB + " to append tables to"
                raise MyError(err)

            bTabular = ImportTabularSQL(newDB, pathList, importVersion, tableList, conn, liteCur)

            if bTabular == False:
                raise MyError("Failed to import all data to SSURGO-Lite DB. Tabular import error.")

            #PrintMsg(".\tUpdating attribute indexes before spatial data loading...", 0)
            # Query optimization and indexes: https://www.sqlite.org/optoverview.html

            if len(createSQLs) > 0:
                conn = sqlite3.connect(newDB)
                conn.enable_load_extension(True)

                liteCur = conn.cursor()
                # PrintMsg(".\tTurning ON foreign key constraints and setting other database modes...", 0)
                conn.execute("PRAGMA foreign_keys = ON;") # PRAGMA foreign_key_check(table-name);
                conn.execute("PRAGMA journal_mode = OFF;")
                conn.execute("PRAGMA synchronous = OFF;")
                conn.execute("PRAGMA locking_mode = EXCLUSIVE;")
                conn.execute("PRAGMA temp_store = MEMORY")
                #conn.execute("PRAGMA temp_store = FILE")  # may need to switch to this option if database is big
                bSet = SetCacheSize(conn, liteCur)

                bIndexed = RestoreAttributeIndexes(conn, liteCur, createSQLs)

                if not bIndexed:
                    PrintMsg(".\tFailed to restore attribute indexes", 1)

                if dbType == 'spatialite':
                    # Get geometry types from geometry_columns table
                    dGeometryTypes = GetGeometryTypes(liteCur)

                conn.close()
                del liteCur
                del conn

            if bTabularOnly == False and len(mupolyList) > 0:
                if bArcPy and bAppend:
                    # Use arcpy.Append_management to import shapefiles, regardless of database spatial format.
                    #
                    PrintMsg(".\tNeed to confirm that AppendFeatures_ArcPy also updates spatial indexes and extents", 0)
                    bProj = SetOutputCoordinateSystem(geogRegion, newDB)
                    PrintMsg(".\tOutput CSR: " + env.outputCoordinateSystem.name, 0)
                    PrintMsg(".\tTM: " + str(env.geographicTransformations), 0)
                    bSpatial = AppendFeatures_ArcPy(newDB, geogRegion, mupolyList, mulineList, mupointList, sflineList, sfpointList, sapolyList, featCnt)

                else:
                    if dbType == 'spatialite':
                        # Using Spatialite database

                        try:
                            # Trying to address locked database when more than one SSA is imported
                            dbConn.close()
                            del dbConn
                            del liteCur

                        except:
                            pass

                        # Spatial indexes are recreated as part of ImportShapefiles function, called by AppendFeatures_Spatialite
                        # This works well, but still not quite as fast as AppendFeatures_ArcPy.
                        # Spatial indexes and extents are updated after all shapefiles have been imported by 'ImportShapefiles' function.

                        bSpatial = AppendFeatures_Spatialite(newDB, geogRegion, aoiWKT, mupolyList, mulineList, mupointList, sflineList, sfpointList, sapolyList, bCompressed, dGeometryTypes)

                        # See if ogr2ogr will work with spatialite database. Initial tests failed, but still warrant further investigation.
                        # bSpatial = AppendFeatures_OGR(newDB, dbType, geogRegion, mupolyList, mulineList, mupointList, sflineList, sfpointList, sapolyList, featCnt)

                        if bSpatial == False:
                            return False

                    elif dbType == "gpkg":
                        # Using Geopackage database
                        #PrintMsg(".\tUsing Ogr2Ogr method", 0)
                        bSpatial = AppendFeatures_OGR(newDB, dbType, geogRegion, mupolyList, mulineList, mupointList, sflineList, sfpointList, sapolyList, featCnt)

                    else:
                        PrintMsg(".\tdbType: " + str(dbType), 0)
                #
                # Update spatial extents for geopackage database
                # Need to move this to the appropriate function
                #
                if bSpatial == True:
                    if dbType == "gpkg":

                        # Create new database connection, just for updating spatial layer foreign keys
                        conn = sqlite3.connect(newDB)
                        conn.enable_load_extension(True)
                        liteCur = conn.cursor()

                        # Get survey area count for each layer

                        saCounts = list()

                        for saList in [sapolyList, mupolyList, mulineList, mupointList, sflineList, sfpointList]:
                            saCounts.append(len(saList))

                        # Get extents for each new layer
                        layerList = ["sapolygon", "mupolygon", "muline", "mupoint", "featline", "featpoint"]

                        PrintMsg(".\t", 0)
                        PrintMsg("Updating extents for each spatial layer", 0)
                        bExtents = GetNewExtentsGpkg(newDB, layerList, conn, liteCur) # , saCounts, spatialExtents

                    else:
                        # For spatialite databases, assuming that spatial indexing is being handled in another function.
                        pass

                else:
                    PrintMsg("Failed to import all data to SSURGO-Lite DB.", 2)
                    return False


            PrintMsg(".", 0)

            if bTabularOnly:
                PrintMsg("All tabular data have been imported...", 0)

            else:
                PrintMsg("All tabular and spatial data have been imported...", 0)

            arcpy.ResetProgressor()
            #PrintMsg(" \nSuccessfully created a geodatabase containing the following surveys: " + queryInfo, 0)

            if len(createSQLs) > 0:

                # Need to assess the need for Vacuum in a 'new' database.
                # What about appending additional data to an existing database?
                # I would assume Vacuum would be critical for when replacing existing data in an existing database.
                #
                #PrintMsg(".\tSkipping database compact...", 0)
                bCompact = CompactDatabase(newDB, tmpFolder)

                if bCompact == False:
                    raise MyError("Failed to compact new database")

            else:
                # no previous indexes, trying creating new ones from metadata tables
                bIndexed = CreateNewIndexes(conn, liteCur)

                if not bIndexed:
                    PrintMsg(".\tFailed to create new attribute indexes", 1)
        else:
            PrintMsg("mupolyList is empty", 0)

        #PrintMsg(".", 0)
        #PrintMsg("Output database:  " + newDB + "  \n ", 0)
        arcpy.SetProgressorLabel("Finished updating database")

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
import sys, string, os, traceback, locale, math, time, datetime, csv, shutil
from operator import itemgetter, attrgetter
from osgeo import ogr
from osgeo import gdal
ogr.UseExceptions()
import subprocess
import sqlite3
sqlite3.enable_callback_tracebacks(True)

try:
    # Get arguments for arcpy script
    import arcpy
    bArcPy = True
    inputFolder = arcpy.GetParameterAsText(0)     # location of SSURGO datasets containing spatial folders
    ssaLayer = arcpy.GetParameterAsText(1)        # Test to see if I can sort the ssaLayer when using the 'Create SSURGO-Lite DB by Map' tool
    templateName = arcpy.GetParameterAsText(2)    # empty SQLite database with SSSURGO schema
    newDB = arcpy.GetParameterAsText(3)           # fullpath for the new output geodatabase
    geogRegion = arcpy.GetParameterAsText(4)      # Geographic Region used to set output coordinate system
    surveyList = arcpy.GetParameter(5)            # list of SSURGO dataset folder names to be proccessed (e.g. 'soil_ne109')
    tmpFolder = arcpy.GetParameterAsText(6)       # Folder where vacuum will take place
    bCompressed = arcpy.GetParameter(7)          # Compress polygon geometries on import
    bAppend = arcpy.GetParameter(8)               # Use arcpy.Append command to import spatial data. Default = False.
    bTabularOnly = arcpy.GetParameter(9)          # Skip shapefile import. Only tabular data will be imported during this session.

except:
    # Get arguments for non-arcpy script
    bArcPy = False
    inputFolder = str(sys.argv[1])
    ssaLayer = str(sys.argv[2])  # is this being used now?
    templateName = str(sys.argv[3])
    newDB = str(sys.argv[4])
    geogRegion = str(sys.argv[5])
    surveyList = sys.argv[6]          # surveyList could be a semi-colon delimited string
    tmpFolder = str(sys.argv[7])
    bCompressed = sys.argv[8]        # boolean values may be strings 'true' or 'false'. Need to convert to Python booleans?
    bAppend = sys.argv[9]
    bTabularOnly = sys.argv[10]

    if bCompressed == 'true':
        bCompressed = True
    else:
        bCompressed = False

    if bAppend == 'true':
        bAppend = True
    else:
        bAppend = False

    if bTabularOnly == 'true':
        bTabularOnly = True
    else:
        bTabularOnly = False


try:
    if __name__ == "__main__":

        args = [inputFolder, ssaLayer, templateName, newDB, geogRegion, surveyList, tmpFolder, bCompressed, bAppend, bTabularOnly]

        for arg in args:
            if arg is None or arg == '':
                raise MyError (os.path.basename(sys.argv[0]) + " is missing one or more input arguments")

            else:
                PrintMsg(".\t" + str(arg), 0)

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
        PrintMsg(".", 0)
        PrintMsg(".\tBase folder: " + basePath, 0)
        PrintMsg(".", 0)

        bGood = main(inputFolder, surveyList, newDB, geogRegion, tmpFolder, templateDB, bCompressed, bAppend, bTabularOnly)

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

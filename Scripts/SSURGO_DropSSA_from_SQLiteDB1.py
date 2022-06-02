# SSURGO_Convert_to_SQLiteDB6.py

# Import data from WSS-SSURGO downloads (.txt and .shp) to an SQLite database.
#
# Using a template database with attribute table schema. Month table is pre-populated.
#
# Tabular import is sequential by table iterating through all survey areas.
#
# This script has functions that can handle OGR spatial import or arcpy spatial import.
#
# July 1. Added spatialite commandline scripting to the AppendFeatures_Spatialite function.
# AppendFeatures_ArcPy appears to be broken, at least for some of the template databases.
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
def errorMsg(excInfo):
    # Capture system error from traceback and then exit
    # Should I be passing in the value for sys.exc_info()?
    try:


        # excInfo object is a tuple that should contain 3 values
        # 0: type gets the type of the exception being handled (a subclass of BaseException)
        # 1: value gets the exception instance (an instance of the exception type)
        # 2: traceback gets a traceback object which encapsulates the call stack at the point where the exception originally occurred

        if not excInfo is None:

            #PrintMsg(70 * "=", 2)
            exc_type, exc_value, exc_tb = sys.exc_info()

            for tb_info in traceback.extract_tb(exc_tb):
                filename, linenum, funcname, source = tb_info
                #errInfo = str(sys.exc_info()[1])

                if funcname != '<module>':
                    funcname = funcname + '()'

                if source.strip().startswith("raise MyError"):
                    # raised error
                    #PrintMsg(errInfo + " (function " + sys._getframe().f_code.co_name + ")", 2)
                    PrintMsg(exc_value + " (function " + sys._getframe().f_code.co_name + ")", 2)

                else:
                    # arcpy.Execute error
                    #PrintMsg("Error '" + errInfo + "' in " + os.path.basename(filename) + \
                    #     " at line number " + str(linenum) + ":" + "\n" + source, 2)
                    PrintMsg("Error '" + exc_value + "' in " + os.path.basename(filename) + \
                         " at line number " + str(linenum) + ":" + "\n" + source, 2)

            #PrintMsg(70 * "=", 2)

            return

    except MyError as e:
        PrintMsg(str(e), 2)

    except:
        PrintMsg(".\tUnhandled error", 2)

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

        return

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

    #

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
        errorMsg(sys.exc_info())
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
def SetOutputCoordinateSystem(inLayer, geogRegion):
    #
    # Not being used any more!
    #
    # The GetXML function is now used to set the XML workspace
    # document and a single NAD1983 to WGS1984 datum transformation (ITRF00) is now being used.
    #
    # Below is a description of the 2013 settings
    # Set a hard-coded output coordinate system (Geographic WGS 1984)
    # Set an ESRI datum transformation method for NAD1983 to WGS1984
    # Based upon ESRI 10.1 documentation and the methods that were used to
    # project SDM featureclasses during the transition from ArcSDE to SQL Server spatial
    #
    #   CONUS - NAD_1983_To_WGS_1984_5
    #   Hawaii and American Samoa- NAD_1983_To_WGS_1984_3
    #   Alaska - NAD_1983_To_WGS_1984_5
    #   Puerto Rico and U.S. Virgin Islands - NAD_1983_To_WGS_1984_5
    #   Other  - NAD_1983_To_WGS_1984_1 (shouldn't run into this case)

    try:

        PrintMsg(" \nHardcoded to ignore geogRegion setting. Currently, output coordinate system will be Geographic WGS 1984.")
        outputSR = arcpy.SpatialReference(4326)        # GCS WGS 1984
        # Get the desired output geographic coordinate system name
        outputGCS = outputSR.GCS.name

        # Describe the input layer and get the input layer's spatial reference, other properties
        desc = arcpy.Describe(inLayer)
        dType = desc.dataType
        sr = desc.spatialReference
        srType = sr.type.upper()
        inputGCS = sr.GCS.name

        # Print name of input layer and dataype
        if dType.upper() == "FEATURELAYER":
            #PrintMsg(" \nInput " + dType + ": " + desc.nameString, 0)
            inputName = desc.nameString

        elif dType.upper() == "FEATURECLASS":
            #PrintMsg(" \nInput " + dType + ": " + desc.baseName, 0)
            inputName = desc.baseName

        else:
            #PrintMsg(" \nInput " + dType + ": " + desc.name, 0)
            inputName = desc.name

        if outputGCS == inputGCS:
            # input and output geographic coordinate systems are the same
            # no datum transformation required
            #PrintMsg(" \nNo datum transformation required", 0)
            tm = ""

        else:
            # Different input and output geographic coordinate systems, set
            # environment to unproject to WGS 1984, matching Soil Data Mart
            tm = "WGS_1984_(ITRF00)_To_NAD_1983"

        # These next two lines set the output coordinate system environment
        arcpy.env.outputCoordinateSystem = outputSR
        arcpy.env.geographicTransformations = tm

        return True

    except MyError as e:
        # Example: raise MyError("This is an error message")
        PrintMsg(str(e) + " \n", 2)
        return False

    except:
        errorMsg(sys.exc_info())
        return False

## ===================================================================================
def GetTableList(inputDB, conn, liteCur):
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
def GetCount(inputDB, tbl):
    # Query sqlite database and return the record count for the specified table
    #
    try:
        recordCount = -1

        tblList = list()

        queryCount = "SELECT COUNT(*) FROM " + tbl + "; "
        conn = sqlite3.connect(inputDB)
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
        errorMsg(sys.exc_info())
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
def DropSSA(inputDB, areasymbolList):
    # Drop any survey areas that already exist. Duplicate records are not allowed.
    #
    # Also ran into issue with muaggatt table which has no cascading delete or foreign key
    #
    try:
        result = False

        PrintMsg(".\tDropping the following soil survey areas: " + ", ".join(areasymbolList), 0)

        if len(areasymbolList) == 1:
            areaSyms = "('" + areasymbolList[0] + "')"

        else:
            areaSyms = str(tuple(areasymbolList))

        PrintMsg(".\tRunning DropSSA function...", 0)
        time.sleep(5)
        slExe = r"C:\Program Files\Utilities\spatialite-tools-5.0.0-win-amd64\spatialite.exe"

        queryDistr = "SELECT distmdkey FROM distlegendmd WHERE areasymbol IN " + areaSyms + ";"
        queryLkey = "SELECT lkey FROM legend WHERE areasymbol IN " + areaSyms + ";"
        queryDrop1 = "DELETE FROM legend WHERE areasymbol IN " + areaSyms + "; "     # this results in foreign key constraint error.
        queryDrop2 = "DELETE FROM sacatalog WHERE areasymbol IN " + areaSyms + "; "  # this works.

        conn = sqlite3.connect(inputDB)
        conn.execute("PRAGMA foreign_keys = ON;") # PRAGMA foreign_key_check(table-name);
        liteCur = conn.cursor()

        #createSQLs = DropIndexes(conn, liteCur)

        PrintMsg(".\tGetting distmdkeys from distlegendmd table", 0)
        # PrintMsg(".\t\t" + queryDistr, 0)
        liteCur.execute(queryDistr)
        mdResult = liteCur.fetchall()

        #PrintMsg(".\tmdResult: " + str(mdResult), 0)

        if not mdResult is None:
            mdList = [row[0] for row in mdResult]

            if len(mdList) > 1:
                mdKeys = str(tuple(mdList))

            else:
                mdKeys = "(" + str(mdList[0]) + ")"

            PrintMsg(".\tdistmdkeys: " + mdKeys, 0)

            PrintMsg(".\tGetting legend key...", 0)
            #PrintMsg(".\t\t" + queryLkey, 0)
            liteCur.execute(queryLkey)
            lkResult = liteCur.fetchall()
            PrintMsg(".\tlkResult: " + str(lkResult), 0)

            if len(lkResult) > 0:
                #lKey = str(lkResult[0])
                lkeyList = [row[0] for row in lkResult]

                if len(lkeyList) > 1:
                    lKeys = str(tuple(lkeyList))

                else:
                    lKeys = "(" + str(lkeyList[0]) + ")"

                PrintMsg(".\tLegend key(s): " + str(lKeys), 0)

                # I need to switch this up so iteration is by lkey
                # This will prevent over-running the drop muaggatt records with a
                # huge list of mukeys.
                #
                if len(lkeyList) > 0:
                    # The following query would have to be executed before legend table is processed
                    dropMuaggatt = "DELETE FROM muaggatt WHERE mukey IN (SELECT M.mukey FROM mapunit AS M WHERE M.lkey IN " + lKeys + ");"
                    PrintMsg(".\tDropping muaggatt records using '" + dropMuaggatt + "'...", 0)
                    #PrintMsg(".\tDropping muaggatt records using '" + dropMuaggatt + "'...", 0)
                    result = subprocess.run([slExe, inputDB, dropMuaggatt], capture_output=True, text=True)  # new
                    #resultOut = result.stdout
                    #resultError = result.stderr
                    #resultCode = result.check_returncode()
                    time.sleep(3)

                else:
                    err = "Failed to get list of legend keys"
                    raise MyError(err)

                PrintMsg(".\tDropping related attribute records from legend for survey area(s): " + areaSyms, 0)
                result = subprocess.run([slExe, inputDB, queryDrop1], capture_output=True, text=True)  # new
                #resultOut = result.stdout
                #resultError = result.stderr
                #resultCode = result.check_returncode()
                PrintMsg(".\tDropped related attribute records from legend for survey area(s): " + areaSyms, 0)
                #PrintMsg(".\t\tReturn code: " + str(resultCode), 0)
                #PrintMsg(".\t\tStdErr: " + str(resultError), 0)
                result = True
                time.sleep(2)

                # This definitely needs to be spatialite command, but not sure about the rest
                PrintMsg(".\tDropping related spatial records from sacatalog for survey area(s): " + areaSyms, 0)
                result = subprocess.run([slExe, inputDB, queryDrop2], capture_output=True, text=True)  # new
                #resultOut = result.stdout
                #resultError = result.stderr
                #resultCode = result.check_returncode()
                #PrintMsg(".\tDropped related spatial records from sacatalog for survey area(s): " + areaSyms, 0)
                #PrintMsg(".\t\tReturn code: " + str(resultCode), 0)
                #PrintMsg(".\t\tStdErr: " + str(resultError), 0)




            else:
                PrintMsg(".\tUnable to get legend keys...", 0)
                mdKeys = ""
                lKeys = ""
                muKeys = ""

        else:
            PrintMsg(".\tUnable to get dismdkeys...", 0)
            mdKeys = ""
            lKeys = ""
            muKeys = ""

        # Need to use lkey to get list of mukeys for use with muaggatt table
        #

        conn.close()
        del conn

        #PrintMsg(".\tNeed mdKeys next", 0)
        PrintMsg(".\tmdKeys: " + str(mdKeys), 0)

        if mdKeys != "":

            queryDrop3 = "DELETE FROM distmd WHERE distmdkey IN " + mdKeys
            PrintMsg(".\tDropping related records from distmd for survey area(s): " + areaSyms, 0)
            result = subprocess.run([slExe, inputDB, queryDrop3], capture_output=True, text=True)  # new
            #resultOut = result.stdout
            #resultError = result.stderr
            #resultCode = result.check_returncode()
            #PrintMsg(".\tDropped related records from distmd for survey area(s): " + areaSyms, 0)

            #PrintMsg(".\tDropping related attribute records from legend for survey area(s): " + areaSyms, 0)
            #result = subprocess.run([slExe, inputDB, queryDrop1], capture_output=True, text=True)  # new
            #resultOut = result.stdout
            #resultError = result.stderr
            #resultCode = result.check_returncode()
            #PrintMsg(".\tDropped related attribute records from legend for survey area(s): " + areaSyms, 0)
            #PrintMsg(".\t\tReturn code: " + str(resultCode), 0)
            #PrintMsg(".\t\tStdErr: " + str(resultError), 0)
            PrintMsg(".\tFinished dropping data from this database", 0)
            result = True

        else:
            # Failed to get distmdkey. Probably this survey area does not exist in this database
            PrintMsg(".\tSkipping drop. There is no match in distribution metdata for " + areaSyms, 0)
            #time.sleep(5)
            result = True

        time.sleep(1)
        #PrintMsg(".\tEnd of function", 0)
        return result

    except MyError as e:
        PrintMsg(str(e), 2)

    except sqlite3.IntegrityError as err:
        PrintMsg(".\tSQLite IntegrityError: ", 2)
        time.sleep(5)
        PrintMsg(".\t" + err.args[0], 2)
        time.sleep(5)

    except sqlite3.OperationalError as err:
        # Even after a 5 second pause, I'm getting an error from SELECT COUNT.
        # no such table: xx_mupolygon
        PrintMsg(".\tSQLite OperationalError: ", 2)
        time.sleep(5)
        PrintMsg(".\t" + err.args[0], 2)
        time.sleep(5)

    except sqlite3.Error as err:
        PrintMsg(".\tSQLite Error: ", 2)
        time.sleep(5)
        msg = err.args[0]
        PrintMsg(".\t" + msg, 2)
        time.sleep(5)

    except subprocess.SubProcessError as err:
        PrintMsg(".\tSQubProcess Error: ", 2)
        time.sleep(5)
        msg = err.args[0]
        PrintMsg(".\t" + msg, 2)
        time.sleep(5)

    except:
        PrintMsg(".\tException in DropSSA", 2)
        errorMsg(sys.exc_info())

    finally:
        #PrintMsg(".\tFinally now", 0)
        return result

## ===================================================================================
def CompactDatabase(inputDB):
    # Query sqlite database and return a list of tables
    #
    # I need to check filesize of database and make sure there is adequate diskspace before
    # executing VACUUM. conus db before vac: 178.392500 GB and after vac: 171.5 GB
    # fileSizeMB = (os.stat(inputDB).st_size / (1024.0 * 1024.0))
    # Having some problems getting disk free space with shutil.disk_usage(path)
    # Need to triple quote path and use \\
    # shutil.disk_usage(path) returns a tuple: (total, used, free) in bytes
    # To change the temp directory, use either TMPDIR setting or for
    # For older verions of sqlite3 library use: PRAGMA temp_store_directory = 'directory-name';

    # Looks like most of the TEMP space will be reclaimed after the VACUUM is complete.
    #
    try:
        arcpy.SetProgressorLabel("Compacting new database...")
        PrintMsg(".", 0)
        PrintMsg("Compacting new database...")

        dbSize = (os.stat(inputDB).st_size / (1024.0 * 1024.0))  # units are MB
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


        conn = sqlite3.connect(inputDB)
        conn.execute("VACUUM;")
        conn.close()

        del conn
        dbSize = (os.stat(inputDB).st_size / (1024.0 * 1024.0))  # units are MB
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
def GetTemplateDate(inputDB, areaSym, liteCur):
    # Get SAVEREST date from previously existing Template database
    # Use it to compare with the date from the WSS dataset
    # If the existing database is same or newer, it will be kept and the WSS version skipped.
    # This function is also used to test the output geodatabase to make sure that
    # the tabular import process was successful.
    #
    try:
        if not arcpy.Exists(inputDB):
            return 0

        dbDate = 0
        #whereClause = "UPPER(AREASYMBOL) = '" + areaSym.upper() + "'"
        #PrintMsg(" \nWhereClause for sacatalog: " + areaSym, 1)
        querySaverest = "SELECT saverest FROM sacatalog WHERE areasymbol = '?'"
        liteCur.execute(querySave, areaSym)
        row = liteCur.fetchone()
        dbDate = str(row[0]).split(" ")[0]
        return dbDate

    except:
        errorMsg(sys.exc_info())
        return 0

## ===================================================================================
def SSURGOVersionTxt(tabularFolder):
    # For future use. Should really create a new table for SSURGO-Lite database in order to implement properly.
    #
    # Get SSURGO version from the Template database "SYSTEM Template Database Information" table
    # or from the tabular/version.txt file, depending upon which is being imported.
    # Compare the version number (first digit) to a hardcoded version number which should
    # be theoretically tied to the XML workspace document that accompanies the scripts.
    #
    # Need to research NASIS-SSURGO export and Staging Server export.
    # Downloads should be a version.txt in both spatial and tabular folders.
    #
    # WSS download:
    # spatial\version.txt contains one line: 2.3.3
    # tabular\version.txt contains one line: 2.3.3
    #

    try:
        # Get SSURGOversion number from version.txt
        versionTxt = os.path.join(tabularFolder, "version.txt")

        if arcpy.Exists(versionTxt):
            # read just the first line of the version.txt file
            fh = open(versionTxt, "r")
            #txtVersion = int(fh.readline().split(".")[0])
            txtVersion = fh.readline().strip()
            fh.close()
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
        errorMsg(sys.exc_info())
        return 0

## ===================================================================================
def SSURGOVersionDB(templateDB):
    # For future use. Should really create a new table for SSURGO-Lite DB in order to implement properly.
    #
    # Get SSURGO version from the Template database "SYSTEM Template Database Information" table

    try:
        if not arcpy.Exists(templateDB):
            err = "Missing input database (" + inputDB + ")"
            raise MyError(err)

        systemInfo = os.path.join(templateDB, "SYSTEM - Template Database Information")

        if arcpy.Exists(systemInfo):
            # Get SSURGO Version from template database
            dbVersion = 0

            with arcpy.da.SearchCursor(systemInfo, "*", "") as srcCursor:
                for rec in srcCursor:
                    if rec[0] == "SSURGO Version":
                        dbVersion = int(str(rec[2]).split(".")[0])
                        #PrintMsg("\tSSURGO Version from DB: " + dbVersion, 1)

            del systemInfo
            del templateDB
            return dbVersion

        else:
            # Unable to open SYSTEM table in existing dataset
            # Warn user but continue
            err = "Unable to open 'SYSTEM - Template Database Information'"
            raise MyError(err)

    except MyError as e:
        # Example: raise MyError("This is an error message")
        PrintMsg(str(e), 2)
        return 0

    except:
        errorMsg(sys.exc_info())
        return 0


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

## ===============================================================================================================
def GetTableInfoGDB(inputDB):
    # For mobile geodatabase, get table name, table alias, iefilename using arcpy data access cursor
    #
    # Retrieve physical and alias names from MDSTATTABS table and assigns them to a blank dictionary.
    # Stores physical names (key) and aliases (value) in a Python dictionary i.e. {chasshto:'Horizon AASHTO,chaashto'}
    # Fieldnames are Physical Name = AliasName,IEfilename

    try:
        tblInfo = dict()

        # Open mdstattabs table containing information for other SSURGO tables
        theMDTable = "mdstattabs"
        env.workspace = inputDB

        # Establishes a cursor for searching through field rows. A search cursor can be used to retrieve rows.
        # This method will return an enumeration object that will, in turn, hand out row objects
        if arcpy.Exists(os.path.join(inputDB, theMDTable)):

            fldNames = ["tabphyname","tablabel","iefilename"]
            # tblInfo[importFileName] = physicalName, aliasName
            with arcpy.da.SearchCursor(os.path.join(inputDB, theMDTable), fldNames) as rows:

                for row in rows:
                    # read each table record and assign 'tabphyname' and 'tablabel' to 2 variables
                    physicalName = row[0]
                    aliasName = row[1]
                    importFileName = row[2]

                    if not importFileName in tblInfo:
                        #PrintMsg("\t" + importFileName + ": " + physicalName, 1)
                        tblInfo[importFileName] = physicalName, aliasName

            del theMDTable

            return tblInfo

        else:
            # The mdstattabs table was not found
            raise MyError("Missing mdstattabs table")
            return tblInfo


    except MyError as e:
        # Example: raise MyError("This is an error message")
        PrintMsg(str(e), 2)
        return False

    except:
        errorMsg(sys.exc_info())
        return dict()


## ===============================================================================================================
def SetCacheSize(conn, liteCur):
    # Restore previous attribute indexes

    try:
        # Restore original attribute indexes
        PrintMsg(".", 0)
        PrintMsg("Setting cache size for indexing performance...", 0)

        queryCacheSize = "PRAGMA main.cache_size = -200000;"
        liteCur.execute(queryCacheSize)
        conn.commit()

        return True

    except MyError as e:
        # Example: raise MyError("This is an error message")
        PrintMsg(str(e), 2)
        return False

    except:
        errorMsg(sys.exc_info())
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
        errorMsg(sys.exc_info())
        return []

## ===============================================================================================================
def RestoreIndexes(conn, liteCur, createSQLs):
    # Restore previous attribute indexes

    try:
        # Restore original attribute indexes
        PrintMsg(".", 0)
        PrintMsg("Restoring previously existing attribute indexes for the new database...", 0)

        for createSQL in createSQLs:
            createSQL = createSQL.replace("CREATE INDEX", "CREATE INDEX IF NOT EXISTS")
            #PrintMsg(".\t" + createSQL, 0)
            liteCur.execute(createSQL)


        conn.commit()

        return True

    except MyError as e:
        # Example: raise MyError("This is an error message")
        PrintMsg(str(e), 2)
        return False

    except:
        errorMsg(sys.exc_info())
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

            arcpy.SetProgressorLabel("Finished with attribute indexes")

        else:
            raise MyError("Failed to get information needed for indexes")

        time.sleep(1)  # Sometimes the indexes aren't being created. Don't understand this.
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
        errorMsg(sys.exc_info())
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
        errorMsg(sys.exc_info())
        return dict()

## ===================================================================================
def DropSpatialIndex(ds, outLayerName):
    # Drop existing spatial index for layer
    # Uses OGR library

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
            #PrintMsg(".", 0)
            #PrintMsg(".\tUsing ogr to disable Spatial Index for " + outLayerName, 0)
            sqlDropIndex = "SELECT DisableSpatialIndex('" + outLayerName + "', 'shape')"
            #PrintMsg(".\tds.ExecuteSQL command: " + sqlDropIndex, 0)
            bDropped = ds.ExecuteSQL(sqlDropIndex)

##            # new, needs testing 2021-0612
##            sqlDropIndex = "SELECT DROP TABLE IF EXISTS idx_" + outLayerName + "_Geometry;"
##            bDropped = ds.ExecuteSQL(sqlDropIndex)
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
        errorMsg(sys.exc_info())
        return False

## ===================================================================================
def CreateSpatialIndex(ds, outLayerName):
    # Create spatial index on this spatial layer
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
        errorMsg(sys.exc_info())
        return False

## ===================================================================================
def SetOutputCoordinateSystem(AOI, newDB):
    # Define new output coordinate system
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
        # AOI
        # Lower 48 States: 'NAD_1983_Contiguous_USA_Albers': EPSG:5070
        # Alaska: Alaska Albers                            : EPSG:3338
        # Hawaii: Hawaii Albers Equal Area Conic           : EPSG:102007
        #
        result = False
        e = 0
        dEPSG = dict()
        dEPSG['Lower 48 States'] = 5070  # 102039
        #dEPSG['Lower 48 States'] = 6350  # 102039
        #dEPSG['Lower 48 States'] = 102039
        dEPSG['Alaska'] = 3338
        dEPSG['Hawaii'] = 102007 # ESRI Albers with apparent problem
        # dEPSG['Hawaii'] = 26963   # NAD_1983_StatePlane_Hawaii_3_FIPS_5103
        dEPSG['Puerto Rico and U.S. Virgin Islands'] = 5070
        dEPSG['Pacific Islands Area'] = 900914  # This is the SRID I used when I created the Western Pacific Islands CSR in the template db.
        dEPSG['World'] = 4326

        dEPSG["GCS NAD1983"]= 4269  # default gt is WGS_1984_(ITRF00)_To_NAD_1983 for kansas.
        # Then to go on to 6350 use a 2-step.  WGS_1984_(ITRF00)_To_NAD_1983 + WGS_1984_(ITRF08)_To_NAD_1983_2011

        # Another more direct route for 4326 to 6350 would be ITRF_2000_To_WGS_1984 + ITRF_2000_To_NAD_1983_2011

        e = 1
        # Assuming that the input coordinate system for SSURGO data and is GCS WGS1984 (4326)
        inputSR = arcpy.SpatialReference(4326)       # GCS WGS 1984
        inputDatum = inputSR.datumCode
        e = 2

        PrintMsg(".\tOutput SRID: " + str(dEPSG[AOI]), 0)

        outputSRID = dEPSG[AOI]

        if outputSRID == 900914:
            outputSR = arcpy.SpatialReference(os.path.join(scriptFolder, "Western_Pacific_Albers_Equal_Area_Conic.prj"))

        else:
            outputSR = arcpy.SpatialReference(outputSRID)

        e = 3
        if inputSR == outputSR:
            PrintMsg(".\tNo projection required", 0)
            env.outputCoordinateSystem = inputSR
            env.geographicTransformations = ""
            return True

        outputSRName = outputSR.name
        e = 4

        # Get list of valid geographic transformations when the input CSR and output CSR are different
        sGT = arcpy.ListTransformations(inputSR, outputSR )
        #PrintMsg(".\tGot transformations...", 0)

        if not sGT is None and len(sGT) > 0:
            tm = sGT[0]
            PrintMsg(".\tApplying geographic transformation: " + tm, 0)

        else:
            tm = ""

        e = 4
        conn = sqlite3.connect(newDB)
        liteCur = conn.cursor()


        # See if the database already has this coordinate system available to use
        sqlSRID = "SELECT COUNT(*) FROM spatial_ref_sys WHERE srid = " + str(outputSRID) + " ;"
        liteCur.execute(sqlSRID)
        bCSR = liteCur.fetchone()
        e = 5

        if bCSR:
            # database has the required outcoordinate system.
            # I should make all these present in the template.

            layerList = [["sapolygon"], ["mupolygon"], ["muline"], ["mupoint"], ["featline"], ["featpoint"]]

            e = 6

            sqlUpdate = "UPDATE geometry_columns SET srid = " + str(outputSRID) + " WHERE srid = 4326 AND f_table_name =?;"
            PrintMsg(".\tsqlUpdate: " + sqlUpdate, 0)
            e = 8
            liteCur.executemany(sqlUpdate, layerList)
            e = 9
            conn.commit()


            e = 10
            # These next two lines set the output coordinate system environment
            PrintMsg(".\tSetting output coordinate system to " + outputSR.name + " (srid:" + str(outputSRID) + ")", 0)
            time.sleep(5)
            env.outputCoordinateSystem = outputSR
            env.geographicTransformations = tm
            e = 11

        else:
            PrintMsg(".\tOutput database does not have the required coordinate system information needed to project the layers", 1)

        e = 12
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
        #errorMsg(sys.exc_info())

    finally:
        try:
            PrintMsg(".\tFinally closing database", 0)
            conn.close()
            del conn

        except:
            pass

        return result

## ===================================================================================
def GetNewExtentsGpkg(inputDB, layerList, conn, liteCur):
    # For geopackage (.gpkg) database only.
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
            err = "Failed to get OGR inputDriver for " + inputDB
            raise MyError(err)

        gdal.SetConfigOption('OGR_GPKG_FOREIGN_KEY_CHECK', 'NO')
        ds = driver.Open(inputDB, 0)

        if ds is None:
            # Not sure why I'm failing to open kansas_test02.gpkg. I've tried the GPKG and SQLite drivers.
            # Do I need to Vacuum after dropping the survey areas? Is there a spatial index problem?
            err = "Failed to open " + inputDB + " using ogr with " + driver.name + " driver"
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
            PrintMsg(".\tRegistering spatial layers to the geopackage database", 0)

            # Update existing records
            sqlUpdate = "UPDATE gpkg_contents SET min_x=?, min_y=?, max_x=?, max_y=? WHERE table_name=?"
            liteCur.executemany(sqlUpdate, spatialExtents)

            conn.commit()
            PrintMsg(".\tRan sqlUpdate", 0)
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
def GetNewExtentsSpatialite(inputDB, layerList, conn, liteCur):
    # For Spatialite.
    # Use OGR to get extents for each spatial layer in the new database
    # Return information as a dictionary,
    # where key = layer name; value = tuple of extents (MinX, MinY, MaxX, MaxY)
    #

    try:
        arcpy.SetProgressorLabel("Registering spatial extents...")
        #from osgeo import ogr, gdal, osr
        #gdal.UseExceptions()
        driverName = "SQLite"
        spatialExtents = list()

        driver = ogr.GetDriverByName(driverName)

        if driver is None:
            err = "Failed to get OGR - " + driverName + " inputDriver for " + inputDB
            raise MyError(err)

        ds = driver.Open(inputDB, 0)

        if ds is None:
            err = "Failed to open " + inputDB + " using ogr with " + driverName + " driver"
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

        if len(spatialExtents) > 0:
            # ["sapolygon", "mupolygon", "muline", "mupoint", "featline", "featpoint"]
            PrintMsg(".\tRegistering spatial layers to the spatialite database", 0)
            #PrintMsg(".\t" + str(spatialExtents), 0)

            # Update existing records
            sqlUpdate = "UPDATE geometry_columns_statistics SET extent_min_x=?, extent_min_y=?, extent_max_x=?, extent_max_y=? WHERE f_table_name=?"
            #PrintMsg(".\tsqlUpdate: " + sqlUpdate, 0)
            liteCur.executemany(sqlUpdate, spatialExtents)
            conn.commit()
            #PrintMsg(".\tUpdated spatial extents for the spatialite database", 0)
            time.sleep(5)

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
def StateNames():
    # Create dictionary object containing list of state abbreviations and their names that
    # will be used to name the file geodatabase.
    # For some areas such as Puerto Rico, U.S. Virgin Islands, Pacific Islands Area the
    # abbrevation is

    # NEED TO UPDATE THIS FUNCTION TO USE THE LAOVERLAP TABLE AREANAME. AREASYMBOL IS STATE ABBREV

    try:
        stDict = dict()
        stDict["AL"] = "Alabama"
        stDict["AK"] = "Alaska"
        stDict["AS"] = "American Samoa"
        stDict["AZ"] = "Arizona"
        stDict["AR"] = "Arkansas"
        stDict["CA"] = "California"
        stDict["CO"] = "Colorado"
        stDict["CT"] = "Connecticut"
        stDict["DC"] = "District of Columbia"
        stDict["DE"] = "Delaware"
        stDict["FL"] = "Florida"
        stDict["GA"] = "Georgia"
        stDict["HI"] = "Hawaii"
        stDict["ID"] = "Idaho"
        stDict["IL"] = "Illinois"
        stDict["IN"] = "Indiana"
        stDict["IA"] = "Iowa"
        stDict["KS"] = "Kansas"
        stDict["KY"] = "Kentucky"
        stDict["LA"] = "Louisiana"
        stDict["ME"] = "Maine"
        stDict["MD"] = "Maryland"
        stDict["MA"] = "Massachusetts"
        stDict["MI"] = "Michigan"
        stDict["MN"] = "Minnesota"
        stDict["MS"] = "Mississippi"
        stDict["MO"] = "Missouri"
        stDict["MT"] = "Montana"
        stDict["NE"] = "Nebraska"
        stDict["NV"] = "Nevada"
        stDict["NH"] = "New Hampshire"
        stDict["NJ"] = "New Jersey"
        stDict["NM"] = "New Mexico"
        stDict["NY"] = "New York"
        stDict["NC"] = "North Carolina"
        stDict["ND"] = "North Dakota"
        stDict["OH"] = "Ohio"
        stDict["OK"] = "Oklahoma"
        stDict["OR"] = "Oregon"
        stDict["PA"] = "Pennsylvania"
        stDict["PRUSVI"] = "Puerto Rico and U.S. Virgin Islands"
        stDict["RI"] = "Rhode Island"
        stDict["Sc"] = "South Carolina"
        stDict["SD"] ="South Dakota"
        stDict["TN"] = "Tennessee"
        stDict["TX"] = "Texas"
        stDict["UT"] = "Utah"
        stDict["VT"] = "Vermont"
        stDict["VA"] = "Virginia"
        stDict["WA"] = "Washington"
        stDict["WV"] = "West Virginia"
        stDict["WI"] = "Wisconsin"
        stDict["WY"] = "Wyoming"
        return stDict

    except:
        PrintMsg("\tFailed to create list of state abbreviations (CreateStateList)", 2)
        return stDict

## ===================================================================================
def SortSurveyAreaLayer(ssaLayer, surveyList):
    # For the 'Create SSURGO-Lite DB by Map', sort the input survey boundary layer by extent
    # Use that sorted order to regenerate the tabular and spatial import sequence
    #
    # Since the input ssaLayer is a map layer with possible selected set or whereclause, this
    # function uses arcpy to perform the spatial sort.
    #
    # Another alternative a little more 'open' would be to copy the ssaLayer to a shapefile in
    # the env.scratchFolder. Then I could use OGR library to iterate throug layer polygons and get extents.


    try:
        # first generate the areasymbol list by parsing the SSURGO download folder names (soil_areasymbol.lower())
        # assuming the areasymbol is foldername[5:]

        # These next few lines are still arcpy-dependent because they are referencing a map layer
        # They will need to be switched to sofware-compatible code if used with other than ArcGIS Pro.
        tmpFolder = env.scratchFolder
        aoiLayer = os.path.join(tmpFolder, "xx_soilsurvey_aoi.shp")

        if arcpy.Exists(aoiLayer):
            arcpy.Delete_management(aoiLayer)

        arcpy.CopyFeatures_management(ssaLayer, aoiLayer)

        # The rest is
        shpDriver = ogr.GetDriverByName("ESRI Shapefile")

        if shpDriver is None:
            err = "Failed to get OGR inputDriver for " + inputDB
            raise MyError(err)

        ds = shpDriver.Open(aoiLayer, 0)

        if ds is None:
            err = "Failed to open " + aoiLayer + " using ogr shapefile driver"
            raise MyError(err)

        # Get layer from ogr object (shapefile).
        # Assuming that this layer is polyogn and has an areasymbol column
        layer = ds.GetLayerByIndex(0)
        featCnt = layer.GetFeatureCount()

        # Iterate through features and create a list of areasymbols and their associated extents
        ssaCentroids = list()

        for feature in layer:
            areaSym = feature.GetField("areasymbol")
            wkt = feature.GetGeometryRef().Centroid().ExportToWkt()  # POINT (-95.6814062221088 45.2826974641629)
            x, y = wkt[ (wkt.find("(") + 1): wkt.find(")")].split(" ")
            #PrintMsg(".\t" + areaSym + ":\t" + str(x) + ", " + str(y), 0)  # MN151:	POINT (-95.6814062221088 45.2826974641629)
            ssaCentroids.append((areaSym, float(x), float(y)))

        sortedSurveyList = list()
        ssaCentroids.sort(key=itemgetter(1), reverse=False)
        ssaCentroids.sort(key=itemgetter(2), reverse=True)
        del shpDriver, ds

        if arcpy.Exists(aoiLayer):
            arcpy.Delete_management(aoiLayer)

        sortedSurveyList = [row[0] for row in ssaCentroids]

        # PrintMsg(".\tSpatially sorted survey list: " + str(sortedSurveyList), 0)

        if len(sortedSurveyList) == 0:
            raise MyError("Failed to get spatially sorted list of survey areas")

        return sortedSurveyList

    except MyError as e:
        PrintMsg(str(e), 2)
        return []

    except:
        errorMsg(sys.exc_info())
        return []

## ===================================================================================
def FindField(theInput, chkField, bVerbose = False):
    # Check table or featureclass to see if specified field exists
    # If fully qualified name is found, return that
    # Set workspace before calling FindField
    try:
        if arcpy.Exists(theInput):
            theDesc = arcpy.Describe(theInput)
            theFields = theDesc.Fields
            #theField = theFields.next()
            # Get the number of tokens in the fieldnames
            #theNameList = arcpy.ParseFieldName(theField.Name)
            #theCnt = len(theNameList.split(",")) - 1

            for theField in theFields:
                theNameList = arcpy.ParseFieldName(theField.Name)
                theCnt = len(theNameList.split(",")) - 1
                theFieldname = theNameList.split(",")[theCnt].strip()

                if theFieldname.upper() == chkField.upper():
                    return theField.Name

                #theField = theFields.next()

            if bVerbose:
                PrintMsg("Failed to find column " + chkField + " in " + theInput, 2)

            return ""

        else:
            PrintMsg("\tInput layer not found", 0)
            return ""

    except:
        errorMsg(sys.exc_info())
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
        errorMsg(sys.exc_info())
        return ""

## ===================================================================================
def main(inputFolder, surveyList, geogRegion, bClipped, tileInfo, inputDB, areasymbolList, bDiet):
    # main function that handles the data processing.
    # Note: the order of spatial import can be handled two ways:
    #    1. If a soil survey map layer is used to define the list of survey areas, then sort
    #       those polygons spatially and generate the list of areasymbols.
    #    2. If only a list of survey areas is provided, iterate through each of the SSURGO datasets,
    #       getting the extents for each soilsa_a*.shp file and saving to a table or array. Sort that by XY.

    try:

        env.overwriteOutput= True
        sys.tracebacklimit = 1
        codePage = 'iso-8859-1'  # allow csv reader to handle non-ascii characters. Currently this variable is not being used.

        # According to Gary Spivak, SDM downloads are UTF-8 and NASIS downloads are iso-8859-1
        # cp1252 also seemed to work well
        #codePage = 'utf-16' this did not work
        #
        # http://stackoverflow.com/questions/6539881/python-converting-from-iso-8859-1-latin1-to-utf-8
        # Next need to try: string.decode('iso-8859-1').encode('utf8')

        dbVersion = 2  # This is the SSURGO version supported by this script and the SSURGO-Lite schema (XML Workspace document)

        if inputDB.endswith(".gpkg"):
            # Drop spatial index first
            PrintMsg(".\tReady to drop spatial indexes...", 0)
            #layerList = ["sapolygon", "mupolygon", "muline", "mupoint", "featline", "featpoint"]
            driverName = "GPKG"
            driver = ogr.GetDriverByName(driverName)

            if driver is None:
                err = "Failed to get OGR driver - " + driverName + " for " + inputDB
                PrintMsg(err, 1)
                time.sleep(5)
                raise MyError(err)

            #gdal.SetConfigOption('OGR_GPKG_FOREIGN_KEY_CHECK', 'NO')
            ds = driver.Open(inputDB, 1)

            if ds is None:
                err = "Failed to open " + os.path.basename(inputDB) + " using ogr with " + driver.name + " driver"
                raise MyError(err)

            for outLayerName in ["sapolygon", "mupolygon", "muline", "mupoint", "featline", "featpoint"]:
                bDropped = DropSpatialIndex(ds, outLayerName)

                if bDropped == False:
                    PrintMsg(".\tFailed to drop spatial index for " + outLayerName, 1)

            del ds
            del driver

        PrintMsg(".\tDropping indexes before dropping survey areas")
        conn = sqlite3.connect(inputDB)
        liteCur = conn.cursor()
        #PrintMsg(".\t1s Opened sqlite3 connection", 0)
        createSQLs = DropIndexes(conn, liteCur)
        conn.close()
        del conn
        del liteCur


        # Drop any of these survey areas if they already exist
        #PrintMsg(".\tReady to drop SSAs - BYPASSED!", 0)

        bDropped = DropSSA(inputDB, areasymbolList)



        # Update spatial extents for each layer
        #
        PrintMsg(".\t1s Opening sqlite3 connection to database and preparing to update spatial extents for each layer", 0)
        time.sleep(1)

        conn = sqlite3.connect(inputDB)
        #conn.enable_load_extension(True)
        liteCur = conn.cursor()
        #PrintMsg(".\t1s Opened sqlite3 connection", 0)
        time.sleep(1)


        # Get extents for each new layer
        layerList = ["sapolygon", "mupolygon", "muline", "mupoint", "featline", "featpoint"]

        #PrintMsg(".\t5s Checking database extension...", 0)
        #time.sleep(5)

        if inputDB.endswith(".gpkg"):
            PrintMsg(".\t10s Passing layerList to GetNewExtentsGPKG function", 0)
            time.sleep(10)
            bExtents = GetNewExtentsGpkg(inputDB, layerList, conn, liteCur) # , saCounts, spatialExtents
            PrintMsg(".\tGot new extents for geopackage", 0)

        elif inputDB.endswith(".sqlite"):
            PrintMsg(".\tUpdating extents for each spatial layer using GetNewExtentsSpatialite", 0)
            PrintMsg(".\t", 0)
            time.sleep(5)
            bExtents = GetNewExtentsSpatialite(inputDB, layerList, conn, liteCur)

            if len(createSQLs) > 0:
                #bIndexed = True  # Skip the re-indexing and see if they were actually dropped.
                #pass
                bIndexed = RestoreIndexes(conn, liteCur, createSQLs)

                if not bIndexed:
                    PrintMsg(".\tFailed to restore attribute indexes", 1)

            else:
                # no previous indexes, trying creating new ones from metadata tables
                bIndexed = CreateNewIndexes(conn, liteCur)

                if not bIndexed:
                    PrintMsg(".\tFailed to create new attribute indexes", 1)

        else:
            err = "Input database has invalid extention"
            raise MyError(err)


        if inputDB.endswith(".gpkg"):
            driverName = "GPKG"
            driver = ogr.GetDriverByName(driverName)
            ds = driver.Open(inputDB, 1)

            if ds is None:
                err = "Failed to open " + os.path.basename(inputDB) + " using ogr with " + driver.name + " driver"
                raise MyError(err)

            for outLayerName in layerList:
                PrintMsg(".\tReady to create new spatialindex for " + outLayerName, 0)
                bCreateSpatialIndex = CreateSpatialIndex(ds, outLayerName)

            del ds
            del driver

        bCompact = CompactDatabase(inputDB)

        if bCompact == False:
            raise MyError("Failed to compact new database")

        PrintMsg(".", 0)
        PrintMsg("Output database:  " + inputDB + "  \n ", 0)
        arcpy.SetProgressorLabel("Finished building new database")

        return True

    except MyError as e:
        PrintMsg(str(e), 2)
        return False

    except:
        errorMsg(sys.exc_info())
        return False

    finally:
        PrintMsg(".\tFinally closing database", 0)
        conn.close()
        del liteCur
        del conn

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
import arcpy, os, sys, string, traceback, locale, time, datetime, csv, shutil
from operator import itemgetter, attrgetter
from osgeo import ogr
from osgeo import gdal
ogr.UseExceptions()
import subprocess
#from subprocess import PIPE, STDOUT, CREATE_NO_WINDOW

# import xml.etree.cElementTree as ET
#from xml.dom import minidom
from arcpy import env


try:
    if __name__ == "__main__":
##        inputFolder = arcpy.GetParameterAsText(0)     # location of SSURGO datasets containing spatial folders
##        ssaLayer = arcpy.GetParameterAsText(1)        # Test to see if I can sort the ssaLayer when using the 'Create SSURGO-Lite DB by Map' tool
##        inputDB = arcpy.GetParameterAsText(2)         # existing SSURGO-SQLite database
##        geogRegion = arcpy.GetParameterAsText(3)      # Geographic Region used to set output coordinate system
##        surveyList = arcpy.GetParameter(4)            # list of SSURGO dataset folder names to be proccessed (e.g. 'soil_ne109')
##        tileInfo = arcpy.GetParameterAsText(5)        # State abbreviation (optional as string) for use in creating SSURGO-Lite databases state-tiled. Or tuple as (tilename, description)
##        bDiet = arcpy.GetParameter(6)                 # Do not import the 6 deprecated cointerp columns
##        bArcPy = arcpy.GetParameter(7)                # Use arcpy.Append command to import spatial data. Default = False.

        inputDB = arcpy.GetParameterAsText(0)           # existing SSURGO-SQLite database
        ssaList = arcpy.GetParameter(1)          # list of existing survey areas to be dropped from this database

        areasymbolList = list()

        for ssa in ssaList:
            areaSym = ssa.split("|")[0].strip()
            areasymbolList.append(areaSym)

        scriptPath = __file__
        scriptFolder = os.path.dirname(scriptPath)
        basePath = os.path.dirname(scriptFolder)

        # location for spatialite binaries
        # no such module rtree error on INSERT. This was with the spatialite 5.1 DLLs. Also replaced sqlite3.dll in Pro and Desktop.
        extFolder = os.path.join(basePath, "Extensions")


        #templatePath = os.path.join(basePath, "TemplateDatabases")
        #templateDB = os.path.join(templatePath, templateName)


        # Yet another attempt to use a different version of sqlite3 that will handle rtree indexes
        #
        #sys.path.insert(0, extFolder)

        # over-ride extension folder to use a different DLL from application_data\extensions
        # Please note. Using mod_spatialite I can create the virtual shapefile,
        # but only using DB Browser can I insert that data into mupolygon.
        # GitHub discussion on spatialite extensions for DB Browser https://github.com/sqlitebrowser/sqlitebrowser/issues/267
        #extFolder = r"C:\Program Files\DB Browser for SQLite"
        #extFolder = r"C:\Program Files\DB Browser for SQLite\extensions"
        #extFolder = r"C:\Program Files\Utilities\spatialite-loadable-modules-5.0.0-win-amd64" # no such module rtree error on INSERT
        #extFolder = r"C:\Program Files\DB Browser for SQLite"  # no such module rtree error on INSERT

        PrintMsg(".\tExtensions folder: " + extFolder, 0)
        time.sleep(5)
        os.environ['PATH'] = extFolder + ";" + os.environ['PATH']    # append to end of path

        import sqlite3  # I've added the sqlite3.dll to the extensions


##        PrintMsg(".\Inserting extensions folder into system path", 0)
##        pathList = os.environ['PATH'].split(";")
##
##        if not extFolder in pathList:
##            os.environ['PATH'] = extFolder + ";" + os.environ['PATH']

##        if arcpy.Exists(ssaLayer):
##            # Sort_management (in_dataset, out_dataset, sort_field, {spatial_sort_method})
##            if len(surveyList) > 0:
##                areasymbolList = SortSurveyAreaLayer(ssaLayer, surveyList)
##
##        else:
##            areasymbolList = list()
        inputFolder = ""
        surveyList = []
        geogRegion = ""
        tileInfo = ""
        bDiet = True

        bGood = main(inputFolder, surveyList, geogRegion, tileInfo, False, inputDB, areasymbolList, bDiet)

        PrintMsg(".\tProcessing complete", 0)
        PrintMsg(".", 0)


except MyError as e:
    PrintMsg(str(e), 2)

except:
    PrintMsg(".\tOops. Got an error in the Main", 0)
    time.sleep(1)
    errorMsg(sys.exc_info())

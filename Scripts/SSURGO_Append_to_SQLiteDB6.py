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
def DropSSA_Old(inputDB, areasymbolList):
    # Drop any survey areas that already exist. Duplicate records are not allowed.
    #
    # Also ran into issue with muaggatt table which has no cascading delete or foreign key
    #
    try:
        result = False

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

        PrintMsg(".\tGetting distmdkeys from distlegendmd table", 0)
        PrintMsg(".\t\t" + queryDistr, 0)
        liteCur.execute(queryDistr)
        mdResult = liteCur.fetchall()

        if not mdResult is None:
            mdList = [row[0] for row in mdResult]

            if len(mdList) > 1:
                mdKeys = str(tuple(mdList))

            else:
                mdKeys = "(" + str(mdList[0]) + ")"

            PrintMsg(".\tGetting legend key...", 0)
            PrintMsg(".\t\t" + queryLkey, 0)
            liteCur.execute(queryLkey)
            lkResult = liteCur.fetchall()

            if not lkResult is None:
                #lKey = str(lkResult[0])
                lkeyList = [row[0] for row in lkResult]

                if len(lkeyList) > 1:
                    lKeys = str(tuple(lkeyList))

                else:
                    lKeys = "(" + str(lkeyList[0]) + ")"


                # I need to switch this up so iteration is by lkey
                # This will prevent over-running the drop muaggatt records with a
                # huge list of mukeys.
                #
                queryLegend = "SELECT mukey FROM mapunit WHERE lkey IN " + lKeys
                PrintMsg(".\tGetting mapunit keys...", 0)
                PrintMsg(".\t\t" + queryLegend, 0)
                liteCur.execute(queryLegend)
                mkResult = liteCur.fetchall()

                if not mkResult is None:
                    mukeyList = [row[0] for row in mkResult]

                    if len(mukeyList) > 1:
                        muKeys = str(tuple(mukeyList))

                    else:
                        muKeys = "(" + str(mukeyList[0]) + ")"

                    dropMukeys = "DELETE FROM muaggatt WHERE mukey IN " + muKeys
                    PrintMsg(".\tDropping muaggatt records...", 0)
                    liteCur.execute(dropMukeys)
                    conn.commit()

                else:
                    PrintMsg(".\tFailed to get mapunit keys from mapunit table", 0)

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


        if mdKeys != "":

            queryDrop3 = "DELETE FROM distmd WHERE distmdkey IN " + mdKeys

            PrintMsg(".\tDropping related records from distmd for survey area(s): " + areaSyms, 0)
            result = subprocess.run([slExe, inputDB, queryDrop3], capture_output=True, text=True)  # new
            resultOut = result.stdout
            resultError = result.stderr
            resultCode = result.check_returncode()
            PrintMsg(".\tDropped related records from distmd for survey area(s): " + areaSyms, 0)
            #PrintMsg(".\t\tReturn code: " + str(resultCode), 0)
            #PrintMsg(".\t\tStdErr: " + str(resultError), 0)


            PrintMsg(".\tDropping related spatial records from sacatalog for survey area(s): " + areaSyms, 0)
            result = subprocess.run([slExe, inputDB, queryDrop2], capture_output=True, text=True)  # new
            resultOut = result.stdout
            resultError = result.stderr
            resultCode = result.check_returncode()
            PrintMsg(".\tDropped related spatialrecords from sacatalog for survey area(s): " + areaSyms, 0)
            #PrintMsg(".\t\tReturn code: " + str(resultCode), 0)
            #PrintMsg(".\t\tStdErr: " + str(resultError), 0)

            PrintMsg(".\tDropping related attribute records from legend for survey area(s): " + areaSyms, 0)
            result = subprocess.run([slExe, inputDB, queryDrop1], capture_output=True, text=True)  # new
            resultOut = result.stdout
            resultError = result.stderr
            resultCode = result.check_returncode()
            PrintMsg(".\tDropped related attribute records from legend for survey area(s): " + areaSyms, 0)
            #PrintMsg(".\t\tReturn code: " + str(resultCode), 0)
            #PrintMsg(".\t\tStdErr: " + str(resultError), 0)
            result = True
            time.sleep(2)


        else:
            # Failed to get distmdkey. Probably this survey area does not exist in this database
            PrintMsg(".\tSkipping drop. There is no match in distribution metdata for " + areaSyms, 0)
            #time.sleep(5)
            result = True

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
        errorMsg(sys.exc_info())

    finally:
        try:
            #time.sleep(2)
            # PrintMsg(".\tFinally closing database")
            time.sleep(5)
            #conn.close()
            #del conn

        except:
            pass

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
        if not os.path.isfile(inputDB):
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

        if os.path.isfile(versionTxt):
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
        if not os.path.isfile(templateDB):
            err = "Missing input database (" + inputDB + ")"
            raise MyError(err)

        systemInfo = os.path.join(templateDB, "SYSTEM - Template Database Information")

        if os.path.isfile(systemInfo):
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
        if os.path.isfile(os.path.join(inputDB, theMDTable)):

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
def ImportMDTabularGDB(inputDB, tabularFolder, tableList):
    # For new mobile geodatabase, using an arcpy data access cursor
    #
    # Import a single set of metadata text files from first survey area's tabular
    # These files contain table information, relationship classes and domain values
    # They have tobe populated before any of the other tables
    #
    # mdstatdomdet
    # mdstatdommas
    # mdstatidxdet
    # mdstatidxmas
    # mdstatrshipdet
    # mdstatrshipmas
    # mdstattabcols
    # mdstattabs
    #codePage = 'cp1252'

    try:
        PrintMsg("Importing metadata textfiles from: " + tabularFolder, 0)
        # PrintMsg("Current workspace: " + env.workspace, 0)

        # Create list of text files to be imported. I think these need to be re-ordered. Put master tables first?
        txtFiles = ['mstabcol', 'msrsdet', 'mstab', 'msrsmas', 'msdommas', 'msidxmas', 'msidxdet',  'msdomdet']

        # Create dictionary containing text filename as key, table physical name as value
        tblInfo = {u'mstabcol': u'mdstattabcols', u'msrsdet': u'mdstatrshipdet', u'mstab': u'mdstattabs', u'msrsmas': u'mdstatrshipmas', u'msdommas': u'mdstatdommas', u'msidxmas': u'mdstatidxmas', u'msidxdet': u'mdstatidxdet', u'msdomdet': u'mdstatdomdet'}

        csv.field_size_limit(128000)

        # Process list of text files
        for txtFile in txtFiles:

            # Get table name and alias from dictionary
            if txtFile in tblInfo:
                tbl = tblInfo[txtFile]

            else:
                err = "Required input textfile '" + txtFile + "' not found in " + tabularFolder
                PrintMsg(err, 1)
                raise MyError(err)

            # Full path to SSURGO text file
            txtPath = os.path.join(tabularFolder, txtFile + ".txt")

            # continue import process only if the target table exists

            if tbl in tableList:
                # Create cursor for all fields to populate the current table
                #
                # For a geodatabase, I need to remove OBJECTID from the fields list
                # os.path.join(inputDB, tbl)
                fldList = arcpy.Describe(tbl).fields
                #fldInfos = GetFieldNames(tblName, liteCur)
                fldNames = list()
                fldLengths = list()
                iRows = 0

                for fld in fldList:
                    #PrintMsg(tbl + " field: " + fld.name, 0)

                    if fld.type != "OID":
                        fldNames.append(fld.name)
                        #PrintMsg(".\t" + fld.name + ", " + fld.type, 0)

                        if fld.type.lower() == "string":
                            fldLengths.append(fld.length)

                        else:
                            fldLengths.append(0)

                if len(fldNames) == 0:
                    err = "Failed to get field names for " + tbl
                    PrintMsg(err, 1)
                    raise MyError(err)

                if os.path.isfile(txtPath):
                    arcpy.SetProgressorLabel("Importing metadata table: " + tbl + "...")
                    PrintMsg(".\tImporting " + tbl + " with " + str(len(fldNames)) + " fields", 0)

                    try:
                        # Use csv reader to read each line in the text file. Save the values to a list of lists.
                        cur = arcpy.da.InsertCursor(tbl, fldNames)

                        with open(txtPath, 'r', encoding='UTF-8') as tabData:

                            rows = csv.reader(tabData, delimiter='|', quotechar='"')

                            for row in rows:
                                iRows += 1
                                fixedrow = [x if x else None for x in row]
                                cur.insertRow(fixedrow)

                        del cur
                        del tbl

                    except:
                        del cur
                        PrintMsg(" \n" + str(row), 1)
                        errorMsg(sys.exc_info())
                        err = "Error writing line " + Number_Format(iRows, 0, True) + " from " + txtPath
                        raise MyError(err)

                else:
                    err = "Missing tabular data file (" + txtPath + ")"
                    raise MyError(err)

            else:
                err = "Required table '" + tbl + "' not found in " + env.workspace
                PrintMsg(err, 1)
                raise MyError(err)


        return True

    except MyError as e:
        #conn.close()
        #del conn
        PrintMsg(str(e), 2)
        return False

    except:
        errorMsg(sys.exc_info())
        return False

## ===================================================================================
def ImportTabularGDB(inputDB, pathList, dbVersion, tableList):
    # For mobile geodatabase, use arcpy data access cursor to import data.
    #
    # Use csv reader method of importing text files into geodatabase for those
    # that do not have a populated SSURGO database
    #
    # Using unique constraint to prevent duplicate records in sdv* tables. Dupes will be skipped.
    # For any of the other data tables, a unique contraint violation will throw an error and stop the import.
    #
    try:
        # new code from ImportTables
        #codePage = 'cp1252'

        env.workspace = inputDB
        csv.field_size_limit(min(sys.maxsize, 2147483646))

        #PrintMsg("Current workspace: " + env.workspace, 0)
        PrintMsg(".", 0)
        PrintMsg(" \nImporting tabular data...", 0)

        iCntr = 0

        # Create a list of textfiles to be imported. The import process MUST follow the
        # order in this list in order to maintain referential integrity. This list
        # will need to be updated if the SSURGO data model is changed in the future.
        #
        txtFiles = ["distmd","legend","distimd","distlmd","lareao","ltext","mapunit", \
        "comp","muaggatt","muareao","mucrpyd","mutext","chorizon","ccancov","ccrpyd", \
        "cdfeat","cecoclas","ceplants","cerosnac","cfprod","cgeomord","chydcrit", \
        "cinterp","cmonth", "cpmatgrp", "cpwndbrk","crstrcts","csfrags","ctxfmmin", \
        "ctxmoicl","ctext","ctreestm","ctxfmoth","chaashto","chconsis","chdsuffx", \
        "chfrags","chpores","chstrgrp","chtext","chtexgrp","chunifie","cfprodo","cpmat","csmoist", \
        "cstemp","csmorgc","csmorhpp","csmormr","csmorss","chstr","chtextur", "chtexmod", \
        "featdesc", "sacatlog","sainterp","sdvalgorithm","sdvattribute","sdvfolder","sdvfolderattribute"]


        # Create a dictionary. Keys are tabular-textfile names with table information
        tblInfo = GetTableInfoGDB(inputDB)

        if len(tblInfo) == 0:
            raise MyError("")


        # For mobile geodatabase, these best method for creating indexes has not been determined
        # PrintMsg("I NEED TO LOOK AT PARENT KEY INDEXES FOR MOBILE GEODATABASES", 1)

        # After all data has been imported, create indexes for soil attribute tables using mdstat* tables.
        # arcpy.management.AddIndex(in_table, fields, {index_name}, {unique}, {ascending})

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
        for rec in liteCur.execute(sqlForeignKeys):
            #
            cntr += 1
            tabphyname, idxcolsequence, idxphyname, colphyname, ltabphyname, ltabcolphyname = rec
            # PrintMsg(str(cntr) + ".\t" + tabphyname + ": " + idxphyname + ", " + str(idxcolsequence) + ", " + str(colphyname) + ", " + str(ltabphyname) + ", " + str(ltabcolphyname) , 0)
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

            #conn.close()
            #del conn



            # Generate and execute SQL for indexes. Right now we're doing one-at-a-time.
            if 1 == 1 and len(dIndexes) > 0:
                # arcpy.management.AddIndex(in_table, fields, {index_name}, {unique}, {ascending})
                #indexQuery = "-- Begin Indexes\n"

                for indexName in dIndexes.keys():
                    if indexName[0:2] == "UC":
                        bUnique = "UNIQUE"

                    else:
                        bUnique = "NON_UNIQUE"

                    # tabphyname, [colphyname], ltabphyname, [ltabcolphyname] (updated dIndexes values)
                    tblName, colNames, parentTbl, parentColumns = dIndexes[indexName]
                    msg = "Adding index for " + tblName + " " + ", ".join(colNames)
                    #PrintMsg(".\t" + msg, 0)
                    arcpy.SetProgressorLabel(msg)

                    arcpy.management.AddIndex(tblName, colNames, indexName, bUnique)

##          # End of attribute indexes before importing data

        # End of Building Indexes


        # Need to import text files in a specific order or the MS Access database will
        # return an error due to table relationships and key violations
        arcpy.SetProgressor("step", "Importing tabular data...", 0, len(txtFiles))

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
                err = "Output table '" + tbl + "' not found in " + inputDB
                raise MyError(err)

            fldList = arcpy.Describe(os.path.join(inputDB, tbl)).fields
            fldNames = list()

            for fld in fldList:
                if fld.type != "OID" and fld.name != "ESRI_OID":
                    fldNames.append(fld.name)
                    #PrintMsg(fld.name + ", " + fld.type, 0)

                #else:
                #    PrintMsg(".\tSkipping " + tbl + "." + fld.name, 1)

            if len(fldNames) == 0:
                err = "Failed to get field names for " + tbl
                raise MyError(err)

            # PrintMsg(".\tProcessing " + tbl + " table with " + str(len(fldNames)) + " fields", 0)
            arcpy.SetProgressorLabel("Importing tabular data for:  " + tbl)

            # Open database cursor on the empty table
            cur = arcpy.da.InsertCursor(os.path.join(inputDB, tbl), fldNames)

            # Begin iterating through the each of the input SSURGO datasets
            for tabularFolder in pathList:
                iCntr += 1

                # parse Areasymbol from database name. If the geospatial naming convention isn't followed,
                # then this will not work.
                soilsFolder = os.path.dirname(tabularFolder)
                spatialFolder = os.path.join(soilsFolder, "spatial")
                fnAreasymbol = soilsFolder[(soilsFolder.rfind("_") + 1):].upper()

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

                # Make sure that input tabular data has the correct SSURGO version for this script
##                ssurgoVersion = SSURGOVersionTxt(tabularFolder)
##
##                if ssurgoVersion != dbVersion:
##                    err = "Tabular data in " + tabularFolder + " (SSURGO Version " + str(ssurgoVersion) + ") is not supported"
##                    raise MyError(err)

                ##  *********************************************************************************************************
                # Full path to SSURGO text file

                if not tbl in ['sdvfolderattribute', 'sdvattribute', 'sdvfolder', 'sdvalgorithm']:
                    # Import all tables except SDV
                    #
                    #time.sleep(0.05)  # Occasional write errors

                    iRows = 1  # input textfile line number

                    if os.path.isfile(txtPath):

                        try:
                            # Use csv reader to read each line in the text file. Save the values to a list of lists.

                            with open(txtPath, 'r', encoding='UTF-8') as tabData:

                                rows = csv.reader(tabData, delimiter='|', quotechar='"')

                                for row in rows:
                                    fixedrow = [x if x else None for x in row]
                                    cur.insertRow(fixedrow)
                                    iRows += 1

                        except:
                            PrintMsg(" \n" + str(fixedrow), 1)
                            errorMsg(sys.exc_info())
                            err = "Error writing line " + Number_Format(iRows, 0, True) + " from " + txtPath
                            raise MyError(err)

                    else:
                        err = "Missing tabular data file (" + txtPath + ")"
                        raise MyError(err)

                else:
                    # Import SDV tables one record at a time, in case there are duplicate keys
                    # 'sdvfolderattribute', 'sdvattribute', 'sdvfolder', 'sdvalgorithm'
                    #
                    # Problem. It appears that with the Mobile Geodatabase it is not
                    # throwing an error on duplicate records. Do not understand this.
                    # So it looks like AddField does not allow specification of a primary key or unique.
                    # It does specify field_is_required (NON_REQUIRED, REQUIRED) and
                    # field_is_nullable (NON_NULLABLE, NULLABLE). Perhaps these should
                    # be applied to the 'key' fields?
                    #
                        iRows = 1  # input textfile line number

                        if os.path.isfile(txtPath):

                            # Use csv reader to read each line in the text file

                            with open(txtPath, 'r', encoding='UTF-8') as tabData:
                                #with arcpy.da.InsertCursor(inputDB, fldNames) as cur:
                                rows = csv.reader(tabData, delimiter='|', quotechar='"')

                                for row in rows:

                                    try:
                                        # watch for unique contraint errors here

                                        fixedrow = [x if x else None for x in row]
                                        cur.insertRow(fixedrow)
                                        iRows += 1

                                    except:
                                        # when indexes already exist, we may see:
                                        # 'Underlying DBMS error [UNIQUE constraint failed: sdvattribute.attributename] [main.sdvattribute]'
                                        # Need to capture this error and pass, else throw an exception.
                                        #errorMsg(sys.exc_info())
                                        pass

                        else:
                            err = "Missing tabular data file (" + txtPath + ")"
                            raise MyError(err)

            del cur
            del tbl

            arcpy.SetProgressorPosition()


        arcpy.ResetProgressor()

##          End Table Iteration
##          *********************************************************************************************************
##          *********************************************************************************************************

##          *********************************************************************************************************
##
        PrintMsg("Creating table relationshipclasses...", 0)
        for indexName in dIndexes.keys():

            # tabphyname, [colphyname], ltabphyname, [ltabcolphyname] (updated dIndexes values)

            tblName, colNames, parentTbl, parentColumns = dIndexes[indexName]

            if not parentTbl is None and len(colNames) == 1:
                # Use this as a relationshipclass?
                msg = "Creating relate for " + str(tblName) + ":\t" + str(colNames[0]) + " --> " + str(parentTbl) + "\t" + str(parentColumns[0])
                arcpy.SetProgressorLabel(msg)
                #PrintMsg(".\tCreating relate for " + str(tblName) + ":\t" + str(colNames[0]) + " --> " + str(parentTbl) + "\t" + str(parentColumns[0]), 0)

                arcpy.CreateRelationshipClass_management( os.path.join(inputDB, tblName), os.path.join(inputDB, parentTbl), "z" + indexName, \
                "SIMPLE", tblName + "-->", "<--" + parentTbl, "FORWARD", "ONE_TO_MANY", "NONE", colNames[0], parentColumns[0])
                #
                #



##          *********************************************************************************************************
##          *********************************************************************************************************
##      # Begin creating indexes for primary keys in the spatial tables.
##      # I am not sure if these indexes and primary-foreign key information is given by the mdstat tables.
##      # Need to look into this.
##
        # For mobile geodatabase, the best method for creating indexes has not been determined
        if 1 == 1:
            PrintMsg(" \nCreating primary key indexes for geometry tables...", 0)

            arcpy.SetProgressorLabel("Tabular import complete")

            # Create primary key indexes for featureclasses
            #
            # Not creating spatial indexes via SQL at this time
            # Spatial Index for ST_Geometry
            # SELECT CreateSpatialIndex('mydatabase','sensitive_areas','zone','rtreexy');

            # Mupolygon
            tblName = "MUPOLYGON"
            PrintMsg(".\tAdding attribute index for " + tblName, 0)
            arcpy.SetProgressorLabel("Adding attribute index for " + tblName)
            primaryKey = "mukey"
            indexName = "Indx_" + tblName + "_" + primaryKey
            parentTbl = "mapunit"
            arcpy.management.AddIndex(tblName, primaryKey, indexName, "NON_UNIQUE")

            # arcpy.CreateRelationshipClass_management("mapunit", fc, "zMapunit_" + fc, "SIMPLE", "> Mapunit Polygon Layer",
            # "< Mapunit Table", "NONE", "ONE_TO_MANY", "NONE", "mukey", "MUKEY", "","")
            arcpy.CreateRelationshipClass_management( tblName, parentTbl, indexName, "SIMPLE", "> Mapunit Polygon Layer", \
            "< Mapunit Table", "NONE", "ONE_TO_MANY", "NONE", primaryKey, primaryKey)


            tblName = "MUPOINT"
            PrintMsg(".\tAdding attribute index for " + tblName, 0)
            arcpy.SetProgressorLabel("Adding attribute index for " + tblName)
            primaryKey = "mukey"
            indexName = "Indx_" + tblName + "_" + primaryKey
            parentTbl = "mapunit"
            arcpy.management.AddIndex(tblName, primaryKey, indexName, "NON_UNIQUE")
            #arcpy.CreateRelationshipClass_management( parentTbl, tblName, indexName, "SIMPLE", "> Mapunit Point Layer", \
            #"< Mapunit Table", "NONE", "ONE_TO_MANY", "NONE", primaryKey, primaryKey)

            tblName = "MULINE"
            PrintMsg(".\tAdding attribute index for " + tblName, 0)
            arcpy.SetProgressorLabel("Adding attribute index for " + tblName)
            primaryKey = "mukey"
            indexName = "Indx_" + tblName + "_" + primaryKey
            parentTbl = "mapunit"
            #arcpy.management.AddIndex(tblName, primaryKey, indexName, "NON_UNIQUE")
            #arcpy.CreateRelationshipClass_management( parentTbl, tblName, indexName, "SIMPLE", "> Mapunit Line Layer", \
            #"< Mapunit Table", "NONE", "ONE_TO_MANY", "NONE", primaryKey, primaryKey)

            tblName = "SAPOLYGON"
            PrintMsg(".\tAdding attribute index for " + tblName, 0)
            arcpy.SetProgressorLabel("Adding attribute index for " + tblName)
            primaryKey = "areasymbol"
            indexName = "Indx_" + tblName + "_" + primaryKey
            parentTbl = "legend"
            arcpy.management.AddIndex(tblName, primaryKey, indexName, "NON_UNIQUE")
            arcpy.CreateRelationshipClass_management( tblName, parentTbl, indexName, "SIMPLE", "> Soil Survey Boundary Layer", \
            "< Mapunit Table", "NONE", "ONE_TO_MANY", "NONE", primaryKey, primaryKey)

            tblName = "FEATLINE"
            PrintMsg(".\tAdding attribute index for " + tblName, 0)
            arcpy.SetProgressorLabel("Adding attribute index for " + tblName)
            primaryKey = "featkey"
            indexName = "Indx_" + tblName + "_" + primaryKey
            parentTbl = "featdesc"
            arcpy.management.AddIndex(tblName, primaryKey, indexName, "NON_UNIQUE")
            arcpy.CreateRelationshipClass_management( tblName, parentTbl, indexName, "SIMPLE", "> Feature Line Layer", \
            "< Mapunit Table", "NONE", "ONE_TO_MANY", "NONE", primaryKey, primaryKey)

            tblName = "FEATPOINT"
            PrintMsg(".\tAdding attribute index for " + tblName, 0)
            arcpy.SetProgressorLabel("Adding attribute index for " + tblName)
            primaryKey = "featkey"
            indexName = "Indx_" + tblName + "_" + primaryKey
            parentTbl = "featdesc"
            arcpy.management.AddIndex(tblName, primaryKey, indexName, "NON_UNIQUE")
            arcpy.CreateRelationshipClass_management( tblName, parentTbl, indexName, "SIMPLE", "> Feature Point Layer", \
            "< Mapunit Table", "NONE", "ONE_TO_MANY", "NONE", primaryKey, primaryKey)
##          End indexes on featureclass primary keys


        arcpy.SetProgressorLabel("Finished with attribute indexes")

        return True

    except MyError as e:
        # Example: raise MyError("This is an error message")
        PrintMsg(str(e), 2)
        return False

    except:
        errorMsg(sys.exc_info())
        return False

## ===================================================================================
def ImportMDTabularSQL2(inputDB, tabularFolder, tableList, conn, liteCur):
    # Import a single set of metadata text files from first survey area's tabular
    # These files contain table information, relationship classes and domain values
    # They have to be populated before any of the other tables
    #
    #will probably sto using this function and pre-populate these tables in the Template db.
    #
    # mdstatdomdet
    # mdstatdommas
    # mdstatidxdet
    # mdstatidxmas
    # mdstatrshipdet
    # mdstatrshipmas
    # mdstattabcols
    # mdstattabs
    #codePage = 'cp1252'

    try:
        PrintMsg("Importing metadata textfiles from: " + tabularFolder, 0)
        #PrintMsg("Current workspace: " + env.workspace, 0)

        # Create list of text files to be imported
        txtFiles = ['mstabcol', 'msrsdet', 'mstab', 'msrsmas', 'msdommas', 'msidxmas', 'msidxdet',  'msdomdet']

        # Create dictionary containing text filename as key, table physical name as value
        tblInfo = {u'mstabcol': u'mdstattabcols', u'msrsdet': u'mdstatrshipdet', u'mstab': u'mdstattabs', u'msrsmas': u'mdstatrshipmas', u'msdommas': u'mdstatdommas', u'msidxmas': u'mdstatidxmas', u'msidxdet': u'mdstatidxdet', u'msdomdet': u'mdstatdomdet'}

        csv.field_size_limit(128000)

        # Process list of text files
        for txtFile in txtFiles:

            # Get table name and alias from dictionary
            if txtFile in tblInfo:
                tbl = tblInfo[txtFile]

            else:
                err = "Required input textfile '" + txtFile + "' not found in " + tabularFolder
                PrintMsg(err, 1)
                raise MyError(err)

            # Full path to SSURGO text file
            txtPath = os.path.join(tabularFolder, txtFile + ".txt")

            # continue import process only if the target table exists

            if tbl in tableList:

                fldInfos = GetFieldInfo(tbl, liteCur)
                fldNames = list()
                fldLengths = list()

                for fld in fldInfos:
                    fldName, fldType = fld
                    #PrintMsg(tbl + " field: " + fld.name, 0)

                    if fldName.lower() != "objectid":
                        fldNames.append(fldName)

                if len(fldNames) == 0:
                    err = "Failed to get field names for " + tbl
                    PrintMsg(err, 1)
                    raise MyError(err)

                curValues = list()
                iRows = 0
                src = len(fldNames) * ['?']  # this will be used below in executemany

                if os.path.isfile(txtPath):

                    arcpy.SetProgressorLabel("Importing metadata table: " + tbl + "...")
                    PrintMsg(".\tImporting " + tbl + " with " + str(len(fldNames)) + " fields", 0)

                    try:
                        # Use csv reader to read each line in the text file. Save the values to a list of lists.

                        with open(txtPath, 'r', encoding='UTF-8') as tabData:
                            rows = csv.reader(tabData, delimiter='|', quotechar='"')

                            for row in rows:
                                curValues.append(tuple(row))
                                iRows += 1

                        insertQuery = "INSERT INTO " + tbl + " VALUES (" + ",".join(src) + ");"
                        liteCur.executemany(insertQuery, curValues)
                        conn.commit()

                    except:
                        #PrintMsg(" \n" + str(row), 1)
                        errorMsg(sys.exc_info())
                        err = "Error writing line " + Number_Format(iRows, 0, True) + " from " + txtPath
                        raise MyError(err)

                else:
                    err = "Missing tabular data file (" + txtPath + ")"
                    raise MyError(err)

            else:
                err = "Required table '" + tbl + "' not found in " + env.workspace
                PrintMsg(err, 1)
                raise MyError(err)

        return True

    except MyError as e:
        conn.close()
        del conn
        PrintMsg(str(e), 2)
        return False

    except sqlite3.IntegrityError:
        PrintMsg("SQLite IntegrityError", 2)
        errorMsg(sys.exc_info())  # not sure if sys will report the appropriate information.

    except:
        errorMsg(sys.exc_info())
        return False


    finally:
        try:
            PrintMsg(".\tFinally closing database after tabular import")
            time.sleep(2)
            conn.close()
            del conn

        except:
            pass

## ===================================================================================
def ImportMDTabularSQL99():
    # Using this temporary function for a one-time import of metadata tables for SQLite Template database
    #
    # Import a single set of metadata text files from first survey area's tabular
    # These files contain table information, relationship classes and domain values
    # They have to be populated before any of the other tables
    #
    #will probably sto using this function and pre-populate these tables in the Template db.
    #
    # mdstatdomdet
    # mdstatdommas
    # mdstatidxdet
    # mdstatidxmas
    # mdstatrshipdet
    # mdstatrshipmas
    # mdstattabcols
    # mdstattabs
    #codePage = 'cp1252'

    try:
        # Hardcoded nputs
        #import csvreader
        #import os, sys
        tabularFolder = r"D:\Geodata\2021\SQLite_Tests\ApplicationData\TemplateDatabases\Metadata_CSV"
        inputDB = r"D:\Geodata\2021\SQLite_Tests\ApplicationData\TemplateDatabases\template_arcmap_geopackage01.gpkg"

        print("Importing metadata textfiles from: " + tabularFolder)
        #PrintMsg("Current workspace: " + env.workspace, 0)

        # Create list of text files to be imported
        txtFiles = ['mdstattabcols', 'mdstatrshipdet', 'mdstattabs', 'mdstatrshipmas', 'mdstatdommas', 'mdstatidxmas', 'mdstatidxdet',  'mdstatdomdet', 'system_templatedatabaseinformation']

        # Create dictionary containing text filename as key, table physical name as value
        #tblInfo = {u'mstabcol': u'mdstattabcols', u'msrsdet': u'mdstatrshipdet', u'mstab': u'mdstattabs', u'msrsmas': u'mdstatrshipmas', u'msdommas': u'mdstatdommas', u'msidxmas': u'mdstatidxmas', u'msidxdet': u'mdstatidxdet', u'msdomdet': u'mdstatdomdet'}

        csv.field_size_limit(128000)


        conn = sqlite3.connect(inputDB)
        #conn.enable_load_extension(True)
        liteCur = conn.cursor()

        # Process list of text files
        for txtFile in txtFiles:
            tbl = str(txtFile)

            # Full path to SSURGO text file
            txtPath = os.path.join(tabularFolder, txtFile + ".csv")

            # continue import process only if the target table exists

            #if tbl in tableList:
            if 1 == 1:

                fldInfos = GetFieldInfo(tbl, liteCur)
                fldNames = list()
                fldLengths = list()

                for fld in fldInfos:
                    fldName, fldType = fld
                    PrintMsg(tbl + " field: " + fldName, 0)

                    if fldName.lower() != "objectid":
                        fldNames.append(fldName)

                if len(fldNames) == 0:
                    err = "Failed to get field names for " + tbl
                    print(err)

                curValues = list()
                iRows = 0
                src = len(fldNames) * ['?']  # this will be used below in execute
                insertQuery = "INSERT INTO " + tbl + " VALUES (" + ",".join(src) + ");"

                if os.path.isfile(txtPath):

                    arcpy.SetProgressorLabel("Importing metadata table: " + tbl + "...")
                    PrintMsg(".\tImporting " + tbl + " with " + str(len(fldNames)) + " fields",  0)

                    try:
                        # Use csv reader to read each line in the text file. Save the values to a list of lists.

                        with open(txtPath, 'r', encoding='UTF-8') as tabData:
                            rows = csv.reader(tabData, delimiter='|', quotechar='"')

                            for row in rows:
                                # skip first item (OID) in these csv files
                                newrow = row[1:]
                                #curValues.append(tuple(row))
                                iRows += 1
                                if not newrow is None:
                                    #insertQuery = "INSERT INTO " + tbl + " VALUES (" + ",".join(src) + ");"
                                    liteCur.execute(insertQuery, newrow)

                        conn.commit()

                    except:
                        #errorMsg(sys.exc_info())
                        err = "Error writing line " + Number_Format(iRows, 0, True) + " from " + txtPath
                        PrintMsg(err, 1)
                        PrintMsg(" \n" + str(newrow), 1)
                        errorMsg(sys.exc_info())

                else:
                    err = "Missing tabular data file (" + txtPath + ")"
                    raise MyError(err)

            else:
                err = "Required table '" + tbl + "' not found in " + env.workspace
                raise MyError(err)

        #conn.close()
        #del conn

        return True

    except MyError as e:
        # Example: raise MyError("This is an error message")
        PrintMsg(str(e), 2)
        return False

    except:
        errorMsg(sys.exc_info())
        return False

    finally:
        try:
            PrintMsg(".\tFinally closing database after tabular import")
            time.sleep(2)
            conn.close()
            del conn

        except:
            pass

## ===================================================================================
def ImportTabularSQL1(inputDB, pathList, dbVersion, tableList, conn, liteCur):
    # Use csv reader method of importing text files into geodatabase for those
    # that do not have a populated SSURGO database
    #
    # Using unique constraint to prevent duplicate records in sdv* tables. Dupes will be skipped.
    # For any of the other data tables, a unique contraint violation will throw an error and stop the import.
    #
    # Import ALL of the original SSURGO cointerp data
    #
    # Currently does not accomodate OBJECTID in attribute tables, but plan to incorporate that functionality.
    # This will be the second attempt to work with a template database having OBJECTID. First attempt failed badly.
    #
    try:
        # new code from ImportTables
        #codePage = 'cp1252'

        #env.workspace = inputDB
        csv.field_size_limit(min(sys.maxsize, 2147483646))

        #PrintMsg("Current workspace: " + env.workspace, 0)
        PrintMsg(".", 0)
        PrintMsg(".\tImporting tabular data using function 'ImportTabularSQL1'...", 0)
        PrintMsg(".\tAll 19 cointerp columns are included")

        iCntr = 0

        # Create a list of textfiles to be imported. The import process MUST follow the
        # order in this list in order to maintain referential integrity. This list
        # will need to be updated if the SSURGO data model is changed in the future.
        #
        txtFiles = ["distmd","legend","distimd","distlmd","lareao","ltext","mapunit", \
        "comp","muaggatt","muareao","mucrpyd","mutext","chorizon","ccancov","ccrpyd", \
        "cdfeat","cecoclas","ceplants","cerosnac","cfprod","cgeomord","chydcrit", \
        "cinterp","cmonth", "cpmatgrp", "cpwndbrk","crstrcts","csfrags","ctxfmmin", \
        "ctxmoicl","ctext","ctreestm","ctxfmoth","chaashto","chconsis","chdsuffx", \
        "chfrags","chpores","chstrgrp","chtext","chtexgrp","chunifie","cfprodo","cpmat","csmoist", \
        "cstemp","csmorgc","csmorhpp","csmormr","csmorss","chstr","chtextur", "chtexmod", \
        "featdesc", "sacatlog","sainterp","sdvalgorithm","sdvattribute","sdvfolder","sdvfolderattribute"]

        # Create a dictionary. Keys are tabular-textfile names with table information
        tblInfo = GetTableInfoSQL(liteCur)

        if len(tblInfo) == 0:
            raise MyError("")

        # Need to import text files in a specific order or the MS Access database will
        # return an error due to table relationships and key violations
        arcpy.SetProgressor("step", "Importing tabular data...", 0, len(txtFiles))

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
                err = "Output table '" + tbl + "' not found in " + inputDB
                raise MyError(err)

            #fldList = arcpy.Describe(os.path.join(inputDB, tbl)).fields

            fldInfos = GetFieldInfo(tbl, liteCur)
            fldNames = list()
            fldLengths = list()

            for fld in fldInfos:
                fldName, fldType = fld
                fldNames.append(fldName)

            # PrintMsg(".\tFields for " + tbl + ": " + ",  ".join(fldNames), 0)

            if len(fldNames) == 0:
                err = "Failed to get field names for " + tbl
                raise MyError(err)

            src = len(fldNames) * ['?']  # this will be used below in executemany

            # PrintMsg(".\tProcessing " + tbl + " table with " + str(len(fldNames)) + " fields", 0)
            arcpy.SetProgressorLabel("Importing tabular data for:  " + tbl)

            # Begin iterating through the each of the input SSURGO datasets
            for tabularFolder in pathList:
                iCntr += 1
                #newFolder = os.path.dirname(os.path.dirname(tabularFolder)) # survey dataset folder

                # parse Areasymbol from database name. If the geospatial naming convention isn't followed,
                # then this will not work.
                soilsFolder = os.path.dirname(tabularFolder)
                spatialFolder = os.path.join(soilsFolder, "spatial")
                fnAreasymbol = soilsFolder[(soilsFolder.rfind("_") + 1):].upper()

                # move to tabular folder. Not sure if this is necessary as long as I use full paths
                # env.workspace = tabularFolder

                if tbl == "featdesc":
                    # this file is the only txt file in the spatial folder
                    txtFile = "soilsf_t_" + fnAreasymbol
                    txtPath = os.path.join(spatialFolder, txtFile + ".txt")
                    #env.workspace =

                else:
                    # Full path to SSURGO tabular folder
                    txtPath = os.path.join(tabularFolder, txtFile + ".txt")

                # if the tabular directory is empty return False
                if len(os.listdir(tabularFolder)) < 1:
                    err = "No text files found in the tabular folder"
                    raise MyError(err)

                # Make sure that input tabular data has the correct SSURGO version for this script
                ssurgoVersion = SSURGOVersionTxt(tabularFolder)

                ## NEED TO FIX THIS VERSION CHECK IN 2 PLACES
                ##                if ssurgoVersion != dbVersion:
                ##                    err = "Tabular data in " + tabularFolder + " (SSURGO Version " + str(ssurgoVersion) + ") is not supported"
                ##                    raise MyError(err)

                ##  *********************************************************************************************************
                # Full path to SSURGO text file
                # txtPath = os.path.join(tabularFolder, txtFile + ".txt")

                curValues = list()

                if not tbl in ['sdvfolderattribute', 'sdvattribute', 'sdvfolder', 'sdvalgorithm']:
                    # Import all tables (including cointerp), except for sdv* tables.
                    # The sdv* tables will be imported one record at a time instead of in a batch.
                    #
                    time.sleep(0.05)  # Occasional write errors

                    iRows = 1  # input textfile line number

                    if os.path.isfile(txtPath):
                    #if arcpy.Exists(txtPath):

                        try:
                            # Use csv reader to read each line in the text file. Save the values to a list of lists.

                            with open(txtPath, 'r', encoding='UTF-8') as tabData:
                                rows = csv.reader(tabData, delimiter='|', quotechar='"')


                                for row in rows:
                                    #row = [val if val else None for val in row]  # trying to eliminate zeros resulting from empty string
                                    curValues.append(tuple([val if val else None for val in row]))
                                    iRows += 1
                                    #if tbl == "comonth" and iRows == 2:
                                    #    PrintMsg(".\tcomonth values: " + str(row))

                            insertQuery = "INSERT INTO " + tbl + " VALUES (" + ",".join(src) + ");"
                            liteCur.executemany(insertQuery, curValues)
                            conn.commit()

                        except:
                            #PrintMsg(" \n" + str(row), 1)
                            errorMsg(sys.exc_info())
                            err = "Error writing line " + Number_Format(iRows, 0, True) + " from " + txtPath
                            raise MyError(err)

                    else:
                        err = "Missing tabular data file (" + txtPath + ")"
                        raise MyError(err)

                elif tbl in ('sdvfolderattribute', 'sdvattribute', 'sdvfolder', 'sdvalgorithm'):
                    # Import SDV tables one record at a time, in case there are duplicate keys
                    # 'sdvfolderattribute', 'sdvattribute', 'sdvfolder', 'sdvalgorithm'
                    #
                        iRows = 1  # input textfile line number

                        if os.path.isfile(txtPath):
                        # if arcpy.Exists(txtPath):

                            # Use csv reader to read each line in the text file
                            insertQuery = "INSERT INTO " + tbl + " VALUES (" + ",".join(src) + ");"

                            with open(txtPath, 'r', encoding='UTF-8') as tabData:
                            #with open(txtPath, 'r', encoding='iso-8859-1') as tabData:
                                # catching different encoding for NASIS export (esp. sdvattribute table) which as of 2020 uses ISO-8859-1
                                rows = csv.reader(tabData, delimiter='|', quotechar='"')

                                for row in rows:
                                    try:
                                        liteCur.execute(insertQuery, row)
                                        conn.commit()
                                        iRows += 1

                                    except sqlite3.IntegrityError:
                                        # Need to see if I can more narrowly define the error types I want to pass or throw an error
                                        pass

                                    except:
                                        errorMsg(sys.exc_info())

                        else:
                            err = "Missing tabular data file (" + txtPath + ")"
                            raise MyError(err)

##                elif tbl == 'cointerp':
##                    # Should only enter this if cointerp is excluded above
##                    iRows = 1  # input textfile line number
##
##                    if os.path.isfile(txtPath):
##
##                        try:
##                            # Use csv reader to read each line in the text file. Save the values to a list of lists.
##
##                            with open(txtPath, 'r', encoding='UTF-8') as tabData:
##                                rows = csv.reader(tabData, delimiter='|', quotechar='"')
##
##
##                                for row in rows:
##                                    #row = [val if val else None for val in row]  # trying to eliminate zeros resulting from empty string
##
##                                    # remove extra data from row
##                                    newrow = row[0:7] + row[11:13] + row[15:]  # seems slow?
##
##                                    #for indx in colIndexes:  # try pop instead of slice. doubtful.
##                                    #    row.pop(indx)
##
##                                    curValues.append(tuple([val if val else None for val in newrow]))
##                                    iRows += 1
##                                    #if tbl == "comonth" and iRows == 2:
##                                    #    PrintMsg(".\tcomonth values: " + str(row))
##
##                            #insertQuery = "INSERT INTO " + tbl + " VALUES (" + ",".join(src) + ");"
##                            insertQuery = "INSERT INTO " + tbl + " " + str(tuple(fldNames)) +  " VALUES (" + ",".join(src) + ");"
##                            liteCur.executemany(insertQuery, curValues)
##                            conn.commit()
##
##                        except:
##                            #PrintMsg(" \n" + str(row), 1)
##                            errorMsg(sys.exc_info())
##                            err = "Error writing line " + Number_Format(iRows, 0, True) + " from " + txtPath
##                            raise MyError(err)
##
##                    else:
##                        err = "Missing tabular data file (" + txtPath + ")"
##                        raise MyError(err)

                # End of table iteration
            arcpy.SetProgressorPosition()

        #conn.close()  # end of importing tabular

##          End Table Iteration
##          *********************************************************************************************************
##          *********************************************************************************************************

##          *********************************************************************************************************
##          *********************************************************************************************************
##      # Create indexes for attribute tables

        PrintMsg(".\tLoading ST_Geometry library", 0)
        #conn.load_extension('stgeometry_sqlite.dll')

        if 1 == 2:
            # After all data has been imported, create indexes for soil attribute tables using mdstat* tables.
            # If I include all indexes in the Template database, this section is not required. Instead, use
            # the DropIndexes and RestoreIndexes functions.
            #
            # At this point we're assuming that the mdstat tables are populated.
            PrintMsg(".\tShould be skipping this section of code that adds new attribute indexes", 0)

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
            arcpy.SetProgressorLabel("Tabular import complete")

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

## ===================================================================================
def ImportTabularSQL2(inputDB, pathList, dbVersion, tableList, conn, liteCur):
    #
    # No objectid used
    #
    # Handles cointerp table differently. Assumes that the several of the interp* columns have been removed from
    # the template database. If the columns ARE still present, they will not be populated.
    #
    # Use csv reader method of importing text files into geodatabase for those
    # that do not have a populated SSURGO database
    #
    # Using unique constraint to prevent duplicate records in sdv* tables. Dupes will be skipped.
    # For any of the other data tables, a unique contraint violation will throw an error and stop the import.
    #
    try:
        result = False
        # new code from ImportTables
        #codePage = 'cp1252'

        # env.workspace = inputDB
        csv.field_size_limit(min(sys.maxsize, 2147483646))

        #PrintMsg("Current workspace: " + env.workspace, 0)
        PrintMsg(".", 0)
        PrintMsg(".\tImporting tabular data using function 'ImportTabularSQL2'...", 0)
        PrintMsg(".\tExcluding 6 deprecated cointerp columns", 0)
        time.sleep(5)

        iCntr = 0

        # Create a list of textfiles to be imported. The import process MUST follow the
        # order in this list in order to maintain referential integrity. This list
        # will need to be updated if the SSURGO data model is changed in the future.
        #
        txtFiles = ["distmd","legend","distimd","distlmd","lareao","ltext","mapunit", \
        "comp","muaggatt","muareao","mucrpyd","mutext","chorizon","ccancov","ccrpyd", \
        "cdfeat","cecoclas","ceplants","cerosnac","cfprod","cgeomord","chydcrit", \
        "cinterp","cmonth", "cpmatgrp", "cpwndbrk","crstrcts","csfrags","ctxfmmin", \
        "ctxmoicl","ctext","ctreestm","ctxfmoth","chaashto","chconsis","chdsuffx", \
        "chfrags","chpores","chstrgrp","chtext","chtexgrp","chunifie","cfprodo","cpmat","csmoist", \
        "cstemp","csmorgc","csmorhpp","csmormr","csmorss","chstr","chtextur", "chtexmod", \
        "featdesc", "sacatlog","sainterp","sdvalgorithm","sdvattribute","sdvfolder","sdvfolderattribute"]

        txtFiles = ["distmd","legend","sacatlog","distimd","distlmd","lareao","ltext","mapunit", \
        "comp","muaggatt","muareao","mucrpyd","mutext","chorizon","ccancov","ccrpyd", \
        "cdfeat","cecoclas","ceplants","cerosnac","cfprod","cgeomord","chydcrit", \
        "cinterp","cmonth", "cpmatgrp", "cpwndbrk","crstrcts","csfrags","ctxfmmin", \
        "ctxmoicl","ctext","ctreestm","ctxfmoth","chaashto","chconsis","chdsuffx", \
        "chfrags","chpores","chstrgrp","chtext","chtexgrp","chunifie","cfprodo","cpmat","csmoist", \
        "cstemp","csmorgc","csmorhpp","csmormr","csmorss","chstr","chtextur", "chtexmod", \
        "featdesc","sainterp","sdvalgorithm","sdvattribute","sdvfolder","sdvfolderattribute"]


        # Create a dictionary. Keys are tabular-textfile names with table information
        tblInfo = GetTableInfoSQL(liteCur)

        if len(tblInfo) == 0:
            raise MyError("")

        # Identify cointerp columns to be skipped during the tabular import.
        # Please note that the script currently does not check to see if they have indeed been removed.
        # The corresponding cointerp column names:
        #     interpll, interpllc, interplr, interplrc, interphh, interphhc
        #
        colIndexes = [14, 13, 10, 9, 8, 7]

        ## Begin Table Iteration

        # Need to import text files in a specific order or the MS Access database will
        # return an error due to table relationships and key violations
        arcpy.SetProgressor("step", "Importing tabular data...", 0, len(txtFiles))

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
                err = "Output table '" + tbl + "' not found in " + inputDB
                raise MyError(err)

            fldInfos = GetFieldInfo(tbl, liteCur)
            fldNames = list()
            fldLengths = list()

            if tbl != 'cointerp':

                for fld in fldInfos:
                    fldName, fldType = fld
                    fldNames.append(fldName)

            else:
                # Skip import of 6 of the original cointerp columms

                for fld in fldInfos:
                    fldName, fldType = fld

                    if not fldName.lower() in ['interpll', 'interpllc', 'interplr', 'interplrc', 'interphh', 'interphhc']:
                        fldNames.append(fldName)

            if len(fldNames) == 0:
                err = "Failed to get field names for " + tbl
                raise MyError(err)

            src = len(fldNames) * ['?']  # this will be used below in executemany

            arcpy.SetProgressorLabel("Importing tabular data for:  " + tbl)

            # Begin iterating through the each of the input SSURGO dat
            iCntr += 1

            for tabularFolder in pathList:
                newFolder = os.path.basename(os.path.dirname(tabularFolder))  # survey dataset folder

                # parse Areasymbol from database name. If the geospatial naming convention isn't followed,
                # then this will not work.
                soilsFolder = os.path.dirname(tabularFolder)
                spatialFolder = os.path.join(soilsFolder, "spatial")
                fnAreasymbol = soilsFolder[(soilsFolder.rfind("_") + 1):].upper()

                # move to tabular folder. Not sure if this is necessary as long as I use full paths
                # env.workspace = tabularFolder

                if tbl == "featdesc":
                    # this file is the only txt file in the spatial folder
                    txtFile = "soilsf_t_" + fnAreasymbol
                    txtPath = os.path.join(spatialFolder, txtFile + ".txt")
                    #env.workspace =

                else:
                    # Full path to SSURGO tabular folder
                    txtPath = os.path.join(tabularFolder, txtFile + ".txt")

                # if the tabular directory is empty return False
                if len(os.listdir(tabularFolder)) < 1:
                    err = "No text files found in the tabular folder"
                    raise MyError(err)

                # Make sure that input tabular data has the correct SSURGO version for this script
                ssurgoVersion = SSURGOVersionTxt(tabularFolder)

                ##  NEED TO FIX THIS CHECK
                ##                if ssurgoVersion != dbVersion:
                ##                    err = "Tabular data in " + tabularFolder + " (SSURGO Version " + str(ssurgoVersion) + ") is not supported"
                ##                    raise MyError(err)

                ##  *********************************************************************************************************
                # Full path to SSURGO text file
                # txtPath = os.path.join(tabularFolder, txtFile + ".txt")

                curValues = list()  # list that will contain a single record from the tabular text file. Used by INSERT.

                if not tbl in ['cointerp', 'sdvfolderattribute', 'sdvattribute', 'sdvfolder', 'sdvalgorithm']:
                #if not tbl in ['sdvfolderattribute', 'sdvattribute', 'sdvfolder', 'sdvalgorithm']:
                    # Import all tables except SDV
                    #
                    #time.sleep(2)  # Occasional write errors
                    #PrintMsg(".\tPreparing to import data into " + tbl + " from " + newFolder, 0)

                    iRows = 1  # input textfile line number

                    if os.path.isfile(txtPath):

##                        try:
                            # Use csv reader to read each line in the text file. Save the values to a list of lists.

                        with open(txtPath, 'r', encoding='UTF-8') as tabData:
                            rows = csv.reader(tabData, delimiter='|', quotechar='"')


                            for row in rows:
                                #row = [val if val else None for val in row]  # trying to eliminate zeros resulting from empty string
                                newrow = tuple([val if val else None for val in row])
                                #PrintMsg(".\t\t" + str(newrow), 1)
                                curValues.append(newrow)
                                iRows += 1
                                #if tbl == "comonth" and iRows == 2:
                                #    PrintMsg(".\tcomonth values: " + str(row))

                        insertQuery = "INSERT INTO " + tbl + " VALUES (" + ",".join(src) + ");"
                        liteCur.executemany(insertQuery, curValues)
                        conn.commit()

##                        except:
##                            #PrintMsg(" \n" + str(row), 1)
##                            errorMsg(sys.exc_info())
##                            err = "Error writing line " + Number_Format(iRows, 0, True) + " from " + txtPath
##                            raise MyError(err)

                    else:
                        err = "Missing tabular data file (" + txtPath + ")"
                        raise MyError(err)

                elif tbl in ('sdvfolderattribute', 'sdvattribute', 'sdvfolder', 'sdvalgorithm'):
                    # Import SDV tables one record at a time, in case there are duplicate keys
                    # 'sdvfolderattribute', 'sdvattribute', 'sdvfolder', 'sdvalgorithm'
                    #
                    iRows = 1  # input textfile line number

                    if os.path.isfile(txtPath):

                        # Use csv reader to read each line in the text file
                        insertQuery = "INSERT INTO " + tbl + " VALUES (" + ",".join(src) + ");"

                        with open(txtPath, 'r', encoding='UTF-8') as tabData:
                        #with open(txtPath, 'r', encoding='iso-8859-1') as tabData:
                            # catching different encoding for NASIS export (esp. sdvattribute table) which as of 2020 uses ISO-8859-1
                            rows = csv.reader(tabData, delimiter='|', quotechar='"')

                            for row in rows:
                                try:
                                    liteCur.execute(insertQuery, row)
                                    conn.commit()
                                    iRows += 1

                                except sqlite3.IntegrityError:
                                    # Need to see if I can more narrowly define the error types I want to pass or throw an error
                                    pass

                                except:
                                    errorMsg(sys.exc_info())

                    else:
                        err = "Missing tabular data file (" + txtPath + ")"
                        raise MyError(err)

                elif tbl == 'cointerp':
                    # Should only enter this if cointerp is excluded above
                    # SSURGO originally specified 19 columns for the cointerp table
                    # interpll is the name of the first deprecated column
                    #
                    iRows = 1  # input textfile line number

                    if os.path.isfile(txtPath):

                        try:

                            with open(txtPath, 'r', encoding='UTF-8') as tabData:
                                rows = csv.reader(tabData, delimiter='|', quotechar='"')

                                for row in rows:
                                    # remove deprecated cointerp data from row

                                    newrow = row[0:7] + row[11:13] + row[15:]  # seems slow?

                                    curValues.append(tuple([val if val else None for val in newrow]))

                                    iRows += 1

                            if len(curValues) > 0:
                                insertQuery = "INSERT INTO " + tbl + " " + str(tuple(fldNames)) +  " VALUES (" + ",".join(src) + ");"
                                liteCur.executemany(insertQuery, curValues)
                                conn.commit()

                        except:
                            #PrintMsg(" \n" + str(row), 1)
                            errorMsg(sys.exc_info())
                            err = "Error writing line " + Number_Format(iRows, 0, True) + " from " + txtPath
                            raise MyError(err)

                    else:
                        err = "Missing tabular data file (" + txtPath + ")"
                        raise MyError(err)

                # End of table iteration
            arcpy.SetProgressorPosition()

        #conn.close()  # end of importing tabular
        time.sleep(2)
        arcpy.ResetProgressor()
        arcpy.SetProgressorLabel("Tabular import complete")

        time.sleep(1)

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
        #errorMsg(sys.exc_info())  # not sure if sys will report the appropriate information.

    except sqlite3.Error as err:
        PrintMsg(".\tSQLite Error: ", 2)
        time.sleep(5)
        msg = err.args[0]
        PrintMsg(".\t" + msg, 2)
        time.sleep(5)
        return result

    except:
        errorMsg(sys.exc_info())
        return result

    finally:
        try:
            PrintMsg(".\tFinally closing database after tabular import")
            time.sleep(2)
            conn.close()
            del conn

        except:
            pass

        return result

## ===============================================================================================================
def ImportTabularSQL3(inputDB, pathList, dbVersion, tableList, conn, liteCur):
    #
    # Inserts objectid value for each record
    #
    # Handles cointerp table differently. Assumes that the several of the interp* columns have been removed from
    # the template database. If the columns ARE still present, they will not be populated.
    #
    # Use csv reader method of importing text files into geodatabase for those
    # that do not have a populated SSURGO database
    #
    # Using unique constraint to prevent duplicate records in sdv* tables. Dupes will be skipped.
    # For any of the other data tables, a unique contraint violation will throw an error and stop the import.
    #
    try:
        # new code from ImportTables
        #codePage = 'cp1252'

        # env.workspace = inputDB
        csv.field_size_limit(min(sys.maxsize, 2147483646))

        #PrintMsg("Current workspace: " + env.workspace, 0)
        PrintMsg(".", 0)
        PrintMsg(".\tImporting tabular data using function 'ImportTabularSQL3'...", 0)
        PrintMsg(".\tAdding objectid and excluding 6 deprecated cointerp columns", 0)

        iCntr = 0

        # Create a list of textfiles to be imported. The import process MUST follow the
        # order in this list in order to maintain referential integrity. This list
        # will need to be updated if the SSURGO data model is changed in the future.
        #
        txtFiles = ["distmd","legend","distimd","distlmd","lareao","ltext","mapunit", \
        "comp","muaggatt","muareao","mucrpyd","mutext","chorizon","ccancov","ccrpyd", \
        "cdfeat","cecoclas","ceplants","cerosnac","cfprod","cgeomord","chydcrit", \
        "cinterp","cmonth", "cpmatgrp", "cpwndbrk","crstrcts","csfrags","ctxfmmin", \
        "ctxmoicl","ctext","ctreestm","ctxfmoth","chaashto","chconsis","chdsuffx", \
        "chfrags","chpores","chstrgrp","chtext","chtexgrp","chunifie","cfprodo","cpmat","csmoist", \
        "cstemp","csmorgc","csmorhpp","csmormr","csmorss","chstr","chtextur", "chtexmod", \
        "featdesc", "sacatlog","sainterp","sdvalgorithm","sdvattribute","sdvfolder","sdvfolderattribute"]

        # Create a dictionary. Keys are tabular-textfile names with table information
        tblInfo = GetTableInfoSQL(liteCur)

        if len(tblInfo) == 0:
            raise MyError("")

        # Identify cointerp columns to be skipped during the tabular import.
        # Please note that the script currently does not check to see if they have indeed been removed.
        # The corresponding cointerp column names:
        #     interpll, interpllc, interplr, interplrc, interphh, interphhc
        #
        colIndexes = [14, 13, 10, 9, 8, 7]

        ## Begin Table Iteration

        # Need to import text files in a specific order or the MS Access database will
        # return an error due to table relationships and key violations
        arcpy.SetProgressor("step", "Importing tabular data...", 0, len(txtFiles))

        for txtFile in txtFiles:

            # objectid value
            rowID = 0

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
                err = "Output table '" + tbl + "' not found in " + inputDB
                raise MyError(err)

            bOID = True # include OBJECTID in field list

            fldInfos = GetFieldInfo(tbl, liteCur)
            fldNames = list()
            fldLengths = list()

            if tbl != 'cointerp':

                for fld in fldInfos:
                    fldName, fldType = fld
                    fldNames.append(fldName.lower())

            else:
                # Skip import of 6 of the original cointerp columms

                for fld in fldInfos:
                    fldName, fldType = fld

                    if not fldName.lower() in ['interpll', 'interpllc', 'interplr', 'interplrc', 'interphh', 'interphhc']:
                        fldNames.append(fldName.lower())

            #if tbl == "cointerp":
            #    PrintMsg(".\t\tFieldNames for " + tbl + ":\t" + ", ".join(fldNames), 0)

            if "objectid" in fldNames:
                bOID = True

            if len(fldNames) == 0:
                err = "Failed to get field names for " + tbl
                raise MyError(err)

            src = len(fldNames) * ['?']  # this will be used below in executemany

            arcpy.SetProgressorLabel("Importing tabular data for:  " + tbl)

            # Begin iterating through the each of the input SSURGO dat
            iCntr += 1

            for tabularFolder in pathList:
                newFolder = os.path.basename(os.path.dirname(tabularFolder))  # survey dataset folder

                # parse Areasymbol from database name. If the geospatial naming convention isn't followed,
                # then this will not work.
                soilsFolder = os.path.dirname(tabularFolder)
                spatialFolder = os.path.join(soilsFolder, "spatial")
                fnAreasymbol = soilsFolder[(soilsFolder.rfind("_") + 1):].upper()

                # move to tabular folder. Not sure if this is necessary as long as I use full paths
                # env.workspace = tabularFolder

                if tbl == "featdesc":
                    # this file is the only txt file in the spatial folder
                    txtFile = "soilsf_t_" + fnAreasymbol
                    txtPath = os.path.join(spatialFolder, txtFile + ".txt")
                    #env.workspace =

                else:
                    # Full path to SSURGO tabular folder
                    txtPath = os.path.join(tabularFolder, txtFile + ".txt")

                # if the tabular directory is empty return False
                if len(os.listdir(tabularFolder)) < 1:
                    err = "No text files found in the tabular folder"
                    raise MyError(err)

                # Make sure that input tabular data has the correct SSURGO version for this script
                ssurgoVersion = SSURGOVersionTxt(tabularFolder)

                ##  NEED TO FIX THIS CHECK
                ##                if ssurgoVersion != dbVersion:
                ##                    err = "Tabular data in " + tabularFolder + " (SSURGO Version " + str(ssurgoVersion) + ") is not supported"
                ##                    raise MyError(err)

                ##  *********************************************************************************************************
                # Full path to SSURGO text file
                # txtPath = os.path.join(tabularFolder, txtFile + ".txt")

                curValues = list()

                if not tbl in ['cointerp', 'sdvfolderattribute', 'sdvattribute', 'sdvfolder', 'sdvalgorithm']:
                #if not tbl in ['sdvfolderattribute', 'sdvattribute', 'sdvfolder', 'sdvalgorithm']:
                    # Import all tables except SDV
                    #
                    time.sleep(0.05)  # Occasional write errors
                    # PrintMsg(".\tPreparing to import data into " + tbl + " from " + newFolder, 0)

                    iRows = 1  # input textfile line number

                    if os.path.isfile(txtPath):

                        try:
                            # Use csv reader to read each line in the text file. Save the values to a list of lists.

                            with open(txtPath, 'r', encoding='UTF-8') as tabData:
                                rows = csv.reader(tabData, delimiter='|', quotechar='"')


                                for row in rows:
                                    #row = [val if val else None for val in row]  # trying to eliminate zeros resulting from empty string
                                    rowID += 1  # objectid value
                                    row.insert(0, rowID)
                                    curValues.append(tuple([val if val else None for val in row]))

                                    iRows += 1
                                    #if tbl == "comonth" and iRows == 2:
                                    #    PrintMsg(".\tcomonth values: " + str(row))

                            insertQuery = "INSERT INTO " + tbl + " VALUES (" + ",".join(src) + ");"
                            liteCur.executemany(insertQuery, curValues)
                            conn.commit()

                        except:
                            #PrintMsg(" \n" + str(row), 1)
                            errorMsg(sys.exc_info())
                            err = "Error writing line " + Number_Format(iRows, 0, True) + " from " + txtPath
                            raise MyError(err)

                    else:
                        err = "Missing tabular data file (" + txtPath + ")"
                        raise MyError(err)

                elif tbl in ('sdvfolderattribute', 'sdvattribute', 'sdvfolder', 'sdvalgorithm'):
                    # Import SDV tables one record at a time, in case there are duplicate keys
                    # 'sdvfolderattribute', 'sdvattribute', 'sdvfolder', 'sdvalgorithm'
                    #
                    iRows = 1  # input textfile line number

                    if os.path.isfile(txtPath):

                        # Use csv reader to read each line in the text file
                        insertQuery = "INSERT INTO " + tbl + " VALUES (" + ",".join(src) + ");"

                        with open(txtPath, 'r', encoding='UTF-8') as tabData:
                            # catching different encoding for NASIS export (esp. sdvattribute table) which as of 2020 uses ISO-8859-1
                            rows = csv.reader(tabData, delimiter='|', quotechar='"')

                            for row in rows:
                                try:
                                    rowID += 1  # objectid value
                                    row.insert(0, rowID)
                                    liteCur.execute(insertQuery, row)
                                    conn.commit()
                                    iRows += 1

                                except sqlite3.IntegrityError:
                                    # Need to see if I can more narrowly define the error types I want to pass or throw an error
                                    rowID -= 1

                                except:
                                    errorMsg(sys.exc_info())

                    else:
                        err = "Missing tabular data file (" + txtPath + ")"
                        raise MyError(err)

                elif tbl == 'cointerp':
                    # Should only enter this if cointerp is excluded above
                    # SSURGO originally specified 19 columns for the cointerp table
                    # interpll is the name of the first deprecated column
                    #
                    iRows = 1  # input textfile line number

                    if os.path.isfile(txtPath):

                        try:
                            # Use csv reader to read each line in the text file. Save the values to a list of lists.

                            with open(txtPath, 'r', encoding='UTF-8') as tabData:
                                rows = csv.reader(tabData, delimiter='|', quotechar='"')

                                for row in rows:
                                    # remove deprecated cointerp data from row
                                    # insert objectid at the beginning
                                    rowID += 1  # objectid value
                                    newrow = [rowID] + row[0:7] + row[11:13] + row[15:]  # seems slow?
                                    curValues.append(tuple([val if val else None for val in newrow]))
                                    iRows += 1

                            if len(curValues) > 0:
                                insertQuery = "INSERT INTO " + tbl + " " + str(tuple(fldNames)) +  " VALUES (" + ",".join(src) + ");"
                                liteCur.executemany(insertQuery, curValues)
                                conn.commit()

                        except:
                            #PrintMsg(" \n" + str(row), 1)
                            errorMsg(sys.exc_info())
                            err = "Error writing line " + Number_Format(iRows, 0, True) + " from " + txtPath
                            raise MyError(err)

                    else:
                        err = "Missing tabular data file (" + txtPath + ")"
                        raise MyError(err)

                # End of table iteration
            arcpy.SetProgressorPosition()

        #conn.close()  # end of importing tabular

        ##  End Table Iteration
        ##  *********************************************************************************************************
        ##  *********************************************************************************************************

        return True

    except MyError as e:
        # Example: raise MyError("This is an error message")
        PrintMsg(str(e), 2)
        return False

    except:
        errorMsg(sys.exc_info())
        return False

    finally:
        try:
            PrintMsg(".\tFinally closing database after tabular import")
            time.sleep(2)
            conn.close()
            del conn

        except:
            pass

        return result
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
            PrintMsg(".", 0)
            PrintMsg(".\tDisabling Spatial Index for " + outLayerName, 0)
            sqlDropIndex = "SELECT DisableSpatialIndex('" + outLayerName + "', 'shape')"
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
def AppendFeatures(inputDB, geogRegion, mupolyList, mulineList, mupointList, sflineList, sfpointList, sapolyList, featCnt):
    # OGR method of importing shapefiles into database
    # Warning! The Python-GDAL method is extremely touchy. Any errors will usually crash Python and then ArcGIS Pro.
    #
    # Merge all spatial layers into a set of file geodatabase featureclasses
    # Compare shapefile feature count to GDB feature count
    # featCnt:  0 mupoly, 1 muline, 2 mupoint, 3 sfline, 4 sfpoint, 5 sapoly
    #
    # Using OGR to populate database with geometries requires .IsValid method and .MakeValid, at
    # least with POLYGON or MULTIPOLYGON

    try:

        # Would like to figure out how to drop and create spatial indexes.
        # data_source.ExecuteSQL("SELECT CreateSpatialIndex('the_table', '{}')".format(layer.GetGeometryColumn()))
        # DisableSpatialIndex(table_name String, geom_column_name String)
        # HasSpatialIndex(‘table_name’,’geom_col_name’)
        arcpy.ResetProgressor()
        PrintMsg(".\tBeginning spatial import using OGR driver", 0)

        #raise MyError("EARLY OUT BECAUSE OF CRASH")
       # time.sleep(1)

        # Open output database using ogr driver
        if inputDB.endswith(".gpkg"):
            ogrDriver = ogr.GetDriverByName("GPKG")
            gdal.SetConfigOption('OGR_GPKG_FOREIGN_KEY_CHECK', 'NO')  # is this still necessary?

        elif inputDB.endswith(".sqlite"):
            # Assuming spatialite database
            ogrDriver = ogr.GetDriverByName("SQLite")

        if ogrDriver is None:
            err = "Failed to get OGR inputDriver for " + inputDB
            raise MyError(err)

        PrintMsg(".\tGot OGR driver", 0)
        time.sleep(5)

        PrintMsg(".\tOpening database...", 0)
        time.sleep(5)

        #ds = ogrDriver.Open(inputDB, 1)
        ds = ogr.Open(inputDB, 1)

        PrintMsg(".\tGot dataset using OGR driver", 0)
        time.sleep(5)

        if ds is None:
            err = "Failed to open " + inputDB + " using ogr with " + ogrDriver.name + " driver"
            PrintMsg(err, 1)
            time.sleep(5)
            raise MyError(err)

        # Start timer to test performance of imports and spatial indexes
        start = time.time()   # start clock to measure total processing time for importing soil polygons

        # Get driver for all input shapefiles
        # Monday morning, I moved this back up to the top, before iterating through different feature types.
        shpDriver = ogr.GetDriverByName("ESRI Shapefile")

        if shpDriver is None:
            err = "Failed to get OGR inputDriver for shapefile"
            raise MyError(err)

        #PrintMsg(".", 0)
        #PrintMsg(".\tGot OGR driver, importing spatial data...", 0)
        #time.sleep(5)
        # Currently assuming input featureclasses from Web Soil Survey are GCS WGS1984

        # Save record of soil polygon shapefiles with invalid geometry
        dBadGeometry = dict()

        # *********************************************************************
        # Merge process MUPOLYGON
        # *********************************************************************
        #
        if len(mupolyList) > 0:

            # Get information for the output layer
            #
            outLayerName = "mupolygon"

            # Drop spatial index first
            bDropped = DropSpatialIndex(ds, outLayerName)

            if bDropped == False:
                PrintMsg(".\tFailed to drop spatial index for " + outLayerName, 1)

            # Get field info from mupolygon (output layer) first
            PrintMsg(".", 0)
            PrintMsg("Appending " + str(len(mupolyList)) + " map unit polygon shapefiles to create new featureclass: " + outLayerName, 0)
            arcpy.SetProgressor("step", "Appending features to " + outLayerName + " layer", 0, len(mupolyList), 1)
            time.sleep(5)
            PrintMsg(".\tGetting " + outLayerName + " layer object from database", 0)
            time.sleep(5)

            outLayer = ds.GetLayerByName(outLayerName)
            outLayerDefn =  outLayer.GetLayerDefn()  #outLayer.GetFieldDefn()
            outFldCount = outLayerDefn.GetFieldCount()

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

            for shpFile in mupolyList:
                time.sleep(0.1)
                layerCnt += 1
                dsShape = shpDriver.Open(shpFile)
                inLayer = dsShape.GetLayer()

                # Get count of input features
                featCnt = inLayer.GetFeatureCount()

                msg = ".\tAppending shapefile no. " + str(layerCnt) + " with " + Number_Format(featCnt, 0, True) + " features  (" + os.path.basename(shpFile) + ")"
                PrintMsg(msg, 0)
                arcpy.SetProgressorLabel(msg)
                time.sleep(3)

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
                        #geomType = geom.GetGeometryName()
                        shpID = inFeature.GetFID()
                        #PrintMsg(".\t\tShapefile " + os.path.basename(shpFile) + " has invalid geometry for " + geomType.lower() + " #" + str(shpID), 0)
                        outFeature.SetGeometry(geom.Buffer(0))  #
                        #outFeature.SetGeometry(geom.MakeValid())

                        if os.path.basename(shpFile) in dBadGeometry:
                            dBadGeometry[os.path.basename(shpFile)].append(shpID)

                        else:
                            dBadGeometry[os.path.basename(shpFile)] = [shpID]

                    outLayer.CreateFeature(outFeature)
                    outFeature = None

                # Calculate total number of input features read from all shapefiles
                # At completion, this should match final count in the output database.
                arcpy.arcpy.SetProgressorPosition()
                inputCnt += featCnt

                inLayer = None
                dsShape = None

            if bDropped:
                # Recreate spatial index
                newSpatialIndex = CreateSpatialIndex(ds, outLayerName)

            arcpy.ResetProgressor()
            PrintMsg(".\tGetting feature count from new " + outLayerName + " layer", 0)
            mupolyCnt = outLayer.GetFeatureCount()
            PrintMsg(".\tFinal output featurecount:\t" + str(mupolyCnt), 0)
            PrintMsg(".\tTotal input featurecount:\t" + str(inputCnt), 0)

            outLayerDefn = None
            outLayer =  None

            theMsg = " \nTotal processing time for soil polygons " + outLayerName + ": " + elapsedTime(start) + " \n "
            PrintMsg(theMsg, 0)


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
            PrintMsg("Appending " + str(len(mulineList)) + " map unit line shapefiles to create new featureclass: " + outLayerName, 0)
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
                arcpy.arcpy.SetProgressorPosition()
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
            PrintMsg("Appending " + str(len(mupointList)) + " map unit point shapefiles to create new featureclass: " + outLayerName, 0)
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
                arcpy.arcpy.SetProgressorPosition()
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
            PrintMsg("Appending " + str(len(sflineList)) + " special feature line shapefiles to create new featureclass: " + outLayerName, 0)
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
                arcpy.arcpy.SetProgressorPosition()
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
            PrintMsg("Appending " + str(len(sfpointList)) + " special feature point shapefiles to create new featureclass: " + outLayerName, 0)
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
                arcpy.arcpy.SetProgressorPosition()
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
            PrintMsg("Appending " + str(len(sapolyList)) + " survey boundary polygon shapefiles to create new featureclass: " + outLayerName, 0)

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

                    outLayer.CreateFeature(outFeature)
                    outFeature = None
                    #geom = None

                # Calculate total number of input features read from all shapefiles
                # At completion, this should match final count in the output database.
                arcpy.arcpy.SetProgressorPosition()
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

        errorMsg(sys.exc_info())
        return False


## ===================================================================================
def AppendFeatures_Spatialite(inputDB, geogRegion, mupolyList, mulineList, mupointList, sflineList, sfpointList, sapolyList, featCnt, srid):
    # Using spatialite.exe commandline to perform all spatial imports.
    # This seems to be one option for avoiding DLL Hell.
    #


    # Merge all spatial layers into a set of file geodatabase featureclasses
    # Compare shapefile feature count to GDB feature count
    # featCnt:  0 mupoly, 1 muline, 2 mupoint, 3 sfline, 4 sfpoint, 5 sapoly

    # Geometry functions:
    #    MPolyFromText, ST_MPolyFromText, MultiPolygonFromText, ST_MultiPolygonFromText
    #    PolygonFromText, ST_PolyFromText, ST_PolygonFromText
    #    LineStringFromText, LineFromText
    #    PointFromText

    try:
        result = False
        #si = subprocess.STARTUPINFO()
        #si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        #si.wShowWindow = subprocess.SW_HIDE # default This did not seem to work
        CREATE_NO_WINDOW = 0x08000000 # for subprocess, don't show window
        PrintMsg(" \nUsing Spatialite Tools!", 0)
        slExe = r"C:\Program Files\Utilities\spatialite-tools-5.0.0-win-amd64\spatialite.exe"
        stExe = r"C:\Program Files\Utilities\spatialite-tools-5.0.0-win-amd64\spatialite_tool.exe"


        # Would like to figure out how to drop and create spatial indexes.
        # data_source.ExecuteSQL("SELECT CreateSpatialIndex('the_table', '{}')".format(layer.GetGeometryColumn()))
        # DisableSpatialIndex(table_name String, geom_column_name String)
        # HasSpatialIndex(‘table_name’,’geom_col_name’)
        arcpy.ResetProgressor()


        # Start timer to test performance of imports and spatial indexes
        start = time.time()   # start clock to measure total processing time for importing soil polygons


        # Save record of soil polygon shapefiles with invalid geometry
        dBadGeometry = dict()

        # *********************************************************************
        # Merge process MUPOLYGON
        # *********************************************************************
        #
        if len(mupolyList) > 0:

            # Get information for the output layer
            #
            outLayerName = "mupolygon"
            tmpShp = "xx_mupolygon"

            # Drop spatial index first
            #PrintMsg(".\tPreparing to drop spatial indexes...", 1)
            #bDropped = DropSpatialIndex(ds, outLayerName)

            #if bDropped == False:
            #    PrintMsg(".\tFailed to drop spatial index for " + outLayerName, 1)


            # Create corresponding list of field names for the virtual shapefile.
            # These tables use pkuid and geometry instead of objectid and shape.
            # Get field info from mupolygon (output layer) first
            PrintMsg(".", 0)
            PrintMsg("Appending " + Number_Format(len(mupolyList), 0, True) + " map unit polygon shapefiles to create new featureclass: " + outLayerName, 0)
            arcpy.SetProgressor("step", "Appending features to " + outLayerName + " layer", 0, len(mupolyList), 1)
            #PrintMsg(".\tGetting " + outLayerName + " layer object from database", 0)

            inputCnt = 0  # counter for total number of features processed
            layerCnt = 0  # counter for total number of shapefiles imported

            for shpFile in mupolyList:
                # Reference
                # http://www.gaia-gis.it/gaia-sins/spatialite-sql-4.2.0.html#cast
                outLayerName = "mupolygon"
                tmpShp = "xx_" + outLayerName
                shp = shpFile[0:-4]

                PrintMsg(".\tProcessing " + shpFile + "...", 0)
                PrintMsg(".\t", 0)
                time.sleep(1)

                layerCnt += 1

                # Try using spatialite to convert shapefile to sqlite tabble, using commandline spatialite_tool.
                # I see there is an AddGeometryColumn error on the second iteration, because the
                # Drop Table is not cleaning up other related metadata from the first shapefile.
                #
                shpArgs1 = [stExe, "-i", "-shp", shp, "-d", inputDB, "-t", tmpShp, "-g", "shape", "-s", "4326", "-c", "CP1252", "--type", "POLYGON"]
                #shpArgs = ", ".join(shpArgs1)
                #PrintMsg(".\t", 0)
                #PrintMsg(str(shpArgs1), 0)
                #PrintMsg(".\t", 0)
                #time.sleep(3)
                #subprocess.call(shpCmd, creationflags=CREATE_NO_WINDOW)  # this works
                result = subprocess.run(shpArgs1, capture_output=True, text=True, creationflags=CREATE_NO_WINDOW)  # new

                time.sleep(3)
                resultOut = result.stdout
                resultError = result.stderr
                resultCode = result.check_returncode()

                if resultError.find("Inserted") < 0:
                    # Seems like spatialite_tool only returns information in stderr,
                    # not in return_code or stdout. See if you can find documentation on this issue.
                    #
                    #PrintMsg(".\tShapefile import error: ", 0)
                    PrintMsg(str(resultError), 0)
                    #PrintMsg(".\tShapefile import result code: " + str(resultCode), 0)
                    #time.sleep(1)
                    pass

                else:
                    #PrintMsg(".\tShapefile imported into temporary table...", 0)
                    #PrintMsg(".\tResult: " + resultError, 0)
                    #time.sleep(1)

                    # If shapefile immport was successful, insert the contents of xx_mupolygon into mupolygon
                    sqlInsert = "INSERT INTO " + outLayerName + " (shape, areasymbol, spatialver, musym, mukey) SELECT CastToMultiPolygon(shape) AS shape, areasymbol, spatialver, musym, mukey FROM " + tmpShp + " ;"
                    insertCmd = [slExe, inputDB, sqlInsert]
                    #PrintMsg(".\t", 0)
                    #PrintMsg(".\tsqlInsert: " + str(sqlInsert), 0)
                    #PrintMsg(".", 0)
                    #time.sleep(1)

                    result = subprocess.run(insertCmd , capture_output=True, text=True)  # new
                    #PrintMsg(".\tRunning:\tsubprocess.run(" + str(insertCmd) + ", capture_output=True, text=True)", 0)
                    #PrintMsg(".", 0)
                    #time.sleep(1)
                    #result = subprocess.run([slExe, inputDB, sqlInsert], capture_output=True, text=True)
                    #PrintMsg(".\tExecuted insert", 0)
                    #PrintMsg(".\t", 0)
                    #time.sleep(1)
                    resultOut = result.stdout
                    resultError = result.stderr
                    resultCode = result.check_returncode()
                    #PrintMsg(".\tGot Insert result objects", 0)
                    #PrintMsg(".\t", 0)
                    #time.sleep(5)

##                    if resultError.find("Inserted") < 0:
##                        # Seems like spatialite_tool only returns information in stderr,
##                        # not in return_code or stdout. See if you can find documentation on this issue.
##                        #
##                        PrintMsg(".\tMupolygon import error? ", 0)
##                        PrintMsg(str(resultError), 0)
##                        #PrintMsg(".\tMupolygon import result code: " + str(resultCode), 0)
##                        PrintMsg(".\tMupolygon import result stdout: " + str(resultOut), 0)
##                        time.sleep(1)
##
##                    else:
##                        PrintMsg(".\tMupolygon successfully imported data...", 0)
##                        PrintMsg(".\tResult: " + resultError, 0)


                    # Try to drop xx_mupolygon.
                    # I see there is an AddGeometryColumn error on the second iteration, because the
                    # Drop Table is not cleaning up other related metadata from the first shapefile.
                    #time.sleep(1)  # see if a pause here will allow the insert to run
                    #PrintMsg(".\t", 0)
                    #PrintMsg(".\tDropping table " + tmpShp, 0)
                    #time.sleep(1)
                    dropSQL = "DROP TABLE IF EXISTS " + tmpShp + " ;"
                    #dropCmd = r'"C:\Program Files\Utilities\spatialite-tools-5.0.0-win-amd64\spatialite.exe" -silent "' + inputDB + '" ' + dropSQL
                    #PrintMsg(str([slExe, "-silent", inputDB, dropSQL]), 0)
                    #subprocess.call(dropCmd, creationflags=CREATE_NO_WINDOW)
                    #subprocess.run([slExe, "-silent", inputDB, dropSQL], capture_output=True, text=True)  # new
                    result = subprocess.run([slExe, inputDB, dropSQL], capture_output=True, text=True)  # new

                    #PrintMsg(".\tDropped temporary table if existed", 0)
                    #time.sleep(1)

                    resultOut = result.stdout
                    resultError = result.stderr
                    resultCode = result.check_returncode()

##                    if resultError != "":
##                        # Seems like spatialite_tool only returns information in stderr,
##                        # not in return_code or stdout. See if you can find documentation on this issue.
##                        #
##                        PrintMsg(".\tDrop error? ", 0)
##                        PrintMsg(str(resultError), 0)
##                        #PrintMsg(".\tMupolygon import result code: " + str(resultCode), 0)
##                        PrintMsg(".\tDrop result stdout: " + str(resultOut), 0)
##                        time.sleep(1)
##
##                    else:
##                        PrintMsg(".\tresultError was an empty string", 0)
##                        PrintMsg(".\tDrop succeeded..", 0)
##                        PrintMsg(".\tDrop result error: " + resultError, 0)
##                        PrintMsg(".\tDrop result stdout: " + str(resultOut), 0)



                    # Drop 'xx_mupolygon' record in geometry_columns table
                    #time.sleep(1)  # see if a pause here will allow the insert to run
                    #PrintMsg(".\t", 0)
                    #PrintMsg(".\tDropping geometry_columns reference to " + tmpShp, 0)
                    #time.sleep(1)
                    dropSQL = "DELETE FROM geometry_columns WHERE f_table_name = '" + tmpShp + "' ;"
                    #dropCmd = r'"C:\Program Files\Utilities\spatialite-tools-5.0.0-win-amd64\spatialite.exe" -silent "' + inputDB + '" ' + dropSQL
                    #PrintMsg(str([slExe, "-silent", inputDB, dropSQL]), 0)
                    #subprocess.call(dropCmd, creationflags=CREATE_NO_WINDOW)
                    #subprocess.run([slExe, "-silent", inputDB, dropSQL], capture_output=True, text=True)  # new
                    result = subprocess.run([slExe, inputDB, dropSQL], capture_output=True, text=True)  # new

                    #PrintMsg(".\tDropped temporary table if existed", 0)
                    #time.sleep(5)

                    resultOut = result.stdout
                    resultError = result.stderr
                    resultCode = result.check_returncode()

##                    if resultError != "":
##                        # Seems like spatialite_tool only returns information in stderr,
##                        # not in return_code or stdout. See if you can find documentation on this issue.
##                        #
##                        PrintMsg(".\tDrop geometry_column error? ", 0)
##                        PrintMsg(str(resultError), 0)
##                        #PrintMsg(".\tMupolygon import result code: " + str(resultCode), 0)
##                        PrintMsg(".\tDrop geometry_column result stdout: " + str(resultOut), 0)
##                        time.sleep(10)
##
##                    else:
##                        PrintMsg(".\tresultError was an empty string", 0)
##                        PrintMsg(".\tDrop geometry_column record succeeded..", 0)
##                        PrintMsg(".\tDrop result error: " + resultError, 0)
##                        PrintMsg(".\tDrop result stdout: " + str(resultOut), 0)

                    del tmpShp

            PrintMsg(".\tCurrent end of 'for shpFile' iteration", 0)



        # *********************************************************************
        # Merge process MULINE
        # *********************************************************************
        # mupolyList, mulineList, mupointList, sflineList, sfpointList, sapolyList
        if len(mulineList) > 0:

            # Get information for the output layer
            #
            outLayerName = "muline"
            tmpShp = "xx_" + outLayerName

            # Create corresponding list of field names for the virtual shapefile.
            # These tables use pkuid and geometry instead of objectid and shape.
            # Get field info from mupolygon (output layer) first
            PrintMsg(".", 0)
            PrintMsg("Appending " + Number_Format(len(mulineList), 0, True) + " map unit line shapefiles to create new featureclass: " + outLayerName, 0)
            arcpy.SetProgressor("step", "Appending features to " + outLayerName + " layer", 0, len(mulineList), 1)

            inputCnt = 0  # counter for total number of features processed
            layerCnt = 0  # counter for total number of shapefiles imported

            for shpFile in mulineList:
                # Reference
                # http://www.gaia-gis.it/gaia-sins/spatialite-sql-4.2.0.html#cast
                outLayerName = "muline"
                tmpShp = "xx_" + outLayerName
                shp = shpFile[0:-4]

                PrintMsg(".\tProcessing " + shpFile + "...", 0)
                PrintMsg(".\t", 0)
                layerCnt += 1

                # Try using spatialite to convert shapefile to sqlite tabble, using commandline spatialite_tool.
                # I see there is an AddGeometryColumn error on the second iteration, because the
                # Drop Table is not cleaning up other related metadata from the first shapefile.
                #
                shpArgs1 = [stExe, "-i", "-shp", shp, "-d", inputDB, "-t", tmpShp, "-g", "shape", "-s", "4326", "-c", "CP1252", "--type", "LINESTRING"]
                result = subprocess.run(shpArgs1, capture_output=True, text=True, creationflags=CREATE_NO_WINDOW)  # new
                resultOut = result.stdout
                resultError = result.stderr
                resultCode = result.check_returncode()

                if resultError.find("Inserted") < 0:
                    # Seems like spatialite_tool only returns information in stderr,
                    # not in return_code or stdout. See if you can find documentation on this issue.
                    pass

                else:
                    PrintMsg(".\tShapefile imported into temporary table...", 0)
                    PrintMsg(".\tResult: " + resultError, 0)
                    time.sleep(1)

                    # If shapefile immport was successful, insert the contents of xx_mupolygon into mupolygon
                    sqlInsert = "INSERT INTO " + outLayerName + " (shape, areasymbol, spatialver, musym, mukey) SELECT shape, areasymbol, spatialver, musym, mukey FROM " + tmpShp + " ;"
                    insertCmd = [slExe, inputDB, sqlInsert]
                    result = subprocess.run(insertCmd , capture_output=True, text=True)  # new

                    resultOut = result.stdout
                    resultError = result.stderr
                    resultCode = result.check_returncode()

                    dropSQL = "DROP TABLE IF EXISTS " + tmpShp + " ;"

                    result = subprocess.run([slExe, inputDB, dropSQL], capture_output=True, text=True)  # new

                    resultOut = result.stdout
                    resultError = result.stderr
                    resultCode = result.check_returncode()


                    # Drop 'tmpShp' record in geometry_columns table
                    dropSQL = "DELETE FROM geometry_columns WHERE f_table_name = '" + tmpShp + "' ;"
                    result = subprocess.run([slExe, inputDB, dropSQL], capture_output=True, text=True)  # new

                    resultOut = result.stdout
                    resultError = result.stderr
                    resultCode = result.check_returncode()


                    del tmpShp

            #PrintMsg(".\tCurrent end of 'for shpFile' iteration", 0)


        # *********************************************************************
        # Merge process MUPOINT
        # *********************************************************************
        # mupolyList, mulineList, mupointList, sflineList, sfpointList, sapolyList
        if len(mupointList) > 0:

            # Get information for the output layer
            #
            outLayerName = "mupoint"
            tmpShp = "xx_" + outLayerName

            # Create corresponding list of field names for the virtual shapefile.
            # These tables use pkuid and geometry instead of objectid and shape.
            # Get field info from mupolygon (output layer) first
            PrintMsg(".", 0)
            PrintMsg("Appending " + Number_Format(len(mupointList), 0, True) + " map unit point shapefiles to create new featureclass: " + outLayerName, 0)
            arcpy.SetProgressor("step", "Appending features to " + outLayerName + " layer", 0, len(mupointList), 1)
            #PrintMsg(".\tGetting " + outLayerName + " layer object from database", 0)

            inputCnt = 0  # counter for total number of features processed
            layerCnt = 0  # counter for total number of shapefiles imported

            for shpFile in mupointList:
                # Reference
                # http://www.gaia-gis.it/gaia-sins/spatialite-sql-4.2.0.html#cast
                tmpShp = "xx_" + outLayerName
                shp = shpFile[0:-4]

                PrintMsg(".\tProcessing " + shpFile + "...", 0)
                PrintMsg(".\t", 0)
                layerCnt += 1

                # Try using spatialite to convert shapefile to sqlite tabble, using commandline spatialite_tool.
                # I see there is an AddGeometryColumn error on the second iteration, because the
                # Drop Table is not cleaning up other related metadata from the first shapefile.
                #
                shpArgs1 = [stExe, "-i", "-shp", shp, "-d", inputDB, "-t", tmpShp, "-g", "shape", "-s", "4326", "-c", "CP1252", "--type", "POINT"]
                result = subprocess.run(shpArgs1, capture_output=True, text=True, creationflags=CREATE_NO_WINDOW)  # new

                resultOut = result.stdout
                resultError = result.stderr
                resultCode = result.check_returncode()

                if resultError.find("Inserted") < 0:
                    # Seems like spatialite_tool only returns information in stderr,
                    # not in return_code or stdout. See if you can find documentation on this issue.
                    pass

                else:
                    # If shapefile immport was successful, insert the contents of xx_mupolygon into mupolygon
                    sqlInsert = "INSERT INTO " + outLayerName + " (shape, areasymbol, spatialver, musym, mukey) SELECT shape, areasymbol, spatialver, musym, mukey FROM " + tmpShp + " ;"
                    insertCmd = [slExe, inputDB, sqlInsert]
                    result = subprocess.run(insertCmd , capture_output=True, text=True)  # new

                    resultOut = result.stdout
                    resultError = result.stderr
                    resultCode = result.check_returncode()

                    dropSQL = "DROP TABLE IF EXISTS " + tmpShp + " ;"
                    result = subprocess.run([slExe, inputDB, dropSQL], capture_output=True, text=True)  # new

                    resultOut = result.stdout
                    resultError = result.stderr
                    resultCode = result.check_returncode()


                    # Drop 'tmpShp' record in geometry_columns table
                    dropSQL = "DELETE FROM geometry_columns WHERE f_table_name = '" + tmpShp + "' ;"
                    result = subprocess.run([slExe, inputDB, dropSQL], capture_output=True, text=True)  # new

                    resultOut = result.stdout
                    resultError = result.stderr
                    resultCode = result.check_returncode()


                    del tmpShp

            #PrintMsg(".\tCurrent end of 'for shpFile' iteration", 0)


        # *********************************************************************
        # Merge process FEATLINE
        # *********************************************************************
        # mupolyList, mulineList, mupointList, sflineList, sfpointList, sapolyList
        if len(sflineList) > 0:

            # Get information for the output layer
            #
            outLayerName = "featline"
            tmpShp = "xx_" + outLayerName

            # Create corresponding list of field names for the virtual shapefile.
            # These tables use pkuid and geometry instead of objectid and shape.
            # Get field info from mupolygon (output layer) first
            PrintMsg(".", 0)
            PrintMsg("Appending " + Number_Format(len(sflineList), 0, True) + " special feature line shapefiles to create new featureclass: " + outLayerName, 0)
            arcpy.SetProgressor("step", "Appending features to " + outLayerName + " layer", 0, len(sflineList), 1)

            inputCnt = 0  # counter for total number of features processed
            layerCnt = 0  # counter for total number of shapefiles imported

            for shpFile in sflineList:
                # Reference
                # http://www.gaia-gis.it/gaia-sins/spatialite-sql-4.2.0.html#cast
                tmpShp = "xx_" + outLayerName
                shp = shpFile[0:-4]

                PrintMsg(".\tProcessing " + shpFile + "...", 0)
                layerCnt += 1

                # Try using spatialite to convert shapefile to sqlite tabble, using commandline spatialite_tool.

                shpArgs1 = [stExe, "-i", "-shp", shp, "-d", inputDB, "-t", tmpShp, "-g", "shape", "-s", "4326", "-c", "CP1252", "--type", "LINESTRING"]
                result = subprocess.run(shpArgs1, capture_output=True, text=True, creationflags=CREATE_NO_WINDOW)  # new
                resultOut = result.stdout
                resultError = result.stderr
                resultCode = result.check_returncode()

                if resultError.find("Inserted") < 0:
                    # Seems like spatialite_tool only returns information in stderr,
                    # not in return_code or stdout. See if you can find documentation on this issue.
                    pass

                else:
                    # If shapefile immport was successful, insert the contents of xx_mupolygon into mupolygon
                    sqlInsert = "INSERT INTO " + outLayerName + " (shape, areasymbol, spatialver, featsym, featkey) SELECT shape, areasymbol, spatialver, featsym, featkey FROM " + tmpShp + " ;"
                    insertCmd = [slExe, inputDB, sqlInsert]
                    result = subprocess.run(insertCmd , capture_output=True, text=True)  # new

                    resultOut = result.stdout
                    resultError = result.stderr
                    resultCode = result.check_returncode()

                    # Try to drop xx_mupolygon.
                    # I see there is an AddGeometryColumn error on the second iteration, because the
                    # Drop Table is not cleaning up other related metadata from the first shapefile.

                    PrintMsg(".\t", 0)

                    dropSQL = "DROP TABLE IF EXISTS " + tmpShp + " ;"

                    result = subprocess.run([slExe, inputDB, dropSQL], capture_output=True, text=True)  # new

                    resultOut = result.stdout
                    resultError = result.stderr
                    resultCode = result.check_returncode()

                    # Drop 'tmpShp' record in geometry_columns table

                    dropSQL = "DELETE FROM geometry_columns WHERE f_table_name = '" + tmpShp + "' ;"
                    result = subprocess.run([slExe, inputDB, dropSQL], capture_output=True, text=True)  # new
                    resultOut = result.stdout
                    resultError = result.stderr
                    resultCode = result.check_returncode()


                    del tmpShp

            #PrintMsg(".\tCurrent end of 'for shpFile' iteration for " + outLayerName, 0)
            #time.sleep(5)

        # *********************************************************************
        # Merge process FEATPOINT
        # *********************************************************************
        # mupolyList, mulineList, mupointList, sflineList, sfpointList, sapolyList
        if len(sfpointList) > 0:

            # Get information for the output layer
            #
            outLayerName = "featpoint"
            tmpShp = "xx_" + outLayerName

            # Create corresponding list of field names for the virtual shapefile.
            # These tables use pkuid and geometry instead of objectid and shape.
            # Get field info from mupolygon (output layer) first
            PrintMsg(".", 0)
            PrintMsg("Appending " + Number_Format(len(sfpointList), 0, True) + " special feature point shapefiles to create new featureclass: " + outLayerName, 0)
            arcpy.SetProgressor("step", "Appending features to " + outLayerName + " layer", 0, len(sfpointList), 1)
            time.sleep(5)

            inputCnt = 0  # counter for total number of features processed
            layerCnt = 0  # counter for total number of shapefiles imported

            for shpFile in sfpointList:
                # Reference
                # http://www.gaia-gis.it/gaia-sins/spatialite-sql-4.2.0.html#cast
                tmpShp = "xx_" + outLayerName
                shp = shpFile[0:-4]

                PrintMsg(".\tProcessing " + shpFile + "...", 0)
                PrintMsg(".\t", 0)
                time.sleep(1)

                layerCnt += 1

                # Try using spatialite to convert shapefile to sqlite tabble, using commandline spatialite_tool.

                shpArgs1 = [stExe, "-i", "-shp", shp, "-d", inputDB, "-t", tmpShp, "-g", "shape", "-s", "4326", "-c", "CP1252", "--type", "POINT"]
                result = subprocess.run(shpArgs1, capture_output=True, text=True, creationflags=CREATE_NO_WINDOW)  # new

                time.sleep(3)
                resultOut = result.stdout
                resultError = result.stderr
                resultCode = result.check_returncode()

                if resultError.find("Inserted") < 0:
                    # Seems like spatialite_tool only returns information in stderr,
                    pass

                else:
                    PrintMsg(".\tShapefile imported into temporary table...", 0)
                    PrintMsg(".\tResult: " + resultError, 0)
                    #time.sleep(5)

                    # If shapefile immport was successful, insert the contents of xx_mupolygon into mupolygon
                    sqlInsert = "INSERT INTO " + outLayerName + " (shape, areasymbol, spatialver, featsym, featkey) SELECT shape, areasymbol, spatialver, featsym, featkey FROM " + tmpShp + " ;"
                    insertCmd = [slExe, inputDB, sqlInsert]
                    result = subprocess.run(insertCmd , capture_output=True, text=True)  # new

                    resultOut = result.stdout
                    resultError = result.stderr
                    resultCode = result.check_returncode()

                    dropSQL = "DROP TABLE IF EXISTS " + tmpShp + " ;"
                    result = subprocess.run([slExe, inputDB, dropSQL], capture_output=True, text=True)  # new
                    resultOut = result.stdout
                    resultError = result.stderr
                    resultCode = result.check_returncode()

                    # Drop 'tmpShp' record in geometry_columns table
                    dropSQL = "DELETE FROM geometry_columns WHERE f_table_name = '" + tmpShp + "' ;"
                    result = subprocess.run([slExe, inputDB, dropSQL], capture_output=True, text=True)  # new

                    resultOut = result.stdout
                    resultError = result.stderr
                    resultCode = result.check_returncode()

                    del tmpShp

        # *********************************************************************
        # Merge process SAPOLYGON
        # *********************************************************************
        # mupolyList, mulineList, mupointList, sflineList, sfpointList, sapolyList
        if len(sapolyList) > 0:

            # Get information for the output layer
            #
            outLayerName = "sapolygon"
            tmpShp = "xx_" + outLayerName
            #PrintMsg(".\toutLayerName: " + str(outLayerName), 0)


            # Create corresponding list of field names for the virtual shapefile.
            # These tables use pkuid and geometry instead of objectid and shape.
            # Get field info from mupolygon (output layer) first
            PrintMsg(".", 0)
            PrintMsg("Appending " + Number_Format(len(sapolyList), 0, True) + " survey boundary shapefiles to create new featureclass: " + outLayerName, 0)
            arcpy.SetProgressor("step", "Appending features to " + outLayerName + " layer", 0, len(sapolyList), 1)

            inputCnt = 0  # counter for total number of features processed
            layerCnt = 0  # counter for total number of shapefiles imported

            for shpFile in sapolyList:
                # Reference
                # http://www.gaia-gis.it/gaia-sins/spatialite-sql-4.2.0.html#cast
                tmpShp = "xx_" + outLayerName
                shp = shpFile[0:-4]

                PrintMsg(".\tProcessing " + shpFile + "...", 0)
                PrintMsg(".\t", 0)

                layerCnt += 1

                # Try using spatialite to convert shapefile to sqlite tabble, using commandline spatialite_tool.
                # I see there is an AddGeometryColumn error on the second iteration, because the
                # Drop Table is not cleaning up other related metadata from the first shapefile.
                #
                shpArgs1 = [stExe, "-i", "-shp", shp, "-d", inputDB, "-t", tmpShp, "-g", "shape", "-s", "4326", "-c", "CP1252", "--type", "POLYGON"]
                result = subprocess.run(shpArgs1, capture_output=True, text=True, creationflags=CREATE_NO_WINDOW)  # new
                resultOut = result.stdout
                resultError = result.stderr
                resultCode = result.check_returncode()

                if resultError.find("Inserted") < 0:
                    # Seems like spatialite_tool only returns information in stderr,
                    pass

                else:
                    sqlInsert = "INSERT INTO " + outLayerName + " (shape, areasymbol, spatialver, lkey) SELECT CastToMultiPolygon(shape) AS shape, areasymbol, spatialver, lkey FROM " + tmpShp + " ;"
                    insertCmd = [slExe, inputDB, sqlInsert]

                    result = subprocess.run(insertCmd , capture_output=True, text=True)  # new

                    resultOut = result.stdout
                    resultError = result.stderr
                    resultCode = result.check_returncode()
                    dropSQL = "DROP TABLE IF EXISTS " + tmpShp + " ;"
                    result = subprocess.run([slExe, inputDB, dropSQL], capture_output=True, text=True)  # new

                    resultOut = result.stdout
                    resultError = result.stderr
                    resultCode = result.check_returncode()


                    # Drop 'tmpShp' record in geometry_columns table

                    dropSQL = "DELETE FROM geometry_columns WHERE f_table_name = '" + tmpShp + "' ;"

                    result = subprocess.run([slExe, inputDB, dropSQL], capture_output=True, text=True)  # new

                    resultOut = result.stdout
                    resultError = result.stderr
                    resultCode = result.check_returncode()

                    del tmpShp

        PrintMsg(".\t", 0)
        PrintMsg(".\tProcess complete for this function...", 0)

        result = True
        return result

    except MyError as e:
        PrintMsg(str(e), 2)
        return result

    except:
        errorMsg(sys.exc_info())
        return result

## ===================================================================================
def AppendFeatures_ArcPy(inputDB, geogRegion, mupolyList, mulineList, mupointList, sflineList, sfpointList, sapolyList, featCnt):
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
        #env.workspace = inputDB

        # Put datum transformation methods in place
        #geogRegion = "CONUS"
        PrintMsg(".", 0)
        PrintMsg(".\tImporting spatial data using AppendFeatures_ArcPy function...", 0)
        time.sleep(1)
        arcpy.ResetProgressor()

        # Assuming input featureclasses from Web Soil Survey are GCS WGS1984 and that
        # output datum is either NAD 1983 or WGS 1984. Output coordinate system will be
        # defined by the existing output featureclass.

        #if not arcpy.Exists(os.path.join(inputDB, "mupolygon")):
        #    raise MyError(".\tOutput not found (" + os.path.join(inputDB, "mupolygon") + ")")

        # Merge process MUPOLYGON
        if len(mupolyList) > 0:
            # Note for June 24th, appending multiple shapefiles is failing for my new spatialite database.
            # Crash with no error message
            # Seems to work OK for a single input shapefile
            # Would like to try running Append multiple times instead..
            #
            PrintMsg(".\tAppending " + str(len(mupolyList)) + " soil mapunit polygon shapefiles to create new featureclass: " + "MUPOLYGON", 0)
            arcpy.SetProgressorLabel("Appending features to MUPOLYGON layer")
            time.sleep(3)
            arcpy.Append_management(mupolyList,  os.path.join(inputDB, "mupolygon"), "NO_TEST" )
            PrintMsg(".\tAppend completed...", 0)
            PrintMsg(".\t")
            time.sleep(5)

##            for mupoly in mupolyList:
##                PrintMsg(".\t\tAppending shapefile " + mupoly + "...", 0)
##                arcpy.Append_management(mupoly,  os.path.join(inputDB, "mupolygon"), "NO_TEST" )
##                PrintMsg(".\tAppend complete for mupoly", 1)
##                time.sleep(5)


##            PrintMsg(".\tGetting feature count from mupolygon", 1)
##            sqlCount = 'SELECT COUNT(*) FROM mupolygon;'
##            liteCur.execute(sqlCount)
##            row = liteCur.fetchone()
##            featCnt = row[0]
##            mupolyCnt = int(arcpy.GetCount_management(os.path.join(inputDB, "mupolygon")).getOutput(0))
##
##            if mupolyCnt != featCnt[0]:
##                err = "Merged MUPOLYGON count: " + Number_Format(mupolyCnt, 0, True) + " \nInput polygon count: " + Number_Format(featCnt[0], 0, True) + ":  "
##                PrintMsg(err, 2)
##                time.sleep(10)
##                raise MyError(err)

        # Merge process MULINE
        if len(mulineList) > 0:
            PrintMsg(".\tAppending " + str(len(mulineList)) + " soil mapunit line shapefiles to create new featureclass: " + "MULINE", 0)
            arcpy.SetProgressorLabel("Appending features to MULINE layer")
            arcpy.Append_management(mulineList,  os.path.join(inputDB, "muline"), "NO_TEST")
            mulineCnt = int(arcpy.GetCount_management(os.path.join(inputDB, "muline")).getOutput(0))

            if mulineCnt != featCnt[1]:
                time.sleep(5)
                err = "MULINE short count"
                raise MyError(err)

        # Merge process MUPOINT
        if len(mupointList) > 0:
            PrintMsg(".\tAppending " + str(len(mupointList)) + " soil mapunit point shapefiles to create new featureclass: " + "MUPOINT", 0)
            arcpy.SetProgressorLabel("Appending features to MUPOINT layer")
            arcpy.Append_management(mupointList,  os.path.join(inputDB, "mupoint"), "NO_TEST")
            mupointCnt = int(arcpy.GetCount_management(os.path.join(inputDB, "mupoint")).getOutput(0))

            if mupointCnt != featCnt[2]:
                time.sleep(5)
                err = "MUPOINT short count"
                raise MyError(err)

            # Add indexes
            arcpy.AddSpatialIndex_management (os.path.join(inputDB, "MUPOINT"))
            #arcpy.AddIndex_management(os.path.join(inputDB, "MUPOINT"), "AREASYMBOL", "Indx_MupointAreasymbol")

        # Merge process FEATLINE
        if len(sflineList) > 0:
            PrintMsg(".\tAppending " + str(len(sflineList)) + " special feature line shapefiles to create new featureclass: " + "FEATLINE", 0)
            arcpy.SetProgressorLabel("Appending features to FEATLINE layer")
            arcpy.Append_management(sflineList,  os.path.join(inputDB, "featline"), "NO_TEST")
            sflineCnt = int(arcpy.GetCount_management(os.path.join(inputDB, "featline")).getOutput(0))

            if sflineCnt != featCnt[3]:
                time.sleep(5)
                err = "FEATLINE short count"
                raise MyError(err)

        # Merge process FEATPOINT
        if len(sfpointList) > 0:
            PrintMsg(".\tAppending " + str(len(sfpointList)) + " special feature point shapefiles to create new featureclass: " + "FEATPOINT", 0)
            arcpy.SetProgressorLabel("Appending features to FEATPOINT layer")
            arcpy.Append_management(sfpointList,  os.path.join(inputDB, "featpoint"), "NO_TEST")
            sfpointCnt = int(arcpy.GetCount_management(os.path.join(inputDB, "featpoint")).getOutput(0))

            if sfpointCnt != featCnt[4]:
                PrintMsg(" \nExported " + str(sfpointCnt) + " points to geodatabase", 1)
                time.sleep(5)
                err = "FEATPOINT short count"
                raise MyError(err)

        # Merge process SAPOLYGON
        #if 1== 2:
        if len(sapolyList) > 0:
            PrintMsg(".\tAppending " + str(len(sapolyList)) + " survey boundary shapefiles to create new featureclass: " + "SAPOLYGON", 0)
            #PrintMsg("sapolyList: " + str(sapolyList), 0)
            #time.sleep(3)
            arcpy.SetProgressorLabel("Appending features to SAPOLYGON layer")

            PrintMsg(".", 0)
            #time.sleep(10)

            arcpy.Append_management(sapolyList,  os.path.join(inputDB, "sapolygon"), "NO_TEST")

            #PrintMsg(".\tSkipping sapolygon feature count", 0)
            #time.sleep(5)
            #sapolyCnt = int(arcpy.GetCount_management(os.path.join(inputDB, "sapolygon")).getOutput(0))

            #if sapolyCnt != featCnt[5]:
            #    #PrintMsg("??? Imported " + Number_Format(sapolyCnt, 0, True) + " polygons from shapefile", 0)
            #    PrintMsg(".\tMismatch. Shapefiles had " + Number_Format(featCnt[5], 0, True) + " polygons", 0)
            #    PrintMsg(".\tOutput SAPOLYGON has " + Number_Format(sapolyCnt, 0, True) + " polygons", 0)
            #    time.sleep(10)
            #    err = "SAPOLYGON short count"
            #    raise MyError(err)

        PrintMsg("Successfully imported all spatial data to new database", 0)

        return True

    except MyError as e:
        PrintMsg(str(e), 2)
        return False

    except sqlite3.IntegrityError as err:
        PrintMsg(".\tSQLite IntegrityError: ", 2)
        time.sleep(5)
        PrintMsg(".\t" + err.args[0], 2)
        time.sleep(5)
        return False
        #errorMsg(sys.exc_info())  # not sure if sys will report the appropriate information.

    except sqlite3.Error as err:
        PrintMsg(".\tSQLite Error: ", 2)
        time.sleep(5)
        msg = err.args[0]
        PrintMsg(".\t" + msg, 2)
        time.sleep(5)
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

##        if outputSR.PCSCode == 0:
##            bProjected = False
##
##        else:
##            bProjected = True

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
            PrintMsg(".\tSetting output coordinate system to " + outputSR.name, 0)
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
def GetNewExtentsSpatialite(inputDB, layerList, conn, liteCur):
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

    try:
        arcpy.SetProgressorLabel("Registering spatial extents...")
        #from osgeo import ogr, gdal, osr
        #gdal.UseExceptions()

        spatialExtents = list()

        driver = ogr.GetDriverByName("SQLite")

        if driver is None:
            err = "Failed to get OGR inputDriver for " + inputDB
            raise MyError(err)

        ds = driver.Open(inputDB, 0)

        if ds is None:
            err = "Failed to open " + inputDB + " using ogr without driver"
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
def GetXML(geogRegion):
    # Not currently being used, but might have future use in setting an output coordinate system.
    #
    # Set appropriate XML Workspace Document according to geogRegion
    # The xml files referenced in this function must all be stored in the same folder as the
    # Python script and toolbox
    #
    # FY2016. Discovered that my MD* tables in the XML workspace documents were out of date.
    # Need to update and figure out a way to keep them updated
    #
    try:
        # Set folder path for workspace document (same as script)
        xmlPath = os.path.dirname(sys.argv[0])

        # Changed datum transformation to use ITRF00 for ArcGIS 10.1
        # FYI. Multiple geographicTransformations would require a semi-colon delimited string
        tm = "WGS_1984_(ITRF00)_To_NAD_1983"

        # Input XML workspace document used to create new SSURGO-Lite schema in an empty geodatabase
        if geogRegion == "Lower 48 States":
            inputXML = os.path.join(xmlPath, "gSSURGO_CONUS_AlbersNAD1983.xml")
            tm = "WGS_1984_(ITRF00)_To_NAD_1983"

        elif geogRegion == "Hawaii":
            inputXML = os.path.join(xmlPath, "gSSURGO_Hawaii_AlbersWGS1984.xml")
            tm = ""

        elif geogRegion == "American Samoa":
            inputXML = os.path.join(xmlPath, "gSSURGO_Hawaii_AlbersWGS1984.xml")
            tm = ""

        elif geogRegion == "Alaska":
            inputXML = os.path.join(xmlPath, "gSSURGO_Alaska_AlbersWGS1984.xml")
            tm = ""

        elif geogRegion == "Puerto Rico and U.S. Virgin Islands":
            inputXML = os.path.join(xmlPath, "gSSURGO_CONUS_AlbersNAD1983.xml")
            tm = "WGS_1984_(ITRF00)_To_NAD_1983"

        elif geogRegion == "Pacific Islands Area":
            inputXML = os.path.join(xmlPath, "gSSURGO_PACBasin_AlbersWGS1984.xml")
            # No datum transformation required for PAC Basin data
            tm = ""

        elif geogRegion == "World":
            PrintMsg(" \nOutput coordinate system will be Geographic WGS 1984", 0)
            inputXML = os.path.join(xmlPath, "gSSURGO_Geographic_WGS1984.xml")
            tm = ""

        else:
            PrintMsg(" \nNo projection is being applied", 1)
            inputXML = os.path.join(xmlPath, "gSSURGO_GCS_WGS1984.xml")
            tm = ""

        # Hardcoding XML workspace document for testing purposes
        inputXML = os.path.join(xmlPath, "SQLite_SpatiaLite1.xml")

        arcpy.env.geographicTransformations = tm

        return inputXML

    except:
        errorMsg(sys.exc_info())
        return ""

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

        if os.path.isfile(aoiLayer):
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

        if os.path.isfile(aoiLayer):
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
        if os.path.isfile(theInput):
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

        if SetScratch() == False:
            err = "Invalid scratch workspace setting (" + env.scratchWorkspace + ")"
            raise MyError(err)

        # get the information from the tileInfo
        if type(tileInfo) == tuple:
            if bClipped:
                # Set the aliasname when this is a clipped layer
                aliasName = ""
                description = tileInfo[1]

            else:
                # Try leaving the aliasname off of the regular layers.
                aliasName = tileInfo[0]
                description = tileInfo[1]

        else:
            stDict = StateNames()
            aliasName = tileInfo

            if aliasName in stDict:
                description = stDict[aliasName]

            else:
                description = tileInfo

        aliasName = ""

        #PrintMsg(" \nAlias and description: " + aliasName + "; " +  description, 1)

        ##  Begin processing input SSURGO datasets located in the 'inputFolder'

        if surveyList is not None and len(surveyList) == 0:
            err = "At least one soil survey area input is required"
            raise MyError(err)

        extentList = list()
        mupolyList = list()
        mupointList = list()
        mulineList = list()
        sflineList = list()
        sfpointList = list()
        sapolyList = list()
        pathList = list()

        if len(areasymbolList) == 0:
            # The 'Create SSURGO-Lite DB by Map' tool will skip this section because the SortSurveyAreas function
            # has already generated a spatial sort using the input survey boundary layer.
            #
            if surveyList is None:
                raise MyError()

            PrintMsg(".", 0)
            PrintMsg("Setting import order for " + str(len(surveyList)) + " selected surveys...", 0)
            PrintMsg(".", 0)

            driver = ogr.GetDriverByName("ESRI Shapefile")

            if driver is None:
                err = "Failed to get OGR inputDriver for " + inputDB
                raise MyError(err)

            for subFolder in surveyList:

                # Req: inputFolder, subFolder
                # build the input shapefilenames for each SSURGO featureclass type using the
                # AREASYMBOL then confirm shapefile existence for each survey and append to final input list
                # used for the Append command. Use a separate list for each featureclass type so
                # that missing or empty shapefiles will not be included in the Merge. A separate
                # Append process is used for each featureclass type.

                #areaSym = subFolder[(subFolder.rfind("_") + 1):].lower()  # STATSGO mod
                areaSym = subFolder[-5:].upper()
                #env.workspace = os.path.join( inputFolder, os.path.join( subFolder, "spatial"))
                shpPath = env.workspace = os.path.join( inputFolder, os.path.join( subFolder, "spatial"))
                mupolyName = "soilmu_a_" + areaSym.lower() + ".shp"
                gsmpolyName = "gsmsoilmu_a_" + areaSym.lower() + ".shp"
                mulineName = "soilmu_l_" + areaSym.lower() + ".shp"
                mupointName = "soilmu_p_" + areaSym.lower() + ".shp"
                sflineName = "soilsf_l_" + areaSym.lower() + ".shp"
                sfpointName = "soilsf_p_" + areaSym.lower() + ".shp"
                sapolyName = "soilsa_a_" + areaSym.lower() + ".shp"
                arcpy.SetProgressorLabel("Getting extent for " + areaSym.upper() + " survey area")
                #PrintMsg(" \nProcessing "  + areaSym.upper() + " survey area", 1)

                ds = driver.Open(os.path.join(shpPath, mupolyName), 0)

                if ds is None:
                    err = "Failed to open " + inputDB + " using ogr without driver"
                    raise MyError(err)

                # Try getting extent from sapolygon first
                layer = ds.GetLayerByIndex(0)
                featCnt = layer.GetFeatureCount()
                XMin, xMax, YMin, YMax = layer.GetExtent()  # ogr extents are not in the same order as arcpy

                ul = (areaSym, round(XMin, 5), round(YMax, 5)) # upper left corner of survey area
                extentList.append(ul)
                areasymbolList.append(areaSym.upper())

            #env.workspace = inputFolder

            if len(extentList) < len(surveyList):
                err = "Problem with survey extent sort key"
                raise MyError(err)

            if len(surveyList) > 1:
                # Sort the upper-left coordinate list so that the drawing order of the merged layer
                # is a little more efficient
                extentList.sort(key=itemgetter(1), reverse=False)
                extentList.sort(key=itemgetter(2), reverse=True)

                # Could use this information for registering spatial layers
                # But we will be missing the lower right coordinates...
                # Probably should use GetNewExtents function instead.
                minX = extentList[0][1]
                minY = extentList[1][2]
                maxX = extentList[-1][1]
                maxY = extentList[0][2]
                spatialExtents = (minX, minY, maxX, maxY)

                # spatially sorted list of areasymbols to control import order
                areasymbolList = list()
                cnt = 0

                for sortValu in extentList:
                    cnt += 1
                    areasym = sortValu[0]
                    areasymbolList.append(areasym)
                    #PrintMsg(str(cnt) + "," + areasym.upper(), 1)

            else:
                # only a single survey being imported
                areasymbolList = [areaSym]

        else:
            # Spatial sort has already been handled using the soil survey boundary layer.
            pass

        # Save the total featurecount for all input shapefiles
        mupolyCnt = 0
        mulineCnt = 0
        mupointCnt = 0
        sflineCnt = 0
        sfpointCnt = 0
        sapolyCnt = 0

        # Create a series of lists that contain the found shapefiles to be merged
        PrintMsg(".\tFound " + Number_Format(len(areasymbolList), 0, True) + " survey areas...", 0)
        PrintMsg(".\tCreating list of shapefiles to be imported for each survey area...", 0)
        arcpy.SetProgressor("step", "Adding surveys to merge list", 1, len(areasymbolList))

        # Drop any of these survey areas if they already exist
        bDropped = DropSSA(inputDB, areasymbolList)

        for areaSym in areasymbolList:
            #areaSym = sortValue[0]
            #PrintMsg(".\t1", 0)
            subFolder = "soil_" + areaSym.lower()

            shpPath = os.path.join( inputFolder, os.path.join( subFolder, "spatial"))

            # soil polygon shapefile
            mupolyName = "soilmu_a_" + areaSym.lower() + ".shp"
            gsmpolyName = "gsmsoilmu_a_" + areaSym.lower() + ".shp"
            muShp = os.path.join(shpPath, mupolyName)
            gsmuShp = os.path.join(shpPath, mupolyName)
            #PrintMsg(".\t2", 0)

            if os.path.isfile(muShp):

                cnt = int(arcpy.GetCount_management(muShp).getOutput(0))

                if cnt > 0:
                    if not muShp in mupolyList:
                        mupolyCnt += cnt
                        mupolyList.append(muShp)
                        #PrintMsg("\tAdding '" + areaSym.upper() + "' survey to merge list", 0)
                        arcpy.SetProgressorLabel("Added " + areaSym.upper() + " survey to merge list")

                        arcpy.SetProgressorLabel("Dropping " + areaSym.upper() + " survey from database if it exists")
                        #bDropped = DropSSA_Single(inputDB, areaSym)
                        #raise MyError(".\tEarly Out after DropSSA")


                else:
                    err = "No features found in " + shpFile
                    raise MyError(err)


            else:
                err = "Shapefile " + muShp + " not found"
                raise MyError(err)

            # input soil polyline shapefile
            mulineName = "soilmu_l_" + areaSym.lower() + ".shp"
            shpFile = os.path.join(shpPath, mulineName)

            if os.path.isfile(shpFile):
                cnt = int(arcpy.GetCount_management(shpFile).getOutput(0))

                if cnt > 0:
                    if not shpFile in mulineList:
                        mulineCnt += cnt
                        mulineList.append(shpFile)

            # input soil point shapefile
            mupointName = "soilmu_p_" + areaSym.lower() + ".shp"
            shpFile = os.path.join(shpPath, mupointName)

            if os.path.isfile(shpFile):
                cnt= int(arcpy.GetCount_management(shpFile).getOutput(0))

                if cnt > 0:
                    mupointCnt += cnt
                    mupointList.append(shpFile)

            # input specialfeature polyline shapefile name
            sflineName = "soilsf_l_" + areaSym.lower() + ".shp"
            shpFile = os.path.join(shpPath, sflineName)

            if os.path.isfile(shpFile):
                cnt = int(arcpy.GetCount_management(shpFile).getOutput(0))

                if cnt > 0:
                    if not shpFile in sflineList:
                        sflineCnt += cnt
                        sflineList.append(shpFile)

            # input special feature point shapefile
            sfpointName = "soilsf_p_" + areaSym.lower() + ".shp"
            shpFile = os.path.join(shpPath, sfpointName)

            if os.path.isfile(shpFile):
                cnt = int(arcpy.GetCount_management(shpFile).getOutput(0))
                #PrintMsg(" \nCounted " + str(cnt) + " features in " + shpFile, 1)

                if cnt > 0:
                    if not shpFile in sfpointList:
                        sfpointCnt += cnt
                        sfpointList.append(shpFile)

            # input soil survey boundary shapefile name
            sapolyName = "soilsa_a_" + areaSym.lower() + ".shp"
            shpFile = os.path.join(shpPath, sapolyName)

            if os.path.isfile(shpFile):
                cnt = int(arcpy.GetCount_management(shpFile.lower()).getOutput(0))

                if cnt > 0:
                    if not shpFile in sapolyList:
                        cnt = int(arcpy.GetCount_management(shpFile).getOutput(0))
                        sapolyCnt += cnt
                        sapolyList.append(shpFile)

            # input soil survey Template database
            # use database path, even if it doesn't exist. It will be used
            # to actually define the location of the tabular folder and textfiles
            # probably need to fix this later
            #
            dbPath = os.path.join( inputFolder, os.path.join( subFolder, "tabular"))

            if not dbPath in pathList:
                pathList.append(dbPath)

            arcpy.SetProgressorPosition()

        time.sleep(1)
        arcpy.ResetProgressor()

        if len(mupolyList) > 0:
            # Convert all shapefiles to a single geometry table
            gdbName = os.path.basename(inputDB)
            outFolder = os.path.dirname(inputDB)
            featCnt = (mupolyCnt, mulineCnt, mupointCnt, sflineCnt, sfpointCnt, sapolyCnt)  # 0 mupoly, 1 muline, 2 mupoint, 3 sfline, 4 sfpoint, 5 sapoly
            # bGeodatabase = CreateSSURGO_DB(inputDB,  areasymbolList, aliasName, templateDB)

            bGeodatabase = True

            if bGeodatabase:
                # Successfully created a new geodatabase
                # Merge all existing shapefiles to file geodatabase featureclasses
                #
                PrintMsg(".\tCreating new database connection...", 0)
                conn = sqlite3.connect(inputDB)
                conn.enable_load_extension(True)
                liteCur = conn.cursor()

                fkCheck = "ON"
                PrintMsg(".\tTurning " + fkCheck + " foreign key constraints...", 0)
                conn.execute("PRAGMA foreign_keys = " + fkCheck + ";") # PRAGMA foreign_key_check(table-name);
                conn.commit()

                PrintMsg(".\tIncreasing database cache size...", 0)
                bSet = SetCacheSize(conn, liteCur)

                # Drop existing attribute indexes from new database
                createSQLs = DropIndexes(conn, liteCur)

                if len(createSQLs) == 0:
                    PrintMsg(".\tNo attribute indexes exist in this new database", 0)
                    raise MyError("")  # remove this when the drop is working correctly

                tableList = GetTableList(inputDB, conn, liteCur)

                dbName, dbExt = os.path.splitext(os.path.basename(inputDB))

                # OGR driver selection. May need to move this. Not sure if it will be used.
                #
                if dbExt == ".gpkg":
                    # input database is geopackage
                    driverName = "GPKG"

                elif dbExt == ".sqlite":
                    driverName = "SQLite"

                else:
                    err = "OGR library is unable to handle type of database for " + inputDB
                    raise MyError(err)

                # Should probably open database connection here, and pass down liteCur to ImportMDTabular and ImportTabular functions.

                if not os.path.isfile(inputDB):
                    err = "Could not find " + inputDB + " to append tables to"
                    raise MyError(err)

                # Import tabular data first. Required to meet foreign key constraints.
                # Metadata tables must be pre-populated in the Template database.
                if dbExt in (".sqlite", ".gpkg"):

                    # Check the legend table to see if it has an objectid column
                    fldInfos = GetFieldInfo("legend", liteCur)
                    #fldNames = list()
                    bOID = False

                    for fld in fldInfos:
                        fldName, fldType = fld
                        if fldName.lower() == "objectid":
                            bOID = True
                            break

                    # Check the legend table to see if it has an objectid column
                    fldInfos = GetFieldInfo("cointerp", liteCur)
                    fldNames = list()

                    for fld in fldInfos:
                        fldName, fldType = fld

                        if fldName != "objectid":
                            fldNames.append(fldName)

                    if len(fldNames) < 18:
                        # output cointerp table doesn't have all columns, force exclusion of the deprecated columns
                        # could also search for specific column names
                        PrintMsg(".\tForcing population of reduced cointerp table", 0)
                        bDiet = True

                    if bOID:
                        # Create database with 'objectid' columns and reduced cointerp
                        #
                        bTabular = ImportTabularSQL3(inputDB, pathList, dbVersion, tableList, conn, liteCur)

                    else:
                        # Create a database without 'objectid'
                        #
                        if bDiet:
                            # Create database with reduced cointerp and no 'objectid' columns
                            #
                            bTabular = ImportTabularSQL2(inputDB, pathList, dbVersion, tableList, conn, liteCur)

                        else:
                            # Create database with standard cointerp and no 'objectid' columns
                            #
                            bTabular = ImportTabularSQL1(inputDB, pathList, dbVersion, tableList, conn, liteCur)

                elif dbExt == ".geodatabase":
                    bTabular = ImportTabularGDB(inputDB, pathList, dbVersion, tableList)

                if bTabular == True:
                    # Successfully imported all tabular data (textfiles or Access database tables)
                    PrintMsg(" \nAll tabular data imported", 0)
                    time.sleep(1)

                else:
                    raise MyError("Failed to export all data to SSURGO-Lite DB. Tabular export error.")

                # Close database before appending spatial data using arcpy
                #
##                conn.close()
##                del liteCur
##                del conn

                if bTabular:
                    # Next, import spatial data
                    # We need to check the SRID for the existing data layers and set the output to match
                    #
                    PrintMsg(".\tTabular import complete, ready to start spatial layers...", 0)

                    if bArcPy:

                        bProj = SetOutputCoordinateSystem(geogRegion, inputDB)
                        #time.sleep(2)
                        PrintMsg(".\tOutput CSR: " + env.outputCoordinateSystem.name, 0)
                        PrintMsg(".\tTM: " + str(env.geographicTransformations), 0)
                        bSpatial = False

                        bSpatial = AppendFeatures_ArcPy(inputDB, geogRegion, mupolyList, mulineList, mupointList, sflineList, sfpointList, sapolyList, featCnt)

                    else:
                        if inputDB.endswith(".sqlite"):
                            try:
                                # Trying to address locked database when more than one SSA is imported
                                dbConn.close()
                                del dbConn
                                del liteCur

                            except:
                                pass

                            PrintMsg(".\tUsing new function: AppendFeatures_Spatialite", 0)
                            bSpatial = AppendFeatures_Spatialite(inputDB, geogRegion, mupolyList, mulineList, mupointList, sflineList, sfpointList, sapolyList, featCnt)

                        elif inputDB.endswith(".gpkg"):
                            bSpatial = AppendFeatures(inputDB, geogRegion, mupolyList, mulineList, mupointList, sflineList, sfpointList, sapolyList, featCnt)


                        PrintMsg(".\tAppendFeatures_Spatialite1 returned: " + str(bSpatial), 0)

                    PrintMsg(".\tAppendFeatures_Spatialite2 returned: " + str(bSpatial), 0)

                    #
                    # Update metadata table to reflect new spatial extents
                    #
                    if bSpatial == True:

                        # Update spatial extents for each layer
                        #
                        conn = sqlite3.connect(inputDB)
                        conn.enable_load_extension(True)
                        liteCur = conn.cursor()

                        # For some reason I have sqlite autoindexes on the mdstat and sdv tables and cause an error
                        # with the ogr driver. Try turning them off or getting rid of them.
                        #queryAutoIndex = "PRAGMA automatic_index = 0;"
                        # queryCacheSize = "PRAGMA schema.cache_size = -200000;
                        #liteCur.execute(queryAutoIndex)
                        #conn.commit()

                        # Get survey area count for each layer
                        saCounts = list()

                        for saList in [sapolyList, mupolyList, mulineList, mupointList, sflineList, sfpointList]:
                            saCounts.append(len(saList))

                        # Get extents for each new layer
                        layerList = ["sapolygon", "mupolygon", "muline", "mupoint", "featline", "featpoint"]

                        if dbExt == ".gpkg":
                            bExtents = GetNewExtentsGpkg(inputDB, layerList, conn, liteCur) # , saCounts, spatialExtents

                        elif dbExt == ".sqlite":
                            PrintMsg(".\tUpdating extents for each spatial layer", 0)
                            PrintMsg(".\t", 0)
                            time.sleep(5)
                            bExtents = GetNewExtentsSpatialite(inputDB, layerList, conn, liteCur)

                        #conn.close()
                        #del liteCur
                        #del conn

                    else:
                        PrintMsg("Failed to export all data to SSURGO-Lite DB. Spatial export error", 2)
                        return False

            else:
                raise MyError("Failed to create new database")

            PrintMsg(".\tAppendFeatures_Spatialite returned: " + str(bSpatial), 0)
            PrintMsg(".", 0)
            PrintMsg("All tabular and spatial data have been imported...", 0)
            #PrintMsg(" \nSuccessfully created a geodatabase containing the following surveys: " + queryInfo, 0)

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

            conn.close()
            del liteCur
            del conn

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
        inputFolder = arcpy.GetParameterAsText(0)     # location of SSURGO datasets containing spatial folders
        ssaLayer = arcpy.GetParameterAsText(1)        # Test to see if I can sort the ssaLayer when using the 'Create SSURGO-Lite DB by Map' tool
        inputDB = arcpy.GetParameterAsText(2)         # existing SSURGO-SQLite database
        geogRegion = arcpy.GetParameterAsText(3)      # Geographic Region used to set output coordinate system
        surveyList = arcpy.GetParameter(4)            # list of SSURGO dataset folder names to be proccessed (e.g. 'soil_ne109')
        tileInfo = arcpy.GetParameterAsText(5)        # State abbreviation (optional as string) for use in creating SSURGO-Lite databases state-tiled. Or tuple as (tilename, description)
        bDiet = arcpy.GetParameter(6)                 # Do not import the 6 deprecated cointerp columns
        bArcPy = arcpy.GetParameter(7)                # Use arcpy.Append command to import spatial data. Default = False.

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

        if os.path.isfile(ssaLayer):
            # Sort_management (in_dataset, out_dataset, sort_field, {spatial_sort_method})
            if len(surveyList) > 0:
                areasymbolList = SortSurveyAreaLayer(ssaLayer, surveyList)

        else:
            areasymbolList = list()

        bGood = main(inputFolder, surveyList, geogRegion, tileInfo, False, inputDB, areasymbolList, bDiet)

        PrintMsg(".\tProcessing complete", 0)
        PrintMsg(".", 0)


except MyError as e:
    PrintMsg(str(e), 2)

except:
    PrintMsg(".\tOops. Got an error in the Main", 0)
    time.sleep(1)
    errorMsg(sys.exc_info())

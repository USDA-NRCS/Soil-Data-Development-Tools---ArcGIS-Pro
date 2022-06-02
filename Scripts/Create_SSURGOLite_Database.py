#-------------------------------------------------------------------------------
# Name:        Create_SSURGOLite_Database.py
# Purpose:     #  Uses pre-existing SQL to create tables, etc. These are stored in the
#              'Queries' folder.
#              Requires sqlite3 library and proper spatialite extension to create a new
#              Template database for SSURGO 3.x.

#
#              Currently does not populate the spatial metadata tables. Is this an ESRI DLL problem?
#              Need to add creation of spatial views.
#              Need to add creation of spatial indexes. This one is critical.
#
# Author:      Steve.Peaslee
#
# Created:     11/06/2021
#
#-------------------------------------------------------------------------------
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
        #sys.tracebacklimit = 1

        # excInfo object is a tuple that should contain 3 values
        # 0: type gets the type of the exception being handled (a subclass of BaseException)
        # 1: value gets the exception instance (an instance of the exception type)
        # 2: traceback gets a traceback object which encapsulates the call stack at the point where the exception originally occurred

        if not excInfo is None:
            #PrintMsg(".\texcInfo is not null and contains " + str(len(excInfo)) + " items", 1)
            #PrintMsg("excInfo is of type: " + str(type(excInfo)), 1)

            exc_type, exc_value, exc_tb = excInfo

            if exc_tb is None:
                PrintMsg(".\tNo traceback info available for this error", 1)
                PrintMsg(".\tNo traceback info available for this error: " + str(exc_type) + " - " + str(exc_value), 1)
                return

            else:
                #PrintMsg(".\tError type and value: " + str(exc_type) + "; " + str(exc_value), 1)
                #PrintMsg(".\tTraceback object: " + str(exc_tb), 2)
                formatted_lines = traceback.format_exc().splitlines()

                msg = formatted_lines[3]
                PrintMsg("Error Type: " + msg, 2)
                msg = formatted_lines[2]
                PrintMsg("Code: " + msg, 2)
                msg = formatted_lines[1]
                PrintMsg("Location: " + msg, 2)


        else:
            PrintMsg("sys.exc_info was null", 2)

        return

    except:
        PrintMsg(".\tUnhandled error in errorMsg function", 2)
        return

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
        #arcpy.SetProgressorLabel("Compacting new database...")
        PrintMsg(".", 0)
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
def GetSQL(sqlFolder, fileName):
    # Read all of the Create Table SQL from this file and save to a list
    try:
        sqlList = list()
        sqlFile = os.path.join(sqlFolder, fileName)


        if os.path.isfile(sqlFile):
            # Found input file....
            fh = open(sqlFile)
            queryString = ""
            rows = fh.readlines()

            for row in rows:
                if not row.startswith("--"):
                    queryString += row

                    if row.strip().endswith(";"):
                        sqlList.append(queryString)
                        queryString = ""

            return sqlList

        else:
            raise MyError("Failed to find sql file: " + sqlFile)


    except MyError as e:
        PrintMsg(str(e), 2)
        return sqlList

    except sqlite3.Error as err:
        msg = 'SQLite error: %s' % (' '.join(err.args))
        PrintMsg(msg, 1)
        msg = "Exception class is: ", err.__class__
        PrintMsg(msg, 1)
        msg = 'SQLite traceback: '
        PrintMsg(msg, 1)
        exc_type, exc_value, exc_tb = sys.exc_info()
        msg = traceback.format_exception(exc_type, exc_value, exc_tb)
        PrintMsg(msg, 1)
        return False

    except:
        errorMsg(sys.exc_info())
        return sqlList

## ===================================================================================
def AddGeometry(dbConn, liteCur, extension):
    # Use sqlite3 and spatialite extension to create an empty database having
    # spatial metadata tables.
    # Query_CreateTables_CascadingDeletes_from_TemplateDB.txt

    try:

        # 1. Enable geometry column. Returns 0
        sqlGeom1 = "SELECT AddGeometryColumn('featline', 'shape', 4326, 'LINESTRING', 2);"

        liteCur.execute(sqlGeom1)

        row = liteCur.fetchone()
        msg = "AddGeometryColumn returned '" + str(row[0])

        dbConn.commit()

        # Not sure why I have to run 'RGC' command. Need to try it 'without'.
        sqlGeom2 = "SELECT RecoverGeometryColumn('featline', 'shape', 4326, 'LINESTRING', 2);"

        liteCur.execute(sqlGeom2)

        row = liteCur.fetchone()  # should return a 1
        msg = "RecoverGeometryColumn returned '" + str(row[0])

        dbConn.commit()

        # 2. Enable geometry column. Returns 0, not sure why
        sqlGeom1 = "SELECT AddGeometryColumn('featpoint', 'shape', 4326, 'POINT', 2);"

        liteCur.execute(sqlGeom1)

        row = liteCur.fetchone()
        msg = "AddGeometryColumn returned '" + str(row[0])

        dbConn.commit()

        # Not sure why I have to run 'RGC' command and why it sometimes fails on the first attempt
        sqlGeom2 = "SELECT RecoverGeometryColumn('featpoint', 'shape', 4326, 'POINT', 2);"

        liteCur.execute(sqlGeom2)

        row = liteCur.fetchone()  # should return a 1
        msg = "RecoverGeometryColumn returned '" + str(row[0])


        # 3. Enable geometry column. Returns 0, not sure why
        sqlGeom1 = "SELECT AddGeometryColumn('muline', 'shape', 4326, 'LINESTRING', 2);"

        liteCur.execute(sqlGeom1)

        row = liteCur.fetchone()
        msg = "AddGeometryColumn returned '" + str(row[0])

        dbConn.commit()

        # Not sure why I have to run 'RGC' command and why it sometimes fails on the first attempt
        sqlGeom2 = "SELECT RecoverGeometryColumn('muline', 'shape', 4326, 'LINESTRING', 2);"

        liteCur.execute(sqlGeom2)

        row = liteCur.fetchone()  # should return a 1
        msg = "RecoverGeometryColumn returned '" + str(row[0])

        dbConn.commit()


        # 4. Enable geometry column. Returns 0, not sure why
        sqlGeom1 = "SELECT AddGeometryColumn('mupoint', 'shape', 4326, 'POINT', 2);"

        liteCur.execute(sqlGeom1)

        row = liteCur.fetchone()
        msg = "AddGeometryColumn returned '" + str(row[0])

        dbConn.commit()

        # Not sure why I have to run 'RGC' command and why it sometimes fails on the first attempt
        sqlGeom2 = "SELECT RecoverGeometryColumn('mupoint', 'shape', 4326, 'POINT', 2);"

        liteCur.execute(sqlGeom2)

        row = liteCur.fetchone()  # should return a 1
        msg = "RecoverGeometryColumn returned '" + str(row[0])

        # 5. Enable geometry column. Returns 0, not sure why
        sqlGeom1 = "SELECT AddGeometryColumn('mupolygon', 'shape', 4326, 'MULTIPOLYGON', 2);"

        liteCur.execute(sqlGeom1)

        row = liteCur.fetchone()
        msg = "AddGeometryColumn returned '" + str(row[0])

        dbConn.commit()

        # Not sure why I have to run 'RGC' command and why it sometimes fails on the first attempt
        sqlGeom2 = "SELECT RecoverGeometryColumn('mupolygon', 'shape', 4326, 'MULTIPOLYGON', 2);"

        liteCur.execute(sqlGeom2)

        row = liteCur.fetchone()  # should return a 1
        msg = "RecoverGeometryColumn returned '" + str(row[0])

        dbConn.commit()

        # 6. Enable geometry column. Returns 0, not sure why
        sqlGeom1 = "SELECT AddGeometryColumn('sapolygon', 'shape', 4326, 'MULTIPOLYGON', 2);"

        liteCur.execute(sqlGeom1)

        row = liteCur.fetchone()
        msg = "AddGeometryColumn returned '" + str(row[0])

        dbConn.commit()

        # Not sure why I have to run 'RGC' command and why it sometimes fails on the first attempt
        sqlGeom2 = "SELECT RecoverGeometryColumn('sapolygon', 'shape', 4326, 'MULTIPOLYGON', 2);"

        liteCur.execute(sqlGeom2)

        row = liteCur.fetchone()  # should return a 1
        msg = "RecoverGeometryColumn returned '" + str(row[0])

        dbConn.commit()

        # Add spatial indexes
        PrintMsg(".\tAdding spatial indexes:")
        tableList = ["featline", "featpoint", "muline", "mupoint", "mupolygon", "sapolygon"]

        for geomTbl in tableList:
            PrintMsg(".\t\t" + geomTbl, 0)
            tblValues = (geomTbl, 'shape')
            sqlIndex = "SELECT CreateSpatialIndex(?, ?);"
            liteCur.execute(sqlIndex, tblValues)

        PrintMsg(".\tAddGeometryColumn complete", 0)

        return True

    except MyError as e:
        PrintMsg(str(e), 2)
        return False

    except sqlite3.Error as err:
        msg = 'SQLite error: %s' % (' '.join(err.args))
        PrintMsg(msg, 1)
        msg = "Exception class is: ", err.__class__
        PrintMsg(msg, 1)
        msg = 'SQLite traceback: '
        PrintMsg(msg, 1)
        exc_type, exc_value, exc_tb = sys.exc_info()
        msg = traceback.format_exception(exc_type, exc_value, exc_tb)
        PrintMsg(msg, 1)
        return False

    except:
        errorMsg(sys.exc_info())
        return False

## ===================================================================================
def CreateTables(dbConn, liteCur, sqlList):
    # Use sqlite3 and spatialite extension to create an empty database having
    # spatial metadata tables.
    # Query_CreateTables_CascadingDeletes_from_TemplateDB.txt

    try:
        # Create attribute tables.
        # Spatial tables will also be created here, but without complete geometry

        for sqlTable in sqlList:
            liteCur.execute(sqlTable)
            row = liteCur.fetchone()

            if not row is None:
                bCreate = row[0]

                if bCreate:
                    PrintMsg(".\tCreated table", 0)

                else:
                    PrintMsg(".\tFailed to create a table using: ", 1)
                    raise MyError("Failed SQL:")

        dbConn.commit()

        return sqlList

    except MyError as e:
        PrintMsg(str(e), 2)
        return sqlList

    except sqlite3.Error as err:
        msg = 'SQLite error: %s' % (' '.join(err.args))
        PrintMsg(msg, 1)
        msg = "Exception class is: ", err.__class__
        PrintMsg(msg, 1)
        msg = 'SQLite traceback: '
        PrintMsg(msg, 1)
        exc_type, exc_value, exc_tb = sys.exc_info()
        msg = traceback.format_exception(exc_type, exc_value, exc_tb)
        PrintMsg(msg, 1)
        return sqlList

    except:
        errorMsg(sys.exc_info())
        return sqlList

## ===================================================================================
def CreateIndexes(dbConn, liteCur, sqlList):
    # Use sqlite3 to create attribute indexes
    # Using Query_CreateIndexes.txt

    try:

        for sqlTable in sqlList:
            liteCur.execute(sqlTable)
            row = liteCur.fetchone()

            if not row is None:
                bCreate = row[0]

                if bCreate:
                    PrintMsg(".\tCreated index", 0)

                else:
                    PrintMsg(".\tFailed to create index using: ", 1)
                    raise MyError("Failed SQL:")

        dbConn.commit()

        return sqlList

    except MyError as e:
        PrintMsg(str(e), 2)
        return sqlList

    except sqlite3.Error as err:
        msg = 'SQLite error: %s' % (' '.join(err.args))
        PrintMsg(msg, 1)
        msg = "Exception class is: ", err.__class__
        PrintMsg(msg, 1)
        msg = 'SQLite traceback: '
        PrintMsg(msg, 1)
        exc_type, exc_value, exc_tb = sys.exc_info()
        msg = traceback.format_exception(exc_type, exc_value, exc_tb)
        PrintMsg(msg, 1)
        return sqlList

    except:
        errorMsg(sys.exc_info())
        return sqlList

## ===================================================================================
def ImportMetadataTables(dbConn, liteCur, dbMetadata, metadataList):
    # Populate mdstat* and system tables from an existing database.
    # These are the only tables in the Template database that are pre-populated.
    # Using Query_CreateTables_CascadingDeletes_from_TemplateDB.txt

    try:
        sqlAttach = "ATTACH DATABASE '" + dbMetadata + "' AS MD;"
        #PrintMsg(".\t" + sqlAttach, 1)
        liteCur.execute(sqlAttach)
        dbConn.commit()

        for sqlImport in metadataList:
            liteCur.execute(sqlImport)
            row = liteCur.fetchone()

            if not row is None:
                bCreate = row[0]

                if bCreate:
                    PrintMsg(".\tImported metadata", 0)

                else:
                    PrintMsg(".\tFailed to create a table using: ", 1)
                    raise MyError("Failed SQL:")

        dbConn.commit()

        return True

    except MyError as e:
        PrintMsg(str(e), 2)
        return False

    except sqlite3.Error as err:
        msg = 'SQLite error: %s' % (' '.join(err.args))
        PrintMsg(msg, 1)
        msg = "Exception class is: ", err.__class__
        PrintMsg(msg, 1)
        msg = 'SQLite traceback: '
        PrintMsg(msg, 1)
        exc_type, exc_value, exc_tb = sys.exc_info()
        msg = traceback.format_exception(exc_type, exc_value, exc_tb)
        PrintMsg(msg, 1)
        return False

    except:
        errorMsg(sys.exc_info())
        return False

## ===================================================================================
def CreateNewDatabase(dbConn, liteCur, extension, dbMetadata):
    # Use sqlite3 and spatialite extension to create an empty database having
    # spatial metadata tables.
    # Query_CreateTables_CascadingDeletes_from_TemplateDB.txt

    try:
        sqlExtension = "SELECT load_extension('" + extension + "');"

        # Creating new database...
        msg = "Creating database connection"
        PrintMsg(msg, 0)

        # load spatialite extension needed for geometry functions
        dbConn.enable_load_extension(True)

        try:
            msg = "Adding extension '" + extension + "'"
            PrintMsg(msg, 0)
            dbConn.execute(sqlExtension)

        except:
            msg = "Failed to load spatialite extension"
            raise MyError(msg)

        # Create spatial metadata tables (this actually worked using ESRI DLL, but creates a LOT of tables!)
        # Need to compare the system tables created by this DLL to other options.
        # msg = "NOT Creating spatial metadata tables!"
        # PrintMsg(msg, 0)
        sqlMetadata = "SELECT InitSpatialMetaData();"
        liteCur.execute(sqlMetadata)
        row = liteCur.fetchone()

        if row is None or row[0] == 0:
            msg = "Failed to create spatial metadata tables for " + dbName
            raise MyError(msg)

        # Read Query tables to get SQL for creating tables and indexes

        # Create lists of SQL commands needed to create all tables and indexes
        sqlFile = "Query_CreateTables_CascadingDeletes_from_TemplateDB.txt"
        PrintMsg(".\tReading '" + sqlFile + "' file...", 0)
        sqlList = GetSQL(sqlFolder, sqlFile)

        if len(sqlList) == 0:
            raise MyError("Failed to get 'Create Table' SQL")

        # Create list of SQLs needed to populate mdstat* tables
        sqlFile = "Query_ImportMetaData_AttachedDB.txt"
        PrintMsg(".\tReading '" + sqlFile + "' file...", 0)
        metadataList = GetSQL(sqlFolder, sqlFile)

        if len(metadataList) == 0:
            raise MyError("Failed to get 'mdstat tables' SQL")

        # Create list of SQLs needed to create attribute indexes
        sqlFile = "Query_CreateIndexes.txt"
        PrintMsg(".\tReading '" + sqlFile + "' file...", 0)
        sqlIndexes = GetSQL(sqlFolder, sqlFile)

        if len(sqlIndexes) == 0:
            raise MyError("Failed to get 'mdstat tables' SQL")

        # End of SQL

        bTables = CreateTables(dbConn, liteCur, sqlList)

        PrintMsg(".\tTurned off AddGeometry. Try using it manually in spatialite commandline", 0)
        bGeometry = True

##        if bTables:
##            bGeometry = AddGeometry(dbConn, liteCur, extension)
##
##        else:
##            raise MyError("")

        if bGeometry:
            bIndexes = CreateIndexes(dbConn, liteCur, sqlIndexes)

        if bIndexes:
            bMetaData = ImportMetadataTables(dbConn, liteCur, dbMetadata, metadataList)

        dbConn.close()
        del dbConn

        return True

    except MyError as e:
        PrintMsg(str(e), 2)
        return sqlList

    except sqlite3.Error as err:
        msg = 'SQLite error: %s' % (' '.join(err.args))
        PrintMsg(msg, 1)
        msg = "Exception class is: ", err.__class__
        PrintMsg(msg, 1)
        msg = 'SQLite traceback: '
        PrintMsg(msg, 1)
        exc_type, exc_value, exc_tb = sys.exc_info()
        msg = traceback.format_exception(exc_type, exc_value, exc_tb)
        PrintMsg(msg, 2)
        return False

    except:
        errorMsg(sys.exc_info())
        return False

## ===================================================================================
## MAIN

import arcpy, os, sys, locale, traceback, sqlite3, shutil

try:
    outputFolder = arcpy.GetParameterAsText(0)
    dbName = arcpy.GetParameterAsText(1)
    dbMetadata = arcpy.GetParameterAsText(2)

    if outputFolder == "":
        raise MyError("")

    PrintMsg(".\tArguments: " + str(outputFolder) + "; " + str(dbName), 0)

    # Get paths for scripts, spatialite extensions, SQL queries
    #
    scriptPath = __file__
    scriptFolder = os.path.dirname(scriptPath)  # Scripts subfolder
    baseFolder = os.path.dirname(scriptFolder)

    # location for spatialite binaries
    extFolder = os.path.join(baseFolder, "Extensions")

    PrintMsg(".\tExtensions Folder: " + extFolder, 0)

    # location for queries used to build databases, import SSURGO data and query database
    sqlFolder = os.path.join(baseFolder, "Queries")

    newPaths = list()
    newPaths.append(extFolder)  # add Extensions subfolder to front of system path

    if len(newPaths) > 0:
        myPath = os.environ['PATH']
        pathList = myPath.split(";")
        addList = list()

        for p in newPaths:
            if not p in pathList:
                PrintMsg(".\tAdding path: " + p + " to environment", 1)
                os.environ['PATH'] += ";" + p

    # Full path and filename for output database
    db = os.path.join(outputFolder, dbName)

    # Try something once. Use an empty spatialite database and copy it to the
    # db.
##    tmpPath = r"D:\Geodata\2021\SQLite_Tests\ApplicationData\TemplateDatabases"
##    tmpDB = "emptydb_spatialitegui_50.sqlite"
##    templateDB = os.path.join(tmpPath, tmpDB)
##    dbCopy = os.path.join(os.path.dirname(db), os.path.basename(templateDB))
##    PrintMsg(".\tCopying empty spatialite database (" + templateDB + ") to " + dbCopy, 0)
##    shutil.copy2(templateDB, dbCopy)
##    time.sleep(5)
##    PrintMsg(".\tRenaming " + dbCopy + " to " + db, 0)
##    os.rename(dbCopy, db)


    PrintMsg(".\tNew output database: " + db , 0)

    # Open database connection and cursor
    dbConn = sqlite3.connect(db)

    liteCur = dbConn.cursor()

    # Using mod_spatialite-5.0.1 64-bit binaries
    # http://www.gaia-gis.it/gaia-sins/windows-bin-amd64-prev/
    # I was originally using an ArcGIS Desktop DLL (spatialite400x.dll).
    # Need to look at options that can be packaged with my application.
    #
    extension = 'spatialite400.dll'  # ESRI DLL worked
    #extension = "mod_spatialite"     # Trying Spatialite official distribution of loadable modules
    #extension = os.path.join(extFolder, "mod_spatialite.dll" )

    # Create new database with required spatial metadata tables
    bDatabase = CreateNewDatabase(dbConn, liteCur, extension, dbMetadata)

    if not bDatabase:
        raise MyError(".\tMain reports failure to create new database")

    else:
        PrintMsg(".\tSuccessfully created new database: " + db, 0)

    dbConn.close()

    bCompact = CompactDatabase(db)

    PrintMsg(".\tProcessing complete...", 0)

except MyError as e:
    PrintMsg(str(e), 2)

except:
    errorMsg(sys.exc_info())


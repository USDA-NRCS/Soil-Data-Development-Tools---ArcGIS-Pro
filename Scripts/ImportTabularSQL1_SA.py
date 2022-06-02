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

        else:
            return 'MyError has been raised'

## ===================================================================================
def errorMsg2(excInfo):
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
                    PrintMsg("Error '" + exc_value + "' in " + os.path.basename(filename) + \
                         " at line number " + str(linenum) + ":" + "\n" + source, 2)

            #PrintMsg(70 * "=", 2)
        

        else:
            PrintMsg("excInfo is null", 1)
            
        return

    except:
        msg = "Exception raised in error-handling function (errorMsg)"
        sys.exit(msg)

## ===================================================================================
def errorMsg(junk):
    # Capture system error from traceback and then exit
    #
    try:
        #sys.tracebacklimit = 1
        excInfo = sys.exc_info()
        # PrintMsg("Got excInfo object which is a tuple that should contain 3 values", 0)
        # 0: type gets the type of the exception being handled (a subclass of BaseException)
        # 1: value gets the exception instance (an instance of the exception type)
        # 2: traceback gets a traceback object which encapsulates the call stack at the point where the exception originally occurred

        if not excInfo is None:
            if len(excInfo) >= 3:
                # type, value, traceback
                errType = str(excInfo[0])
                errValue = excInfo[1]
                errTB = excInfo[2]
                msgType, msgValue, msgTB = traceback.format_exception(errType, errValue, errTB, limit=1, chain=True)

                if not errTB is None:
                    try:
                        msgType, msgValue, msgTB = traceback.format_exception(errType, errValue, errTB, limit=1, chain=True)
                        #msgValue = msgValue.replace("\n", " ").replace(",", "\n")  # format_exception has some issues...

                    except:
                        msgType, msgValue, msgTB = ("NA", "NA", "NA")

                    if msgTB.strip() != "SystemExit: 0":
                        # Skip traceback if this was raised as a custom error
                        #theMsg = str(msgTB) + ":: " + str(msgType) + ":: " + str(msgValue)
                        msgList = msgValue.replace("\n", " ").split(", ")
                        errMsg = msgList[0]
                        errScript = msgList[1]
                        errLine = msgList[2]
                        errModule = msgList[3]
                        msgValue = errMsg + "\n" + errModule + "\t" + errLine + "\n" + errScript

                        PrintMsg(".", 0)
                        PrintMsg(msgTB, 2)
                        PrintMsg(msgValue, 2)
                        del tbInfo

                    PrintMsg("ErrorMsg1 ended up with: " + msgTB, 0)

        
            del excInfo

        else:
            PrintMsg("\nexcInfo is null", 0)
            
    except:
        #PrintMsg("Unhandled error in errorMsg1 method", 2)
        sys.exit(0)

## ===================================================================================
def PrintMsg(msg, severity=0):
    # Adds tool message to the geoprocessor
    #
    #Split the message on \n first, so that if it's multiple lines, a GPMessage will be added for each line
    try:
        for string in msg.split('\n'):
            #Add a geoprocessing message (in case this is run as a tool)
            if severity == 0:
                #arcpy.AddMessage(string)
                print(string)
                #pass

            elif severity == 1:
                #arcpy.AddWarning(string)
                print("Warning", string)
                #pass

            elif severity == 2:
                #arcpy.AddError(" \n" + string)
                print("Error", string)
                #pass

    except:
        #errorMsg(sys.exc_info())
        print("Error in PrintMsg function")

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
        errorMsg()
        return ""

## ===============================================================================================================
def SetCacheSize(conn, liteCur):
    # Restore previous attribute indexes

    try:
        PrintMsg(".", 0)
        PrintMsg("Setting cache size for indexing performance...", 0)

        #queryCacheSize = "PRAGMA main.cache_size = -200000;"
        queryCacheSize = "PRAGMA main.cache_size = 500;"
        liteCur.execute(queryCacheSize)
        conn.commit()

        return True
    
    except sqlite3.IntegrityError as err:
        PrintMsg(err, 2)
        result = False

    except sqlite3.OperationalError as e:
        PrintMsg(str(e), 2)
        result = False

    except sqlite3.Error as e:
        PrintMsg(str(e), 2)
        result = False
        
    except MyError as e:
        # Example: raise MyError("This is an error message")
        PrintMsg(str(e), 2)
        return False

    except:
        errorMsg(sys.exc_info())
        return False

## ===============================================================================================================
def DropIndexes(conn, liteCur):
    # Drop existing attribute table indexes from the database

    try:

        # Delete all attribute indexes for faster database creation
        PrintMsg("Dropping attribute indexes from new database...", 0)

        vals = ('index', 'sqlite%', 'idx_%')
        queryIndexes = "SELECT name, sql FROM sqlite_master WHERE type = 'index' AND NOT name LIKE 'sqlite%' AND NOT name LIKE 'idx_%';"
        liteCur.execute(queryIndexes)
        indexes = liteCur.fetchall()
        PrintMsg(queryIndexes, 0)

        if len(indexes) == 0:
            PrintMsg(".\tNo indexes found in template database", 1)
            return []

        createSQLs = list()
        
        for indx in indexes:
            createSQLs.append(indx[1])
            dropSQL = "DROP INDEX IF EXISTS " + indx[0] + ";"
            #PrintMsg(dropSQL, 0)
            liteCur.execute(dropSQL)
            conn.commit()

        # Confirm that the indexes were actually dropped. Probably don't need this in production.
        liteCur.execute(queryIndexes)
        post_indexes = liteCur.fetchall()

        if len(post_indexes) == 0:
            PrintMsg(".\tAll indexes successfully dropped", 0)

        return createSQLs

    except sqlite3.IntegrityError as err:
        PrintMsg(err, 2)
        return []

    except sqlite3.OperationalError as e:
        PrintMsg(str(e), 2)
        return []

    except sqlite3.Error as e:
        PrintMsg(str(e), 2)
        return []

    except MyError as e:
        # Example: raise MyError("This is an error message")
        PrintMsg(str(e), 2)
        return []

    except:
        errorMsg(sys.exc_info())
        return []

## ===============================================================================================================
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
        #arcpy.SetProgressorLabel("Compacting new database...")
        PrintMsg(".", 0)
        PrintMsg("Compacting new database using " + tmpFolder + "...")

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
        PrintMsg(".\tFinished compacting database...")

        return True

    except sqlite3.IntegrityError as err:
        PrintMsg(err, 2)
        result = False

    except sqlite3.OperationalError as e:
        PrintMsg(str(e), 2)
        result = False

    except sqlite3.Error as e:
        PrintMsg(str(e), 2)
        return []
        
    except MyError as e:
        PrintMsg(str(e), 2)
        return False

    except:
        errorMsg(sys.exc_info())
        return False

## ===============================================================================================================
def RestoreIndexes(newDB, createSQLs):
    # Restore previous attribute indexes

    try:
        # Restore original attribute indexes
        result = False
        PrintMsg(".", 0)
        PrintMsg("Restoring previously existing attribute indexes (" + str(len(createSQLs)) + ") for the new database...", 0)
        restoreSQL = list()
        conn = sqlite3.connect(newDB)
        liteCur = conn.cursor()
        #time.sleep(2)
            
        for createSQL in createSQLs:
            newSQL = createSQL.replace("CREATE INDEX", "CREATE INDEX IF NOT EXISTS")
            #PrintMsg(newSQL, 0)
            liteCur.execute(newSQL)

        conn.commit()
        PrintMsg("\tFinished restoring indexes", 0)
        
        result = True
    
    except sqlite3.IntegrityError as err:
        PrintMsg(err, 2)
        result = False

    except sqlite3.OperationalError as e:
        PrintMsg(str(e), 2)
        result = False

    except sqlite3.Error as e:
        PrintMsg(str(e), 2)
        result = False
        
    except MyError as e:
        # Example: raise MyError("This is an error message")
        PrintMsg(str(e), 2)
        result = False

    except:
        errorMsg(sys.exc_info())
        result = False

    finally:
        PrintMsg("\tClosing database in RestoreIndexes", 0)
        conn.close
        del conn
        del liteCur
        return result
        
## ===============================================================================================================
def CreateNewIndexes(newDB):
    # Create attribute indexes using metadata from mdstat* tables
    #
    # Big question. Does this work for spatialite database?
    try:
        result = False
        PrintMsg(".\tCreating new attribute indexes using metadata tables...", 0)

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

        conn = sqlite3.connect(newDB)
        liteCur = conn.cursor()
        
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
                    #PrintMsg(".\tIndex for " + tblName + " on " + ", ".join(colNames), 0)
                    PrintMsg(sCreateIndex, 1)
                    liteCur.execute(sCreateIndex)
                    conn.commit

                except:
                    PrintMsg(".\tError while creating an attribute index", 1)
                    break

            #arcpy.SetProgressorLabel("Finished with attribute indexes")

        else:
            raise MyError("Failed to get information needed for indexes")

        time.sleep(1)  # Sometimes the indexes aren't being created. Don't understand this.
        arcpy.SetProgressorLabel("Creation of attribute indexes from metadata is complete")

        # End of attribute indexes
        # *********************************************************************************************************
        # *********************************************************************************************************
        result = True

    except sqlite3.IntegrityError as err:
        PrintMsg(err, 2)
        result = False

    except sqlite3.OperationalError as e:
        PrintMsg(str(e), 2)
        result = False

    except sqlite3.Error as e:
        PrintMsg(str(e), 2)
        result = False
 
    except MyError as e:
        # Example: raise MyError("This is an error message")
        PrintMsg(str(e), 2)
        result = False

    except:
        errorMsg(sys.exc_info())
        result = False

    finally:
        PrintMsg("\tClosing database in CreateNewIndexes", 0)
        conn.close
        del conn
        del liteCur
        return result
    
## ===================================================================================
def ImportTabularSQL1(newDB, pathList, dbVersion, conn, liteCur):

    # Use csv reader method of importing text files into geodatabase for those
    # that do not have a populated SSURGO database
    #
    # Using unique constraint to prevent duplicate records in sdv* tables. Dupes will be skipped.
    # For any of the other data tables, a unique contraint violation will throw an error and stop the import.
    #
    # The cointerp table is handled a little differently. It can handle either the original 19 column version or a 13 column version.
    #
    try:
        result = False

        if os.path.isfile(newDB):
            PrintMsg("Using database: " + newDB, 0)

        else:
            raise MyError("Database does not exist: " + newDB)

        csv.field_size_limit(min(sys.maxsize, 2147483646))
        encoder = "UTF-8"
        #encoder = "ISO-8859-1"
        #encoder = "CP1252"
        
        PrintMsg(".", 0)
        PrintMsg(".\tImporting tabular data using function 'ImportTabularSQL1'...", 0)

        # get a checklist of existing tables in the database
        PrintMsg("Preparing to get list of existing tables", 0)
        tableList = GetTableList(conn, liteCur)

        if len(tableList) < 50:
            raise MyError("Missing one or more tables in output database: " + newDB)

        else:
            PrintMsg("\nOutput database has " + str(len(tableList)) + " tables", 0)

        #PrintMsg("\tPreparing to get list of field infos", 0)
        fldInfos = GetFieldInfo("mdstattabs", liteCur)

        #PrintMsg("\nTarget table (mdstattabls) has " + str(len(fldInfos)) + " field infos", 0)
        
        fldNames = list()

        for fld in fldInfos:
            fldName, fldType = fld
            fldNames.append(fldName.lower())

        if "daglevel" in fldNames:
            # Get ordered list of tables to import
            PrintMsg(".\tGetting DAG Levels to define tabular import sequence", 0)
            importOrder = GetImportOrder(liteCur)
            txtFiles = [f[0] for f in importOrder]

        else:
            PrintMsg("Missing DAG Level information in mdstattabs table", 2)
            
        # Create a dictionary. Keys are tabular-textfile names with table information
        PrintMsg(".\tGetting TableInfo", 0)
        tblInfo = GetTableInfoSQL(liteCur)

        if len(tblInfo) == 0:
            PrintMsg(".\tTable Info is empty", 0)
            raise MyError("Table Info is empty")

        # Need to import text files in a specific order or the MS Access database will
        # return an error due to table relationships and key violations
        #arcpy.SetProgressor("step", "Importing tabular data...", 0, len(txtFiles))

        start = time.time()
        PrintMsg(".\tBeginning import process...", 0)
        #PrintMsg(".\tImport order: " + str(txtFiles), 0)

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
                PrintMsg(err, 2)
                raise MyError(err)

            fldInfos = GetFieldInfo(tbl, liteCur)
            fldNames = list()
            fldLengths = list()

            for fld in fldInfos:
                fldName, fldType = fld
                fldNames.append(fldName)

            #PrintMsg(".\tFields for " + tbl + ": " + ",  ".join(fldNames), 0)

            if len(fldNames) == 0:
                err = "Failed to get field names for " + tbl
                raise MyError(err)

            src = len(fldNames) * ['?']  # this will be used below in executemany

            PrintMsg(".\tProcessing " + tbl + " table with " + str(len(fldNames)) + " fields", 0)
            #arcpy.SetProgressorLabel("Importing tabular data for:  " + tbl)

            iCntr = 0
            
            # Begin iterating through the each of the input SSURGO datasets
            for tabularFolder in pathList:

                iCntr += 1
                #PrintMsg(".\tImporting tabular data from " + tabularFolder + "...", 0)

                # parse Areasymbol from parent folder. If the geospatial naming convention isn't followed,
                # then this will not work.
                soilsFolder = os.path.dirname(tabularFolder)
                spatialFolder = os.path.join(soilsFolder, "spatial")
                fnAreasymbol = soilsFolder[(soilsFolder.rfind("_") + 1):].upper()
                #PrintMsg(".\tParsed areasymbol: " + fnAreasymbol, 0)

                # move to tabular folder. Not sure if this is necessary as long as I use full paths
                # env.workspace = tabularFolder

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

                curValues = list()

                if not tbl in ['cointerp', 'sdvfolderattribute', 'sdvattribute', 'sdvfolder', 'sdvalgorithm']:
                    # Import all tables, except for cointerp and sdv* tables.
                    # The sdv* tables will be imported one record at a time instead of in a batch.
                    #
                    #time.sleep(0.05)  # Occasional write errors

                    #iRows = 1  # input textfile line number

                    if os.path.isfile(txtPath):

                        try:
                            # Use csv reader to read each line in the text file. Save the values to a list of lists.

                            with open(txtPath, 'r', encoding=encoder) as tabData:
                                rows = csv.reader(tabData, delimiter='|', quotechar='"')

                                for row in rows:
                                    curValues.append(tuple([val.strip() if val else None for val in row]))
                                    #iRows += 1

                            insertQuery = "INSERT INTO " + tbl + " VALUES (" + ",".join(src) + ");"
                            liteCur.executemany(insertQuery, curValues)
                            #conn.commit()

                        except:
                            #PrintMsg(" \n" + str(row), 1)
                            errorMsg(sys.exc_info())
                            #err = "Error writing line " + Number_Format(iRows, 0, True) + " from " + txtPath
                            err = "Error writing to " + tbl + " from " + txtPath
                            raise MyError(err)

                    else:
                        err = "Missing tabular data file (" + txtPath + ")"
                        raise MyError(err)

                elif tbl == 'cointerp':
                    # Should only enter this if cointerp is excluded above
                    # SSURGO originally specified 19 columns for the cointerp table
                    # interpll is the name of the first deprecated column
                    #
                    if os.path.isfile(txtPath):

                        try:
                            with open(txtPath, 'r', encoding=encoder) as tabData:
                                rows = csv.reader(tabData, delimiter='|', quotechar='"')

                                if len(fldNames) == 13:
                                    #PrintMsg(".\tImporting cointerp with 13 columns", 0)
                                    # 'reduced' cointerp table with 13 columns
                                    for row in rows:
                                        # remove deprecated cointerp data from row
                                        newrow = row[0:7] + row[11:13] + row[15:]  # seems slow?
                                        curValues.append(tuple([val.strip() if val else None for val in newrow]))

                                else:
                                    # standard cointerp table with 19 columns
                                    #PrintMsg(".\tImporting cointerp with " + len(fldNames) + " columns", 0)
                                    for row in rows:
                                        curValues.append(tuple([val.strip() if val else None for val in row]))

                            if len(curValues) > 0:
                                insertQuery = "INSERT INTO " + tbl + " " + str(tuple(fldNames)) +  " VALUES (" + ",".join(src) + ");"
                                liteCur.executemany(insertQuery, curValues)
                                #conn.commit()

                        except:
                            #PrintMsg(" \n" + str(row), 1)
                            errorMsg(sys.exc_info())
                            #err = "Error writing line " + Number_Format(iRows, 0, True) + " from " + txtPath
                            err = "Error writing to " + tbl + " from " + txtPath
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

                            with open(txtPath, 'r', encoding=encoder) as tabData:

                                # catching different encoding for NASIS export (esp. sdvattribute table) which as of 2020 uses ISO-8859-1
                                rows = csv.reader(tabData, delimiter='|', quotechar='"')

                                for row in rows:
                                    try:
                                        newRow = tuple([val.strip() if val else None for val in row])
                                        liteCur.execute(insertQuery, newRow)
                                        conn.commit()
                                        iRows += 1

                                    except sqlite3.IntegrityError:
                                        # Need to see if I can more narrowly define the error types I want to pass or throw an error
                                        # These should be duplicate records
                                        pass

                                    except:
                                        err = "Error writing line " + Number_Format(iRows, 0, True) + " from " + txtPath
                                        errorMsg(err)
                                        #errorMsg(sys.exc_info())

                        else:
                            err = "Missing tabular data file (" + txtPath + ")"
                            raise MyError(err)

                else:
                    PrintMsg(".\tNo method for " + tbl + " table", 1)
                    
                # End of table iteration
            #arcpy.SetProgressorPosition()
            conn.commit()

        PrintMsg(".\tTable iteration process complete", 0)
        PrintMsg(".\t", 0)
        theMsg = ".\tTotal processing time for tabular import: " + elapsedTime(start) + " \n "
        PrintMsg(theMsg, 0)
        PrintMsg(".", 0)

        result = True

    except sqlite3.IntegrityError as e:
        PrintMsg(e, 2)
        result = False

    except sqlite3.OperationalError as e:
        PrintMsg(str(e), 2)
        result = False

    except sqlite3.Error as e:
        PrintMsg(str(e), 2)
        result = False
    
    except MyError as e:
        # Example: raise MyError("This is an error message")
        PrintMsg(str(e), 2)
        result = False

    except:
        errorMsg("x")
        result = False

    finally:
        try:
            conn.close()
            del conn
            del newDB

        except:
            pass

        return result

## ===================================================================================
def GetTableList(conn, liteCur):
    # Get list of tables from the current database connection

    try:
        tableList = list()

        queryTableNames = "SELECT name FROM sqlite_master WHERE type = 'table' AND NOT name LIKE 'idx_%';"
        PrintMsg("Using query to get table info:\t" + queryTableNames, 0)
        liteCur.execute(queryTableNames)
        rows = liteCur.fetchall()

        tableList = [row[0] for row in rows]
        #PrintMsg("tblNames: " + str(tableList), 0)
        
        if len(tableList) == 0:
            raise MyError("Failed to get required sqlite_master. Is database empty?")

        return tableList

    except sqlite3.IntegrityError as e:
        PrintMsg(e, 2)
        return tableList

    except sqlite3.OperationalError as e:
        PrintMsg(str(e), 2)
        return tablelist

    except sqlite3.Error as e:
        PrintMsg(str(e), 2)
        return tableList
        
    except MyError as e:
        # Example: raise MyError("This is an error message")
        PrintMsg(str(e), 2)
        return tableList

    except:
        errorMsg(sys.exc_info())
        return tableList

## ===================================================================================
def GetTableInfoSQL(liteCur):
    # Retrieve physical and alias names from MDSTATTABS table and assigns them to a blank dictionary.
    # Stores tabular-text filename (key) tablename, table aliase (value) in a Python dictionary i.e. {chasshto:'Horizon AASHTO,chaashto'}

    try:
        tblInfo = dict()

        # Query mdstattabs table containing information for other SSURGO tables
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
    
    except sqlite3.IntegrityError as err:
        PrintMsg(err, 2)
        return tblInfo

    except sqlite3.OperationalError as e:
        PrintMsg(str(e), 2)
        return tblInfo

    except sqlite3.Error as e:
        PrintMsg(str(e), 2)
        return tblInfo
        
    except MyError as e:
        # Example: raise MyError("This is an error message")
        PrintMsg(str(e), 2)
        return tblInfo

    except:
        errorMsg(sys.exc_info())
        return tblInfo

## ===================================================================================
def GetFieldInfo(tblName, liteCur):
    # Get list of (fieldname, type) for this table
    try:
        fldInfo = list()
        
        fldNames = list()

        queryFieldNames = "SELECT name, type FROM PRAGMA_TABLE_INFO('" + tblName + "');"
        liteCur.execute(queryFieldNames)
        rows = liteCur.fetchall()
        fldInfo = [row for row in rows]

        return fldInfo

    except sqlite3.IntegrityError as err:
        PrintMsg(err, 2)
        return fldInfo

    except sqlite3.OperationalError as e:
        PrintMsg(str(e), 2)
        return fldInfo

    except sqlite3.Error as e:
        PrintMsg(str(e), 2)
        return fldInfo
    
    except:
        errorMsg(sys.exc_info())
        return []

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
    
    except sqlite3.IntegrityError as err:
        PrintMsg(err, 2)
        return importList

    except sqlite3.OperationalError as e:
        PrintMsg(str(e), 2)
        return importList

    except sqlite3.Error as e:
        PrintMsg(str(e), 2)
        return importList

    except MyError as e:
        # Example: raise MyError("This is an error message")
        PrintMsg(str(e), 2)
        return importList

    except:
        errorMsg(sys.exc_info())
        return importList

## ====================================================================================
# Main
# Import system modules
import sys, string, os, traceback, locale, time, datetime, csv, shutil, math, click #, argparse
import sqlite3
#from sqlite3 import Error

# number = click.prompt("Enter the number", type=float, default=0.025)
# import argparse https://docs.python.org/3.3/library/argparse.html

PrintMsg("Done importing libraries", 0)

try:

    PrintMsg("Setting function arguments", 0)

    # set template database
    #tmpDB = "D:\\Geodata\\2021\\SQLite_Tests\\ApplicationData\\TemplateDatabases\\template_spatialite5.sqlite"
    #tmpDB = "D:\\Geodata\\2021\\SQLite_Tests\\ApplicationData\\TemplateDatabases\\template_albers_textkeys2.sqlite"
    tmpDB = "D:\\Geodata\\2021\\SQLite_Tests\\ApplicationData\\TemplateDatabases\\template_albers_textkeys_cinterp19.sqlite"
    #tmpDB = "D:\\Geodata\\2021\\SQLite_Tests\\Oregon\\oregon_both_4326.sqlite"
    templateDB = click.prompt("\nEnter existing template database \n", type=string, default=tmpDB)

    # set new output database
    #newDB = click.prompt("\nEnter output database \n", type=string, default="D:\\Geodata\\2021\\SQLite_Tests\\oregon\\or631_tabular09.sqlite")
    newDB = click.prompt("\nEnter output database \n", type=string, default="D:\\Geodata\\2021\\SQLite_Tests\\Oregon\\or631_tabonlytextkeys02.sqlite")

    # set input tabular folders (containing SSURGO .txt files)
    pList1 = ['D:\\Geodata\\2021\\SSURGO_Downloads\\soil_or631\\tabular', \
             'D:\\Geodata\\2021\\SSURGO_Downloads\\soil_or625\\tabular', \
             'D:\\Geodata\\2021\\SSURGO_Downloads\\soil_or604\\tabular']

    pList2 = ['D:\\Geodata\\2021\\SSURGO_Downloads\\soil_ne075\\tabular',\
             'D:\\Geodata\\2021\\SSURGO_Downloads\\soil_ne171\\tabular']

    pList3 = ['D:\\Geodata\\2021\\SSURGO_Downloads\\soil_or631\\tabular', \
             'D:\\Geodata\\2021\\SSURGO_Downloads\\soil_or625\\tabular', \
             'D:\\Geodata\\2021\\SSURGO_Downloads\\soil_or604\\tabular', \
             'D:\\Geodata\\2021\\SSURGO_Downloads\\soil_or670\\tabular', \
             'D:\\Geodata\\2021\\SSURGO_Downloads\\soil_or607\\tabular']

    pList = ['D:\\Geodata\\2021\\SSURGO_Downloads\\soil_or631\\tabular']
    
    pathList = list()

    i = 0
    
    while True:
        try:
            defVal = pList[i]

        except:
            defVal = ""
            
        p = click.prompt("\nEnter one of the 'tabular' paths to be imported \n", type=string, default=defVal)
        i += 1
        
        if p:
            pathList.append(p)

        else:
            break

    dbVersion = 2

    # copy template database to new output database

    if os.path.isfile(newDB):
        PrintMsg("Using existing database: " + newDB, 0)

    else:
        PrintMsg("Creating new database: " + newDB, 0)
        shutil.copy2(templateDB, newDB)
        time.sleep(2)

    # open connection to new output database
    PrintMsg("Opening database connection to '" + newDB + "'", 0)
    conn = sqlite3.connect(newDB)

    # setting database to allow faster imports
    PrintMsg(".\tTurning ON foreign key constraints and setting other database modes...", 0)
    conn.execute("PRAGMA foreign_keys = ON;") # PRAGMA foreign_key_check(table-name);
    conn.execute("PRAGMA journal_mode = OFF;")
    conn.execute("PRAGMA synchronous = OFF;")
    conn.execute("PRAGMA locking_mode = EXCLUSIVE;")
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.commit()

    PrintMsg("Creating database cursor", 0)
    liteCur = conn.cursor()

    bSet = SetCacheSize(conn, liteCur)

    # Drop existing attribute indexes from new database
    createSQLs = DropIndexes(conn, liteCur)

    PrintMsg("Ready to import tabular...", 0)

    bImported = ImportTabularSQL1(newDB, pathList, dbVersion, conn, liteCur)

    if bImported:
        # Possible problems recreating indexes? Try closing the database and re-opening.
        PrintMsg("Closing database connection", 0)
        conn.close()
        del liteCur
        del conn
        PrintMsg(".", 0)
        PrintMsg("All tabular data have been imported...", 0)

        if len(createSQLs) > 0:
            start = time.time()
            bIndexed = RestoreIndexes(newDB, createSQLs)

            if not bIndexed:
                PrintMsg(".\tFailed to restore attribute indexes", 1)

            else:
                theMsg = ".\tTotal processing time for re-indexing: " + elapsedTime(start) + " \n "
                PrintMsg(theMsg, 0)
                PrintMsg(".", 0)
                

        else:
            # no previous indexes, trying creating new ones from metadata tables
            bIndexed = CreateNewIndexes(newDB)

            if not bIndexed:
                PrintMsg(".\tFailed to create new attribute indexes", 1)
                    
    else:
        PrintMsg(".\tFailed to import data", 1)

except:
    PrintMsg("Error in main function", 2)

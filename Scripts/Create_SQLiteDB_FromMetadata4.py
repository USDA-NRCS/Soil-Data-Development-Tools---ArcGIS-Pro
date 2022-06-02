# Create_SQLiteDB_FromMetadata.py
# Requires ArcGIS Pro 2.7
#
# Create SQL for SSURGO schema
# No data will be populated in any of the tables. Schema only.
# ??? No spatial tables defined in the mdstat tables??? Confirm this please 02-13-22021.
# so that will have to come from SDM or perhaps convert featureclasses from gSSURGO?
#  1. Use the sequence defined by SSURGO Template DB in VBA script
#  2. Use the column definitions, keys and indexes defined in the mdstat* tables of the SSURGO Template DB
#  3. Build a dictionary containing the column info
#  4. Iterate through the table sequence and build CREATE TABLE sql statements.
#  5. This method is not intended to be used as a production tool, but as an aid to creating a new Template DB.


# Python 3.6.10
#
# 2021-02-01
#
# ogr drivers available to ArcGIS Pro 2.6.
# Could try PGeo to see if it will read MS Access mdb. Answer appears to be NO.
# What about ODBC driver and mdb? Does not appear to work either. Probably a 32-64bit issue.
#
# ARCGEN, AVCBin, AVCE00, AeronavFAA, AmigoCloud, BNA, CAD, CSV, CSW, Carto, Cloudant,
# CouchDB, DB2ODBC, DGN, DXF, EDIGEO, ESRI Shapefile, ESRIJSON, ElasticSearch, GFT, GML,
# GMLAS, GPKG, GPSBabel, GPSTrackMaker, GPX, GeoJSON, GeoRSS, Geoconcept, Geomedia, HTF,
# HTTP, Idrisi, JML, JP2KAK, KML, MBTiles, MSSQLSpatial, MVT, MapInfo File, Memory, NAS,
# ODBC, ODS, OGR_GMT, OGR_PDS, OGR_SDTS, OGR_VRT, OSM, OpenAir, OpenFileGDB, PCIDSK, PDF,
# PGDUMP, PGeo, PLSCENES, REC, S57, SEGUKOOA, SEGY, SQLite, SUA, SVG, SXF, Selafin, TIGER,
# TopoJSON, UK .NTF, VDV, VFK, WAsP, WFS, WFS3, Walk, XLS, XLSX, XPlane, netCDF
#
# Python 3.7.9
# 2021-02-05 Upgraded my laptop to ArcGIS Pro 2.7 which can create the '.geodatabase' version
# of a SQLite database.
#
# 2021-02-15 Revising queries to separate out key info from more basic table-column info.
#   Trying to make sure the final queries contain all the correct primary and foreign key settings.
#
# 2021-03-10 Views don't seem to work as well in mobile geodatabase. Popups specifically don't
# show any information for views.
#
# 2021-03-10 Looking at sqlite3 option for adding geometry column to spatial tables.

# 2021-03-11 Using an ESRI? DLL to add ST_Geometry capability and AddGeometryColumn
#            to sqlite databases. Need to see if there is a spatialite equivalent.
#
# 2021-03-15 Preliminary tests with Spatialite finds a problem with the 'mod_spatialite.dll'.
# 2021-03-15 As a workaround, I was able to manually create a template database for Spatialite using QGIS.
#
# The Spatialite/Spatialite database seems to work OK. Spatial Views work in both Pro and QGIS.
# Currently my Geopackage Spatial Views work in Pro, but are not working in QGIS.
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
            return ""
            #return 'MyError has been raised'

## ===================================================================================
def MyWarning(msg):
    # If I use sys.exit(1), the script will drop down to the exception clause where usually errorMsg1 is called.
    # Do I need to clear the traceback when MyError is called?
    PrintMsg(msg, 1)
    return

## ===================================================================================
def errorMsg1(excInfo):
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
        return False

    except:
        errorMsg1(sys.exc_info())
        return False

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
        pass

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
        errorMsg1(sys.exc_info())
        return False
        return "???"

## ===================================================================================
def elapsedTime(start):
    # Calculate amount of time since "start" and return time string
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

    except MyError as e:
        PrintMsg(str(e), 2)
        return ""

    except:
        errorMsg1(sys.exc_info())
        return ""

## ===================================================================================
def CreateMobileGDB(outputDB, dTableInfo, bInteger, tabOrder):
    # Create new mobile geodatabase template for SSURGO data
    # This function uses arcpy!!!

    try:

        arcpy.management.CreateMobileGDB(os.path.dirname(outputDB), os.path.basename(outputDB))

        tmpDB = "in_memory"

        env.workspace = tmpDB

        for tbl in tabOrder:
            tblInfos = dTableInfo[tbl]
            #tmpTbl = os.path.join("in_memory", tbl)
            PrintMsg(".\tCreating new table " + tbl, 0)
            newTbl = os.path.join(outputDB, tbl)
            arcpy.management.CreateTable(tmpDB, tbl)
            tmpTbl = os.path.join(tmpDB, tbl)

            for colInfos in tblInfos:
                colCnt = len(colInfos)

                colCnt -= 1
                colseq, colName, dataType, fldSize, fldPrec, notNull, domain, colAlias = colInfos

                # make sure the 'notnull' column gets changed to a legal name
                if colName == "notnull":
                    colName = "notnull_"

                if notNull == "Yes":
                    notNull = "NON_NULLABLE"

                elif notNull == "No":
                    notNull = "NULLABLE"

                # Logic to set column definitions for
                colList = [colName]

                if dataType == "String":
                    if bInteger and colName[-3:].lower() == "key" and fldSize == 30:
                        fldType = "INTEGER"
                        fldSize = 0

                    else:
                        fldType = "TEXT"

                elif dataType == "Choice":
                    fldType = "TEXT"

                elif dataType == "Integer":
                    fldType = "INTEGER"

                elif dataType == "Boolean":

                    if fldSize is None:
                        fldType = "INTEGER"

                    else:
                        fldType = "TEXT"

                elif dataType == "Date/Time":
                    fldType = "DATE"

                elif dataType == "Float":
                    fldType = "FLOAT"

                elif dataType == "Vtext":
                    fldType = "TEXT"
                    fldSize = 2147483647

                else:
                    PrintMsg("Unhandled datatype: " + dataType + " " + str(fldSize), 0)

                # colseq, colName, dataType, fldSize, fldPrec, notNull, domain, colAlias
                arcpy.management.AddField(tmpTbl, colName, fldType, "", fldPrec, fldSize, colAlias, notNull, "REQUIRED")

            #env.workspace = outputDB
            arcpy.conversion.TableToTable(tmpTbl, outputDB, tbl)
            del tmpTbl

        ## End of creating mobile geodatabase from scrach
        ##
        # Need to cofirm that valid output database exists
        return True

    except MyError as e:
        PrintMsg(str(e), 2)
        return False

    except:
        errorMsg1(sys.exc_info())
        return False

## ===================================================================================
def CreateSQLiteDB(conn2, outcur, outputDB, dbExt, spatial_type, mdQuery, tblValues, bInteger, tabOrder):
    # Create sqlite or geopackage database

    try:
        # For sqlite or geopackage, create the attribute tables directly,
        # using the query generated from the metadata tables
        #
        # More than one way to create an sqlite database.

        # 1. Use arcpy command

        if mdQuery == "":
            # bailout if the CreateTable query is empty
            raise MyError("")

        #arcpy.management.CreateSQLiteDatabase(outputDB, spatial_type)

        # 2. or just connect to a non-existent database and it will be created
        #
        # There are two versions of 'stgeometry_sqlite.dll' in the ArcGIS 10.8 install
        # C:\Program Files (x86)\ArcGIS\Desktop10.8\DatabaseSupport\SQLite\Windows64 * using this one initially
        # C:\Program Files (x86)\ArcGIS\Desktop10.8\DatabaseSupport\SQLite\Windows32



        # Create all standard SSURGO attribute tables
        outcur.executescript(mdQuery)
        conn2.commit()

        # Pre-populate month table
        monthValues = [(4,'April'),(8,'August'),(12,'December'),(2,'February'),(1,'January'),(7,'July'),(6,'June'),(3,'March'),(5,'May'),(11,'November'),(10,'October'),(9,'September')]

        outcur.executemany('INSERT INTO month VALUES (?,?)', monthValues)
        conn2.commit()

        # For a geopackage, we need to register each table to the gpkg_contents table or
        # else ArcGIS will not find them.
        if dbExt == ".gpkg":

            #if len(tblValues) == (6 + len(tabOrder)):
            if len(tblValues) == len(tabOrder):
                # make sure that there is a value for each table. Quick check just compares counts.
                # tblValues includes the 6 spatial layers
                queryRegisterTables = "INSERT INTO gpkg_contents (table_name, data_type, identifier, description) VALUES(?, ?, ?, ?)"
                outcur.executemany(queryRegisterTables, tblValues)
                conn2.commit()

            else:
                PrintMsg("Length of tblValues != tabOrder: " + str(len(tblValues)) + " .. " + str(len(tabOrder)), 2)

##        if viewQuery != "":
##            # Create views in Template database
##            outcur.executescript(viewQuery)
##            conn2.commit()

##        # do I need to delete outcur?
##        conn2.close
##        del outcur
##        del conn2
        #PrintMsg("Output database: " + outputDB, 0)

        # end of sqlite, gpkg option
        # Need to cofirm that valid output database exists
        return True

    except MyError as e:
        PrintMsg(str(e), 2)
        return False

    except:
        errorMsg1(sys.exc_info())
        return False

## ===================================================================================
def GetTableInfo(cur):
    # Using metadata database connection, create dictionary containing table information
    try:
        dTableInfo = dict() # save column info in this dictionary for random access

        sqlColumnInfo = """SELECT TC.tabphyname, TC.colsequence, TC.colphyname,
        TC.logicaldatatype, TC.fieldsize, TC.precision, TC.notnull_, TC.domainname, TC.collabel
        FROM mdstattabcols TC
        ORDER BY TC.tabphyname, TC.colsequence ASC
        ; """

        lastTable = "xxxx"
        infoList = list()

        for rec in cur.execute(sqlColumnInfo):
            # tblName and colName will later be used to represent child table and child column in foreign keys
            tblName, colSeq, colName, fldType, fldSize, fldPrec, notNull, domain, colAlias = rec

            if tblName != lastTable:
                dTableInfo[lastTable] = infoList
                infoList = [[colSeq, colName, fldType, fldSize, fldPrec, notNull, domain, colAlias]]
                lastTable = tblName
                #PrintMsg(".\tdTableInfo: " + lastTable, 0)

            else:
                infoList.append([colSeq, colName, fldType, fldSize, fldPrec, notNull, domain, colAlias])

        if not lastTable in dTableInfo:
            #PrintMsg(".\tdTableInfo: " + lastTable, 0)
            dTableInfo[lastTable] = infoList

        return dTableInfo

    except MyError as e:
        PrintMsg(str(e), 2)
        return dTableInfo

    except:
        errorMsg1(sys.exc_info())
        return dTableInfo

## ===================================================================================
def GetTableLists(cur):
    # Get table info including name, alias, description for use in registering tables to geopackage
    # Currently these will include the geometry tables (AKA featureclasses).
    try:
        tblValues = list()

        sqlTableInfo = """SELECT tabphyname, tablabel, tabdesc
        FROM mdstattabs
        ORDER BY tabphyname
        ;"""

        for rec in cur.execute(sqlTableInfo):
            tblName, tblAlias, tblDesc = rec
            tnta = (tblName, "attributes", tblAlias, tblDesc)
            tblValues.append(tnta)

        return tblValues

    except MyError as e:
        PrintMsg(str(e), 2)
        return tblValues

    except:
        errorMsg1(sys.exc_info())
        return tblValues

## ===================================================================================
def GetPrimaryKeys(cur, spatialLayers):
    # Get information for primary keys
    # Not sure if 'mukey' for mupolygon table should be listed as a foreign key?
    try:
        dPrimaryKeys = dict()  # Key value is tablename. When accessing data from this dictionary, sort on first item value (colsequence).

        sqlPrimaryKeys = """SELECT IM.tabphyname, ID.idxcolsequence, IM.idxphyname, IM.uniqueindex, ID.colphyname
        FROM mdstatidxmas AS IM
        INNER JOIN mdstatidxdet AS ID ON (IM.idxphyname = ID.idxphyname) AND (IM.tabphyname = ID.tabphyname)
        WHERE IM.idxphyname LIKE 'PK%'
        ORDER BY IM.tabphyname, IM.idxphyname, ID.idxcolsequence ASC
        ;"""

        lastTable = "xxxx"
        infoList = list()

        for rec in cur.execute(sqlPrimaryKeys):
            #
            tabphyname, idxcolsequence, idxphyname, uniqueindex, colphyname = rec

            # PrintMsg(str(rec), 1)

            if tabphyname != lastTable:
                dPrimaryKeys[lastTable] = infoList
                # PrintMsg(".\tPrimary key for " + lastTable + ": " + str(infoList), 0)
                keyColumns = [colphyname]
                infoList = [idxphyname, uniqueindex, keyColumns]
                lastTable = tabphyname

            else:
                keyColumns.append(colphyname)

        if not lastTable in dPrimaryKeys:
            dPrimaryKeys[lastTable] = infoList

        return dPrimaryKeys

    except MyError as e:
        PrintMsg(str(e), 2)
        return dPrimaryKeys

    except:
        errorMsg1(sys.exc_info())
        return dPrimaryKeys

## ===================================================================================
def GetIndexes(cur, spatialLayers):
    # Get information for foreign keys and indexes

    try:
        dForeignKeys = dict()  # Key value is tablename. When accessing data from this dictionary, sort on first item value (colsequence).

        # idxcolsequence is important. Make sure that order is maintained in the dictionary objects.
        sqlForeignKeys = """SELECT IM.tabphyname, ID.idxcolsequence, IM.idxphyname, ID.colphyname, RD.ltabphyname, RD.ltabcolphyname
        FROM mdstatidxmas AS IM
        LEFT OUTER JOIN mdstatidxdet AS ID ON (IM.idxphyname = ID.idxphyname) AND (IM.tabphyname = ID.tabphyname)
        LEFT OUTER JOIN mdstatrshipdet AS RD ON (ID.tabphyname = RD.rtabphyname AND ID.colphyname = RD.rtabcolphyname)
        WHERE IM.idxphyname LIKE 'DI%' AND NOT RD.ltabphyname IS NULL
        ORDER BY IM.tabphyname, IM.idxphyname, ID.idxcolsequence ASC
        ;"""

        #dForeignKeys = dict()  # Key value is tablename. When accessing data from this dictionary, sort on first item value (colsequence).
        dTableIndexes = dict()  # Key value is tablename. Value is a list of indexes for each table.
        dIndexes = dict()      # Key value is idxphyname.
        infoList = list()
        cntr = 0

        for rec in cur.execute(sqlForeignKeys):
            #
            cntr += 1
            tabphyname, idxcolsequence, idxphyname, colphyname, ltabphyname, ltabcolphyname = rec
            #PrintMsg(str(cntr) + ".\t" + tabphyname + ": " + idxphyname + ", " + str(idxcolsequence) + ", " + str(colphyname) + ", " + str(ltabphyname) + ", " + str(ltabcolphyname) , 0)

            if not idxphyname in dIndexes:
                # start new index
                dIndexes[idxphyname] = tabphyname, [colphyname], ltabphyname, [ltabcolphyname]

                if not tabphyname in dTableIndexes:
                    dTableIndexes[tabphyname] = [idxphyname]

                else:
                    dTableIndexes[tabphyname].append(idxphyname)

            else:
                # append additional columns to the existing information for this index
                dIndexes[idxphyname][1].append(colphyname)
                dIndexes[idxphyname][3].append(ltabcolphyname)

        return dTableIndexes, dIndexes

    except MyError as e:
        PrintMsg(str(e), 2)
        return dTableIndexes, dIndexes

    except:
        errorMsg1(sys.exc_info())
        return dTableIndexes, dIndexes

## ===================================================================================
def GetUniqueConstraints(cur):
    # Key value is tablename. When accessing data from this dictionary, sort on first item value (colsequence).

    try:
        #
        dUniqueKeys = dict()

        sqlUniqueKeys = """SELECT IM.tabphyname, ID.idxcolsequence, IM.idxphyname, ID.colphyname
        FROM mdstatidxmas AS IM
        LEFT OUTER JOIN mdstatidxdet AS ID ON (IM.idxphyname = ID.idxphyname) AND (IM.tabphyname = ID.tabphyname)
        WHERE IM.idxphyname LIKE 'UC%'
        ORDER BY IM.tabphyname, IM.idxphyname, ID.idxcolsequence ASC
        ;"""

        lastTable = "xxxx"
        lastIndex = "xxxx"
        infoList = list()
        constraintList = list()
        keyColumns = list()
        cntr = 0

        for rec in cur.execute(sqlUniqueKeys):
            #
            cntr += 1
            tabphyname, idxcolsequence, idxphyname, colphyname = rec
            # PrintMsg(str(cntr) + ".\t" + tabphyname + ": " + idxphyname + " " + str(idxcolsequence) + "\t" + colphyname, 0)

            if tabphyname != lastTable:
                # Add all unique constraints from previous table
                dUniqueKeys[lastTable] = [constraintList]

                # Reset constraints for next table
                constraintList = list()  # list of all unique key constraints for this table
                infoList = list()        # information for a single constraint, which could consist of multiple columns
                lastTable = tabphyname

            if idxphyname != lastIndex:
                # wrap up previous constraint with complete list of all columns used
                # and add this unique key constraint to the list for this table
                infoList = [idxphyname, keyColumns]
                constraintList.append(infoList)
                # start new constraint
                lastIndex = idxphyname
                keyColumns = [colphyname]

            else:
                # Adding additional column names to the current constraint
                keyColumns.append(colphyname)
                lastIndex = idxphyname

        if not lastTable in dUniqueKeys:
            dUniqueKeys[lastTable] = [constraintList]

        return dUniqueKeys

    except MyError as e:
        PrintMsg(str(e), 2)
        return dUniqueKeys

    except:
        errorMsg1(sys.exc_info())
        return dUniqueKeys

## ===================================================================================
def CreateQuery(tabOrder, dTableInfo, dPrimaryKeys, dTableIndexes, dIndexes, dUniqueKeys, dbExt, dSpatial):
    # Generate SQL for SSURGO schema
    # Need to compare results between AddGeometryColumn and CreateFeatureClass_management
    #
    try:
        # Problem for spatial tables
        # Since shapefiles weren't part of the original SSURGO database,
        # primary keys and indexes are not defined in the metadata tables
        #
        # SRID for WGS1984 Geographic
        # I believe this is included by default inthe spatial_ref_sys table
        srid = "4326"

        mdQuery = "-- Begin Create Table queries"
        tabIndexes = list()

        for tbl in tabOrder:

            if tbl in dTableInfo:
                #PrintMsg(tbl + ": " + str(dTableInfo[tbl]), 1)
                msg = "\nCREATE TABLE " + tbl + "(\n"
                mdQuery += msg
                #PrintMsg(msg, 0)
                colInfos = dTableInfo[tbl]
                colCnt = len(colInfos)

                # Get primary keys for this table
                # [idxphyname, uniqueindex, keyColumns, tablabel]
                if tbl in dPrimaryKeys:
                    primaryKeys = dPrimaryKeys[tbl] # list of primary keys in this table (usually just one, except for mdstat tables)

                else:
                    primaryKeys = dict()

                # Get foreign keys for this table
                foreignKeys = list()

                if tbl in dTableIndexes:

                    indxphynames = dTableIndexes[tbl]

                    for indxphyname in indxphynames:

                        if indxphyname in dIndexes:
                            foreignKeys.append(dIndexes[indxphyname])
                            #PrintMsg("Found foreign key info for " + indxphyname, 0)

                else:
                    PrintMsg("No foreign keys found for " + tbl, 1)
                    foreignKeys = list()

                for colInfo in colInfos:
                    colCnt -= 1
                    colseq, colName, dataType, fldSize, fldPrec, notNull, domain, colAlias = colInfo

                    # make sure the 'notnull' column gets changed to a legal name
                    if colName == "notnull":
                        colName = "notnull_"

                    # Logic to set column
                    colList = [colName]

                    if dataType == "String":
                        if bInteger and colName[-3:] == "key" and fldSize == 30: # new code for integer keys
                            fldType = "Integer" # new code for integer keys
                            fldSize = None      # new code for integer keys

                        else:
                            # Original code
                            fldType = "CHARACTER(" + str(fldSize) + ")"

                    elif dataType == "Choice":
                        fldType = "CHARACTER(" + str(fldSize) + ")"

                    elif dataType == "Integer":
                        fldType = "INTEGER"

                    elif dataType == "Boolean":

                        if fldSize is None:
                            fldType = "INTEGER"

                        else:
                            fldType = "CHARACTER(" + str(fldSize) + ")"

                    elif dataType == "Date/Time":
                        fldType = "TIMESTAMP"

                        #if dbExt in (".sqlite", ".gpkg"):
                        #    fldType = "TIMESTAMP"

                        #elif dbExt == ".geodatabase":
                        #    fldType = "DATETIME"

                    elif dataType == "Float":
                        fldType = "REAL"

                    elif dataType == "Vtext":
                        fldType = "CHARACTER(2147483647)"

                    else:
                        PrintMsg("Unhandled datatype: " + dataType + " " + str(fldSize), 0)

                    colList.append(fldType)

                    if notNull == "Yes":
                        colList.append( "NOT NULL")

                    #if indexSeq is not None and indexSeq > 0 and indexName.startswith("UC"):
                    #    colList.append("UNIQUE")

                    if colCnt > 0:
                        msg = " ".join(colList) + ",\n"
                        mdQuery += msg

                    elif len(foreignKeys) == 0 and len(primaryKeys) == 0:
                        # no primary key or foreign key constraints, skip the comma
                        # [idxphyname, uniqueindex, [keyColumns]]
                        msg = " ".join(colList) + "\n"
                        mdQuery += msg

                    else:
                        # Add comma
                        msg = " ".join(colList) +",\n"
                        mdQuery += msg

                if len(primaryKeys) > 0:
                    # [idxphyname, uniqueindex, [keyColumns]]
                    idxphyname, uniqueindex, keyColumns = primaryKeys

                    if len(keyColumns) == 1:
                        # Single primary key column

                        if len(foreignKeys) > 0:
                            # foreign key constraints will be added next
                            mdQuery += "PRIMARY KEY (" + keyColumns[0] + "), \n"

                        else:
                            # end of the query for this table
                            mdQuery += "PRIMARY KEY (" + keyColumns[0] + ") \n"

                    else:
                        if len(foreignKeys) > 0:
                            mdQuery += "PRIMARY KEY (" + ", ".join(keyColumns) + "),\n"

                        else:
                            mdQuery += "PRIMARY KEY (" + ", ".join(keyColumns) + ")\n"

                    if len(foreignKeys) == 0:
                        mdQuery = mdQuery[0:-1]

                else:
                    err = "WARNING! No primary key identified for table: " + tbl
                    PrintMsg(".\t" + err, 1)
                    #raise MyError(err)


                if len(foreignKeys) > 0:
                    # one foreign key looks like: ('sainterp', ['sacatalogkey'], 'sacatalog', ['sacatalogkey'])

                    for fkey in foreignKeys:
                        #PrintMsg(tbl + " foreign key: " + str(fkey), 0)

                        childTable, childKey, parentTable, parentKey = fkey



                        if len(parentKey) == 1:
                            mdQuery += "FOREIGN KEY (" + childKey[0] + ") REFERENCES " + parentTable + "(" + parentKey[0] + "),\n"

                        elif len(parentKey) > 1:
                            mdQuery += "FOREIGN KEY (" + ", ".join(childKey) + ") REFERENCES " + parentTable + "(" + ", ".join(childKey) + "),\n"

                        else:
                            pass

                    mdQuery = mdQuery[0:-2]  # remove last comma from foreign keys

                msg = "\n);"
                mdQuery += msg

                if tbl in dSpatial and databaseType.upper() == "SPATIALITE":
                #if tbl in dSpatial and databaseType.upper() == "SPATIALITE" and spatial_type.upper() == "ST_GEOMETRY":
                    # Add geometry column to spatial layer
                    #if tbl == "mupoint":  # skip others to see if the first featureclass even works
                    if 1 == 1:
                        dSpatial = {'featline':'2', 'featpoint':'1', 'muline':'2', 'mupoint':'1', 'mupolygon':'6', 'sapolygon':'6'}
                        geomType = dSpatial[tbl]

                        # ESRI Desktop help for AddGeometryColumn
                        # https://desktop.arcgis.com/en/arcmap/latest/manage-data/using-sql-with-gdbs/register-an-st-geometry-column.htm
                        # Currently I believe I am using the 64-bit version. There are two different DLLs included with 10.8.
                        # 0: 'main' or null
                        # 1: table_name
                        # 2: spatial_column_name
                        # 3: srid
                        # 4: geometry_type
                        #      0 st_geometry
                        #      1 st_point
                        #      2 st_linestring
                        #      3 st_polygon
                        #      4 st_multipoint
                        #      5 st_multstring
                        #      6 st_multipolygon
                        #  5: coordinate_dimension 2 'xy', 3 'xyz', 4 'xyzm'
                        #  6: 'null' or 'not null'
                        #
                        #
                        #  SELECT AddGeometryColumn(
                        #  null,
                        #  'hazardous_sites',
                        #  'location',
                        #  4326,
                        #  'polygon',
                        #  'xy',
                        #  'null'
                        #  );
                        #

                        #        SELECT AddGeometryColumn ( NULL, 'geoms', 'geometry', 4326, 'geometry', 'xy', 'null' );
                        #
                        # Not sure about this one (SELECT CreateOGCTables();). On this ESRI Help page:
                        # https://desktop.arcgis.com/en/arcmap/latest/manage-data/databases/spatially-enable-sqlilte.htm
                        # It says that command will add the ST_Geometry tables to the database. This may not be
                        # referring to the same DLL that has the 'SDE_SQL_funcs_init' option.
                        #
                        # I've also notice that for Spatialite there is an extension named 'mod_spatialite'. I have not found this one yet.
                        #
                        # Another reference for creating SQLite or Geopackage geometry can be found here.
                        # https://desktop.arcgis.com/en/arcmap/latest/manage-data/databases/spatially-enable-sqlilte.htm


                        msg = "\nSELECT AddGeometryColumn( 'main', '" + tbl.lower() + "', 'shape', " + str(srid) + ", " +  geomType  + ", 'XY', 'not null');"
                        #PrintMsg(".\t", 0)
                        #PrintMsg(msg, 0)
                        mdQuery += msg

                mdQuery += "\n--"



            else:
                raise MyError("dTableInfo is missing data for " + tbl)


        msg = "-- End of Create Table Queries \n"
        mdQuery += msg
        # End of the 'CREATE TABLE' queries

        # For diagnostic purposes, save the attribute table query to a text file ...
        queryPath = os.path.join(basePath, "Queries")
        queryFile = os.path.join(queryPath, "Query_CreateTables_" + dbExt[1:] + ".txt")

        if arcpy.Exists(queryFile):
            arcpy.Delete_management(queryFile)

        with open(queryFile, "w") as fh:
            fh.writelines(mdQuery)
            fh.close()

        # Popup the query in a text editor
        os.startfile(queryFile)

        return mdQuery

    except MyError as e:
        PrintMsg(str(e), 2)
        return ""

    except:
        errorMsg1(sys.exc_info())
        return ""

## ===================================================================================
def CreateViews(conn2, outcur, databaseType, spatial_type):
    # Create views in the Template database. The first two are spatial views.
    # Seeing an error "Exception from HRESULT: 0x8004152A" when I try to add one of
    # these views to ArcGIS Pro Map document
    #
    # views_geometry_columns: view_name, view_geometry, view_rowid, f_table_name, geometry_column, read_only
    # views_geometry_columns_auth: view_name, view_geometry, hidden
    #
    # views_geometry_columns_field_infos: view_name, view_geometry, ordinal, column_name, null_values,
    #    integer_values, double_values, text_values, blob_values, max_size, integer_min, integer_max, double_min, double_max
    try:
        dViews = dict()

        if databaseType.upper() == "SPATIALITE" and spatial_type.upper() == "ST_GEOMETRY":
            PrintMsg(".\t", 0)
            PrintMsg(".\tCreating spatial views...", 0)

            # New test, creating views for ST_Geometry databases inside the create table queries
            # Adding spatial view for mupolygon-muaggatt table
            PrintMsg(".", 0)
            PrintMsg(".\tAdding spatial view for map unit name", 0)
            view_name = "view_muname"
            view_geometry = "shape"
            view_rowid = "objectid"
            f_table_name = "mupolygon"
            geometry_column = "shape"
            view_query = """CREATE VIEW view_muname AS SELECT
            M.objectid, M.shape, M.areasymbol, M.spatialver, M.musym, M.mukey, R.muname
            FROM MUPOLYGON M
            INNER JOIN mapunit R ON M.mukey = R.mukey
            ORDER BY M.objectid ASC;\n"""
            dViews[view_name] = {"view_query":view_query, "view_geometry":view_geometry, "view_rowid":view_rowid, "f_table_name":f_table_name, "geometry_column":geometry_column, "read_only":1, "hidden":0}
            outcur.execute(view_query)
            conn2.commit()

            ##Add spatial view for mupolygon-muaggatt table
            PrintMsg(".\tAdding spatial view of selected muaggatt data", 0)
            view_name = "view_mupolyextended"
            view_geometry = "shape"
            view_rowid = "objectid"
            f_table_name = "mupolygon"
            geometry_column = "shape"
            view_query = """CREATE VIEW view_mupolyextended AS SELECT
            M.objectid, M.shape, M.areasymbol, M.spatialver, M.musym, M.mukey, G.muname,
            G.slopegradwta, G.brockdepmin, G.aws025wta, G.drclassdcd, G.hydgrpdcd, G.niccdcd, G.hydclprs
            FROM MUPOLYGON M
            INNER JOIN muaggatt G ON M.mukey = G.mukey
            ORDER BY M.objectid ASC;\n"""
            dViews[view_name] = {"view_query":view_query, "view_geometry":view_geometry, "view_rowid":view_rowid, "f_table_name":f_table_name, "geometry_column":geometry_column, "read_only":1, "hidden":0}
            outcur.execute(view_query)
            conn2.commit()
            #
            # End of spatial views

        else:
            PrintMsg(".\tSkipping creation of spatial views: " + databaseType + ":" + spatial_type, 0)

        return dViews

    except MyError as e:
        PrintMsg(str(e), 2)
        return dViews

    except:
        errorMsg1(sys.exc_info())
        return dViews

## ===================================================================================
def RegisterViews(conn, cur, dViews, ddatabaseType, spatial_type):
    # Register new views in database. This is a test.
    #
    # views_geometry_columns: view_name, view_geometry, view_rowid, f_table_name, geometry_column, read_only
    # views_geometry_columns_auth: view_name, view_geometry, hidden
    # views_geometry_columns_field_infos: view_name, view_geometry, ordinal, column_name, null_values,
    #    integer_values, double_values, text_values, blob_values, max_size, integer_min, integer_max, double_min, double_max
    #    This table appears to allow for table value statistics to be stored. Ordinal is the column order number (0-based)
    #    for each column within the table.
    #
    # Also noticed that the vector_layers_statistics table does not have populated row_count, or extent max-min values.
    # The vector_layer_field_infos table isn't even formed.

    # dViews[view_name] = {"view_query":view_query, "view_geometry":view_geometry, "view_rowid":view_rowid,
    # "f_table_name":f_table_name, "geometry_column":geometry_column, "read_only":1, "hidden":0}
    #
    try:

        if databaseType.upper() == "SPATIALITE" and spatial_type.upper() == "SPATIALITE":
            # check existing views in view metadata tables to make sure these new views haven't been registered
            colsQuery = "SELECT view_name FROM views_geometry_columns"
            cur.execute(colsQuery)
            registeredViews = cur.fetchall()

        for view_name, view_info in dViews.items():
            view_query, view_geometry, view_rowid, f_table_name, f_geometry_column, read_only, hidden = view_info

            if not view_name in registeredViews:
                # view_name, view_geometry, view_rowid, f_table_name, geometry_column, read_only
                regValues = (view_name, view_geometry, view_rowid, f_table_name, f_geometry_column, read_only)
                cur.execute('INSERT INTO views_geometry_columns (view_name, view_geometry, view_rowid, f_table_name, f_geometry_column, read_only) \
                VALUES (?, ?, ?, ?, ?, ?) ', str(regValues) )

                regValues = ( view_name, view_geometry, hidden )
                cur.execute('INSERT INTO views_geometry_columns_auth ( view_name, view_geometry, hidden )  \
                VALUES (?, ?, ?)', str(regValues))


        else:
            PrintMsg(".\tSkipping registration of spatial views for " + databaseType + ":" + spatial_type, 0)

        conn.commit()

        return True

    except MyError as e:
        PrintMsg(str(e), 2)
        return False

    except:
        errorMsg1(sys.exc_info())
        return False

## ===================================================================================
def CreateDbConnection(outputDB, spatial_type):
    # Create connection that will be used to execute the Create Table and Insert statements
    # for spatialite databases
    #
    try:

        conn2 = sqlite3.connect(outputDB)

        if spatial_type == "ST_GEOMETRY":
            PrintMsg("Adding ST Geometry extension for sqlite3 database", 0)
            conn2.enable_load_extension(True)
            conn2.load_extension('stgeometry_sqlite.dll')
            outcur = conn2.cursor()
            PrintMsg("Executing CreateOGCTables...", 0)
            conn2.execute("SELECT CreateOGCTables();")
            conn2.commit()

        elif spatial_type == "SPATIALITE":
            #PrintMsg("Adding Spatialite extension for sqlite3 database", 0)
            # mod_spatialite is not working!
            #conn2.enable_load_extension(True)
            #conn2.load_extension('mod_spatialite')
            #conn2.commit()
            PrintMsg("Skipping Spatialite extension for sqlite3 database", 0)
            outcur = conn2.cursor()

        else:
            outcur = conn2.cursor()

        return conn2, outcur


    except MyError as e:
        PrintMsg(str(e), 2)
        return None, None

    except:
        errorMsg1(sys.exc_info())
        return None, None

## ===================================================================================
def CreateTemplateDB(inputDB, outputFolder, templatePath, dbName, dbExt, bInteger, spatial_type):
    # Set up the process for generating a new template database+++++++

    try:

        PrintMsg("Using metadata tables in '" + inputDB + "' to generate the queries", 0)
        #PrintMsg("Returned: " + str(outputTbl) + ";\t" + str(outputValues), 0)

        # Tabular import order which was adapted from MS Template VBA - Import module
        tabOrder = ['sacatalog', 'sainterp', 'distmd', 'legend', 'distinterpmd', 'distlegendmd',
        'laoverlap', 'legendtext', 'mapunit', 'component', 'muaggatt', 'muaoverlap', 'mucropyld',
        'mutext', 'chorizon', 'cocanopycover', 'cocropyld', 'codiagfeatures', 'coecoclass',
        'coerosionacc', 'coeplants', 'coforprod', 'cogeomordesc', 'cohydriccriteria', 'cointerp',
        'comonth', 'copmgrp', 'copwindbreak', 'corestrictions', 'cosurffrags', 'cotaxfmmin',
    'cotxfmother', 'cotaxmoistcl', 'cotext', 'cotreestomng', 'chaashto', 'chconsistence',
    'chdesgnsuffix', 'chfrags', 'chpores', 'chstructgrp', 'chtext', 'chtexturegrp', 'chunified',
    'coforprodo', 'copm', 'cosoilmoist', 'cosoiltemp', 'cosurfmorphgc', 'cosurfmorphhpp',
    'cosurfmorphmr', 'cosurfmorphss', 'chstruct', 'chtexture', 'chtexturemod', 'featdesc',
    'mdstatdommas', 'mdstatdomdet', 'mdstatidxmas', 'mdstatidxdet', 'mdstatrshipmas', 'mdstatrshipdet',
    'mdstattabs', 'mdstattabcols', 'month', 'sdvalgorithm', 'sdvattribute', 'sdvfolder', 'sdvfolderattribute',
    'featline', 'featpoint', 'muline', 'mupoint', 'mupolygon', 'sapolygon']

        spatialLayers = ['featline', 'featpoint', 'muline', 'mupoint', 'mupolygon', 'sapolygon']

        # Define geometry types for SSURGO featureclasses
        # This information may be specified in the mdstat tables somewhere? Need to look.
        #dSpatial = {'featline':'POLYLINE', 'featpoint':'POINT', 'muline':'POLYLINE', 'mupoint':'POINT', 'mupolygon':'MULTIPOLYGON', 'sapolygon':'MULTIPOLYGON'}
        dSpatial = {'featline':'LINE', 'featpoint':'POINT', 'muline':'LINE', 'mupoint':'POINT', 'mupolygon':'MULTIPOLYGON', 'sapolygon':'MULTIPOLYGON'}
        #dSpatial = {'featline':'ST_Line', 'featpoint':'ST_Point', 'muline':'ST_Line', 'mupoint':'ST_Point', 'mupolygon':'ST_Polygon', 'sapolygon':'ST_Polygon'}

        # Open database containing just the populated metadata tables
        # After the metadata information has been read, close this database connection
        # and get ready to create the new database with a new connection
        #
        if arcpy.Exists(inputDB):
            conn = sqlite3.connect(inputDB)
            cur = conn.cursor()


            # These functions get table/column definitions needed to create schema for the attribute tables
            # Handling spatial tables separately.
            tblValues = GetTableLists(cur)

            dTableInfo = GetTableInfo(cur)

            dPrimaryKeys = GetPrimaryKeys(cur, spatialLayers)

            dTableIndexes, dIndexes = GetIndexes(cur, spatialLayers)

            dUniqueKeys = GetUniqueConstraints(cur)

            mdQuery = CreateQuery(tabOrder, dTableInfo, dPrimaryKeys, dTableIndexes, dIndexes, dUniqueKeys, dbExt, dSpatial)

##            dViews = CreateViews(conn, cur, databaseType, spatial_type)
##
##
##            if databaseType == "Spatialite" and geomType == "SPATIALITE":
##                bRegistered = RegisterViews(conn, cur, dViews, databaseType, spatial_type)

            del cur

            conn.close()
            del conn

            # Currently I have another tool (Create SSURGO SQLite Template Database) which
            # will read Query files and generate the database with geometry tables.
            #
            PrintMsg(".\tTaking EARLY OUT, before database is actually created...", 0)
            return True



            #PrintMsg("=====================================", 0)
            #for tabphyname, info in dUniqueKeys.items():
            #    PrintMsg(tabphyname + ": " + str(info), 0)

            # The rest of this script uses SQLite syntax, but could be modified to work
            # with other SQL databases.
            # Metadata data types: String, Integer, Date/Time, Choice, Vtext, Boolean, Float
            #
            # dTableInfo[tableName] = [[colseq, colName, fldType, fldSize, fldPrec, notNull, domain, colAlias]] (sorted by colseq)
            # dPrimaryKeys[tableName] = [idxphyname, uniqueindex, [keyColumns]]
            # dForeignKeys[tableName] = [idxphyname, [keyColumns], ltabphyname, [relColumns]]
            # dUniqueKeys[tableName] = [[idxphyname, [keyColumns]]]

            # Create a new sqlite database and then execute the big 'CREATE TABLE' query
            # Indexes are created in another script, after the database has been populated.
            dbName = dbName + dbExt
            outputDB = os.path.join(outputFolder, dbName)

            if arcpy.Exists(outputDB):
                arcpy.management.Delete(outputDB)

            if dbExt == ".sqlite":
                #spatial_type = "SPATIALITE" # could also be ST_GEOMETRY
                #spatial_type = "ST_GEOMETRY" # could also be ST_GEOMETRY
                PrintMsg("Creating new database with " + spatial_type + " geometry: \n" + outputDB, 0)

            elif dbExt == ".gpkg":
                # For some reason the tables and views created using sqlite3 are not being registered.
                # Looks like using gpkg_contents table and adding info to .table_name, .data_type, .identifier, .description
                #spatial_type = "GEOPACKAGE_1.3"
                PrintMsg("Creating new geopackage database: \n" + outputDB, 0)

            elif dbExt == ".geodatabase":
                # This parameter is not used by the 'Create Mobile Geodatabase command'
                #spatial_type = "ST_GEOMETRY"
                PrintMsg("Creating new database with " + spatial_type + " geometry: \n" + outputDB, 0)


            if dbExt in (".sqlite", ".gpkg"):
                # Run the Create Table and Create View queries needed to build the SSURGO Template schema
                #  missing 2 required positional arguments: 'bInteger' and 'tabOrder'

                # Create new sqlite or geopackage database
                arcpy.management.CreateSQLiteDatabase(outputDB, spatial_type)

                # Create connection to new sqlite or geopackage database
                conn2, outcur = CreateDbConnection(outputDB, spatial_type)

                if conn2 is None:
                    raise MyError("")

                bNewDB = CreateSQLiteDB(conn2, outcur, outputDB, dbExt, spatial_type, mdQuery, tblValues, bInteger, tabOrder)

                if bNewDB :
                    # Create spatial views
                    dViews = CreateViews(conn2, outcur, databaseType, spatial_type)

                    if 1 == 2 and databaseType == "Spatialite" and spatial_type == "SPATIALITE" and len(dViews) > 0:

                        # Register the spatial views to the view-metadata tables
                        bRegistered = RegisterViews(conn2, outcur, dViews, databaseType, spatial_type)

                else:
                    raise MyError("")
                    del conn2, outcur

                del conn2, outcur

            # Create new mobile database
            elif dbExt == ".geodatabase":
                # Try creating mobile geodatabase from scratch, using all arcpy
                # Creating the tables using sqlite3 fails to register tables?
                # Need to investigate this further because arcpy is slower.
                bNewDB = CreateMobileGDB(outputDB, dTableInfo, bInteger, tabOrder)

                PrintMsg(".", 0)
                PrintMsg("SSURGO attribute tables created for: " + outputDB, 0)

            else:
                err = "Not a valid database name extension (" + dbExt + ")"
                raise MyError(err)


        return True


    except MyError as e:
        PrintMsg(str(e), 2)
        return False

    except:
        errorMsg1(sys.exc_info())
        return False

## ===================================================================================
## MAIN
## ===================================================================================

# Import system modules
import arcpy, os, sys, string, traceback, locale, operator, json, math, random, time
from arcpy import env
sys.tracebacklimit = 1

try:
    if __name__ == "__main__":
        metadataDB = arcpy.GetParameterAsText(0)     # database containing populated SSURGO metadata tables
        outputFolder = arcpy.GetParameterAsText(1)   # folder location where new Template database will be created
        databaseType = arcpy.GetParameterAsText(2)   # Spatialite, Geopackage, Mobile Geodatabase
        spatial_type = arcpy.GetParameterAsText(3)   # ESRI options for CreateSQLiteDB
        bInteger = arcpy.GetParameter(4)             # Use Integer primary keys instead of Text 30
        dbName = arcpy.GetParameterAsText(5)         # Name of new Template database

        dbName, dbExt = os.path.splitext(dbName)
        #outputFolder = env.scratchFolder

        # Hardcode location of inputDB to the ..\TemplateDatabases folder
        scriptPath = __file__
        scriptFolder = os.path.dirname(scriptPath)
        sys.path.insert(0, scriptFolder)  # also saw someone use os.environ['PATH'] = scriptFolder ";" + os.environ['PATH']
        os.environ['PATH'] = scriptFolder + ";" + os.environ['PATH']
        basePath = os.path.dirname(scriptFolder)
        templatePath = os.path.join(basePath, "TemplateDatabases")
        inputDB = os.path.join(templatePath, metadataDB)
        # PrintMsg("inputDB: "  + inputDB, 0)

        import sqlite3  # try using downloaded copy in scriptPath

        if arcpy.Exists(inputDB):
            # database containing SSURGO mdstat* tables exists, proceed
            # ToDo: add a check to make sure all tables are present.
            #
            bProcessed = CreateTemplateDB(inputDB, outputFolder, templatePath, dbName, dbExt, bInteger, spatial_type)

            if bProcessed:
                PrintMsg("Successfully created new Template Database ", 0)

            else:
                PrintMsg("Failed to create new Template Database: " + os.path.join(templatePath, dbName + "." + dbExt), 1)

        else:
            PrintMsg("Failed to find input database with metadata tables: " + inputDB, 2)

    else:
        PrintMsg("Not designed to be called", 2)

except MyError as e:
    PrintMsg(str(e), 2)



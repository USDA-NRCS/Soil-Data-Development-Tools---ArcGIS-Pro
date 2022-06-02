# Create_SQLiteDB_FromMetadata.py
# Requires ArcGIS Pro 2.7 because it now creates a Mobile Geodatabase (.geodatabase)
#
# Create SSURGO schema for new, empty Template SQLite database.
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
# 2021-02-21 This version does not create any sort of an ObjectID, which seems to prevent
# creation of spatial views in an sqlite database. Need to test this hypothesis.
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
        return False

        return ""

## ===================================================================================
## MAIN
## ===================================================================================

# Import system modules
import arcpy, os, sys, string, traceback, locale, operator, json, math, random, time, sqlite3
from arcpy import env
sys.tracebacklimit = 1

try:
    if __name__ == "__main__":
        inputdbName = arcpy.GetParameterAsText(0)
        outputLocation = arcpy.GetParameterAsText(1)
        dbName = arcpy.GetParameterAsText(2)

        dbName, dbExt = os.path.splitext(dbName)
        #outputLocation = env.scratchFolder

        # Hardcode location of inputDB to the ..\TemplateDatabases folder
        scriptPath = __file__
        scriptFolder = os.path.dirname(scriptPath)
        basePath = os.path.dirname(scriptFolder)
        templatePath = os.path.join(basePath, "TemplateDatabases")
        inputDB = os.path.join(templatePath, inputdbName)
        # PrintMsg("inputDB: "  + inputDB, 0)

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
    'mdstattabs', 'mdstattabcols', 'month', 'sdvalgorithm', 'sdvattribute', 'sdvfolder', 'sdvfolderattribute']

        spatialLayers = ['featline', 'featpoint', 'muline', 'mupoint', 'mupolygon', 'sapolygon']

        # Data for pre-populated 'month' table
        monthValues = [(4,'April'),(8,'August'),(12,'December'),(2,'February'),(1,'January'),(7,'July'),(6,'June'),(3,'March'),(5,'May'),(11,'November'),(10,'October'),(9,'September')]

        # Define geometry types for SSURGO featureclasses
        dSpatial = {'featline':'POLYLINE', 'featpoint':'POINT', 'muline':'POLYLINE', 'mupoint':'POINT', 'mupolygon':'POLYGON', 'sapolygon':'POLYGON'}

        # Open database containing just the populated metadata tables
        if arcpy.Exists(inputDB):
            conn = sqlite3.connect(inputDB)
            #conn.enable_load_extension(True)
            #conn.execute("SELECT load_extension('stgeometry_sqlite.dll','SDE_SQL_funcs_init');")
            cur = conn.cursor()

            # Get table info including name, alias, description for use in registering tables to geopackage
            sqlTableInfo = """SELECT tabphyname, tablabel, tabdesc
            FROM mdstattabs
            ORDER BY tabphyname
            ;"""

            tblValues = list()

            for rec in cur.execute(sqlTableInfo):
                tblName, tblAlias, tblDesc = rec
                tnta = (tblName, "attributes", tblAlias, tblDesc)
                tblValues.append(tnta)

            # 02-04-2021 Revised the column_info table in the SQLite_MD table
            # 02-15-2021 table indexes are not properly ordered in the column_info table.
            #   Perhaps I should be using the original query on-the-fly and generating
            #   information for primary and foreign keys as a separate dictionary?
            #
            sqlColumnInfo = """SELECT TC.tabphyname, TC.colsequence, TC.colphyname,
            TC.logicaldatatype, TC.fieldsize, TC.precision, TC.notnull_, TC.domainname, TC.collabel
            FROM mdstattabcols TC
            ORDER BY TC.tabphyname, TC.colsequence ASC
            ; """

            dTableInfo = dict()  # save column info in this dictionary for random access
            dDates = dict()      # save information for all datetime columns to use in alteralias for mobile geodatabases
            lastTable = "xxxx"
            infoList = list()

            for rec in cur.execute(sqlColumnInfo):
                # tblName and colName will later be used to represent child table and child column in foreign keys
                tblName, colSeq, colName, fldType, fldSize, fldPrec, notNull, domain, colAlias = rec

                if fldType == "Date/Time":
                    if not tblName in dDates:
                        dDates[tblName] = [rec]

                    else:
                        dDates[tblName].append(rec)


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

            sqlPrimaryKeys = """SELECT IM.tabphyname, ID.idxcolsequence, IM.idxphyname, IM.uniqueindex, ID.colphyname
            FROM mdstatidxmas AS IM
            INNER JOIN mdstatidxdet AS ID ON (IM.idxphyname = ID.idxphyname) AND (IM.tabphyname = ID.tabphyname)
            WHERE IM.idxphyname LIKE 'PK%'
            ORDER BY IM.tabphyname, IM.idxphyname, ID.idxcolsequence ASC
            ;"""

            dPrimaryKeys = dict()  # Key value is tablename. When accessing data from this dictionary, sort on first item value (colsequence).
            lastTable = "xxxx"
            infoList = list()

            for rec in cur.execute(sqlPrimaryKeys):
                #
                tabphyname, idxcolsequence, idxphyname, uniqueindex, colphyname = rec

                # PrintMsg(str(rec), 1)

                if tabphyname != lastTable:
                    dPrimaryKeys[lastTable] = infoList
                    #PrintMsg("Primary key for " + lastTable + ": " + str(infoList), 0)
                    keyColumns = [colphyname]
                    infoList = [idxphyname, uniqueindex, keyColumns]
                    lastTable = tabphyname

                else:
                    keyColumns.append(colphyname)

            if not lastTable in dPrimaryKeys:
                dPrimaryKeys[lastTable] = infoList

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

            sqlUniqueKeys = """SELECT IM.tabphyname, ID.idxcolsequence, IM.idxphyname, ID.colphyname
            FROM mdstatidxmas AS IM
            LEFT OUTER JOIN mdstatidxdet AS ID ON (IM.idxphyname = ID.idxphyname) AND (IM.tabphyname = ID.tabphyname)
            WHERE IM.idxphyname LIKE 'UC%'
            ORDER BY IM.tabphyname, IM.idxphyname, ID.idxcolsequence ASC
            ;"""

            dUniqueKeys = dict()  # Key value is tablename. When accessing data from this dictionary, sort on first item value (colsequence).
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

            mdQuery = "-- Begin query"
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

                        if dataType in ("String", "Choice"):
                            # Original code
                            fldType = "CHARACTER(" + str(fldSize) + ")"

                            #if colName[-3:] == "key" and fldSize == 30: # new code for integer keys
                            #    fldType = "Integer" # new code for integer keys
                            #    fldSize = None      # new code for integer keys

                            #else:
                            # Original code
                            #    fldType = "CHARACTER(" + str(fldSize) + ")"

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
                        PrintMsg("WARNING! No primary key identified for table: " + tblName, 1)


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
                    mdQuery += "\n--"

                else:
                    raise MyError("dTableInfo is missing data for " + tbl)


            msg = "-- End query"
            mdQuery += msg

            conn.close()

            # End of the 'CREATE TABLE' query

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

            # Create a new sqlite database and then execute the 'CREATE TABLE' query
            # Indexes are created in another script, after the database has been populated.
            dbName = dbName + dbExt
            outputDB = os.path.join(outputLocation, dbName)

            if arcpy.Exists(outputDB):
                arcpy.management.Delete(outputDB)

            PrintMsg("Begin process of creating " + outputDB, 0)

            # Begin sqlite or geopackage option
            if dbExt in (".sqlite", ".gpkg"):

                if dbExt == ".sqlite":
                    spatial_type = "SPATIALITE" # could also be ST_GEOMETRY
                    #spatial_type = "ST_GEOMETRY" # could also be ST_GEOMETRY
                    PrintMsg("Creating new database with " + spatial_type + " geometry: " + outputDB, 0)

                elif dbExt == ".gpkg":
                    # For some reason the tables and views created using sqlite3 are not being registered.
                    # Looks like using gpkg_contents table and adding info to .table_name, .data_type, .identifier, .description
                    spatial_type = "GEOPACKAGE_1.3"
                    PrintMsg("Creating new geopackage database: " + outputDB, 0)

                # For sqlite or geopackage, create the attribute tables directly,
                # using the query generated from the metadata tables
                #
                # More than one way to create an sqlite database.

                # 1. Use arcpy command
                arcpy.management.CreateSQLiteDatabase(outputDB, spatial_type)

                # 2. or just connect to a non-existent database and it will be created
                conn2 = sqlite3.connect(outputDB)

                outcur = conn2.cursor()
                outcur.executescript(mdQuery)
                conn2.commit()

                # Pre-populate month table
                outcur.executemany('INSERT INTO month VALUES (?,?)', monthValues)
                conn2.commit()

                # For a geopackage, we need to register each table to the gpkg_contents table or
                # else ArcGIS will not find them.
                if dbExt == ".gpkg":

                    if len(tblValues) == (6 + len(tabOrder)):
                        # make sure that there is a value for each table. Quick check just compares counts.
                        # tblValues includes the 6 spatial layers
                        queryRegisterTables = "INSERT INTO gpkg_contents (table_name, data_type, identifier, description) VALUES(?, ?, ?, ?)"
                        outcur.executemany(queryRegisterTables, tblValues)
                        conn2.commit()

                    else:
                        PrintMsg("Length of tblValues != tabOrder: " + str(len(tblValues)) + " .. " + str(len(tabOrder)), 2)

                # do I need to delete outcur?
                conn2.close
                #PrintMsg("Output database: " + outputDB, 0)

            # end of sqlite, gpkg option


            # Begin mobile database option
            elif dbExt == ".geodatabase":
                # First create a temporary SQLite database and create attribute
                # tables in it. Then copy the tables from sqlite to mobile geodatabase.
                # Pretty clunky, but the sqlite3

                # Use [newDB, tabOrder, dTableInfo lists] to create table

                ## Try creating mobile geodatabase from scratch, using all arcpy
                ##
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

                    for colInfo in tblInfos:

                        colCnt -= 1
                        colseq, colName, dataType, fldSize, fldPrec, notNull, domain, colAlias = colInfo

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


##                tmpName = "tmp_SSURGO.sqlite"
##                tmpDB = os.path.join(env.scratchFolder, tmpName)
##
##                if arcpy.Exists(tmpDB):
##                    arcpy.Delete_management(tmpDB)
##
##                PrintMsg(".", 0)
##
##
##                PrintMsg("Using temporary SQLite database to build schema for a mobile geodatabase: " + tmpDB, 0)
##
##
##                # Tried using in in-memory workspace instead, but could not figure
##                # out how to make it visible to ArcGIS Pro.
##                PrintMsg("Created temporary sqlite database and running CREATE TABLE query", 0)
##                conn2 = sqlite3.connect(tmpDB)
##                outcur = conn2.cursor()
##                outcur.executescript(mdQuery)
##                conn2.commit()
##
##                # Pre-populate month table for mobile geodatabase.
##                outcur.executemany('INSERT INTO month VALUES (?,?)', monthValues)
##                conn2.commit()
##
##                conn2.close
##                #PrintMsg("Output database: " + outputDB, 0)
##
##                env.workspace = tmpDB
##                sqlTables = arcpy.ListTables()
##
##                if len(sqlTables) == 0:
##                    PrintMsg("Tables not found in " + tmpDB, 2)
##                    raise MyError(err)
##
##                PrintMsg("Found " + str(len(sqlTables)) + " new SQLite tables", 0)
##
##
##                PrintMsg("Creating new output database as ESRI Mobile geodatabase", 0)
##                arcpy.management.CreateMobileGDB(os.path.dirname(outputDB), os.path.basename(outputDB))
##
##                # Copy SSURGO attribute tables from SQLite database to ESRI Mobile Geodatabase,
##                # using arcpy Copy command.
##
##
##
##                #PrintMsg(".\tdDates: " + str(dDates), 0)
##
##                PrintMsg("Copying temporary SQLite tables to new Mobile Geodatabase: " + outputDB, 0)
##
##                for tblName in sqlTables:
##                    newName = tblName[5:]
##                    PrintMsg(".\tCopying empty " + tblName + " table to " + newName, 0)
##                    arcpy.management.Copy(tblName, os.path.join(outputDB, tblName))

            # end of .geodatabase option

                PrintMsg(".", 0)
                PrintMsg("SSURGO attribute tables created for: " + outputDB, 0)

            else:
                err = "Not a valid database name extension (" + dbExt + ")"
                raise MyError(err)


            env.workspace = outputDB



        else:
            PrintMsg("Failed to find input: " + inputDB, 2)

    else:
        PrintMsg("Not designed to be called", 2)

except MyError as e:
    PrintMsg(str(e), 2)



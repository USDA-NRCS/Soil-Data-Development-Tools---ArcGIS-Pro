# gSSURGO_MapunitAggregation4.py
#
# Trying to extract aggregation functionality into a separate script
# Python 3.6.10
#
# 2020-11-10
#
# THINGS TO DO:
#
# Test the input MUPOLYGON featurelayer to see how many polygons are selected when compared
# to the total in the source featureclass. If there is a significant difference, consider
# applying a query filter using AREASYMBOL to limit the size of the master query table.
#
# 0. Need to look at WTA for Depth to Any Restrictive Layer. Customer reported problem. The
#    201 values are being used in the weighting.
#
# 1.  Aggregation method "Weighted Average" can now be used for non-class soil interpretations.
#
# 2.   "Minimum or Maximum" and its use is now restricted to numeric attributes or attributes
#   with a corresponding domain that is logically ordered.
#
# 3.  Aggregation method "Absence/Presence" was replaced with a more generalized version
# thereof, which is referred to as "Percent Present".  Up to now, aggregation method
# "Absence/Presence" was supported for one and only one attribute, component.hydricrating.
# Percent Present is a powerful new aggregation method that opens up a lot of new possibilities,
# e.g. "bedrock within two feel of the surface".
#
# 4.  The merged aggregation engine now supports two different kinds of horizon aggregation,
# "weighted average" and "weighted sum".  For the vast majority of horizon level attributes,
# "weighted average" is used.  At the current time, the only case where "weighted sum" is used is
# for Available Water Capacity, where the water holding capacity needs to be summed rather than
# averaged.

# 5.  The aggregation process now always returns two values, rather than one, the original
# aggregated result AND the percent of the map unit that shares that rating.  For example, for
# the drainage class/dominant condition example below, the rating would be "Moderately well
# drained" and the corresponding map unit percent would be 60:
#
# 6.  A horizon or layer where the attribute being aggregated is null will now never contribute
# to the final aggregated result.  There # was a case for the second version of the aggregation
# engine where this was not true.
#
# 7.  Column sdvattribute.fetchallcompsflag is no longer needed.  The new aggregation engine was
# updated to know that it needs to # include all components whenever no component percent cutoff
# is specified and the aggregation method is "Least Limiting" or "Most # Limiting" or "Minimum or Maximum".
#
# 8.  For aggregation methods "Least Limiting" and "Most Limiting", the rating will be set to "Unknown"
# if any component has a null # rating, and no component has a fully conclusive rating (0 or 1), depending
# on the type of rule (limitation or suitability) and the # corresponding aggregation method.
#
# This is the version where I want to reduce or eliminate the use of the arcpy library
#
# Big ticket items will be using open source drivers and elimination of arcpy data access cursors
# Original script has 100 instances of data access cursors that will need to be replaced.
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
def errorMsg1():
    # Capture system error from traceback and then exit
    #
    try:
        sys.tracebacklimit = 1
        PrintMsg("Current function 1 : " + sys._getframe().f_code.co_name, 1)

        excInfo = sys.exc_info()

        # PrintMsg("Got excInfo object which is a tuple that should contain 3 values", 0)
        # 0: type gets the type of the exception being handled (a subclass of BaseException)
        # 1: value gets the exception instance (an instance of the exception type)
        # 2: traceback gets a traceback object which encapsulates the call stack at the point where the exception originally occurred

        if not excInfo is None:

            if len(excInfo) >= 3:
                errType = str(excInfo[0])
                PrintMsg("errType" + errType, 1)
                errValue = excInfo[1]
                PrintMsg("errValue" + errType + "; " + str(errValue), 1)
                errTB = excInfo[2]
                #PrintMsg("" + errType + "; " + str(errValue) + "; " + str(errTB), 1)

                if not errTB is None:
                    #PrintMsg("Current function 9 : " + sys._getframe().f_code.co_name, 1)
                    try:

                        msgType, msgValue, msgTB = errTB.format_exception(errType, errValue, errTB, limit=1, chain=True)

                    except:
                        msgType, msgValue, msgTB = ("NA", "NA", "NA")

                    if msgValue is not None and msgTB.strip() != "SystemExit: 0":
                        # Skip traceback if this was raised as a custom error
                        msgList = msgValue.replace("\n", " ").split(", ")

                        #PrintMsg("msgList: " + str(msgList), 1)

                        if len(msgList) == 4:
                            errMsg = msgList[0]
                            errScript = msgList[1]
                            errLine = msgList[2]
                            errModule = msgList[3]

                            PrintMsg("Current function 14 : " + sys._getframe().f_code.co_name, 1)
                            msgValue = errMsg + "\n" + errModule + "\t" + errLine + "\n" + errScript

                            PrintMsg(".", 0)
                            PrintMsg(msgTB, 2)
                            PrintMsg(msgValue, 2)

                    PrintMsg("ErrorMsg1 ended up with: " + msgTB, 0)

                else:
                    PrintMsg("Traceback object is null", 1)

            else:
                PrintMsg("excInfo has data, but only " + str(len(excInfo)) + " items", 2)

        else:
            PrintMsg("excInfo is None", 2)

        del excInfo

    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
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

    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return "???"

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
        return "???"


## ===================================================================================
def ErrorTest():
    #
    # Error handling test
    # x = 15.0 / 0
    x = "a" + 10

    return

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

    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return ""

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

        return ""

## ===================================================================================
def BadTable(tbl):
    # Make sure the table has data
    #
    # If has contains one or more records, return False (not a bad table)
    # If the table is empty, return True (bad table)

    try:
        if not arcpy.Exists(tbl):
            return True

        recCnt = int(arcpy.GetCount_management(tbl).getOutput(0))

        if recCnt > 0:
            return False

        else:
            return True

    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return True

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

        return True

## ===================================================================================
def SortData(muVals, a, b, sortA, sortB):
    # Input muVals is a list of lists to be sorted. Each list must have contain at least two items.
    # Input 'a' is the first item index in the sort order (integer)
    # Item 'b' is the second item index in the sort order (integer)
    # Item sortA is a bookean for reverse sort
    # Item sortB is a boolean for reverse sort
    # Perform a 2-level sort by then by item i, then by item j.
    # Return a single list

    try:
        #PrintMsg("muVals: " + str(muVals), 1)

        if len(muVals) > 0:
            muVal = sorted(sorted(muVals, key = lambda x : x[b], reverse=sortB), key = lambda x : x[a], reverse=sortA)[0]

        else:
            muVal = muVals[0]

        #PrintMsg(str(muVal) + " <- " + str(muVals), 1)

        return muVal

    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return []

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
        return []


## ===================================================================================
def SortData0(muVals):
    # Sort by then by item 1, then by item 0 a list of tuples containing comppct_r and rating value or index and return a single tuple

    try:
        #PrintMsg("muVals: " + str(muVals), 1)

        if len(muVals) > 0:
            if tieBreaker == dSDV["tiebreakhighlabel"]:
                # return higher value
                muVal = sorted(sorted(muVals, key = lambda x : x[1], reverse=True), key = lambda x : x[0], reverse=True)[0]

            elif tieBreaker == dSDV["tiebreaklowlabel"]:
                muVal = sorted(sorted(muVals, key = lambda x : x[1], reverse=False), key = lambda x : x[0], reverse=True)[0]

            else:
                muVal = (None, None)

        else:
            muVal = [None, None]

        #PrintMsg("\tReturning " + str(muVal) + " from: " + str(muVals), 1)

        return muVal


    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return []

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
        return []

## ===================================================================================
def ValidateName(inputName):
    # Remove characters from file name or table name that might cause problems
    try:
        #PrintMsg("Validating input table name: " + inputName, 1)
        f = os.path.basename(inputName)
        db = os.path.dirname(inputName)
        validName = ""
        validChars = "_.abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        lastChar = "."
        charList = list()

        for s in f:
            if s in validChars:
                if  not (s == "_" and lastChar == "_"):
                    charList.append(s)

                elif lastChar != "_":
                    lastChar = s

        validName = "".join(charList)

        return os.path.join(db, validName)

    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return ""

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

        try:
            arcpy.RemoveJoin_management(inputLayer, outputTbl)
            return ""

        except:
            return ""

## ===================================================================================
def ReadTable(ds, tblName, flds, filterQuery, sql):
    # Read target table using specified fields and optional sql
    # Other parameters will need to be passed or other functions created
    # to handle aggregation methods and tie-handling
    # ReadTable(dSDV["attributetablename"].upper(), flds, primSQL, level, sql)
    try:
        # bVerbose = True

        if bVerbose:
            PrintMsg("Current function : " + sys._getframe().f_code.co_name, 1)
            PrintMsg(60 * "*", 1)
            PrintMsg("ReadTable: " + tblName + ", Fields: " + str(flds), 1)
            PrintMsg("WhereClause: " + str(filterQuery), 1)
            PrintMsg("SqlClause: " + str(sql), 1)

        arcpy.SetProgressorLabel("Reading input data (" + tblName.lower() +")")
        start = time.time()

        # Create dictionary to store data for this table
        dTbl = dict()

        # Open table using OGR methods
        iCnt = 0
        inputTbl = ds.GetLayerByName(tblName)

        if inputTbl is None:
            err = "Failed to open " + tblName + " table"
            raise MyError(err)

        else:
            PrintMsg("Got table object for " + tblName, 1)

        inputTbl.SetAttributeFilter(filterQuery)

        # OGR. GetFeatureCount always returns the count for all records, not the selected set.
        # Only iteration using GetNextFeature will use the filter.
        recCnt = 0
        feat = inputTbl.GetNextFeature()

        if feat is None:
            err = "Failed to select any records in " + tblName + " using filterQuery: " + filterQuery
            raise MyError(err)

        while feat is not None:
            rec = list()

            for fld in flds:
                rec.append(feat.GetField(fld))

            val = list(rec[1:])  # assuming here that the first item is the key field and the rest are data

            try:
                dTbl[rec[0]].append(val)

            except:
                dTbl[rec[0]] = [val]

            feat = inputTbl.GetNextFeature()
            recCnt += 1

        inputTbl.ResetReading()
        del inputTbl

        if bVerbose:
            theMsg = "Processed " + Number_Format(recCnt, 0, True) + " " + tblName + " records in " + elapsedTime(start)
            PrintMsg(theMsg, 1)

        return dTbl

    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return dict()

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


        return dict()

## ===================================================================================
def ListMonths():
    # return list of months
    try:
        moList = ['NULL', 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
        return moList

    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return []

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
        return []

## ===================================================================================
def GetAreasymbols(ds, areasymbolList):
    # return a dictionary for AREASYMBOL. Key = LKEY and Value = AREASYMBOL
    # this will allow us to easily get attach areasymbol values to the final rating table, independant of spatial layers
    #
    try:
        #global dAreasymbols
        dAreasymbols = dict()

        if 1 == 1:
            # We have a selection on the inputLayer polygon layer
            # PrintMsg("Getting dictionary of legend keys from the input database", 1)


            if len(areasymbolList) == 0:
                err = "xxx dAreasymbols is not populated"
                raise MyError(err)

            areasymbolList.sort()

            if len(areasymbolList) == 1:
                filterQuery = "areasymbol = '" + areasymbolList[0] + "'"

            else:
                filterQuery = "areasymbol IN ('" + "','".join(areasymbolList) + "')"

            # Now get associated mapunit-legend keys for use in other queries
            #
            tblName = "legend"
            legendTbl = ds.GetLayerByName(tblName)

            if legendTbl is None:
                err = "Failed to open " + tblName + " table"
                raise MyError(err)

            else:
                PrintMsg("Got table object for " + tblName, 1)

            legendTbl.SetAttributeFilter(filterQuery)

            # OGR. GetFeatureCount always returns the count for all records, not the selected set.
            # Only iteration using GetNextFeature will use the filter.
            recCnt = 0
            feat = legendTbl.GetNextFeature()

            if feat is None:
                err = "Failed to select any records in " + tblName + " using filterQuery: " + filterQuery
                raise MyError(err)

            while feat is not None:
                areasym = feat.GetField("areasymbol")
                lkey = feat.GetField("lkey")
                PrintMsg("Record " + str(areasym) + ", " + str(lkey), 1)

                if not lkey in dAreasymbols:
                    dAreasymbols[lkey] = areasym
                    PrintMsg("Added legendkey '" + lkey + "' for dAreasymbols as '" + areasym + "'", 1)

                else:
                    PrintMsg("Skipped legendkey '" + lkey + "' addition to dAreasymbols", 1)

                feat = legendTbl.GetNextFeature()
                recCnt += 1

            legendTbl.ResetReading()
            PrintMsg("Read " + Number_Format(recCnt, 0, True) + " records from " + tblName, 1)

        else:
            # raster layer code
            #
            # For raster layers, get AREASYMBOL from legend table. Not ideal, but alternatives could be much slower.
            #
            # Should test this again using mukeys from raster and get lkey and areasymbol from legend table
            #
            # PrintMsg("Getting list of areasymbols from " + inputTbl + "...", 1)

            if (fcCnt == polyCnt):
                # using entire dataset
                inputTbl = os.path.join(gdb, "LEGEND")

                with arcpy.da.SearchCursor(inputTbl, ["LKEY", "AREASYMBOL"], sql_clause=(None, "ORDER BY areasymbol ASC")) as cur:
                    for rec in cur:
                        # This will fail if Null values exist in the legend table
                        lkey = rec[0]
                        areasym = rec[1]
                        dAreasymbols[lkey] = areasym

            else:
                # using selected set
                dMukeys = dict()

                with arcpy.da.SearchCursor(inputLayer, ["MUKEY"], sql_clause=sqlClause) as cur:  # new code
                    for rec in cur:  # new code
                        mukey = rec[1]
                        dMukeys[mukey] = ''

                with arcpy.da.SearchCursor(inputTbl, ["LKEY", "AREASYMBOL"], sql_clause=(None, "ORDER BY areasymbol ASC")) as cur:
                    for rec in cur:
                        # This will fail if Null values exists in the legend table
                        lkey = rec[0]
                        areasym = rec[1]

                        try:
                            dMukeys[mukey] = lkey
                            dAreasymbols[lkey] = areasym

                        except:
                            pass

        PrintMsg("Returning dAreasymbols: " + str(dAreasymbols), 1)

        return dAreasymbols

    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return dAreasymbols

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

        return dAreasymbols

## ===================================================================================
def GetSDVAtts(ds, sdvAtt, aggMethod, tieBreaker, bFuzzy):
    # Create a dictionary containing SDV attributes for the selected attribute fields
    #
    try:
        # Open sdvattribute table and query for [attributename] = sdvAtt
        dSDV = dict()  # dictionary that will store all sdvattribute data using column name as key
        sdvTableName = "sdvattribute"

        filterQuery = "attributename = '" + sdvAtt + "'"

        if bVerbose:
            PrintMsg("Reading sdvattribute table into dSDV dictionary", 1)

        # OGR. open input soil polygon layer
        # problem. This will just be the featureclass, not the featurelayer with any possible filters or selections
        #
        sdvTbl = ds.GetLayerByName(sdvTableName)

        if sdvTbl is None:
            err = "Failed to open '" + sdvTbl
            raise MyError(err)

        else:
            PrintMsg("Got table object for " + sdvTableName, 1)

        #PrintMsg("Count of sdvattribute table: " + Number_Format(fcCnt, 0, True), 1)
        sdvTbl.SetAttributeFilter(filterQuery)

        # OGR. Get soil polygon layer fields
        sdvDef = sdvTbl.GetLayerDefn()
        sdvFieldNames = list()

        for n in range(sdvDef.GetFieldCount()):
            fDef = sdvDef.GetFieldDefn(n)
            sdvFieldNames.append(fDef.name)

        #PrintMsg("Fields for " + sdvTableName + ": " + ", ".join(sdvFieldNames), 1)


        # OGR. GetFeatureCount always returns the count for all records, not the selected set.
        # Only iteration using GetNextFeature will use the filter.

        feat = sdvTbl.GetNextFeature()

        for fld in sdvFieldNames:
            dSDV[fld] = feat.GetField(fld)

        sdvTbl.ResetReading()
        #PrintMsg("dSDV dictionary: " + str(dSDV), 1)

        # Revise some attributes to accomodate fuzzy number mapping code
        #
        # Temporary workaround for NCCPI. Switch from rating class to fuzzy number

        if dSDV["interpnullsaszeroflag"]:
            bZero = True

        if dSDV["attributetype"].lower() == "interpretation" and (dSDV["effectivelogicaldatatype"].lower() == "float" or bFuzzy == True):
            #PrintMsg("Over-riding attributecolumnname for " + sdvAtt, 1)
            dSDV["attributecolumnname"] = "INTERPHR"

            # WHAT HAPPENS IF I SKIP THIS NEXT SECTION. DOES IT BREAK EVERYTHING ELSE WHEN THE USER SETS bFuzzy TO True?
            # Test is ND035, Salinity Risk%
            # Answer: It breaks my map legend.

            if dSDV["attributetype"].lower() == "interpretation" and dSDV["attributelogicaldatatype"].lower() == "string" and dSDV["effectivelogicaldatatype"].lower() == "float":
                #PrintMsg("\tIdentified " + sdvAtt + " as being an interp with a numeric rating", 1)
                pass

            else:
            #if dSDV["nasisrulename"][0:5] != "NCCPI":
                # This comes into play when user selects option to create soil map using interp fuzzy values instead of rating classes.
                dSDV["effectivelogicaldatatype"] = 'float'
                dSDV["attributelogicaldatatype"] = 'float'
                dSDV["maplegendkey"] = 3
                dSDV["maplegendclasses"] = 5
                dSDV["attributeprecision"] = 2

        # Workaround for sql whereclause stored in sdvattribute table. File geodatabase is case sensitive.
        if dSDV["sqlwhereclause"] is not None:
            sqlParts = dSDV["sqlwhereclause"].split("=")
            #dSDV["sqlwhereclause"] = 'UPPER("' + sqlParts[0] + '") = ' + sqlParts[1].upper()
            if sqlParts[0].find(".") != -1:
                sqlField = sqlParts[0].split(".")[1].strip()

            else:
                sqlField = sqlParts[0].strip()

            dSDV["sqlwhereclause"] = '"' + sqlField + '" = ' + sqlParts[1].title()
            PrintMsg("Fixed case in sqlwhereclause", 1)

        if dSDV["attributetype"].lower() == "interpretation" and bFuzzy == False and dSDV["notratedphrase"] is None:
            # Add 'Not rated' to choice list
            dSDV["notratedphrase"] = "Not rated" # should not have to do this, but this is not always set in Rule Manager

        if dSDV["secondaryconcolname"] is not None and dSDV["secondaryconcolname"].lower() == "yldunits":
            # then this would be units for legend (component crop yield)
            #PrintMsg("Setting units of measure to: " + secCst, 1)
            dSDV["attributeuomabbrev"] = secCst

            #PrintMsg("Using attribute column " + dSDV["attributecolumnname"], 1)

        # Working with sdvattribute tiebreak attributes:
        # tiebreakruleoptionflag (0=cannot change, 1=can change)
        # tiebreaklowlabel - if null, defaults to 'Lower'
        # tiebreaklowlabel - if null, defaults to 'Higher'
        # tiebreakrule -1=use lower  1=use higher
        if dSDV["tiebreaklowlabel"] is None:
            dSDV["tiebreaklowlabel"] = "Lower"

        if dSDV["tiebreakhighlabel"] is None:
            dSDV["tiebreakhighlabel"] = "Higher"

        if tieBreaker == dSDV["tiebreakhighlabel"]:
            #PrintMsg("Updating dAgg", 1)
            dAgg["Minimum or Maximum"] = "Max"

        else:
            dAgg["Minimum or Maximum"] = "Min"
            #PrintMsg("Updating dAgg", 1)

        if aggMethod == "":
            aggMethod = dSDV["algorithmname"]

        if dAgg[aggMethod] != "":
            dSDV["resultcolumnname"] = dSDV["resultcolumnname"] + "_" + dAgg[aggMethod]

        if dSDV["attributeprecision"] is None:
            dSDV["attributeprecision"] = 0

        #PrintMsg("Setting resultcolumn name to: '" + dSDV["resultcolumnname"] + "'", 1)


        return dSDV


    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return dSDV

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

        return dSDV

## ===================================================================================
def GetRuleKey(distinterpTbl, nasisrulename):

    # distinterpmd: rulekey, rulekey
    # cointerp: mrulekey, mrulename, ruledepth=0
    # Need to determine if there is always 1:1 for rulekey and rulename

    try:
        #bVerbose = True
        whereClause = "rulename = '" + nasisrulename + "'"
        ruleKeys = list()

        with arcpy.da.SearchCursor(distinterpTbl, ["rulekey"], where_clause=whereClause) as mCur:
            for rec in mCur:
                ruleKey = rec[0]

                if not ruleKey in ruleKeys:
                    ruleKeys.append(ruleKey)

        if len(ruleKeys) == 1:
            keyString = "('" + ruleKeys[0] + "')"

        else:
            keyString = "('" + "','".join(ruleKeys) + "')"

        if bVerbose:
            PrintMsg("\tSQL for " + nasisrulename + ": " + keyString, 1)

        return keyString

    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return keyString

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


        return keyString

## ===================================================================================
def GetRatingDomain(ds):
    # return list of tiebreak domain values for rating
    # modify this function to use uppercase string version of values
    #
    # The tiebreak domain name is not always used, even when there is a set
    # of domain names for the attribute (eg Conservation Tree and Shrub Group)

    try:
        domainValues = list()

        if dSDV["tiebreakdomainname"] is not None:
            filterQuery = "domainname = '" + dSDV["tiebreakdomainname"] + "' and choiceobsolete = 'No'"
            #sc = (None, "ORDER BY choicesequence ASC")

        else:
            # no domain available, return an empty list
            return []


        # OGR METHOD
        tblName = "mdstatdomdet"
        mdTbl = ds.GetLayerByName(tblName)

        if mdTbl is None:
            err = "Failed to open " + tblName + " table"
            raise MyError(err)

        else:
            PrintMsg("Got table object for " + tblName, 1)

        dValues = dict()

        PrintMsg("Query filter: " + filterQuery, 1)
        mdTbl.SetAttributeFilter(filterQuery)

        # OGR. GetFeatureCount always returns the count for all records, not the selected set.
        # Only iteration using GetNextFeature will use the filter.
        recCnt = 0
        feat = mdTbl.GetNextFeature()

        if feat is None:
            err = "Failed to select any records in " + tblName + " using filterQuery: " + filterQuery
            raise MyError(err)

        fldList = ["choice", "choicesequence"]

        while feat is not None:
            #PrintMsg("Reading record " + str(recCnt) + " from " + tblName, 1)
            seq = feat.GetField("choicesequence")
            val = feat.GetField("choice")
            dValues[seq] = val
            recCnt += 1
            PrintMsg(str(seq) + ". " + str(val), 1)
            feat = mdTbl.GetNextFeature()

        if len(dValues) == 0:
            err = "No domain values retrieved from " + tblName
            raise MyError(err)

        else:
            PrintMsg("dValues: " + str(dValues), 1)

        seqList = sorted(list(dValues.keys()))

        if len(seqList) > 0:
            domainValues = [dValues[i] for i in seqList]
            PrintMsg("Domain values: " + ", ".join(domainValues), 1)

        else:
            PrintMsg("No domain values found for '" + dSDV["tiebreakdomainname"] + "'", 1)

        del mdTbl

        return domainValues

    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return []

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

        return []

## ===================================================================================
def GetValuesFromLegend(dLegend):
    # return list of legend values from dLegend (XML source)
    # modify this function to use uppercase string version of values

    try:
        legendValues = list()

        if len(dLegend) > 0:
            pass
            #dLabels = dLegend["labels"] # dictionary containing just the label properties such as value and labeltext Now a global

        else:

            #PrintMsg("Changing legend name to 'Progressive'", 1)
            #PrintMsg("dLegend: " + str(dLegend["name"]), 1)
            legendValues = list()
            #dLegend["name"] = "Progressive"  # bFuzzy
            dLegend["type"] = "1"

        labelCnt = len(dLabels)     # get count for number of legend labels in dictionary

        #if not dLegend["name"] in ["Progressive", "Defined"]:
        # Note: excluding defined caused error for Interp DCD (Haul Roads and Log Landings)

        if not dLegend["name"] in ["Progressive", "Defined"]:
            # example AASHTO Group Classification
            legendValues = list()      # create empty list for label values

            for order in range(1, (labelCnt + 1)):
                #legendValues.append(dLabels[order]["value"].title())
                legendValues.append(dLabels[order]["value"])

                if bVerbose:
                    PrintMsg("\tAdded legend value #" + str(order) + " ('" + dLabels[order]["value"] + "') from XML string", 1)

        elif dLegend["name"] == "Defined":
            #if dSDV["attributelogicaldatatype"].lower() in ["string", "choice]:
            # Non-numeric values
            for order in range(1, (labelCnt + 1)):
                try:
                    # Hydric Rating by Map Unit
                    legendValues.append(dLabels[order]["upper_value"])
                    legendValues.append(dLabels[order]["lower_value"])

                except:
                    # Other Defined such as 'Basements With Dwellings', 'Land Capability Class'
                    legendValues.append(dLabels[order]["value"])

        return legendValues

    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return []

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

        return []

## ===================================================================================
def CreateInitialTable_Old(outputDriver, tmpDS, allFields, dFieldInfo):
    # Create the empty output table (SDV_Data) that will contain key fields from all levels plus
    # the input rating field
    #
    try:
        bVerbose = True

        if bVerbose:
            PrintMsg("Current function : " + sys._getframe().f_code.co_name, 1)

        # Create dictionary to convert input field data types to OGR types

        flatName = "SDV_Data"
        # from dataclasses import make_dataclass  # trying to create a pandas dataframe record class; but not available until Python 3.7

        try:
            PrintMsg("Deleting existing table: " + flatName, 1)

            bDel = tmpDS.DeleteLayer(flatName)
            PrintMsg("bDel: " + str(bDel), 1)   # Seems to return a zero when it doesn't fail

        except:
            #PrintMsg("Error when trying to delete layer (" + flatName + ")", 1)
            pass

        # In order to create an attribute table without geometry, add these two parameters. Works with GPKG. Have not tested others.
        # srs=None, geom_type=ogr.wkbNone
        #flatTbl = tmpDS.CreateLayer(flatName, srs=None, geom_type=ogr.wkbNone)

##        if flatTbl is None:
##            err = "Failed to create new table: " + flatName
##            raise MyError(err)

        # Add required fields to initial table
        # OGR field types = OFTString (SetWidth()); OFTReal, OFTInteger
        if "LKEY" in allFields:
            allFields.remove("LKEY")

        PrintMsg("Creating SDV_Data table with these fields: ", 1)
        PrintMsg(", ".join(allFields), 1)

        #dfColumns = dict()
        dataTypes = list()

        for fld in allFields:
            # PrintMsg("Getting data type for " + fld, 1)

            fldInfo = dFieldInfo[fld]
            fldType = fldInfo[0]

            if fldType == "TEXT":
                #fType = ogr.OFTString
                fWidth = fldInfo[1]
                dftype = 'object'
                dftype = 'a' + str(fWidth)  # for use with numpy array

            elif fldType == "FLOAT":
                #fType = ogr.OFTReal
                fWidth = ""
                dftype = 'float'
                dftype = 'f8'               # for use with numpy array. Not sure about width

            elif fldType == "SHORT":
                #fType = ogr.OFTInteger
                fWidth = ""
                dftype = 'int'
                dftype = 'i4'               # for use with numpy array.

            else:
                err = "Failed to identify OGR data type for field: " + fld
                raise MyError(err)

            #dfColumns2[fld] = pd.Series(fld, data=None, dtype=dftype, name=fld)
            #dfColumns[fld] = dftype
            dataTypes.append((fld, dftype))

            #columnsList.append(pd.Series(data=None, dtype=dftype, name=fld))

##        for fld in allFields:
##            #columnsList.append(dfColumns2[fld])
##            dfColumns[fld] = []

        if len(dataTypes) == 0:
            err = "Failed to save data types for each field"
            raise MyError(err)

        else:
            PrintMsg("dataType: " + str(dataTypes), 1)

        return dataTypes # instead of returning an ogr table, return a Pandas dataframe.

    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return None

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

        return None


## ===================================================================================
def CreateInitialTable(outputDriver, tmpDS, allFields, dFieldInfo):
    # Create the empty output table (SDV_Data) that will contain key fields from all levels plus
    # the input rating field
    #
    try:
        bVerbose = True

        if bVerbose:
            PrintMsg("Current function : " + sys._getframe().f_code.co_name, 1)

        # Create dictionary to convert input field data types to OGR types

        flatName = "SDV_Data"
        # from dataclasses import make_dataclass  # trying to create a pandas dataframe record class; but not available until Python 3.7

        try:
            PrintMsg("Deleting existing table: " + flatName, 1)

            bDel = tmpDS.DeleteLayer(flatName)
            PrintMsg("bDel: " + str(bDel), 1)   # Seems to return a zero when it doesn't fail

        except:
            #PrintMsg("Error when trying to delete layer (" + flatName + ")", 1)
            pass

        # In order to create an attribute table without geometry, add these two parameters. Works with GPKG. Have not tested others.
        # srs=None, geom_type=ogr.wkbNone
        #flatTbl = tmpDS.CreateLayer(flatName, srs=None, geom_type=ogr.wkbNone)

##        if flatTbl is None:
##            err = "Failed to create new table: " + flatName
##            raise MyError(err)

        # Add required fields to initial table
        # OGR field types = OFTString (SetWidth()); OFTReal, OFTInteger
        if "LKEY" in allFields:
            allFields.remove("LKEY")

        PrintMsg("Creating SDV_Data table with these fields: ", 1)
        PrintMsg(", ".join(allFields), 1)

        #dfColumns = dict()
        dataTypes = list()

        for fld in allFields:
            # PrintMsg("Getting data type for " + fld, 1)

            fldInfo = dFieldInfo[fld]
            fldType = fldInfo[0]

            if fldType == "TEXT":
                #fType = ogr.OFTString
                fWidth = fldInfo[1]
                dftype = 'object'
                dftype = 'a' + str(fWidth)  # for use with numpy array

            elif fldType == "FLOAT":
                #fType = ogr.OFTReal
                fWidth = ""
                dftype = 'float'
                dftype = 'f8'               # for use with numpy array. Not sure about width

            elif fldType == "SHORT":
                #fType = ogr.OFTInteger
                fWidth = ""
                dftype = 'int'
                dftype = 'i4'               # for use with numpy array.

            else:
                err = "Failed to identify OGR data type for field: " + fld
                raise MyError(err)

            #dfColumns2[fld] = pd.Series(fld, data=None, dtype=dftype, name=fld)
            #dfColumns[fld] = dftype
            dataTypes.append((fld, dftype))

            #columnsList.append(pd.Series(data=None, dtype=dftype, name=fld))

##        for fld in allFields:
##            #columnsList.append(dfColumns2[fld])
##            dfColumns[fld] = []

        if len(dataTypes) == 0:
            err = "Failed to save data types for each field"
            raise MyError(err)

        else:
            PrintMsg("dataType: " + str(dataTypes), 1)

        return dataTypes # instead of returning an ogr table, return a Pandas dataframe.

    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return None

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

        return None

## ===================================================================================
def GetMapunitSymbols(gdb):
    # Populate dictionary using mukey and musym
    # This function is for development purposes only and will probably not be
    # used in the final version.

    dSymbols = dict()
    env.workspace = gdb

    try:

        with arcpy.da.SearchCursor("MAPUNIT", ["MUKEY", "MUSYM"]) as mCur:
            for rec in mCur:
                dSymbols[rec[0]] = rec[1]

        return dSymbols

    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return dSymbols

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

        return dSymbols


## ===================================================================================
def CreateOutputTable(tmpDS, flatTbl, outputTbl, dFieldInfo):
    # Create the initial output table that will contain key fields from all levels plus the input rating field
    #
    try:
        if bVerbose:
            PrintMsg("Current function : " + sys._getframe().f_code.co_name, 1)

        # Validate output table name
        outputTbl = ValidateName(outputTbl)

        if outputTbl == "":
            return ""

        # Delete table from prior runs
        if arcpy.Exists(outputTbl):
            arcpy.Delete_management(outputTbl)

        # Create the final output table using flatTbl as a template
        try:
            # arcpy.CreateTable_management(os.path.dirname(outputTbl), os.path.basename(outputTbl), flatTbl)
            arcpy.CreateTable_management(os.path.dirname(outputTbl), os.path.basename(outputTbl))

        except:
            err = "Unable to create table: " + outputTbl
            raise MyError(err)

        # Drop the last column which should be 'attributecolumname' and replace with 'resultcolumname'
        #lastFld = dSDV["attributecolumnname"]

        # Switching to AddField instead of using template table (flatTbl)
        inputFields = [fld.name.upper() for fld in arcpy.Describe(flatTbl).fields if not fld.type.upper() == "OID"]

        # switch attributecolumnname for resultcolumnname
        inputFields[-1] = dSDV["resultcolumnname"].upper()

        excludeFields = ["MUSYM", "COMPNAME", "COKEY", "CHKEY", "HZDEPT_R", "HZDEPB_R", "COMONTHKEY", "LKEY"]

        if dSDV["resultcolumnname"].upper() != "MUNAME":
            excludeFields.append("MUNAME")
            #PrintMsg("ExcludeFields: " + ", ".join(excludeFields), 1)
            newFieldNames = list()
            newFieldInfos = list()

        # Switch from output-as-table to output-as-json

        for fldName in inputFields:

            if not fldName in excludeFields and fldName in dFieldInfo:
                theType = dFieldInfo[fldName][0]
                dataLen = dFieldInfo[fldName][1]
                arcpy.AddField_management(outputTbl, fldName, theType, "", "", dataLen)

                #PrintMsg("\tAdded field '" + fldName + "' to output table", 1)
                newFieldNames.append(fldName)
                newFieldInfos.append([theType, dataLen])

        arcpy.AddIndex_management(outputTbl, "MUKEY", "Indx" + os.path.basename(outputTbl))

        if arcpy.Exists(outputTbl):
            return outputTbl

        else:
            err = "Failed to create output table"
            raise MyError(err)

    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return ""

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

        return ""

## ===================================================================================
def CreateOutputJSON(tmpDS, flatTbl, dFieldInfo, inputFields):
    # Create the JSON 'file' will contain key fields from all levels plus the input rating field
    #
    try:
        if bVerbose:
            PrintMsg("Current function : " + sys._getframe().f_code.co_name, 1)

        # switch attributecolumnname for resultcolumnname
        inputFields[-1] = dSDV["resultcolumnname"].upper()

        PrintMsg("inputFields: " + str(inputFields), 1)

        #excludeFields = ["MUSYM", "COMPNAME", "COKEY", "CHKEY", "HZDEPT_R", "HZDEPB_R", "COMONTHKEY", "LKEY"]
        excludeFields = ["COMPNAME", "COKEY", "CHKEY", "HZDEPT_R", "HZDEPB_R", "COMONTHKEY", "LKEY"]

        if dSDV["resultcolumnname"].upper() != "MUNAME":
            excludeFields.append("MUNAME")

        #PrintMsg("ExcludeFields: " + ", ".join(excludeFields), 1)

        newFieldNames = list()
        newFieldInfos = list()

        for fldName in inputFields:

            if not fldName in excludeFields and fldName in dFieldInfo:
                theType = dFieldInfo[fldName][0]
                dataLen = dFieldInfo[fldName][1]

                PrintMsg("\tAdded field '" + fldName + "' to output ", 1)
                newFieldNames.append(fldName)
                newFieldInfos.append([theType, dataLen])

        jsonData = list()
        jsonData.append(newFieldNames)
        jsonData.append(newFieldInfos)

        return jsonData

    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return []

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

        return []

## ===================================================================================
def AddNewFields(newTable, columnNames, columnInfo):
    # Create the empty output table using Soil Data Access table metadata
    #
    # ColumnNames and columnInfo come from the Attribute query JSON string
    # MUKEY would normally be included in the list, but it should already exist in the output featureclass
    #
    try:
        # Dictionary: key is SQL Server data types and value is FGDB data type
        dType = dict()

        dType["int"] = "long"
        dType["bigint"] = "long"
        dType["smallint"] = "short"
        dType["tinyint"] = "short"
        dType["bit"] = "short"
        dType["varbinary"] = "blob"
        dType["nvarchar"] = "text"
        dType["varchar"] = "text"
        dType["char"] = "text"
        dType["datetime"] = "date"
        dType["datetime2"] = "date"
        dType["smalldatetime"] = "date"
        dType["decimal"] = "double"
        dType["numeric"] = "double"
        dType["float"] = "double"
        dType["udt"] = "text"  # probably geometry or geography data
        dType["xml"] = "text"

        dType2 = dict()
        dType2["ProviderSpecificDataType"] = "Microsoft.SqlServer.Types.SqlGeometry"

        # numeric type conversion depends upon the precision and scale
        dType["numeric"] = "float"  # 4 bytes
        dType["real"] = "double" # 8 bytes

        # Introduce option for field aliases
        # Use uppercase physical name as key
        dAliases = dict()
        dAliases["MU_KFACTOR"] = "Kw"
        dAliases["SOIL_SLP_LGTH_FCTR"] = "LS"
        dAliases["MU_TFACTOR"] = "T"
        dAliases["NA1"] = "C"
        dAliases["MU_IFACTOR"] = "WEI"
        dAliases["SOIL_LCH_IND"] = "LCH"
        dAliases["LONG_LEAF_SUIT_IND"] = "LLP"
        dAliases["WESL_IND"] = "WESL"
        dAliases["NA2"] = "Water EI"
        dAliases["MUKEY"] = "mukey"
        dAliases["NA3"] = "Wind EI"
        dAliases["NCCPI"] = "NCCPI"
        dAliases["NA4"] = "RKLS"
        dAliases["CFACTOR"] = "CFactor"
        dAliases["RFACTOR"] = "RFactor"
        dAliases["NIRRCAPCLASS"] = "NIrrCapClass"
        dAliases["POLY_ACRES"] = "PolyAcres"

        #PrintMsg("Adding new fields (" + str(columnInfo) + ") to " + newTable, 1)

        # Iterate through list of field names and add them to the output table
        i = 0

        # ColumnInfo contains:
        # ColumnOrdinal, ColumnSize, NumericPrecision, NumericScale, ProviderType, IsLong, ProviderSpecificDataType, DataTypeName
        # PrintMsg("FieldName, Length, Precision, Scale, Type", 1)
        # Field soilgeog: [u'ColumnOrdinal=4', u'ColumnSize=2147483647', u'NumericPrecision=255', u'NumericScale=255', u'ProviderType=Udt', u'IsLong=True', u'ProviderSpecificDataType=Microsoft.SqlServer.Types.SqlGeometry', u'DataTypeName=tempdb.sys.geography']

        joinFields = list()

        # Get list of existing fields iin newTable
        existingFlds = [fld.name.upper() for fld in arcpy.Describe(newTable).fields]

        for i, fldName in enumerate(columnNames):

            if fldName is None or fldName == "":
                raise MyError("Query for " + os.path.basenaame(newTable) + " returned an empty fieldname (" + str(columnNames) + ")")

            vals = columnInfo[i].split(",")
            length = int(vals[1].split("=")[1])
            precision = int(vals[2].split("=")[1])
            scale = int(vals[3].split("=")[1])
            dataType = dType[vals[4].lower().split("=")[1]]
            #PrintMsg("\t" + fldName + " is returned as a " + vals[4].lower().split("=")[1] + " SQL ProviderType", 1)

            if fldName.upper() in dAliases:
                alias = dAliases[fldName.upper()]

            else:
                alias = fldName

            if fldName.upper() == "MUKEY":
                # switch to SSURGO standard TEXT 30 chars
                dataType = "text"
                length = 30
                precision = ""
                scale = ""

            if fldName.upper() == "MU_IFACTOR":
                # switch to integer so that map legend sorts numerically instead of alphabetically
                dataType = "short"
                length = 0
                precision = ""
                scale = ""

            if not fldName.upper() in existingFlds and not dataType == "udt" and not fldName.upper() in ["WKTGEOM", "WKBGEOG", "SOILGEOG"]:
                arcpy.AddField_management(newTable, fldName, dataType, precision, scale, length, alias)
                joinFields.append(fldName)

                #if fldName.lower() in ["mu_kfactor", "mu_ifactor"]:
                #    PrintMsg("Setting " + fldName + " for " + os.path.basename(newTable) + " to " + dataType, 1)
                #    PrintMsg("\t" + fldName + " is returned as a " + vals[4].lower().split("=")[1] + " SQL ProviderType", 1)

        if arcpy.Exists(newTable):
            #PrintMsg("New table fields: " + ", ".join(joinFields), 1)
            return joinFields

        else:
            return []

    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return []

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

        return []

## ===============================================================================================================
def GetTableKeys(templateDB):
    #
    # Retrieve physical and alias names from mdstatidxdet table and assigns them to a blank dictionary.
    # tabphyname, idxphyname, idxcolsequence, colphyname
    # indxphyname prefixes: PK_, DI_

    try:
        tableKeys = dict()  # key = table name, values are a list containing [primaryKey, foreignKey]

        # Open mdstattabs table containing information for other SSURGO tables
        theMDTable = "mdstatidxdet"
        env.workspace = templateDB

        # Get primary and foreign keys for each table using mdstatidxdet table.
        #
        if arcpy.Exists(os.path.join(templateDB, theMDTable)):

            fldNames = ["tabphyname", "idxphyname", "colphyname"]
            wc = "idxphyname NOT LIKE 'UC_%'"
            #wc = ""

            with arcpy.da.SearchCursor(os.path.join(templateDB, theMDTable), fldNames, wc) as rows:

                for row in rows:
                    # read each table record and assign 'tabphyname' and 'tablabel' to 2 variables
                    tblName, indexName, columnName = row
                    #PrintMsg(str(row), 1)

                    if indexName[0:3] == "PK_":
                        # primary key
                        if tblName in tableKeys:
                            tableKeys[tblName][0] = columnName

                        else:
                            tableKeys[tblName] = [columnName, None]

                    elif indexName[0:3] == "DI_":
                        # foreign key
                        if tblName in tableKeys:
                            tableKeys[tblName][1] = columnName

                        else:
                            tableKeys[tblName] = [None, columnName]

            del theMDTable

            return tableKeys

        else:
            # The mdstattabs table was not found
            err = "Missing mdstattabs table"
            raise MyError(err)
            return dict()

    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return dict()

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

        return dict()


## ===================================================================================
def CreateRatingTable1(ds, tblList, sdvTbl, dataTypes, allFields, dAreasymbols):
#def CreateRatingTable1(ds, tblList, sdvTbl, dfInitial, allFields, dAreasymbols):
#def CreateRatingTable1(ds, tblList, sdvTbl, flatTbl, allFields, dAreasymbols):
    # Create level 1 table (using mapunit only). Output table is SDV_Data (flatTbl)
    # As of 11-07-2020 this seems to be working. Will see if I can use it as a basis for the other functions.
    #
    try:
        #bVerbose = True

        arcpy.SetProgressorLabel("Saving all relevant data to a single query table")

        if bVerbose:
            PrintMsg("Current function : " + sys._getframe().f_code.co_name, 1)

        if "LKEY" in allFields:
            allFields.remove("LKEY")

        if bVerbose:
            # Read mapunit table and populate initial table
            #PrintMsg("Using input fields: " + ", ".join(dFields["MAPUNIT"]), 1)
            PrintMsg("CreateRatingTable1: using mapunit where_clause: " + legendQuery + " and sql_clause: " + str(dSQL["MAPUNIT"]) + " \n", 1)
            #PrintMsg("dFields: " + str(dFields["MAPUNIT"]), 1)
            #PrintMsg("allFields: " + str(allFields), 1)

        # Reading mapunit table using OGR
        tblName = "mapunit"
        muTable = ds.GetLayerByName(tblName)

        if legendQuery != "":
            PrintMsg("Using query filter (" + legendQuery + ") with table: " + tblName, 0)
            time.sleep(10)
            muTable.SetAttributeFilter(legendQuery)

        # Create new dataframe. This will be the pandas dataframe equivalent of SDV_Data table.
        # Convert outputData to an array
        #PrintMsg("Creating new array based on mapunit count", 1)
        muCnt = muTable.GetFeatureCount()
        dataArray = np.zeros((muCnt, ), dtype=dataTypes)
        PrintMsg("Created new, empty array using these datatypes: \n" + str(dataTypes) + "\n", 1)
        #dfRaw = pd.DataFrame(dataArray)
        #PrintMsg(". ", 1)
        #PrintMsg("Created new dataframe: \n" + str(dfRaw.info()), 1)

        recCnt = 0
        outputData = list()       # list of tuples
        outputSeries = list()     # list of series
        rec = muTable.GetNextFeature()

        while rec is not None:
            recCnt += 1              # increment record counter
            #PrintMsg("Processing table " + tblName + " record " + str(recCnt), 0)
            lkey = rec.GetField("lkey")
            areasym = dAreasymbols[lkey]
            newrec = [areasym]

            for fld in allFields[1:]:                        # skip areasymbol, but iterate through each of the input values from this record
                newrec.append(rec.GetField(fld))

            outputData.append(tuple(newrec))
            series = pd.Series( newrec, index=dfRaw.columns )
            outputSeries.append(series)
            #PrintMsg("newrec: " + str(newrec), 1)
            rec = muTable.GetNextFeature()

        time.sleep(1)

##        # Create new dataframe. This will be the pandas dataframe equivalent of SDV_Data table.
##        # Convert outputData to an array
##        PrintMsg(".    Creating new array", 1)
##        dataArray = np.zeros((len(outputData), ), dtype=dataTypes)
        dataArray[:] = outputData

        # Try using dataframe.append(series)...
        #dfNew = dfRaw.append(outputSeries, ignore_index=True)

        # if numeric data, get min-max values
        ratingType = dataTypes[-1][1][0]  # first character of rating np.datatype
        #tShape = dataArray.shape
        #PrintMsg("shape " + str(tShape), 1)
        colIndx = len(dataTypes) - 1
        PrintMsg(str(colIndx) + " is the column index for the dataArray", 1)

        if ratingType in ['i', 'f']:
            iMin = np.amin(dataArray[:, colIndx])
            iMax = np.amax(dataArray[:, colIndx])
            dStats["range"] = (iMin, iMax)
            PrintMsg(", ".join(str(dStats)), 1)

        else:
            PrintMsg(str(dataArray), 1)
            ratingsArray = dataArray[:, -1]
            uniqueValues = np.unique(ratingsArray).tolist()
            iUnique = len(uniqueValues)
            PrintMsg("Number of unique values: " + str(iUnique), 1)
            PrintMsg(", ".join(uniqueValues), 1)

        # dfRaw = pd.DataFrame(dataArray)
        PrintMsg(str(dataTypes), 1)
        PrintMsg(".", 1)
        PrintMsg(str(dfRaw), 1)
        PrintMsg("Finished processing table " + sdvTbl, 0)

        muTable.ResetReading()

        muCnt = dataArray.size
        PrintMsg("rawData dataframe populated with " + Number_Format(muCnt, 0, True) + " records", 1)

        del muTable

        return dfNew

    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return None

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

        return False

## ===================================================================================
def CreateRatingTable1S(ds, tblList, sdvTbl, dTbl, flatTbl, allFields, dAreasymbols):
    # Create level 2 table (mapunit, sdvTbl)
    #

    try:
        #bVerbose = True

        arcpy.SetProgressorLabel("Saving all relevant data to a single query table")

        if bVerbose:
            PrintMsg("Current function : " + sys._getframe().f_code.co_name, 1)

        if "LKEY" in allFields:
            allFields.remove("LKEY")

        if bVerbose:
            # Read mapunit table and populate initial table
            #PrintMsg("Using input fields: " + ", ".join(dFields["MAPUNIT"]), 1)
            PrintMsg("CreateRatingTable1: using mapunit where_clause: " + legendQuery + " and sql_clause: " + str(dSQL["MAPUNIT"]) + " \n", 1)
            #PrintMsg("dFields: " + str(dFields["MAPUNIT"]), 1)
            #PrintMsg("allFields: " + str(allFields), 1)

        # Reading mapunit table using OGR
        tblName = "mapunit"
        muTable = ds.GetLayerByName(tblName)

        if legendQuery != "":
            PrintMsg("Using query filter (" + legendQuery + ") against " + tblName, 0)
            time.sleep(10)
            muTable.SetAttributeFilter(legendQuery)
            PrintMsg("Set query filter successfully", 0)

        recCnt = 0
        rec = muTable.GetNextFeature()

        # Writing SDV_Data table using OGR
        # PrintMsg("Reading mapunit table", 0)

        if "AREASYMBOL" in allFields:
            allFields.remove("AREASYMBOL")

        outputDefn = flatTbl.GetLayerDefn()

        testRec = list()  # used to test input data

        while rec is not None:
            recCnt += 1              # increment record counter
            lkey = rec.GetField("lkey")
            mukey = rec.GetField("mukey")
            areasym = dAreasymbols[lkey]

            try:
                sdvrecs = dTbl[mukey]
                sdvrec = sdvrecs[0][0]

            except:
                PrintMsg("No match for mukey: " + mukey, 1)
                sdvrec = ""

            testRec = [areasym]

            # create new output record
            newrec = ogr.Feature(outputDefn)
            newrec.SetField("areasymbol", areasym)

            for fld in allFields[:-1]:                        # skip areasymbol, but iterate through each of the input values from this record
                newrec.SetField(fld, rec.GetField(fld))
                testRec.append(rec.GetField(fld))

            testRec.append(sdvrec)
            PrintMsg("testRec: " + str(testRec), 1)
            newrec.SetField(allFields[-1], sdvrec)
            flatTbl.CreateFeature(newrec)
            rec = muTable.GetNextFeature()

        PrintMsg("Finished processing table " + sdvTbl, 0)

        time.sleep(1)
        muTable.ResetReading()
        flatTbl.ResetReading()

        #if bVerbose:
        muCnt = flatTbl.GetFeatureCount()
        PrintMsg("SDV_Data table populated with " + Number_Format(muCnt, 0, True) + " records", 1)

        del muTable
        del flatTbl

        return True

    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return False

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

        return False

## ===================================================================================
def CreateRatingTable2(ds, sdvTbl, dComponent, flatTbl, dAreasymbols):
    # Populate SDV_Data table using (mapunit, component) where rating is in the component table,
    # which means there is only one rating value per component
    #
    try:
        #bVerbose = True

        arcpy.SetProgressorLabel("Saving all relevant data to a single query table")

        if bVerbose:
            PrintMsg("Current function : " + sys._getframe().f_code.co_name, 1)

        if bVerbose:
            PrintMsg(".", 1)
            PrintMsg("Using mapunit fields: " + ", ".join(dFields["MAPUNIT"]), 1)
            PrintMsg("Using initial table fields: " + ", ".join(allFields), 1)
            PrintMsg("Using sql_clause: " + str(dSQL["MAPUNIT"]) + " \n", 1)
            PrintMsg("Using where_clause: '" + legendQuery + "'", 1)
            PrintMsg("Output table: " + os.path.basename(flatTbl.GetName()), 1)
            PrintMsg("" + ", ".join(allFields) + " \n ", 1)
            #PrintMsg(80 * "=", 1)

        # Get mapunit table
        muTable = ds.GetLayerByName("mapunit")

        # Get SDV_Data table
        sdvData = tmpDS.GetLayerByName("SDV_Data")  # Created by CreateInitialTable function

        # Reading mapunit table using OGR
        tblName = "mapunit"
        muTable = ds.GetLayerByName(tblName)

        if legendQuery != "":
            PrintMsg("Using query filter (" + legendQuery + ") against " + tblName, 0)
            time.sleep(10)
            muTable.SetAttributeFilter(legendQuery)
            PrintMsg("Set query filter successfully", 0)

        recCnt = 0
        rec = muTable.GetNextFeature()

        # Writing SDV_Data table using OGR
        PrintMsg("Reading mapunit table", 0)

        # list of null values for missing component data
        missingComp = dMissing["COMPONENT"]
        outputDefn = flatTbl.GetLayerDefn()
        #testRec = list()  # used to test input data

        while rec is not None:
            recCnt += 1              # increment record counter
            #PrintMsg("Processing table " + tblName + " record " + str(recCnt), 0)
            lkey = rec.GetField("lkey")
            mukey = rec.GetField("mukey")
            musym = rec.GetField("musym")
            muname = rec.GetField("muname")
            areasym = dAreasymbols[lkey]

            try:
                # corecs: [['16641198', 'Penden', 90, 'Well drained'], ['16641199', 'Canlon', 5, 'Somewhat excessively drained'], ['16641200', 'Uly', 5, 'Well drained']]
                coRecs = dComponent[mukey]

                for coVals in coRecs:
                    newVals = [areasym, mukey, musym, muname]
                    newVals.extend(coVals)  # should be cokey, compname, comppct_r, rating
                    newrec = ogr.Feature(outputDefn)

                    # Important. newVals must be in the same order as allFields.
                    #
                    for fldId, fld in enumerate(allFields):
                        newrec.SetField(fld, newVals[fldId])


                    PrintMsg("TestRec: " + str(newVals), 1)
                    flatTbl.CreateFeature(newrec)

            except:
                # No component records
                #coVals = missingComp
                newVals = [areasym, mukey, musym, muname]
                newVals.extend(missingComp)
                newrec = ogr.Feature(outputDefn)

                for fldId, fld in enumerate(allFields):
                    newrec.SetField(fld, newVals[fldId])

                PrintMsg("TestRec: " + str(newVals), 1)
                flatTbl.CreateFeature(newrec)

            rec = muTable.GetNextFeature()

        PrintMsg("Finished processing table " + sdvTbl, 0)

        time.sleep(1)
        muTable.ResetReading()
        flatTbl.ResetReading()

        #if bVerbose:
        muCnt = flatTbl.GetFeatureCount()
        PrintMsg("SDV_Data table populated with " + Number_Format(muCnt, 0, True) + " records", 1)

        del muTable
        del flatTbl

        return True

    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return False

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

        return False

## ===================================================================================
def CreateRatingTable2S(ds, sdvTbl, dComponent, dTbl, flatTbl, dAreasymbols):
    # ds, tblList, dSDV["attributetablename"].upper(), dComponent, dTbl, flatTbl, dAreasymbols
    # Create level 2 table (mapunit, component, sdvTbl) where rating is in a child table for component
    # which means there could be more than rating value per component
    #

    try:
        #bVerbose = True

        arcpy.SetProgressorLabel("Saving all relevant data to a single query table")

        if bVerbose:
            PrintMsg("Current function : " + sys._getframe().f_code.co_name, 1)
            PrintMsg(".", 1)
            PrintMsg("Using mapunit fields: " + ", ".join(dFields["MAPUNIT"]), 1)
            PrintMsg("Using initial table fields: " + ", ".join(allFields), 1)
            PrintMsg("Using sql_clause: " + str(dSQL["MAPUNIT"]) + " \n", 1)
            PrintMsg("Using where_clause: '" + legendQuery + "'", 1)
            PrintMsg("Output table: " + os.path.basename(flatTbl.GetName()), 1)
            PrintMsg("" + ", ".join(allFields) + " \n ", 1)
            #PrintMsg(80 * "=", 1)

        # Get mapunit table
        muTable = ds.GetLayerByName("mapunit")

        # Get SDV_Data table
        sdvData = tmpDS.GetLayer("SDV_Data")  # Created by CreateInitialTable function

        # Reading mapunit table using OGR
        tblName = "mapunit"
        muTable = ds.GetLayerByName(tblName)

        if legendQuery != "":
            PrintMsg("Using query filter (" + legendQuery + ") against " + tblName, 0)
            time.sleep(10)
            muTable.SetAttributeFilter(legendQuery)
            PrintMsg("Set query filter successfully", 0)

        recCnt = 0
        rec = muTable.GetNextFeature()

        # list of null values for missing component data
        missingComp = dMissing["COMPONENT"]
        missingData = dMissing[sdvTbl]
        outputDefn = flatTbl.GetLayerDefn()
        #testRec = list()  # used to test input data

        while rec is not None:
            recCnt += 1              # increment record counter
            #PrintMsg("Processing table " + tblName + " record " + str(recCnt), 0)
            lkey = rec.GetField("lkey")
            mukey = rec.GetField("mukey")
            musym = rec.GetField("musym")
            muname = rec.GetField("muname")
            areasym = dAreasymbols[lkey]

            try:
                # corecs: [['16641198', 'Penden', 90, 'Well drained'], ['16641199', 'Canlon', 5, 'Somewhat excessively drained'], ['16641200', 'Uly', 5, 'Well drained']]
                coRecs = dComponent[mukey]

                for coVals in coRecs:

                    try:
                        sdvrecs = dTbl[coVals[0]]

                        for sdvrec in sdvrecs:
                            newVals = [areasym, mukey, musym, muname]
                            newVals.extend(coVals)  # should be cokey, compname, comppct_r, rating
                            newVals.extend(sdvrec)
                            newrec = ogr.Feature(outputDefn)

                            # Important. newVals must be in the same order as allFields.
                            #
                            for fldId, fld in enumerate(allFields):
                                newrec.SetField(fld, newVals[fldId])

                            PrintMsg("TestRec: " + str(newVals), 1)
                            flatTbl.CreateFeature(newrec)

                    except KeyError:
                        newVals = [areasym, mukey, musym, muname]
                        newVals.extend(coVals)  # should be cokey, compname, comppct_r, rating
                        newVals.extend(missingData)
                        newrec = ogr.Feature(outputDefn)

                        # Important. newVals must be in the same order as allFields.
                        #
                        for fldId, fld in enumerate(allFields):
                            newrec.SetField(fld, newVals[fldId])

                        PrintMsg("TestRec: " + str(newVals), 1)
                        flatTbl.CreateFeature(newrec)

            except:
                # No component records
                coVals = missingComp
                newVals = [areasym, mukey, musym, muname]
                newVals.extend(coVals)
                newVals.extend(missingData)
                newrec = ogr.Feature(outputDefn)

                for fldId, fld in enumerate(allFields):
                    newrec.SetField(fld, newVals[fldId])

                PrintMsg("TestRec: " + str(newVals), 1)
                flatTbl.CreateFeature(newrec)

            rec = muTable.GetNextFeature()

        PrintMsg("Finished processing table " + tblName, 0)

        time.sleep(1)
        muTable.ResetReading()
        flatTbl.ResetReading()

        #if bVerbose:
        muCnt = flatTbl.GetFeatureCount()
        PrintMsg("SDV_Data table populated with " + Number_Format(muCnt, 0, True) + " records", 1)

        del muTable
        del flatTbl

        # raise MyError("EARLY OUT TO CHECK CORECS", 1)

        return True

    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return False

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

        return False

## ===================================================================================
def CreateRatingTable3(ds, dComponent, dHorizon, flatTbl, dAreasymbols):
    # ds, sdvTbl, dComponent, dTbl, flatTbl, dAreasymbols
    # Populate level 3 table (mapunit, component, chorizon)
    #

    try:
        #bVerbose = True

        arcpy.SetProgressorLabel("Saving all relevant data to a single query table")

        if bVerbose:
            PrintMsg("Current function : " + sys._getframe().f_code.co_name, 1)
            PrintMsg(".", 1)
            PrintMsg("Using mapunit fields: " + ", ".join(dFields["MAPUNIT"]), 1)
            PrintMsg("Using initial table fields: " + ", ".join(allFields), 1)
            PrintMsg("Using sql_clause: " + str(dSQL["MAPUNIT"]) + " \n", 1)
            PrintMsg("Using where_clause: '" + legendQuery + "'", 1)
            PrintMsg("Output table: " + os.path.basename(flatTbl.GetName()), 1)
            PrintMsg("" + ", ".join(allFields) + " \n ", 1)
            #PrintMsg(80 * "=", 1)

        # Get SDV_Data table
        sdvData = tmpDS.GetLayerByName("SDV_Data")  # Created by CreateInitialTable function

        # Reading mapunit table using OGR
        tblName = "mapunit"
        muTable = ds.GetLayerByName(tblName)
        missingData = dMissing["CHORIZON"]

        PrintMsg("missingData: " + str(missingData), 1)


        if legendQuery != "":
            PrintMsg("Using query filter (" + legendQuery + ") against " + tblName, 0)
            time.sleep(10)
            muTable.SetAttributeFilter(legendQuery)
            PrintMsg("Set query filter successfully", 0)

        recCnt = 0
        rec = muTable.GetNextFeature()

        # Writing SDV_Data table using OGR
        PrintMsg("Reading mapunit table", 0)

        # list of null values for missing component data
        missingComp = dMissing["COMPONENT"]
        outputDefn = flatTbl.GetLayerDefn()
        #testRec = list()  # used to test input data

        while rec is not None:
            recCnt += 1              # increment record counter
            #PrintMsg("Processing table " + tblName + " record " + str(recCnt), 0)
            lkey = rec.GetField("lkey")
            mukey = rec.GetField("mukey")
            musym = rec.GetField("musym")
            muname = rec.GetField("muname")
            areasym = dAreasymbols[lkey]

            try:
                # corecs: [['16641198', 'Penden', 90, 'Well drained'], ['16641199', 'Canlon', 5, 'Somewhat excessively drained'], ['16641200', 'Uly', 5, 'Well drained']]
                coRecs = dComponent[mukey]

                for corec in coRecs:

                    try:
                        chrecs = dHorizon[corec[0]]

                        for chrec in chrecs:

                            newVals = [areasym, mukey, musym, muname]
                            newVals.extend(corec)  # should be cokey, compname, comppct_r, rating
                            newVals.extend(chrec)
                            newrec = ogr.Feature(outputDefn)

                            # Important. newVals must be in the same order as allFields.
                            #
                            for fldId, fld in enumerate(allFields):
                                newrec.SetField(fld, newVals[fldId])

                            PrintMsg("TestRec: " + str(newVals), 1)
                            flatTbl.CreateFeature(newrec)

                    except KeyError:
                        # no horizon data
                        newVals = [areasym, mukey, musym, muname]
                        newVals.extend(corec)  # should be cokey, compname, comppct_r, rating
                        newVals.extend(missingData)
                        newrec = ogr.Feature(outputDefn)

                        # Important. newVals must be in the same order as allFields.
                        #
                        for fldId, fld in enumerate(allFields):
                            newrec.SetField(fld, newVals[fldId])

                        PrintMsg("TestRec: " + str(newVals), 1)
                        flatTbl.CreateFeature(newrec)

            except KeyError:
                # No component data
                coVals = missingComp
                newVals = [areasym, mukey, musym, muname]
                newVals.extend(corec)
                newVals.extend(missingComp)
                newVals.extend(missingData)
                newrec = ogr.Feature(outputDefn)

                for fldId, fld in enumerate(allFields):
                    newrec.SetField(fld, newVals[fldId])

                PrintMsg("TestRec: " + str(newVals), 1)
                flatTbl.CreateFeature(newrec)

            rec = muTable.GetNextFeature()

        PrintMsg("Finished processing table " + tblName, 0)

        time.sleep(1)
        muTable.ResetReading()
        flatTbl.ResetReading()

        #if bVerbose:
        muCnt = flatTbl.GetFeatureCount()
        PrintMsg("SDV_Data table populated with " + Number_Format(muCnt, 0, True) + " records", 1)

        del muTable
        del flatTbl

        raise MyError("EARLY OUT TO CHECK CORECS", 1)

        # PrintMsg("Processed " + Number_Format(iCnt, 0, True) + " mapunit records", 1)

        return True

    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return False

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

        return False

## ===================================================================================
def CreateRatingTable3S(ds, sdvTbl, dComponent, dHorizon, dTbl, flatTbl, dAreasymbols):
    #                   ds, dComponent, dHorizon, dTbl, flatTbl, dAreasymbols
    # Create level 4 table (mapunit, component, chorizon, sdvTbl)
    # This is set up for surface texture. Is it called by others?
    #
    # At some point may want to look at returning top mineral horizon instead of hzdept_r = 0.
    #
    try:
        arcpy.SetProgressorLabel("Saving all relevant data to a single query table")
        #bVerbose = True

        if bVerbose:
            PrintMsg("Current function : " + sys._getframe().f_code.co_name, 1)

        #
        # Read mapunit table
        if "LKEY" in allFields:
            allFields.remove("LKEY")

        # Get SDV_Data table
        sdvData = tmpDS.GetLayerByName("SDV_Data")  # Created by CreateInitialTable function

        # Reading mapunit table using OGR
        tblName = "mapunit"
        muTable = ds.GetLayerByName(tblName)

        if legendQuery != "":
            PrintMsg("Using query filter (" + legendQuery + ") against " + tblName, 0)
            time.sleep(10)
            muTable.SetAttributeFilter(legendQuery)
            PrintMsg("Set query filter successfully", 0)

        recCnt = 0
        rec = muTable.GetNextFeature()

        # Writing SDV_Data table using OGR

        # list of null values for missing component data
        missingComp = dMissing["COMPONENT"]
        missingHZ = dMissing["CHORIZON"]
        missingData = dMissing[sdvTbl]
        PrintMsg("missingDataX: " + str(missingData), 1)
        outputDefn = flatTbl.GetLayerDefn()
        testRec = list()  # used to test input data

        while rec is not None:
            recCnt += 1              # increment record counter
            #PrintMsg("Processing table " + tblName + " record " + str(recCnt), 0)
            lkey = rec.GetField("lkey")
            mukey = rec.GetField("mukey")
            musym = rec.GetField("musym")
            muname = rec.GetField("muname")
            areasym = dAreasymbols[lkey]

            try:
                # corecs: [['16641198', 'Penden', 90, 'Well drained'], ['16641199', 'Canlon', 5, 'Somewhat excessively drained'], ['16641200', 'Uly', 5, 'Well drained']]
                coRecs = dComponent[mukey]

                for corec in coRecs:

                    try:
                        chrecs = dHorizon[corec[0]]  #  chrecs = dHorizon[corec[0]]

                        for chrec in chrecs:

                            newVals = [areasym, mukey, musym, muname]
                            newVals.extend(corec)  # should be cokey, compname, comppct_r, rating
                            newVals.extend(chrec)
                            sdvrec = dTbl[chrec[0]][0]
                            newVals.extend(sdvrec)

                            newrec = ogr.Feature(outputDefn)

                            # Important. newVals must be in the same order as allFields.
                            #
                            for fldId, fld in enumerate(allFields):
                                newrec.SetField(fld, newVals[fldId])

                            PrintMsg("TestRec: " + str(newVals), 1)
                            flatTbl.CreateFeature(newrec)

                    except KeyError:
                        # no horizon data
                        newVals = [areasym, mukey, musym, muname]
                        newVals.extend(corec)  # should be cokey, compname, comppct_r, rating
                        newVals.extend(missingHZ)
                        newVals.extend(missingData)
                        newrec = ogr.Feature(outputDefn)

                        # Important. newVals must be in the same order as allFields.
                        #
                        for fldId, fld in enumerate(allFields):
                            newrec.SetField(fld, newVals[fldId])

                        PrintMsg("TestRec: " + str(newVals), 1)
                        flatTbl.CreateFeature(newrec)

            except KeyError:
                # No component records
                coVals = missingComp
                newVals = [areasym, mukey, musym, muname]
                newVals.extend(missingComp)
                newVals.extend(missingHz)
                newVals.extend(missingData)
                newrec = ogr.Feature(outputDefn)

                for fldId, fld in enumerate(allFields):
                    newrec.SetField(fld, newVals[fldId])

                PrintMsg("TestRec: " + str(newVals), 1)

                flatTbl.CreateFeature(newrec)

            rec = muTable.GetNextFeature()

        time.sleep(1)

        PrintMsg("Finished processing table " + tblName, 0)

        time.sleep(1)
        muTable.ResetReading()
        flatTbl.ResetReading()

        #if bVerbose:
        muCnt = flatTbl.GetFeatureCount()
        PrintMsg("SDV_Data table populated with " + Number_Format(muCnt, 0, True) + " records", 1)

        del muTable
        del flatTbl

        raise MyError("EARLY OUT TO CHECK HORIZON DATA", 1)

        return True

    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return False

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

        return False


## ===================================================================================
def CreateRatingInterps(ds, sdvTbl, dComponent, dTbl, flatTbl, dAreasymbols):
    # ds, sdvTbl, dComponent, dTbl, flatTbl, dAreasymbols
    #
    # Populate table for standard interp using (mapunit, component, cointerp)
    #

    try:
        #bVerbose = True

        arcpy.SetProgressorLabel("Saving all relevant data to a single query table")

        if bVerbose:
            PrintMsg("Current function : " + sys._getframe().f_code.co_name, 1)

        # Get SDV_Data table
        sdvData = tmpDS.GetLayer("SDV_Data")  # Created by CreateInitialTable function

        # Reading mapunit table using OGR
        tblName = "mapunit"
        muTable = ds.GetLayerByName(tblName)

        if legendQuery != "":
            PrintMsg("Using query filter (" + legendQuery + ") against " + tblName, 0)
            time.sleep(10)
            muTable.SetAttributeFilter(legendQuery)
            PrintMsg("Set query filter successfully", 0)

        recCnt = 0
        rec = muTable.GetNextFeature()

        # Writing SDV_Data table using OGR
        PrintMsg("Reading mapunit table", 0)

        # list of null values for missing component data
        missingComp = dMissing["COMPONENT"]
        outputDefn = flatTbl.GetLayerDefn()
        testRec = list()  # used to test input data

        while rec is not None:
            recCnt += 1              # increment record counter
            #PrintMsg("Processing table " + tblName + " record " + str(recCnt), 0)
            lkey = rec.GetField("lkey")
            mukey = rec.GetField("mukey")
            musym = rec.GetField("musym")
            muname = rec.GetField("muname")
            areasym = dAreasymbols[lkey]

            try:
                coRecs = dComponent[mukey]

                for coVals in coRecs:

                    try:
                        sdvrecs = dTbl[coVals[0]]

                        for sdvrec in sdvrecs:
                            newVals = [areasym, mukey, musym, muname]
                            newVals.extend(coVals)  # should be cokey, compname, comppct_r, rating
                            newVals.extend(sdvrec)
                            newrec = ogr.Feature(outputDefn)

                            # Important. newVals must be in the same order as allFields.
                            #
                            for fldId, fld in enumerate(allFields):
                                newrec.SetField(fld, newVals[fldId])

                            PrintMsg("TestRec: " + str(newVals), 1)
                            flatTbl.CreateFeature(newrec)

                    except KeyError:
                        newVals = [areasym, mukey, musym, muname]
                        newVals.extend(coVals)  # should be cokey, compname, comppct_r, rating
                        newVals.extend(dMissing[sdvTbl])
                        newrec = ogr.Feature(outputDefn)

                        # Important. newVals must be in the same order as allFields.
                        #
                        for fldId, fld in enumerate(allFields):
                            newrec.SetField(fld, newVals[fldId])

                        PrintMsg("TestRec: " + str(newVals), 1)
                        flatTbl.CreateFeature(newrec)

            except:
                # No component records
                coVals = missingComp
                newVals = [areasym, mukey, musym, muname]
                newVals.extend(coVals)
                newVals.extend(dMissing[sdvTbl])
                newrec = ogr.Feature(outputDefn)

                for fldId, fld in enumerate(allFields):
                    newrec.SetField(fld, newVals[fldId])

                PrintMsg("TestRec: " + str(newVals), 1)
                flatTbl.CreateFeature(newrec)

            rec = muTable.GetNextFeature()

        PrintMsg("Finished processing table " + tblName, 0)

        time.sleep(1)
        muTable.ResetReading()
        flatTbl.ResetReading()

        #if bVerbose:
        muCnt = flatTbl.GetFeatureCount()
        PrintMsg("SDV_Data table populated with " + Number_Format(muCnt, 0, True) + " records", 1)

        del muTable
        del flatTbl

        raise MyError("EARLY OUT TO CHECK INTERPS", 1)

        return True

    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return False

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

        return False

## ===================================================================================
def CreateSoilMoistureTable(ds, sdvTbl, dComponent, dMonth, dTbl, flatTbl, begMo, endMo, dAreasymbols):
    # Create level 4 table (mapunit, component, cmonth, cosoilmoist)
    #
    # Problem 2017-07-24 Steve Campbell found Yolo County mapunits where dominant component,
    # Depth to Water Table map is reporting 201cm for 459272 where the correct result should be 91cm.
    # My guess is that because there are some months in COSOILMOIST table that are Null, this function
    # is using that value instead of the other months that are 91cm. Try removing NULLs in query that
    # creates the SDV_Data table.
    #
    try:
        #bVerbose = True

        arcpy.SetProgressorLabel("Saving all relevant data to a single query table")

        if bVerbose:
            PrintMsg("Current function : " + sys._getframe().f_code.co_name, 1)
            PrintMsg

        # Read mapunit table and then populate the initial output table
        if "LKEY" in allFields:
            allFields.remove("LKEY")

        # Get SDV_Data table
        sdvData = tmpDS.GetLayerByName("SDV_Data")  # Created by CreateInitialTable function

        # Reading mapunit table using OGR
        tblName = "mapunit"
        muTable = ds.GetLayerByName(tblName)

        if legendQuery != "":
            PrintMsg("Using query filter (" + legendQuery + ") against " + tblName, 0)
            time.sleep(10)
            muTable.SetAttributeFilter(legendQuery)
            PrintMsg("Set query filter successfully", 0)

        recCnt = 0
        rec = muTable.GetNextFeature()

        # list of null values for missing component data
        missingData = dMissing[sdvTbl]
        outputDefn = flatTbl.GetLayerDefn()
        testRec = list()  # used to test input data

        while rec is not None:
            recCnt += 1              # increment record counter
            #PrintMsg("Processing table " + tblName + " record " + str(recCnt), 0)
            lkey = rec.GetField("lkey")
            mukey = rec.GetField("mukey")
            musym = rec.GetField("musym")
            muname = rec.GetField("muname")
            areasym = dAreasymbols[lkey]

            try:
                # corecs: [['16641198', 'Penden', 90, 'Well drained'], ['16641199', 'Canlon', 5, 'Somewhat excessively drained'], ['16641200', 'Uly', 5, 'Well drained']]
                coRecs = dComponent[mukey]

                for corec in coRecs:
                    try:
                        morecs = dMonth[corec[0]]

                        for morec in morecs:

                            try:
                                # moisture data
                                sdvrecs = dTbl[morec[0]]

                                for sdvrec in sdvrecs:
                                    newVals = [areasym, mukey, musym, muname]
                                    newVals.extend(corec)  # should be cokey, compname, comppct_r, rating
                                    newVals.extend(morec)
                                    newVals.extend(sdvrec)
                                    newrec = ogr.Feature(outputDefn)

                                    # Important. newVals must be in the same order as allFields.
                                    for fldId, fld in enumerate(allFields):
                                        newrec.SetField(fld, newVals[fldId])

                                    PrintMsg("TestRec: " + str(newVals), 1)
                                    flatTbl.CreateFeature(newrec)

                            except KeyError:
                                # no data in sdvTbl
                                newVals = [areasym, mukey, musym, muname]
                                newVals.extend(corec)  # should be cokey, compname, comppct_r, rating
                                newVals.extend(morec)
                                newVals.extend(missingData)
                                newrec = ogr.Feature(outputDefn)

                                # Important. newVals must be in the same order as allFields.
                                for fldId, fld in enumerate(allFields):
                                    newrec.SetField(fld, newVals[fldId])

                                PrintMsg("TestRec: " + str(newVals), 1)
                                flatTbl.CreateFeature(newrec)

                    except KeyError:
                        # no months
                                # no data in sdvTbl
                                newVals = [areasym, mukey, musym, muname]
                                newVals.extend(corec)  # should be cokey, compname, comppct_r, rating
                                newVals.extend(dMissing["COMONTH"])
                                newVals.extend(missingData)
                                newrec = ogr.Feature(outputDefn)

                                # Important. newVals must be in the same order as allFields.
                                for fldId, fld in enumerate(allFields):
                                    newrec.SetField(fld, newVals[fldId])

                                PrintMsg("TestRec: " + str(newVals), 1)
                                flatTbl.CreateFeature(newrec)


            except KeyError:
                # No component records
                coVals = missingComp
                newVals = [areasym, mukey, musym, muname]
                newVals.extend(dMissing["COMPONENT"])
                newVals.extend(dMissing["COMONTH"])
                newVals.extend(missingData)
                newrec = ogr.Feature(outputDefn)

                for fldId, fld in enumerate(allFields):
                    newrec.SetField(fld, newVals[fldId])

                PrintMsg("TestRec: " + str(newVals), 1)


            flatTbl.CreateFeature(newrec)
            rec = muTable.GetNextFeature()

        time.sleep(1)

        PrintMsg("Finished processing table " + tblName, 0)

        muTable.ResetReading()
        flatTbl.ResetReading()

        #if bVerbose:
        muCnt = flatTbl.GetFeatureCount()
        PrintMsg("SDV_Data table populated with " + Number_Format(muCnt, 0, True) + " records", 1)

        del muTable
        del flatTbl

        raise MyError("EARLY OUT TO CHECK COINTERP DATA", 1)

        return True

    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return False

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

        return False

## ===================================================================================
def Aggregate1(tmpDS, sdvAtt, sdvFld, dfRaw, dataTypes, bZero, cutOff, tieBreaker):
    # Aggregate map unit level table
    # Added Areasymbol to output
    try:
        arcpy.SetProgressorLabel("Assembling map unit level data")

        if bVerbose:
            PrintMsg("Current function : " + sys._getframe().f_code.co_name, 1)

        # Read mapunit table and populate final output table
        # Create final output table with MUKEY and sdvFld
        #
        # Really no difference between the two tables, so this
        # is redundant. Should fix this later after everything
        # else is working.
        #

        #PrintMsg("AttributeColumnName: " + dSDV["attributecolumnname"].upper(), 1)
        #PrintMsg("ResultColumnName: " + dSDV["resultcolumnname"].upper(), 1)

        inFlds = ["AREASYMBOL", "MUKEY", dSDV["attributecolumnname"].upper()]
        outFlds = ["AREASYMBOL", "MUKEY", dSDV["resultcolumnname"].upper()]

        # I wonder if I should take outfields from flatTbl?
        outputValues = list()

        if dSDV["attributeprecision"] is None:
            fldPrecision = 0

        else:
            fldPrecision = dSDV["attributeprecision"]

        recCnt = 0
        testRec = list()  # used to test input data
        inputDefn = flatTbl.GetLayerDefn()        # OGR. Get soil polygon layer fields
        inputFieldNames = list()

        for n in range(inputDefn.GetFieldCount()):
            fDef = inputDefn.GetFieldDefn(n)
            inputFieldNames.append(fDef.name)

        # See if I can use inputFieldNames to create a proper header for jsonData
        #jsonData = CreateOutputJSON(tmpDS, flatTbl, dFieldInfo, inputFieldNames)

        #if len(jsonData) == 0:
        #    # failed to create list to contain data records
        #    return jsonData, outputValues

        #PrintMsg("jsonData: " + str(jsonData[0]), 1)
        #PrintMsg("jsonData: " + str(jsonData[1]), 1)
        PrintMsg("dataTypes: " + str(dataTypes), 1)
        ratingField = dataTypes[-1][0]
        ratingType = dataTypes[1-1][1]

        PrintMsg("Rating type: " + ratingField + " - " + ratingType, 1)

        if dSDV["effectivelogicaldatatype"].lower() in ["integer", "float"]:
            # populate sdv_initial table and create list of min-max values
            iMax = -999999999
            iMin = 999999999

            # assume last field is the rating
            ratingField = inputFieldNames.pop(-1)
            rec = flatTbl.GetNextFeature()  # wondering if I should close flatTbl and reopen as read-only????

            while rec is not None: # read through through SDV_Data table
                #lkey = rec.GetField("lkey")
                recCnt += 1
                newrec = list()

                for fld in inputFieldNames:
                    newrec.append(rec.GetField(fld))

                val = rec.GetField(ratingField)

                if not val is None:
                    val = round(val, fldPrecision)
                    iMax = max(val, iMax)
                    iMin = min(val, iMin)

                newrec.append(val)
                jsonData.append(newrec)
                PrintMsg(str(newrec), 1)
                rec = flatTbl.GetNextFeature()

            # add max and min values to list
            outputValues = [iMin, iMax]

            if iMin == None and iMax == -999999999:
                # No data
                err = "8. No data for " + sdvAtt
                raise MyError(err)

        else:

            rec = flatTbl.GetNextFeature()  # wondering if I should close flatTbl and reopen as read-only????

            while rec is not None: # read through through SDV_Data table
                #lkey = rec.GetField("lkey")
                recCnt += 1
                newrec = list()

                for fld in inputFieldNames:
                    newrec.append(rec.GetField(fld))

                val = newrec[-1]
                jsonData.append(newrec)
                PrintMsg(str(newrec), 1)

                if not val is None and not val in outputValues:
                    outputValues.append(val)

                rec = flatTbl.GetNextFeature()


        if len(outputValues) < 20 and bVerbose:
            PrintMsg("Initial output values: " + str(outputValues), 1)

        outputValues.sort()

        return jsonData, outputValues

    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return jsonData, outputValues

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

        return jsonData, outputValues

## ===================================================================================
def AggregateCo_DCP(gdb, sdvAtt, sdvFld, flatTbl, bZero, cutOff, tieBreaker):
    # Aggregate mapunit-component data to the map unit level using dominant component
    # Added areasymbol to output
    try:
        bVerbose = True
        arcpy.SetProgressorLabel("Aggregating rating information to the map unit level")

        #
        if bVerbose:
            PrintMsg("Current function : " + sys._getframe().f_code.co_name, 1)
            PrintMsg("This function uses dValues dictionary", 1)

        if tieBreaker == dSDV["tiebreaklowlabel"]:
            sqlClause =  (None, " ORDER BY MUKEY ASC, COMPPCT_R DESC, " + dSDV["attributecolumnname"].upper() + " ASC ")
            #PrintMsg("Ascending sort on " + dSDV["attributecolumnname"], 1)

        else:
            sqlClause =  (None, " ORDER BY MUKEY ASC, COMPPCT_R DESC, " + dSDV["attributecolumnname"].upper() + " DESC ")
            #PrintMsg("Descending sort on " + dSDV["attributecolumnname"], 1)

        PrintMsg("AttributeColumnName: " + dSDV["attributecolumnname"].upper(), 1)
        PrintMsg("ResultColumnName: " + dSDV["resultcolumnname"].upper(), 1)
        inFlds = ["AREASYMBOL", "MUKEY", dSDV["attributecolumnname"].upper()]
        outFlds = ["AREASYMBOL", "MUKEY", dSDV["resultcolumnname"].upper()]
        outputValues = list()

        if dSDV["attributeprecision"] is None:
            fldPrecision = 0

        else:
            fldPrecision = dSDV["attributeprecision"]

        recCnt = 0
        testRec = list()  # used to test input data
        inputDefn = flatTbl.GetLayerDefn()        # OGR. Get soil polygon layer fields
        inputFieldNames = list()

        for n in range(inputDefn.GetFieldCount()):
            fDef = inputDefn.GetFieldDefn(n)
            inputFieldNames.append(fDef.name)

        # assume last field is the rating
        ratingField = inputFieldNames.pop(-1)


        # See if I can use inputFieldNames to create a proper header for jsonData
        jsonData = CreateOutputJSON(tmpDS, flatTbl, dFieldInfo, inputFieldNames)

        if len(jsonData) == 0:
            # failed to create list to contain data records
            return jsonData, outputValues

        PrintMsg("jsonData2: " + str(jsonData[0]), 1)
        PrintMsg("jsonData2: " + str(jsonData[1]), 1)
        PrintMsg("Rating field name from SDV_Data table: " + ratingField, 0)
        ## =====================================================================

        lastMukey = "xxxx"




        # New test. See if we can convert the flatTbl to a Pandas dataframe which has more
        # aggregation options.
        PrintMsg(".    Converting " + flatTbl + " to a pandas dataframe...", 0)
        data = list()


        # Reading numeric data from initial table
        #
        if dSDV["effectivelogicaldatatype"].lower() in ["integer", "float"]:
            # populate sdv_initial table and create list of min-max values
            iMax = -999999999
            iMin = 999999999

            rec = flatTbl.GetNextFeature()  # wondering if I should close flatTbl and reopen as read-only????

            while rec is not None: # read through through SDV_Data table
                recCnt += 1
                newrec = list()

                for fld in inputFieldNames:
                    newrec.append(rec.GetField(fld))

                val = rec.GetField(ratingField)

                if not val is None:
                    val = round(val, fldPrecision)
                    iMax = max(val, iMax)
                    iMin = min(val, iMin)

                newrec.append(val)
                #jsonData.append(newrec)
                data.append(newrec) # pandas df
                PrintMsg(str(newrec), 1)
                rec = flatTbl.GetNextFeature()

            # add max and min values to list
            outputValues = [iMin, iMax]

            if iMin == None and iMax == -999999999:
                # No data
                err = "8. No data for " + sdvAtt
                raise MyError(err)

##            with arcpy.da.SearchCursor(flatTbl, inFlds, sql_clause=sqlClause) as cur:
##
##                with arcpy.da.InsertCursor(outputTbl, outFlds) as ocur:
##                    for rec in cur:
##                        mukey, areasym, cokey, comppct, rating = rec
##
##                        #if mukey != lastMukey and lastMukey != "xxxx":  # This was dropping first map unit!!!
##                        if mukey != lastMukey:
##
##                            if not rating is None:
##                                #
##                                newrec = mukey, areasym, comppct, round(rating, fldPrecision)
##
##                            else:
##                                newrec = mukey, areasym, comppct, None
##
##                            ocur.insertRow(newrec)
##
##                            if not rating is None:
##                                iMax = max(rating, iMax)
##                                iMin = min(rating, iMin)
##
##                        lastMukey = mukey

            # add max and min values to list
            outputValues = [iMin, iMax]

        else:
            # For text, vtext or choice data types
            #
            #PrintMsg("dValues: " + str(dValues), 1)
            #PrintMsg("outputValues: " + str(outputValues), 1)
            rec = flatTbl.GetNextFeature()  # wondering if I should close flatTbl and reopen as read-only????

            while rec is not None: # read through through SDV_Data table
                #lkey = rec.GetField("lkey")
                recCnt += 1
                newrec = list()

                for fld in inputFieldNames:
                    newrec.append(rec.GetField(fld))

                val = newrec[-1]
                #jsonData.append(newrec)
                data.append(newrec) # pandas df
                PrintMsg(str(newrec), 1)

                if not val is None and not val in outputValues:
                    outputValues.append(val)

                rec = flatTbl.GetNextFeature()




        if len(outputValues) < 20 and bVerbose:
            PrintMsg("Initial output values: " + str(outputValues), 1)

        outputValues.sort()

        return jsonData, outputValues
##            with arcpy.da.SearchCursor(flatTbl, inFlds, sql_clause=sqlClause) as cur:
##
##                if len(dValues) > 0:
##                    # Text, has domain values or values in the maplegendxml
##                    #
##                    with arcpy.da.InsertCursor(outputTbl, outFlds) as ocur:
##                        for rec in cur:
##
##                            mukey, areasym, cokey, comppct, rating = rec
##
##                            if mukey != lastMukey:
##
##                                #if not rating is None:
##                                if str(rating).upper() in dValues:
##                                    if dValues[rating.upper()][1] != rating: # we have a case problem in the maplegendxml
##                                        # switch the dValue to lowercase to match the data
##                                        dValues[str(rating).upper()][1] = rating
##
##                                    newrec = [mukey, areasym, comppct, rating]
##
##                                elif not rating is None:
##
##                                    dValues[str(rating).upper()] = [None, rating]
##                                    newrec = [mukey, areasym, comppct, rating]
##
##                                else:
##                                    newrec = [mukey, areasym, None, None]
##
##                                if not rating in outputValues and not rating is None:
##                                    outputValues.append(rating)
##
##                                ocur.insertRow(newrec)
##                                #PrintMsg(str(rec), 1)
##
##                            lastMukey = mukey
##
##                else:
##                    pass
##                    # Text, without domain values
##                    #
##                    with arcpy.da.InsertCursor(outputTbl, outFlds) as ocur:
##                        for rec in cur:
##                            mukey, areasym, cokey, comppct, rating = rec
##
##                            if mukey != lastMukey:
##                                if not rating is None:
##                                    newVal = rating.strip()
##
##                                else:
##                                    newVal = None
##
##                                ocur.insertRow([mukey, areasym, comppct, newVal])
##
##
##                                if not newVal is None and not newVal in outputValues:
##                                    outputValues.append(newVal)
##
##                            #else:
##                            #    PrintMsg("\tSkipping " + str(rec), 1)
##
##                            lastMukey = mukey


        #if None in outputValues:
        #    outputValues.remove(None)

        if outputValues[0] == -999999999.0 or outputValues[1] == 999999999.0:
            # Sometimes no data can skip through the max min test
            outputValues = [0.0, 0.0]
            err = "No data for " + sdvAtt
            raise MyError(err)

        # Trying to handle NCCPI for dominant component
        if dSDV["attributetype"].lower() == "interpretation" and (dSDV["nasisrulename"][0:5] == "NCCPI"):
            outputValues = [0.0, 1.0]

        if dSDV["effectivelogicaldatatype"].lower() in ("float", "integer"):
            outputValues.sort()
            return outputTbl, outputValues

        else:
            return outputTbl, sorted(outputValues, key=lambda s: s.lower())

    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return outputTbl, outputValues

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

        return outputTbl, outputValues

## ===================================================================================
def AggregateCo_Limiting(gdb, sdvAtt, sdvFld, flatTbl, bZero, cutOff, tieBreaker):
    #
    # Select either the "Least Limiting" or "Most Limiting" rating from all components
    # Component aggregation to the maximum or minimum value for the mapunit.

    # Based upon AggregateCo_DCD function, but sorted on rating or domain value instead of comppct
    #
    # domain: soil_erodibility_factor (text)  range = .02 .. .64
    # Added Areasymbol to output

    # Note! I have some dead code for 'no domain values'. Need to delete if those sections are never used.

    try:
        arcpy.SetProgressorLabel("Aggregating rating information to the map unit level")

        #
        if bVerbose:
            PrintMsg("Current function : " + sys._getframe().f_code.co_name, 1)
            PrintMsg("Effective Logical data type: " + dSDV["effectivelogicaldatatype"], 1)
            PrintMsg("Attribute type: " + dSDV["attributetype"] + "; bFuzzy " + str(bFuzzy), 1)
            PrintMsg("This function uses dValues dictionary", 1)

        # Create final output table with MUKEY, COMPPCT_R and sdvFld
        outputTbl = os.path.join(gdb, tblName)

        inFlds = ["MUKEY", "AREASYMBOL", "COKEY", "COMPPCT_R", dSDV["attributecolumnname"].upper()]
        outFlds = ["MUKEY", "AREASYMBOL", "COMPPCT_R", dSDV["resultcolumnname"].upper()]

        # ignore any null values
        whereClause = "COMPPCT_R >=  " + str(cutOff) + " AND " + dSDV["attributecolumnname"].upper() + " IS NOT NULL"

        # flatTbl must be in a file geodatabase to support ORDER_BY
        #
        sqlClause =  (None, " ORDER BY MUKEY ASC")

        if arcpy.Exists(outputTbl):
            arcpy.Delete_management(outputTbl)

        outputTbl = CreateOutputTable(tmpDS, flatTbl, outputTbl, dFieldInfo)
        outputValues = list()

        if outputTbl == "":
            return outputTbl, outputValues

        lastCokey = "xxxx"
        dComp = dict()
        dCompPct = dict()
        dMapunit = dict()
        dAreasym = dict()

        aggMethod = dSDV["algorithmname"]

        if not dSDV["notratedphrase"] is None:
            # This should be for most interpretations
            notRatedIndex = domainValues.index(dSDV["notratedphrase"])

        else:
            # set notRatedIndex for properties that are not interpretations
            notRatedIndex = -1

        # 1. For ratings that have domain values, read data from initial table
        #
        if len(domainValues) > 0:
            #PrintMsg("dValues: " + str(dValues), 1)

            # Save the rating for each component along with a list of components for each mapunit
            #
            try:
                with arcpy.da.SearchCursor(flatTbl, inFlds, sql_clause=sqlClause, where_clause=whereClause) as cur:
                    # inFlds: 0 mukey, 1 cokey, 2 comppct, 3 rating

                    for rec in cur:
                        #PrintMsg(str(rec), 1)
                        mukey, areasym, cokey, comppct, rating = rec
                        dAreasym[mukey] = areasym

                        # Save the associated domain index for this rating
                        dComp[cokey] = dValues[str(rating).upper()][0]

                        # save component percent for each component
                        dCompPct[cokey] = comppct

                        # save list of components for each mapunit using mukey as key
                        try:
                            dMapunit[mukey].append(cokey)

                        except:
                            dMapunit[mukey] = [cokey]

                        #PrintMsg("Component '" + rec[1] + "' at " + str(rec[2]) + "% has a rating of: " + str(rec[3]), 1)

            except:
                errorMsg1()

        else:
            # 2. No Domain Values, read data from initial table. Use alpha sort for tiebreaker
            #
            err = "No Domain values"
            raise MyError(err)


        # Write aggregated data to output table

        with arcpy.da.InsertCursor(outputTbl, outFlds) as ocur:

            if aggMethod == "Least Limiting":
                #
                # Need to take a closer look at how 'Not rated' components are handled in 'Least Limiting'
                #
                if domainValues:

                    for mukey, cokeys in dMapunit.items():
                        dRating = dict()   # save sum of comppct for each rating within a mapunit
                        muVals = list()    # may not need this for DCD
                        #maxIndx = 0        # Initialize index as zero ('Not rated')
                        indexes = list()

                        for cokey in cokeys:
                            compPct = dCompPct[cokey]
                            ratingIndx = dComp[cokey]
                            indexes.append(ratingIndx)
                            #PrintMsg("\t\t" + mukey + ": " + cokey + " - " + str(ratingIndx) + ",  " + domainValues[ratingIndx], 1)

                            if ratingIndx in dRating:
                                 dRating[ratingIndx] = dRating[ratingIndx] + compPct

                            else:
                                dRating[ratingIndx] = compPct

                        # Use the highest index value to assign the map unit rating
                        indexes = sorted(set(indexes), reverse=True)
                        maxIndx = indexes[0]  # get the lowest index value

                        if maxIndx == notRatedIndex and len(indexes) > 1:
                            # if the lowest index is for 'Not rated', try to get the next higher index
                            maxIndx = indexes[1]

                        pct = dRating[maxIndx]
                        rating = domainValues[maxIndx]
                        areasym = dAreasym[mukey]
                        newrec = [mukey, areasym, pct, rating]
                        ocur.insertRow(newrec)
                        #PrintMsg("\tMapunit rating: " + str(indexes) + "; " + str(maxIndx) + "; " + rating + " \n ", 1)

                        if not rating is None and not rating in outputValues:
                            outputValues.append(rating)

                else:
                    # Least Limiting, no domain values
                    #
                    err = "No domain values"
                    raise MyError(err)

            elif aggMethod == "Most Limiting":
                #
                # with domain values...
                #
                # Need to take a closer look at how 'Not rated' components are handled in 'Most Limiting'
                #
                if len(domainValues) > 0:
                    #
                    # Most Limiting, has domain values
                    #
                    for mukey, cokeys in dMapunit.items():
                        dRating = dict()   # save sum of comppct for each rating within a mapunit
                        minIndx = 9999999  # save the lowest index value for each mapunit
                        indexes = list()

                        for cokey in cokeys:
                            compPct = dCompPct[cokey]  # get comppct_r for this component
                            ratingIndx = dComp[cokey]  # get rating index for this component
                            indexes.append(ratingIndx)

                            # save the sum of comppct_r for each rating index in the dRating dictionary
                            if ratingIndx in dRating:
                                dRating[ratingIndx] = dRating[ratingIndx] + compPct

                            else:
                                dRating[ratingIndx] = compPct

                        indexes = sorted(set(indexes))
                        minIndx = indexes[0]  # get the lowest index value

                        if minIndx == notRatedIndex and len(indexes) > 1:
                            # if the lowest index is for 'Not rated', try to get the next higher index
                            minIndx = indexes[1]

                        newrec = [mukey, dAreasym[mukey], dRating[minIndx], domainValues[minIndx]]
                        #PrintMsg("\t" + mukey + ": " + " - " + str(minIndx) + ",  " + domainValues[minIndx], 1)
                        ocur.insertRow(newrec)

                        if not domainValues[minIndx] is None and not domainValues[minIndx] in outputValues:
                            outputValues.append(domainValues[minIndx])

                else:
                    #
                    # Most Limiting, no domain values
                    err = "No domain values"
                    raise MyError(err)

                    #PrintMsg("Testing " + aggMethod + ", no domain values!!!", 1)
                    #
                    for mukey, cokeys in dMapunit.items():
                        dRating = dict()  # save sum of comppct for each rating within a mapunit
                        muVals = list()   # list of rating values for each mapunit

                        for cokey in cokeys:
                            compPct = dCompPct[cokey]  # component percent
                            ratingIndx = dComp[cokey]  # component rating

                            if ratingIndx != 0:
                                if ratingIndx in dRating:
                                    dRating[ratingIndx] = dRating[ratingIndx] + compPct

                                else:
                                    dRating[ratingIndx] = compPct

                        for rating, compPct in dRating.items():
                            muVals.append([compPct, rating])

                        if len(muVals) > 0:
                            muVal = SortData(muVals)

                            newrec = [mukey, dAreasym[mukey], muVal[0], muVal[1]]
                            ocur.insertRow(newrec)
                            #PrintMsg("\t" + mukey + ": " + ",  " + str(muVals), 1)

                        if not newrec[2] is None and not newrec[2] in outputValues:
                            outputValues.append(newrec[2])

                # End of Lower

        outputValues.sort()

        return outputTbl, outputValues

    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return outputTbl, outputValues

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


        return outputTbl, outputValues

## ===================================================================================
def AggregateCo_MaxMin(gdb, sdvAtt, sdvFld, flatTbl, bZero, cutOff, tieBreaker):
    #
    # Looks at all components and returns the lowest or highest rating value. This
    # may be based upon the actual value or the index (for those properties with domains).
    #
    # "Minimum or Maximum" method of aggregation uses the tiebreak setting
    # and returns the highest or lowest rating accordingly.

    # "Least Limiting", "Most Limiting"
    # Component aggregation to the maximum or minimum value for the mapunit.
    #
    # dSDV["tiebreakrule"]: -1, 1 originally in sdvattribute table
    #
    # If tieBreak value == "lower" return the minimum value for the mapunit
    # Else return "Higher" value for the mapunit
    #
    # Based upon AggregateCo_DCD function, but sorted on rating or domain value instead of comppct
    #
    # domain: soil_erodibility_factor (text)  range = .02 .. .64
    # Added Areasymbol to output

    try:
        #bVerbose = True

        arcpy.SetProgressorLabel("Aggregating rating information to the map unit level")

        #
        if bVerbose:
            PrintMsg("Current function : " + sys._getframe().f_code.co_name, 1)
            PrintMsg("Effective Logical data type: " + dSDV["effectivelogicaldatatype"], 1)
            PrintMsg("Attribute type: " + dSDV["attributetype"] + "; bFuzzy " + str(bFuzzy), 1)
            PrintMsg("This function uses dValues dictionary", 1)

        # Create final output table with MUKEY, COMPPCT_R and sdvFld
        outputTbl = os.path.join(gdb, tblName)

        inFlds = ["MUKEY", "AREASYMBOL", "COKEY", "COMPPCT_R", dSDV["attributecolumnname"].upper()]
        outFlds = ["MUKEY", "AREASYMBOL", "COMPPCT_R", dSDV["resultcolumnname"].upper()]

        # ignore any null values
        whereClause = "COMPPCT_R >=  " + str(cutOff) + " AND " + dSDV["attributecolumnname"].upper() + " IS NOT NULL"

        # flatTbl must be in a file geodatabase to support ORDER_BY
        # Do I really need to sort by attributecolumn when it will be replaced by Domain values later?
        #
        if tieBreaker == dSDV["tiebreaklowlabel"]:
            sqlClause =  (None, " ORDER BY MUKEY ASC, COMPPCT_R DESC, " + dSDV["attributecolumnname"].upper() + " ASC ")

        else:
            sqlClause =  (None, " ORDER BY MUKEY ASC, COMPPCT_R DESC, " + dSDV["attributecolumnname"].upper() + " DESC ")

        if arcpy.Exists(outputTbl):
            arcpy.Delete_management(outputTbl)

        outputTbl = CreateOutputTable(tmpDS, flatTbl, outputTbl, dFieldInfo)
        outputValues = list()

        if outputTbl == "":
            return outputTbl, outputValues

        lastCokey = "xxxx"
        dComp = dict()
        dCompPct = dict()
        dMapunit = dict()
        dAreasym = dict()

        if not dSDV["notratedphrase"] is None:
            # This should work for most interpretations
            if dSDV["notratedphrase"] in domainValues:
                notRatedIndex = domainValues.index(dSDV["notratedphrase"])

            else:
                notRatedIndex = -1

        else:
            # set notRatedIndex for properties that are not interpretations
            notRatedIndex = -1

        #
        # Begin component level processing. Branch according to whether values are members of a domain.
        #
        if len(domainValues) > 0:
            # Save the rating for each component along with a list of components for each mapunit
            #
            # PrintMsg("domainValues for " + sdvAtt + ": " + str(domainValues), 1)

            try:
                with arcpy.da.SearchCursor(flatTbl, inFlds, sql_clause=sqlClause, where_clause=whereClause) as cur:
                    # inFlds: 0 mukey, 1 cokey, 2 comppct, 3 rating

                    for rec in cur:
                        #PrintMsg(str(rec), 1)
                        mukey, areasym, cokey, comppct, rating = rec
                        dAreasym[mukey] = areasym

                        # Save the associated domain index for this rating
                        dComp[cokey] = dValues[str(rating).upper()][0]

                        # save component percent for each component
                        dCompPct[cokey] = comppct

                        # save list of components for each mapunit using mukey as key
                        try:
                            dMapunit[mukey].append(cokey)

                        except:
                            dMapunit[mukey] = [cokey]

                        #PrintMsg("Component '" + rec[1] + "' at " + str(rec[2]) + "% has a rating of: " + str(rec[3]), 1)

            except:
                errorMsg1()

        else:
            # 2. No Domain Values, read data from initial table. Use alpha sort for tiebreaker.
            #
            with arcpy.da.SearchCursor(flatTbl, inFlds, sql_clause=sqlClause, where_clause=whereClause) as cur:

                for rec in cur:
                    mukey, areasym, cokey, comppct, rating = rec
                    dAreasym[mukey] = areasym
                    # Assume that this is the first rating for the component
                    dComp[cokey] = rating

                    # save component percent for each component
                    dCompPct[cokey] = comppct

                    # save list of components for each mapunit
                    try:
                        dMapunit[mukey].append(cokey)

                    except:
                        dMapunit[mukey] = [cokey]

        # End of component level processing
        #


        #
        # Begin process of writing mapunit-aggregated data to output table
        # Branch according to aggregation method and tiebreak settings and whether ratings are members of a domain
        #
        if bVerbose:
            PrintMsg("TieBreaker: " + str(tieBreaker), 1)
            #PrintMsg("Tiebreak high label: " + str(dSDV["tiebreakhighlabel"]), 1)
            #PrintMsg("Tiebreak low label: " + str(dSDV["tiebreaklowlabel"]), 1)
            PrintMsg("Tiebreak Rule: " + str(dSDV["tiebreakrule"]), 1)
            PrintMsg("domainValues: " + str(domainValues), 1)
            PrintMsg("notRatedIndex: " + str(notRatedIndex), 1)

        with arcpy.da.InsertCursor(outputTbl, outFlds) as ocur:

            #
            # Begin Minimum or Maximum
            #
            if aggMethod == "Minimum or Maximum" and tieBreaker == dSDV["tiebreaklowlabel"]:
                #
                # MIN
                #
                if len(domainValues) > 0:
                    #
                    # MIN
                    # Has Domain
                    #
                    #PrintMsg("This option has domain values for MinMax!", 1) example WEI MaxMin

                    for mukey, cokeys in dMapunit.items():
                        dRating = dict()   # save sum of comppct for each rating within a mapunit
                        minIndx = 9999999  # save the lowest index value for each mapunit
                        indexes = list()

                        for cokey in cokeys:
                            compPct = dCompPct[cokey]  # get comppct_r for this component
                            ratingIndx = dComp[cokey]  # get rating index for this component
                            indexes.append(ratingIndx)

                            # save the sum of comppct_r for each rating index in the dRating dictionary
                            if ratingIndx in dRating:
                                dRating[ratingIndx] = dRating[ratingIndx] + compPct

                            else:
                                dRating[ratingIndx] = compPct

                        indexes = sorted(set(indexes), reverse=False)
                        minIndx = indexes[0]  # get the lowest index value

                        if minIndx == notRatedIndex and len(indexes) > 1:
                            # if the lowest index is for 'Not rated', try to get the next higher index
                            minIndx = indexes[1]

                        newrec = [mukey, dAreasym[mukey], dRating[minIndx], domainValues[minIndx]]
                        #PrintMsg("\t" + mukey + ": " + " - " + str(minIndx) + ",  " + domainValues[minIndx], 1)
                        ocur.insertRow(newrec)
                        #PrintMsg("\tPessimistic 3 Mapunit rating: " + str(indexes) + ", " + str(minIndx) + ", " + str(domainValues[minIndx]) + " \n ", 1)

                        if not domainValues[minIndx] is None and not domainValues[minIndx] in outputValues:
                            outputValues.append(domainValues[minIndx])

                else:
                    #
                    # MIN
                    # No domain
                    #
                    for mukey, cokeys in dMapunit.items():
                        dRating = dict()  # save sum of comppct for each rating within a mapunit
                        muVals = list()   # list of rating values for each mapunit

                        for cokey in cokeys:
                            compPct = dCompPct[cokey]  # component percent
                            rating = dComp[cokey]  # component rating

                            #if rating != 0:
                            if rating in dRating:
                                dRating[rating] = dRating[rating] + compPct

                            else:
                                dRating[rating] = compPct

                        for rating, compPct in dRating.items():
                            muVals.append([compPct, rating])

                        if len(muVals) > 0:
                            muVal = SortData(muVals, 1, 0, False, True)

                            newrec = [mukey, dAreasym[mukey], muVal[0], muVal[1]]
                            ocur.insertRow(newrec)

                            #if mukey == '2774629':
                            #    #PrintMsg("\t" + mukey + ": " + str(muVal) + " <- " + str(muVals), 1)
                            #    PrintMsg("\tThis mapunit " + mukey + " is rated: " + str(muVal[1]) + " <- " + str(muVals), 1)

                        if not muVal[1] is None and not muVal[1] in outputValues:
                            outputValues.append(muVal[1])

                # End of Lower

            elif aggMethod == "Minimum or Maximum" and tieBreaker == dSDV["tiebreakhighlabel"]:
                #
                # MAX
                #
                if len(domainValues) > 0:
                    #
                    # MAX
                    # Has Domain
                    #
                    #PrintMsg("This option has domain values for MinMax!", 1)

                    for mukey, cokeys in dMapunit.items():
                        dRating = dict()   # save sum of comppct for each rating within a mapunit
                        minIndx = 9999999  # save the lowest index value for each mapunit
                        indexes = list()

                        for cokey in cokeys:
                            compPct = dCompPct[cokey]  # get comppct_r for this component
                            ratingIndx = dComp[cokey]  # get rating index for this component
                            indexes.append(ratingIndx)

                            # save the sum of comppct_r for each rating index in the dRating dictionary
                            if ratingIndx in dRating:
                                dRating[ratingIndx] = dRating[ratingIndx] + compPct

                            else:
                                dRating[ratingIndx] = compPct

                        indexes = sorted(set(indexes), reverse=True)
                        minIndx = indexes[0]  # get the lowest index value

                        if minIndx == notRatedIndex and len(indexes) > 1:
                            # if the lowest index is for 'Not rated', try to get the next higher index
                            minIndx = indexes[1]

                        newrec = [mukey, dAreasym[mukey], dRating[minIndx], domainValues[minIndx]]
                        #PrintMsg("\t" + mukey + ": " + " - " + str(minIndx) + ",  " + domainValues[minIndx], 1)
                        ocur.insertRow(newrec)
                        #PrintMsg("\tOptimistic 3 Mapunit rating: " + str(indexes) + ", " + str(minIndx) + ", " + str(domainValues[minIndx]) + " \n ", 1)

                        if not not domainValues[minIndx] is None and not domainValues[minIndx] in outputValues:
                            outputValues.append(domainValues[minIndx])

                else:
                    #PrintMsg("Testing " + aggMethod + " - " + tieBreaker + ", no domain values", 1)
                    #
                    # MAX
                    # No Domain

                    for mukey, cokeys in dMapunit.items():
                        dRating = dict()  # save sum of comppct for each rating within a mapunit
                        muVals = list()   # list of rating values for each mapunit

                        for cokey in cokeys:
                            compPct = dCompPct[cokey]  # component percent
                            rating = dComp[cokey]  # component rating

                            #if rating != 0:
                            if rating in dRating:
                                dRating[rating] = dRating[rating] + compPct

                            else:
                                dRating[rating] = compPct

                        for rating, compPct in dRating.items():
                            muVals.append([compPct, rating])

                        if len(muVals) > 0:
                            muVal = SortData(muVals, 1, 0, True, True)

                            newrec = [mukey, dAreasym[mukey], muVal[0], muVal[1]]
                            ocur.insertRow(newrec)
                            # muVal[0] is comppct, muVal[1] is rating
                            # PrintMsg("\tThis mapunit " + mukey + " is rated: " + str(muVal[1]) + " <- " + str(muVals), 1)

                        if not muVal[1] is None and not muVal[1] in outputValues:
                            outputValues.append(muVal[1])

                # End of Higher


        outputValues.sort()

        if bVerbose:
            PrintMsg("outputValues: " + str(outputValues), 1)

        return outputTbl, outputValues

    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return outputTbl, outputValues

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


        return outputTbl, outputValues

## ===================================================================================
def AggregateCo_DCD(gdb, sdvAtt, sdvFld, flatTbl, bZero, cutOff, tieBreaker):
    #
    # Component aggregation to the dominant condition for the mapunit.
    #
    # 2020-02-25. Looking at options for normalizing sum-of-comppct_r to 100 and reporting that value.
    #
    # Current problem: where dcp = 50%, it should trump dcd where lesser components sum to the same 50%
    #
    try:
        # bVerbose = True

        arcpy.SetProgressorLabel("Aggregating rating information to the map unit level")

        #
        if bVerbose:
            PrintMsg("Current function : " + sys._getframe().f_code.co_name, 1)
            PrintMsg("This function uses dValues dictionary", 1)

        # Create final output table with MUKEY, COMPPCT_R and sdvFld
        outputTbl = os.path.join(gdb, tblName)

        inFlds = ["MUKEY", "COKEY", "COMPPCT_R", dSDV["attributecolumnname"].upper(), "AREASYMBOL"]
        outFlds = ["MUKEY", "COMPPCT_R", dSDV["resultcolumnname"].upper(), "AREASYMBOL"]

        # Keep any null values as part of the aggregation
        if bZero:
            # Default setting
            whereClause = "COMPPCT_R >=  " + str(cutOff)

        else:
            whereClause = "COMPPCT_R >=  " + str(cutOff) + " AND " + dSDV["attributecolumnname"].upper() + " IS NOT NULL"

        if tieBreaker == dSDV["tiebreaklowlabel"]:
            sqlClause =  (None, " ORDER BY MUKEY ASC, COMPPCT_R DESC, " + dSDV["attributecolumnname"].upper() + " ASC ")

        else:
            sqlClause =  (None, " ORDER BY MUKEY ASC, COMPPCT_R DESC, " + dSDV["attributecolumnname"].upper() + " DESC ")

        if bVerbose:
            PrintMsg("whereClause: " + whereClause, 1)

        # flatTbl must be in a file geodatabase to support ORDER_BY

        if arcpy.Exists(outputTbl):
            #time.sleep(2)
            arcpy.Delete_management(outputTbl)

        outputTbl = CreateOutputTable(tmpDS, flatTbl, outputTbl, dFieldInfo)
        outputValues = list()

        if outputTbl == "":
            raise MyError("Failed to create output table (" + os.path.basename(outputTbl) + ")")

        lastCokey = "xxxx"
        dComp = dict()
        dCompPct = dict()
        dMapunit = dict()
        dAreasym = dict()

        if len(dValues) and not dSDV["tiebreakdomainname"] is None:
            if bZero and not "NONE" in dValues:
                # Add Null value to domain
                dValues["NONE"] = [[len(dValues), None]]

                if bVerbose:
                    PrintMsg("Domain Values: " + str(domainValues), 1)
                    PrintMsg("dValues: " + str(dValues), 1)
                    PrintMsg("data type: " + dSDV["effectivelogicaldatatype"].lower(), 1 )

            with arcpy.da.SearchCursor(flatTbl, inFlds, sql_clause=sqlClause, where_clause=whereClause) as cur:
                # Use tiebreak rules and rating index values

                for rec in cur:
                    # read raw data from initial table
                    mukey, cokey, comppct, rating, areasym = rec
                    dRating = dict()

                    # get index for this rating
                    ratingIndx = dValues[str(rating).upper()][0]

                    #if bVerbose and mukey == '2969034':
                    #    PrintMsg("\t" + str(rec), 1)

                    dComp[cokey] = ratingIndx
                    dCompPct[cokey] = comppct
                    dAreasym[mukey] = areasym

                    # summarize the comppct for this rating and map unit combination
                    try:
                        dRating[ratingIndx] += comppct

                    except:
                        dRating[ratingIndx] = comppct

                    # Create a list of cokeys for each mapunit, in descending order for comppct
                    try:
                        dMapunit[mukey].append(cokey)

                    except:
                        dMapunit[mukey] = [cokey]

        else:
            # No domain values
            # 2 Read initial table (no domain values, must use alpha sort for tiebreaker)
            # Issue noted by ?? that without tiebreaking method, inconsistent results may occur
            #
            with arcpy.da.SearchCursor(flatTbl, inFlds, sql_clause=sqlClause, where_clause=whereClause) as cur:
                #
                # numeric values
                if dSDV["effectivelogicaldatatype"].lower() in ['integer', 'float']:
                    fldPrecision = dSDV["attributeprecision"]

                    for rec in cur:
                        mukey, cokey, comppct, rating, areasym = rec
                        # Assume that this is the rating for the component
                        # PrintMsg("\t" + str(rec[1]) + ": " + str(rec[3]), 1)
                        dComp[cokey] = rating
                        dAreasym[mukey] = areasym

                        # save component percent for each component
                        dCompPct[cokey] = comppct

                        # save list of components for each mapunit
                        # key value is mukey; dictionary value is a list of cokeys
                        try:
                            dMapunit[mukey].append(cokey)

                        except:
                            dMapunit[mukey] = [cokey]

                else:
                    #
                    # choice, text, vtext values
                    for rec in cur:
                        # Assume that this is the rating for the component
                        mukey, cokey, comppct, rating, areasym = rec

                        if not rating is None:
                            dComp[cokey] = rating.strip()

                        else:
                            dComp[cokey] = None

                        # save component percent for each component
                        dCompPct[cokey] = comppct
                        dAreasym[mukey] = areasym

                        # save list of components for each mapunit
                        # key value is mukey; dictionary value is a list of cokeys
                        try:
                            dMapunit[mukey].append(cokey)

                        except:
                            dMapunit[mukey] = [cokey]

        if len(dMapunit) == 0:
            raise MyError("No data in dMapunit dictionary")

        else:
            PrintMsg("dMapunit has " + Number_Format(len(dMapunit), 0, True) + " items", 1)

        # Aggregate component-level data to the map unit
        #
        # Try capturing number of component ratings per mapunit and use that number to normalize
        # the comppct_r written to the SDV_Rating table.
        #
        iCnt = 0

        with arcpy.da.InsertCursor(outputTbl, outFlds) as ocur:
            # Using domain values and tiebreaker is DCD Lower

            if tieBreaker == dSDV["tiebreaklowlabel"]:
                #
                # No domain values, Lower
                for mukey, cokeys in dMapunit.items():
                    dRating = dict()  # save sum of comppct for each rating within a mapunit
                    muVals = list()   # may not need this for DCD
                    areasym = dAreasym[mukey]
                    totalPct = 0
                    dcpPct = dCompPct[cokeys[0]]  # rating for dominant component

                    for cokey in cokeys:
                        # These cokeys should be in comppct descending order
                        compPct = dCompPct[cokey]
                        rating = dComp[cokey]
                        totalPct += compPct

                        if rating in dRating:
                            sumPct = dRating[rating] + compPct
                            dRating[rating] = sumPct  # this part could be compacted

                        else:
                            dRating[rating] = compPct

                    if dcpPct < 50:
                        # sort all ratings and select dominant condition

                        for rating, compPct in dRating.items():
                            muVals.append([compPct, rating])

                        muValues = SortData(muVals, 0, 1, True, False)  # switched from True, False
                        muPct, muVal = muValues

                        if totalPct > 0:
                            muPct = round(100 * (muPct / float(totalPct)), 0)

                        else:
                            muPct = 0

                    else:
                        muPct = round(100 * (dcpPct / float(totalPct)), 0)
                        muVal = dComp[cokeys[0]]

                    newrec = [mukey, muPct, muVal, areasym]
                    ocur.insertRow(newrec)
                    iCnt += 1

                    if not newrec[2] is None and not newrec[2] in outputValues:
                        outputValues.append(newrec[2])

            elif tieBreaker == dSDV["tiebreakhighlabel"]:
                #
                # No domain values, Higher
                for mukey, cokeys in dMapunit.items():
                    dRating = dict()   # save sum of comppct for each rating within a mapunit
                    muVals = list()   # may not need this for DCD
                    areasym = dAreasym[mukey]
                    totalPct = 0
                    dcpPct = dCompPct[cokeys[0]]  # rating for dominant component

                    for cokey in cokeys:
                        compPct = dCompPct[cokey]
                        rating = dComp[cokey]
                        totalPct += compPct

                        if rating in dRating:
                            sumPct = dRating[rating] + compPct
                            dRating[rating] = sumPct  # this part could be compacted

                        else:
                            dRating[rating] = compPct

                    if dcpPct < 50:
                        # sort all ratings and select dominant condition

                        for rating, compPct in dRating.items():
                            muVals.append([compPct, rating])

                        muValues = SortData(muVals, 0, 1, True, True)  # switched from True, True

                        muPct, muVal = muValues

                        if totalPct > 0:
                            muPct = round(100 * (muPct / float(totalPct)), 0)

                        else:
                            muPct = 0

                    else:
                        muPct = round(100 * (dcpPct / float(totalPct)), 0)
                        muVal = dComp[cokeys[0]]

                    newrec = [mukey, muPct, muVal, areasym]
                    ocur.insertRow(newrec)
                    iCnt += 1

                    if not newrec[2] is None and not newrec[2] in outputValues:
                        outputValues.append(newrec[2])

            else:
                # tiebreakrule: 1 (select higher value); -1 (select the lower value)
                #
                # tiebreakruleoptionflag controls whether user can change the tiebreakrule option
                #
                err = "Failed to aggregate map unit data"
                raise MyError(err)

        if iCnt == 0:
            raise MyError("Warning! No data written to output table.")

        else:
            PrintMsg("Wrote " + Number_Format(len(dMapunit), 0, True) + " records to " + os.path.basename(outputTbl), 1)

        outputValues.sort()

        if (bZero and outputValues ==  [0.0, 0.0]):
            err = "No data for " + sdvAtt
            raise MyError(err)

        if dSDV["effectivelogicaldatatype"].lower() in ['integer', 'float']:

            for rating in outputValues:

                if rating in dValues:
                    dValues[rating][1] = rating

        else:
            for rating in outputValues:
                #PrintMsg("dValues for " + rating.upper() + ": " + str(dValues[rating.upper()][1]), 1)

                if rating.upper() in dValues and dValues[rating.upper()][1] != rating:
                    # rating is in dValues but case is wrong
                    # fix dValues value
                    #PrintMsg("\tChanging dValue rating to: " + rating, 1)
                    dValues[rating.upper()][1] = rating

        if dSDV["effectivelogicaldatatype"].lower() in ["float", "integer"]:
            return outputTbl, outputValues

        else:
            return outputTbl, sorted(outputValues, key=lambda s: s.lower())

    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return outputTbl, outputValues

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

        return outputTbl, outputValues

## ===================================================================================
def AggregateCo_DCP_DTWT(gdb, sdvAtt, sdvFld, flatTbl, bZero, cutOff, tieBreaker):
    #
    # Depth to Water Table, dominant component
    #
    # Aggregate mapunit-component data to the map unit level using dominant component
    # and the tie breaker setting to select the lowest or highest monthly rating.
    # Use this for COMONTH table. domainValues
    #
    # PROBLEMS with picking the correct depth for each component. Use tiebreaker to pick
    # highest or lowest month and then aggregate to DCP?
    # Added areasymbol to output

    try:
        arcpy.SetProgressorLabel("Aggregating rating information to the map unit level")

        #
        if bVerbose:
            PrintMsg("Current function : " + sys._getframe().f_code.co_name, 1)

        # Create final output table with MUKEY, COMPPCT_R and sdvFld
        outputTbl = os.path.join(gdb, tblName)
        #attribcolumn = dSDV["attributecolumnname"].upper()
        #resultcolumn = dSDV["resultcolumnname"].upper()

        inFlds = ["MUKEY", "COMPPCT_R", dSDV["attributecolumnname"].upper(), "AREASYMBOL"]
        outFlds = ["MUKEY", "COMPPCT_R", dSDV["resultcolumnname"].upper(), "AREASYMBOL"]
        whereClause = "COMPPCT_R >=  " + str(cutOff)  # Leave in NULLs and try to substitute 200
        sqlClause =  (None, " ORDER BY MUKEY ASC, COMPPCT_R DESC")

        if arcpy.Exists(outputTbl):
            arcpy.Delete_management(outputTbl)

        outputTbl = CreateOutputTable(tmpDS, flatTbl, outputTbl, dFieldInfo)
        outputValues = list()

        if outputTbl == "":
            return outputTbl, outputValues

        dMapunit = dict()
        dAreasym = dict()
        dataCnt = int(arcpy.GetCount_management(flatTbl).getOutput(0))

        with arcpy.da.SearchCursor(flatTbl, inFlds, sql_clause=sqlClause, where_clause=whereClause) as cur:
            #cnt = 0
            #PrintMsg("Reading input table " + os.path.basename(flatTbl) + "...", 1)
            arcpy.SetProgressor("step", "Reading input table " + os.path.basename(flatTbl) + "...", 0, dataCnt, 1 )

            # "MUKEY", "COMPPCT_R", attribcolumn
            for rec in cur:
                arcpy.SetProgressorPosition()
                mukey, compPct, rating, areasym = rec
                dAreasym[mukey] = areasym

                try:
                    dMapunit[mukey].append([compPct, rating])

                except:
                    dMapunit[mukey] = [[compPct, rating]]

        del flatTbl  # Trying to save some memory 2016-06-23

        with arcpy.da.InsertCursor(outputTbl, outFlds) as ocur:
            #PrintMsg("Writing to output table " + outputTbl + "...", 1)
            arcpy.SetProgressor("step", "Writing to output table (" + os.path.basename(outputTbl) + ")", 0, len(dMapunit), 1 )

            for mukey, coVals in dMapunit.items():
                arcpy.SetProgressorPosition()
                # Grab the first pair of values (pct, depth) from the sorted list.
                # This is the dominant component rating using tie breaker setting
                #dcpRating = SortData(coVals, 0, 1, True, True)
                dcpRating = SortData(coVals, 0, 1, True, False)  # For depth to water table, we want the lower value (closer to surface)
                rec =[mukey, dcpRating[0], dcpRating[1], dAreasym[mukey]]
                ocur.insertRow(rec)

                if  not rec[2] is None and not rec[2] in outputValues:
                    outputValues.append(rec[2])

        outputValues.sort()
        return outputTbl, outputValues

    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return outputTbl, outputValues

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

        return outputTbl, outputValues

## ===================================================================================
def AggregateCo_DCD_DTWT(gdb, sdvAtt, sdvFld, flatTbl, bZero, cutOff, tieBreaker):
    #
    # Not being used???
    #
    # Aggregate mapunit-component-comonth data to the map unit level using dominant condition
    # and the tie breaker setting to select the lowest or highest monthly rating.
    # Use this for COMONTH table. domainValues
    # Added areasymbol to output
    try:
        arcpy.SetProgressorLabel("Aggregating rating information to the map unit level")

        #
        if bVerbose:
            PrintMsg("Current function : " + sys._getframe().f_code.co_name, 1)

        # Create final output table with MUKEY, COMPPCT_R and sdvFld
        outputTbl = os.path.join(gdb, tblName)
        #attribcolumn = dSDV["attributecolumnname"].upper()
        #resultcolumn = dSDV["resultcolumnname"].upper()

        inFlds = ["MUKEY", "COKEY", "COMPPCT_R", dSDV["attributecolumnname"].upper(), "AREASYMBOL"]
        outFlds = ["MUKEY", "COMPPCT_R", dSDV["attributecolumnname"].upper(), "AREASYMBOL"]
        whereClause = "COMPPCT_R >=  " + str(cutOff)  # Leave in NULLs and try to substitute 200
        sqlClause =  (None, " ORDER BY MUKEY ASC, COMPPCT_R DESC")

        if arcpy.Exists(outputTbl):
            arcpy.Delete_management(outputTbl)

        outputTbl = CreateOutputTable(tmpDS, flatTbl, outputTbl, dFieldInfo)
        outputValues = list()

        if outputTbl == "":
            return outputTbl, outputValues

        dMapunit = dict()
        dComponent = dict()
        dCoRating = dict()
        dAreasym = dict()

        with arcpy.da.SearchCursor(flatTbl, inFlds, sql_clause=sqlClause, where_clause=whereClause) as cur:

            # MUKEY,COKEY , COMPPCT_R, attribcolumn
            for rec in cur:
                mukey, cokey, compPct, rating, areasym = rec

                if rating is None:
                    rating = nullRating

                dAreasym[mukey] = areasym

                # Save list of cokeys for each mukey
                try:
                    if not cokey in dMapunit[mukey]:
                        dMapunit[mukey].append(cokey)

                except:
                    dMapunit[mukey] = [cokey]

                try:
                    # Save list of rating values along with comppct for each component
                    dComponent[cokey][1].append(rating)

                except:
                    #  Save list of rating values along with comppct for each component
                    dComponent[cokey] = [compPct, [rating]]

        if tieBreaker == dSDV["tiebreakhighlabel"]:
            for cokey, coVals in dComponent.items():
                # Find high or low value for each component
                dCoRating[cokey] = max(coVals[1])

        else:
            for cokey, coVals in dComponent.items():
                # Find high or low value for each component
                dCoRating[cokey] = min(coVals[1])


        dFinalRatings = dict()  # final dominant condition. mukey is key

        for mukey, cokeys in dMapunit.items():
            # accumulate ratings for each mapunit by sum of comppct
            dMuRatings = dict()  # create a dictionary of values for just this map unit
            domPct = 0

            for cokey in cokeys:
                # look at values for each component within the map unit
                rating = dCoRating[cokey]
                compPct = dComponent[cokey][0]

                try:
                    dMuRatings[rating] += compPct

                except:
                    dMuRatings[rating] = compPct

            for rating, compPct in dMuRatings.items():
                # Find rating with highest sum of comppct
                if compPct > domPct:
                    domPct = compPct
                    dFinalRatings[mukey] = [compPct, rating]
                    #PrintMsg("\t" + mukey + ", " + str(compPct) + "%" + ", " + str(rating) + "cm", 1)

            del dMuRatings

        with arcpy.da.InsertCursor(outputTbl, outFlds) as ocur:
            # Write final ratings to output table
            for mukey, vals in dFinalRatings.items():
                rec = mukey, vals[0], vals[1], dAreasym[mukey]
                ocur.insertRow(rec)

                if not rec[2] is None and not rec[2] in outputValues:
                    outputValues.append(rec[2])

        outputValues.sort()
        return outputTbl, outputValues

    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return outputTbl, outputValues

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


        return outputTbl, outputValues


## ===================================================================================
def AggregateCo_Mo_MaxMin(gdb, sdvAtt, sdvFld, flatTbl, bZero, cutOff, tieBreaker):
    #
    # Aggregate mapunit-component data to the map unit level using Minimum or Maximum
    # based upon the TieBreak rule.
    # Use this for COMONTH table. Example Depth to Water Table.
    #
    # It appears that WSS includes 0 percent components in the MinMax. This function
    # is currently set to duplicate this behavior
    # Added areasymbol to output
    #
    # Seems to be a problem with TitleCase Values in maplegendxml vs. SentenceCase in the original data. Domain values are SentenceCase.
    #

    try:
        #
        #bVerbose = True

        arcpy.SetProgressorLabel("Aggregating rating information to the map unit level")

        if bVerbose:
            PrintMsg("Current function : " + sys._getframe().f_code.co_name, 1)

        # Create final output table with MUKEY, COMPPCT_R and sdvFld
        outputTbl = os.path.join(gdb, tblName)
        #attribcolumn = dSDV["attributecolumnname"].upper()
        #resultcolumn = dSDV["resultcolumnname"].upper()

        inFlds = ["MUKEY", "COKEY", "COMPPCT_R", dSDV["attributecolumnname"].upper(), "AREASYMBOL"]
        outFlds = ["MUKEY", "COMPPCT_R", dSDV["resultcolumnname"].upper(), "AREASYMBOL"]
        whereClause = "COMPPCT_R >=  " + str(cutOff)  # Leave in NULLs and try later to substitute dSDV["nullratingreplacementvalue"]
        #whereClause = "COMPPCT_R >=  " + str(cutOff) + " and not " + dSDV["attributecolumnname"].upper() + " is null"
        sqlClause =  (None, " ORDER BY MUKEY ASC, COMPPCT_R DESC")

        if arcpy.Exists(outputTbl):
            arcpy.Delete_management(outputTbl)

        outputTbl = CreateOutputTable(tmpDS, flatTbl, outputTbl, dFieldInfo)
        outputValues = list()

        if outputTbl == "":
            return outputTbl, outputValues

        dMapunit = dict()
        dComponent = dict()
        dCoRating = dict()
        dAreasym = dict()

        #PrintMsg("SQL: " + whereClause, 1)
        #PrintMsg("Fields: " + str(inFlds), 1)

        with arcpy.da.SearchCursor(flatTbl, inFlds, sql_clause=sqlClause, where_clause=whereClause) as cur:

            # MUKEY,COKEY , COMPPCT_R, attribcolumn
            for rec in cur:

                mukey, cokey, compPct, rating, areasym = rec
                dAreasym[mukey] = areasym
                #PrintMsg("\t" + str(rec), 1)


                # Save list of cokeys for each mapunit-mukey
                try:
                    if not cokey in dMapunit[mukey]:
                        dMapunit[mukey].append(cokey)

                except:
                    dMapunit[mukey] = [cokey]

                try:
                    # Save list of rating values along with comppct for each component
                    if not rating is None:
                        dComponent[cokey][1].append(rating)

                except:
                    #  Save list of rating values along with comppct for each component
                    if not rating is None:
                        dComponent[cokey] = [compPct, [rating]]

        if tieBreaker == dSDV["tiebreakhighlabel"]:
            # This is working correctly for DTWT
            # Backwards for Ponding

            # Identify highest value for each component
            for cokey, coVals in dComponent.items():
                # Find high value for each component
                #PrintMsg("Higher values for " + cokey + ": " + str(coVals) + " = " + str(max(coVals[1])), 1)
                dCoRating[cokey] = max(coVals[1])

        else:
            # This is working correctly for DTWT
            # Backwards for Ponding

            # Identify lowest value for each component
            for cokey, coVals in dComponent.items():
                # Find low rating value for each component
                #PrintMsg("Lower values for " + cokey + ": " + str(coVals) + " = " + str(min(coVals[1])), 1)
                dCoRating[cokey] = min(coVals[1])


        dFinalRatings = dict()  # final dominant condition. mukey is key

        for mukey, cokeys in dMapunit.items():
            # accumulate ratings for each mapunit by sum of comppct
            dMuRatings = dict()  # create a dictionary of values for just this map unit
            domPct = 0

            for cokey in cokeys:
                # look at values for each component within the map unit
                try:
                    rating = dCoRating[cokey]
                    compPct = dComponent[cokey][0]

                    try:
                        dMuRatings[rating] += compPct

                    except:
                        dMuRatings[rating] = compPct

                except:
                    pass

            if tieBreaker == dSDV["tiebreakhighlabel"]:
                # This is working correctly for DTWT
                # Backwards for Ponding
                highRating = 0

                for rating, compPct in dMuRatings.items():
                    # Find the highest
                    if rating > highRating:
                        highRating = rating
                        dFinalRatings[mukey] = [compPct, rating]
            else:
                # This is working correctly for DTWT
                # Backwards for Ponding
                lowRating = nullRating

                for rating, compPct in dMuRatings.items():

                    if rating < lowRating and rating is not None:
                        lowRating = rating
                        dFinalRatings[mukey] = [compPct, rating]

            del dMuRatings

        with arcpy.da.InsertCursor(outputTbl, outFlds) as ocur:
            # Write final ratings to output table
            for mukey in sorted(dMapunit):

                try:
                    vals = dFinalRatings[mukey]

                except:
                    sumPct = 0
                    for cokey in dMapunit[mukey]:
                        try:
                            sumPct += dComponent[cokey][0]

                        except:
                            pass

                    vals = [sumPct, nullRating]

                rec = mukey, vals[0], vals[1], dAreasym[mukey]
                ocur.insertRow(rec)

                if not rec[2] is None and not rec[2] in outputValues:
                    outputValues.append(rec[2])

        outputValues.sort()
        return outputTbl, outputValues

    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return outputTbl, outputValues

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

        return outputTbl, outputValues

## ===================================================================================
def AggregateCo_Mo_DCD(gdb, sdvAtt, sdvFld, flatTbl, bZero, cutOff, tieBreaker):
    #
    # Aggregate mapunit-component data to the map unit level using the dominant condition
    # based upon the TieBreak rule.
    # Use this for COMONTH table. Example Depth to Water Table.
    #
    # It appears that WSS includes 0 percent components in the MinMax. This function
    # is currently set to duplicate this behavior
    #
    # Currently there is a problem with the comppct. It ends up being 12X.

    try:
        #
        arcpy.SetProgressorLabel("Aggregating rating information to the map unit level")

        if bVerbose:
            PrintMsg("Current function : " + sys._getframe().f_code.co_name, 1)

        # Create final output table with MUKEY, COMPPCT_R and sdvFld
        outputTbl = os.path.join(gdb, tblName)
        #attribcolumn = dSDV["attributecolumnname"].upper()
        #resultcolumn = dSDV["resultcolumnname"].upper()

        inFlds = ["MUKEY", "COKEY", "COMPPCT_R", dSDV["attributecolumnname"].upper(), "AREASYMBOL"]
        outFlds = ["MUKEY", "COMPPCT_R", dSDV["resultcolumnname"].upper(), "AREASYMBOL"]
        whereClause = "COMPPCT_R >=  " + str(cutOff)  # Leave in NULLs and try to substitute dSDV["nullratingreplacementvalue"]
        #whereClause = "COMPPCT_R >=  " + str(cutOff) + " and not " + dSDV["attributecolumnname"].upper() + " is null"
        sqlClause =  (None, " ORDER BY MUKEY ASC, COMPPCT_R DESC")

        if arcpy.Exists(outputTbl):
            arcpy.Delete_management(outputTbl)

        outputTbl = CreateOutputTable(tmpDS, flatTbl, outputTbl, dFieldInfo)
        outputValues = list()

        if outputTbl == "":
            return outputTbl, outputValues

        dMapunit = dict()
        dComponent = dict()
        dCoRating = dict()
        dAreasym = dict()

        PrintMsg("SQL: " + whereClause, 1)
        PrintMsg("Fields: " + str(inFlds), 1)

        with arcpy.da.SearchCursor(flatTbl, inFlds, sql_clause=sqlClause, where_clause=whereClause) as cur:

            # MUKEY,COKEY , COMPPCT_R, attribcolumn
            for rec in cur:
                #mukey = rec[0]; cokey = rec[1]; compPct = rec[2]; rating = rec[3]
                mukey, cokey, compPct, rating, areasym = rec
                if rating is None:
                    rating = 201

                # Save list of cokeys for each mapunit-mukey
                try:
                    if not cokey in dMapunit[mukey]:
                        dMapunit[mukey].append(cokey)

                except:
                    dMapunit[mukey] = [cokey]
                    dAreasym[mukey] = areasym
                    PrintMsg("Check dAreasymbols setting", 1)

                try:
                    # if the rating value meets the tiebreak rule, save the rating value along with comppct for each component
                    #if not rating is None:
                    if tieBreaker == dSDV["tiebreakhighlabel"]:
                        if rating > dComponent[cokey][1]:
                            dComponent[cokey][1] = rating

                    elif rating < dComponent[cokey][1]:
                        dComponent[cokey][1] = rating

                except:
                    #  Save rating value along with comppct for each component
                    if not rating is None:
                        dComponent[cokey] = [compPct, rating]

        dFinalRatings = dict()  # final dominant condition. mukey is key

        for mukey, cokeys in dMapunit.items():
            # accumulate ratings for each mapunit by sum of comppct
            dMuRatings = dict()
            dMuRatings[mukey] = [None, None]  # create a dictionary of values for just this map unit
            domPct = 0

            for cokey in cokeys:
                # look at values for each component within the map unit
                if cokey in dComponent:

                    compPct, rating = dComponent[cokey]

                    if compPct > domPct:
                        domPct = compPct
                        dMuRatings[mukey] = [compPct, rating]
                        PrintMsg("\t" + mukey + ":" + cokey  + ", " + str(compPct) + "%, " + str(rating), 1)

            dFinalRatings[mukey] = dMuRatings[mukey]

        with arcpy.da.InsertCursor(outputTbl, outFlds) as ocur:
            # Write final ratings to output table
            for mukey in sorted(dFinalRatings):
                compPct, rating = dFinalRatings[mukey]
                rec = mukey, compPct, rating, dAreasym[mukey]
                ocur.insertRow(rec)

                if not rating is None and not rating in outputValues:
                    outputValues.append(rating)

        outputValues.sort()
        return outputTbl, outputValues

    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return outputTbl, outputValues

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


        return outputTbl, outputValues


## ===================================================================================
def AggregateCo_Mo_DCP_Domain(gdb, sdvAtt, sdvFld, flatTbl, bZero, cutOff, tieBreaker):
    #
    # Use this function for Flooding or Ponding Frequency which involves the COMONTH table
    #
    # Need to modify this so that COMPPCT_R is summed using just one value per component, not 12X.
    #
    # We have a case problem with Flooding Frequency Class: 'Very frequent'
    #
    # My tests on ND035 appear to return results based upon dominant condition, not dominant component!
    #

    try:
        # bVerbose = True
        arcpy.SetProgressorLabel("Aggregating rating information to the map unit level")

        #
        if bVerbose:
            PrintMsg("Current function : " + sys._getframe().f_code.co_name, 1)
            PrintMsg("This function uses dValues dictionary", 1)

        # Create final output table with MUKEY, COMPPCT_R and sdvFld
        outputTbl = os.path.join(gdb, tblName)

        inFlds = ["MUKEY", "COKEY", "COMPPCT_R", dSDV["attributecolumnname"].upper(), "AREASYMBOL"]
        outFlds = ["MUKEY", "COMPPCT_R", dSDV["resultcolumnname"].upper(), "AREASYMBOL"]
        whereClause = "COMPPCT_R >=  " + str(cutOff) + " AND " + dSDV["attributecolumnname"].upper() + " IS NOT NULL"

        # flatTbl must be in a file geodatabase to support ORDER_BY
        # Do I really need to sort by attribucolumn when it will be replaced by Domain values later?
        sqlClause =  (None, " ORDER BY MUKEY ASC, COMPPCT_R DESC")


        if arcpy.Exists(outputTbl):
            arcpy.Delete_management(outputTbl)

        outputTbl = CreateOutputTable(tmpDS, flatTbl, outputTbl, dFieldInfo)
        outputValues = list()

        if outputTbl == "":
            return outputTbl, outputValues

        lastCokey = "xxxx"
        dComp = dict()
        dCompPct = dict()
        dMapunit = dict()
        missingDomain = list()
        dCase = dict()
        dAreasym = dict()

        # Read initial table for non-numeric data types
        # 02-03-2016 Try adding 'choice' to this method to see if it handles Cons. Tree/Shrub better
        # than the next method. Nope, did not work. Still have case problems.
        #
        if dSDV["attributelogicaldatatype"].lower() == "string":
            PrintMsg("*dValues for " + dSDV["attributelogicaldatatype"] + " values: " + str(dValues), 1)

            with arcpy.da.SearchCursor(flatTbl, inFlds, sql_clause=sqlClause, where_clause=whereClause) as cur:

                for rec in cur:
                    dAreasym[rec[0]] = rec[4]
                    rating = rec[3]

                    try:
                        # capture component ratings as index numbers instead.
                        dComp[rec[1]].append(dValues[rating.upper()][0])

                    except:
                        dComp[rec[1]] = [dValues[rating.upper()][0]]
                        dCompPct[rec[1]] = rec[2]
                        dCase[rating.upper()] = rating  # save original value using uppercase key


                        # save list of components for each mapunit
                        try:
                            dMapunit[rec[0]].append(rec[1])

                        except:
                            dMapunit[rec[0]] = [rec[1]]

        elif dSDV["attributelogicaldatatype"].lower() in ["float", "integer", "choice"]:

            PrintMsg("**dValues for " + dSDV["attributelogicaldatatype"] + " values: " + str(dValues), 1)

            with arcpy.da.SearchCursor(flatTbl, inFlds, sql_clause=sqlClause, where_clause=whereClause) as cur:

                for rec in cur:
                    dAreasym[rec[0]] = rec[4]
                    rating = rec[3]

                    try:
                        # capture component ratings as index numbers instead
                        if rating is None:
                            dComp[rec[1]].append(dValues["<Null>"][0])

                        else:
                            dComp[rec[1]].append(dValues[rating.upper()][0])

                    except:
                        #PrintMsg("domainValues is empty, but legendValues has " + str(legendValues), 1)
                        dCase[rating.upper()] = rating

                        if rating.upper() in dValues:
                            dComp[rec[1]] = [dValues[rating.upper()][0]]
                            dCompPct[rec[1]] = rec[2]

                            # compare actual rating value to domainValues to make sure case is correct
                            if not rating in domainValues: # this is a case problem
                                # replace the original dValue item
                                dValues[rating.upper()][1] = rating

                                # replace the value in domainValues list
                                for i in range(len(domainValues)):
                                    if domainValues[i].upper() == rating.upper():
                                        domainValues[i] = rating

                        else:
                            # dValues is keyed on uppercase string rating
                            #
                            if not rating in missingDomain:
                                # Try to add missing value to dDomainValues dict and domainValues list
                                dValues[rating.upper()] = [len(dValues), rating]
                                #domainValues.append(rating])
                                #domainValuesUp.append(rating.upper()
                                #missingDomain.append(rating)
                                PrintMsg("\tAdding value '" + str(rating) + "' to domainValues", 1)

                        # save list of components for each mapunit
                        try:
                            dMapunit[rec[0]].append(rec[1])

                        except:
                            dMapunit[rec[0]] = [rec[1]]

        else:
            PrintMsg("Problem with handling domain values of type '" + dSDV["attributelogicaldatatype"] + "'", 1)


        # Aggregate monthly index values to a single value for each component
        # Sort depending upon tiebreak setting
        # Update dictionary with a single index value for each component
        #
        # Testing on 2017-11-07 shows that I'm ending up with lower ratings when tiebreak is set High
        #PrintMsg("Not sure about this sorting code for tiebreaker", 1)

        if tieBreaker == dSDV["tiebreakhighlabel"]:
            # "Higher" (default for flooding and ponding frequency)
            #PrintMsg("Tiebreak High: " + dSDV["tiebreakhighlabel"], 1)
            for cokey, indexes in dComp.items():
                val = sorted(indexes, reverse=True)[0]  #original that does not work
                #val = sorted(indexes, reverse=False)[0]  #test 1
                dComp[cokey] = val
        else:
            #PrintMsg("Tiebreak low: " + dSDV["tiebreaklowlabel"], 1)
            for cokey, indexes in dComp.items():
                val = sorted(indexes)[0]
                dComp[cokey] = val

        # Save list of component data to each mapunit
        dRatings = dict()

        with arcpy.da.InsertCursor(outputTbl, outFlds) as ocur:

            if tieBreaker == dSDV["tiebreakhighlabel"]:
                # Default for flooding and ponding frequency
                #
                #PrintMsg("domainValues: " + str(domainValues), 1)

                for mukey, cokeys in dMapunit.items():
                    dRating = dict()   # save sum of comppct for each rating within a mapunit
                    muVals = list()   # may not need this for DCD

                    for cokey in cokeys:
                        #PrintMsg("\tB ratingIndx: " + str(dComp[cokey]), 1)
                        compPct = dCompPct[cokey]
                        ratingIndx = dComp[cokey]
                        muVals.append([compPct, ratingIndx])

                        # I think this section of code is in effect doing a dominant condition
                        # Fixed 2017-11-07
                        #if ratingIndx in dRating:
                        #    sumPct = dRating[ratingIndx] + compPct
                        #    dRating[ratingIndx] = sumPct  # this part could be compacted

                        #else:
                        #    dRating[ratingIndx] = compPct

                        # End of bad code

                    #for rating, compPct in dRating.items():
                    #    muVals.append([compPct, rating])

                    #newVals = sorted(muVals, key = lambda x : (-x[0], x[1]))[0]  # Works for maplegendkey=2
                    #newVals = sorted(sorted(muVals, key = lambda x : x[0], reverse=True), key = lambda x : x[1], reverse=True)[0]

                    muVal = SortData(muVals, 0, 1, True, True)
                    newrec = [mukey, muVal[0], domainValues[muVal[1]], dAreasym[mukey]]
                    ocur.insertRow(newrec)

                    if  not newrec[2] is None and not newrec[2] in outputValues:
                        outputValues.append(newrec[2])

            else:
                # Lower
                PrintMsg("Final lower tiebreaker", 1)

                for mukey, cokeys in dMapunit.items():
                    dRating = dict()  # save sum of comppct for each rating within a mapunit
                    muVals = list()   # may not need this for DCD

                    for cokey in cokeys:
                        try:
                            #PrintMsg("\tA ratingIndx: " + str(dComp[cokey]), 1)
                            compPct = dCompPct[cokey]
                            ratingIndx = dComp[cokey]
                            muVals.append([compPct, ratingIndx])

                        except:
                            pass

                    muVal = SortData(muVals, 0, 1, True, False)
                    newrec = [mukey, muVal[0], domainValues[muVal[1]], dAreasym[mukey]]
                    ocur.insertRow(newrec)

                    if not newrec[2] is None and not newrec[2] in outputValues:
                        outputValues.append(newrec[2])


        outputValues.sort()
        return outputTbl, outputValues

    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return outputTbl, outputValues

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

        return outputTbl, outputValues

## ===================================================================================
def AggregateCo_Mo_DCD_Domain(gdb, sdvAtt, sdvFld, flatTbl, bZero, cutOff, tieBreaker):
    #
    # Flooding or ponding frequency, dominant condition
    #
    # Aggregate mapunit-component data to the map unit level using dominant condition.
    # Use domain values to determine sort order for tiebreaker
    #
    # Need to modify this function to correctly sum the comppct_r for the final output table.

    # Using global dValues[key = uppercase-domain value] value = [sequence, domain value]

    try:
        arcpy.SetProgressorLabel("Aggregating rating information to the map unit level")

        #
        #bVerbose = False

        if bVerbose:
            PrintMsg("Current function : " + sys._getframe().f_code.co_name, 1)
            PrintMsg("This function uses dValues dictionary", 1)

        # Create final output table with MUKEY, COMPPCT_R and sdvFld
        outputTbl = os.path.join(gdb, tblName)

        inFlds = ["MUKEY", "COKEY", "COMPPCT_R", dSDV["attributecolumnname"].upper(), "AREASYMBOL"]
        outFlds = ["MUKEY", "COMPPCT_R", dSDV["resultcolumnname"].upper(), "AREASYMBOL"]

        if bZero:
            whereClause = "COMPPCT_R >=  " + str(cutOff) + " AND " + dSDV["attributecolumnname"].upper() + " IS NOT NULL"

        else:
            whereClause = "COMPPCT_R >=  " + str(cutOff)

        # flatTbl must be in a file geodatabase to support ORDER_BY
        # Do I really need to sort by attribucolumn when it will be replaced by Domain values later?
        sqlClause =  (None, " ORDER BY MUKEY ASC, COMPPCT_R DESC")

        if arcpy.Exists(outputTbl):
            arcpy.Delete_management(outputTbl)

        outputTbl = CreateOutputTable(tmpDS, flatTbl, outputTbl, dFieldInfo)
        outputValues = list()

        if outputTbl == "":
            return outputTbl, outputValues

        dComp = dict()     # Try replacing this and dCompPct with dCompRating
        dCompPct = dict()
        dCompRating = dict()  # Dictionary with cokey as key, tuple(compPct, ratingIndx)

        dMapunit = dict()
        missingDomain = list()
        dAreasym = dict()
        #dCase = dict()

        # Read initial table for non-numeric soil properties. Capture domain values and all component ratings.
        #
        if not dSDV["attributetype"].lower() == "interpretation" and dSDV["attributelogicaldatatype"].lower() in ["string", "vtext"]:  # Changed here 2016-04-28
            #
            # No domain values for non-interp string ratings
            # !!! Probably never using this section of code.
            #
            if bVerbose:
                PrintMsg((40 * '*'), 1)
                PrintMsg("*dValues for " + dSDV["attributelogicaldatatype"] + " values: " + str(dValues), 1)
                PrintMsg("domainValues for " + dSDV["attributelogicaldatatype"] + " values: " + str(domainValues), 1)
                PrintMsg((40 * '*'), 1)

            with arcpy.da.SearchCursor(flatTbl, inFlds, sql_clause=sqlClause, where_clause=whereClause) as cur:

                if bVerbose:
                    PrintMsg("Reading initial data...", 1)

                for rec in cur:
                    # "MUKEY", "COKEY", "COMPPCT_R", RATING
                    mukey, cokey, compPct, rating, areasym = rec
                    dAreasym[mukey] = areasym
                    #dComp[cokey] = rating
                    #dCompPct[cokey] = compPct
                    dCompRating[cokey] = [compPct, rating]
                    #dCase[str(rating).upper()] = rating  # save original value using uppercase key

                    # save list of components for each mapunit
                    try:
                        dMapunit[mukey].append(cokey)

                    except:
                        dMapunit[mukey] = [cokey]

        elif dSDV["attributelogicaldatatype"].lower() in ["string", "float", "integer", "choice"]:
            # Interp or numeric soil properties
            # Flooding and Ponding Frequency would fall in the second section below that has a domain

            if len(domainValues) > 1 and not "None" in domainValues:
                PrintMsg("******************* Immediately adding 'None' to dValues ****************" , 1)
                #dValues["<NULL>"] = [len(dValues), None]
                #domainValues.append("None")

            if bVerbose:
                PrintMsg("**domainValues for " + dSDV["attributelogicaldatatype"] + " values: " + str(domainValues) + " \n ", 1)
                PrintMsg("**dValues for " + dSDV["attributelogicaldatatype"] + " values: " + str(dValues), 1)


            if  dSDV["tiebreakdomainname"] is None:
                # There are no domain values. We must make sure that the legend values are the same as
                # the output values.
                #
                PrintMsg("No domain name for this property", 1)

                with arcpy.da.SearchCursor(flatTbl, inFlds, sql_clause=sqlClause, where_clause=whereClause) as cur:

                    if bVerbose:
                        PrintMsg("Reading initial data...", 1)

                    for rec in cur:
                        mukey, cokey, compPct, rating, areasym = rec
                        dAreasym[mukey] = areasym

                        # save list of components for each mapunit
                        try:
                            dMapunit[mukey].append(cokey)

                        except:
                            dMapunit[mukey] = [cokey]

                        # this is a new component record. create a new dictionary item.
                        #
                        if not cokey in dComp:

                            if not rating is None:
                                dCase[str(rating).upper()] = rating

                                if str(rating).upper() in dValues:
                                    dValues[str(rating).upper()][1] = rating
                                    dCompRating[cokey] = [compPct, dValues[str(rating).upper()][0]]

                                    if not rating in domainValues: # this is a case problem
                                        # replace the original dValue item
                                        dValues[str(rating).upper()][1] = rating

                                        # replace the value in domainValues list
                                        for i in range(len(domainValues)):
                                            if str(domainValues[i]).upper() == str(rating).upper():
                                                domainValues[i] = rating


                                else:
                                    # dValues is keyed on uppercase string rating or is Null
                                    #PrintMsg("\tdValue not found for: " + str(rec), 1)
                                    if not str(rating) in missingDomain:

                                        dValues[str(rating).upper()] = [len(dValues), rating]
                                        domainValues.append(rating)
                                        missingDomain.append(str(rating))
                                        dCompRating[cokey] = [compPct, rating]

                                        #PrintMsg("\tAdding value '" + str(rating) + "' to domainValues", 1)

                            else:
                                # Rating is Null
                                dCompRating[cokey] = [compPct, None]



            else:
                # New code for Ponding Frequency which has a domain
                #
                PrintMsg(".", 1)
                PrintMsg("Ponding Frequency code needs to check to make sure that dValues dictionary is populate.", 1)
                PrintMsg("If it is not, build it using domainValues list", 1)
                PrintMsg("Currently using an if-else below, which is not efficient", 1)
                PrintMsg(".", 1)
                PrintMsg("Domain name for this property: '" + dSDV["tiebreakdomainname"] + "'", 1)
                PrintMsg("domainValues: " + str(domainValues) + " \n ", 1)
                PrintMsg("dValues     : " + str(dValues), 1)

                if tieBreaker == dSDV["tiebreakhighlabel"]:

                    with arcpy.da.SearchCursor(flatTbl, inFlds, sql_clause=sqlClause, where_clause=whereClause) as cur:
                        if bVerbose:
                            PrintMsg("Reading initial data from " + flatTbl + "...", 1)

                        for rec in cur:
                            mukey, cokey, compPct, ratingClass, areasym = rec
                            dAreasym[mukey] = areasym

                            if not ratingClass is None:

                                # Get the rating sequence number from the ordered domain
                                try:
                                    if ratingClass in dValues:
                                        ratingIndx = dValues[str(ratingClass).upper()][0]

                                    else:
                                        ratingIndx = domainValues.index(ratingClass)

                                    # this is a new component record. create a new dictionary item.
                                    #
                                    if not cokey in dCompRating:
                                        # save list of components for each mapunit
                                        dCompRating[cokey] = [compPct, ratingIndx]

                                        try:
                                            # existing mapunit
                                            dMapunit[mukey].append(cokey)

                                        except:
                                            # new mapunit
                                            dMapunit[mukey] = [cokey]

                                    else:
                                        # other months for this component
                                        # if this new index is greater than the old one, keep  it
                                        oldIndx = dCompRating[cokey][1]

                                        if oldIndx < ratingIndx:
                                            dCompRating[cokey][1] = ratingIndx

                                except KeyError:
                                    # encountered value that is not a member of the domain
                                    # Example: "Common" is obsolete value in the Ponding Frequency Class
                                    PrintMsg("KeyError for ratingIndx of '" + str(ratingClass) + "' in dValues: " + str(dValues), 1)
                                    pass


                elif tieBreaker == dSDV["tiebreaklowlabel"]:

                    with arcpy.da.SearchCursor(flatTbl, inFlds, sql_clause=sqlClause, where_clause=whereClause) as cur:
                        if bVerbose:
                            PrintMsg("Reading initial data from " + flatTbl + "...", 1)

                        for rec in cur:
                            mukey, cokey, compPct, ratingClass, areasym = rec
                            #mukey = int(mukey)
                            #cokey = int(cokey)
                            dAreasym[mukey] = areasym

                            if not ratingClass is None:

                                # Get the rating sequence number from the ordered domain
                                try:
                                    ratingIndx = dValues[str(ratingClass).upper()][0]

                                    # this is a new component record. create a new dictionary item.
                                    #
                                    if not cokey in dCompRating:
                                        # save list of components for each mapunit
                                        dCompRating[cokey] = [compPct, ratingIndx]

                                        try:
                                            # existing mapunit
                                            dMapunit[mukey].append(cokey)

                                        except:
                                            # new mapunit
                                            dMapunit[mukey] = [cokey]

                                    else:
                                        # other months for this component
                                        # if this new index is greater than the old one, keep  it
                                        oldIndx = dCompRating[cokey][1]

                                        if oldIndx > ratingIndx:
                                            dCompRating[cokey][1] = ratingIndx

                                except KeyError:
                                    # encountered value that is not a member of the domain
                                    # Example: "Common" is obsolete value in the Ponding Frequency Class
                                    pass


        else:
            err = "Problem with handling domain values of type '" + dSDV["attributelogicaldatatype"]
            raise MyError(err)

        # Aggregate monthly index values to a single value for each component??? Would it not be better to
        # create a new function for COMONTH-DCD? Then I could simplify this function.
        #
        # Sort depending upon tiebreak setting
        # Update dictionary with a single index value for each component
        #if not dSDV["attributelogicaldatatype"].lower() in ["string", "vText"]:

        if bVerbose:
            PrintMsg("Aggregating to a single value per component which would generally only apply to COMONTH properties?", 1)


        # Save list of component rating data to each mapunit, sort and write out
        # a single map unit rating
        #
        dRatings = dict()

        if bVerbose:
            PrintMsg("Writing map unit rating data (" + str(len(dMapunit)) + " values) to final output table", 1)
            PrintMsg("Using tiebreaker '" + tieBreaker + "' (where choices are " + dSDV["tiebreaklowlabel"] + " or " + dSDV["tiebreakhighlabel"] + ")", 1)

        if tieBreaker == dSDV["tiebreakhighlabel"]:
            with arcpy.da.InsertCursor(outputTbl, outFlds) as ocur:

                for mukey, cokeys in dMapunit.items():
                    # Since this is COMONTH data, each cokey could be listed 12X.
                    dRating = dict()  # save sum of comppct for each rating within a mapunit
                    muVals = list()   # may not need this for DCD

                    for cokey in cokeys:

                        compPct, ratingIndx = dCompRating[cokey]

                        if ratingIndx in dRating:
                            dRating[ratingIndx] += compPct

                        else:
                            dRating[ratingIndx] = compPct

                    for ratingIndx, compPct in dRating.items():
                        muVals.append([compPct, ratingIndx])

                    if len(muVals) > 0:
                        #This is the final aggregation from component to map unit rating
                        muVal = SortData(muVals, 0, 1, True, True)  # high
                        del dRating

                        try:
                            # Get final rating class value using index
                            ratingClass = domainValues[muVal[1]]
                            compPct = muVal[0]

                        except:
                            err = "Failed to get rating for muVals: " + str(muVals)
                            raise MyError(err)

                        newrec = [mukey, compPct, ratingClass, dAreasym[mukey]]
                        ocur.insertRow(newrec)
                        PrintMsg(newrec,1)

                        if not ratingClass is None and not ratingClass in outputValues:
                            outputValues.append(ratingClass)

                    else:
                        PrintMsg("No data in dRating for " + mukey + ": " + str(dRating), 1)

        elif tieBreaker == dSDV["tiebreaklowlabel"]:
            with arcpy.da.InsertCursor(outputTbl, outFlds) as ocur:

                for mukey, cokeys in dMapunit.items():
                    # Since this is COMONTH data, each cokey could be listed 12X.
                    dRating = dict()  # save sum of comppct for each rating within a mapunit
                    muVals = list()   # may not need this for DCD

                    for cokey in cokeys:

                        compPct, ratingIndx = dCompRating[cokey]

                        if ratingIndx in dRating:
                            dRating[ratingIndx] += compPct

                        else:
                            dRating[ratingIndx] = compPct

                    for ratingIndx, compPct in dRating.items():
                        muVals.append([compPct, ratingIndx])

                    if len(muVals) > 0:
                        #This is the final aggregation from component to map unit rating
                        muVal = SortData(muVals, 0, 1, True, False) # low
                        del dRating

                        try:
                            # Get final rating class value using index
                            ratingClass = domainValues[muVal[1]]
                            compPct = muVal[0]

                        except:
                            err = "Failed to get rating for muVals: " + str(muVals)
                            raise MyError(err)

                        newrec = [mukey, compPct, ratingClass, dAreasym[mukey]]
                        ocur.insertRow(newrec)

                        if not ratingClass is None and not ratingClass in outputValues:
                            outputValues.append(ratingClass)

        del dComp
        del dCompPct
        del dAreasym
        outputValues.sort()
        return outputTbl, outputValues

    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return outputTbl, outputValues

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

        return outputTbl, outputValues

## ===================================================================================
def AggregateCo_Mo_DCD_DomainX(gdb, sdvAtt, sdvFld, flatTbl, bZero, cutOff, tieBreaker):
    #
    # Flooding or ponding frequency, dominant condition
    #
    # Aggregate mapunit-component data to the map unit level using dominant condition.
    # Use domain values to determine sort order for tiebreaker
    #
    # Need to modify this function to correctly sum the comppct_r for the final output table.

    # Using global dValues[key = uppercase-domain value] value = [sequence, domain value]

    try:
        arcpy.SetProgressorLabel("Aggregating rating information to the map unit level")

        #
        #bVerbose = False

        if bVerbose:
            PrintMsg("Current function : " + sys._getframe().f_code.co_name, 1)
            PrintMsg("This function uses dValues dictionary", 1)

        # Create final output table with MUKEY, COMPPCT_R and sdvFld
        outputTbl = os.path.join(gdb, tblName)

        inFlds = ["MUKEY", "COKEY", "COMPPCT_R", dSDV["attributecolumnname"].upper(), "AREASYMBOL"]
        outFlds = ["MUKEY", "COMPPCT_R", dSDV["resultcolumnname"].upper(), "AREASYMBOL"]

        if bZero:
            whereClause = "COMPPCT_R >=  " + str(cutOff) + " AND " + dSDV["attributecolumnname"].upper() + " IS NOT NULL"

        else:
            whereClause = "COMPPCT_R >=  " + str(cutOff)

        # flatTbl must be in a file geodatabase to support ORDER_BY
        # Do I really need to sort by attribucolumn when it will be replaced by Domain values later?
        sqlClause =  (None, " ORDER BY MUKEY ASC, COMPPCT_R DESC")

        if arcpy.Exists(outputTbl):
            arcpy.Delete_management(outputTbl)

        outputTbl = CreateOutputTable(tmpDS, flatTbl, outputTbl, dFieldInfo)
        outputValues = list()

        if outputTbl == "":
            return outputTbl, outputValues

        dComp = dict()     # Try replacing this and dCompPct with dCompRating
        dCompPct = dict()
        dCompRating = dict()  # Dictionary with cokey as key, tuple(compPct, ratingIndx)

        dMapunit = dict()
        missingDomain = list()
        dAreasym = dict()
        #dCase = dict()

        # Read initial table for non-numeric soil properties. Capture domain values and all component ratings.
        #
        if not dSDV["attributetype"].lower() == "interpretation" and dSDV["attributelogicaldatatype"].lower() in ["string", "vtext"]:  # Changed here 2016-04-28
            #
            # No domain values for non-interp string ratings
            # !!! Probably never using this section of code.
            #
            if bVerbose:
                PrintMsg((40 * '*'), 1)
                PrintMsg("*dValues for " + dSDV["attributelogicaldatatype"] + " values: " + str(dValues), 1)
                PrintMsg("domainValues for " + dSDV["attributelogicaldatatype"] + " values: " + str(domainValues), 1)
                PrintMsg((40 * '*'), 1)

            with arcpy.da.SearchCursor(flatTbl, inFlds, sql_clause=sqlClause, where_clause=whereClause) as cur:

                if bVerbose:
                    PrintMsg("Reading initial data...", 1)

                for rec in cur:
                    # "MUKEY", "COKEY", "COMPPCT_R", RATING
                    mukey, cokey, compPct, rating, areasym = rec
                    dAreasym[mukey] = areasym
                    dCompRating[cokey] = [compPct, rating]

                    # save list of components for each mapunit
                    try:
                        dMapunit[mukey].append(cokey)

                    except:
                        dMapunit[mukey] = [cokey]

        elif dSDV["attributelogicaldatatype"].lower() in ["string", "float", "integer", "choice"]:
            # Interp or numeric soil properties
            # Flooding and Ponding Frequency would fall in the second section below that has a domain

            if len(domainValues) > 1 and not "None" in domainValues:
                PrintMsg("******************* Immediately adding 'None' to dValues ****************" , 1)
                #dValues["<NULL>"] = [len(dValues), None]
                #domainValues.append("None")

            if bVerbose:
                PrintMsg("**domainValues for " + dSDV["attributelogicaldatatype"] + " values: " + str(domainValues) + " \n ", 1)
                PrintMsg("**dValues for " + dSDV["attributelogicaldatatype"] + " values: " + str(dValues), 1)


            if  dSDV["tiebreakdomainname"] is None:
                # There are no domain values. We must make sure that the legend values are the same as
                # the output values.
                #
                PrintMsg("No domain name for this property", 1)

                with arcpy.da.SearchCursor(flatTbl, inFlds, sql_clause=sqlClause, where_clause=whereClause) as cur:

                    if bVerbose:
                        PrintMsg("Reading initial data...", 1)

                    for rec in cur:
                        mukey, cokey, compPct, rating, areasym = rec
                        dAreasym[mukey] = areasym

                        try:
                            dMapunit[mukey].append(cokey)

                        except:
                            dMapunit[mukey] = [cokey]

                        # this is a new component record. create a new dictionary item.
                        #
                        if not cokey in dComp:

                            if not rating is None:
                                dCase[str(rating).upper()] = rating

                                if str(rating).upper() in dValues:

                                    dValues[str(rating).upper()][1] = rating
                                    dCompRating[cokey] = [compPct, dValues[str(rating).upper()][0]]

                                    # compare actual rating value to domainValues to make sure case is correct
                                    #
                                    # This does not make sense. domainValues must be coming from maplegendxml.
                                    #
                                    if not rating in domainValues: # this is a case problem
                                        # replace the original dValue item
                                        dValues[str(rating).upper()][1] = rating

                                        # replace the value in domainValues list
                                        for i in range(len(domainValues)):
                                            if str(domainValues[i]).upper() == str(rating).upper():
                                                domainValues[i] = rating

                                else:
                                    # dValues is keyed on uppercase string rating or is Null
                                    #
                                    # Conservation Tree Shrub has some values not found in the domain.
                                    # How can this be? Need to check with George?
                                    #
                                    if not str(rating) in missingDomain:
                                        # Try to add missing value to dDomainValues dict and domainValues list
                                        dValues[str(rating).upper()] = [len(dValues), rating]
                                        domainValues.append(rating)
                                        missingDomain.append(str(rating))
                                        dCompRating[cokey] = [compPct, rating]


                                        PrintMsg("\tAdding value '" + str(rating) + "' to domainValues", 1)

                            else:
                                # Rating is Null
                                dCompRating[cokey] = [compPct, None]

            else:
                # New code for Ponding Frequency which has a domain
                #
                PrintMsg("Domain name for this property: '" + dSDV["tiebreakdomainname"] + "'", 1)
                PrintMsg("domainValues: " + str(domainValues) + " \n ", 1)
                PrintMsg("dValues: " + str(dValues), 1)

                if tieBreaker == dSDV["tiebreakhighlabel"]:

                    with arcpy.da.SearchCursor(flatTbl, inFlds, sql_clause=sqlClause, where_clause=whereClause) as cur:
                        if bVerbose:
                            PrintMsg("Reading initial data from " + flatTbl + "...", 1)

                        for rec in cur:
                            mukey, cokey, compPct, ratingClass, areasym = rec
                            dAreasym[mukey] = areasym

                            if not ratingClass is None:

                                # Get the rating sequence number from the ordered domain
                                try:
                                    ratingIndx = dValues[str(ratingClass).upper()][0]

                                    # this is a new component record. create a new dictionary item.
                                    #
                                    if not cokey in dCompRating:
                                        # save list of components for each mapunit
                                        dCompRating[cokey] = [compPct, ratingIndx]

                                        try:
                                            # existing mapunit
                                            dMapunit[mukey].append(cokey)

                                        except:
                                            # new mapunit
                                            dMapunit[mukey] = [cokey]

                                    else:
                                        # other months for this component
                                        # if this new index is greater than the old one, keep  it
                                        oldIndx = dCompRating[cokey][1]

                                        if oldIndx < ratingIndx:
                                            dCompRating[cokey][1] = ratingIndx

                                except KeyError:
                                    # encountered value that is not a member of the domain
                                    # Example: "Common" is obsolete value in the Ponding Frequency Class
                                    pass


                elif tieBreaker == dSDV["tiebreaklowlabel"]:

                    with arcpy.da.SearchCursor(flatTbl, inFlds, sql_clause=sqlClause, where_clause=whereClause) as cur:
                        if bVerbose:
                            PrintMsg("Reading initial data from " + flatTbl + "...", 1)

                        for rec in cur:
                            mukey, cokey, compPct, ratingClass, areasym = rec
                            dAreasym[mukey] = areasym

                            if not ratingClass is None:

                                # Get the rating sequence number from the ordered domain
                                try:
                                    ratingIndx = dValues[str(ratingClass).upper()][0]

                                    # this is a new component record. create a new dictionary item.
                                    #
                                    if not cokey in dCompRating:
                                        # save list of components for each mapunit
                                        dCompRating[cokey] = [compPct, ratingIndx]

                                        try:
                                            # existing mapunit
                                            dMapunit[mukey].append(cokey)

                                        except:
                                            # new mapunit
                                            dMapunit[mukey] = [cokey]

                                    else:
                                        # other months for this component
                                        # if this new index is greater than the old one, keep  it
                                        oldIndx = dCompRating[cokey][1]

                                        if oldIndx > ratingIndx:
                                            dCompRating[cokey][1] = ratingIndx

                                except KeyError:
                                    # encountered value that is not a member of the domain
                                    # Example: "Common" is obsolete value in the Ponding Frequency Class
                                    pass


        else:
            err = "Problem with handling domain values of type '" + dSDV["attributelogicaldatatype"]
            raise MyError(err)

        # Aggregate monthly index values to a single value for each component??? Would it not be better to
        # create a new function for COMONTH-DCD? Then I could simplify this function.
        #
        # Sort depending upon tiebreak setting
        # Update dictionary with a single index value for each component
        #if not dSDV["attributelogicaldatatype"].lower() in ["string", "vText"]:

        if bVerbose:
            PrintMsg(".", 1)
            PrintMsg("****Aggregating to a single value per component which would generally only apply to COMONTH properties?", 1)


        # Save list of component rating data to each mapunit, sort and write out
        # a single map unit rating
        #
        dRatings = dict()

        if bVerbose:
            PrintMsg("Writing map unit rating data to final output table", 1)
            PrintMsg("Using tiebreaker '" + tieBreaker + "' (where choices are '" + dSDV["tiebreaklowlabel"] + "' or '" + dSDV["tiebreakhighlabel"] + "')", 1)
            PrintMsg(str(len(dMapunit)) + " values in dMapunit dictionary", 1)


        if tieBreaker == dSDV["tiebreakhighlabel"]:
            with arcpy.da.InsertCursor(outputTbl, outFlds) as ocur:

                for mukey, cokeys in dMapunit.items():
                    # Since this is COMONTH data, each cokey could be listed 12X.
                    dRating = dict()  # save sum of comppct for each rating within a mapunit
                    muVals = list()   # may not need this for DCD

                    for cokey in cokeys:

                        compPct, ratingIndx = dCompRating[cokey]

                        if ratingIndx in dRating:
                            dRating[ratingIndx] += compPct

                        else:
                            dRating[ratingIndx] = compPct

                    for ratingIndx, compPct in dRating.items():
                        muVals.append([compPct, ratingIndx])

                    if len(muVals) > 0:
                        #This is the final aggregation from component to map unit rating
                        muVal = SortData(muVals, 0, 1, True, True)  # high
                        del dRating

                        try:
                            # Get final rating class value using index
                            ratingClass = domainValues[muVal[1]]
                            compPct = muVal[0]

                        except:
                            err = "Failed to get rating for muVals: " + str(muVals)
                            raise MyError(err)

                        newrec = [mukey, compPct, ratingClass, dAreasym[mukey]]
                        ocur.insertRow(newrec)
                        PrintMsg(tieBreaker + ": " + str(newrec), 1)

                        if not ratingClass is None and not ratingClass in outputValues:
                            outputValues.append(ratingClass)

        elif tieBreaker == dSDV["tiebreaklowlabel"]:
            with arcpy.da.InsertCursor(outputTbl, outFlds) as ocur:

                for mukey, cokeys in dMapunit.items():
                    # Since this is COMONTH data, each cokey could be listed 12X.
                    dRating = dict()  # save sum of comppct for each rating within a mapunit
                    muVals = list()   # may not need this for DCD

                    for cokey in cokeys:

                        compPct, ratingIndx = dCompRating[cokey]

                        if ratingIndx in dRating:
                            dRating[ratingIndx] += compPct

                        else:
                            dRating[ratingIndx] = compPct

                    for ratingIndx, compPct in dRating.items():
                        muVals.append([compPct, ratingIndx])

                    if len(muVals) > 0:
                        #This is the final aggregation from component to map unit rating
                        muVal = SortData(muVals, 0, 1, True, False) # low
                        del dRating

                        try:
                            # Get final rating class value using index
                            ratingClass = domainValues[muVal[1]]
                            compPct = muVal[0]

                        except:
                            err = "Failed to get rating for muVals: " + str(muVals)
                            raise MyError(err)

                        newrec = [mukey, compPct, ratingClass, dAreasym[mukey]]
                        ocur.insertRow(newrec)
                        PrintMsg(tieBreaker + ": " + str(newrec), 1)

                        if not ratingClass is None and not ratingClass in outputValues:
                            outputValues.append(ratingClass)

        del dComp
        del dCompPct
        del dAreasym
        outputValues.sort()
        return outputTbl, outputValues

    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return outputTbl, outputValues

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

        return outputTbl, outputValues

## ===================================================================================
def AggregateCo_Mo_WTA(gdb, sdvAtt, sdvFld, flatTbl, bZero, cutOff, tieBreaker):
    #
    # Aggregate monthly depth to water table to the map unit level using a special type
    # of Weighted average.
    #
    # Web Soil Survey takes only the Lowest or Highest of the monthly values from
    # each component and calculates the weighted average of those.
    #

    try:
        #
        arcpy.SetProgressorLabel("Aggregating rating information to the map unit level")

        if bVerbose:
            PrintMsg("Current function : " + sys._getframe().f_code.co_name, 1)

        # Create final output table with MUKEY, COMPPCT_R and sdvFld
        outputTbl = os.path.join(gdb, tblName)
        #attribcolumn = dSDV["attributecolumnname"].upper()
        #resultcolumn = dSDV["resultcolumnname"].upper()

        inFlds = ["MUKEY", "COKEY", "COMPPCT_R", dSDV["attributecolumnname"].upper(), "AREASYMBOL"]
        outFlds = ["MUKEY", "COMPPCT_R", dSDV["resultcolumnname"].upper(), "AREASYMBOL"]


        #whereClause = "COMPPCT_R >=  " + str(cutOff)  # Leave in NULLs and try to substitute dSDV["nullratingreplacementvalue"]

        if bZero:
            #PrintMsg("Including components with null rating values...", 1)
            whereClause = "COMPPCT_R >=  " + str(cutOff)

        else:
            #PrintMsg("Skipping components with null rating values...", 1)
            whereClause = "COMPPCT_R >=  " + str(cutOff) + " AND " + dSDV["attributecolumnname"].upper() + " IS NOT NULL"

        sqlClause =  (None, " ORDER BY MUKEY ASC, COMPPCT_R DESC")

        if arcpy.Exists(outputTbl):
            arcpy.Delete_management(outputTbl)

        outputTbl = CreateOutputTable(tmpDS, flatTbl, outputTbl, dFieldInfo)
        outputValues = list()

        if outputTbl == "":
            return outputTbl, outputValues

        dMapunit = dict()
        dComponent = dict()
        dCoRating = dict()
        dAreasym = dict()

        #PrintMsg("SQL: " + whereClause, 1)
        #PrintMsg("Fields: " + str(inFlds), 1)

        with arcpy.da.SearchCursor(flatTbl, inFlds, sql_clause=sqlClause, where_clause=whereClause) as cur:

            # MUKEY,COKEY , COMPPCT_R, attribcolumn
            for rec in cur:

                mukey, cokey, compPct, rating, areasym = rec
                dAreasym[mukey] = areasym

                # Save list of cokeys for each mapunit
                try:
                    if not cokey in dMapunit[mukey]:
                        dMapunit[mukey].append(cokey)

                except:
                    dMapunit[mukey] = [cokey]

                try:
                    # Save list of rating values along with comppct for each component
                    if not rating is None:
                        dComponent[cokey][1].append(rating)

                except:
                    #  Save list of rating values along with comppct for each component
                    if not rating is None:
                        dComponent[cokey] = [compPct, [rating]]

        if tieBreaker == dSDV["tiebreakhighlabel"]:
            # This is working correctly for DepthToWaterTable

            # Identify highest value for each component
            for cokey, coVals in dComponent.items():
                # Find highest monthly value for each component
                #PrintMsg("Higher values for cokey " + cokey + ": " + str(coVals[1]) + " = " + str(max(coVals[1])), 1)
                dCoRating[cokey] = max(coVals[1])

        else:
            # This is working correctly for DepthToWaterTable

            # Identify lowest monthly value for each component
            for cokey, coVals in dComponent.items():
                # Find low rating value for each component
                #PrintMsg("Lower values for cokey " + cokey + ": " + str(coVals[1]) + " = " + str(min(coVals[1])), 1)
                dCoRating[cokey] = min(coVals[1])

        dFinalRatings = dict()  # final dominant condition. mukey is key

        for mukey, cokeys in dMapunit.items():
            # accumulate ratings for each mapunit by sum of comppct
            #dMuRatings = dict()  # create a dictionary of values for just this map unit
            muPct = 0
            muRating = None

            for cokey in cokeys:
                # look at values for each component within the map unit
                try:
                    rating = dCoRating[cokey]
                    compPct = dComponent[cokey][0]
                    muPct += compPct

                    if not rating is None:
                      # accumulate product of depth and component percent
                      try:
                          muRating += (compPct * rating)

                      except:
                          muRating = compPct * rating

                except:
                    pass

            # Calculate weighted mapunit value from sum of products
            if not muRating is None:
                muRating = muRating / float(muPct)

            dFinalRatings[mukey] = [muPct, muRating]

        with arcpy.da.InsertCursor(outputTbl, outFlds) as ocur:
            # Write final ratings to output table
            for mukey in sorted(dMapunit):
                compPct, rating = dFinalRatings[mukey]
                rec = mukey, compPct, rating, dAreasym[mukey]
                ocur.insertRow(rec)

                if not rating is None and not rating in outputValues:
                    outputValues.append(rating)

        outputValues.sort()
        return outputTbl, outputValues

    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return outputTbl, outputValues

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

        return outputTbl, outputValues

## ===================================================================================
def AggregateCo_WTA_DTWT(gdb, sdvAtt, sdvFld, flatTbl, bZero, cutOff, tieBreaker):
    # Depth to water table weighted average

    try:
        #
        arcpy.SetProgressorLabel("Aggregating rating information to the map unit level")

        #PrintMsg("Testing nullRating variable: " + str(nullRating), 1)

        if bVerbose:
            PrintMsg("Current function : " + sys._getframe().f_code.co_name, 1)

        # Create final output table with MUKEY, COMPPCT_R and sdvFld
        outputTbl = os.path.join(gdb, tblName)
        inFlds = ["MUKEY", "COKEY", "COMPPCT_R", dSDV["attributecolumnname"].upper(), "AREASYMBOL"]
        outFlds = ["MUKEY", "COMPPCT_R", dSDV["resultcolumnname"].upper(), "AREASYMBOL"]

        if bZero:
            #PrintMsg("Including components with null rating values...", 1)
            whereClause = "COMPPCT_R >=  " + str(cutOff)

        else:
            #PrintMsg("Skipping components with null rating values...", 1)
            whereClause = "COMPPCT_R >=  " + str(cutOff) + " AND " + dSDV["attributecolumnname"].upper() + " IS NOT NULL"

        sqlClause =  (None, " ORDER BY MUKEY ASC, COMPPCT_R DESC")

        if arcpy.Exists(outputTbl):
            arcpy.Delete_management(outputTbl)

        outputTbl = CreateOutputTable(tmpDS, flatTbl, outputTbl, dFieldInfo)
        outputValues = list()

        if outputTbl == "":
            return outputTbl, outputValues

        dMapunit = dict()
        dComponent = dict()
        dCoRating = dict()
        dAreasym = dict()

        with arcpy.da.SearchCursor(flatTbl, inFlds, sql_clause=sqlClause, where_clause=whereClause) as cur:

            # MUKEY,COKEY , COMPPCT_R, attribcolumn
            for rec in cur:
                #mukey = rec[0]
                #cokey = rec[1]
                #compPct = rec[2]
                #rating = rec[3]
                mukey, cokey, compPct, rating, areasym = rec

                dAreasym[mukey] = areasym

                if rating is None:
                    rating = nullRating

                # Save list of cokeys for each mukey
                try:
                    if not cokey in dMapunit[mukey]:
                        dMapunit[mukey].append(cokey)

                except:
                    dMapunit[mukey] = [cokey]

                try:
                    # Save list of rating values along with comppct for each component
                    dComponent[cokey][1].append(rating)

                except:
                    #  Save list of rating values along with comppct for each component
                    dComponent[cokey] = [compPct, [rating]]


        if tieBreaker == dSDV["tiebreakhighlabel"]:
            for cokey, coVals in dComponent.items():
                # Find high value for each component
                dCoRating[cokey] = max(coVals[1])

        else:
            for cokey, coVals in dComponent.items():
                # Find low value for each component
                dCoRating[cokey] = min(coVals[1])

        dFinalRatings = dict()  # final dominant condition. mukey is key

        for mukey, cokeys in dMapunit.items():
            # accumulate ratings for each mapunit by sum of comppct
            sumPct = 0
            muProd = 0

            for cokey in cokeys:
                # look at values for each component within the map unit
                rating = dCoRating[cokey]
                compPct = dComponent[cokey][0]

                #if rating != nullRating:
                if not rating is None:
                    # Don't include the 201 (originally null) depths in the WTA calculation
                    sumPct += compPct            # sum comppct for the mapunit
                    muProd += (rating * compPct)   # calculate product of component percent and component rating

            if sumPct > 0:
                dFinalRatings[mukey] = [sumPct, round(float(muProd) / sumPct)]

            else:
                # now replace the nulls with 201
                dFinalRatings[mukey] = [100, nullRating]

        with arcpy.da.InsertCursor(outputTbl, outFlds) as ocur:
            # Write final ratings to output table
            for mukey, vals in dFinalRatings.items():
                rec = mukey, vals[0], vals[1], dAreasym[mukey]
                ocur.insertRow(rec)

                if not vals[1] is None and not vals[1] in outputValues:
                    outputValues.append(vals[1])

        outputValues.sort()
        return outputTbl, outputValues

    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return None, None

    except:
        # Catch python errors here
        # tbInfo contains the script, function and error line number
        tb = sys.exc_info()[2]
        tbInfo = traceback.format_tb(tb)[0]
        # Need to see how this handles errors that are in the main

        errInfo = str(sys.exc_info()[1])

        # Concatenate information together concerning the error into a message string
        pymsg = tbInfo + "\n" + errInfo

        if errInfo.find("MyError") == -1:
            # Report python errors
            PrintMsg("Python Error", 1)
            arcpy.AddError(pymsg)

        else:
            # raised error condition
            PrintMsg("Raised Error", 1)
            arcpy.AddError(err)

        return outputTbl, outputValues


## ===================================================================================
def AggregateCo_DCD_Domain(gdb, sdvAtt, sdvFld, flatTbl, bZero, cutOff, tieBreaker):
    #
    # Flooding or ponding frequency, dominant condition
    #
    # Aggregate mapunit-component data to the map unit level using dominant condition.
    # Use domain values to determine sort order for tiebreaker
    #
    # Problem with domain values for some indexes which are numeric. Need to accomodate for
    # domain key values which cannot be 'uppercased'.
    #
    # Some domain values are not found in the data and vise versa.
    #
    # Bad problem 2016-06-08.
    # Noticed that my final rating table may contain multiple ratings (tiebreak) for a map unit. This creates
    # a funky join that may display a different map color than the Identify value shows for the polygon. NIRRCAPCLASS.
    # Added areasymbol to output
    #
    # Conservation Tree and Shrub group are located in the component table
    # This has domain values and component values which are all lowercase
    # The maplegendxml is all uppercase
    #
    # I think I need to loop through each output value from the table, find the UPPER match and
    # then alter the legend value and label to match the output value.
    #
    # Nov 2017 problem noticed with Irrigated Capability Class where null values are not used
    # as the dominant condition. Fixed.
    #

    try:
        arcpy.SetProgressorLabel("Aggregating rating information to the map unit level")

        #
        #bVerbose = True

        if bVerbose:
            PrintMsg("Current function : " + sys._getframe().f_code.co_name, 1)
            PrintMsg("This function uses dValues dictionary", 1)

        # Create final output table with MUKEY, COMPPCT_R and sdvFld
        outputTbl = os.path.join(gdb, tblName)

        inFlds = ["MUKEY", "COKEY", "COMPPCT_R", dSDV["attributecolumnname"].upper(), "AREASYMBOL"]
        outFlds = ["MUKEY", "COMPPCT_R", dSDV["resultcolumnname"].upper(), "AREASYMBOL"]

        # Default setting is to include Null values as part of the aggregation process
        if bZero:
            #PrintMsg("Including components with null rating values...", 1)
            whereClause = "COMPPCT_R >=  " + str(cutOff)

        else:
            #PrintMsg("Skipping components with null rating values...", 1)
            whereClause = "COMPPCT_R >=  " + str(cutOff) + " AND " + dSDV["attributecolumnname"].upper() + " IS NOT NULL"

        # flatTbl must be in a file geodatabase to support ORDER_BY
        # Do I really need to sort by attribucolumn when it will be replaced by Domain values later?
        sqlClause =  (None, " ORDER BY MUKEY ASC, COMPPCT_R DESC")

        if arcpy.Exists(outputTbl):
            arcpy.Delete_management(outputTbl)

        outputTbl = CreateOutputTable(tmpDS, flatTbl, outputTbl, dFieldInfo)
        outputValues = list()

        if outputTbl == "":
            #PrintMsg("\nCreateOutputTable returned nothing", 1)
            return outputTbl, outputValues

        lastCokey = "xxxx"
        dComp = dict()
        dCompPct = dict()
        dMapunit = dict()
        missingDomain = list()
        dAreasym = dict()
        dCase = dict()

        # PrintMsg("tiebreakdomainname: " + str(dSDV["tiebreakdomainname"]), 1)

        # Read initial table for non-numeric data types. Capture domain values and all component ratings.
        #
        if bVerbose:
            PrintMsg("Reading initial data...", 1)
            PrintMsg(whereClause, 1)
            initCnt = int(arcpy.GetCount_management(flatTbl).getOutput(0))
            PrintMsg("\nInput table contains " + Number_Format(initCnt, 0, True) + " records", 1)
            PrintMsg("Data is from " + dSDV["attributecolumnname"].upper() + " column", 1)
            PrintMsg(dSDV["attributetype"] + " attribute logical data type: " + dSDV["attributelogicaldatatype"].lower(), 1)

        if not dSDV["attributetype"].lower() == "interpretation" and dSDV["attributelogicaldatatype"].lower() in ["string", "vtext"]:  # Changed here 2016-04-28
            # No domain values for non-interp string ratings
            # Probably not using this section of code.
            #
            if bVerbose:
                PrintMsg("" + dSDV["attributetype"] + " values for " + dSDV["attributelogicaldatatype"] + " data type: " + str(dValues), 1)
                PrintMsg("domainValues for " + dSDV["attributelogicaldatatype"] + " values: " + str(domainValues), 1)


            with arcpy.da.SearchCursor(flatTbl, inFlds, sql_clause=sqlClause, where_clause=whereClause) as cur:

                for rec in cur:
                    # "MUKEY", "COKEY", "COMPPCT_R", RATING
                    # PrintMsg("\t" + str(rec), 1)
                    mukey, cokey, compPct, rating, areasym = rec
                    dAreasym[mukey] = areasym
                    dComp[cokey] = rating
                    dCompPct[cokey] = compPct
                    dCase[str(rating).upper()] = rating  # save original value using uppercase key

                    # save list of components for each mapunit
                    try:
                        dMapunit[mukey].append(cokey)

                    except:
                        dMapunit[mukey] = [cokey]

        elif dSDV["attributelogicaldatatype"].lower() in ["string", "float", "integer", "choice"]:
            #
            # if dSDV["tiebreakdomainname"] is not None:  # this is a test to see if there are true domain values
            # Use this to compare dValues to output values
            #

            if len(domainValues) > 1 and not None in domainValues:

                if tieBreaker == dSDV["tiebreakhighlabel"]:
                    # Put the null value at the beginning of the domain
                    dValues[None] = [0, None]
                    #domainValues.insert(0, None)

                else:
                    # Put the null value at the end of the domain
                    dValues[None] = [len(dValues), None]
                    #domainValues.append(None)

            # PrintMsg("tiebreakdomainname: " + str(dSDV["tiebreakdomainname"]), 1)

            if bVerbose:
                # ********************** GPR Problem here
                #
                PrintMsg("" + dSDV["attributetype"] + " values for " + dSDV["attributelogicaldatatype"] + " data type: " + str(dValues), 1)
                PrintMsg("domainValues for " + dSDV["attributelogicaldatatype"] + " values: " + str(domainValues) + " \n ", 1)
                PrintMsg("tiebreakdomainname: " + str(dSDV["tiebreakdomainname"]), 1)

            if  dSDV["tiebreakdomainname"] is None:
                # There are no domain values.
                # We must make sure that the legend values are the same as the output values.
                #
                with arcpy.da.SearchCursor(flatTbl, inFlds, sql_clause=sqlClause, where_clause=whereClause) as cur:

                    for rec in cur:
                        mukey, cokey, compPct, rating, areasym = rec
                        #PrintMsg("\t" + str(rec), 1)
                        dAreasym[mukey] = areasym

                        #if bVerbose and mukey == '397784':
                        #    PrintMsg("\tRECORD:  " + str(rec), 1)

                        # save list of components for each mapunit
                        try:
                            dMapunit[mukey].append(cokey)

                        except:
                            dMapunit[mukey] = [cokey]

                        # this is a new component record. create a new dictionary item.
                        #
                        if not cokey in dComp:
                            dCase[str(rating).upper()] = rating


                            # I have a Problem here with domain values and 'None' vs None with GPR
                            # Perhaps I could add a '<Null>' value to the domain at the beginning or end?
                            #
                            if str(rating).upper() in dValues or rating is None:
                                #PrintMsg("\tNew rating '" + rating + "' assigning index '" + str(dValues[str(rating).upper()][0]) + "' to dComp", 1)
                                if not rating is None:
                                    # Don't confuse 'None' with None
                                    # Get the index from dValues for this component rating and save it to dComp by cokey
                                    dComp[cokey] = dValues[str(rating).upper()][0]  #

                                else:
                                    # Get the index from dValues for <Null> and save it to dComp by cokey
                                    #dComp[cokey] = dValues["<Null>"][0]
                                    dComp[cokey] = dValues["NONE"][0]


                                dCompPct[cokey] = compPct

                                # compare actual rating value to domainValues to make sure case is correct
                                #
                                # This does not make sense. domainValues must be coming from maplegendxml.
                                #
                                if not rating in domainValues: # this is a case problem or perhaps
                                    # replace the original dValue item
                                    dValues[str(rating).upper()][1] = rating

                                    # replace the value in domainValues list
                                    for i in range(len(domainValues)):
                                        if str(domainValues[i]).upper() == str(rating).upper():
                                            domainValues[i] = rating


                            else:
                                # dValues is keyed on uppercase string rating or is Null
                                #
                                # Conservation Tree Shrub has some values not found in the domain.
                                # How can this be? Need to check with George?
                                #
                                #PrintMsg("\tdValue not found for: " + str(rec), 1)
                                if not str(rating) in missingDomain:
                                    # Try to add missing value to dDomainValues dict and domainValues list
                                    dComp[cokey] = len(dValues)
                                    dValues[str(rating).upper()] = [len(dValues), rating]
                                    domainValues.append(rating)
                                    domainValuesUp.append(str(rating).upper())
                                    missingDomain.append(str(rating))
                                    dCompPct[cokey] = compPct
                                    #PrintMsg("\t****Adding value '" + str(rating) + "' to domainValues", 1)


            else:
                # New code for property or interps with domain values

                with arcpy.da.SearchCursor(flatTbl, inFlds, sql_clause=sqlClause, where_clause=whereClause) as cur:

                    for rec in cur:
                        mukey, cokey, compPct, rating, areasym = rec
                        dAreasym[mukey] = areasym

                        # save list of components for each mapunit
                        try:
                            dMapunit[mukey].append(cokey)

                        except:
                            dMapunit[mukey] = [cokey]

                        # this is a new component record. create a new dictionary item.
                        #
                        if not cokey in dComp:
                            dCase[str(rating).upper()] = rating

                            if str(rating).upper() in dValues:

                                dComp[cokey] = dValues[str(rating).upper()][0]  # think this is bad
                                dCompPct[cokey] = compPct

                                # compare actual rating value to domainValues to make sure case is correct
                                if not rating in domainValues: # this is a case problem
                                    # replace the original dValue item
                                    dValues[str(rating).upper()][1] = rating

                                    # replace the value in domainValues list
                                    for i in range(len(domainValues)):
                                        if str(domainValues[i]).upper() == str(rating).upper():
                                            domainValues[i] = rating


                            else:
                                # dValues is keyed on uppercase string rating or is Null
                                #
                                # Conservation Tree Shrub has some values not found in the domain.
                                # How can this be? Need to check with George?
                                #
                                #PrintMsg("\tdValue not found for: " + str(rec), 1)
                                if not str(rating) in missingDomain:
                                    # Try to add missing value to dDomainValues dict and domainValues list
                                    dComp[cokey] = len(dValues)
                                    dValues[str(rating).upper()] = [len(dValues), rating]
                                    domainValues.append(rating)
                                    domainValuesUp.append(str(rating).upper())
                                    missingDomain.append(str(rating))
                                    dCompPct[cokey] = compPct
                                    #PrintMsg("\tAdding value '" + str(rating) + "' to domainValues", 1)



        else:
            err = "Problem with handling domain values of type '" + dSDV["attributelogicaldatatype"]
            raise MyError(err)

        # Aggregate monthly index values to a single value for each component??? Would it not be better to
        # create a new function for COMONTH-DCD? Then I could simplify this function.
        #
        # Sort depending upon tiebreak setting
        # Update dictionary with a single index value for each component

        # Save list of component rating data to each mapunit, sort and write out
        # a single map unit rating
        #
        dRatings = dict()

        if bVerbose:
            PrintMsg("Writing map unit rating data to final output table", 1)
            PrintMsg("Using tiebreaker '" + tieBreaker + "' (where choices are " + dSDV["tiebreaklowlabel"] + " or " + dSDV["tiebreakhighlabel"] + ")", 1)

        if tieBreaker == dSDV["tiebreakhighlabel"]:
            with arcpy.da.InsertCursor(outputTbl, outFlds) as ocur:

                for mukey, cokeys in dMapunit.items():
                    dRating = dict()  # save sum of comppct for each rating within a mapunit
                    muVals = list()   # may not need this for DCD

                    for cokey in cokeys:
                        try:
                            #PrintMsg("\tA ratingIndx: " + str(dComp[cokey]), 1)
                            compPct = dCompPct[cokey]
                            ratingIndx = dComp[cokey]

                            if ratingIndx in dRating:
                                sumPct = dRating[ratingIndx] + compPct
                                dRating[ratingIndx] = sumPct  # this part could be compacted

                            else:
                                dRating[ratingIndx] = compPct

                        except:
                            pass

                    for ratingIndx, compPct in dRating.items():
                        muVals.append([compPct, ratingIndx])  # This muVal is not being populated

                    #This is the final aggregation from component to map unit rating

                    if len(muVals) > 0:
                        muVal = SortData(muVals, 0, 1, True, True)
                        compPct, ratingIndx = muVal

                        try:
                            rating = domainValues[ratingIndx]
                            #PrintMsg("\tRating: " + str(rating) + "(index=" + str(ratingIndx) + ")", 1)

                        except:
                            err = "domainValues missing value for index (" + str(ratingIndx) + "): " + str(domainValues)
                            raise MyError(err)

                        #if bVerbose and mukey == '397784':
                        #    PrintMsg("\tmuVal for mukey: " + mukey + ", " + str(muVal), 1)
                        #    PrintMsg("\tRating: " + str(rating), 1)

                    else:
                        rating = None
                        compPct = None

                    #PrintMsg("" + tieBreaker + ". Checking index values for mukey " + mukey + ": " + str(muVal[0]) + ", " + str(domainValues[muVal[1]]), 1)
                    #PrintMsg("\tGetting mukey " + mukey + " rating: " + str(rating), 1)
                    newrec = [mukey, compPct, rating, dAreasym[mukey]]

                    ocur.insertRow(newrec)

                    if not rating is None and not rating in outputValues:
                        outputValues.append(rating)

        else:
            # tieBreaker Lower
            # Overhauling this tiebreaker lower, need to do the rest once it is working properly
            #
            #PrintMsg("Actually in Lower tiebreaker code", 1)
            #PrintMsg("dMapunit has " + str(len(dMapunit)) + " records", 1 )

            with arcpy.da.InsertCursor(outputTbl, outFlds) as ocur:

                # Process all mapunits
                for mukey, cokeys in dMapunit.items():
                    dRating = dict()  # save sum of comppct for each rating within a mapunit
                    muVals = list()   # may not need this for DCD
                    #PrintMsg("\t" + mukey + ":" + str(cokeys), 1)

                    for cokey in cokeys:
                        try:
                            compPct = dCompPct[cokey]
                            ratingIndx = dComp[cokey]
                            #PrintMsg("\t" + cokey + " index: " + str(ratingIndx), 1)

                            if ratingIndx in dRating:
                                sumPct = dRating[ratingIndx] + compPct
                                dRating[ratingIndx] = sumPct  # this part could be compacted

                            else:
                                dRating[ratingIndx] = compPct

                        except:
                            errorMsg1()

                    for ratingIndx, compPct in dRating.items():
                        muVals.append([compPct, ratingIndx])  # This muVal is not being populated

                    #PrintMsg("\t" + str(dRating), 1)
                    if len(muVals) > 0:
                        muVal = SortData(muVals, 0, 1, True, False)
                        #PrintMsg("\tmuVal for mukey: " + mukey + ", " + str(muVal), 1)
                        compPct, ratingIndx = muVal
                        rating = domainValues[ratingIndx]

                    else:
                        rating = None
                        compPct = None

                    #PrintMsg("" + tieBreaker + ". Checking index values for mukey " + mukey + ": " + str(muVal[0]) + ", " + str(domainValues[muVal[1]]), 1)
                    #PrintMsg("\tGetting mukey " + mukey + " rating: " + str(rating), 1)
                    newrec = [mukey, compPct, rating, dAreasym[mukey]]

                    ocur.insertRow(newrec)

                    if not rating is None and not rating in outputValues:
                        outputValues.append(rating)

        outputValues.sort()
        return outputTbl, outputValues

    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return None, None

    except:
        # Catch python errors here
        # tbInfo contains the script, function and error line number
        tb = sys.exc_info()[2]
        tbInfo = traceback.format_tb(tb)[0]
        # Need to see how this handles errors that are in the main

        errInfo = str(sys.exc_info()[1])

        # Concatenate information together concerning the error into a message string
        pymsg = tbInfo + "\n" + errInfo

        if errInfo.find("MyError") == -1:
            # Report python errors
            PrintMsg("Python Error", 1)
            arcpy.AddError(pymsg)

        else:
            # raised error condition
            PrintMsg("Raised Error", 1)
            arcpy.AddError(err)

        return outputTbl, outputValues

## ===================================================================================
def AggregateCo_DCP_Domain(gdb, sdvAtt, sdvFld, flatTbl, bZero, cutOff, tieBreaker):
    # Not being use.
    #
    # I may not use this function. Trying to handle ratings with domain values using the
    # standard AggregateCo_DCP function
    #
    # Flooding or ponding frequency, dominant component with domain values
    #
    # Use domain values to determine sort order for tiebreaker
    #
    # Problem with domain values for some indexes which are numeric. Need to accomodate for
    # domain key values which cannot be 'uppercased'.
    # Added areasymbol to output

    try:
        arcpy.SetProgressorLabel("Aggregating rating information to the map unit level")

        #
        if bVerbose:
            PrintMsg("Current function : " + sys._getframe().f_code.co_name, 1)

        # Create final output table with MUKEY, COMPPCT_R and sdvFld
        outputTbl = os.path.join(gdb, tblName)

        inFlds = ["MUKEY", "COKEY", "COMPPCT_R", dSDV["attributecolumnname"].upper(), "AREASYMBOL"]
        outFlds = ["MUKEY", "COMPPCT_R", dSDV["resultcolumnname"].upper(), "AREASYMBOL"]
        whereClause = "COMPPCT_R >=  " + str(cutOff) + " AND " + dSDV["attributecolumnname"].upper() + " IS NOT NULL"

        # flatTbl must be in a file geodatabase to support ORDER_BY
        # Do I really need to sort by attribucolumn when it will be replaced by Domain values later?
        sqlClause =  (None, " ORDER BY MUKEY ASC, COMPPCT_R DESC")


        if arcpy.Exists(outputTbl):
            arcpy.Delete_management(outputTbl)

        outputTbl = CreateOutputTable(tmpDS, flatTbl, outputTbl, dFieldInfo)
        outputValues = list()

        if outputTbl == "":
            return outputTbl, outputValues

        lastCokey = "xxxx"
        dComp = dict()
        dCompPct = dict()
        dMapunit = dict()
        missingDomain = list()
        dCase = dict()
        dAreasym = dict()

        # Read initial table for non-numeric data types
        # 02-03-2016 Try adding 'choice' to this method to see if it handles Cons. Tree/Shrub better
        # than the next method. Nope, did not work. Still have case problems.
        #
        if dSDV["attributelogicaldatatype"].lower() == "string":
            # PrintMsg("domainValues for " + dSDV["attributelogicaldatatype"].lower() + "-type values : " + str(domainValues), 1)

            with arcpy.da.SearchCursor(flatTbl, inFlds, sql_clause=sqlClause, where_clause=whereClause) as cur:

                for rec in cur:
                    dAreasym[rec[0]] = rec[4]
                    try:
                        # capture component ratings as index numbers instead.
                        dComp[rec[1]].append(dValues[str(rec[3]).upper()][0])

                    except:
                        dComp[rec[1]] = [dValues[str(rec[3]).upper()][0]]
                        dCompPct[rec[1]] = rec[2]
                        dCase[str(rec[3]).upper()] = rec[3]  # save original value using uppercase key


                        # save list of components for each mapunit
                        try:
                            dMapunit[rec[0]].append(rec[1])

                        except:
                            dMapunit[rec[0]] = [rec[1]]

        elif dSDV["attributelogicaldatatype"].lower() in ["float", "integer", "choice"]:
            # PrintMsg("domainValues for " + dSDV["attributelogicaldatatype"] + " values: " + str(domainValues), 1)

            with arcpy.da.SearchCursor(flatTbl, inFlds, sql_clause=sqlClause, where_clause=whereClause) as cur:

                for rec in cur:
                    dAreasym[rec[0]] = rec[4]
                    try:
                        # capture component ratings as index numbers instead
                        dComp[rec[1]].append(dValues[str(rec[3]).upper()][0])

                    except:
                        #PrintMsg("domainValues is empty, but legendValues has " + str(legendValues), 1)
                        dCase[str(rec[3]).upper()] = rec[3]

                        if str(rec[3]).upper() in dValues:
                            dComp[rec[1]] = [dValues[str(rec[3]).upper()][0]]
                            dCompPct[rec[1]] = rec[2]

                            # compare actual rating value to domainValues to make sure case is correct
                            if not rec[3] in domainValues: # this is a case problem
                                # replace the original dValue item
                                dValues[str(rec[3]).upper()][1] = rec[3]
                                # replace the value in domainValues list
                                for i in range(len(domainValues)):
                                    if domainValues[i].upper() == rec[3].upper():
                                        domainValues[i] = rec[3]

                        else:
                            # dValues is keyed on uppercase string rating
                            #
                            if not str(rec[3]) in missingDomain:
                                # Try to add missing value to dDomainValues dict and domainValues list
                                dValues[str(rec[3]).upper()] = [len(dValues), rec[3]]
                                domainValues.append(rec[3])
                                domainValuesUp.append(rec[3].upper())
                                missingDomain.append(str(rec[3]))
                                #PrintMsg("\tAdding value '" + str(rec[3]) + "' to domainValues", 1)

                        # save list of components for each mapunit
                        try:
                            dMapunit[rec[0]].append(rec[1])

                        except:
                            dMapunit[rec[0]] = [rec[1]]

        else:
            PrintMsg("Problem with handling domain values of type '" + dSDV["attributelogicaldatatype"] + "'", 1)

        # Aggregate monthly index values to a single value for each component
        # Sort depending upon tiebreak setting
        # Update dictionary with a single index value for each component
        PrintMsg("Not sure about this sorting code for tiebreaker", 1)

        if tieBreaker == dSDV["tiebreakhighlabel"]:
            # "Higher" (default for flooding and ponding frequency)
            for cokey, indexes in dComp.items():
                val = sorted(indexes, reverse=True)[0]
                dComp[cokey] = val
        else:
            for cokey, indexes in dComp.items():
                val = sorted(indexes)[0]
                dComp[cokey] = val

        # Save list of component data to each mapunit
        dRatings = dict()

        with arcpy.da.InsertCursor(outputTbl, outFlds) as ocur:

            if tieBreaker == dSDV["tiebreakhighlabel"]:
                # Default for flooding and ponding frequency
                #
                #PrintMsg("domainValues: " + str(domainValues), 1)

                for mukey, cokeys in dMapunit.items():
                    dRating = dict()   # save sum of comppct for each rating within a mapunit
                    muVals = list()   # may not need this for DCD

                    for cokey in cokeys:
                        #PrintMsg("\tB ratingIndx: " + str(dComp[cokey]), 1)
                        compPct = dCompPct[cokey]
                        ratingIndx = dComp[cokey]

                        if ratingIndx in dRating:
                            sumPct = dRating[ratingIndx] + compPct
                            dRating[ratingIndx] = sumPct  # this part could be compacted

                        else:
                            dRating[ratingIndx] = compPct

                    for rating, compPct in dRating.items():
                        muVals.append([compPct, rating])

                    #newVals = sorted(muVals, key = lambda x : (-x[0], x[1]))[0]  # Works for maplegendkey=2
                    #newVals = sorted(sorted(muVals, key = lambda x : x[0], reverse=True), key = lambda x : x[1], reverse=True)[0]
                    muVal = SortData(muVals, 0, 1, True, True)
                    newrec = [mukey, muVal[0], domainValues[muVal[1]], dAreasym[mukey]]
                    ocur.insertRow(newrec)

                    if not newrec[2] is None and not newrec[2] in outputValues:
                        outputValues.append(newrec[2])

            else:
                # Lower
                PrintMsg("Final lower tiebreaker", 1)

                for mukey, cokeys in dMapunit.items():
                    dRating = dict()  # save sum of comppct for each rating within a mapunit
                    muVals = list()   # may not need this for DCD

                    for cokey in cokeys:
                        try:
                            #PrintMsg("\tA ratingIndx: " + str(dComp[cokey]), 1)
                            compPct = dCompPct[cokey]
                            ratingIndx = dComp[cokey]

                            if ratingIndx in dRating:
                                sumPct = dRating[ratingIndx] + compPct
                                dRating[ratingIndx] = sumPct  # this part could be compacted

                            else:
                                dRating[ratingIndx] = compPct

                        except:
                            pass

                    for rating, compPct in dRating.items():
                        muVals.append([compPct, rating])

                    #newVals = sorted(muVals, key = lambda x : (-x[0], -x[1]))[0] # Works for maplegendkey=2
                    #newVals = sorted(sorted(muVals, key = lambda x : x[0], reverse=True), key = lambda x : x[1], reverse=False)[0]
                    muVal = SortData(muVals, 0, 1, True, False)
                    newrec = [mukey, muVal[0], domainValues[muVal[1]], dAreasym[mukey]]
                    ocur.insertRow(newrec)

                    if not newrec[2] is None and not newrec[2] in outputValues:
                        outputValues.append(newrec[2])


        outputValues.sort()
        return outputTbl, outputValues

    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return None, None

    except:
        # Catch python errors here
        # tbInfo contains the script, function and error line number
        tb = sys.exc_info()[2]
        tbInfo = traceback.format_tb(tb)[0]
        # Need to see how this handles errors that are in the main

        errInfo = str(sys.exc_info()[1])

        # Concatenate information together concerning the error into a message string
        pymsg = tbInfo + "\n" + errInfo

        if errInfo.find("MyError") == -1:
            # Report python errors
            PrintMsg("Python Error", 1)
            arcpy.AddError(pymsg)

        else:
            # raised error condition
            PrintMsg("Raised Error", 1)
            arcpy.AddError(err)

        return outputTbl, outputValues

## ===================================================================================
def AggregateCo_WTA(gdb, sdvAtt, sdvFld, flatTbl, bZero, cutOff, tieBreaker):
    # Aggregate mapunit-component data to the map unit level using a weighted average
    #
    # Possible problem with Depth to Restriction and the null replacement values of 201. nullRating
    # Should be calculating 'BrD' mapunit using [ (66/(66 + 15) X 38cm) + (15/(66 + 15) X 0cm) ]

    # Another question. For depth to any restriction, there could be multiple restrictions per
    # component. Do I need to sort on depth according to tieBreaker setting?

    try:
        #bVerbose = True

        # TEST CODE FOR nullRating handling
        if bVerbose:
            PrintMsg("nullRating: " + str(nullRating), 1)

        arcpy.SetProgressorLabel("Aggregating rating information to the map unit level")

        # Create final output table with MUKEY, COMPPCT_R and sdvFld
        if bVerbose:
            PrintMsg("Current function : " + sys._getframe().f_code.co_name, 1)

        outputTbl = os.path.join(gdb, tblName)
        #attribcolumn = dSDV["attributecolumnname"].upper()
        #resultcolumn = dSDV["resultcolumnname"].upper()
        fldPrecision = dSDV["attributeprecision"]

        inFlds = ["MUKEY", "COKEY", "COMPPCT_R", dSDV["attributecolumnname"].upper(), "AREASYMBOL"]
        outFlds = ["MUKEY", "COMPPCT_R", dSDV["resultcolumnname"].upper(), "AREASYMBOL"]

        # sort order of value is important
        if tieBreaker == "Lower":
            sOrder = " DESC"

        else:
            sOrder = " ASC"

        sqlClause =  (None, "ORDER BY MUKEY ASC, COMPPCT_R DESC, " + dSDV["attributecolumnname"].upper() + sOrder)

        # Added this replacement logic on 2020-09-18 in response to pH problem and general lack of consistency in applying null-handling settings
        if bZero:
            whereClause = "COMPPCT_R >=  " + str(cutOff)  # this will treat Nulls as zero which for example will lower pH values beyond the range when a lower horizon has no data

        else:
            whereClause = "COMPPCT_R >=  " + str(cutOff) + " AND " + dSDV["attributecolumnname"].upper() + " IS NOT NULL"

        if arcpy.Exists(outputTbl):
            arcpy.Delete_management(outputTbl)

        if bVerbose:
            PrintMsg("SQL: " + whereClause, 1)
            PrintMsg("Input table (" + flatTbl + ") has " + str(int(arcpy.GetCount_management(flatTbl).getOutput(0))) + " records", 1)

        outputTbl = CreateOutputTable(tmpDS, flatTbl, outputTbl, dFieldInfo)
        outputValues = list()

        if outputTbl == "":
            return outputTbl, outputValues

        lastMukey = "xxxx"
        dRating = dict()
        # reset variables for cursor
        sumPct = 0
        sumProd = 0
        meanVal = 0
        #prec = dSDV["attributeprecision"]
        outputValues = [999999999, -999999999]
        recCnt = 0
        areasym = ""
        dPct = dict()  # sum of comppct_r for each map unit
        dMapunit = dict()

        with arcpy.da.SearchCursor(flatTbl, inFlds, where_clause=whereClause, sql_clause=sqlClause) as cur:
            with arcpy.da.InsertCursor(outputTbl, outFlds) as ocur:
                for rec in cur:
                    recCnt += 1
                    mukey, cokey, comppct, val, areasym = rec
                    #PrintMsg(str(recCnt) + ". " + str(rec), 1)

                    # Capture component list for each mapunit
                    try:
                        if not cokey in dMapunit[mukey]:
                            dMapunit[mukey].append(cokey)

                            if not val == nullRating:
                                dPct[mukey] += comppct

                    except:
                        dMapunit[mukey] = [cokey]

                        if not val == nullRating:
                            dPct[mukey] = comppct

                    if val is None and bZero:
                        # convert null values to zero
                        val = 0.0

                    if val == nullRating:
                        #
                        val = None



                    #if bVerbose and mukey in ['374414', '374451']:
                    #    PrintMsg("\t\tMukey " + mukey + ":" + cokey + ";  " + str(comppct) + "%;  " + str(val), 1)

                    if mukey != lastMukey and lastMukey != "xxxx":
                        # I'm losing an output value when there is only one rated component and bZeros == True
                        # This is because only the non-Null ratings are being processed for things like Range Production (Normal Year) in Batch Mode.
                        #
                        try:
                            sumPct = dPct[lastMukey]

                        except:
                            dPct[lastMukey] = 0
                            sumPct = 0

                        if (sumPct > 0 and sumProd is not None):
                            # write out record for previous mapunit

                            meanVal = round(float(sumProd) / sumPct, fldPrecision)
                            newrec = [lastMukey, sumPct, meanVal, areasym]
                            ocur.insertRow(newrec)

                            #if bVerbose and lastMukey in ['374414', '374451']:
                            #    PrintMsg("\tTest mapunit1 " + lastMukey + ": " + str(meanVal) + ";  " + str(sumPct) + "%", 1)

                            # reset variables for the next mapunit record
                            sumPct = 0
                            sumProd = None

                            # save max-min values
                            if not meanVal is None:
                                outputValues[0] = min(meanVal, outputValues[0])
                                outputValues[1] = max(meanVal, outputValues[1])

                        else:
                        #    Tried to bring back null rating replacement value (201), but that didn't work because those
                        #    are being excluded from the entire process by the sql_clause.
                        #
                            newrec = [lastMukey, sumPct, nullRating, areasym]
                            #if bVerbose and lastMukey in ['374414', '374451']:
                            #    PrintMsg("\tTest mapunit2 " + lastMukey + ": " + str(nullRating) + ";  " + str(sumPct) + "%", 1)

                            ocur.insertRow(newrec)
                            # reset variables for the next mapunit record
                            sumPct = 0
                            sumProd = None
                            dPct[lastMukey] = 0

                    # accumulate data for this mapunit
                    #PrintMsg("\tFollowup summary", 1)
                    #sumPct += comppct

                    if val is not None:
                        prod = comppct * float(val)
                        try:
                            sumProd += prod

                        except:
                            sumProd = prod

                    # set new mapunit flag
                    lastMukey = mukey

                # Add final record
                try:
                    sumPct = dPct[lastMukey]

                except:
                    dPct[lastMukey] = 0

                if areasym != "" and sumPct != 0:  #
                    if sumProd is None:
                        meanVal = nullRating

                    else:
                        meanVal = round(float(sumProd) / sumPct, fldPrecision)

                    newrec = [lastMukey, sumPct, meanVal, areasym]  # if there is no data, this will error
                    ocur.insertRow(newrec)

                    if dSDV["resultcolumnname"].upper().startswith("NCCPI"):
                        # For NCCPI, hardcode the range of values from 0.0 to 1.0 for a consistent map legend
                        outputValues = [0.0, 1.0]

                    elif not meanVal is None:
                        outputValues[0] = min(meanVal, outputValues[0])
                        outputValues[1] = max(meanVal, outputValues[1])

        outputValues.sort()
        del sumPct
        del sumProd
        del meanVal

        if outputValues[0] == -999999999 or outputValues[1] == 999999999:
            # Sometimes no data can skip through the max min test
            outputValues = [0.0, 0.0]

        return outputTbl, outputValues

    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return None, None

    except:
        # Catch python errors here
        # tbInfo contains the script, function and error line number
        tb = sys.exc_info()[2]
        tbInfo = traceback.format_tb(tb)[0]
        # Need to see how this handles errors that are in the main

        errInfo = str(sys.exc_info()[1])

        # Concatenate information together concerning the error into a message string
        pymsg = tbInfo + "\n" + errInfo

        if errInfo.find("MyError") == -1:
            # Report python errors
            PrintMsg("Python Error", 1)
            arcpy.AddError(pymsg)

        else:
            # raised error condition
            PrintMsg("Raised Error", 1)
            arcpy.AddError(err)

        return outputTbl, outputValues

## ===================================================================================
def AggregateCo_PP_SUM(gdb, sdvAtt, sdvFld, flatTbl, bZero, cutOff, tieBreaker):
    #
    # Aggregate data to the map unit level using a sum (Hydric)
    # This is Percent Present
    # Soil Data Viewer reports zero for non-Hydric map units. This function is
    # currently not creating a record for those because they are not included in the
    # sdv_initial table.
    #
    # Will try removing sql whereclause from cursor and apply it to each record instead.
    #
    # Added Areasymbol to output

    try:
        arcpy.SetProgressorLabel("Aggregating rating information to the map unit level")

        # Create final output table with MUKEY, COMPPCT_R and sdvFld
        if bVerbose:
            PrintMsg("Current function : " + sys._getframe().f_code.co_name, 1)

        outputTbl = os.path.join(gdb, tblName)
        fldPrecision = dSDV["attributeprecision"]
        inFlds = ["MUKEY", "AREASYMBOL", "COMPPCT_R", dSDV["attributecolumnname"].upper(), "AREASYMBOL"]  # not sure why I have AREASYMBOL on the end..
        outFlds = ["MUKEY", "AREASYMBOL", dSDV["resultcolumnname"].upper(), "AREASYMBOL"]

        inFlds = ["MUKEY", "AREASYMBOL", "COMPPCT_R", dSDV["attributecolumnname"].upper()]  # not sure why I have AREASYMBOL on the end..
        outFlds = ["MUKEY", "AREASYMBOL", dSDV["resultcolumnname"].upper()]

        sqlClause =  (None, "ORDER BY MUKEY ASC")

        # For Percent Present, do not apply the whereclause to the cursor. Wait
        # and use it against each record so that all map units are rated.
        #whereClause = dSDV["sqlwhereclause"]
        whereClause = ""

        #hydric = dSDV["sqlwhereclause"].split("=")[1].encode('ascii').strip().replace("'","")
        hydric = dSDV["sqlwhereclause"].split("=")[1].strip().replace("'","")
        #PrintMsg("" + attribcolumn + " = " + hydric, 1)

        if arcpy.Exists(outputTbl):
            arcpy.Delete_management(outputTbl)

        # Create outputTbl based upon flatTbl schema
        outputTbl = CreateOutputTable(tmpDS, flatTbl, outputTbl, dFieldInfo)

        if outputTbl == "":
            return outputTbl, outputValues

        lastMukey = "xxxx"
        dRating = dict()
        # reset variables for cursor
        sumPct = 0
        sumProd = 0
        meanVal = 0
        iMax = -999999999
        iMin = 999999999

        if bVerbose:
            PrintMsg("Reading " + flatTbl + " and writing to " + outputTbl, 1)

        with arcpy.da.SearchCursor(flatTbl, inFlds, where_clause=whereClause, sql_clause=sqlClause) as cur:
            with arcpy.da.InsertCursor(outputTbl, outFlds) as ocur:
                for rec in cur:
                    mukey, areasym, comppct, val= rec

                    if comppct is None:
                        comppct = 0

                    if mukey != lastMukey and lastMukey != "xxxx":
                        #if sumPct > 0:
                        # write out record for previous mapunit
                        newrec = [lastMukey, areasym, sumPct]
                        ocur.insertRow(newrec)
                        iMax = max(sumPct, iMax)

                        if not sumPct is None:
                            iMin = min(sumPct, iMin)

                        # reset variables for the next mapunit record
                        sumPct = 0

                    # set new mapunit flag
                    lastMukey = mukey

                    # accumulate data for this mapunit
                    if str(val).upper() == hydric.upper():
                        # using the sqlwhereclause on each record so that
                        # the 'NULL' hydric map units are assigned zero instead of NULL.
                        sumPct += comppct

                # Add final record
                newrec = [lastMukey, areasym, sumPct]
                ocur.insertRow(newrec)

        return outputTbl, [iMin, iMax]

    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return None, None

    except:
        # Catch python errors here
        # tbInfo contains the script, function and error line number
        tb = sys.exc_info()[2]
        tbInfo = traceback.format_tb(tb)[0]
        # Need to see how this handles errors that are in the main

        errInfo = str(sys.exc_info()[1])

        # Concatenate information together concerning the error into a message string
        pymsg = tbInfo + "\n" + errInfo

        if errInfo.find("MyError") == -1:
            # Report python errors
            PrintMsg("Python Error", 1)
            arcpy.AddError(pymsg)

        else:
            # raised error condition
            PrintMsg("Raised Error", 1)
            arcpy.AddError(err)

        return outputTbl, []

## ===================================================================================
def AggregateHz_WTA_SUM(gdb, sdvAtt, sdvFld, flatTbl, bZero, cutOff, tieBreaker, top, bot):
    # Aggregate mapunit-component-horizon data to the map unit level using a weighted average
    #
    # This version uses SUM for horizon data as in AWS
    # Added areasymbol to output
    #
    try:
        import decimal

        arcpy.SetProgressorLabel("Aggregating rating information to the map unit level")
        #
        # Create final output table with MUKEY, COMPPCT_R and sdvFld
        if bVerbose:
            PrintMsg("Current function : " + sys._getframe().f_code.co_name, 1)

        outputTbl = os.path.join(gdb, tblName)
        #attribcolumn = dSDV["attributecolumnname"].upper()
        #resultcolumn = dSDV["resultcolumnname"].upper()
        fldPrecision = dSDV["attributeprecision"]

        inFlds = ["MUKEY", "COKEY", "COMPPCT_R", "HZDEPT_R", "HZDEPB_R", dSDV["attributecolumnname"].upper(), "AREASYMBOL"]
        outFlds = ["MUKEY", "COMPPCT_R", dSDV["resultcolumnname"].upper(), "AREASYMBOL"]

        sqlClause =  (None, "ORDER BY MUKEY ASC, COMPPCT_R DESC, HZDEPT_R ASC")

        if bZero:
            whereClause = "COMPPCT_R >=  " + str(cutOff)  # this will treat Nulls as zero which for example will lower pH values beyond the range when a lower horizon has no data

        else:
            whereClause = "COMPPCT_R >=  " + str(cutOff) + " AND " + dSDV["attributecolumnname"].upper() + " IS NOT NULL"

        if arcpy.Exists(outputTbl):
            arcpy.Delete_management(outputTbl)

        outputTbl = CreateOutputTable(tmpDS, flatTbl, outputTbl, dFieldInfo)

        if outputTbl == "":
            return outputTbl, outputValues

        dPct = dict()  # sum of comppct_r for each map unit
        dComp = dict() # component level information
        dMu = dict()

        # reset variables for cursor
        sumPct = 0
        sumProd = 0
        meanVal = 0
        #prec = dSDV["attributeprecision"]
        roundOff = 2

        with arcpy.da.SearchCursor(flatTbl, inFlds, where_clause=whereClause, sql_clause=sqlClause) as cur:
            with arcpy.da.InsertCursor(outputTbl, outFlds) as ocur:
                #arcpy.SetProgressor("step", "Reading initial query table ...",  0, iCnt, 1)

                for rec in cur:
                    mukey, cokey, comppct, hzdept, hzdepb, val, areasym = rec
                    # top = hzdept
                    # bot = hzdepb
                    # td = top of range
                    # bd = bottom of range
                    if val is None and bZero:
                        val = 0

                    if val is not None:

                        # Calculate sum of horizon thickness and sum of component ratings for all horizons above bottom
                        try:
                            hzT = min(hzdepb, bot) - max(hzdept, top)   # Getting a None error here.usable thickness from this horizon

                        except:
                            hzT = 0

                        if hzT > 0:
                            aws = float(hzT) * val
                            #PrintMsg("\t" + str(aws), 1)

                            if not cokey in dComp:
                                # Create initial entry for this component using the first horiozon CHK
                                dComp[cokey] = [mukey, comppct, hzT, aws, areasym]

                                try:
                                    dPct[mukey] = dPct[mukey] + comppct

                                except:
                                    dPct[mukey] = comppct

                            else:
                                # accumulate total thickness and total rating value by adding to existing component values  CHK
                                mukey, comppct, dHzT, dAWS, areasym = dComp[cokey]
                                dAWS = dAWS + aws
                                dHzT = dHzT + hzT
                                dComp[cokey] = [mukey, comppct, dHzT, dAWS, areasym]

                        #arcpy.SetProgressorPosition()

                # get the total number of major components from the dictionary count
                iComp = len(dComp)

                # Read through the component-level data and summarize to the mapunit level

                if iComp > 0:
                    #PrintMsg("\t" + str(top) + " - " + str(bot) + "cm (" + Number_Format(iComp, 0, True) + " components)"  , 0)

                    for cokey, dRec in dComp.items():
                        # get component level data  CHK
                        mukey, comppct, hzT, val, areasym = dRec

                        # get sum of component percent for the mapunit  CHK
                        try:
                            sumCompPct = float(dPct[mukey])

                        except:
                            # set the component percent to zero if it is not found in the
                            # dictionary. This is probably a 'Miscellaneous area' not included in the  CHK
                            # data or it has no horizon information.
                            sumCompPct = 0

                        #PrintMsg(areasym + ", " + mukey + ", " + cokey + ", " + str(comppct) + ", " + str(sumCompPct) + ", " + str(hzT) + ", " + str(val), 1)  # These look good


                        # calculate component percentage adjustment

                        if sumCompPct > 0:
                            # If there is no data for any of the component horizons, could end up with 0 for
                            # sum of comppct_r
                            adjCompPct = float(comppct) / sumCompPct   # WSS method

                            # adjust the rating value down by the component percentage and by the sum of the
                            # usable horizon thickness for this component
                            aws = adjCompPct * val
                            hzT = hzT * adjCompPct    # Adjust component share of horizon thickness by comppct

                            # Update component values in component dictionary
                            dComp[cokey] = mukey, comppct, hzT, aws, areasym

                            # Populate dMu dictionary
                            if mukey in dMu:
                                val1, val3, areasym = dMu[mukey]
                                comppct = comppct + val1
                                aws = aws + val3

                            dMu[mukey] = [comppct, aws, areasym]

                # Write out map unit aggregated AWS
                #
                murec = list()
                outputValues= [999999999, -999999999]

                for mukey, val in dMu.items():
                    compPct, aws, areasym = val
                    aws = round(aws, fldPrecision) # Test temporary removal of rounding
                    #aws = decimal.Decimal(str(aws)).quantize(decimal.Decimal("0.01"), decimal.ROUND_HALF_UP)
                    murec = [mukey, comppct, aws, areasym]
                    ocur.insertRow(murec)

                    # save max-min values
                    if not aws is None:
                        outputValues[0] = min(aws, outputValues[0])
                        outputValues[1] = max(aws, outputValues[1])

        outputValues.sort()

        #if (bZero and outputValues ==  [0.0, 0.0]):
            #PrintMsg("2. No data for " + sdvAtt, 1)

        return outputTbl, outputValues

    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return None, None

    except:
        # Catch python errors here
        # tbInfo contains the script, function and error line number
        tb = sys.exc_info()[2]
        tbInfo = traceback.format_tb(tb)[0]
        # Need to see how this handles errors that are in the main

        errInfo = str(sys.exc_info()[1])

        # Concatenate information together concerning the error into a message string
        pymsg = tbInfo + "\n" + errInfo

        if errInfo.find("MyError") == -1:
            # Report python errors
            PrintMsg("Python Error", 1)
            arcpy.AddError(pymsg)

        else:
            # raised error condition
            PrintMsg("Raised Error", 1)
            arcpy.AddError(err)

        return outputTbl, []

## ===================================================================================
def AggregateHz_WTA_WTA(gdb, sdvAtt, sdvFld, flatTbl, bZero, cutOff, tieBreaker, top, bot):
    # Aggregate mapunit-component-horizon data to the map unit level using a weighted average
    #
    # This version uses weighted average for horizon data as in AWC and most others
    # Added areasymbol to output
    try:
        arcpy.SetProgressorLabel("Aggregating rating information to the map unit level")

        #
        if bVerbose:
            PrintMsg("Current function : " + sys._getframe().f_code.co_name, 1)

        # Create final output table with MUKEY, COMPPCT_R and sdvFld
        outputTbl = os.path.join(gdb, tblName)
        fldPrecision = dSDV["attributeprecision"]
        inFlds = ["MUKEY", "COKEY", "COMPPCT_R", "HZDEPT_R", "HZDEPB_R", dSDV["attributecolumnname"].upper(), "AREASYMBOL"]
        outFlds = ["MUKEY", "COMPPCT_R", dSDV["resultcolumnname"].upper(), "AREASYMBOL"]

        sqlClause =  (None, "ORDER BY MUKEY ASC, COMPPCT_R DESC, HZDEPT_R ASC")

        if bZero:
            whereClause = "COMPPCT_R >=  " + str(cutOff)  # this will treat Nulls as zero which for example will lower pH values beyond the range when a lower horizon has no data

        else:
            whereClause = "COMPPCT_R >=  " + str(cutOff) + " AND " + dSDV["attributecolumnname"].upper() + " IS NOT NULL"

        if arcpy.Exists(outputTbl):
            arcpy.Delete_management(outputTbl)

        outputTbl = CreateOutputTable(tmpDS, flatTbl, outputTbl, dFieldInfo)

        if outputTbl == "":
            return outputTbl,[]

        dPct = dict()  # sum of comppct_r for each map unit
        dComp = dict() # component level information
        dMu = dict()

        # reset variables for cursor
        sumPct = 0
        sumProd = 0
        meanVal = 0

        with arcpy.da.SearchCursor(flatTbl, inFlds, where_clause=whereClause, sql_clause=sqlClause) as cur:
            with arcpy.da.InsertCursor(outputTbl, outFlds) as ocur:
                #arcpy.SetProgressor("step", "Reading initial query table ...",  0, iCnt, 1)

                for rec in cur:
                    mukey, cokey, comppct, hzdept, hzdepb, val, areasym = rec
                    # top = hzdept
                    # bot = hzdepb
                    # td = top of range
                    # bd = bottom of range
                    if val is None and bZero:
                        val = 0

                    if val is not None and hzdept is not None and hzdepb is not None:

                        # Calculate sum of horizon thickness and sum of component ratings for all horizons above bottom
                        try:
                            hzT = min(hzdepb, bot) - max(hzdept, top)   # usable thickness from this horizon

                        except:
                            hzT = 0

                        if hzT > 0:
                            aws = float(hzT) * val * comppct

                            if not cokey in dComp:
                                # Create initial entry for this component using the first horiozon CHK
                                dComp[cokey] = [mukey, comppct, hzT, aws, areasym]
                                try:
                                    dPct[mukey] = dPct[mukey] + comppct

                                except:
                                    dPct[mukey] = comppct

                            else:
                                # accumulate total thickness and total rating value by adding to existing component values  CHK
                                mukey, comppct, dHzT, dAWS, areasym = dComp[cokey]
                                dAWS = dAWS + aws
                                dHzT = dHzT + hzT
                                dComp[cokey] = [mukey, comppct, dHzT, dAWS, areasym]

                        #else:
                        #    PrintMsg("\tFound horizon for mapunit (" + mukey + ":" + cokey + " with hzthickness of " + str(hzT), 1)

                    #else:
                    #    PrintMsg("\tFound horizon with no data for mapunit (" + mukey + ":" + cokey + " with hzthickness of " + str(hzT), 1)

                # get the total number of major components from the dictionary count
                iComp = len(dComp)

                # Read through the component-level data and summarize to the mapunit level

                if iComp > 0:
                    #PrintMsg("\t" + str(top) + " - " + str(bot) + "cm (" + Number_Format(iComp, 0, True) + " components)"  , 0)
                    #arcpy.SetProgressor("step", "Saving map unit and component AWS data...",  0, iComp, 1)

                    for cokey, vals in dComp.items():

                        # get component level data
                        mukey, comppct, hzT, cval, areasym = vals

                        # get sum of comppct for mapunit
                        sumPct = dPct[mukey]

                        # calculate component weighted values
                        # get weighted layer thickness
                        divisor = sumPct * hzT

                        if divisor > 0:
                            newval = float(cval) / divisor

                        else:
                            newval = 0.0

                        if mukey in dMu:
                            pct, mval, areasym = dMu[mukey]
                            newval = newval + mval

                        dMu[mukey] = [sumPct, newval, areasym]

                # Write out map unit aggregated AWS
                #
                murec = list()
                outputValues= [999999999, -999999999]

                for mukey, vals in dMu.items():
                    sumPct, val, areasym = vals
                    aws = round(val, fldPrecision)
                    murec = [mukey, sumPct, aws, areasym]
                    ocur.insertRow(murec)
                    # save max-min values
                    if not aws is None:
                        outputValues[0] = min(aws, outputValues[0])
                        outputValues[1] = max(aws, outputValues[1])

        outputValues.sort()

        #if (bZero and outputValues ==  [0.0, 0.0]):
        #    PrintMsg("No data for " + sdvAtt, 1)


        return outputTbl, outputValues

    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return None, None

    except:
        # Catch python errors here
        # tbInfo contains the script, function and error line number
        tb = sys.exc_info()[2]
        tbInfo = traceback.format_tb(tb)[0]
        # Need to see how this handles errors that are in the main

        errInfo = str(sys.exc_info()[1])

        # Concatenate information together concerning the error into a message string
        pymsg = tbInfo + "\n" + errInfo

        if errInfo.find("MyError") == -1:
            # Report python errors
            PrintMsg("Python Error", 1)
            arcpy.AddError(pymsg)

        else:
            # raised error condition
            PrintMsg("Raised Error", 1)
            arcpy.AddError(err)

        return outputTbl, []

## ===================================================================================
def AggregateHz_DCP_WTA(gdb, sdvAtt, sdvFld, flatTbl, bZero, cutOff, tieBreaker, top, bot):
    #
    # Dominant component for mapunit-component-horizon data to the map unit level
    #
    # This version uses weighted average for horizon data
    # Added areasymbol to output
    #
    # Problem: Need to fix bZero logic related to pH (per Chad)

    try:
        arcpy.SetProgressorLabel("Aggregating rating information to the map unit level")

        # Create final output table with MUKEY, COMPPCT_R and sdvFld
        #bVerbose = True

        if bVerbose:
            PrintMsg("Current function : " + sys._getframe().f_code.co_name, 1)

        outputTbl = os.path.join(gdb, tblName)
        fldPrecision = dSDV["attributeprecision"]
        inFlds = ["MUKEY", "COKEY", "COMPPCT_R", "HZDEPT_R", "HZDEPB_R", dSDV["attributecolumnname"].upper(), "AREASYMBOL"]
        outFlds = ["MUKEY", "COMPPCT_R", dSDV["resultcolumnname"].upper(), "AREASYMBOL"]

        sqlClause =  (None, "ORDER BY MUKEY ASC, COMPPCT_R DESC, COKEY ASC, HZDEPT_R ASC")  # 2020-01-23 added cokey to sort

        if bZero:
            whereClause = "COMPPCT_R >=  " + str(cutOff)  # this will treat Nulls as zero which for example will lower pH values beyond the range when a lower horizon has no data

        else:
            whereClause = "COMPPCT_R >=  " + str(cutOff) + " AND " + dSDV["attributecolumnname"].upper() + " IS NOT NULL"


        if arcpy.Exists(outputTbl):
            arcpy.Delete_management(outputTbl)

        outputTbl = CreateOutputTable(tmpDS, flatTbl, outputTbl, dFieldInfo)
        outputValues = [999999999, -999999999]

        if outputTbl == "":
            err = ""
            raise MyError(err)

        dPct = dict()  # sum of comppct_r for each map unit
        dHorizon = dict()
        dComp = dict() # component level information
        dMu = dict()
        dCompList = dict()

        # reset variables for cursor
        sumPct = 0
        sumProd = 0
        meanVal = 0

        #testMu = '676909'  # STATSGO mapunit with inconsistencies in horizon calculations for dominant component

        with arcpy.da.SearchCursor(flatTbl, inFlds, where_clause=whereClause, sql_clause=sqlClause) as cur:
            with arcpy.da.InsertCursor(outputTbl, outFlds) as ocur:
                #arcpy.SetProgressor("step", "Reading initial query table ...",  0, iCnt, 1)

                for rec in cur:
                    mukey, cokey, comppct, hzdept, hzdepb, val, areasym = rec
                    # top = hzdept
                    # bot = hzdepb
                    # td = top of range
                    # bd = bottom of range

                    #if mukey == testMu:
                    #    PrintMsg("\tRaw: " + str(rec), 1)

                    if not cokey in dHorizon:
                        if not mukey in dPct:
                            # Problem:
                            # This statement above is only getting the first component and ignoring any ties based upon component percent
                            # It also may be skipping the dominant component when the value is Null. Is this what I really want?
                            #
                            dCompList[mukey] = [cokey]  # initialize list of components for this mapunit

                            dPct[mukey] = comppct  # cursor is sorted on comppct_r descending, so this should be dominant component percent.

                            if val is not None and hzdept is not None and hzdepb is not None:
                                # Normal component with horizon data
                                hzT = min(hzdepb, bot) - max(hzdept, top)
                                aws = float(hzT) * val
                                newrec = [mukey, comppct, hzT, aws, areasym]
                                dHorizon[cokey] = newrec

                                #if mukey == testMu:
                                #    PrintMsg("\t1. " + str(newrec), 1)

                            elif hzdept is not None and hzdepb is not None:
                                # new code to capture components where the rating value is Null
                                hzT = min(hzdepb, bot) - max(hzdept, top)
                                aws = None
                                newrec = [mukey, comppct, hzT, aws, areasym]
                                dHorizon[cokey] = newrec

                                #if mukey == testMu:
                                #    PrintMsg("\t1 For NULL. " + str(newrec), 1)


                        elif comppct >= dPct[mukey]:
                            # This should be a mapunit that has more than one dominant component
                            dCompList[mukey].append(cokey)

                            if val is not None and hzdept is not None and hzdepb is not None:
                                # Normal component with horizon data
                                hzT = min(hzdepb, bot) - max(hzdept, top)
                                aws = float(hzT) * val
                                newrec = [mukey, comppct, hzT, aws, areasym]
                                dHorizon[cokey] = newrec

                                #if mukey == testMu:
                                #    PrintMsg("\t2. " + str(newrec), 1)

                            elif hzdept is not None and hzdepb is not None:
                                # new code to capture components where the rating value is Null
                                hzT = min(hzdepb, bot) - max(hzdept, top)
                                aws = None
                                newrec = [mukey, comppct, hzT, aws, areasym]
                                dHorizon[cokey] = newrec

                                #if mukey == testMu:
                                #    PrintMsg("\t2 For NULL. " + str(newrec), 1)

                            else:
                                # Component with no data for this horizon
                                newrec = [mukey, comppct, None, None, areasym]
                                dHorizon[cokey] = newrec

                                #if mukey == testMu:
                                #    PrintMsg("\t3. " + str(newrec), 1)


                    else:
                        try:
                            # For dominant component:
                            # accumulate total thickness and total rating value by adding to existing component values  CHK

                            mukey, comppct, dHzT, dAWS, areasym = dHorizon[cokey]

                            if val is not None and hzdept is not None and hzdepb is not None:
                                hzT = min(hzdepb, bot) - max(hzdept, top)
                                aws = float(hzT) * val
                                dAWS = max(0, dAWS) + aws
                                dHzT = max(0, dHzT) + hzT
                                newrec = [mukey, comppct, dHzT, dAWS, areasym]
                                dHorizon[cokey] = newrec

                                #if mukey == testMu:
                                #    PrintMsg("\t4. " + str(newrec), 1)

                            elif hzdept is not None and hzdepb is not None:
                                hzT = min(hzdepb, bot) - max(hzdept, top)
                                aws = 0
                                dAWS = max(0, dAWS) + aws
                                dHzT = max(0, dHzT) + hzT
                                newrec = [mukey, comppct, dHzT, dAWS, areasym]
                                dHorizon[cokey] = newrec

                                #if mukey == testMu:
                                #    PrintMsg("\t4 For Null. " + str(newrec), 1)

                        except KeyError:
                            # Hopefully this is a component other than dominant
                            #if mukey == testMu:
                            #    PrintMsg("\t5. Skipped because of dHorizon KeyError for cokey: " + cokey, 1)
                            pass

                        except:
                            errorMsg1()


                # get the total number of major components from the dictionary count
                iComp = len(dHorizon)

                # Read through the component-level data and summarize to the mapunit level

                if iComp > 0:

                    for cokey, vals in dHorizon.items():

                        # get component level data
                        mukey, pct, hzT, cval, areasym = vals

                        # calculate mean value for entire depth range
                        if not cval is None and hzT > 0:
                            newval = float(cval) / hzT

                        else:
                            newval = None

                        if cokey in dComp:
                            pct, mval, areasym = dComp[cokey]
                            newval = newval + mval

                        dComp[cokey] = [pct, newval, areasym]

                # Test iteration through dCompList?? and replace dMu
                if tieBreaker == dSDV["tiebreakhighlabel"]:
                    bRev = True

                else:
                    bRev = False

                for mukey, cokeys in dCompList.items():
                    if len(cokeys) > 0:
                        # find component with value according to tiebreaker rule
                        # assign that set of values to dMu
                        valList = list()

                        for cokey in cokeys:
                            try:
                                pct, newval, areasym = dComp[cokey]

                                if not newval is None:
                                    valList.append(newval)

                            except:
                                #PrintMsg("\tNo data for cokey: " + cokey, 1)
                                pass

                        if len(valList):
                            valList.sort(reverse=bRev)
                            val = valList[0]

                            if not val is None:
                                val = round(val, fldPrecision)

                            outputValues[0] = min(valList[0], outputValues[0])
                            outputValues[1] = max(valList[0], outputValues[1])

                        else:
                            val = None


                        murec =  mukey, pct, val, areasym
                        #dMu[mukey] = newrec
                        ocur.insertRow(murec)
                        #PrintMsg("\tMapunit: " + mukey + "; " + str(pct) + "%; " + str(val), 1)


        outputValues.sort()

        #if (bZero and outputValues ==  [0.0, 0.0]):
        #    PrintMsg("No data for " + sdvAtt, 1)

        return outputTbl, outputValues

    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return None, None

    except:
        # Catch python errors here
        # tbInfo contains the script, function and error line number
        tb = sys.exc_info()[2]
        tbInfo = traceback.format_tb(tb)[0]
        # Need to see how this handles errors that are in the main

        errInfo = str(sys.exc_info()[1])

        # Concatenate information together concerning the error into a message string
        pymsg = tbInfo + "\n" + errInfo

        if errInfo.find("MyError") == -1:
            # Report python errors
            PrintMsg("Python Error", 1)
            arcpy.AddError(pymsg)

        else:
            # raised error condition
            PrintMsg("Raised Error", 1)
            arcpy.AddError(err)

        return outputTbl, outputValues

## ===================================================================================
def AggregateHz_MaxMin_WTA(gdb, sdvAtt, sdvFld, flatTbl, bZero, cutOff, tieBreaker, top, bot):
    # Aggregate mapunit-component-horizon data to the map unit level using weighted average
    # for horizon data, but the assigns either the minimum or maximum component rating to
    # the map unit, depending upon the Tiebreaker setting.
    # Added areasymbol to output
    try:
        arcpy.SetProgressorLabel("Aggregating rating information to the map unit level")
        #
        if bVerbose:
            PrintMsg("Current function : " + sys._getframe().f_code.co_name, 1)

        # Create final output table with MUKEY, COMPPCT_R and sdvFld
        outputTbl = os.path.join(gdb, tblName)
        fldPrecision = dSDV["attributeprecision"]

        inFlds = ["MUKEY", "COKEY", "COMPPCT_R", "HZDEPT_R", "HZDEPB_R", dSDV["attributecolumnname"].upper(), "AREASYMBOL"]
        outFlds = ["MUKEY", "COMPPCT_R", dSDV["resultcolumnname"].upper(), "AREASYMBOL"]

        sqlClause =  (None, "ORDER BY MUKEY ASC, COMPPCT_R DESC, HZDEPT_R ASC")

        if bZero == False:
            # ignore any null values
            whereClause = "COMPPCT_R >=  " + str(cutOff) + " AND " + dSDV["attributecolumnname"].upper() + " IS NOT NULL"

        else:
            # retrieve null values and convert to zeros during the iteration process
            whereClause = "COMPPCT_R >=  " + str(cutOff)

        if arcpy.Exists(outputTbl):
            arcpy.Delete_management(outputTbl)

        outputTbl = CreateOutputTable(tmpDS, flatTbl, outputTbl, dFieldInfo)

        if outputTbl == "":
            return outputTbl,[]

        dPct = dict()  # sum of comppct_r for each map unit
        dComp = dict() # component level information
        dMu = dict()

        # reset variables for cursor
        sumPct = 0
        sumProd = 0
        meanVal = 0

        with arcpy.da.SearchCursor(flatTbl, inFlds, where_clause=whereClause, sql_clause=sqlClause) as cur:
            with arcpy.da.InsertCursor(outputTbl, outFlds) as ocur:

                for rec in cur:
                    mukey, cokey, comppct, hzdept, hzdepb, val, areasym = rec
                    # top = hzdept
                    # bot = hzdepb
                    # td = top of range
                    # bd = bottom of range
                    if val is None and bZero:
                        val = 0

                    if val is not None and hzdept is not None and hzdepb is not None:

                        # Calculate sum of horizon thickness and sum of component ratings for all horizons above bottom
                        try:
                            hzT = min(hzdepb, bot) - max(hzdept, top)   # usable thickness from this horizon

                        except:
                            hzT = 0

                        if hzT > 0:
                            rating = float(hzT) * val   # Not working for KFactor WTA
                            #rating = float(hzT) * float(val)   # Try floating the KFactor to see if that will work. Won't it still have to be rounded to standard KFactor index value?

                            #PrintMsg("\t" + str(aws), 1)

                            if not cokey in dComp:
                                # Create initial entry for this component using the first horiozon CHK
                                dComp[cokey] = [mukey, comppct, hzT, rating, areasym]

                            else:
                                # accumulate total thickness and total rating value by adding to existing component values  CHK
                                mukey, comppct, dHzT, dRating, areasym = dComp[cokey]
                                dRating += rating
                                dHzT += hzT
                                dComp[cokey] = [mukey, comppct, dHzT, dRating, areasym]

                # get the total number of major components from the dictionary count
                iComp = len(dComp)

                # Read through the component-level data and summarize to the mapunit level

                if iComp > 0:
                    #PrintMsg("\t" + str(top) + " - " + str(bot) + "cm (" + Number_Format(iComp, 0, True) + " components)"  , 0)

                    for cokey, vals in dComp.items():

                        # get component level data
                        mukey, comppct, hzT, cval, areasym = vals
                        if not cval is None and hzT > 0:
                            rating = cval / hzT  # final horizon weighted average for this component

                        else:
                            rating = None

                        #PrintMsg("\t" + mukey + ", " + cokey + ", " + str(round(rating, 1)), 1)

                        try:
                            # append component weighted average rating to the mapunit dictionary
                            dMu[mukey].append([comppct, rating, areasym])

                        except:
                            # create a new mapunit record in the dictionary
                            dMu[mukey] = [[comppct, rating, areasym]]

                # Write out map unit aggregated rating
                #
                #murec = list()
                outputValues = [999999999, -999999999]

                if tieBreaker == dSDV["tiebreakhighlabel"]:
                    for mukey, muVals in dMu.items():
                        muVal = SortData(muVals, 1, 0, True, True)
                        pct, val, areasym = muVal
                        rating = round(val, fldPrecision)
                        murec = [mukey, pct, rating, areasym]
                        ocur.insertRow(murec)

                        if not rating is None:
                            # save overall max-min values
                            outputValues[0] = min(rating, outputValues[0])
                            outputValues[1] = max(rating, outputValues[1])

                else:
                    # Lower
                    for mukey, muVals in dMu.items():
                        muVal = SortData(muVals, 1, 0, False, True)
                        pct, val, areasym = muVal
                        rating = round(val, fldPrecision)
                        murec = [mukey, pct, rating, areasym]
                        ocur.insertRow(murec)

                        if not rating is None:
                            # save overall max-min values
                            outputValues[0] = min(rating, outputValues[0])
                            outputValues[1] = max(rating, outputValues[1])

        #if (bZero and outputValues ==  [0.0, 0.0]):
        #    PrintMsg("7. No data for " + sdvAtt, 1)

        return outputTbl, outputValues

    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return None, None

    except:
        # Catch python errors here
        # tbInfo contains the script, function and error line number
        tb = sys.exc_info()[2]
        tbInfo = traceback.format_tb(tb)[0]
        # Need to see how this handles errors that are in the main

        errInfo = str(sys.exc_info()[1])

        # Concatenate information together concerning the error into a message string
        pymsg = tbInfo + "\n" + errInfo

        if errInfo.find("MyError") == -1:
            # Report python errors
            PrintMsg("Python Error", 1)
            arcpy.AddError(pymsg)

        else:
            # raised error condition
            PrintMsg("Raised Error", 1)
            arcpy.AddError(err)

        return outputTbl, []

## ===================================================================================
def AggregateHz_MaxMin_DCD(gdb, sdvAtt, sdvFld, flatTbl, bZero, cutOff, tieBreaker, top, bot):
    # Aggregate mapunit-component-horizon data to the map unit level using the highest rating
    # from all horizons. Currently this would only apply to K Factor and dominant condition.

    try:
        arcpy.SetProgressorLabel("Aggregating rating information to the map unit level")
        #
        if bVerbose:
            PrintMsg("Current function : " + sys._getframe().f_code.co_name, 1)

        # Create final output table with MUKEY, COMPPCT_R and sdvFld
        outputTbl = os.path.join(gdb, tblName)
        fldPrecision = dSDV["attributeprecision"]

        inFlds = ["MUKEY", "COKEY", "COMPPCT_R", "HZDEPT_R", "HZDEPB_R", dSDV["attributecolumnname"].upper(), "AREASYMBOL"]
        outFlds = ["MUKEY", "COMPPCT_R", dSDV["resultcolumnname"].upper(), "AREASYMBOL"]

        sqlClause =  (None, "ORDER BY MUKEY ASC, COMPPCT_R DESC, HZDEPT_R ASC")

        if bZero == False:
            # ignore any null values
            whereClause = "COMPPCT_R >=  " + str(cutOff) + " AND " + dSDV["attributecolumnname"].upper() + " IS NOT NULL"

        else:
            # retrieve null values and convert to zeros during the iteration process
            whereClause = "COMPPCT_R >=  " + str(cutOff)

        if arcpy.Exists(outputTbl):
            arcpy.Delete_management(outputTbl)

        outputTbl = CreateOutputTable(tmpDS, flatTbl, outputTbl, dFieldInfo)

        if outputTbl == "":
            return outputTbl,[]

        dPct = dict()  # sum of comppct_r for each map unit
        dComp = dict() # component level information
        dMu = dict()

        # reset variables for cursor
        sumPct = 0
        sumProd = 0
        meanVal = 0

        with arcpy.da.SearchCursor(flatTbl, inFlds, where_clause=whereClause, sql_clause=sqlClause) as cur:
            with arcpy.da.InsertCursor(outputTbl, outFlds) as ocur:

                for rec in cur:
                    mukey, cokey, comppct, hzdept, hzdepb, val, areasym = rec
                    # top = hzdept
                    # bot = hzdepb
                    # td = top of range
                    # bd = bottom of range

                    if val is not None and hzdept is not None and hzdepb is not None:

                        # Calculate sum of horizon thickness and sum of component ratings for all horizons above bottom
                        try:
                            hzT = min(hzdepb, bot) - max(hzdept, top)   # usable thickness from this horizon

                        except:
                            hzT = 0

                        if hzT > 0:
                            ratingIndx = domainValues.index(val)   # Change KFactor to an index based upon domain order

                            #PrintMsg("\t" + str(aws), 1)

                            if not cokey in dComp:
                                # Create initial entry for this component using the first horiozon CHK
                                ratingList = [ratingIndx]
                                dComp[cokey] = [mukey, comppct, ratingList, areasym]

                            else:
                                # accumulate total thickness and total rating value by adding to existing component values  CHK
                                mukey, comppct, ratingList, areasym = dComp[cokey]

                                if not ratingIndx in ratingList:
                                    ratingList.append(ratingIndx)
                                    dComp[cokey] = [mukey, comppct, ratingList, areasym]

                # get the total number of major components from the dictionary count
                iComp = len(dComp)

                # Read through the component-level data and summarize to the mapunit level

                if iComp > 0:
                    #PrintMsg("\t" + str(top) + " - " + str(bot) + "cm (" + Number_Format(iComp, 0, True) + " components)"  , 0)

                    for cokey, vals in dComp.items():

                        # get component level data
                        mukey, comppct, ratingList, areasym = vals

                        ratingIndx = max(ratingList)  # get highest K Factor from all horizons for this component
                        #PrintMsg("\t" + mukey + ", " + cokey + ", " + str(round(rating, 1)), 1)

                        try:
                            # append component weighted average rating to the mapunit dictionary
                            dMu[mukey].append([comppct, ratingIndx, areasym])

                        except:
                            # create a new mapunit record in the dictionary
                            dMu[mukey] = [[comppct, ratingIndx, areasym]]

                # Write out map unit aggregated rating
                #
                outputValues = [domainValues[0], domainValues[-1]]

                #if tieBreaker == dSDV["tiebreakhighlabel"]:
                oid = 0

                for mukey, muVals in dMu.items():
                    oid += 1
                    #muVal = SortData(muVals, 1, 0, True, True)
                    muVal = SortData(muVals, 0, 0, True, True)
                    pct, ratingIndx, areasym = muVal
                    rating = domainValues[ratingIndx]
                    murec = [mukey, pct, rating, areasym]


                    #if mukey == "1427104":
                    #if mukey == "1380525":
                    #    PrintMsg("Output Table: " + outputTbl, 1)
                    #    PrintMsg("\t" + str(muVals), 1)
                    #    PrintMsg("\t" + str(muVal), 1)
                    #    PrintMsg("\t" + rating, 1)
                    #    PrintMsg("\t" + str(oid) + ", " + str(murec), 1)


                    ocur.insertRow(murec)

                    if not rating is None:
                    #    # save overall max-min values
                        outputValues[0] = min(rating, outputValues[0])
                        outputValues[1] = max(rating, outputValues[1])

        return outputTbl, outputValues

    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return None, None

    except:
        # Catch python errors here
        # tbInfo contains the script, function and error line number
        tb = sys.exc_info()[2]
        tbInfo = traceback.format_tb(tb)[0]
        # Need to see how this handles errors that are in the main

        errInfo = str(sys.exc_info()[1])

        # Concatenate information together concerning the error into a message string
        pymsg = tbInfo + "\n" + errInfo

        if errInfo.find("MyError") == -1:
            # Report python errors
            PrintMsg("Python Error", 1)
            arcpy.AddError(pymsg)

        else:
            # raised error condition
            PrintMsg("Raised Error", 1)
            arcpy.AddError(err)

        return outputTbl, []

## ===================================================================================
def AggregateHz_MaxMin_DCP(gdb, sdvAtt, sdvFld, flatTbl, bZero, cutOff, tieBreaker, top, bot):
    # Aggregate mapunit-component-horizon data to the map unit level using the highest rating
    # from all horizons. Currently this would only apply to K Factor and dominant component

    try:
        arcpy.SetProgressorLabel("Aggregating rating information to the map unit level")
        #
        if bVerbose:
            PrintMsg("Current function : " + sys._getframe().f_code.co_name, 1)

        # Create final output table with MUKEY, COMPPCT_R and sdvFld
        outputTbl = os.path.join(gdb, tblName)
        fldPrecision = dSDV["attributeprecision"]

        inFlds = ["MUKEY", "COKEY", "COMPPCT_R", "HZDEPT_R", "HZDEPB_R", dSDV["attributecolumnname"].upper(), "AREASYMBOL"]
        outFlds = ["MUKEY", "COMPPCT_R", dSDV["resultcolumnname"].upper(), "AREASYMBOL"]

        sqlClause =  (None, "ORDER BY MUKEY ASC, COMPPCT_R DESC, HZDEPT_R ASC")

        if bZero == False:
            # ignore any null values
            whereClause = "COMPPCT_R >=  " + str(cutOff) + " AND " + dSDV["attributecolumnname"].upper() + " IS NOT NULL"

        else:
            # retrieve null values and convert to zeros during the iteration process
            whereClause = "COMPPCT_R >=  " + str(cutOff)

        if arcpy.Exists(outputTbl):
            arcpy.Delete_management(outputTbl)

        outputTbl = CreateOutputTable(tmpDS, flatTbl, outputTbl, dFieldInfo)

        if outputTbl == "":
            return outputTbl,[]

        dPct = dict()  # sum of comppct_r for each map unit
        dComp = dict() # component level information
        dMu = dict()

        # reset variables for cursor
        sumPct = 0
        sumProd = 0
        meanVal = 0

        with arcpy.da.SearchCursor(flatTbl, inFlds, where_clause=whereClause, sql_clause=sqlClause) as cur:
            with arcpy.da.InsertCursor(outputTbl, outFlds) as ocur:

                for rec in cur:
                    mukey, cokey, comppct, hzdept, hzdepb, val, areasym = rec
                    # top = hzdept
                    # bot = hzdepb
                    # td = top of range
                    # bd = bottom of range

                    if val is not None and hzdept is not None and hzdepb is not None:

                        # Calculate sum of horizon thickness and sum of component ratings for all horizons above bottom
                        try:
                            hzT = min(hzdepb, bot) - max(hzdept, top)   # usable thickness from this horizon

                        except:
                            hzT = 0

                        if hzT > 0:
                            ratingIndx = domainValues.index(val)   # Change KFactor to an index based upon domain order

                            #PrintMsg("\t" + str(aws), 1)

                            if not cokey in dComp:
                                if not mukey in dMu:
                                    dMu[mukey] = cokey

                                    # Create initial entry for this component using the first horiozon CHK
                                    ratingList = [ratingIndx]
                                    dComp[cokey] = [mukey, comppct, ratingList, areasym]

                            elif cokey == dMu[mukey]:
                                # accumulate total thickness and total rating value by adding to existing component values  CHK
                                mukey, comppct, ratingList, areasym = dComp[cokey]

                                if not ratingIndx in ratingList:
                                    ratingList.append(ratingIndx)
                                    dComp[cokey] = [mukey, comppct, ratingList, areasym]

                # get the total number of major components from the dictionary count
                iComp = len(dComp)

                # Read through the component-level data and summarize to the mapunit level

                if iComp > 0:
                    #PrintMsg("\t" + str(top) + " - " + str(bot) + "cm (" + Number_Format(iComp, 0, True) + " components)"  , 0)

                    for cokey, vals in dComp.items():

                        # get component level data
                        mukey, comppct, ratingList, areasym = vals

                        ratingIndx = max(ratingList)  # get highest K Factor from all horizons for this component
                        #PrintMsg("\t" + mukey + ", " + cokey + ", " + str(round(rating, 1)), 1)

                        try:
                            # append component weighted average rating to the mapunit dictionary
                            dMu[mukey].append([comppct, ratingIndx, areasym])

                        except:
                            # create a new mapunit record in the dictionary
                            dMu[mukey] = [[comppct, ratingIndx, areasym]]

                # Write out map unit aggregated rating
                #
                outputValues = [domainValues[0], domainValues[-1]]

                #if tieBreaker == dSDV["tiebreakhighlabel"]:
                oid = 0

                for mukey, muVals in dMu.items():
                    oid += 1
                    muVal = SortData(muVals, 1, 0, True, True)
                    pct, ratingIndx, areasym = muVal
                    rating = domainValues[ratingIndx]
                    murec = [mukey, pct, rating, areasym]
                    #if mukey == "1427104":
                    #    PrintMsg("Output Table: " + outputTbl, 1)
                    #    PrintMsg("\t" + str(muVals), 1)
                    #    PrintMsg("\t" + str(muVal), 1)
                    #    PrintMsg("\t" + rating, 1)
                    #    PrintMsg("\t" + str(oid) + ", " + str(murec), 1)
                    ocur.insertRow(murec)

                    if not rating is None:
                    #    # save overall max-min values
                        outputValues[0] = min(rating, outputValues[0])
                        outputValues[1] = max(rating, outputValues[1])

        return outputTbl, outputValues

    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return None, None

    except:
        # Catch python errors here
        # tbInfo contains the script, function and error line number
        tb = sys.exc_info()[2]
        tbInfo = traceback.format_tb(tb)[0]
        # Need to see how this handles errors that are in the main

        errInfo = str(sys.exc_info()[1])

        # Concatenate information together concerning the error into a message string
        pymsg = tbInfo + "\n" + errInfo

        if errInfo.find("MyError") == -1:
            # Report python errors
            PrintMsg("Python Error", 1)
            arcpy.AddError(pymsg)

        else:
            # raised error condition
            PrintMsg("Raised Error", 1)
            arcpy.AddError(err)

        return outputTbl, []

## ===================================================================================
def AggregateData(inputLayer, gdb, dFilter, sdvAtt, aggMethod, primCst, secCst, top, bot, begMo, endMo, tieBreaker, bZero, bFuzzy):
    # sdvAtt, aggMethod, primCst, secCst, top, bot, begMo, endMo, tieBreaker, bZero, cutOff, bFuzzy, sRV, grpLayerName, mxd, dfName
    # function that can be called by other scripts
    #
    # To do:
    #    switch parameters from menu to a JSON dictionary
    #    add two new arguments 1. filter field (mukey or areasymbol or lkey), 2. JSON list of key valuess for filter
    #
    # OGR Reference:
    # https://pcjericks.github.io/py-gdalogr-cookbook/gotchas.html
    # https://pcjericks.github.io/py-gdalogr-cookbook/
    # https://gdal.org/python/
    #
    try:
        global bVerbose

        global fc, muDesc, dataType, tmpDS, legendQuery # gdb

        bVerbose = False   # hard-coded boolean to print diagnostic messages
        bVerbose = True

        if bVerbose:
            PrintMsg("Current function : " + sys._getframe().f_code.co_name, 1)

        PrintMsg("Aggregating soils data for: " + str(sdvAtt), 0)

        # Set component percent cutoff to zero. May want to remove any use of this variable.
        cutOff = 0

        # Get featureclass from inputLayer
        # Problem if the featureclass is not named the same as the featurelayer (in TOC)
        if inputLayer.startswith("main."):
            inputLayer = inputLayer[5:]

        # OGR. Get ogr input driver for input database
        # Follow up with a second driver for SQLite that will be used for temporary tables such as SDV_Data
        #
        dbName, dbExt = os.path.splitext(os.path.basename(gdb))

        if dbExt == ".gdb":
            # input database is ESRI file geodatabase
            # Big problem is this is a read-only driver. This may limit me to using SQLite database for
            # temporary tables and outputting only JSON data.
            #
            driverName = "OpenFileGDB"

        elif dbExt == ".gpkg":
            # input database is geopackage
            driverName = "GPKG"

        elif dbExt == ".sqlite":
            driverName = "SQLite"

        else:
            err = "I am Unable to handle type of database for " + gdb
            raise MyError(err)

        inputDriver = ogr.GetDriverByName(driverName)

        if inputDriver is None:
            err = "Failed to get OGR inputDriver for " + gdb
            raise MyError(err)

        # Create the environment
        # from arcpy import env

        # Get target gSSURGO database. This needs to be migrated to ogr
        # Driver names: OpenFileGDB, SQLite, GPKG, ESRI Shapefile, Memory, ODBC

        ds = inputDriver.Open(gdb, 0)  # open input database with read-only access

        # OGR. open input database
        if ds is None:
            err = "Failed to open database '" + gdb + "' using driver: " + driverName
            raise MyError(err)

        # Create output driver and temporary database (try memory and SQLite)
        # Open output database in write mode
        tmpDBName = "TempDB"
        outputDriver = ogr.GetDriverByName("memory")
        tmpDS = outputDriver.CreateDataSource(tmpDBName)
        tmp = outputDriver.Open(tmpDBName, 1)

        if tmpDS is None:
            err = "Failed to create in-memory dataset"
            raise MyError(err)

        # OGR. Create in-memory database for use as storage for temporary tables such as SDV_Data, etc.
        #tmpName = "TempDB
        #memDriver = ogr.GetDriverByName("memory")
        #tmpDB = memDriver.CreateDataSource(tmpName)




        # OGR. open input soil polygon layer
        # problem. This will just be the featureclass, not the featurelayer with any possible filters or selections
        #
        muLayer = ds.GetLayerByName(inputLayer)

        if muLayer is None:
            err = "Failed to open '" + inputLayer + "' in " + os.path.basename(gdb)
            raise MyError(err)

        else:
            PrintMsg("Got layer object for " + inputLayer, 1)

        # Get count for featureclass. This is not the selected set.
        fcCnt = muLayer.GetFeatureCount()

        PrintMsg("Count of soil polygons: " + Number_Format(fcCnt, 0, True), 1)

        if "field" in dFilter and "values" in dFilter:
            filterField = dFilter["field"]
            filterValues = dFilter["values"]

            if len(filterValues) == 1:
                filterQuery = filterField + " = " + filterValues[0]

            else:
                filterQuery = filterField + " IN " + str(tuple(filterValues))

            PrintMsg("Using test query: " + filterQuery, 1)

            muLayer.SetAttributeFilter(filterQuery)

        else:
            filterQuery = ""
            PrintMsg("No filter used for input polygon layer", 1)

        # OGR. GetFeatureCount always returns the count for all records, not the selected set.
        # Only iteration using GetNextFeature will use the filter.
        polyCnt = 0
        areasymbolList = list()
        feat = muLayer.GetNextFeature()

        while feat is not None:
            polyCnt += 1
            areasym = feat.GetField("areasymbol")  # this will be a problem for a raster layer

            if not areasym in areasymbolList:
                areasymbolList.append(areasym)
                PrintMsg("Adding '" + areasym + "' to list", 1)

            feat = muLayer.GetNextFeature()

        muLayer.ResetReading()

        PrintMsg("Follow up count of selected soil polygons: " + Number_Format(polyCnt, 0, True), 1)

        PrintMsg("areasymbolList: " + str(areasymbolList), 1)

        dAreasymbols = GetAreasymbols(ds, areasymbolList)

        # Getting Areasymbols and legendkeys
        if len(dAreasymbols) == 0:
            err = "xxx dAreasymbols is not populated"
            raise MyError(err)


        # OGR. Get soil polygon layer fields
        muDef = muLayer.GetLayerDefn()
        muFieldNames = list()

        for n in range(muDef.GetFieldCount()):
            fDef = muDef.GetFieldDefn(n)
            muFieldNames.append(fDef.name)


        # Create list of months for use in some queries
        moList = ListMonths()

        # Create a dictionary based upon domainValues or legendValues.
        # This dictionary will use an uppercase-string version of the original value as the key
        #
        global dValues
        dValues = dict()  # Try creating a new dictionary. Key is uppercase-string value. Value = [order, original value]

        # Dictionary for aggregation method abbreviations
        #
        global dAgg
        dAgg = dict()
        dAgg["Dominant Component"] = "DCP"
        dAgg["Dominant Condition"] = "DCD"
        dAgg["No Aggregation Necessary"] = ""
        dAgg["Percent Present"] = "PP"
        dAgg["Weighted Average"] = "WTA"
        dAgg["Most Limiting"] = "ML"
        dAgg["Least Limiting"] = "LL"
        dAgg[""] = ""

        # raise MyError("EARLY OUT")

        # Open sdvattribute table and query for [attributename] = sdvAtt
        # if aggMethod is not already set, get the default method from the sdvattribute table
        global dSDV

        dSDV = GetSDVAtts(ds, sdvAtt, aggMethod, tieBreaker, bFuzzy)  # In batch mode, bFuzzy is set to False. This does not work for interps like NCCPI.

        if aggMethod == "":
            aggMethod = dSDV["algorithmname"]

        if (sdvAtt in ["Surface Texture"] or sdvAtt.endswith("(Surface)")) and not (top == 0 and bot == 1):
            # The CreateSoilMap tool, unlike SDV or WSS will allow the user to specify a slice other than 0-1cm for
            # surface texture. No longer appropriate to use the word 'Surface' in describing the output layer.

            if __name__ == "__main__":
                PrintMsg("Renaming layer...", 1)

                if sdvAtt == "Surface Texture":
                    #outputLayer = "Texture"
                    dSDV["resultcolumnname"] = "TEXTURE"

                elif sdvAtt.endswith("(Surface)"):
                    #outputLayer = sdvAtt.replace("(Surface)", ", ")
                    pass

            else:
                PrintMsg("Keeping this as a surface layer...", 1)
                #outputLayer = sdvAtt
                top = 0
                bot = 1

        if dSDV["attributetype"].lower() == "interpretation" and dSDV["effectivelogicaldatatype"] == "float":
            # For batch mode processing, override default bFuzzy setting to true. This applies to NCCPI interps.
            bFuzzy == True

        if tieBreaker == "":
            if dSDV["tiebreakrule"] == -1:
                tieBreaker = dSDV["tiebreaklowlabel"]

                if tieBreaker is None or tieBreaker == "":
                    tieBreaker = "Lower"

            else:
                tieBreaker = dSDV["tiebreakhighlabel"]

                if tieBreaker is None:
                    tieBreaker = "Higher"

        # Set null replacement values according to SDV rules
        global nullRating

        if not dSDV["nullratingreplacementvalue"] is None:
            if dSDV["attributelogicaldatatype"].lower() == "integer":
                nullRating = int(dSDV["nullratingreplacementvalue"])

            elif dSDV["attributelogicaldatatype"].lower() == "float":
                nullRating = float(dSDV["nullratingreplacementvalue"])

            elif dSDV["attributelogicaldatatype"].lower() in ["string", "choice"]:
                nullRating = dSDV["nullratingreplacementvalue"]

            else:
                nullRating = None

        else:
            nullRating = None

        if dSDV["interpnullsaszerooptionflag"]:
            bZero = True

        if len(dSDV) == 0:
            err = "dSDV is not populated"
            raise MyError(err)

        # 'Big' 3 tables
        big3Tbls = ["MAPUNIT", "COMPONENT", "CHORIZON"]

        #  Create a dictionary to define minimum field list for the tables being used
        #
        global dFields
        dFields = dict()
        dFields["MAPUNIT"] = ["MUKEY", "MUSYM", "MUNAME", "LKEY"]
        dFields["COMPONENT"] = ["MUKEY", "COKEY", "COMPNAME", "COMPPCT_R"]
        dFields["CHORIZON"] = ["COKEY", "CHKEY", "HZDEPT_R", "HZDEPB_R"]
        dFields["COMONTH"] = ["COKEY", "COMONTHKEY"]

        # Create dictionary containing substitute values for missing data
        global dMissing
        dMissing = dict()
        dMissing[dSDV["attributetablename"].upper()] = [nullRating]
        dMissing["MAPUNIT"] = [None] * len(dFields["MAPUNIT"])
        dMissing["COMPONENT"] = [None] * (len(dFields["COMPONENT"]) - 1)  # adjusted number down because of mukey
        dMissing["CHORIZON"] = [None] * (len(dFields["CHORIZON"]) - 1)
        dMissing["COMONTH"] = [None] * (len(dFields["COMONTH"]) - 1)

        # Dictionary containing sql_clauses for the Big 3
        #
        global dSQL
        dSQL = dict()
        dSQL["MAPUNIT"] = (None, "ORDER BY MUKEY ASC")
        dSQL["COMPONENT"] = (None, "ORDER BY MUKEY ASC, COMPPCT_R DESC")
        dSQL["CHORIZON"] = (None, "ORDER BY COKEY ASC, HZDEPT_R ASC")

        # Get information about the SDV output result field
        # PrintMsg("dFieldInfo resultcolumnname: " + dSDV["resultcolumnname"], 1)
        resultcolumn = dSDV["resultcolumnname"]
        primaryconcolname = dSDV["primaryconcolname"]
        secondaryconcolname = dSDV["secondaryconcolname"]

        if primaryconcolname is not None:
            primaryconcolname = primaryconcolname.upper()

        if secondaryconcolname is not None:
            secondaryconcolname = secondaryconcolname.upper()

        # Create dictionary to contain key field definitions
        # AddField_management (in_table, field_name, field_type, {field_precision}, {field_scale}, {field_length}, {field_alias}, {field_is_nullable}, {field_is_required}, {field_domain})
        # TEXT, FLOAT, DOUBLE, SHORT, LONG, DATE, BLOB, RASTER, GUID
        # field_type, field_length (text only),
        #
        global dFieldInfo
        dFieldInfo = dict()

        # Convert original sdvattribute field settings to ArcGIS data types
        # and for use in JSON header
        if dSDV["effectivelogicaldatatype"].upper() in ['CHOICE', 'STRING']:
            #
            dFieldInfo[resultcolumn.upper()] = ["CHARACTER", 254]
            dFieldInfo[dSDV["attributecolumnname"].upper()] = ["CHARACTER", 254]

        elif dSDV["effectivelogicaldatatype"].upper() in ['VTEXT', 'NARRATIVE TEXT']:
            #
            dFieldInfo[resultcolumn.upper()] = ["CHARACTER", 1024]  # guess
            dFieldInfo[dSDV["attributecolumnname"].upper()] = ["CHARACTER", 1024]

        elif dSDV["effectivelogicaldatatype"].upper() == 'FLOAT':
            #dFieldInfo[resultcolumn] = ["DOUBLE", ""]
            dFieldInfo[resultcolumn.upper()] = ["REAL", ""]  # trying to match muaggatt table data type
            dFieldInfo[dSDV["attributecolumnname"].upper()] = ["REAL", ""]

        elif dSDV["effectivelogicaldatatype"].upper() == 'INTEGER':
            dFieldInfo[resultcolumn.upper()] = ["INTEGER", ""]
            dFieldInfo[dSDV["attributecolumnname"].upper()] = ["INTEGER", ""]

        else:
            err = "Failed to set dFieldInfo for " + resultcolumn + ", " + dSDV["effectivelogicaldatatype"]
            raise MyError(err)

        # Define datatypes for some of the most commonly used fields
        dFieldInfo["AREASYMBOL"] = ["TEXT", 20]
        dFieldInfo["LKEY"] = ["INTEGER", ""]
        dFieldInfo["MUKEY"] = ["INTEGER", ""]
        dFieldInfo["MUSYM"] = ["CHARACTER", 6]
        dFieldInfo["MUNAME"] = ["CHARACTER", 240]
        dFieldInfo["COKEY"] = ["INTEGER", ""]
        dFieldInfo["COMPNAME"] = ["CHARACTER", 60]
        dFieldInfo["CHKEY"] = ["INTEGER", ""]
        dFieldInfo["COMPPCT_R"] = ["INTEGER", ""]
        dFieldInfo["HZDEPT_R"] = ["INTEGER", ""]
        dFieldInfo["HZDEPB_R"] = ["INTEGER", ""]
        dFieldInfo["INTERPHR"] = ["REAL", ""]  # trying to match muaggatt data type

        # I don't remember why I did this
        if dSDV["attributetype"].lower() == "interpretation" and (bFuzzy == True or dSDV["effectivelogicaldatatype"].lower() == "float"):
            # For NCCPI?
            dFieldInfo["INTERPHRC"] = ["REAL", ""]

        else:
            dFieldInfo["INTERPHRC"] = ["TEXT", 254]

        dFieldInfo["MONTH"] = ["TEXT", 10]
        dFieldInfo["MONTHSEQ"] = ["TEXT", ""]
        dFieldInfo["COMONTHKEY"] = ["TEXT", 30]


        # PrintMsg("dFieldInfo: " + str(dFieldInfo), 1)

        # Get possible result domain values from mdstattabcols and mdstatdomdet tables
        # There is a problem because the XML for the legend does not always match case
        # Create a dictionary as backup, but uppercase and use that to store the original values
        #
        # Assume that data types of string and vtext do not have domains

        #PrintMsg("Creating global variables for domainValues and domainValuesUp", 1)
        global domainValues, domainValuesUp

        if not dSDV["attributelogicaldatatype"].lower() in ["string", "vtext"]:
            domainValues = GetRatingDomain(ds)
            #PrintMsg( "\ndomainValues: " + str(domainValues), 1)
            domainValuesUp = [x.upper() for x in domainValues]    # Is this variable being used?

        else:
            domainValues = list()
            domainValuesUp = list()

        # Identify related tables using mdstatrshipdet and add to tblList
        #
        mdTable = os.path.join(gdb, "mdstatrshipdet")
        mdFlds = ["LTABPHYNAME", "RTABPHYNAME", "LTABCOLPHYNAME", "RTABCOLPHYNAME"]
        level = 0  # table depth
        tblList = list()

        # Make sure mdstatrshipdet table is populated.
        if int(arcpy.GetCount_management(mdTable).getOutput(0)) == 0:
            err = "Required table (" + mdTable + ") is not populated"
            raise MyError(err)

        if dSDV["horzlevelattribflag"] == 1:
            tf = "HZDEPT_R"
            bf = "HZDEPB_R"

            if (bot - top) == 1:
                # single slice
                hzQuery = "((" + tf + " = " + str(top) + " or " + bf + " = " + str(bot) + ") or ( " + tf + " <= " + str(top) + " and " + bf + " >= " + str(bot) + " ) )"

            else:
                # depth range
                hzQuery = "((" + tf + " >= " + str(top) + " AND  " + bf + " < " + str(bot) + ") OR ( " + tf + " <= " + str(top) + " AND " + bf + " >= " + str(bot) + " ) )"

            #PrintMsg("hzQuery: " + hzQuery, 1)


        legendKeys = list(dAreasymbols.keys())

        if len(legendKeys) > 0 and (fcCnt > polyCnt):
            # Only create a filter on areasymbol if there is a selected set on the input layer
            if len(legendKeys) == 1:
                legendQuery = "lkey = '" + legendKeys[0] + "'"

            else:
                legendQuery = "lkey IN ('" + "','".join(legendKeys) + "')"

        else:
            legendQuery = "1 = 1"

        # Warning. I need to make sure there are no TableViews for SSURGO tables that might cause problems.
        # I removed the old mapping functions for this
        #
        rtabphyname = "XXXXX"
        mdSQL = "RTABPHYNAME = '" + dSDV["attributetablename"].lower() + "'"  # initial whereclause for mdstatrshipdet

        # Setup initial queries
        level = 0

        while rtabphyname.upper() != "MAPUNIT":
            # This clause will still run through MAPUNIT table, one time
            level += 1

            with arcpy.da.SearchCursor(mdTable, mdFlds, where_clause=mdSQL) as cur:
                # This should only select one record
                cntr = 0

                for rec in cur:
                    cntr += 1

                    if cntr == 1:
                        ltabphyname = rec[0].upper()
                        rtabphyname = rec[1].upper()
                        ltabcolphyname = rec[2].upper()
                        rtabcolphyname = rec[3].upper()
                        mdSQL = "RTABPHYNAME = '" + ltabphyname.lower() + "'"

                        if bVerbose:
                            PrintMsg("\tGetting level " + str(level) + " information for " + rtabphyname.upper(), 1)

                        if not rtabphyname in tblList:
                            tblList.append(rtabphyname) # save list of tables involved

                        if rtabphyname.upper() == dSDV["attributetablename"].upper():
                            #
                            # This is the table that contains the rating values
                            #
                            # check for primary and secondary restraints
                            # and use a query to apply them if found.

                            # Begin setting up SQL statement for initial filter
                            # This may be changed further down
                            #
                            primSQL = None

                            #if dSDV["attributelogicaldatatype"].lower() in ['integer', 'float']:
                                #

                            if not dSDV["sqlwhereclause"] is None:
                                primSQL = dSDV["sqlwhereclause"]

                            else:
                                primSQL = None

                            #PrintMsg("\tTesting primSQL: " + str(primSQL), 1)

                            if not primaryconcolname is None:
                                # has primary constraint, get primary constraint value
                                if primSQL is None:
                                    primSQL = primaryconcolname + " = '" + primCst + "'"

                                else:
                                    primSQL = primSQL + " and " + primaryconcolname + " = '" + primCst + "'"

                                if not secondaryconcolname is None:
                                    # has primary constraint, get primary constraint value
                                    secSQL = secondaryconcolname + " = '" + secCst + "'"
                                    primSQL = primSQL + " and " + secSQL
                                    #PrintMsg("primSQL = " + primSQL, 0)

                            if dSDV["attributetablename"].upper() == "MAPUNIT":
                                primSQL = legendQuery

                            elif dSDV["attributetablename"].upper() == "COINTERP":

                                # New code using rulekey and distinterpmd table
                                distinterpTbl = os.path.join(gdb, "distinterpmd")
                                ruleKey = GetRuleKey(distinterpTbl, dSDV["nasisrulename"])

                                if ruleKey == None:
                                    err = "Interp query failed to return key values for " + dSDV["nasisrulename"]
                                    raise MyError(err)

                                # Time for CONUS using different indexes and queries
                                # ruledepth and mrulename 9:53 min
                                # rulekey 4:09 min
                                # ruledepth and mrulekey: 4:03 min
                                #
                                #interpSQL = "MRULENAME like '%" + dSDV["nasisrulename"] + "' and RULEDEPTH = 0"  # 9:53
                                #interpSQL = "RULEDEPTH = 0 AND MRULEKEY = '" + ruleKey + "'"                      # 4:09
                                interpSQL = "RULEKEY IN " + ruleKey                                        # 4:03

                                if primSQL is None:
                                    primSQL = interpSQL
                                    #primSQL = "MRULENAME like '%" + dSDV["nasisrulename"] + "' and RULEDEPTH = 0"

                                else:
                                    #primSQL = primSQL + " and MRULENAME like '%" + dSDV["nasisrulename"] + "' and RULEDEPTH = 0"
                                    primSQL = interpSQL + " AND " + primSQL

                                # Try populating the cokeyList variable here and use it later in ReadTable
                                cokeyList = list()

                            elif dSDV["attributetablename"].upper() == "CHORIZON":
                                if primSQL is None:
                                    primSQL = hzQuery

                                else:
                                    primSQL = primSQL + " and " + hzQuery

                            elif dSDV["attributetablename"].upper() == "CHUNIFIED":
                                if not primSQL is None:
                                    primSQL = primSQL + " and RVINDICATOR = 'Yes'"

                                else:
                                    primSQL = "RVINDICATOR = 'Yes'"

                            elif dSDV["attributetablename"].upper() == "COMONTH":
                                if primSQL is None:
                                    if begMo == endMo:
                                        # query for single month
                                        primSQL = "(MONTHSEQ = " + str(moList.index(begMo)) + ")"

                                    else:
                                        primSQL = "(MONTHSEQ IN " + str(tuple(range(moList.index(begMo), (moList.index(endMo) + 1 )))) + ")"

                                else:
                                    if begMo == endMo:
                                        # query for single month
                                        primSQL = primSQL + " AND (MONTHSEQ = " + str(moList.index(begMo)) + ")"

                                    else:
                                        primSQL = primSQL + " AND (MONTHSEQ IN " + str(tuple(range(moList.index(begMo), (moList.index(endMo) + 1 )))) + ")"

                            elif dSDV["attributetablename"].upper() == "COSOILMOIST":
                                # Having problems with NULL values for some months. Need to retain NULL values with query,
                                # but then substitute 201cm in ReadTable
                                #
                                primSQL = dSDV["sqlwhereclause"]


                            if primSQL is None:
                                primSQL = ""

                            if bVerbose:
                                PrintMsg("\tRating table (" + rtabphyname.upper() + ") SQL: " + primSQL, 1)

                            # Create list of necessary fields

                            # Get field list for mapunit or component or chorizon
                            if rtabphyname in big3Tbls:
                                flds = dFields[rtabphyname]
                                if not dSDV["attributecolumnname"].upper() in flds:
                                    flds.append(dSDV["attributecolumnname"].upper())

                                dFields[rtabphyname] = flds
                                dMissing[rtabphyname] = [None] * (len(dFields[rtabphyname]) - 1)

                            else:
                                # Not one of the big 3 tables, just use foreign key and sdvattribute column
                                flds = [rtabcolphyname, dSDV["attributecolumnname"].upper()]
                                dFields[rtabphyname] = flds

                                if not rtabphyname in dMissing:
                                    dMissing[rtabphyname] = [None] * (len(dFields[rtabphyname]) - 1)
                                    #PrintMsg("\nSetting missing fields for " + rtabphyname + " to " + str(dMissing[rtabphyname]), 1)

                            try:
                                sql = dSQL[rtabphyname]

                            except:
                                # For tables other than the primary ones.
                                sql = (None, None)

                            if rtabphyname == "MAPUNIT":
                                # Not sure when I would hit this situation. Need to find out.
                                PrintMsg("" + sdvAtt + " aggregation method set to: " + aggMethod, 1)

                                if aggMethod == "No Aggregation Necessary":
                                    dMapunit = ReadTable(ds, rtabphyname, flds, legendQuery, sql)

                                else:
                                    #
                                    PrintMsg("How to handle MAPUNIT table properly with this aggregation method \n", 1)
                                    dMapunit = ReadTable(ds, rtabphyname, flds, legendQuery, sql)

                                if len(dMapunit) == 0:
                                    err = "Length of dMapunit is zero"
                                    raise MyError(err)

                            elif rtabphyname == "MUTEXT" and aggMethod == "No Aggregation Necessary":
                                # No aggregation necessary?
                                #dMapunit = ReadTable(rtabphyname, flds, primSQL, level, sql)
                                primSQL = dSDV["sqlwhereclause"]
                                dTbl = ReadTable(ds, rtabphyname, flds, primSQL, sql)

                            elif rtabphyname == "COMPONENT":
                                #if cutOff is not None:
                                if dSDV["sqlwhereclause"] is not None:
                                    if cutOff == 0:
                                        # Having problems with CONUS database. Including COMPPCT_R in the
                                        # where_clause is returning zero records. Found while testing Hydric map. Is a Bug?
                                        # Work around is to put COMPPCT_R part of query last in the string

                                        primSQL =  dSDV["sqlwhereclause"] + " AND COMPNAME <> 'NOTCOM'"
                                        primSQL = dSDV["sqlwhereclause"] + " AND COMPPCT_R >= 1 AND COMPNAME <> 'NOTCOM'"

                                    else:
                                        primSQL = dSDV["sqlwhereclause"] + " AND COMPPCT_R >= " + str(cutOff)  + " AND COMPNAME <> 'NOTCOM'"

                                else:
                                    # Should I use bNull flag here?/
                                    #
                                    #
                                    #
                                    #
                                    #
                                    #
                                    primSQL = "COMPNAME <> 'NOTCOM'"


                                #PrintMsg("Populating dictionary from component table", 1)

                                dComponent = ReadTable(ds, rtabphyname, flds, primSQL, sql)

                                if len(dComponent) == 0:
                                    err = "No component data for " + sdvAtt
                                    raise MyError(err)

                            elif rtabphyname == "CHORIZON":
                                #primSQL = "(CHORIZON.HZDEPT_R between " + str(top) + " and " + str(bot) + " or CHORIZON.HZDEPB_R between " + str(top) + " and " + str(bot + 1) + ")"
                                #PrintMsg("CHORIZON hzQuery: " + hzQuery, 1)
                                dHorizon = ReadTable(ds, rtabphyname, flds, hzQuery, sql)

                                if len(dHorizon) == 0:
                                    err = "No horizon data for " + sdvAtt
                                    raise MyError(err)

                            else:
                                # This should be the bottom-level table containing the requested data
                                #
                                cokeyList = list()  # Try using this to pare down the COINTERP table record count
                                #cokeyList = dComponent.keys()  # Won't work. dComponent isn't populated yet

                                PrintMsg("Reading " + dSDV["attributetablename"] + " table, using " + ", ".join(flds), 1)
                                PrintMsg("Using primSQL: " + str(primSQL) + ";  " + " sql: " + str(sql), 1)

                                dTbl = ReadTable(ds, dSDV["attributetablename"].upper(), flds, primSQL, sql)

                                if len(dTbl) == 0:
                                    err = "No " + dSDV["attributetablename"] + " data for " + sdvAtt
                                    raise MyError(err)

                        else:
                            # Bottom section
                            #
                            # This is one of the intermediate tables
                            # Create list of necessary fields
                            # Get field list for mapunit or component or chorizon
                            #
                            flds = dFields[rtabphyname]
                            try:
                                sql = dSQL[rtabphyname]

                            except:
                                # This needs to be fixed. I have a whereclause in the try and an sqlclause in the except.
                                sql = (None, None)

                            #PrintMsg("primSQL was set to: " + primSQL, 1)
                            primSQL = ""
                            #PrintMsg("\tReading intermediate table: " + rtabphyname + "   sql: " + str(sql), 1)

                            if rtabphyname == "MAPUNIT":
                                PrintMsg("Reading the mapunit table using legendQuery: " + legendQuery, 1)
                                #dMapunit = ReadTable(rtabphyname, flds, primSQL, level, sql)
                                dMapunit = ReadTable(ds, rtabphyname, flds, legendQuery, sql)

                                if len(dMapunit) == 0:
                                    err = "Length of dMapunit is zero"
                                    raise MyError(err)

                            elif rtabphyname == "COMPONENT":
                                primSQL = "COMPPCT_R >= " + str(cutOff)

                                #PrintMsg("Populating dictionary from component table", 1)

                                dComponent = ReadTable(ds, rtabphyname, flds, primSQL, sql)

                                if len(dComponent) == 0:
                                    err = "Length of dComponent is zero"
                                    raise MyError(err)

                            elif rtabphyname == "CHORIZON":
                                #primSQL = "(CHORIZON.HZDEPT_R between " + str(top) + " and " + str(bot) + " or CHORIZON.HZDEPB_R between " + str(top) + " and " + str(bot + 1) + ")"
                                tf = "HZDEPT_R"
                                bf = "HZDEPB_R"
                                #primSQL = "( ( " + tf + " between " + str(top) + " and " + str(bot - 1) + " or " + bf + " between " + str(top) + " and " + str(bot) + " ) or " + \
                                #"( " + tf + " <= " + str(top) + " and " + bf + " >= " + str(bot) + " ) )"
                                if (bot - top) == 1:
                                    #rng = str(tuple(range(top, (bot + 1))))
                                    hzQuery = "((" + tf + " = " + str(top) + " or " + bf + " = " + str(bot) + ") or ( " + tf + " <= " + str(top) + " and " + bf + " >= " + str(bot) + " ) )"

                                else:
                                    rng = str(tuple(range(top, bot)))
                                    hzQuery = "((" + tf + " in " + rng + " or " + bf + " in " + rng + ") or ( " + tf + " <= " + str(top) + " and " + bf + " >= " + str(bot) + " ) )"

                                #PrintMsg("Setting primSQL for when rtabphyname = 'CHORIZON' to: " + hzQuery, 1)
                                dHorizon = ReadTable(ds, rtabphyname, flds, hzQuery, sql)

                                if len(dHorizon) == 0:
                                    err = "Length of dHorizon is zero"
                                    raise MyError(err)

                            elif rtabphyname == "COMONTH":

                                # Need to look at the SQL for the other tables as well...
                                if begMo == endMo:
                                    # query for single month
                                    primSQL = "(MONTHSEQ = " + str(moList.index(begMo)) + ")"

                                else:
                                    primSQL = "(MONTHSEQ IN " + str(tuple(range(moList.index(begMo), (moList.index(endMo) + 1 )))) + ")"

                                #PrintMsg("Intermediate SQL: " + primSQL, 1)
                                dMonth = ReadTable(ds, rtabphyname, flds, primSQL, sql)

                                if len(dMonth) == 0:
                                    err = "No comonth data for " + sdvAtt + " \n "
                                    raise MyError(err)

                            else:
                                PrintMsg("\tUnable to read data from: " + rtabphyname, 1)


            if level > 6:
                err = "Failed to get table relationships"
                raise MyError(err)


        # Create a list of all fields needed for the initial output table. This
        # one will include primary keys that won't be in the final output table.
        #
        if len(tblList) == 0:
            # No Aggregation Necessary, append field to mapunit list
            tblList = ["MAPUNIT"]

            if dSDV["attributecolumnname"].upper() in dFields["MAPUNIT"]:
                PrintMsg("Skipping addition of field "  + dSDV["attributecolumnname"].upper(), 1)

            else:
                dFields["MAPUNIT"].append(dSDV["attributecolumnname"].upper())

        tblList.reverse()  # Set order of the tables so that mapunit is on top

        if bVerbose:
            PrintMsg("Using these tables: " + ", ".join(tblList), 1)

        # Create a list of all fields to be used in the flat SDV_Data table
        global allFields
        allFields = ["AREASYMBOL"]

        # Substitute resultcolumnname for last field in allFields
        for tbl in tblList:
            tFields = dFields[tbl]

            for fld in tFields:
                if not fld.upper() in allFields:
                    # PrintMsg("\tAdding field: " + fld.upper() + " to allFields", 1)
                    allFields.append(fld.upper())

        # PrintMsg("allFields 2: " + ", ".join(allFields), 1)

        if not dSDV["attributecolumnname"].upper() in allFields:
            #PrintMsg("\tAdding attribute columnname (" + dSDV["attributecolumnname"].upper() + " to allFields", 1)
            allFields.append(dSDV["attributecolumnname"].upper())


        PrintMsg(".    AllFields: " + ", ".join(allFields), 0)

        # Create initial output table (one-to-many)
        # Now created with resultcolumnname, but without LKEY.
        #
        # PrintMsg(".", 1)
        # PrintMsg("Calling CreateInitialTable", 1)
        # PrintMsg("Using allFields: " + ", ".join(allFields), 1)
        #flatTbl = CreateInitialTable(outputDriver, tmpDS, allFields, dFieldInfo)

        # Instead of SQLite table, try creating a pandas dataframe
        dataTypes = CreateInitialTable(outputDriver, tmpDS, allFields, dFieldInfo)

        if dataTypes is None:
            raise MyError("")

##        if flatTbl is None:
##            err = "Failed to create initial query table"
##            raise MyError(err)

        if tblList == ['MAPUNIT']:
            # No aggregation needed
            dfRaw = CreateRatingTable1(ds, tblList, dSDV["attributetablename"].upper(), dataTypes, allFields, dAreasymbols)
            #if CreateRatingTable1(ds, tblList, dSDV["attributetablename"].upper(), dfInitial, allFields, dAreasymbols) == False:
            #if CreateRatingTable1(ds, tblList, dSDV["attributetablename"].upper(), flatTbl, allFields, dAreasymbols) == False:

            if dfRaw is None:
                err = "CreateRatingTable failed using " + ", ".join(tblList)
                raise MyError(err)

        elif tblList == ['MAPUNIT', 'COMPONENT']:
            if CreateRatingTable2(ds, dSDV["attributetablename"].upper(), dComponent, flatTbl, dAreasymbols) == False:
                err = "CreateRatingTable failed using " + ", ".join(tblList)
                raise MyError(err)
            del dComponent

        elif tblList == ['MAPUNIT', 'COMPONENT', 'CHORIZON']:
            #                     ds, sdvTbl, dComponent, dHorizon, dTbl, flatTbl, dAreasymbols
            if CreateRatingTable3(ds, dComponent, dHorizon, flatTbl, dAreasymbols) == False:
                err = "CreateRatingTable failed using " + ", ".join(tblList)
                PrintMsg(err, 1)
                raise MyError(err)
            del dComponent, dHorizon

        elif tblList == ['MAPUNIT', 'COMPONENT', 'CHORIZON', dSDV["attributetablename"].upper()]:
            # COMPONENT, CHORIZON, CHTEXTUREGRP
            if CreateRatingTable3S(ds, dSDV["attributetablename"].upper(), dComponent, dHorizon, dTbl, flatTbl, dAreasymbols) == False:
                err = "CreateRatingTable failed using " + ", ".join(tblList)
                raise MyError(err)

            del dComponent, dHorizon

        elif tblList in [['MAPUNIT', "MUAGGATT"], ['MAPUNIT', "MUCROPYLD"], ['MAPUNIT', 'MUTEXT']]:
            if CreateRatingTable1S(ds, tblList, dSDV["attributetablename"].upper(), dTbl, flatTbl, allFields, dAreasymbols) == False:
                err = "CreateRatingTable failed using " + ", ".join(tblList)
                raise MyError(err)

            else:
                # pause so I can read status
                time.sleep(5)
                ds.Destroy()
                del ds
                raise MyError("EARLY OUT AFTER CreateRatingTable1S")


        elif tblList == ['MAPUNIT', 'COMPONENT', dSDV["attributetablename"].upper()]:
            if dSDV["attributetablename"].upper() == "COINTERP":
                if CreateRatingInterps(ds, dSDV["attributetablename"].upper(), dComponent, dTbl, flatTbl, dAreasymbols) == False:
                    #
                    err = "CreateRatingTable failed using " + ", ".join(tblList)
                    raise MyError(err)
                del dComponent

            else:
                if CreateRatingTable2S(ds, dSDV["attributetablename"].upper(), dComponent, dTbl, flatTbl, dAreasymbols) == False:
                    err = "xxx CreateRatingTable failed"
                    raise MyError(err)

        elif tblList == ['MAPUNIT', 'COMPONENT', 'COMONTH', 'COSOILMOIST']:
            if dSDV["attributetablename"].upper() == "COSOILMOIST":

                #PrintMsg("dMissing values before CreateSoilMoistureTable: " + str(dMissing))

                if CreateSoilMoistureTable(ds, dSDV["attributetablename"].upper(), dComponent, dMonth, dTbl, flatTbl, begMo, endMo, dAreasymbols) == False:
                    #                      ds, sdvTbl, dComponent, dMonth, dTbl, flatTbl, begMo, endMo, dAreasymbols
                    err = "CreateRatingTable failed using " + ", ".join(tblList)
                    raise MyError(err)
                del dMonth, dComponent # trying to lower memory usage

            else:
                PrintMsg("Cannot handle table:" + dSDV["attributetablename"].upper(), 1)
                err = "Tables Bad Combo: " + str(tblList)
                raise MyError(err)

        else:
            # Need to add ['COMPONENT', 'COMONTH', 'COSOILMOIST']
            err = "Problem with list of input tables: " + str(tblList)
            raise MyError(err)

        # **************************************************************************
        # Look at attribflags and apply the appropriate aggregation function
##
##        if not arcpy.Exists(flatTbl):
##            # Output table was not created. Exit program.
##            err = "Failed to create " + flatTbl + " table"
##            raise MyError(err)

##        #PrintMsg(os.path.basename(flatTbl) + " has " + arcpy.GetCount_management(flatTbl).getOutput(0) + " records", 1)
##        result = arcpy.GetCount_management(flatTbl)
##
##        if int(result.getOutput(0)) == 0:
##            ## TEST
##            err = "Failed to populate query table '" + flatTbl + "'"
##            raise MyError(err)

        # Proceed with aggregation if the intermediate table has data.
        # Add result column to fields list
        iFlds = len(allFields)
        newField = dSDV["resultcolumnname"].upper()

        #PrintMsg("allFields: " + ", ".join(allFields), 1)
        allFields[len(allFields) - 1] = newField
        rmFields = ["MUSYM", "COMPNAME", "LKEY"]

        for fld in rmFields:
            if fld in allFields:
                allFields.remove(fld)

        if newField == "MUNAME":
            allFields.remove("MUNAME")

        # Create name for final output table that will be saved to the input gSSURGO database
        #
        global tblName
        #PrintMsg("\taggMethod: '" + dAgg[aggMethod] + "'", 1)



        if dAgg[aggMethod] == "":
            # No aggregation method necessary
            tblName = "SDV_" + dSDV["resultcolumnname"]

        else:
            if secCst != "":
                # Problem with primary and secondary constraint values. These can produce
                # illegal table names
                #
                tblName = "SDV_" + dSDV["resultcolumnname"] + "_" + primCst.replace(" ", "_") + "_" + secCst.replace(" ", "_")


            elif primCst != "":
                #tblName = "SDV_" + dSDV["resultcolumnname"] + "_" + dAgg[aggMethod] + "_" + primCst.replace(" ", "_")
                tblName = "SDV_" + dSDV["resultcolumnname"] + "_" + primCst.replace(" ", "_")

            elif dSDV["horzlevelattribflag"]:
                #tblName = "SDV_" + dSDV["resultcolumnname"] + "_" + dAgg[aggMethod] + "_" + str(top) + "to" + str(bot)
                tblName = "SDV_" + dSDV["resultcolumnname"] + "_" + str(top) + "to" + str(bot)

            else:
                #tblName = "SDV_" + dSDV["resultcolumnname"]+ "_" + dAgg[aggMethod]
                tblName = "SDV_" + dSDV["resultcolumnname"]


        # Need to replace this arcpy function
        #
        # tblName = arcpy.ValidateTableName(tblName, gdb)

        # Cleanup any duplicate underscores in the table name
        newName = ""
        lastChar = "_"

        for c in tblName:
            if c == lastChar and c == "_":
                # Don't use this character because it is another underscore
                lastChar = c

            else:
                newName += c
                lastChar = c

        if newName[-1] == "_":
            newName = newName[:-1]

        tblName = newName

        #PrintMsg("Output table name = " + tblName, 1)

        # **************************************************************************
        #
        # Aggregation Logic to determine which functions will be used to process the
        # intermediate table and produce the final output table.
        #
        # This is where outputValues is set
        #
        if dSDV["attributetype"].lower() == "property":
            # These are all Soil Properties
            # Added addtional logic for Minnesota Crop Index. It has a problem in that mapunitlevelattribflag is set to zero.

            if dSDV["mapunitlevelattribflag"] == 1 or \
               (dSDV["mapunitlevelattribflag"] == 0 and dSDV["complevelattribflag"] == 0 \
                and dSDV["cmonthlevelattribflag"] == 0 and dSDV["horzlevelattribflag"] == 0 ) :
                # This is a Map unit Level Soil Property or it is Minnesota Crop Index in the MUTEXT table
                #PrintMsg("Map unit level, no aggregation neccessary", 1)
                # outputJSON, outputValues = Aggregate1(tmpDS, sdvAtt, dSDV["attributecolumnname"].upper(), flatTbl, bZero, cutOff, tieBreaker)
                outputJSON, outputValues = Aggregate1(tmpDS, sdvAtt, dSDV["attributecolumnname"].upper(), dfRaw, dataTypes, bZero, cutOff, tieBreaker)

                raise MyError("EARLY OUT AFTER outputJSON")

            elif dSDV["complevelattribflag"] == 1:

                if dSDV["horzlevelattribflag"] == 0:
                    # These are Component Level-Only Soil Properties

                    if dSDV["cmonthlevelattribflag"] == 0:
                        #
                        #  These are Component Level Soil Properties

                        if aggMethod == "Dominant Component":
                            #PrintMsg("1. domainValues: " + ", ".join(domainValues), 1)
                            outputTbl, outputValues = AggregateCo_DCP(gdb, sdvAtt, dSDV["attributecolumnname"].upper(), flatTbl, bZero, cutOff, tieBreaker)

                        elif aggMethod == "Minimum or Maximum":
                            outputTbl, outputValues = AggregateCo_MaxMin(gdb, sdvAtt, dSDV["attributecolumnname"].upper(), flatTbl, bZero, cutOff, tieBreaker)

                        elif aggMethod == "Dominant Condition":
                            if bVerbose:
                                PrintMsg("Domain Values are now: " + str(domainValues), 1)

                            if len(domainValues) > 0 and dSDV["tiebreakdomainname"] is not None :  # Problem with NonIrr CapSubCls
                                if bVerbose:
                                    PrintMsg("1. aggMethod = " + aggMethod + " and domainValues = " + str(domainValues), 1)

                                outputTbl, outputValues = AggregateCo_DCD_Domain(gdb, sdvAtt, dSDV["attributecolumnname"].upper(), flatTbl, bZero, cutOff, tieBreaker)

                                if bVerbose:
                                    PrintMsg("OuputValues: " + str(outputValues), 1)

                            else:
                                if bVerbose:
                                    PrintMsg("2. aggMethod = " + aggMethod + " and no domainValues", 1)

                                outputTbl, outputValues = AggregateCo_DCD(gdb, sdvAtt, dSDV["attributecolumnname"].upper(), flatTbl, bZero, cutOff, tieBreaker)

                        elif aggMethod == "Minimum or Maximum":
                            #
                            outputTbl, outputValues = AggregateCo_MaxMin(gdb, sdvAtt, dSDV["attributecolumnname"].upper(), flatTbl, bZero, cutOff, tieBreaker)

                        elif aggMethod == "Weighted Average" and dSDV["attributetype"].lower() == "property":
                            # Using NCCPI for any numeric component level value?
                            # This doesn't seem to be working for Range Prod 2016-01-28
                            #
                            outputTbl, outputValues = AggregateCo_WTA(gdb, sdvAtt, dSDV["attributecolumnname"].upper(),  flatTbl, bZero, cutOff, tieBreaker)

                        elif aggMethod == "Percent Present":
                            # This is Hydric?
                            outputTbl, outputValues = AggregateCo_PP_SUM(gdb, sdvAtt, dSDV["attributecolumnname"].upper(), flatTbl, bZero, cutOff, tieBreaker)

                        else:
                            # Don't know what kind of interp this is
                            err = "5. Component aggregation method has not yet been developed ruledesign 3 (" + dSDV["algorithmname"] + ", " + dSDV["horzaggmeth"] + ")"
                            raise MyError(err)


                    elif dSDV["cmonthlevelattribflag"] == 1:
                        #
                        # These are Component-Month Level Soil Properties
                        #
                        if dSDV["resultcolumnname"].startswith("Dep2WatTbl"):
                            #PrintMsg("This is Depth to Water Table (" + dSDV["resultcolumnname"] + ")", 1)

                            if aggMethod == "Dominant Component":
                                outputTbl, outputValues = AggregateCo_DCP_DTWT(gdb, sdvAtt, dSDV["attributecolumnname"].upper(), flatTbl, bZero, cutOff, tieBreaker)

                            elif aggMethod == "Dominant Condition":
                                outputTbl, outputValues = AggregateCo_Mo_DCD(gdb, sdvAtt, dSDV["attributecolumnname"].upper(), flatTbl, bZero, cutOff, tieBreaker)

                            elif aggMethod == "Weighted Average":
                                outputTbl, outputValues = AggregateCo_WTA_DTWT(gdb, sdvAtt, dSDV["attributecolumnname"].upper(), flatTbl, bZero, cutOff, tieBreaker)

                            else:
                                # Component-Month such as depth to water table - Minimum or Maximum
                                outputTbl, outputValues = AggregateCo_Mo_MaxMin(gdb, sdvAtt, dSDV["attributecolumnname"].upper(), flatTbl, bZero, cutOff, tieBreaker)

                        else:
                            # This will be flooding or ponding frequency. In theory these should be the same value
                            # for each month because these are normally annual ratings
                            #
                            # PrintMsg("This is Flooding or Ponding (" + dSDV["resultcolumnname"] + ")", 1 )
                            #
                            if aggMethod == "Dominant Component":
                                # Problem with this aggregation method (AggregateCo_DCP). The CompPct sum is 12X because of the months.
                                outputTbl, outputValues = AggregateCo_Mo_DCP_Domain(gdb, sdvAtt, dSDV["attributecolumnname"].upper(), flatTbl, bZero, cutOff, tieBreaker)

                            elif aggMethod == "Dominant Condition":
                                # Problem with this aggregation method (AggregateCo_DCP_Domain). The CompPct sum is 12X because of the months.
                                outputTbl, outputValues = AggregateCo_Mo_DCD_Domain(gdb, sdvAtt, dSDV["attributecolumnname"].upper(), flatTbl, bZero, cutOff, tieBreaker) # Orig
                                #PrintMsg("outputValues: " + ", ".join(outputValues), 1)

                            elif aggMethod == "Minimum or Maximum":
                                outputTbl, outputValues = AggregateCo_Mo_MaxMin(gdb, sdvAtt, dSDV["attributecolumnname"].upper(), flatTbl, bZero, cutOff, tieBreaker)

                            elif aggMethod == "Weighted Average":
                              outputTbl, outputValues = AggregateCo_Mo_WTA(gdb, sdvAtt, dSDV["attributecolumnname"].upper(), flatTbl, bZero, cutOff, tieBreaker)

                            else:
                                err = "Aggregation method: " + aggMethod + "; attibute " + dSDV["attributecolumnname"].upper()
                                raise MyError(err)

                    else:
                        err = "Attribute level flag problem"
                        raise MyError(err)

                elif dSDV["horzlevelattribflag"] == 1:
                    # These are all Horizon Level Soil Properties

                    if sdvAtt.startswith("K Factor"):
                        # Need to figure out aggregation method for horizon level  max-min
                        if aggMethod == "Dominant Condition":
                            outputTbl, outputValues = AggregateHz_MaxMin_DCD(gdb, sdvAtt, dSDV["attributecolumnname"].upper(),  flatTbl, bZero, cutOff, tieBreaker, top, bot)

                        elif aggMethod == "Dominant Component":
                            outputTbl, outputValues = AggregateHz_MaxMin_DCP(gdb, sdvAtt, dSDV["attributecolumnname"].upper(),  flatTbl, bZero, cutOff, tieBreaker, top, bot)

                    elif aggMethod == "Weighted Average":
                        # component aggregation is weighted average
                        #PrintMsg("Here in hzaggregation for weighted average", 1)

                        if dSDV["attributelogicaldatatype"].lower() in ["integer", "float"]:
                            # Just making sure that these are numeric values, not indexes
                            if dSDV["horzaggmeth"] == "Weighted Average":
                                # Use weighted average for horizon data (works for AWC)
                                outputTbl, outputValues = AggregateHz_WTA_WTA(gdb, sdvAtt, dSDV["attributecolumnname"].upper(), flatTbl, bZero, cutOff, tieBreaker, top, bot)

                            elif dSDV["horzaggmeth"] == "Weighted Sum":
                                # Calculate sum for horizon data (egs. AWS)
                                outputTbl, outputValues = AggregateHz_WTA_SUM(gdb, sdvAtt, dSDV["attributecolumnname"].upper(), flatTbl, bZero, cutOff, tieBreaker, top, bot)

                        else:
                            err = "12. Weighted Average not appropriate for " + dataType
                            raise MyError(err)

                    elif aggMethod == "Dominant Component":
                        # Need to find or build this function

                        if sdvAtt.startswith("Surface") or sdvAtt.endswith("(Surface)"):
                            #
                            outputTbl, outputValues = AggregateCo_DCP(gdb, sdvAtt, dSDV["attributecolumnname"].upper(), flatTbl, bZero, cutOff, tieBreaker)

                        elif dSDV["effectivelogicaldatatype"].lower() == "choice":
                            # Indexed value such as kFactor, cannot use weighted average
                            # for horizon properties.
                            outputTbl, outputValues = AggregateCo_DCP(gdb, sdvAtt,dSDV["attributecolumnname"].upper(), flatTbl, bZero, cutOff, tieBreaker)

                        elif dSDV["horzaggmeth"] == "Weighted Average":
                            #PrintMsg("Horizon aggregation method = WTA and attributelogical datatype = " + dSDV["attributelogicaldatatype"].lower(), 1)
                            outputTbl, outputValues = AggregateHz_DCP_WTA(gdb, sdvAtt, dSDV["attributecolumnname"].upper(), flatTbl, bZero, cutOff, tieBreaker, top, bot)

                        else:
                            err = "9. Aggregation method has not yet been developed (" + dSDV["algorithmname"] + ", " + dSDV["horzaggmeth"] + ")"
                            raise MyError(err)

                    elif aggMethod == "Dominant Condition":

                        if sdvAtt.startswith("Surface") or sdvAtt.endswith("(Surface)"):
                            if dSDV["effectivelogicaldatatype"].lower() == "choice":
                                if bVerbose:
                                    PrintMsg("Dominant condition for surface-level attribute", 1)
                                outputTbl, outputValues = AggregateCo_DCD_Domain(gdb, sdvAtt, dSDV["attributecolumnname"].upper(), flatTbl, bZero, cutOff, tieBreaker)

                            else:
                                outputTbl, outputValues = AggregateCo_DCD(gdb, sdvAtt, dSDV["attributecolumnname"].upper(), flatTbl, bZero, cutOff, tieBreaker)


                        elif dSDV["effectivelogicaldatatype"].lower() in ("float", "integer"):
                            # Dominant condition for a horizon level numeric value is probably not a good idea
                            outputTbl, outputValues = AggregateCo_DCD(gdb, sdvAtt, dSDV["attributecolumnname"].upper(), flatTbl, bZero, cutOff, tieBreaker)

                        elif dSDV["effectivelogicaldatatype"].lower() == "choice" and dSDV["tiebreakdomainname"] is not None:
                            # KFactor (Indexed values)
                            #PrintMsg("Dominant condition for choice type", 1)
                            outputTbl, outputValues = AggregateCo_DCD_Domain(gdb, sdvAtt, dSDV["attributecolumnname"].upper(), flatTbl, bZero, cutOff, tieBreaker)

                        else:
                            err = "No aggregation calculation selected for DCD"
                            raise MyError(err)

                    elif aggMethod == "Minimum or Maximum":
                        # Need to figure out aggregation method for horizon level  max-min
                        if dSDV["effectivelogicaldatatype"].lower() == "choice":
                            # PrintMsg("\tRunning AggregateCo_MaxMin for " + sdvAtt, 1)
                            outputTbl, outputValues = AggregateCo_MaxMin(gdb, sdvAtt, dSDV["attributecolumnname"].upper(),  flatTbl, bZero, cutOff, tieBreaker)

                        else:  # These should be numeric, probably need to test here.
                            outputTbl, outputValues = AggregateHz_MaxMin_WTA(gdb, sdvAtt, dSDV["attributecolumnname"].upper(), flatTbl, bZero, cutOff, tieBreaker, top, bot)

                    else:
                        err = "'" + aggMethod + "' aggregation method for " + sdvAtt + " has not been developed"
                        raise MyError(err)

                else:
                    err = "Horizon-level '" + aggMethod + "' aggregation method for " + sdvAtt + " has not been developed"
                    raise MyError(err)

            else:
                # Should never hit this
                err = "Unable to handle assigned aggregation method (" + aggMethod + ") for " + sdvAtt
                raise MyError(err)

        elif dSDV["attributetype"].lower() == "interpretation":

            if dSDV["ruledesign"] == 1:
                #
                # This is a Soil Interpretation for Limitations or Risk

                if aggMethod == "Dominant Component":
                    outputTbl, outputValues = AggregateCo_DCP(gdb, sdvAtt, dSDV["attributecolumnname"].upper(), flatTbl, bZero, cutOff, tieBreaker)

                elif aggMethod == "Dominant Condition":
                    #PrintMsg("Interpretation; aggMethod = " + aggMethod, 1)
                    outputTbl, outputValues = AggregateCo_DCD_Domain(gdb, sdvAtt, dSDV["attributecolumnname"].upper(), flatTbl, bZero, cutOff, tieBreaker)

                elif aggMethod in ['Least Limiting', 'Most Limiting']:
                    outputTbl, outputValues = AggregateCo_Limiting(gdb, sdvAtt, dSDV["attributecolumnname"].upper(), flatTbl, bZero, cutOff, tieBreaker)

                elif aggMethod == "Weighted Average":
                    # This is an interp that has been set to use fuzzy values
                    outputTbl, outputValues = AggregateCo_WTA(gdb, sdvAtt, dSDV["attributecolumnname"].upper(), flatTbl, bZero, cutOff, tieBreaker)
                    outputValues = [0.0, 1.0]

                else:
                    # Don't know what kind of interp this is
                    #PrintMsg("mapunitlevelattribflag: " + str(dSDV["mapunitlevelattribflag"]) + ", complevelattribflag: " + str(dSDV["complevelattribflag"]) + ", cmonthlevelattribflag: " + str(dSDV["cmonthlevelattribflag"]) + ", horzlevelattribflag: " + str(dSDV["horzlevelattribflag"]) + ", effectivelogicaldatatype: " + dSDV["effectivelogicaldatatype"], 1)
                    #PrintMsg(aggMethod + "; " + dSDV["effectivelogicaldatatype"], 1)
                    err = "5. Aggregation method has not yet been developed (" + dSDV["algorithmname"] + ", " + dSDV["horzaggmeth"] + ")"
                    raise MyError(err)

            elif dSDV["ruledesign"] == 2:
                # This is a Soil Interpretation for Suitability

                if aggMethod == "Dominant Component":
                    outputTbl, outputValues = AggregateCo_DCP(gdb, sdvAtt, dSDV["attributecolumnname"].upper(), flatTbl, bZero, cutOff, tieBreaker)

                elif aggMethod == "Dominant Condition":
                    outputTbl, outputValues = AggregateCo_DCD_Domain(gdb, sdvAtt, dSDV["attributecolumnname"].upper(), flatTbl, bZero, cutOff, tieBreaker)  # changed this for Sand Suitability

                elif bFuzzy or (aggMethod == "Weighted Average" and dSDV["effectivelogicaldatatype"].lower() == 'float'):
                    # This is NCCPI
                    #PrintMsg("A Aggregate2_NCCPI", 1)
                    #outputTbl, outputValues = Aggregate2_NCCPI(gdb, sdvAtt, dSDV["attributecolumnname"].upper(), flatTbl, bZero, cutOff, tieBreaker)
                    # PrintMsg("NCCPI 3", 1)
                    outputTbl, outputValues = AggregateCo_WTA(gdb, sdvAtt, dSDV["attributecolumnname"].upper(), flatTbl, bZero, cutOff, tieBreaker)
                    outputValues = [0.0, 1.0]

                elif aggMethod in ['Least Limiting', 'Most Limiting']:
                    # Least Limiting or Most Limiting Interp
                    outputTbl, outputValues = AggregateCo_Limiting(gdb, sdvAtt, dSDV["attributecolumnname"].upper(), flatTbl, bZero, cutOff, tieBreaker)

                else:
                    # Don't know what kind of interp this is
                    # Friday problem here for NCCPI
                    #PrintMsg("" + str(dSDV["mapunitlevelattribflag"]) + ", " + str(dSDV["complevelattribflag"]) + ", " + str(dSDV["cmonthlevelattribflag"]) + ", " + str(dSDV["horzlevelattribflag"]) + " -NA2", 1)
                    #PrintMsg(aggMethod + "; " + dSDV["effectivelogicaldatatype"], 1)
                    err = "5. Aggregation method has not yet been developed (" + dSDV["algorithmname"] + ", " + dSDV["horzaggmeth"] + ")"
                    raise MyError(err)


            elif dSDV["ruledesign"] == 3:
                # This is a Soil Interpretation for Class. Only a very few interps in the nation use this.
                # Such as MO- Pasture hayland; MT-Conservation Tree Shrub Groups; CA- Revised Storie Index

                if aggMethod == "Dominant Component":
                    outputTbl, outputValues = AggregateCo_DCP(gdb, sdvAtt, dSDV["attributecolumnname"].upper(), flatTbl, bZero, cutOff, tieBreaker)

                elif aggMethod == "Dominant Condition":
                    outputTbl, outputValues = AggregateCo_DCD(gdb, sdvAtt, dSDV["attributecolumnname"].upper(), flatTbl, bZero, cutOff, tieBreaker)

                elif aggMethod in ['Least Limiting', 'Most Limiting']:
                    #PrintMsg("Not sure about aggregation method for ruledesign = 3", 1)
                    # Least Limiting or Most Limiting Interp
                    outputTbl, outputValues = AggregateCo_Limiting(gdb, sdvAtt, dSDV["attributecolumnname"].upper(), flatTbl, bZero, cutOff, tieBreaker)

                else:
                    # Don't know what kind of interp this is
                    PrintMsg("Ruledesign 3: " + str(dSDV["mapunitlevelattribflag"]) + ", " + str(dSDV["complevelattribflag"]) + ", " + str(dSDV["cmonthlevelattribflag"]) + ", " + str(dSDV["horzlevelattribflag"]) + " -NA2", 1)
                    PrintMsg(aggMethod + "; " + dSDV["effectivelogicaldatatype"], 1)
                    err = "5. Interp aggregation method has not yet been developed ruledesign 3 (" + dSDV["algorithmname"] + ", " + dSDV["horzaggmeth"] + ")"
                    raise MyError(err)


            elif dSDV["ruledesign"] is None:
                # This is a Soil Interpretation???
                err = "Soil Interp with no RuleDesign setting"
                raise MyError(err)

            else:
                err = "No aggregation calculation selected 10"
                raise MyError(err)

        else:
            err = "Invalid SDV AttributeType: " + str(dSDV["attributetype"])
            raise MyError(err)

        # quit if no data is available for selected property or interp
        if outputValues is None:
            PrintMsg("\toutputValues is 'None'", 1)
            return None, None

        if outputValues == [0.0, 0.0] or len(outputValues) == 0 or (len(outputValues) == 1 and (outputValues[0] == None or outputValues[0] == "")):

            if bot > 0 and dSDV["attributetablename"] == "chorizon":
                PrintMsg("\tNo data available for '" + sdvAtt + " " + str(top) + " to " + str(bot) + "cm'", 1)

            else:
                PrintMsg("\tNo data available for '" + sdvAtt + "'", 1)

            return None, None
            #PrintMsg("No data available for '" + sdvAtt + "'", 1)

        elif BadTable(outputTbl):
            #PrintMsg("\tBadTable check, No data available for '" + sdvAtt + "'", 1)

            if bot > 0:
                PrintMsg("\tNo data available for '" + sdvAtt + " " + str(top) + " to " + str(bot) + "cm'", 1)

            else:
                PrintMsg("\tNo data available for '" + sdvAtt + "'", 1)

            return None, None

        # Check numeric output values for max-min and number of decimal places
        #
        if dSDV["effectivelogicaldatatype"] == 'float' and len(outputValues) == 2:
            outputValues = [round(outputValues[0], dSDV["attributeprecision"]), round(outputValues[1], dSDV["attributeprecision"])]

        #
        # End of Aggregation Logic and Data Processing
        # **************************************************************************
        # **************************************************************************
        #
        PrintMsg("This is the end of aggregation", 0)

        if not arcpy.Exists(outputTbl):
            err = "Failed to create table: " + outputTbl
            raise MyError(err)

        PrintMsg("Output table with " + arcpy.GetCount_management(outputTbl).getOutput(0) + " records: " + outputTbl, 0)

        with arcpy.da.SearchCursor(outputTbl, "*") as cur:
            for rec in cur:
                PrintMsg(str(rec), 1)

        return outputTbl, outputValues

    except arcpy.ExecuteError:
        # Catch arcpy errors here
        PrintMsg("arcpy.ExecuteError encountered", 1)
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        return None, None

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

        return None, None

    finally:
        try:
            del inputDriver
            ds.Destroy()  # close input database
            tmpDS.Destroy()
            PrintMsg("Cleaned up datasets", 1)

        except:
            pass

## ===================================================================================
def create_connection(db_file):
    # Example create a database connection to a SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        #print(sqlite3.version)

    except Error as e:
        #print(e)
        pass

    finally:
        if conn:
            conn.close()

## ===================================================================================
## MAIN
## ===================================================================================

# Import system modules
import arcpy, os, sys, string, traceback, locale, operator, json, math, random, time, ogr
from arcpy import env
import pandas as pd
import numpy as np
#ogr.UseExceptions()  # not sure how this works

try:
    if __name__ == "__main__":
        inputLayer = arcpy.GetParameterAsText(0)      # Input mapunit polygon layer
        #inputDB = arcpy.GetParameterAsText(1)
        sdvFolder = arcpy.GetParameter(1)             # SDV Folder
        sdvAtt = arcpy.GetParameter(2)                # SDV Attribute
        aggMethod = arcpy.GetParameter(3)             # Aggregation method
        primCst = arcpy.GetParameter(4)               # Primary Constraint choice list
        secCst = arcpy.GetParameter(5)                # Secondary Constraint choice list
        top = arcpy.GetParameter(6)                   # top horizon depth
        bot = arcpy.GetParameter(7)                   # bottom horizon depth
        begMo = arcpy.GetParameter(8)                 # beginning month
        endMo = arcpy.GetParameter(9)                 # ending month
        tieBreaker = arcpy.GetParameter(10)           # tie-breaker setting
        bZero = arcpy.GetParameter(11)                # treat null values as zero
        # 13 is component percent cutoff which does not appear to be used any more
        bFuzzy = False               # Map fuzzy values for interps
        # the rest of the menu parameters are only used in the validation code

        # need to get selected set or return an empty dictionary?
        # thinking of something like dFilter = {"field": "areasymbol", "values": ["RO163"]}
        dFilter = {"field":"objectid", "values":[191, 1831, 2213, 2916, 3505, 3527]}

        PrintMsg("Calling AggregateData...", 0)

        inputDesc = arcpy.Describe(inputLayer)
        if inputDesc.dataType == "FeatureLayer":
            featureClass = inputDesc.catalogPath
            inputDB = os.path.dirname(featureClass)

        else:
            # input is a featureclass
            inputDB = os.path.dirname(inputLayer)

        PrintMsg(".\tInput database: " + inputDB)


        outputTbl, outputValues = AggregateData(inputLayer, inputDB, dFilter, sdvAtt, aggMethod, primCst, secCst, top, bot, begMo, endMo, tieBreaker, bZero, bFuzzy)
        #outputTbl, outputValues = AggregateData(inputLayer, inputDB, dFilter, sdvAtt, aggMethod, primCst, secCst, top, bot, begMo, endMo, tieBreaker, bZero, bFuzzy)
        #PrintMsg("Returned: " + str(outputTbl) + ";\t" + str(outputValues), 0)

except arcpy.ExecuteError:
    # Catch arcpy errors here
    PrintMsg("arcpy.ExecuteError encountered", 1)
    msgs = arcpy.GetMessages(2)
    arcpy.AddError(msgs)

except:
    # Catch python errors here
    # tbInfo contains the script, function and error line number
    tb = sys.exc_info()[2]
    tbInfo = traceback.format_tb(tb)[0]
    # Need to see how this handles errors that are in the main

    errInfo = str(sys.exc_info()[1])

    # Concatenate information together concerning the error into a message string
    pymsg = tbInfo + "\n" + errInfo

    if errInfo.find("MyError") == -1:
        # Report python errors
        PrintMsg("Python Error", 1)
        arcpy.AddError(pymsg)

    else:
        # raised error condition
        PrintMsg("Raised Error", 1)
        arcpy.AddError(err)


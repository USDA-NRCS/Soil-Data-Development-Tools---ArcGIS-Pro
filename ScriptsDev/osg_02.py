# D:\notes\2021\11\Gaia-1160\tests_20211102\osg_02.py
# Based upon D:\notes\2021\11\Gaia-1160\tests_20211101_tx451\osg_01.py
# original created by Khaled Garadah and provided to me 10/26/2021 (?).
# Goal for this code modification:
# 1. Understand what Khaled's code does.
# 2. Load the TX415 SSA SSURGO mupolygon shapefile into a GeoPackage.
# invoke with:
#	"c:\Program Files\ArcGIS\Pro\bin\Python\scripts\propy.bat" D:\notes\2021\11\Gaia-1160\tests_20211102\osg_02.py
# or:
#	"c:\Program Files\ArcGIS\Pro\bin\Python\scripts\proenv.bat"
#	python D:\notes\2021\11\Gaia-1160\tests_20211102\osg_02.py
# Other files of interest:
#   D:\notes\2021\11\Gaia-1160\tests_20211102\empty.gpkg    -- the empty GeoPackage
#   D:\notes\2021\11\Gaia-1160\tests_20211102\osg_02.gpkg   -- new populated GeoPackage 
#   D:\notes\2021\11\Gaia-1160\data                         -- root of SSA\spatial folders 
#   D:\notes\2021\11\Gaia-1160\tests_20211102\ogr2ogr.py    -- Simulate OGR "ogr2ogr.exe" utility
# Reference:
#   https://pcjericks.github.io/py-gdalogr-cookbook/
#   https://gdal.org/python/

import osgeo
import os 
import sqlite3
import sys
import subprocess
import os.path
import shutil

# Modified to not overite new geopackage and will add mupolygons

workdir ='D:\\notes\\2021\\11\\Gaia-1160\\tests_20211102\\'
dataRoot = 'D:\\notes\\2021\\11\\Gaia-1160\\data\\'
pythonScript = 'c:\\Program Files\\ArcGIS\\Pro\\bin\\Python\\scripts\\propy.bat'
ogr2ogrScript = workdir + 'ogr2ogr.py'

def insert_data(daShapefile, dbDatabase, layername, pythonScript, ogr2ogrScript):
    shp = daShapefile.replace('\\', '/')
    db = dbDatabase.replace('\\', '/')
    # Arguments of interest:
    # -nln <name>   assign alternative name to layer
    # -append       qppend to curent data
    cmd = [pythonScript, ogr2ogrScript,
        "-f", "GPKG", "-append", "-nln", layername, dbDatabase, daShapefile]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
    stdout,stderr=proc.communicate()
    exit_code=proc.wait()
    if exit_code: 
        print("failure")
        print("cmd:")
        for c in cmd:
            print(c)
        sys.exit(stderr)


# Enable GDAL/OGR exceptions (original)
#gdal.UseExceptions()

try:
    from osgeo import ogr, osr, gdal
except:
    sys.exit('ERROR: cannot find GDAL/OGR modules')

# Enable GDAL/OGR exceptions (relocated)
gdal.UseExceptions()

#projection csr adjustmet 
"""from osgeo import osr
testSR = osr.SpatialReference()
res = testSR.ImportFromEPSG(4326)
if res != 0:
    raise RuntimeError(repr(res) + ': could not import from EPSG')
print(testSR.ExportToPrettyWkt())"""

# set working dir
os.chdir(workdir) 
print(os.getcwd())
# Copy empty geopackage to define target
dbDatabase = workdir + 'osg_02.gpkg'
# shutil.copyfile(workdir + 'empty.gpkg', dbDatabase)
print('target dbDatabase: %s' % dbDatabase)

# Files of interest for the layer
layername = 'mupolygon' #'sacatalog'
shpnameprefix = 'soilmu_a_'  # 'soilsa_a_'
for root, d_names, f_names in os.walk(dataRoot):
    for f in f_names:
        if f.startswith(shpnameprefix) and f.endswith('.shp'):
            fqn = os.path.join(root, f)
            print(fqn)
            insert_data(fqn, dbDatabase, layername, pythonScript, ogr2ogrScript)




"""
#read the shapfiles in directory 
daShapefile = workdir + '\\soilmu_a_tx451.shp'

driver = ogr.GetDriverByName('ESRI Shapefile')

dataSource = driver.Open(daShapefile, 0) # 0 means read-only. 1 means writeable.

layer = dataSource.GetLayer()
featureCount = layer.GetFeatureCount()
print("Number of features in %s: %d" % (os.path.basename(daShapefile),featureCount))
"""

# In the context of ArcGIS Pro Python an initial script must be executed 
# to condition the environment, then this Python script and its 
# arguments can be provided.

# Consider only the SSA boundaryes "soilsa_a_*.shp"

# Arguments of interest:
# -nln <name>   assign alternative name to layer
# -append       qppend to curent data
"""
cmd = [r"c:\Program Files\ArcGIS\Pro\bin\Python\scripts\propy.bat",
    r"D:\notes\2021\11\Gaia-1160\tests_20211102\ogr2ogr.py",
    "-f", "GPKG", "-qppend", dbDatabase, daShapefile]

proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
stdout,stderr=proc.communicate()
exit_code=proc.wait()
if exit_code: print(stderr)
else: print(stdout)
"""
#check the output database 
#gpkg_layers = [l.GetName() for l in ogr.Open(dbDatabase )]
#print(gpkg_layers)

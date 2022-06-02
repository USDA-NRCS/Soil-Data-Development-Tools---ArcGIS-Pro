This folder contains several SQLite-spatialite SSURGO Template databases.

The most recent version is template_spatialite_cascades.sqlite. The most important things about this database is that it uses POLYGON instead of MULTIPOLYGON geometry. 

The SSURGO_DataLoader02 script has been modified to be compatible with POLYGON only! The older versions of template databases will only work with a script that outputs MULTIPOLYGON.

The out-dated versions of template databases are still good examples of how the cointerp table can be reduced.

The TemplateMetadataTables.sqlite only contains the 'static' mdstat, month and system_templatedatabaseinformation tables. It is used to create new SSURGO Template databases.

Steve Peaslee. 2021-12-22.
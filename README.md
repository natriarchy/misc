# misc
Some Python scripts I've used and keep as a reference for future work.

## ArcGIS Pro Custom Python Tool: [Select Layer from Text Array](ArcGIS_Tool_SelectLayerTextArray.py)
Main purpose is to tie additional parcels that are referenced by a board application or ownership record to the primary parcel. Especially when the additional parcels are referenced in a single field as a text list. A screenshot of the tool it generates is [here](ArcGISCustomTool.png)

## Utility Python Script: [Convert Database of Project Records to GIS Layer](Script_DBRecordsToGISParcels.py)
Script to query an online database (Quickbase) of internal board records Then convert to usable ArcGIS Feature layer. Allows for repeated queries to overcome response limits, and reads out the real-time status in terminal/notebook.

## Utility Python Script: [Getting Bus Headways and First/Last Bus](ArcGIS_Script_BusAnalysis.py)
This includes two short functions I used when analysing the bus network of Newark for the Master Plan. The first went through 800+ bus stops and calculated the mean time between bus arrivals, the second just returned the first or last bus scheduled to arrive at a station.

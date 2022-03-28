import numpy
import arcpy

def getAverageHeadways(stopId):
    """
    Function to get the average time between bus arrivals
    for a given bus stop (stopId)
    """
    # Query the table of scheduled bus arrivals for the specified bus stop on Mon/Wed/Thurs Schedules
    rows = arcpy.SearchCursor(
        "D:/Documents/ArcGIS/Projects/NewarkGeneral/Default.gdb/GTFS_2020_09_02_StopTimes_Weekdays_09_14",
        where_clause="stop_id={} AND service_id IN (4,9,19,20,21,25)".format(stopId),
        fields="stop_id; arrival_time; service_id",
        sort_fields="arrival_time A")
    times = []
    for row in rows:
        rowtime = row.getValue("arrival_time")
        # The following two lines are to convert the text time to a simple number (seconds) so we can calculate differences
        timeels = rowtime.split(":")
        rowsecs = (float(timeels[0]) * 60) + float(timeels[1]) + float(float(timeels[2]) / 60)
        times.append(rowsecs)
    # numpy.diff is the utility we use to get the headways between bus arrivals
    # it's used to calcalulate the difference between each element in an array and the one following it
    headways = numpy.diff(times)
    # the following line just calculates the average of the headways
    return numpy.mean(headways)

import numpy
import arcpy

def getFirstOrLastBus(stopId, firstOrLast):
    """
    Function to get the first or last (firstOrLast) scheduled bus arrival
    for a given bus stop (stopId)
    """
    # Query the table of scheduled bus arrivals for the specified bus stop on Mon/Wed/Thurs Schedules
    rows = arcpy.SearchCursor(
        "D:/Documents/ArcGIS/Projects/NewarkGeneral/Default.gdb/GTFS_2020_09_02_StopTimes_Weekdays_09_14",
        where_clause="stop_id={} AND service_id IN (4,9,19,20,21,25)".format(stopId),
        fields="stop_id; arrival_time; service_id",
        sort_fields="arrival_time A")
    times = []
    position = 0 if firstOrLast == "first" else -1
    for row in rows:
        times.append(row.getValue("arrival_time"))
    return times[position]

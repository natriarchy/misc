import pandas
import csv
import sys

# Progress bar printer
def drawProgressBar(percent, barLen = 20):
    sys.stdout.write("\r")
    sys.stdout.write(
        "[{:<{}}] {:.0f}%".format(
        "=" * int(barLen * percent),
        barLen,
        percent * 100
    ))
    sys.stdout.flush()

def getWeekdayBusToSubway(fp="", outputFolder="."):
    """
    Function to query MTA 2018 Travel Survey (Unlinked), return
    new csv file with average weekday bus-subway transfers
    """
    print("Retrieving Dataset, Could Take a little While...")
    surveyURL = r'https://new.mta.info/document/29061' if fp == "" else fp
    df = pandas.read_excel(surveyURL)
    print("Dataset Retreived!")
    
    ## Get list of unique weekdays for records including > 1 transit leg
    baseQuery = "traveldate_dow not in ('Saturday','Sunday') &\
         num_transit_legs == num_transit_legs & num_transit_legs > 1"
    uniqueDays = list(
        df.query(baseQuery).value_counts("traveldate").keys()
        )
    print("Found {} Unique Weekday Travel Dates".format(len(uniqueDays)))

    outputHeaders = [
        'station_id',
        'station_name',
        'transfers_bustosw_averagewd'
        ]
    ## data including transfers per stop by day
    rawResults = []
    ## Store a list of all the stationids so we can summarize afterwards
    allStopIds = []
    ## Store weekday averages calculated for each stop in rawresults
    finalResults = []

    print("Iterating Through Ridership Data...")
    for day in uniqueDays:
        ## Object to store station info for each day
        byStationResults = {}

        ## Filter main dataset for trips on this day with > 1 transit leg
        #### If there was only one leg than there wasn't a transfer
        dayQuery = df.query(
            "traveldate == @day &\
            num_transit_legs == num_transit_legs & num_transit_legs > 1"
            )
        
        ## Get list of tripids, to check each one for a bus transfer
        dayTrips = list(dayQuery.value_counts("tripid").keys())
        for trip in dayTrips:
            ## Query all legs of the trip
            dtq = dayQuery.query("tripid == @trip")
            
            ## Generate list of "legids" for all subway legs of the trip
            subwayTrips = list(
                dtq.query(
                    "transit_system == 'New York City Transit Subway'"
                    ).value_counts("legid").keys()
                )
            ## Generate list of legids for all bus legs of the trip
            busTrips = list(
                dtq.query(
                    "transit_system in [\
                        'Local MTA/New York City Transit Bus',\
                        'Express/SBS MTA/New York City Transit Bus'\
                    ]").value_counts("legid").keys()
                )
            
            ## Filter bus legids for ones directly before a subway leg
            busBeforeSubway = list(
                filter(lambda el: int(el + 1) in subwayTrips, busTrips)
                )
            ## Now we know the bus legs directly preceding subway legs,
            ## so add one to each, to list subway legids for each transfer 
            subwayPostBusTrips = list(
                map(lambda el: el + 1, busBeforeSubway)
                )
            
            ## Query all the subway legs that occur right after bus legs
            finalQuery = dtq.query("legid in @subwayPostBusTrips").filter(
                    items=[
                        'board_stop_id',
                        'board_stop_name',
                        'per_weight_wd_trips_rsadj'
                        ]
                    )
            
            ## Summarize trip data for each stop in byStationResults object
            ## per_weight_wd_trips_rsadj weights trips based on average
            ## weekday trips, so sum all of them
            for label,trip in finalQuery.iterrows():
                bsID = trip['board_stop_id']
                bsName = trip["board_stop_name"]
                tripWeight = trip['per_weight_wd_trips_rsadj']
                if trip["board_stop_id"] in byStationResults:
                    byStationResults[bsID]['trips'] += tripWeight
                else:
                    byStationResults[bsID] = {
                        'board_stop_name': bsName,
                        'trips': tripWeight
                    }
        ## Now let's write each day's trip data to the rawResults object
        for stopId in byStationResults.keys():
            if stopId not in allStopIds:
                allStopIds.append(stopId)
            rawResults.append([
                stopId,
                byStationResults[stopId]['board_stop_name'],
                day,
                byStationResults[stopId]['trips']
            ])
        
        drawProgressBar(uniqueDays.index(day)/len(uniqueDays))
    
    print("\nRidersip Data Collected, Summarizing Averages per Stop")
    for stop in allStopIds:
        ## Filter Daily Totals in rawResults Object
        filteredData = list(
            filter(lambda el: el[0] == stop, rawResults)
            )
        stopName = "" if len(filteredData) < 1 else filteredData[0][1]
        
        ## Calculate average ridership
        stopAverage = sum(
            map(lambda el: el[3], filteredData)
            ) if len(filteredData) > 0 else 0
        
        ## Add row to the final results
        finalResults.append([stop, stopName, stopAverage])

    print("Printing Result to CSV file...")
    with open(
        f'{outputFolder}/BusTransfersPerStation_2018.csv',
        'w',
        encoding="UTF8",
        newline=''
        ) as f:
        writer = csv.writer(f, dialect="excel")
        writer.writerow(outputHeaders)
        writer.writerows(finalResults)
    print(
        f"Done!\nOutput at {outputFolder}/BusTransfersPerStation_2018.csv"
        )

getWeekdayBusToSubway()

import arcpy
import datetime
import requests
import sys

startTime = datetime.datetime.now()
fields = [
    ["3","Record_ID","SHORT","QB ID"],
    ["7","DocketNum","TEXT","DocketNum"],
    ["10","Project_Name","TEXT","Project Name"],
    ["9","Date_Received","DATE","Date Received"],
    ["12","Application_Types","TEXT","Application Types"],
    ["152","Project_Status","TEXT","Project Status"],
    ["150","Legal_Address_Primary","TEXT","Legal Address Primary"],
    ["151","Legal_Address_List","TEXT","Legal Address List"],
    ["13","BlockLot_Primary","TEXT","BlockLot Primary"],
    ["14","BlockLot_List","TEXT","BlockLot List"],
    ["15","Ward","TEXT","Ward"],
    ["16","Zoning_District","TEXT","Zoning District"],
    ["19","Historic_District","TEXT","Historic District"],
    ["29","Hearing_Date","TEXT","Hearing Date"],
    ["30","Hearing_Status","TEXT","Hearing Status"],
    ["21","EJCIO_Status","TEXT","EJCIO Status"],
    ["25","Summary_Project","TEXT","Summary Project"],
    ["26","Summary_Notes","TEXT","Summary Notes"],
    ["17","Zoning_Determination","TEXT","Zoning Determination"],
    ["18","Zoning_CVariances","SHORT","Zoning CVariances"],
    ["107","Zoning_DVariances","TEXT","Zoning DVariances"],
    ["31","Residential_New_Units","SHORT","Residential New Units"],
    ["32","Residential_New_SqFt","FLOAT","Residential New SqFt"],
    ["33","Residential_Exist_Units","SHORT","Residential Exist Units"],
    ["34","Residential_Exist_SqFt","FLOAT","Residential Exist SqFt"],
    ["35","Residential_Rehab_Units","SHORT","Residential Rehab Units"],
    ["36","Residential_Rehab_SqFt","FLOAT","Residential Rehab SqFt"],
    ["37","Retail_New_Units","SHORT","Retail New Units"],
    ["38","Retail_New_SqFt","FLOAT","Retail New SqFt"],
    ["39","Retail_Rehab_Units","SHORT","Retail Rehab Units"],
    ["40","Retail_Rehab_SqFt","FLOAT","Retail Rehab SqFt"],
    ["65","Office_New_Units","SHORT","Office New Units"],
    ["66","Office_New_SqFt","FLOAT","Office New SqFt"],
    ["67","Office_Rehab_Units","SHORT","Office Rehab Units"],
    ["68","Office_Rehab_SqFt","FLOAT","Office Rehab SqFt"],
    ["69","Industrial_Type","TEXT","Industrial Type"],
    ["70","Industrial_New_Units","SHORT","Industrial New Units"],
    ["71","Industrial_New_SqFt","FLOAT","Industrial New SqFt"],
    ["72","Industrial_Rehab_Units","SHORT","Industrial Rehab Units"],
    ["73","Industrial_Rehab_SqFt","FLOAT","Industrial Rehab SqFt"],
    ["74","Other_Type","TEXT","Other Type"],
    ["75","Other_New_Units","SHORT","Other New Units"],
    ["76","Other_New_SqFt","FLOAT","Other New SqFt"],
    ["77","Other_Rehab_Units","SHORT","Other Rehab Units"],
    ["78","Other_Rehab_SqFt","FLOAT","Other Rehab SqFt"],
    ["43","Total_ProjFloor_SqFt","FLOAT","Total Project Floor SqFt"],
    ["45","Total_Parking","SHORT","Total Parking"],
    ["122","Compliance_Overall_Status","TEXT","Compl. Status"],
    ["167","Compliance_Planning_Status","TEXT","Compl. Status: Planning"],
	  ["168","Compliance_Engineering_Status","TEXT","Compl. Status: Engineering"],
	  ["169","Compliance_WaterSewer_Status","TEXT","Compl. Status: Water & Sewer"],
	  ["175","Compliance_TaxAssessor_Status","TEXT","Compl. Status: Tax Assessor"],
	  ["176","Compliance_Bond_Status","TEXT","Compl. Status: Bond"],
    ["62","Application_PDF","TEXT","Application"],
    ["63","Application_Plans_Eng","TEXT","Plans - Eng."],
    ["164","Application_Plans_Arch","TEXT","Plans - Arch."],
    ["64","Application_Render","TEXT","Renderings"],
    ["166","Application_Resolution","TEXT","Resolution"]
]
# removed values for security of data, necessary for proper response
headers = {
  	'QB-Realm-Hostname': '',
    'User-Agent': '',
    'Authorization': ''
}
skipCounter = 0
fullResponse = []
blocklotlist = []
parcelInfoList = []
def makeReq(skip):
    fieldIDs = [field[0] for field in fields]
    body = {
        "from": "bq8edipds",
        "select": fieldIDs,
        "sortBy": [
            {
                "fieldId": 9,
                "order": 'ASC'
            }
        ],
        "options": {
            "skip": skip,
            "top": 4000
        }
    }
    r = requests.post(
        'https://api.quickbase.com/v1/records/query', 
        headers = headers,
        json = body
    )
    return r

def formatResp(obj):
    newdata = []
    for f in fields:
        if f[0] in ("22","55","57","59","61","62","63","64","164","166"):
            url = ""
            # Create link to quickbase attachment "https://cityofnewark.quickbase.com/up/{Table ID}/a/r{Record ID}/e{Field ID}/v{Version Number}"
            if obj[f[0]]["value"]["url"] != "":
                urlArray = obj[f[0]]["value"]["url"][1:].split("/")
                url = "https://cityofnewark.quickbase.com/up/{}/a/r{}/e{}/v{}".format(urlArray[1],urlArray[2],urlArray[3],urlArray[4])
            newdata.append((f[1], url))
        elif f[0] in ("12","16","30","69","74","107","167","168","169","175"):
            # Convert list (mult-select) fields to one semicolon separated string
            newdata.append((f[1], ";".join(obj[f[0]]["value"])))
        elif f[2] == 'DATE' and obj[f[0]]["value"] != '':
            newdata.append((f[1], str(datetime.datetime.strptime(obj[f[0]]["value"], "%Y-%m-%d"))))
        elif f[2] == 'DATE' and obj[f[0]]["value"] == '':
            newdata.append((f[1], None))
        else:
            newdata.append((f[1], obj[f[0]]["value"]))
    # Create link to full quickbase record "https://cityofnewark.quickbase.com/db/{Table ID}?a=dr&rid={Record ID}"
    newdata.append(("Record_URL","https://cityofnewark.quickbase.com/db/bq8edipds?a=dr&rid={}".format(obj['3']["value"])))
    return dict(newdata)

def makeBlockLotList(row):
    return row['BlockLot_Primary']

def makeParcelList(row):
    return { 'BlockLot': row.getValue('LOT_BLOCK_LOT'), 'SHAPE': row.getValue('SHAPE') }

# Create an in_memory feature class
feature_class = arcpy.CreateFeatureclass_management(
    "in_memory", "Quickbase_PZO_Applications", "POLYGON", spatial_reference=3424)[0]

# Convert fields object to an array of field names
def makeFeatureFields():
    fieldlist = [field[1] for field in fields]
    fieldlist.append("Record_URL")
    fieldlist.insert(0, "SHAPE@")
    addField_Format = [[field[1],field[2],field[3]] for field in fields]
    addField_Format.append(["Record_URL", "TEXT", "Record URL"])
    # Add fields to feature class
    arcpy.management.AddFields(
        feature_class,
        addField_Format
        )
    return fieldlist

# Make feature fields with record url and shape
feature_fields = makeFeatureFields()

# Progress bar printer during feature class creation
def drawProgressBar(percent, barLen = 20):
    # percent float from 0 to 1. 
    sys.stdout.write("\r")
    sys.stdout.write("[{:<{}}] {:.0f}%".format("=" * int(barLen * percent), barLen, percent * 100))
    sys.stdout.flush()

def doQuery():
    global skipCounter
    r = makeReq(skipCounter)
    fullResponse.extend([formatResp(row) for row in r.json()['data']])
    blocklotlist.extend([makeBlockLotList(row) for row in fullResponse])
    
    # Set the workspace
    arcpy.env.workspace = "D:/Documents/ArcGIS/Projects/NewarkGeneral/Default.gdb"

    # Set the parcel featureset
    parcels = "D:/Documents/ArcGIS/Projects/NewarkGeneral/Default.gdb/Newark_Parcels_2020_07_31_AddLotFixed"
    parcelsCursor = arcpy.SearchCursor(parcels, 'LOT_BLOCK_LOT in {} AND SHAPE IS NOT NULL'.format(str(tuple(blocklotlist))), ["LOT_BLOCK_LOT", "SHAPE@"])
    parcelInfoList.extend([makeParcelList(row) for row in parcelsCursor])
    print('Parcels Gathered, {} Parcels'.format(len(parcelInfoList)))
    if (r.json()['metadata']['skip'] + r.json()['metadata']['top']) >= int(r.json()['metadata']['totalRecords']):
        print("Print Done, Writing Features...")
        # Open an insert cursor
        with arcpy.da.InsertCursor(feature_class, tuple(feature_fields)) as cursor:
            # Iterate through list of coordinates and add to cursor
            for feat in fullResponse:
                shape = None
                if list(filter(lambda obj: obj['BlockLot'] == feat['BlockLot_Primary'], parcelInfoList)) != []:
                    shape = list(filter(lambda obj: obj['BlockLot'] == feat['BlockLot_Primary'], parcelInfoList))[0]["SHAPE"]
                row = []
                for field in feature_fields[1:]:
                    if len(str(feat[field])) > 255:
                        row.append(feat[field][:254])
                    else:
                        row.append(feat[field])
                cursor.insertRow([shape]+row)
                drawProgressBar(fullResponse.index(feat)/len(fullResponse))
        print("\nFeature Class Set Up.")
    else:
        print(str(r.json()['metadata']['skip'] + r.json()['metadata']['top']) +
        '/' + str(r.json()['metadata']['totalRecords']))
        skipCounter = r.json()['metadata']['skip'] + 4000
        doQuery()

doQuery()
print('Executed in {}'.format(datetime.datetime.now() - startTime))

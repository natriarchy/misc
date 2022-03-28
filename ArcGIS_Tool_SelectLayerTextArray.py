# -*- coding: utf-8 -*-

import json
import arcpy


class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "MyPyTools"
        self.alias = "My Python Scripts for Common Tasks"

        # List of tool classes associated with this toolbox
        self.tools = [Tool]


class Tool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Select Layer from Text Array"
        self.description = "Used to select records in one layer from a text array field in another"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Source Layer",
            name="source_layer",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input"
        )

        param1 = arcpy.Parameter(
            displayName="Source Layer ID Field",
            name="source_id_field",
            datatype="Field",
            parameterType="Required",
            direction="Input"
        )
        param1.parameterDependencies = [param0.name]
        
        param2 = arcpy.Parameter(
            displayName="Source Layer Primary Field",
            name="source_primary_field",
            datatype="Field",
            parameterType="Optional",
            direction="Input"
        )
        param2.parameterDependencies = [param0.name]

        param3 = arcpy.Parameter(
            displayName="Source Layer Field with Text Array",
            name="source_array_field",
            datatype="Field",
            parameterType="Required",
            direction="Input"
        )
        param3.filter.list = ['Text']
        param3.parameterDependencies = [param0.name]

        param4 = arcpy.Parameter(
            displayName="Text Array Delimiter",
            name="array_delimiter",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )
        # Set a value list of text delimiters for separating string array
        param4.filter.type = "ValueList"
        param4.filter.list = [",",";",".","/"]
        param4.value = ","
        
        param5 = arcpy.Parameter(
            displayName="Output Type (Table or Feature Layer)",
            name="output_type",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )
        param5.filter.type = "ValueList"
        param5.filter.list = ["Table","Feature Layer"]
        param5.value = "Table"

        param6 = arcpy.Parameter(
            displayName="Target Layer",
            name="target_layer",
            datatype="GPLayer",
            parameterType="Required",
            direction="Input"
        )
        
        param7 = arcpy.Parameter(
            displayName="Field in Target Layer to Select",
            name="target_id_field",
            datatype="Field",
            parameterType="Required",
            direction="Input"
        )
        param7.parameterDependencies = [param6.name]

        param8 = arcpy.Parameter(
            displayName="Output workspace",
            name="out_workspace",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input"
        )
        param8.defaultEnvironmentName = "workspace"

        param9 = arcpy.Parameter(
            displayName="Output Layer Name",
            name="out_name",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )
        
        param10 = arcpy.Parameter(
            displayName="Check All Other Delimiters (Exp)",
            name="check_others",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input"
        )

        params = [
            param0,
            param1,
            param2,
            param3,
            param4,
            param5,
            param6,
            param7,
            param8,
            param9,
            param10
        ]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        
        if parameters[5].valueAsText == 'Table':
            parameters[6].enabled = False
            parameters[7].enabled = False
        else:
            parameters[6].enabled = True
            parameters[7].enabled = True

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""

        return

    def execute(self, parameters, messages):
        """The source code of the tool."""

        # Convert params to variables
        source_layer = parameters[0].value.dataSource
        source_id_field = parameters[1]
        source_primary_field = parameters[2]
        source_array_field = parameters[3]
        array_delimiter = parameters[4]
        output_type = parameters[5]
        target_layer = parameters[6].value.dataSource if parameters[6].enabled else None
        target_id_field = parameters[7] if parameters[7].enabled else None
        out_workspace = parameters[8]
        out_name = parameters[9]
        check_others = parameters[10]

        # Lists of data to work with
        sourceRows = []
        targetRows = []

        sourceCursorFields = [source_id_field.valueAsText, source_array_field.valueAsText, 'SHAPE@']
        if source_primary_field.value != None:
            sourceCursorFields.append(source_primary_field.valueAsText)

        # First cursor functions
        with arcpy.da.SearchCursor(
            in_table=source_layer,
            field_names=sourceCursorFields,
            where_clause="{} IS NOT NULL AND {} <> ''".format(source_array_field.valueAsText, source_array_field.valueAsText)
            ) as sourceCursor:
                # Get the array data and insert into sourceRow list
                for sourceRow in sourceCursor:
                    field_array = str(sourceRow[1]).split(array_delimiter.value)
                    if check_others.valueAsText == 'true' and field_array[0] == sourceRow[1]:
                        no_spaces_txt = str(sourceRow[1]).replace(' ','')
                        other_delimiters = [",",";","/"]
                        other_delimiters.remove(array_delimiter.value)
                        for delimiter in other_delimiters:
                            new_array = str(no_spaces_txt).split(delimiter)
                            if len(new_array) > 1:
                                field_array = new_array
                                break
                    if source_primary_field.value != None:
                        field_array.insert(0, sourceRow[3])
                    if output_type.valueAsText == 'Table':
                        sourceRows.append([sourceRow[0], field_array])
                    else:
                        sourceRows.append([sourceRow[0], field_array, sourceRow[2]])

        messages.addMessage('Gathered ' + str(len(sourceRows)) + ' Source Records to Search Target Layer For')

        arcpy.SetProgressor("step", "Generating Rows from Target Layer...",
            0, len(sourceRows), 1)

        mergedRecords = 0
        messages.addMessage("Generating "+output_type.valueAsText)
        # Collect the records from the target layer
        for row in sourceRows:
            if output_type.valueAsText == 'Table':
                for target in row[1]:
                    targetRows.append((row[0],target))
            else:
                in_statement = "= '{}'".format(row[1][0]) if len(row[1]) == 1 else "in {}".format(tuple(row[1]))
                with arcpy.da.SearchCursor(
                    in_table=target_layer,
                    field_names=[target_id_field.valueAsText,'SHAPE@'],
                    where_clause="{} {}".format(target_id_field.valueAsText, in_statement)
                ) as targetCursor:
                    cursorChecker = []
                    newfeat = row[2]
                    for feat in targetCursor:
                        if bool(type(row[2]) == type(feat[1])):
                            newfeat = newfeat.union(feat[1])
                            cursorChecker.append(feat[0])
                            mergedRecords = mergedRecords + 1
                    targetRows.append((
                        row[0],
                        str(array_delimiter.valueAsText).join(map(str, row[1])),
                        str(array_delimiter.valueAsText).join(map(str, cursorChecker)),
                        newfeat
                        ))
            sourceRowsStatus = sourceRows.index(row)
            arcpy.SetProgressorPosition(sourceRowsStatus)
        arcpy.ResetProgressor()
        messages.addMessage('Merged {} Records'.format(mergedRecords))
        messages.addMessage('Gathered {} Target Records for Output {}\n...Generating Output'.format(len(targetRows),output_type.valueAsText))

        data_json = {
            "objectIdFieldName": "objectid",
            "globalIdFieldName": "globalid",
            "fields": [
                {
                    "name": "Source_ID",
                    "alias": "Source ID",
                    "type": "esriFieldTypeString",
                    "length": 255
                }
            ],
            "features": []
        }

        if output_type.valueAsText == 'Table':
            targetIDField = {
                "name": "Target_ID",
                "alias": "Target ID",
                "type": "esriFieldTypeString",
                "length": 255
            }
            data_json["fields"].append(targetIDField)
        else:
            data_json["geometryType"] = "esriGeometryPolygon"
            data_json["spatialReference"] = { "wkid" : 102711, "latestWkid" : 3424 }
            targetIDListField = {
                "name": "Target_ID_List",
                "alias": "Target ID List",
                "type": "esriFieldTypeString",
                "length": 255
            }
            joinedIDListField = {
                "name": "Joined_ID_List",
                "alias": "Joined_ID_List",
                "type": "esriFieldTypeString",
                "length": 255
            }
            data_json["fields"].append(targetIDListField)
            data_json["fields"].append(joinedIDListField) 

        outData = arcpy.RecordSet(data_json) if output_type.valueAsText == 'Table' else arcpy.FeatureSet(json.dumps(data_json))

        messages.addMessage(outData)
        messages.addMessage("{} Generated\n...Adding Final Records".format(output_type.valueAsText))

        arcpy.SetProgressor("step", "Generating Final {}...".format(output_type.valueAsText),
            0, len(targetRows), 1)
        
        if output_type.valueAsText == "Table":
            out_fields = ["Source_ID", "Target_ID"]
        else:
            out_fields = ["Source_ID", "Target_ID_List", "Joined_ID_List", "SHAPE@"]

        # Iterate through targetRows and add to cursor
        with arcpy.da.InsertCursor(outData, out_fields) as outCursor:
            for row in targetRows:
                outCursor.insertRow([row[0],row[1]] if output_type.valueAsText == "Table" else [row[0],row[1],row[2],row[3]])
                arcpy.SetProgressorPosition(targetRows.index(row))
            arcpy.ResetProgressor()

        outData.save("{}\{}".format(out_workspace.value,out_name.value))
        
        del sourceCursor,outCursor

        messages.addMessage("Done, Output at {}\{}".format(out_workspace.value,out_name.value))
        return

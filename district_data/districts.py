import json
import csv
import os
import requests
import sys
import pdb
from collections import OrderedDict
from datetime import datetime

if not os.path.exists('single_district_geojson'):
    os.makedirs('single_district_geojson')

if not os.path.exists('single_district_json'):
    os.makedirs('single_district_json')

if not os.path.exists('committees'):
    os.makedirs('committees')

if not os.path.exists('council_members'):
    os.makedirs('council_members')

# INSERT LEGISTAR TOKEN
TOKEN = ""
if len(sys.argv) == 2:

    if sys.argv[1] == "convert": # IF THE JSON HAS NOT BEEN MADE CREATE IT
        try:
            # Will refactor, currently inefficient to open the csv twice: once to get the headers dynamically, and twice to get the csv in a ioTextWrapper object
            CSV_FILE_IO = open('nycc_district-cm_data.csv', 'r')
            JSON_FILE = open('cm_master_file.json', 'w')
            READER = csv.DictReader(CSV_FILE_IO, csv.DictReader(CSV_FILE_IO).fieldnames)
            JSON_FILE.write('[')
            for index, row in enumerate(READER): #CONVERT CSV INTO JSON
                NESTED_DICT = OrderedDict([("id", int(row["district"])),("district", int(row["district"]))])
                del row["district"]
                NESTED_DICT.update({"council_member":row})
                json.dump(NESTED_DICT, JSON_FILE, indent=2)
                if int(index) is not 50:
                    JSON_FILE.write(',\n')
            JSON_FILE.write(']')
            print('CSV has been successfully converted to JSON.')

        except FileNotFoundError: # BAD FILE NAME
            print("The file 'nycc_district-cm_data.csv' does not exist in this folder!")

    elif sys.argv[1] == "legistar": # IF JSON EXISTS, START PARSING
        with open('cm_master_file.json') as json_data:
            ALL_CM = json.load(json_data)

        # IF IT HAS LESS THAN CERTAIN NUMBER OF FIELDS, IT HAS NOT GONE THROUGH LEGISTAR YET
        for cm in ALL_CM:
            PERSON_LINK = "https://webapi.legistar.com/v1/nyc/persons/{}/?token={}".format(cm["council_member"]["person_id"], TOKEN)
            TODAY = datetime.today()
            if (TODAY.year % 4) >= 2:
                TODAY = TODAY.replace(year=TODAY.year - ((TODAY.year % 4) - 2), month=1, day=1).strftime("%Y-%m-%d")
            else:
                TODAY = TODAY.replace(year=TODAY.year - ((TODAY.year % 4) + 2), month=1, day=1).strftime("%Y-%m-%d")
            END = "{}-{}-{}".format(int(TODAY.split("-")[0]) + 3, 12, 31)
            COMMITTEE_LINK = "https://webapi.legistar.com/v1/nyc/persons/{}/officerecords/?$filter=OfficeRecordStartDate+ge+datetime'{}'+and+OfficeRecordEndDate+eq+datetime'{}'&token={}".format(cm["council_member"]["person_id"], TODAY, END, TOKEN)
            # BELOW EXCLUDES THE COUNCIL MEMBER TITLE
            # COMMITTEE_LINK = "https://webapi.legistar.com/v1/nyc/persons/{}/officerecords/?$filter=OfficeRecordStartDate+ge+datetime'{}'+and+OfficeRecordEndDate+le+datetime'{}'+and+OfficeRecordBodyId+ne+1&token={}".format(cm["council_member"]["person_id"], TODAY.strftime("%Y-%m-%d"), END, TOKEN)

            CM_GET_DATA = requests.get(url=PERSON_LINK)
            CM_DATA = CM_GET_DATA.json()
            CM_DATA.pop('PersonFirstName', None)
            CM_DATA.pop('PersonLastName', None)
            COMMITTEE_GET_DATA = requests.get(url=COMMITTEE_LINK)
            COMMITTEE_DATA = COMMITTEE_GET_DATA.json()
            CM_DATA["committees"] = []
            for committee in COMMITTEE_DATA:
                if committee["OfficeRecordBodyId"] != 1:
                    CM_DATA["committees"].append(committee)
            cm["council_member"].update(CM_DATA)
        with open('cm_master_file.json', 'w') as master_file:
            json.dump(ALL_CM, master_file, indent=2)
        print("Data from Legistar has successfully been merged with the original data.")

    elif sys.argv[1] == "json": # IF NUMBER OF FIELDS MATCH UP, IT'S TIME TO MERGE THE GEOJSON
        with open('cm_master_file.json') as json_data:
            ALL_CM = json.load(json_data)
        # GEO_INPUT = input("Enter the URL of the GeoJSON exactly as it appears: ")
        GEO_INPUT = "http://services5.arcgis.com/GfwWNkhOj9bNBqoJ/arcgis/rest/services/nycc/FeatureServer/0/query?where=1=1&outFields=*&outSR=4326&f=geojson"
        GEO_GET_DATA = requests.get(url=GEO_INPUT)
        GEO_DATA = GEO_GET_DATA.json()
        for points in GEO_DATA["features"]:
            ALL_CM[points["properties"]["CounDist"] - 1].update({"district_boundaries":points}) # FIND THE RIGHT CM (INDEX MATCHES UP WITH DISTRICT NUMBER (MINUS 1) BASED ON THE CSV
            # Create separate files for each district
            DISTRICT_JSON_FILE = os.path.join(os.getcwd(), 'single_district_json/district-{}.json'.format(points["properties"]["CounDist"]))
            with open(DISTRICT_JSON_FILE, 'w') as single_file:
                json.dump(ALL_CM[points["properties"]["CounDist"] - 1], single_file, indent=2)

        with open('cm_master_file.json', 'w') as master_file:
            json.dump(ALL_CM, master_file, indent=2)
        print("GeoJSON data from City Planning has successfully been merged with the master data.")

    elif sys.argv[1] == "geojson":
        with open('cm_master_file.json') as json_data:
            ALL_CM = json.load(json_data)
        GEO_INPUT = "http://services5.arcgis.com/GfwWNkhOj9bNBqoJ/arcgis/rest/services/nycc/FeatureServer/0/query?where=1=1&outFields=*&outSR=4326&f=geojson"
        GEO_GET_DATA = requests.get(url=GEO_INPUT)
        GEO_DATA = GEO_GET_DATA.json()
        for points in GEO_DATA["features"]:
            ALL_CM[points["properties"]["CounDist"] - 1].pop('district_boundaries', None)
            ALL_CM[points["properties"]["CounDist"] - 1].pop('district', None)
            points["properties"].update(ALL_CM[points["properties"]["CounDist"] - 1])
            DISTRICT_GEOJSON_FILE = os.path.join(os.getcwd(), 'single_district_geojson/district-{}.geojson'.format(points["properties"]["CounDist"]))
            with open(DISTRICT_GEOJSON_FILE, 'w') as single_file:
                json.dump(points, single_file, indent=2)
        with open('cm_master_file.geojson', 'w') as master_file:
            json.dump(GEO_DATA, master_file, indent=2)
        print("Master data has successfully been merged with the GeoJSON data from City Planning.")

    elif sys.argv[1] == "no_geo":
        with open('cm_master_file.json') as json_data:
            READ_JSON = JSON_FILE = json.load(json_data)
        WRITE_JSON = open('cm_master_file_no_geo.json', 'w')  
        CM_NO_GEO= []
        for cm in READ_JSON:
            CM_DATA = {
                "id": cm["id"],
                "district": cm["district"],
                "council_member": cm["council_member"]
            }
            CM_NO_GEO.append(CM_DATA)
        json.dump(CM_NO_GEO, WRITE_JSON, indent=2)
        print("Master file created without the GeoJSON data from City Planning.")

    elif sys.argv[1] == "committees":
        # TO DO: Trim out unnecessary data from legistar
        TODAY = datetime.today()
        if (TODAY.year % 4) >= 2:
            TODAY = TODAY.replace(year=TODAY.year - ((TODAY.year % 4) - 2), month=1, day=1).strftime("%Y-%m-%d")
        else:
            TODAY = TODAY.replace(year=TODAY.year - ((TODAY.year % 4) + 2), month=1, day=1).strftime("%Y-%m-%d")
        END = "{}-{}-{}".format(int(TODAY.split("-")[0]) + 3, 12, 31)
        # CURRENT COMMITTEES ENDPOINT
        ALL_COMMITTEES_LINK = "https://webapi.legistar.com/v1/nyc/bodies/?token={}&$filter=(BodyTypeName+eq+'Committee'+or+BodyTypeName+eq+'Subcommittee'+or+BodyTypeName+eq+'Land Use')".format(TOKEN)
        ALL_COMMITTEES = requests.get(url=ALL_COMMITTEES_LINK).json()
        # LOOP THRU COMMITTEES, GET THE COMMITTEE/BODY ID, THEN USE NEXT ENDPOINT
        COMMITTEE_DATA = []
        for committee in ALL_COMMITTEES:
        # OFFICE RECORDS/MEMBERS FOR A COMMITTEE
            COMMITTEE_RECORD_LINK = "https://webapi.legistar.com/v1/nyc/bodies/{}/officerecords/?token={}&$filter=OfficeRecordStartDate+ge+datetime'{}'+and+OfficeRecordEndDate+le+datetime'{}'".format(committee["BodyId"], TOKEN, TODAY, END)
            COMMITTEE_RECORDS = requests.get(url=COMMITTEE_RECORD_LINK).json()
            RECORDS = []
            for record in COMMITTEE_RECORDS:
                UPDATED_RECORD = {
                    "Id": record["OfficeRecordId"],
                    "Guid": record["OfficeRecordGuid"],
                    "MemberId": record["OfficeRecordPersonId"],
                    "FirstName": record["OfficeRecordFirstName"],
                    "LastName": record["OfficeRecordLastName"],
                    "FullName": record["OfficeRecordFullName"],
                    "CommitteeId": record["OfficeRecordBodyId"],
                    "CommitteeName": record["OfficeRecordBodyName"],
                    "CommitteeActive": True if committee["BodyActiveFlag"] else False,
                    "MemberTypeId": record["OfficeRecordMemberTypeId"],
                    "Title": record["OfficeRecordTitle"].capitalize(),
                    "MemberActive": True if END in record["OfficeRecordEndDate"] else False,
                    "StartDate": record["OfficeRecordStartDate"],
                    "EndDate": record["OfficeRecordEndDate"],
                    "Version": record["OfficeRecordRowVersion"],
                    "LastUpdatedUTC": record["OfficeRecordLastModifiedUtc"],
                }
                RECORDS = RECORDS + [UPDATED_RECORD]
            COMMITTEE_DATA = COMMITTEE_DATA + RECORDS
        JSON_FILE = open(os.path.join(os.getcwd(),'committees/committees_and_memebers.json'), 'w')
        json.dump(COMMITTEE_DATA, JSON_FILE, indent=2)
        with open(os.path.join(os.getcwd(),'committees/committees_and_members.csv'), mode='w') as csv_file:
            fieldnames = ["Id", "Guid", "MemberId", "FirstName", "LastName", "FullName", "CommitteeId", "CommitteeName", "CommitteeActive", "MemberTypeId", "Title", "MemberActive", "StartDate", "EndDate", "Version", "LastUpdatedUTC"]
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            for row in COMMITTEE_DATA:
                writer.writerow(row)
        print("List of all committees and assignments in current session created in JSON and CSV")

    elif sys.argv[1] == "members":
        MASTER_LIST = None
        JSON_LIST = []
        with open('nycc_district-cm_data.csv', newline='') as csvfile:
            MASTER_CSV = csv.DictReader(csvfile, delimiter=",")
            MASTER_LIST = list(MASTER_CSV)
        with open(os.path.join(os.getcwd(),'council_members/members.csv'), mode='w') as csv_file_2:
            fieldnames = ["PersonId", "Guid", "District", "CouncilDistrict", "FirstName", "LastName", "FullName", "Gender", "Title", "Party", "Active", "PhotoURL", "FacebookURL", "TwitterURL", "TwitterHandle", "InstagramURL", "InstagramHandle", "Website", "Email", "DistrictOfficeAddress", "DistrictOfficeCity", "DistrictOfficeState", "DistrictOfficeZip", "DistrictOfficePhone", "DistrictOfficeFax", "LegislativeOfficeAddress", "LegislativeOfficeCity", "LegislativeOfficeState", "LegislativeOfficeZip", "LegislativeOfficePhone", "LegislativeOfficeFax", "Version", "LastUpdatedUTC"]
            writer = csv.DictWriter(csv_file_2, fieldnames=fieldnames)
            writer.writeheader()
            for row in MASTER_LIST:
                DICT_ROW = dict(row)
                CM_DATA = requests.get(url="https://webapi.legistar.com/v1/nyc/persons/{}/?token={}".format(row["PersonId"],TOKEN)).json()
                CM_ROW = {
                    "FirstName": CM_DATA["PersonFirstName"],
                    "LastName": CM_DATA["PersonLastName"],
                    "FullName": CM_DATA["PersonFullName"],
                    "Active": CM_DATA["PersonActiveFlag"],
                    "Guid": CM_DATA["PersonGuid"],
                    "Version": CM_DATA["PersonRowVersion"],
                    "LastUpdatedUTC": CM_DATA["PersonLastModifiedUtc"],
                    "DistrictOfficeAddress": CM_DATA["PersonAddress1"],
                    "DistrictOfficeCity": CM_DATA["PersonCity1"],
                    "DistrictOfficeState": CM_DATA["PersonState1"],
                    "DistrictOfficeZip": CM_DATA["PersonZip1"],
                    "DistrictOfficePhone": CM_DATA["PersonPhone"],
                    "DistrictOfficeFax": CM_DATA["PersonFax"],
                    "Email": CM_DATA["PersonEmail"],
                    "LegislativeOfficeAddress": CM_DATA["PersonAddress2"],
                    "LegislativeOfficeCity": CM_DATA["PersonCity2"],
                    "LegislativeOfficeState": CM_DATA["PersonState2"],
                    "LegislativeOfficeZip": CM_DATA["PersonZip2"],
                    "LegislativeOfficePhone": CM_DATA["PersonPhone2"],
                    "LegislativeOfficeFax": CM_DATA["PersonFax2"],
                }
                DICT_ROW.update(CM_ROW)
                writer.writerow(DICT_ROW)
                JSON_LIST.append(DICT_ROW)
        JSON_FILE = open(os.path.join(os.getcwd(),'council_members/members.json'), 'w')
        json.dump(JSON_LIST, JSON_FILE, indent=2)
        print('List of all council members in current session created in JSON and CSV.')

    elif sys.argv[1] == "check":
        with open('cm_master_file.json') as json_data:
            JSON_FILE = json.load(json_data)
        with open('cm_master_file.geojson') as geojson_data:
            GEOJSON_FILE = json.load(geojson_data)
        print("There are {} records in this JSON".format(len(JSON_FILE)))
        print("There are {} records in this GEOJSON".format(len(GEOJSON_FILE["features"])))
    else:
        print("Please state a command:\n'convert' - Converts CSV to JSON\n'legistar' - Merges Legistar data with JSON\n'json' - Adds City Planning data to JSON\n'geojson' - Appends JSON to City Planning's GeoJSON")
else:
    print("Please state a command:\n'convert' - Converts CSV to JSON\n'legistar' - Merges Legistar data with JSON\n'json' - Adds City Planning data to JSON\n'geojson' - Appends JSON to City Planning's GeoJSON")
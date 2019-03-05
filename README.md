# NYC City Council District and Council Member Information
Council Member District Information
<br>
[Council.nyc.gov/districts/](https://council.nyc.gov/districts)

## District Data
  ### The Commands:
  1. While in the `district_data` directory, run `python districts.py convert`.
    - This command will create the `single_district_json` and `single_district_geojson` directories if they do not exist.
    - It will also create the CSV source file (downloading it from a Google Sheet) if it does not exist.
    - Finally, the command will convert the CSV to a JSON file.
  2. `python districts.py legistar` will merge the master JSON file with the following datasets from [Legistar](http://webapi.legistar.com/Home/Examples):
    - Person data - personal and contact information for each council member.
    - Committee data - all committees the council member is on during the current session.
  3. `python districts.py json` will do the following:
    - Merge GeoJSON data from [City Planning](https://www1.nyc.gov/site/planning/data-maps/open-data/districts-download-metadata.page) to the master JSON file.
    - Create separate files for each district in the `single_district_json` directory.
  4. `python districts.py geojson` will do the reverse of Step 3:
    - Merge the master JSON file with the GeoJSON from [City Planning](https://www1.nyc.gov/site/planning/data-maps/open-data/districts-download-metadata.page)
    - Create separate files for each district in the `single_district_geojson` directory.
  4. `python districts.py check` will just confirm that there are 51 objects in the JSON and GeoJSON.

  NOTE: Each command is dependent on the previous command as it assumes the files made from previous commands exist.

  ### Coming Soon
  * Script will prompt you for the GeoJSON URL so that everything will be dynamic.

<!-- ## Constituent Data
  ### The Commands:
  1. Run `python constituents.py` to retrieve and download the latest CSV of constituent service data from the [OpenData Portal](#)
    * This command will organize and next all constituent service request by the district number.
    * This command will also break out all constituent service requests into individual files by district. -->
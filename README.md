# B.DeVries Final Project 507

This program will accept either a list of licenses or a .csv (current_licenses.csv) and create a database of scraped data from the state of Michigan Licensing and Regulatory affairs (LARA) website.

Once per day, if the program is run, it will update its definitions by scraping a new set of data from all available / non-ignored licenses.

running app.py will create a webserver at localhost:5000 that will add the ability to make the database interactive.

Data Sources Used:
- the Michigan Licensing and Regulatory Affairs Website (https://w2.lara.state.mi.us/VAL/License/Search).
- There are no API or client secrets required
- To directly pull licensing information though, you will need a "LARA ID number" (this program will search/supply this value)

Pointers for Running this Program:
- Pretty much all you need to do is run 'app.py'.
- THe program will self initialize the database upon running any of the files (model.py / model_test.py / app.py)

Important Data functions:
- data_check - this is automatically called on all programming files.  It will create/update the database (no more than once daily) as neeeded
- edit_reputation - will update or create specific rows in the Reputation table of the database
- edit LicenseData - same as edit_reputation but for the LicenseData table.
- db_init - will completely remove/recreate the database from the CACHE file.
- The primary way data is created for output is via the Report Class.  THis is only used by the flask module, however and therefore is only used by app.py

User guide
- Note: this will run with the standard modules from this class.
- THe best way to interact with the program is to simply run app.py.

License Dashboard/ Home
- Once app.py is run, you will be on the main page/index.  It is the dashboard for the entire program; any licenses which have one or more errors/warnings (e.g. license expired, complaints, or disciplinary info will show up here).
- Tracked licenses is the count of every type of license being recorded in the database.

Results
- Is a detailed view of the data saved within the database.
- clicking the download link will create a CSV file in your local directory of the data.

Edit Entries
- Ability to add new entries or edit existing entries.
- Note: you MUST provide data for ALL fields.  ANYTHING put into the editing fields will be sent to the database (including the default 'false')



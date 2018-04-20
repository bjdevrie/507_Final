# B.DeVries Final Project 507

This program will accept either a list of licenses or a .csv (current_licenses.csv) and create a database of scraped data from the state of Michigan Licensing and Regulatory affairs (LARA) website.

Once per day, if the program is run, it will update its definitions by scraping a new set of data from all available / non-ignored licenses.

running app.py will create a webserver at localhost:5000 that will add the ability to make the database interactive.

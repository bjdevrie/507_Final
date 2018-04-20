from model import *
import unittest
import os
import csv

# print(model.parse('1640587'))
class TestDatabase(unittest.TestCase):

    def test_scraping(self):
        Abney_License = '6801081460' # Regina Abney - no warnings
        Higgins_License='6801067165' #Tom Higgins - will have warnings
        Abney_LARA= LARA_ID_request(Abney_License)
        Higgins_LARA =LARA_ID_request(Higgins_License)
        Abney_Parse= parse(Abney_LARA)
        Higgins_Parse = parse(Higgins_LARA)
        self.assertEqual(Abney_LARA, '1640587')
        self.assertEqual(Higgins_LARA, '276087')
        self.assertEqual(len(Abney_Parse.keys()),13)
        self.assertEqual(len(Higgins_Parse['warning']),2)
        self.assertEqual(len(Higgins_Parse.keys()),13)
        self.assertEqual(type(Higgins_Parse['warning']), type([]))
        self.assertEqual(Abney_Parse['warning'],False)
        self.assertEqual(Abney_Parse['status'],'Active')
        self.assertEqual(Higgins_Parse['status'],'Voluntary Termination')


    def test_db_creation(self):
        data_check()
        licenses = get_licenses_from_db()
        warnings = get_warnings()
        self.assertEqual(isinstance(licenses,list), True)
        self.assertFalse(len(licenses) == 0)
        self.assertFalse(len(warnings) == 0)
        self.assertEqual(isinstance(warnings,list), True)

    def test_db_editing(self):

        '''
        Reputation Table
        '''
        Higgins_License='6801067165'
        updated_license = '8675309'
        #ensure this license does not exist in db
        edit_reputation(Higgins_License, term=True)
        self.assertEqual(check_if_data_exists(Higgins_License)[0], False)

        #add Higgins to DB
        edit_reputation(Higgins_License, init=True)
        self.assertEqual(check_if_data_exists(Higgins_License)[0], True)
        edit_reputation(Higgins_License, Ignore = 1)
        self.assertEqual(retrieve_data(Higgins_License, 'Reputation')[1],Higgins_License)
        self.assertEqual(retrieve_data(Higgins_License, 'Reputation')[6],1) #ensure Ignore = 1
        edit_reputation(Higgins_License, Ignore='Hello')
        self.assertEqual(retrieve_data(Higgins_License, 'Reputation')[6],1) #ensure Ignore still = 1
        edit_reputation(Higgins_License, Ignore=0)
        self.assertEqual(retrieve_data(Higgins_License, 'Reputation')[6],0)
        edit_reputation(Higgins_License, Ignore=1, Name='Joe Bob') # test multiple edits
        self.assertEqual(retrieve_data(Higgins_License, 'Reputation')[6],1) #ensure Ignore still = 1
        self.assertEqual(retrieve_data(Higgins_License, 'Reputation')[3],'Joe Bob')
        edit_reputation(Higgins_License, new_license=updated_license)
        self.assertEqual(retrieve_data(updated_license, 'Reputation')[1],updated_license)
        edit_reputation(updated_license, term=True)  #neither new_license or Higgins license should be in DB
        self.assertEqual(check_if_data_exists(Higgins_License)[0], False)
        self.assertEqual(check_if_data_exists(updated_license)[0], False)

        '''
        LicenseData Table
        '''

        # edit_licenseData

        '''
        Database Cleanup
        '''
        #remove license from DB
        edit_reputation(Higgins_License, term=True)
        self.assertEqual(check_if_data_exists(Higgins_License)[0], False)

unittest.main()

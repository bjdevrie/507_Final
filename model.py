import csv
from bs4 import BeautifulSoup as BS
import requests
import sqlite3 as sql3
import json
import datetime

"""
Core Definitions
"""

DBNAME = 'license.db'
CACHE_FNAME = 'cache.json'
now = str(datetime.datetime.now()).split()[0]  #Today's date as string 'YYYY-MM-DD'

"""
Class
"""
#when a report is generated on the website, the results are also loaded into a class in case the results want to be downloaded as a csv
class Report():
    def __init__(self, title=None, test=None, type=None, fileName=None, License=None, id=None, table=None):
        self.title = title
        self.type = type
        self.fileName= fileName
        self.error=False
        if self.title == None:
            self.title = self.type
        if self.fileName==None:
            self.fileName = self.type

        if test == 'all':
            self.headers = ['Name','License Number', 'Issue Date', 'Link', 'License Expiration']
            self.fileName='All_data'
            self.data = qry_results()

        if test == 'results':
            self.headers = ['Name','License Number', 'Issue Date', 'Link', 'License Expiration']
            self.data = qry_results(type=self.type)

        if test == 'License':
            License=str(License)
            licList = get_licenses_from_db()
            if License in licList:
                self.headers = {'Reputation': ['License Number','LARA Number','NAME','License Type', 'Issue Date', 'Ignore', 'Edit Data'],'LicenseData':['DataDate','License Status', 'License Expiration', 'Warnings', 'Url', 'Address','Ignore']}
                repData=retrieve_data(License, 'Reputation')
                dates =  get_dates()
                licData = []
                for i in dates:
                    try:
                        licData.append(retrieve_data(License, 'LicenseData', date=i))
                    except:
                        pass
                self.data = {'Reputation':repData, 'LicenseData':licData}
            else:
                self.data=None
                self.headers=None
                self.error = True

        if test == 'Edit':
            self.table = table
            self.id = id
            self.data = ret_ID(self.table,self.id)



    def write_rpt(self):
        self.fileName += '.csv'
        with open (self.fileName,'w',newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(self.headers)
            for row in self.data:
                writer.writerow(row)

    def get_data(self):
        return self.data

    def get_headers(self):
        return self.headers

"""
CACHE / Data Collection Functions
"""

try:
    with open(CACHE_FNAME,'r') as fcacheref:
        CACHE = json.loads(fcacheref.read())
except:
    CACHE = {}
if 'Avail_Data_Dates' not in CACHE.keys():
    CACHE['Avail_Data_Dates']=[]
#param: None
#returns: None.  This simply saves the cache to a file
def write_cache():
    if len(CACHE.keys()) != 0:
        with open (CACHE_FNAME,'w') as cf:
            json.dump(CACHE,cf)

#param: a Michigan License Number, optional include "forceupdate=True" as param to overwrite cache
#return: the mapped "LARA ID Number" / the internal identifier the Michign agency uses to store license data.  Note, this will ignore any LARA ID Numbers that might return for a clinician which is not the one being searched for
def LARA_ID_request(LicenseNumber, CKey='License_LaraID', forceupdate=False, init=False):
    url='https://w2.lara.state.mi.us/VAL/License/Search'
    c_key=url+'/'+str(LicenseNumber)
    if init == False:
        if CKey not in CACHE.keys():
            pass
        else:
            try:
                conn = sql3.connect(DBNAME)
                cur = conn.cursor()
                cur.execute('''
                SELECT LARANumber
                FROM Reputation
                WHERE LicenseNumber = ?
                ''',(LicenseNumber,))
                val= cur.fetchone()[0]
                conn.close()
                return val
            except:
                pass
    if CKey not in CACHE.keys():
        CACHE[CKey] = {}
    if c_key in CACHE[CKey].keys():
        if forceupdate != True:
            return CACHE[CKey][c_key]
    else:
        payload = {
            '_RequestVerificationToken':'',
            'City':'',
            'CountyName':'Any',
            'CurrentPage':0,
            'FirstName':'',
            'IsBusiness':1,
            'LastName':'',
            'LicenseNumber':LicenseNumber,
            'LicenseTypeId':100,
            'ProfessionalId':0,
            'SpecialtyId':0,
        }
        r=requests.post(url, payload)
        if r.status_code == 200:
            page_soup = BS(r.text,"html.parser")
            returnList=[]
            for link in page_soup.findAll('a',href=True):
                returnList.append(link)
            for link in returnList:
                if str(LicenseNumber) == str(link.text):
                    CACHE[CKey].update({c_key:str(link['href'].split('/')[-1])})
                    return CACHE[CKey][c_key]
            CACHE[CKey].update({c_key:None})
            return CACHE[CKey][c_key]
        else:
            print(r.status_code, r.reason)
            return False

#Param: 'Internal LARA ID number' optional include "forceupdate=True" as param to overwrite cache
#Return: dictionary of website fields
def parse(LARA_ID, forceupdate=False, now=now, writeCache=True):
    #will abort the search if value inaccurate
    if LARA_ID == False:
        return False
    #Function Definitions:
    base_url='https://w2.lara.state.mi.us/VAL/License/Details/'
    url=base_url+str(LARA_ID)
    c_key='LARA_ID_PARSE_'+str(LARA_ID)

    #set warning flag to false
    warning=False
    #init key if required
    if c_key not in CACHE.keys():
        CACHE[c_key]={}
    #check to see if a recent search was made:
    if now in CACHE[c_key].keys():
        if forceupdate != True:
            return CACHE[c_key][now]
    else:
        req = requests.get(base_url+LARA_ID)
        page_soup = BS(req.text, 'html.parser')
        #license Number
        try:
            lic_num= page_soup.find('div',{'id':'permanentId'})
            i= lic_num.find('span',{'class':'detailItem'})
            lic_num= i.get_text().strip()
        except:
            lic_num=''

        #License Name
        try:
            lic_name = page_soup.find('div',{'id':'personName'}).contents[3].get_text().strip()
        except:
            lic_name=''
        #expiration
        try:
            lic_exp= page_soup.find('div',{'id':'licenseExpirationDate'}).contents[5].get_text().strip()
        except:
            lic_exp=''
        #complaints
        try:
            complaints = page_soup.find('div',{'id':'complaintsAndDisciplineContainer'}).contents[1].get_text().strip()
            complaints = complaints.split()
            complaints = complaints[3]
        except:
            complaints =''
        #license Type:
        try:
            type=page_soup.find('div',{'id':'licenseType'}).contents[3].get_text().strip()
        except:
            type=''
        #License Status
        try:
            status=page_soup.find('div',{'id':'licenseStatus'}).contents[5].get_text().strip()
        except:
            status=''
        #Issue Date
        try:
            issue = page_soup.find('div',{'id':'licenseIssueDate'}).contents[5].get_text().strip()
        except:
            issue =''

        #Specialties:
        try:
            #set names
            specialtyContainer = page_soup.find('div',{'id':'specialties'})
            sc_names=[]
            for i in specialtyContainer.find_all('span',{'class':'detailItem'}):
                sc_names.append(i.get_text().strip())
            #set issue dates
            sci= page_soup.find('div',{'id':'specialtyIssueDates'})
            sc_issue=[]
            for i in sci.find_all('span',{'class':'detailItem'}):
                try:
                    sc_issue.append(i.get_text().strip())
                except:
                    sc_issue.append(None)
            #set expirations
            sc_exp=[]
            sce= page_soup.find('div',{'id':'specialtyExpirationDates'})
            for i in sce.find_all('span',{'class':'detailItem'}):
                try:
                    sc_exp.append(i.get_text().strip())
                except:
                    sc_exp.append(None)

            #concatenate
            specialties={}
            for i in range(len(sc_names)):
                try:
                    specialties.update({sc_names[i]:{'issueDate':sc_issue[i],'expirationDate':sc_exp[i]}})
                except:
                    pass
        except:
            specialties=None

        #Discipline
        try:
            #set Discipline Action
            d_act = page_soup.find('div',{'id':'disciplinaryActions'})
            d_act_list=[]
            for i in d_act.find_all('span',{'class':'detailItem'}):
                d_act_list.append(i.get_text().strip())
            #set Date of Action
            d_doa = page_soup.find('div',{'id':'disciplineStarts'})
            d_doa_list = []
            for i in d_doa.find_all('span',{'class':'detailItem'}):
                try:
                    d_doa_list.append(i.get_text().strip())
                except:
                    d_doa_list.append(None)
            #set Date of Compliance
            d_doc = page_soup.find('div',{'id':'disciplineEnds'})
            d_doc_list = []
            for i in d_doc.find_all('span',{'class':'detailItem'}):
                try:
                    d_doc_list.append(i.get_text().strip())
                except:
                    d_doc_list.append(None)
            #concatnate
            discipline={}
            for i in range(len(d_act_list)):
                try:
                    discipline.update({d_act_list[i]:{'disciplineStarts':d_doa_list[i],'disciplineEnds':d_doc_list[i]}})
                except:
                    pass
        except:
            discipline = None
        #Address
        try:
            address= page_soup.find('div',{'id':'personAddress'})
            i= address.find('span',{'class':'detailItem'})
            address= i.get_text().strip()

            eval_add=address.split(',')

            address=str(eval_add[0])
            eval_add = eval_add[1].strip()
            eval_add = eval_add.split(' ')
            address += ', '+str(eval_add[0])+' '
            zip = eval_add[1]
            if len(zip)<7:
                address += str(zip)
            else:
                address += str(zip[:5])+'-'+str(zip[5:])

        except:
            address=''

        #Flag for Warnings
        if complaints != 'None' or status != 'Active':
            warning = []
            if complaints !='None':
                warning.append('Complaints section is not "None"')
            if status != 'Active':
                warning.append('License Status is {}'.format(status))
        if discipline != None:
            acc=0
            for k in discipline.keys():
                val =discipline[k]['disciplineEnds']
                if  val == '':
                    acc+=1
                else:
                    try:
                        val = val.split('/')
                        comp_val = now.split('-')

                        #check to see if discipline has ended
                        if datetime(val[0],val[1],val[2]) <= datetime(comp_val[0],comp_val[1],comp_val[2]):
                            pass
                        else:
                            acc+=1

                    except:
                        pass
            if acc >0:
                if warning == False:
                    warning =[]
                warning.append('One or more unresolved "Disciplinary Actions" against this clinician')
        if lic_num== '' and complaints=='' and lic_exp =='' and type=='' and address=='':
            ignore = 1
            warning.append('No data found for License Number')
        else:
            ignore = 0

        CACHE[c_key].update({now:{
            'licenseNum':lic_num,
            'complaints':complaints,
            'expiration':lic_exp,
            'name':lic_name,
            'url':url,
            'warning':warning,
            'type':type,
            'status':status,
            'issue':issue,
            'specialties':specialties,
            'discipline':discipline,
            'address':address,
            'ignore':ignore
        }})
        if writeCache == True:
            write_cache()

    return CACHE[c_key][now]

"""
Database Functions
"""

#required for edit_reputation and edit_licenseData
def ignore(id, table, val):
    try:
        if int(val) not in [0,1]:
            return False
    except:
        return False
    conn = sql3.connect(DBNAME)
    cur = conn.cursor()
    cur.execute('''
    UPDATE {}
    SET Ignore = {}
    WHERE Id = {}
    '''.format(table,val,id)
    )
    conn.commit()
    conn.close()

#requried for edit_Reputation & LicenseData
def delete_row(id,table):
    conn = sql3.connect(DBNAME)
    cur = conn.cursor()
    cur.execute('''
    DELETE
    FROM {}
    WHERE Id = {}
    '''.format(table,id)
    )
    conn.commit()
    conn.close()

#return: all warning messages for all staff
def get_warnings():
    conn = sql3.connect(DBNAME)
    cur = conn.cursor()
    cur.execute('''
    SELECT R.Name, L.Warnings, L.Url, L.DataDate
    FROM LicenseData AS L
    JOIN Reputation AS R
        ON R.Id = L.RepId
    WHERE L.DataDate = ? AND L.Warnings <> "False" AND L.Ignore = 0
    ''',(now,))
    data = cur.fetchall()
    retList = []
    conn.close()
    return data

#return: sorted (ascending) list of all license numbers in database:
def get_licenses_from_db(DBNAME=DBNAME):
    conn = sql3.connect(DBNAME)
    cur = conn.cursor()
    cur.execute('''
    SELECT LicenseNumber
    FROM Reputation
    WHERE Ignore = 0
    ''')
    data= cur.fetchall()
    retList=[]
    for i in data:
        retList.append(i[0])
    conn.close()
    retList.sort()
    return retList

#param - License Number
#return - the corresponding ID from the reputation table or None if it doesn't exist
def get_rep_id_from_db(LicenseNumber):
    LicenseNumber=str(LicenseNumber)
    conn = sql3.connect(DBNAME)
    cur = conn.cursor()
    try:
        cur.execute('''
        SELECT Id
        FROM Reputation
        WHERE LicenseNumber is {}
        '''.format(LicenseNumber))
        data= cur.fetchone()
        conn.close()
        return data[0]
    except:
        conn.close()
        return None

def get_licenseData_id_from_db(LicenseNumber,Date=now):
    LicenseNumber=str(LicenseNumber)
    rId = get_rep_id_from_db(LicenseNumber)
    if rId == False:
        return False
    conn = sql3.connect(DBNAME)
    cur = conn.cursor()
    try:
        cur.execute('''
        SELECT Id
        FROM LicenseData
        WHERE RepId = {} AND DataDate = "{}"
        '''.format(rId,Date))
        data= cur.fetchone()
        conn.close()
        return data [0]
    except:
        conn.close()
        return None

#param License Number, table
#Returns [True,[values]] if value exists, [False] if not
def check_if_data_exists(LicenseNum,table='Reputation',date=''):
    LicenseNum=str(LicenseNum)
    conn = sql3.connect(DBNAME)
    cur = conn.cursor()
    if table =='Reputation':
        cur.execute('''
        SELECT *
        FROM {}
        WHERE LicenseNumber= {}
        '''.format(table,LicenseNum))
    if table == 'LicenseData':
        lId = get_licenseData_id_from_db(LicenseNum,Date=date)
        try:
            cur.execute('''
            SELECT *
            FROM {}
            WHERE Id = {}
            '''.format(table,lId))
        except:
            conn.close()
            return[False]
    val= cur.fetchall()
    conn.close()
    try:
        if len(val) >0:
            return [True,val[0]]
        else:
            return [False]
    except:
        return[False]

#param: license number
#return: False if error, else None
def edit_reputation(LicenseNum,
    LARANumber=False,
    Name=False,
    LicenseType=False,
    IssueDate=False,
    Ignore='',
    DBNAME=DBNAME,
    init=False,
    new_license=False,
    term=False
    ):

    LicenseNum=str(LicenseNum)

    param_dict ={
        'new_license':new_license,
        'LARANumber':LARANumber,
        'Name':Name,
        'LicenseType':LicenseType,
        'IssueDate':IssueDate,
    }
    if term== True:
        if check_if_data_exists(LicenseNum)[0] == True:
            rId = get_rep_id_from_db(str(LicenseNum))
            delete_row(rId, 'Reputation')
            return None
        else:
            return None

    if init == False:
        oldData= check_if_data_exists(LicenseNum)
    else:
        oldData=[False]
    conn = sql3.connect(DBNAME)
    cur = conn.cursor()
    if oldData[0] == False:
        try:
            lID = LARA_ID_request(LicenseNum)
            if lID == None:
                return False
            else:
                try:
                    data = parse(lID)
                    cur.execute("""
                        INSERT INTO Reputation
                        VALUES(?,?,?,?,?,?,?)
                    """, (None,data['licenseNum'],str(lID),data['name'],data['type'],data['issue'],0)
                    )
                    conn.commit()
                except:
                    return False
        except:
            return False

    if oldData[0] == True:
        try:
            rId = get_rep_id_from_db(str(LicenseNum))
        except:
            return False
        if Ignore != '':
            ignore(rId, 'Reputation', Ignore)
        if all(value == False for value in param_dict.values()) == False:
            set_values=[]
            if LARANumber != False:
                set_values.append('LARANumber = "{}"'.format(str(LARANumber)))
            if Name != False:
                set_values.append('Name = "{}"'.format(str(Name)))
            if LicenseType != False:
                set_values.append('LicenseType = "{}"'.format(str(LicenseType)))
            if IssueDate != False:
                set_values.append('IssueDate = "{}"'.format(str(IssueDate)))
            if new_license != False:
                set_values.append('LicenseNumber = {}'.format(str(new_license)))
            if len(set_values) != 0 :
                set_str = 'SET '
                for value in set_values:
                    v= str(value)+', '
                    set_str+=v
                set_str=set_str[:-2]
                cur.execute("""
                    UPDATE Reputation
                    {}
                    WHERE Id = {}
                """.format(set_str,rId))
                conn.commit()

    conn.close()

#param: license number
#return: False if error, else None
def edit_licenseData(LicenseNum,
    RepId=False,
    DataDate=now,
    LicenseStatus=False,
    LicenseExpiration=False,
    Ignore='',
    Warnings=False,
    Url=False,
    DBNAME=DBNAME,
    init=False,
    new_date=False,
    term=False,
    address=False
    ):

    LicenseNum=str(LicenseNum)

    param_dict={
        'RepId':RepId,
        'DataDate':DataDate,
        'LicenseStatus':LicenseStatus,
        'LicenseExpiration':LicenseExpiration,
        'Warnings':Warnings,
        'Url':Url,
        'new_date':new_date,
        'address': address
    }
    if term== True:
        if check_if_data_exists(LicenseNum, table='LicenseData', date=DataDate)[0] == True:
            lId = get_licenseData_id_from_db(LicenseNum,Date=DataDate)
            delete_row(lId, 'LicenseData')
            return None
        else:
            return None

    if init == False:
        oldData= check_if_data_exists(LicenseNum, table='LicenseData', date=DataDate)
    else:
        oldData=[False]
    if oldData[0] == False:
        rID = str(get_rep_id_from_db(LicenseNum))
        lID = str(LARA_ID_request(LicenseNum))
        conn = sql3.connect(DBNAME)
        cur = conn.cursor()
        data = parse(lID)
        if data['warning']== False:
            warning='False'
        else:
            warning =''
            for warning_element in data['warning']:
                warning += str(warning_element)+' | '
            warning = warning[:-3]
        cur.execute("""
            INSERT INTO LicenseData
            VALUES(?,?,?,?,?,?,?,?,?)
        """, (None,str(rID),DataDate,data['status'],data['expiration'],warning,data['url'],0,data['address'])
        )
        conn.commit()
    if oldData[0] == True:
        lId= get_licenseData_id_from_db(LicenseNum,Date=DataDate)
        if Ignore != '':
            ignore(lId, 'LicenseData', Ignore)
        if all(value == False for value in param_dict.values()) == False:
            try:
                set_values=[]
                if RepId != False:
                    set_values.append('RepId = {}'.format(str(RepId)))
                if new_date != False:
                    set_values.append('DataDate = "{}"'.format(str(new_date)))
                if LicenseStatus != False:
                    set_values.append('LicenseStatus = "{}"'.format(str(LicenseStatus)))
                if LicenseExpiration != False:
                    set_values.append('LicenseExpiration = "{}"'.format(str(LicenseExpiration)))
                if Warnings != False:
                    set_values.append('Warnings = "{}"'.format(str(Warnings)))
                if Url != False:
                    set_values.append('Url = "{}"'.format(str(Url)))
                if address != False:
                    set_values.append('Address = "{}"'.format(str(address)))

                conn = sql3.connect(DBNAME)
                cur = conn.cursor()
                set_str = 'SET '
                for value in set_values:
                    v= str(value)+', '
                    set_str+=v
                set_str=set_str[:-2]

                cur_state = """
                UPDATE LicenseData
                {}
                WHERE Id = {}

                """.format(set_str,lId)
                cur.execute(cur_state)
                conn.commit()


            except:
                return False

    conn.close()

#return list of data dates from a particular source (Database by Default).  Able to return just a single list of dates for a given license # / False if error
def get_dates(init=False, src='DB', LicenseNumber=False):
    if init == True:
        src='CACHE'
    if src == 'DB':
        try:
            where=''
            if LicenseNumber != False:
                pass
            conn = sql3.connect(DBNAME)
            cur = conn.cursor()
            cur.execute('''
            SELECT DISTINCT L.DataDate
            FROM LicenseData AS L
            ''')
            data= cur.fetchall()
            conn.close()
            retList=[]
            for date in data:
                retList.append(date[0])
            return retList
        except:
            return False

    if src == 'CACHE':
        try:
            return CACHE['Avail_Data_Dates']
        except:
            return False

def retrieve_data(LicenseNumber, table, date=now):
    if table == 'Reputation':
        id = get_rep_id_from_db(LicenseNumber)

    if table == 'LicenseData':
        id = get_licenseData_id_from_db(LicenseNumber,Date=date)

    if id == None:
        return None

    conn = sql3.connect(DBNAME)
    cur = conn.cursor()
    cur.execute('''
    SELECT *
    FROM {}
    WHERE Id = {}
    '''.format(table,id))
    data = cur.fetchone()
    conn.close()
    return data

def ret_ID(table,ID):
    conn = sql3.connect(DBNAME)
    cur = conn.cursor()
    cur.execute('''
    SELECT *
    FROM {}
    WHERE Id = {}
    '''.format(table,ID))
    data = cur.fetchone()
    conn.close()
    return data


#This function is used to describe the data contained within the database - it is used by the flask application
# returns list of tuples
def retrieveLicData():
    conn = sql3.connect(DBNAME)
    cur = conn.cursor()
    cur.execute('''
    SELECT DISTINCT LicenseType, COUNT(LicenseType)
    FROM Reputation
    GROUP BY LicenseType
    ''')
    data= cur.fetchall()
    conn.close()
    return data

def qry_results(type=''):
    if type == '':
        val =''
    else:
        val = 'AND R.LicenseType = "{}"'.format(type)
    conn = sql3.connect(DBNAME)
    cur = conn.cursor()
    cur.execute('''
        SELECT DISTINCT R.Name, R.LicenseNumber, R.IssueDate, L.Url, L.LicenseExpiration
        FROM Reputation AS R
        JOIN LicenseData AS L
        ON L.RepId = R.Id
        WHERE R.[Ignore]=0 {}
        ORDER BY R.Name ASC
    '''.format(val))
    data=cur.fetchall()
    conn.close()
    return data

def get_license_from_id(id):
    conn = sql3.connect(DBNAME)
    cur = conn.cursor()
    cur.execute('''
    SELECT LicenseNumber
    FROM Reputation
    WHERE Id = {}
    '''.format(id))
    data = cur.fetchone()[0]
    return data

def get_Licenses_Id_from_Db():
    retList=[]
    Licenses=get_licenses_from_db()
    for license in Licenses:
        retList.append((license, get_rep_id_from_db(license)))
    return retList


"""
Database/CACHE integrity functions
"""

#update database (run when new data is introduced)
#params: date (default = now), licenses = list of licenses to update.  By default, this will update all non-ignored licenses in DB.
#return: False if error else None
def update_licenseData(licenses=False,date=now):
    if licenses != False:
        licenseList=licenses
    else:
        licenseList= get_licenses_from_db()
    for license_element in licenseList:
        edit_licenseData(str(license_element),DataDate=date)
    if now not in CACHE['Avail_Data_Dates']:
        CACHE['Avail_Data_Dates'].insert(0,now)

def db_init(DBNAME=DBNAME,initial_licenses=False):
    if initial_licenses == False:
        try:
            with open('current_licenses.csv',mode='r') as file_obj:
                initial_licenses = list(csv.reader(file_obj))
        except:
            return False
    conn = sql3.connect(DBNAME)
    cur = conn.cursor()
    #delete, then rebuild tables if they exist
    cur.executescript('''
        DROP TABLE IF EXISTS 'Reputation';
        DROP TABLE IF EXISTS 'LicenseData';
        CREATE TABLE 'Reputation' (
            'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
            'LicenseNumber' TEXT,
            'LARANumber' TEXT,
            'Name' TEXT,
            'LicenseType' TEXT,
            'IssueDate' TEXT,
            'Ignore' INTEGER
            );
        CREATE TABLE 'LicenseData' (
            'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
            'RepId' INTEGER,
            'DataDate' TEXT,
            'LicenseStatus' TEXT,
            'LicenseExpiration' TEXT,
            'Warnings' TEXT,
            'Url' TEXT,
            'Ignore' INTEGER,
            'Address' TEXT
        );
    ''')
    conn.commit()

    #Initialize Reputation Table
    try:
        for row in initial_licenses:
            try:
                edit_reputation(row[0], init=True)
            except:
                print ('Error writing {}'.format(str(row[0])))
                pass

    except:
        print ('Error Reading initial license data - ensure data is list of strings.  Exiting Program')
        conn.close()
        quit()

    conn.commit()

    #Initialize LicenseData Table
    licList = get_licenses_from_db(DBNAME)
    dateList = get_dates(init=True)
    for license in licList:
        license = str(license)
        rId = get_rep_id_from_db(str(license))
        for date in dateList:
            edit_licenseData(license, init=True, DataDate=date)

    conn.commit()

    conn.close()

#checks to ensure data is up to date / rebuilds db as necessary
def data_check(DBNAME = DBNAME, date=now):
    try:
        conn = sql3.connect(DBNAME)
        cur = conn.cursor()
        cur.execute('''
        SELECT COUNT(*)
        FROM Reputation
        ''')
        val = cur.fetchone()[0]
        cur.execute('''
        SELECT COUNT(*)
        FROM LicenseData
        ''')
        val2 = cur.fetchone()[0]
        conn.close()
        if  val == 0 or val2 == 0:
            db_init()
    except:
        db_init()
    dates = get_dates()
    if date not in dates:
        update_licenseData(date=date)
    if date not in CACHE['Avail_Data_Dates'] and date == now:
        CACHE['Avail_Data_Dates'].insert(0,date)
        write_cache()

def edit_cache(LicenseNumber, type='parse', date=now, term=False):
    License=str(LicenseNumber)
    if type == 'parse':
        lId = LARA_ID_request(License)
        key = 'LARA_ID_PARSE_'+str(lId)
        if term == True:
            try:
                del CACHE[key][date]
            except:
                pass

if __name__=="__main__":
    data_check()

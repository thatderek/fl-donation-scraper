# A Python script for scraping information from the Florida Division of 
# Elections donor database, compiling it, and storing that data in a database.

import requests
import tablib
import json
import re

from bs4 import BeautifulSoup

class queryDOE:
    """Queries the Florida Division of Elections for Contribution Records"""
    
    def __init__(self):
        self.ContributionPage = 'http://election.dos.state.fl.us/cgi-bin/contrib.exe'
        self.PostDict = {'election': 'All',   # REQ, YYYYMMDD-GEN|S01|S02
                'CanFName': '',      # max 20 char
                'CanLName': '',      # max 30 char
                'CanNameSrch': '1',  # 1:LName Containes, 2:Starts W, 3:Sounds like
                'office': 'All', 
                #All, PRE, USS, USR, GOV, SEC (Sec of State), ATG, CMP, CFO, TRE, 
                #EDU, AGR, STA (StAtty), PUB (PublicDef), STS, STR, SCJ, DCA, CTJ
                'cdistrict': '',     # Circuit/Dist, Max 3 char
                'cgroup': '',        # max 3 char
                'party': 'All',      # All,DEM,IND (npa),NOP (non-part off), REP... 
                'search_on': '',     
                # Candidate:3 Contribution Totals, 2 List
                # Commitee: 5 Totals, 4 List
                'ComName': '',       # max 30 char
                'ComNameSrch': '2',   # 1:NameContains, 2:StartsW, 3:SoundsLike
                'committee': 'All',  # All, CCE, ECO, PAC, PAP, PTY 
                'cfname': '',        # Contributor First Name, max 20
                'clname': '',        # Contributor Last Name, max 30
                'namesearch': '2',   # LastName 1:Contains, 2:StartsW, 3:Sounds
                'ccity': '',         # Contributor City, max 20
                'cstate': '',        # Contributor State, max 2
                'czipcode': '',      # Contributor Zip, max 5
                'coccupation': '',   # Contributor Occupation, max 20
                'cdollar_minimum': '',# $, max 12
                'cdollar_maximum': '',# $, max 12
                'rowlimit': '7500',  # max 5
                'csort1': 'DAT',     # Sort Contribs by AMT DAT NAM CAN
                'csort2': 'CAN',     # Sort Contribs by AMT DAT NAM CAN
                'cdatefrom': '',     # MM/DD/YY
                'cdateto': '',       # MM/DD/YY
                'queryformat': '2',  # 1 Screen, 2 Tab Delimited File
                'Submit': 'Submit'   # 
                }
        self.Elections =[
            u'20181106-GEN',u'20161108-GEN',u'20141104-GEN',u'20140311-S01',
            u'20131015-S01',u'20130611-S01',u'20121106-S03',u'20121106-S01',
            u'20121106-GEN',u'20111018-S01',u'20110628-S01',u'20110301-S01',
            u'20101102-GEN',u'20100413-S02',u'20100413-S01',u'20100223-S01',
            u'20091006-S01',u'20090922-S01',u'20090804-S01',u'20081104-GEN',
            u'20080415-S01',u'20080304-S01',u'20080226-S01',u'20080129-PPP',
            u'20071120-S01',u'20071106-S01',u'20070918-S01',u'20070626-S01',
            u'20070424-S01',u'20070227-S01',u'20061107-GEN',u'20050614-S01',
            u'20050308-S01',u'20041102-GEN',u'20040127-S01',u'20031007-S01',
            u'20030513-S01',u'20030325-S01',u'20021105-GEN',u'20011016-S01',
            u'20010925-S01',u'20010821-S01',u'20001107-GEN',u'20000425-S01',
            u'20000125-S01',u'19991102-S02',u'19991102-S01',u'19990309-S01',
            u'19981103-GEN',u'19980317-S01',u'19980310-S01',u'19971021-S01',
            u'19961105-S02',u'19961105-S01',u'19961105-GEN',u'19960427-S01',
            ]
        self.CandidateTableHeaders = (u'Candidate Name', u'Party', 
                                      u'Office', u'District', u'Group', 
                                      u'Total Amount', u'Election')
        self.CommitteeTableHeaders = (u'Committee Name', u'Type',
                                      u'Total Amount')
        self.ContribsTableHeaders = (u'Candidate/Committee', u'Date', 
                                     u'Amount', u'Typ', u'Contributor Name', 
                                     u'Address', u'City State Zip', 
                                     u'Occupation', u'Inkind Desc', u'Election')
        pass
    def alternateQuery(self, params):
        """ Backup query if there is an error with query(), parses html and returns tablib obj"""
        post_params = params
        post_params.update({'queryformat': '1'})
        response = requests.post(self.ContributionPage, params=post_params)
        response = BeautifulSoup(response.content)
        # <pre> is the tag used by the DOE to denote the part of the page that contains the relevant data.
        template = response.find('pre').b.string.split()[13:]
        temp_template = [len(x) for x in template]
        counter = 0
        template = []
        for x in temp_template:
            counter = counter + x
            template.append(counter)
        unparsed = [x for x in response.find('pre')][2]
        parsed = []
        returned_strings = [x for x in unparsed.split('\r\n')][1:-4]
        temp_data = tablib.Dataset()
        temp_data.headers = self.ContribsTableHeaders
        temp_data.headers.pop()
        print temp_data.headers
        for string in returned_strings:
            returnable = []
            y = 0
            counter = 0
            for x in template:
                # this monstrosity moves the cursor the appropriate length to parse the html. I expect this will be the first thing that breaks. Any update to the generated page will probably kill this function.
                returnable.append(string[y+counter:x+counter].strip())
                returnable.append(string[y+counter:x+counter].strip())
                counter += 1
                y = x 
            temp_data.append(tuple(returnable))
        post_params.update({'queryformat': '2'})
        return temp_data
        
    def query(self, params):
        """ Queries the Division of Elections site and returns a tablib obj"""
        post_params = self.PostDict
        post_params.update(params)
        response = requests.post(self.ContributionPage, params=post_params)
        # Effing windows dumbness, cp1252 is by best guess for this. so dumb.
        r = response.content.decode('cp1252').encode('utf8')
        with open('temp.tsv', 'w') as file:
            file.writelines(r)
        temp_data = tablib.Dataset()
        while True:
            try:
                temp_data.tsv = r
                break
            except: 
                # if the .tsv has errors, run the alternate query
                print "!!!ERROR!!!"
                print post_params
                temp_data = self.alternateQuery(post_params)
                break
        return temp_data
        
    
    def removeNameExtras(self, name):
        """Names have characters that break the DOE's search; 
this returns a name with those removed."""
        bad_things = re.compile(r",| jr.?$| sr.?$| iii$| ii$| i$| iv$| 
                               v$|[A-Za-z]'|jr.$|\(.+\)", re.IGNORECASE)
        name = bad_things.sub("", name)
        return name
        
    def addElectionColumn(self, temp_data, data, election):
        """Adds a column with default values to a tablib object and returns that tablib object"""
        election_col = ()
        # if the object doesn't have any rows, then don't add column. 
        if len(temp_data) > 0:
            for i in range(len(temp_data)):
                election_col = election_col + (election, )
            temp_data.append_col(election_col, header=u'Election')
            data = data.stack(temp_data)
        return data
        
    def getCandidates(self):
        """Gets a list of candidates and writes it to candidates.csv"""
        data = tablib.Dataset()
        
self.CommitteeTableHeaders
        params = {'search_on':'5'}
        data = self.query(params)
        with open('committees.csv', 'w') as file:
            file.writelines(data.csv)
            
    def getCandidateContributions(self):
        """Requests list of contributions for each candidate in candidates.csv"""
        data = tablib.Dataset()
        data.headers = self.ContribsTableHeaders
        data_temp = tablib.Dataset()
        receptical = ''
        with open('candidates.csv', 'r') as candidates:
            for line in candidates.readlines():
                receptical = receptical + line
            data_temp.csv = receptical
        counter = 0
        for candidate in data_temp.dict:
            counter += 1
            cname = self.removeNameExtras(candidate['Candidate Name'])
            clastname = cname[cname.rfind(' '):]
            party, election = candidate['Party'], candidate['Election']
            office, group = candidate['Office'], candidate['Group']
            district = candidate['District']
            params = {'search_on':'2', 'CanLName':clastname,
                      'party':party, 'election':election, 
                      'office':office, 'cgroup':group,
                      'cdistrict':district}
            data_dump = self.query(params)
            data = self.addElectionColumn(data_dump, data, election)
            print counter, ' - ', len(data_temp), ' - ', cname, ' - ', 'Length:',len(data_dump)
        with open('contributions.csv', 'w') as file:
            file.writelines(data.csv)
            
def main():
    p = queryDOE()
    return p.getCandidateContributions()
    pass

    

if __name__ == '__main__':
    main()

###

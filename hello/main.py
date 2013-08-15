#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import urllib
import json

from google.appengine.api import users
from google.appengine.ext import ndb
from csv import DictReader, DictWriter

import jinja2
import webapp2
import xlrd
import itertools
from sets import Set 

global url_new
url_new = ""
global topic_new
topic_new = ""

wb = xlrd.open_workbook('web_credibility_1000_url_ratings.xls')
sh = wb.sheet_by_index(0)

JINJA_ENVIRONMENT = jinja2.Environment(
	loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
	extensions=['jinja2.ext.autoescape'])


DEFAULT_GUESTBOOK_NAME = 'guestbook_name'
DEFAULT_CHOOSE_NAME = ''


# We set a parent key on the 'Greetings' to ensure that they are all in the same
# entity group. Queries across the single entity group will be consistent.
# However, the write rate should be limited to ~1/second.

def guestbook_key(guestbook_name=DEFAULT_GUESTBOOK_NAME):
    """Constructs a Datastore key for a Guestbook entity with guestbook_name."""
    return ndb.Key('Guestbook', guestbook_name)


class Greeting(ndb.Model):
    """Models an individual Guestbook entry with author, content, and date."""
    author = ndb.UserProperty()
    content = ndb.StringProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)


####################################################################

class MainPage(webapp2.RequestHandler):

    def get(self):
        guestbook_name = self.request.get('guestbook_name',DEFAULT_GUESTBOOK_NAME)
        greetings_query = Greeting.query(ancestor=guestbook_key(guestbook_name)).order(-Greeting.date)
        greetings = greetings_query.fetch(1)
        choose_name = self.request.get('choose_name',DEFAULT_CHOOSE_NAME)
        
        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template_values = {
            'greetings': greetings,
            'guestbook_name': urllib.quote_plus(guestbook_name),
            'url': url,
            'url_linktext': url_linktext,
            'choose_name' : choose_name
        }

        template = JINJA_ENVIRONMENT.get_template('templates/mypage.html')
        self.response.write(template.render(template_values))

####################################################################

class Guestbook(webapp2.RequestHandler):

    def post(self):
        # We set the same parent key on the 'Greeting' to ensure each Greeting
        # is in the same entity group. Queries across the single entity group
        # will be consistent. However, the write rate to a single entity group
        # should be limited to ~1/second.
        guestbook_name = self.request.get('guestbook_name',
                                          DEFAULT_GUESTBOOK_NAME)
        greeting = Greeting(parent=guestbook_key(guestbook_name))


        if users.get_current_user():
            greeting.author = users.get_current_user()

        greeting.content = self.request.get('content')
        greeting.put()

        query_params = {'guestbook_name': guestbook_name}
        self.redirect('/?' + urllib.urlencode(query_params))

####################################################################

class MainPage_URL(webapp2.RequestHandler):
    def get(self):
        template_values = {}
        #self.redirect('templates/main_URL.html')
        template = JINJA_ENVIRONMENT.get_template('templates/main_URL2.html')
        self.response.write(template.render(template_values))


####################################################################
class MainPage_Topic(webapp2.RequestHandler):
    def get(self):
        list_of_topics = TopicsList()
        template_values = {
        'list_of_topics' : list_of_topics,
        }
        #self.redirect('templates/main_Topic.html')
        template = JINJA_ENVIRONMENT.get_template('templates/main_Topic.html')
        self.response.write(template.render(template_values))


####################################################################

class GiveTopics(webapp2.RequestHandler):

    def get(self):
        Found, website, info = GiveMeTopic(self.request.get('url'))
        global url_new, topic_new

        if Found:
            topic = info[0]
            subject = info[1]
            credibility = info[4]
            template_values = {
                'topic': topic,
                'subject' : subject,
                'credibility' : credibility,
                'website' : website,
                'Found' : Found,
            }
        else:
            Flag, url_new, topic_new = alchemy_func(self.request.get('url'))
            template_values={
                'Flag' : Flag,
                'topic' : topic_new,
                'url_new' : url_new,
                'Found' : Found,
            }
            # check whether the new_url exists in the database
            if url_new:
                Found2, website2, info2 = GiveMeTopic(url_new)
                if Found2:
                    template_values = {
                        'Flag' : Flag,
                        'topic' : topic_new,
                        'url_new' : url_new,
                        'Found' : Found,
                        'topic2' : info2[0],
                        'subject2' : info2[1],
                        'credibility2' : info2[4],
                        'Found2' : Found2,
                    }

        template = JINJA_ENVIRONMENT.get_template('templates/index_topic.html')
        self.response.write(template.render(template_values))
        #self.response.write(info)

####################################################################

class GiveWebsites(webapp2.RequestHandler):

    def get(self):
        topic = self.request.get('topic')
        number = self.request.get('number')
        if topic and number:        
            websites, credibilities, webs = GiveMeWebsite(topic, number)
            template_values = {
                'websites': websites,
                'credibilities' : credibilities,
                'webs' : webs,
                'topic' : topic,
                'number' : number,
            }
        else:
            template_values={
                'topic' : topic,
                'number' : number,
            }
        template = JINJA_ENVIRONMENT.get_template('templates/index_websites.html')
        self.response.write(template.render(template_values))
        #self.response.write(webs)

####################################################################

class Finish(webapp2.RequestHandler):
    def get(self):
        grade = self.request.get('grade')
        global url_new, topic_new

        if grade:
            #modify_database(website=url_new, grade=grade, topic=topic_new, title='No title is available')
            print 'salam'
        
        template_values={
            'grade' : grade,
            'url_new' : url_new,
            'topic_new' : topic_new,
            }

        template = JINJA_ENVIRONMENT.get_template('templates/finish.html')
        self.response.write(template.render(template_values))

####################################################################

class Ranked_List_Topics(webapp2.RequestHandler):
    def get(self):
        TOPICS, MEAN, STD = Ranked_Topics()
        template_values = {
        'TOPICs' : TOPICS,
        'MEANs' : MEAN,
        'STDs' : STD,
        'num' : len(TOPICS),
        }
        template = JINJA_ENVIRONMENT.get_template('templates/topic_list.html')
        self.response.write(template.render(template_values))

#######################################################################
#######################################################################
########################### Python functions ##########################
#######################################################################
#######################################################################

def Ranked_Topics():
    m_reader = DictReader(open('data_processing/url_data.csv'))
    TOPICS = TopicsList()
    rates = []
    for j in range(len(TOPICS)):
        rates.append([])
    
    for row in m_reader:
        if row['Likert Rating - Microsoft']:
            i=0
            for topic in TOPICS:
                if row['Topic'] == topic:
                    rates[i].append(int(row['Likert Rating - Microsoft']))
                    break
                else:
                    i+=1
        else:
            continue
    MEAN = []
    STD = []

    for i in range(len(TOPICS)):
        MEAN.append(float(sum(rates[i])) / len(rates[i]))

    for i in range(len(TOPICS)):
        var = float(sum((MEAN[i] - value) ** 2 for value in rates[i])) / len(rates[i])
        STD.append( var ** 0.5)
    
 #   for i in range(len(TOPICS)):
 #       temp = np.zeros(len(rates[i]))
 #       for j in range(len(temp)):
 #           temp[j] = rates[i][j]

 #       MEAN.append(temp.mean())
 #       STD.append(temp.std())
 

    INDICES = [MEAN.index(x) for x in sorted(MEAN)]
    TOPICS = [TOPICS[i] for i in INDICES]
    MEAN = [MEAN[i] for i in INDICES]
    STD = [STD[i] for i in INDICES]

    return TOPICS[::-1], MEAN[::-1], STD[::-1]  
           

           
#######################################################################            

def alchemy_func(url):

    alchemy_key = '6c15f2ea82b0dab7bc9bbb9cda438933fdc02ea3'
    endpoint = 'http://access.alchemyapi.com/calls/url/URLGetCategory'
    params = {'url': url,
      'apikey':alchemy_key,
      'outputMode':'json'}
    alchemy_call = endpoint+'?'+urllib.urlencode(params)
    response = urllib.urlopen(alchemy_call).read()
    print response
    jresponse = json.loads(response)
    
    
    Flag = False
    url_new = ''
    topic = ''
    if jresponse['status'] == 'OK': # means that (uncomplete) url is valid 
        Flag = True
        url_new = jresponse['url']
        if jresponse.has_key('category'):
            topic = jresponse['category']

    return Flag, url_new, topic

####################################################################


def GiveMeTopic2(website):
    Found = False
    info = ''
    for rownum in range(sh.nrows):
        if sh.cell(rownum,3).value == website:
            Found = True
            info = sh.row_values(rownum)

    return Found, website, info


def GiveMeTopic(website):
    Found = False
    info = ''
    m_reader = DictReader(open('data_processing/url_data.csv'))
    for row in m_reader:
        if row['URL'] == website:
            Found = True
            info = [
            row['Topic'],
            row['Query'],
            row['Result Rank'],
            row['URL'],
            row['Likert Rating - Microsoft'] 
            ]
            break

    return Found, website, info

####################################################################

def GiveMeWebsite2(topic, number):

    list_rows = [] # which rows are celebrities
    sorted_rows = [] # a list of lists where each list contains rows of websites with same credibility
    number = int(number)

    for rownum in range(sh.nrows):
        if sh.cell(rownum,0).value == topic:
            list_rows.append(rownum)

    #print list_rows

    cred = [5, 4, 3, 2, 1]
    for i in cred:
        sorted_rows_temp = [] # temporary list
        for rownum in list_rows:
            if sh.cell(rownum, 4).value == i:
                sorted_rows_temp.append(rownum)
        sorted_rows.append(sorted_rows_temp)


    merged = list(itertools.chain.from_iterable(sorted_rows))

    websites = []
    credibilities = []
    webs = []
    for i in range(number):
        websites.append(sh.cell(merged[i], 3).value)
        credibilities.append(sh.cell(merged[i], 4).value)
        webs.append([sh.cell(merged[i], 3).value, sh.cell(merged[i], 4).value])
    return websites, credibilities, webs


def GiveMeWebsite(topic, number):

    list_rows = [] # which rows are celebrities
    sorted_rows = [] # a list of lists where each list contains rows of websites with same credibility
    number = int(number)

    m_reader = DictReader(open('data_processing/url_data.csv'))
    for row in m_reader:
        if row['Topic'] == topic:
            list_rows.append(row)

    cred = [5, 4, 3, 2, 1]
    for i in cred:
        sorted_rows_temp = [] # temporary list
        for row in list_rows:
            if row['Likert Rating - Microsoft'] == str(i):
                sorted_rows_temp.append(row)
        sorted_rows.append(sorted_rows_temp)


    merged = list(itertools.chain.from_iterable(sorted_rows))

    websites = []
    credibilities = []
    webs = []
    
    for i in range(number):
        websites.append(merged[i]['URL'])
        credibilities.append(merged[i]['Likert Rating - Microsoft'])
        webs.append([ merged[i]['URL'], merged[i]['Likert Rating - Microsoft'] ]) 
    return websites, credibilities, webs

####################################################################

def TopicsList2():
    my_list = []
    for rownum in range(sh.nrows):
        my_list.append(sh.cell(rownum, 0).value)

    b = set(my_list)
    b.remove('Topic')    
    return list(b)

def TopicsList():
    my_list = []
    m_reader = DictReader(open('data_processing/url_data.csv'))
    for row in m_reader:
        my_list.append(row['Topic'])

    b = set(my_list)
    #b.remove('topic')
    return list(b)
####################################################################

def modify_database(website, grade, topic, title='No title is available'):
    grade = int(grade)
    f = open('data_processing/mj_data3.csv', 'rb')
    m_reader = DictReader(f, delimiter=',')
    rows = [row for row in m_reader]
    Exist = False
    for row in rows:
        if row['url'] == website:
            ratings = [int(row['ratings'][2*i]) for i in range(5)]
            print ratings
            ratings[grade-1] += 1
            print ratings
            row['ratings'] = ','.join([str(r) for r in ratings])
            row['total'] = str(int(row['total']) + 1)
            Exist = True
            print row
            break
    f.close()

    g = open('data_processing/mj_data3.csv', 'wb')
    m_writer = DictWriter(g, ['topic', 'url', 'index', 'ratings', 'total', 'snapshot', 'title'])
    firstrow = {
            'topic':'topic', 
            'url': 'url',
            'index' : 'index', 
            'ratings': 'ratings', 
            'total' : 'total', 
            'snapshot' : 'snapshot', 
            'title':'title'
            }

    if Exist == True:
        m_writer.writerow(firstrow)
        m_writer.writerows(rows)
    else:
        ratings = [0, 0, 0, 0, 0]
        ratings[grade-1] += 1
        rates = ','.join([str(r) for r in ratings])

        newrow = {
        'topic': topic,
        'url': website,
        'index' : str(len(rows) + 1),
        'ratings' : rates,
        'total' : str(1),
        'snapshot' : '/static/snapshots/l/url'+str(len(rows)+1)+'.jpg',
        'title' : title
        }
        m_writer.writerow(firstrow)
        m_writer.writerows(rows)
        m_writer.writerow(newrow)

    g.close()
####################################################################

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/URL', MainPage_URL),
    ('/Topic', MainPage_Topic),
    ('/sign', Guestbook),
    ('/info', GiveTopics),
    ('/websites', GiveWebsites),
    ('/Finish', Finish),
    ('/topic_list', Ranked_List_Topics),
], debug=True)


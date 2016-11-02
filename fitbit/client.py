# -*- coding: utf-8 -*-
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import XMLParser
import json
import datetime, time

import urllib
try:
    import urllib2
except ImportError:
    import urllib.request
    import urllib.parse
    Request = urllib.request.Request
    build_opener = urllib.request.build_opener
    HTTPCookieProcessor = urllib.request.HTTPCookieProcessor
    urlencode = urllib.parse.urlencode
    HTTPError = urllib.HTTPError
else:
    Request = urllib2.Request
    build_opener = urllib2.build_opener
    HTTPCookieProcessor = urllib2.HTTPCookieProcessor
    urlencode = urllib.urlencode
    HTTPError = urllib2.HTTPError
import logging
import re
try:
    import cookielib
except ImportError:
    import http.cookiejar as cookielib

import dateutil.parser
import json

logging.basicConfig(filename='example.log', filemode='w', level=logging.DEBUG)
_log = logging.getLogger("fitbit")

class Client(object):
    """A simple API client for the www.fitbit.com website.
    see README for more details
    """
    
    def __init__(self, user_id, opener, url_base="http://www.fitbit.com"):
        self.user_id = user_id
        self.opener = opener
        self.url_base = url_base
    
    def intraday_calories_burned(self, date):
        """Retrieve the calories burned every 5 minutes
        the format is: [(datetime.datetime, calories_burned), ...]
        """
        return self._graphdata_intraday_request("intradayCaloriesBurned", date)
    
    def intraday_active_score(self, date):
        """Retrieve the active score for every 5 minutes
        the format is: [(datetime.datetime, active_score), ...]
        """
        return self._graphdata_intraday_request("intradayActiveScore", date)

    def intraday_distance(self, date):
        """Retrieve the active score for every 5 minutes
        the format is: [(datetime.datetime, active_score), ...]
        """
        return self._graphdata_intraday_request("intradayActiveScore", date)

    def intraday_floor_climbed(self, date):
        """Retrieve the active score for every 5 minutes
        the format is: [(datetime.datetime, active_score), ...]
        """
        return self._graphdata_intraday_request("intradayFloors", date)

    def intraday_steps(self, date):
        """Retrieve the steps for every 5 minutes
        the format is: [(datetime.datetime, steps), ...]
        """
        return self._graphdata_intraday_request("intradaySteps", date)
    
    def intraday_sleep(self, date, sleep_id=None):
        """Retrieve the sleep status for every 1 minute interval
        the format is: [(datetime.datetime, sleep_value), ...]
        The statuses are:
            0: no sleep data
            1: asleep
            2: awake
            3: very awake
        For days with multiple sleeps, you need to provide the sleep_id
        or you will just get the first sleep of the day
        """
        return self._graphdata_intraday_sleep_request("intradaySleep", date, sleep_id=sleep_id)
    
    def activity_logs(self,date):
        """Retrieve the available activity logs for the given date
        the format is: [(id,datetime.datetime,name,steps,distance,duration,calories), ...]
        """
        json_data=self._api2request("GET /api/2/user/activities/logs","user","getActivitiesLogs",{"fromDate":str(date),"toDate":str(date),"period":"day","offset":0,"limit":10})
        values=map(lambda log:Client._marshall_activity_log(log),json_data)
        # fitbit api getActivitiesLogs no longer filters by date so do it ourselves
        values=filter(lambda log:log[1].date()==date,values)
        return values

    def activity_log_data_calories(self,date,id):
        """Retrieve the calories burned data in 1 minute intervals for the given date and activity log
        the format is: [(datetime.datetime,calories), ...]
        You need to call activity_logs() first to find the ids for activity log entries
        """
        return self._activity_log_data(date,id,'activityRecordCaloriesBurned')

    def activity_log_data_steps(self,date,id):
        """Retrieve the steps data in 1 minute intervals for the given date and activity log
        the format is: [(datetime.datetime,steps), ...]
        You need to call activity_logs() first to find the ids for activity log entries
        """
        return self._activity_log_data(date,id,'activityRecordSteps')

    def activity_log_data_floors(self,date,id):
        """Retrieve the steps floors climbed in 1 minute intervals for the given date and activity log
        the format is: [(datetime.datetime,floors), ...]
        You need to call activity_logs() first to find the ids for activity log entries
        """
        return self._activity_log_data(date,id,'activityRecordFloors')

    def activity_log_data_pace(self,date,id):
        """Retrieve the pace data in 1 minute intervals for the given date and activity log
        the format is: [(datetime.datetime,pace), ...]
        You need to call activity_logs() first to find the ids for activity log entries
        """
        return self._activity_log_data(date,id,'activityRecordPace')

    def activity_log_data_all(self,date,id):
        """Retrieve the activity data in 1 minute intervals for the given date and activity log
        the format is: [(datetime.datetime,calories,steps,floors,pace), ...]
        You need to call activity_logs() first to find the ids for activity log entries
        """
        calories=self.activity_log_data_calories(date,id)
        steps=self.activity_log_data_steps(date,id)
        floors=self.activity_log_data_floors(date,id)
        pace=self.activity_log_data_pace(date,id)

        # assumes len(calories)==len(steps) etc - which is probably reasonable

        return zip(
            [ l[0] for l in calories], 
            [ l[1] for l in calories],
            [ l[1] for l in steps],
            [ l[1] for l in floors],
            [ l[1] for l in pace])

    def _request(self, path, parameters, request_body=""):
        data=self._request_raw(path, parameters, request_body=request_body)
        return ET.fromstring(data.strip().replace("&hellip;", "..."))

    def _request_json(self, path, post_data, method, request_body=""):
        data=self._request_raw(path, post_data, method, request_body)
        return json.loads(data)

    def _request_raw(self, path, parameters,method="GET", request_body=""):

        if method == "POST":
            request = Request("%s%s" % (self.url_base, path),parameters)
        else:    
            # Throw out parameters where the value is not None
            parameters = dict([(k,v) for k,v in parameters.items() if v])
            query_str = urlencode(parameters)
            request = Request("%s%s?%s" % (self.url_base, path, query_str), request_body)
        
        _log.debug("requesting (%s): %s", method,request.get_full_url())
        data = None
        try:
            response = self.opener.open(request)
            data = response.read()
            response.close()
        except HTTPError as httperror:
            data = httperror.read()
            httperror.close()
        _log.debug("response: %s", data.strip())
        return data.strip()

    def _graphdata_intraday_xml_request(self, graph_type, date, data_version=2108, **kwargs):
        params = dict(
            userId=self.user_id,
            type=graph_type,
            version="amchart",
            dataVersion=data_version,
            chart_Type="column2d",
            period="1d",
            dateTo=str(date)
        )
        
        if kwargs:
            params.update(kwargs)

        return self._request("/graph/getGraphData", params)

    def _graphdata_intraday_xml_request_new(self, graph_type, date, **kwargs):
        params = dict(
            userId=self.user_id,
            type=graph_type,
            apiFormat="json",
            dateTo=str(date),
            dateFrom=str(date),
            ts=time.time()*1000
        )

        if kwargs:
            params.update(kwargs)

        return json.loads(self._request_raw("/graph/getNewGraphData", params))

    def _ajax_request(self,requestObject):
        request_body={"serviceCalls":[requestObject],"template":"activities/modules/models/ajax.response.json.jsp"}
        request_json= urlencode({"request":json.dumps(request_body, separators=(',',':'))})
        return json.loads(self._request_raw("/ajaxapi", {},request_body=request_json))

    def _graphdata_intraday_request(self, graph_type, date):
        # This method used for the standard case for most intraday calls (data for each 5 minute range)
        xml = self._graphdata_intraday_xml_request(graph_type, date)
        
        base_time = datetime.datetime.combine(date, datetime.time())
        timestamps = [base_time + datetime.timedelta(minutes=m) for m in range(0, 288*5, 5)]
        values = [int(float(v.text)) for v in xml.findall("data/chart/graphs/graph/value")]
        return zip(timestamps, values)
    
    def _get_day_details(self,details,date,timeStart=["0","0"],timeEnd=["23","59"]):
        activity={"isAnnotation":True,
                        "date":str(date),
                        "clock":"24",
                        "create":"on",
                        "apiFormat":"htmljson",
                        "name":"test",
                        "annotationStartTimeHours":timeStart[0],
                        "annotationStartTimeMinutes":timeStart[1],
                        "annotationEndTimeHours":timeEnd[0],
                        "annotationEndTimeMinutes":timeEnd[1],
                        "annotationEndTimeDay":"same",
                        "note":"Virtual day activity",
                        "manualCaloriesEnabled":False}

        request={"id":"POST /api/2/user/activities/annotations",
                        "name":"user",
                        "method":"postActivitiesAnnotations",
                        "args":{"activity":json.dumps(activity, separators=(',',':'))        }}
        response= self._ajax_request(request)
        data={};
        for reqId,reqResponse in response.items():
            if reqResponse['status']==200:
                activityId=reqResponse['result']['id']
                #print reqResponse['result']
                for graphtype in details:
                    graphData =self._graphdata_intraday_xml_request_new("activityRecord"+graphtype,reqResponse['result']['date'],arg=activityId)
                    dataPoints=graphData["graph"]["dataSets"]["activity"]["dataPoints"]
                    if not data.has_key(graphtype):data[graphtype]=[]
                    data[graphtype].extend([(d["dateTime"],d["value"]) for d in dataPoints])
                    #print dataPoints
                request={"id":"DELETE /api/2/user/activities/annotations/"+str(activityId),
                        "name":"user",
                        "method":"deleteActivitiesAnnotations",
                        "args":{"activityId":activityId}}
                self._ajax_request(request)
        return data

    def _graphdata_intraday_sleep_request(self, graph_type, date, sleep_id=None):
        # Sleep data comes back a little differently
        xml = self._graphdata_intraday_xml_request(graph_type, date, data_version=2112, arg=sleep_id)
        
        
        elements = xml.findall("data/chart/graphs/graph/value")
        try:
            timestamps = [datetime.datetime.strptime(e.attrib['description'].split(' ')[-1], "%I:%M%p") for e in elements]
        except ValueError:
            timestamps = [datetime.datetime.strptime(e.attrib['description'].split(' ')[-1], "%H:%M") for e in elements]
        
        # TODO: better way to figure this out?
        # Check if the timestamp cross two different days
        last_stamp = None
        datetimes = []
        base_date = date
        for timestamp in timestamps:
            if last_stamp and last_stamp > timestamp:
                base_date -= datetime.timedelta(days=1)
            last_stamp = timestamp
        
        last_stamp = None
        for timestamp in timestamps:
            if last_stamp and last_stamp > timestamp:
                base_date += datetime.timedelta(days=1)
            datetimes.append(datetime.datetime.combine(base_date, timestamp.time()))
            last_stamp = timestamp
        
        values = [int(float(v.text)) for v in xml.findall("data/chart/graphs/graph/value")]
        return zip(datetimes, values)
    
    def _api2request(self,id,name,method,args):

        c=json.dumps({"serviceCalls":
                    [
                    {
                        "id":id,
                        "name":name,
                        "method":method,
                        "args":args
                    }
                    ],"template":"activities/modules/models/ajax.response.json.jsp"},
                separators=(',',':')
                )

        api_data = urllib.urlencode(
            {   'request' : 
                c})     

        json_data =  self._request_json('/ajaxapi', api_data,"POST")

        for service,result in json_data.items():
            status=result.get('status',None)
            value=result.get('result',None)

            if (status==200 and result!=None):
                #print service
                return value

    def _activity_log_data(self,date,id,chart_type):
        json_data=self._newgraph_json_request(chart_type,date,id)

        values=[]

        if ('graph' in json_data):
            data_points=json_data['graph']['dataSets']['activity']['dataPoints']

            values=[(
                dateutil.parser.parse(data_point['dateTime']),
                int(data_point['value'])) 
                for data_point in data_points]

        return values        

    def _newgraph_json_request(self,graph_type,date,arg):
        params = dict(
            userId=self.user_id,
            type=graph_type,
            dateFrom=str(date),
            dateTo=str(date),
            arg=arg,
            apiFormat='json'
        )
        json_data=self._request_json("/graph/getNewGraphData", params,"GET")
        return json_data                

    @staticmethod
    def _marshall_activity_log(log):
        
        #_log.debug("log json: %s", log)

        timestamp=dateutil.parser.parse(log['dateTime'])
        id=log['id']
        steps=int(log['steps']) if log['steps'] else 0
        calories=int(log['calories']) if log['calories'] else 0

        name=log['name'] if log['name'] else log['defaultName']

        match = re.match(r"([0-9\.]+) +(.*)", log['formattedDistance'])
        distance=float(match.group(1))
        unit=match.group(2)
        distance=distance*1.609344  if unit=='miles' else distance

        parts=re.split(r":",log["formattedDuration"])        
        while len(parts)<3:
            parts.insert(0,0)
        duration=datetime.timedelta(hours=int(parts[0]), minutes=int(parts[1]), seconds=int(parts[2]))

        return (id,timestamp,name,steps,distance,duration,calories)

    @staticmethod
    def login(email, password, base_url="https://www.fitbit.com"):
        cj = cookielib.CookieJar()
        opener = build_opener(HTTPCookieProcessor(cj))
        opener.addheaders = [("User-agent", "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36")]

        # fitbit.com wierdness - as of 2014-06-20 the /login page gives a 500: Internal Server Error
        # if there's no cookie
        # Workaround: open the https://www.fitbit.com/ page first to get a cookie
        opener.open(base_url)

        # Get the login page so we can load the magic values
        login_page = opener.open(base_url + "/login").read().decode("utf8")

        source_page = re.search(r"""name="_sourcePage".*?value="([^"]+)["]""", login_page).group(1)
        fp = re.search(r"""name="__fp".*?value="([^"]+)["]""", login_page).group(1)

        data = urlencode({
                "email": email, "password": password,
                "_sourcePage": source_page, "__fp": fp,
                "login": "Log In", "includeWorkflow": "false",
                "redirect": "", "rememberMe": "true"
            }).encode("utf8")

        logged_in = opener.open(base_url + "/login", data)

        if logged_in.geturl() == "http://www.fitbit.com/" or logged_in.geturl() == "https://www.fitbit.com/" \
                or logged_in.geturl() == "https://www.fitbit.com:443/":
            page = logged_in.read().decode("utf8")
        
            match = re.search(r"""userId=([a-zA-Z0-9]+)""", page)
            if match is None:
                match = re.search(r"""/user/([a-zA-Z0-9]+)" """, page)
            user_id = match.group(1)

            return Client(user_id, opener, base_url)
        else:
            raise ValueError("Incorrect username or password.")

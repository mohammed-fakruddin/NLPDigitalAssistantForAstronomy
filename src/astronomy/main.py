
from flask import jsonify
#import os, sys
#import subprocess

#import os
#import io
import xmltodict

from urllib.request import urlopen
#from skimage import io

import requests as req
import sys

from bs4 import BeautifulSoup
from geopy.geocoders import Nominatim

import firebase_admin
from firebase_admin import credentials
from firebase import firebase
from firebase_admin import db

#GREEN = 11
#YELLOW = 13
#RED = 15
#GPIO.setmode(GPIO.BOARD)
#GPIO.setup(GREEN,GPIO.OUT)
#GPIO.output(GREEN,GPIO.LOW)
#GPIO.setup(YELLOW,GPIO.OUT)
#GPIO.output(YELLOW,GPIO.LOW)
#GPIO.setup(RED,GPIO.OUT)
#GPIO.output(RED,GPIO.LOW)

cred = credentials.Certificate("serviceAccountCertificate.json")
default_app = firebase_admin.initialize_app(cred, {'databaseURL': 'https://astronomydb-9a541.firebaseio.com/'})

def astronomy(request):
  req_body = request.get_json()
  #print(req_body)
  resp1=''
  intentName = req_body['queryResult']['intent']['displayName']
  testFirebase()
  getGPSCoordinates()
  updateDriverActions('left')
  #
  #****************** Intention - 1 ********************
  #
  if intentName == 'takePicture':
    response = base_response.copy()
    #response['fulfillmentText'] = 'Picture was sent by an email'
    print(response)
    return jsonify(response)
  if intentName == 'VoiceActivatedCar':
  	direction = req_body['queryResult']['parameters']['Direction']
  	print('diection of the car is:', direction)
  	if (direction):
  		updateDriverActions(direction)
  	response = getSimpleFeedbackResp()
  	response['fulfillmentText'] = 'Moving in the ' + direction + ' direction.'
  	print(response)
  	return jsonify(response)  
  #
  #****************** Intention - 2 ********************
  #  
  if intentName == 'GetSkyMapForALocation':
    city = req_body['queryResult']['parameters']['geo-city']
    country = req_body['queryResult']['parameters']['geo-country']
    mapType = req_body['queryResult']['parameters']['MapType']
    lon = req_body['queryResult']['parameters']['Longitude']
    lat = req_body['queryResult']['parameters']['Latitude']
    northSouth = req_body['queryResult']['parameters']['NorthSouth']
    eastWest = req_body['queryResult']['parameters']['EastWest']
    gpsLoc = req_body['queryResult']['parameters']['GPSLocation']
    print('******************')
    print('city:', city)
    print('country:', country)
    print('map type:', mapType)
    print('lat:', lat)
    print('lon:', lon)
    print('NorthSouth:', northSouth)
    print('EastWest:', eastWest)
    print('GPS Location:', gpsLoc)
    print('*****************')
    if (gpsLoc.find('current')!=-1):
    	gpsCordinates = getGPSCoordinates()
    	if(len(gpsCordinates) == 2):
    		lon = gpsCordinates[0]
    		lat = gpsCordinates[1]

    respList = getSkyMap(city, country, lon, lat, northSouth, eastWest, mapType)
    if(len(respList)==2):
      response = getSkyMapRespSuccess()
      msg1=respList[0]
      url1 = respList[1]
      response['fulfillmentMessages'][1]['basicCard']['image']['imageUri'] = response['fulfillmentMessages'][1]['basicCard']['image']['imageUri'].format(replaceURL=url1)
      response['payload']['google']['richResponse']['items'][1]['basicCard']['image']['url'] = response['payload']['google']['richResponse']['items'][1]['basicCard']['image']['url'].format(replaceURL=url1)
      response['payload']['google']['richResponse']['items'][0]['simpleResponse']['textToSpeech'] = response['payload']['google']['richResponse']['items'][0]['simpleResponse']['textToSpeech'].format(replaceRespText=msg1)
      response['payload']['google']['richResponse']['items'][0]['simpleResponse']['displayText'] = response['payload']['google']['richResponse']['items'][0]['simpleResponse']['textToSpeech'].format(displayText=msg1)
    else:
      response = getSimpleFeedbackResp()
      response['fulfillmentText'] = respList[0]
      #response['fulfillmentText'] = respList[0]
    print(response)
    return jsonify(response)
  #
  #****************** Intention - 3 ********************
  #  
  if intentName == 'GetCoordinatesAndImages':
  	objName = req_body['queryResult']['parameters']['ObjectName']
  	resp1=''
  	print('***** object name is: ', objName)
  	respDetails = getCelestialObjectDetails(objName)
  	msg1 = respDetails[0]
  	url1 = respDetails[1]
  	print('#######################################')
  	print('**** resp 0: ', msg1)
  	print('**** resp 1: ', url1)
  	#resp1 = astro_response.copy()
  	resp1 = getAstroResp()
  	resp1['fulfillmentMessages'][1]['basicCard']['image']['imageUri'] = resp1['fulfillmentMessages'][1]['basicCard']['image']['imageUri'].format(replaceURL=url1)
  	resp1['payload']['google']['richResponse']['items'][1]['basicCard']['image']['url'] = resp1['payload']['google']['richResponse']['items'][1]['basicCard']['image']['url'].format(replaceURL=url1)
  	resp1['payload']['google']['richResponse']['items'][0]['simpleResponse']['textToSpeech'] = resp1['payload']['google']['richResponse']['items'][0]['simpleResponse']['textToSpeech'].format(replaceRespText=msg1)
  	resp1['payload']['google']['richResponse']['items'][0]['simpleResponse']['displayText'] = resp1['payload']['google']['richResponse']['items'][0]['simpleResponse']['textToSpeech'].format(displayText=msg1)
  	print(resp1)
  	print('#######################################')
  	return jsonify(resp1)


def getCelestialObjectDetails(objName):
  objDetails=[]
  #objName='M1'
  inputURLPrefix = 'http://www.strudel.org.uk/lookUP/xml/?name='
  URL = inputURLPrefix + objName
  resp = req.get(URL)
  #print(resp.text)

  doc = xmltodict.parse(resp.text)
  ra = doc['result']['ra']['#text']
  de = doc['result']['dec']['#text']
  image1 = doc['result']['image']['@src']
  image2 = doc['result']['image']['@href']
  category = doc['result']['category']['#text']
  # build the url to return to the google assitant
  urlPrefix1='http://server7.sky-map.org/imgcut?survey=DSS2&w=256&h=256&ra='
  urlPrefix2='&de='
  urlPrefix3='&angle=1.25&output=PNG'
  url = urlPrefix1 + ra + urlPrefix2 + de + urlPrefix3
  # extract all URLs from the results/maps object
  map_urls={}
  maps_len= len(doc['result']['maps']['map'])
  for i in range(0 , maps_len):
    #print(i)
    band= doc['result']['maps']['map'][i]['@band']
    url_map = doc['result']['maps']['map'][0]['@href']
    map_urls[band]=url_map
  
  url = urlPrefix1 + ra + urlPrefix2 + de + urlPrefix3

  #print('the coordinate details are:')
  #print('ra:', ra)
  #print('de:', de)
  #print('image 1:', image1)
  #print('image 2:', image2)
  #print('url:', url)
  #print('category:', category)
  #for k in map_urls.keys():
  #  #print(k,':', map_urls[k])
  #
  respText1 = 'The details of the celestial object ' + objName + ' are  as follows: ' \
  + 'the RA (right ascension) co-ordinate is: ' + ra + ' and DEC (declination) co-ordinate is: ' + de \
  + ' and the category of the object is: ' + category

  objDetails.append(respText1)
  objDetails.append(url)
  objDetails.append(image2)
  return objDetails


def getAstroResp():
	astro_response = {
                 'fulfillmentMessages': [
                  {
                      "simpleResponses":{
                        "simpleResponses":[
                          {
                            "textToSpeech":"Astronomy - object details - 1"
                          }
                        ]
                      }
                  },
                  {
                    "platform": "ACTIONS_ON_GOOGLE",
                    "basicCard": {
                        "title": "Astronomy 1",
                        "subtitle": "Celestial System",
                        "formattedText": "Astronomy 2",
                        "image":{
                          "imageUri": "{replaceURL}",
                          "accessibilityText": "Astronomy object details"
                        }                        
                      }
                  } 
                ],
                'fulfillmentText':"Astronomy - object details - 2",
                'payload':{
                    "google": {                          
                          "richResponse": {
                            "items": [
                                {
                                  "simpleResponse": {
                                    "textToSpeech": "{replaceRespText}",
                                    "displayText": "{replaceRespText}"
                                  }
                                },
                                  {
                                  "basicCard": {
                                      "title": "Astronomy Object Details",
                                      "subtitle": "Astronomy System",
                                      "formattedText": "Astronomy - Rich Response",
                                      "image":{
                                          "url": "{replaceURL}",
                                          "accessibilityText": "Astronomy object details"
                                        }                        
                                    }
                                  }  
                              ]
                          }
                    }
                },
                 'source' : 'Manual'}
	return astro_response

def getSimpleFeedbackResp():
  base_response = {
                 'fulfillmentMessages': [
                  {
                      "simpleResponses":{
                        "simpleResponses":[
                          {
                            "textToSpeech":"Webhook response for GetSkyMapForALocation intent"
                          }
                        ]
                      }
                  }
                ],
                'fulfillmentText':"picture LED sent",
                 'source' : 'Manual'}
  return base_response  

def getSkyMapRespSuccess():
  skymap_response = {
                 'fulfillmentMessages': [
                  {
                      "simpleResponses":{
                        "simpleResponses":[
                          {
                            "textToSpeech":"Astronomy - the geo location sky map details - 1"
                          }
                        ]
                      }
                  },
                  {
                    "platform": "ACTIONS_ON_GOOGLE",
                    "basicCard": {
                        "title": "Astronomy Geo Location Map 1",
                        "subtitle": "Geo Location Map",
                        "formattedText": "Geo Location Map 2",
                        "image":{
                          "imageUri": "{replaceURL}",
                          "accessibilityText": "Astronomy geo location sky map details"
                        }                        
                      }
                  } 
                ],
                'fulfillmentText':"Astronomy - the geo location sky map details - 2",
                'payload':{
                    "google": {                          
                          "richResponse": {
                            "items": [
                                {
                                  "simpleResponse": {
                                    "textToSpeech": "{replaceRespText}",
                                    "displayText": "{replaceRespText}"
                                  }
                                },
                                  {
                                  "basicCard": {
                                      "title": "Astronomy Geo Location Map Image",
                                      "subtitle": "Astronomy Geo Location Map System",
                                      "formattedText": "Astronomy - Geo Location Map",
                                      "image":{
                                          "url": "{replaceURL}",
                                          "accessibilityText": "Astronomy Geo Location Map details"
                                        }                        
                                    }
                                  }  
                              ]
                          }
                    }
                },
                 'source' : 'Manual'}
  return skymap_response

def getSkyMap(city, country, lon, lat, ns, ew, mapType):
  respList=[]
  urlInputPre = 'http://www.fourmilab.ch/cgi-bin/Yoursky?z=1&'
  
  if (not city and not country and not lon and not lat):
    respList.append('please provide the co-ordinates and the location details')
  #elif (not lon and not lat):
  #  respList.append('Please provide location details such as city or country or longitude or longitude')
    return respList

  geoLocator = Nominatim()
  if(city and country):
    location = geoLocator.geocode(city + ',' + country)
    lon = location.longitude
    lat = location.latitude
  elif(city):
    location = geoLocator.geocode(city)
    lon = location.longitude
    lat = location.latitude
  elif(country):
    location = geoLocator.geocode(country)
    lon = location.longitude
    lat = location.latitude
  #if (not city and not country and not lon and not lat):
  #  respList.append('please provide the co-ordinates and the location details')
  #  return respList

  urlLonLat='lon=' + str(lon) + '&lat=' + str(lat) + '&ns=' + ns + '&ew=' + ew
  inputURL = urlInputPre + urlLonLat
  print('url for input request is: ', inputURL)
  respForURL = req.get(inputURL)
  html = respForURL.text
  #print(html)
  soup = BeautifulSoup(html, 'html.parser')
  finalUrlP = 'http://www.fourmilab.ch'
  urlImage= soup.find('img')['src']
  print('url image', urlImage)
  urlH = finalUrlP + urlImage.replace('Yoursky', 'Yourhorizon')
  urlSky = finalUrlP + urlImage
  urlT = finalUrlP + urlImage.replace('Yoursky', 'Yourtel')
  #print('final url:', respList[1])
  #jjj
  respList.append('The ' + mapType + ' for the chosen location is:')
  if ('sky' in mapType):
    respList.append(urlSky)
  if ('horizon' in mapType):
    respList.append(urlH)
  if('tele' in mapType):
    respList.append(urlT)  
  print('len:', len(respList))
  if(len(respList)==2):
    print('final url:', respList[1])
  return respList


def testFirebase():
	try:
		#print('***** before json****')
		#cred = credentials.Certificate("serviceAccountCertificate.json")
		#print('***** after json****')
		#default_app = firebase_admin.initialize_app(cred, {'databaseURL': 'https://astronomydb-9a541.firebaseio.com/'})
		print('***** after app init****')
		ref = db.reference('root/')
		print(ref.get())
	except:
		print('exception: ', sys.exc_info()[0], " occured")
		


def getGPSCoordinates():
	gps=[]
	try:
		#print('***** before json****')
		#cred = credentials.Certificate("serviceAccountCertificate.json")
		#print('***** after json****')
		#default_app = firebase_admin.initialize_app(cred, {'databaseURL': 'https://astronomydb-9a541.firebaseio.com/'})
		#print('***** after app init****')
		lon = db.reference('root/gps/lon')
		lat = db.reference('root/gps/lat')
		print('gps lon:', lon.get())
		print('gps lat:', lat.get())
		if (lon.get()!=None):
			gps.append(lon.get())
		if (lat.get()!=None):
			gps.append(lat.get())
		print('length of gps coordinates are: ', len(gps))
		return gps
	except:
		print('exception: ', sys.exc_info()[0], " occured")


def updateDriverActions(action):
	try:
		#print('***** before json****')
		#cred = credentials.Certificate("serviceAccountCertificate.json")
		#print('***** after json****')
		#default_app = firebase_admin.initialize_app(cred, {'databaseURL': 'https://astronomydb-9a541.firebaseio.com/'})
		#print('***** after app init****')
		ref_action = db.reference('root')
		print('current action:', ref_action.get())
		ref_action.update({'action': action})
	except:
		print('exception: ', sys.exc_info()[0], " occured")

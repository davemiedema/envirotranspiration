#!/usr/bin/python

################################################################
#
# Envirotranspiration calculator for Wunderground based data
#
# Copyright 2014, Dave Miedema
#
# This is based on FAO ET equations found here
#   http://www.fao.org/docrep/x0490e/x0490e00.htm
#
# and a computation of solar radiation based on estimated 
# cloud cover using equations from here
#
#   http://www.shodor.org/os411/courses/_master/tools/calculators/solarrad/
#
################################################################

import urllib, json, sys, math, time, os, smtplib; 
from datetime import date, timedelta, datetime
from email.mime.text import MIMEText

# Location constant
GMTOFFSET = 5
LATITUDE = 45.4214
LONGITUDE = -75.6919
ELEVATION = 100
COUNTRY = "Canada"
CITY = "Ottawa"
KEY = ""

#debug level.  0 gives a summary
level = 0

#number of days to go back into the history to compute deficit
window = 21

# Mapping of conditions to a level of cloud cover.  These can be adjusted
# since they are all made up anyway
conditions = {
  "Blowing Snow"                   :8,
  "Clear"                          :0,
  "Fog"                            :5,
  "Haze"                           :2,
  "Heavy Blowing Snow"             :9,
  "Heavy Fog"                      :9,
  "Heavy Low Drifting Snow"        :10,
  "Heavy Rain"                     :10,
  "Heavy Rain Showers"             :10,
  "Heavy Thunderstorms and Rain"   :10,
  "Light Drizzle"                  :10,
  "Light Freezing Rain"            :10,
  "Light Ice Pellets"              :10,
  "Light Rain"                     :10,
  "Light Rain Showers"             :10,
  "Light Snow"                     :10,
  "Light Snow Grains"              :10,
  "Light Snow Showers"             :10,
  "Light Thunderstorms and Rain"   :10,
  "Low Drifting Snow"              :10,
  "Mist"                           :3,
  "Mostly Cloudy"                  :8,
  "Overcast"                       :10,
  "Partial Fog"                    :2,
  "Partly Cloudy"                  :5,
  "Patches of Fog"                 :2,
  "Rain"                           :10,
  "Rain Showers"                   :10,
  "Scattered Clouds"               :4,
  "Shallow Fog"                    :3,
  "Snow"                           :10,
  "Snow Showers"                   :10,
  "Thunderstorm"                   :10,
  "Thunderstorms and Rain"         :10,
  "Unknown"                        :5,  
}


# Print an attribute
def printAttr(indata, name, uiname):
  print "  " + uiname + " " + str(indata[name])

# Get forecast data for the city.  Unused right now.  
# Results could be used to suppress watering based on forecast rainfall
def getForecastData():
  forecastURL = 'http://api.wunderground.com/api/' + KEY + '/forecast/q/' + COUNTRY + '/' + CITY + '.json'

  response = urllib.urlopen(forecastURL).read();

  data = json.loads(response)

  print CITY + ', ' + COUNTRY

  # Forecast day.  Could make this a loop to lookahead even more
  day = 0

  if (level > 3):
    printAttr(data['forecast']['simpleforecast']['forecastday'][day]['date'], "pretty", "Date")
    printAttr(data['forecast']['simpleforecast']['forecastday'][day]['high'], "celsius", "High temp")
    printAttr(data['forecast']['simpleforecast']['forecastday'][day]['low'], "celsius", "Low temp")
    printAttr(data['forecast']['simpleforecast']['forecastday'][day], "maxhumidity", "High humidity")
    printAttr(data['forecast']['simpleforecast']['forecastday'][day], "avehumidity", "Average humidity")
    printAttr(data['forecast']['simpleforecast']['forecastday'][day], "minhumidity", "Low humidity")
    printAttr(data['forecast']['simpleforecast']['forecastday'][day]['maxwind'], "kph", "Max wind")
    printAttr(data['forecast']['simpleforecast']['forecastday'][day]['avewind'], "kph", "Average wind")
    printAttr(data['forecast']['simpleforecast']['forecastday'][day]['qpf_allday'], "mm", "Daily rainfall")
    print

  forecast = float(data['forecast']['simpleforecast']['forecastday'][day]['qpf_allday']['mm'])
 
  return forecast

# Returns a calculation of saturation vapour pressure based on temperature in degrees
def saturationVapourPressure(T):
  return 0.6108 * math.exp((17.27 * T) / (T + 237.3))

def getHistoricalData(forecast):

  totalBalance = 0
  for day in range(window,-1,-1):

    today = date.today() - timedelta(day)
    datestring = today.strftime("%Y%m%d")

    #response = urllib.urlopen(historyURL).read();

    try:
      with open("water/" + datestring) as f:
        for line in f:
          irrigation = float(line)
          if (irrigation == -1):
            print "    Reset balance"
            totalBalance = 0
          else:
            print "    " + str(float(line)) + "mm of irrigation"
            totalBalance += float(line)
    except:
      pass

    if (day < 4):
      try:
        os.remove("data/" + datestring)
      except OSError:
        pass

    try:
      data = json.load(open("data/" + datestring))
      source = "file " + datestring
    except:
      historyURL = 'http://api.wunderground.com/api/'+ KEY + '/history_'+datestring+'/q/Canada/Ottawa.json'
      time.sleep(10)
      response = urllib.urlopen(historyURL).read()
      cachefile = open("data/" + datestring, 'w')
      cachefile.write(response)
      cachefile.close()
      data = json.loads(urllib.urlopen(historyURL).read())
      source = historyURL

    thedate = date(int(data['history']['dailysummary'][0]['date']['year']),
                   int(data['history']['dailysummary'][0]['date']['mon']),
                   int(data['history']['dailysummary'][0]['date']['mday']))

    dayOfYear = thedate.timetuple().tm_yday

    if (level > 0):
      print 'Data for ' + CITY + ', ' + COUNTRY + ' from ' + source + " on " + str(thedate)

    if (level > 2 ):
      printAttr(data['history']['dailysummary'][0], "maxtempm", "High temp")
      printAttr(data['history']['dailysummary'][0], "meantempm", "Average temp")
      printAttr(data['history']['dailysummary'][0], "mintempm", "Low temp")
      printAttr(data['history']['dailysummary'][0], "maxhumidity", "High humidity")
      printAttr(data['history']['dailysummary'][0], "minhumidity", "Low humidity")
      printAttr(data['history']['dailysummary'][0], "maxwspdm", "Max wind")
      printAttr(data['history']['dailysummary'][0], "meanwindspdm", "Average wind")
      printAttr(data['history']['dailysummary'][0], "minwspdm", "Min wind")
      printAttr(data['history']['dailysummary'][0], "precipm", "Daily rainfall")
      printAttr(data['history']['dailysummary'][0], "meanpressurem", "Average air pressure")

    
    # Calculate solar radiation from location
    totalSolarRadiation = 0
    totalClearSkyIsolation = 0
    sunnyHours = 0

    # Get the conditions for the 24 hours of the requested day
    for hour in range(0,24):

      # Sometimes data is missing for an hour.  If we don't find data, cloud cover will stay at
      # -1
      cloudCover = -1

      # Look through the historical data we have
      for period in range(0, len(data['history']['observations'])):

        # Look for our hour in the date
        if (int(data['history']['observations'][period]['date']['hour']) == hour):

          # If there are conditions in the data, get them, and find the percent cloud cover 
          # for this hour
          if (data['history']['observations'][period]['conds']):
            cloudCover = float(conditions[data['history']['observations'][period]['conds']])/10
            cloudCoverString = data['history']['observations'][period]['conds']
            break;

      # If we didn't find any conditions for this hour, assume the same conditions as the 
      # previous hour.  Sometimes we are missing early data, but this is usually at night
      # anyway, so we are safe
      if (cloudCover == -1): cloudCover = previousCloudCover
      previousCloudCover = cloudCover

      # If we have data
      if (cloudCover != -1):

        # Track the number of sunny hours
        if (cloudCover < 0.5): 
          sunnyHours = sunnyHours + 1

        # Find out the angle of the sun was in the middle of this hour as a good 
        # estimate
        gmtHour = hour + GMTOFFSET + 0.5
        fractionalDay = (360/365.25)*(dayOfYear+gmtHour/24)
        f = math.radians(fractionalDay)
        declination = 0.396372 - 22.91327  * math.cos(f) + 4.02543  * math.sin(f) - 0.387205 * math.cos(2 * f) + 0.051967 * math.sin(2 * f) - 0.154527 * math.cos(3 * f) + 0.084798 * math.sin(3 * f)
        timeCorrection = 0.004297 + 0.107029 * math.cos(f) - 1.837877 * math.sin(f) - 0.837378 * math.cos(2*f) - 2.340475*math.sin(2*f)
        solarHour = (gmtHour + 0.5 - 12)*15 + LONGITUDE + timeCorrection 

        if (solarHour < -180): solarHour = solarHour + 360
        if (solarHour > 180): solarHour = solarHour - 360

        solarFactor = math.sin(math.radians(LATITUDE))*math.sin(math.radians(declination))+math.cos(math.radians(LATITUDE))*math.cos(math.radians(declination))*math.cos(math.radians(solarHour))

        sunElevation = math.degrees(math.asin(solarFactor))
        clearSkyInsolation = 990 * math.sin(math.radians(sunElevation))-30

        if (clearSkyInsolation < 0): clearSkyInsolation = 0
          
        solarRadiation = clearSkyInsolation * (1 - 0.75*(math.pow(cloudCover,3.4)))

        # Accumulate clear sky radiation and solar radiation on the ground
        totalSolarRadiation += solarRadiation
        totalClearSkyIsolation += clearSkyInsolation

    # Convert from Wh / m^2 / d 
    totalSolarRadiation = totalSolarRadiation #* 0.75

    # Solar Radiation
    Rs = totalSolarRadiation * 3600 / 1000 / 1000 # MJ / m^2 / d

    # Extraterrestrial Radiation
    Ra = totalClearSkyIsolation * 3600 / 1000 / 1000 # MJ / m^2 / d

    # Clear sky solar radiation
    Rso = (0.75 + 0.00002 * ELEVATION) * Ra

    # Net shortwave radiation
    Rns = 0.77 * Rs

    # m/s at 2m above ground
    windspeed = float(data['history']['dailysummary'][0]['meanwindspdm']) * 1000 / 3600  * 0.748

    pressure = float(data['history']['dailysummary'][0]['meanpressurem']) / 10 # kPa

    tempAvg = float(data['history']['dailysummary'][0]['meantempm']) # degrees C
    tempMin = float(data['history']['dailysummary'][0]['mintempm']) # degrees C
    tempMax = float(data['history']['dailysummary'][0]['maxtempm']) # degrees C
    humidMax = float(data['history']['dailysummary'][0]['maxhumidity']) # degrees C
    humidMin = float(data['history']['dailysummary'][0]['minhumidity']) # degrees C

    sigmaTmax4 = 0.000000004903 * math.pow(tempMax+273.16,4)
    sigmaTmin4 = 0.000000004903 * math.pow(tempMin+273.16,4)
    aveSigmaT = (sigmaTmax4 + sigmaTmax4) / 2
    
    if (level > 2):
      print "  ground windspeed " + str(windspeed)
      print "  Sunny hours " + str(sunnyHours)

    D = 4098 * saturationVapourPressure(tempAvg) / math.pow(tempAvg + 237.3,2)
    g = 0.665e-3 * pressure

    es = (saturationVapourPressure(tempMin) + saturationVapourPressure(tempMax)) / 2
    ea = saturationVapourPressure(tempMin) * humidMax / 200 + saturationVapourPressure(tempMax) * humidMin / 200

    vaporPressDeficit = es - ea

    if (level > 2):
      print "  Solar Radiation " + str(totalSolarRadiation)
      print "  Clear Sky Solar Radiation " + str(totalClearSkyIsolation)
      print "  Ra " + str(Ra)
      print "  Rs " + str(Rs)
      print "  Rso " + str(Rso)
      print "  Rns " + str(Rns)
      print "  aveSigmaT " + str(aveSigmaT)

    # Net longwave radiation
    Rnl = aveSigmaT * (0.34 - 0.14 * math.sqrt(ea)) * (1.35 * Rs / Rso - 0.35)

    # Net radiation
    Rn = Rns - Rnl

    if (level > 2):
      print "  Rnl " + str(Rnl)
      print "  Rn " + str(Rn)

    if (level > 3):
      print "  D " + str(D)
      print "  g " + str(g)
      print "  es " + str(es)
      print "  ea " + str(ea)
      print "  Vapor Pressure Deficit " + str(vaporPressDeficit)

    ETo = ((0.408 * D * Rn) + (g * 900 * windspeed * vaporPressDeficit) / (tempAvg + 273)) / (D + g * (1 + 0.34 * windspeed))

    rainfall = float(data['history']['dailysummary'][0]['precipm'])
    dailyBalance = rainfall - ETo   
    totalBalance += dailyBalance

    if (level > 0):
      print "  Enviro-Transpiration " + str(ETo)
      print "  Daily Balance " + str(dailyBalance)

    print "  " + str(day) + " day balance " + str(totalBalance)

    if (level > 0):
      print
  
  print 
  print "  Forecast " + str(forecast)
  print "  Balance over " + str(window) + " days = " + str(totalBalance + forecast)

  totalBalance += forecast

  if (totalBalance > -5):
    try:
      os.remove("need")
    except:
      pass
    f = open('skip','w')
    f.write(str(totalBalance)+'\n') 
    f.close() 
  else:
    try:
      os.remove("skip")
    except:
      pass
    f = open('need','w')
    f.write(str(totalBalance)+'\n') 
    f.close() 


forecast = getForecastData()
getHistoricalData(forecast)

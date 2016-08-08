# envirotranspiration

This repository holds one file:  getWeather2.py

This is a python script attempts to calculate the envirotranspirtation
based on weather data obtained from the Wunderground weather site.

To do this it needs solar raditation data, and since most locations do
not publish solar radiation data, this is estimated based on historical
text strings describing the weather conditions.   

With an estimate of cloud cover for every hour, the script can calculate
the solar radiation.

Some parameters of interest to help customize the script:

 - GMTOFFSET 
   - the timezone the location is in.  This can possibly be inferred
     from the location using an API, but it is just as easy to type in a
     number since the location does not change very often

 - LATITUDE and LONGITUDE
   - this is the coordinates of the location.  This is used to calculate
     solar radiation independent of cloud cover.

 - ELEVATION (meters)
   - a minor parameter, used in the ETo calculations

 - COUNTRY and CITY
   - Country/City is used in the Wunderground API to get the correct weather
     data

 - KEY
   - Wunderground API key.  User specific


When the script is run, it will try to find historical data in the local
"water" directory.  These files are named based on timestamp and contain
a number that indicates how much irrigation was applied for that day.

If the file in the "water" directory contains "-1", the balance is
reset.  This is useful to ignore previous computations in spring or
after a vacation.

Data is obtained from the Weather Underground site for the previous
window of days and stored in the cached files in the "data" directory.
This cache is used to compute ETo for the window.  Weather data for the
most recent 4 days is always downloaded from the site and put in the
cache.  The 4 day window is present because the weather
sites are sometimes updated with more accurate information for the
recent days and we want to get updated data if possible.

The total balance is computed, and if the balance is lower than the
threshold, a file called "need" is written with the balance contained
within it.

If the balance is higher than the threshold, the "need" file is removed
and a file called "skip" is created with the balance in it.

A watering program can the look for the presence of these files daily
and run a watering cycle.  The watering program should then update the
data in the "water" directory to indicate how much water was applied.



  
              

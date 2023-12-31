# -*- coding: utf-8 -*-

### Import packages used:

# standard inputs
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
# these imports allow accessing data from websites
from bs4 import BeautifulSoup
import requests
# this import is to make the graph look nicer
import matplotlib.colors as mcolors
st.title('Current RAOB (Balloon Sonde) data from Albany Airport, plotted for Temperature Inversion')

"""
This code takes the most current sounding from the NOAA's webstite from the albany airport station and places all of the data into a dataframe. It then plots the data and checks for potential temperature inversion patterns.
"""
"""Information about how to format the url is at:  https://rucsoundings.noaa.gov/text_sounding_query_parameters.pdf

The data format information is at: https://rucsoundings.noaa.gov/raob_format.html

The codes for different sounding locations are at: https://rucsoundings.noaa.gov/raob.short"""

import requests
url = 'https://rucsoundings.noaa.gov/get_soundings.cgi?start=latest&airport=72518&'
page = requests.get(url)
if page.status_code == 200:
    # Parse the HTML content using BeautifulSoup
    inputdata = BeautifulSoup(page.text, 'html.parser')
    # Now 'inputdata' contains the parsed HTML content
else:
    print(f"Error: Failed to retrieve the page. Status code: {page.status_code}")
soup = BeautifulSoup(page.content, 'html.parser')

data = inputdata.string[408:]
data = data.strip()
data = ' '.join(data.split())
data = data.replace(" ", ",")
rows = data.split(',')
df = pd.DataFrame([rows[i:i+7] for i in range(0, len(rows), 7)], columns=['TYPE', 'PRESSURE', 'HEIGHT', 'TEMP', 'DEWPT', 'WIND DIR', 'WIND SPD'])
df = df.apply(pd.to_numeric, errors='ignore')

def celsius_to_fahrenheit(celsius):
    return (celsius * 9/5) + 32
def tenthcelsius_to_celsius(tenthcelcius):
    return (tenthcelcius * 1/10)
def meters_to_feet(meters):
    return (meters * 3.28084)

df['TEMP_celsius'] = df['TEMP'].apply(tenthcelsius_to_celsius)
df['TEMP_fahrenheit'] = df['TEMP_celsius'].apply(celsius_to_fahrenheit)
df['HEIGHT_feet'] = df['HEIGHT'].apply(meters_to_feet)

#This list shows all of the heights that split the data into boxes that get checked for inversions
boxpartition = [0,500,1000,2000,3000,4000,5000,6000,7000,8000]

#This list will represent if there is an inversion between heights i and i+1 in the boxpartition list
#A zero represents no inversion a 1 represents an inversion
flaglist = []

# Loop 9 times for 9 boxes checked
for i in range(9):

    #the height of the checked box will start at the first value of the boxpartition list then go to the next highest
    box = df[(df['HEIGHT'] >= boxpartition[i]) & (df['HEIGHT'] <= boxpartition[i+1])]['HEIGHT']

    #find the index number of the maximum height of the box
    boxmaxindex = box.idxmax()
    boxmax = box.max()

    #find the index number of the lowest temp in the box
    boxtemp = df.loc[0:boxmaxindex, 'TEMP']
    boxtempmin = boxtemp.min()
    boxtempminindex = df.index[df['TEMP'] == boxtempmin].tolist()

    #if the minimum temperature is in the same place as the maximum height there is no inversion
    #if the mimimum temperature happens not at the highest height there is an inversion
    #if there are two minimum temperatures there is an inversion
    #this is flagged by taking the lower height of the two minimums
    if boxmaxindex == boxtempminindex[0]:
        flaglist.append(0)
    else:
        flaglist.append(1)


df.plot(x='TEMP_fahrenheit', y='HEIGHT_feet', kind='line')

#axis labels and legend
plt.xlabel(r'Temp ($^\circ$F)')
plt.ylabel('Height (feet)')
plt.title('Temperature Inversions')
plt.legend(['Temperature at that Height'])

#the y axis goes from 0 to the max height looked at
plt.ylim(0,26246.72)

#this sets the x axis using the highest and lowest temperatures in the range
height_range = df[(df['HEIGHT'] >= 0 ) & (df['HEIGHT'] <= 10000)]['HEIGHT']
maxheightindex = box.idxmax()
temps = df.loc[0:maxheightindex, 'TEMP_fahrenheit']
tempmin = temps.min()
tempmax = temps.max()
plt.xlim(tempmin-7,tempmax+7)

#this highlights the regions of the plot that were previously flagged as having an inversion and highlights them
colors = mcolors.LinearSegmentedColormap.from_list('red_to_yellow', ['red', 'yellow'])
for i in range(9):
    flag = flaglist[i]
    boxbottom = boxpartition[i]* 3.28084
    boxtop = boxpartition[i+1]* 3.28084
    color_value = i / 9
    xmid = (tempmin+tempmax)/2
    ymid = (boxbottom+boxtop)/2
    if flag == 1:
        plt.fill_betweenx([boxbottom, boxtop], tempmin-7, tempmax+7, color=colors(color_value), alpha=0.3)
        plt.text(xmid-30, ymid-900, 'Inversion', fontsize=12, color='red', ha='center', va='bottom')


flaglist
fig, ax = plt.subplots()
df.plot(x='TEMP', y='HEIGHT', kind='line', ax=ax)
plt.ylim(0,8000)
plt.grid()
st.pyplot(fig)
df


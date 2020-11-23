import requests
import json
import math
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

url = 'http://www.hiautosale.com/HiAutoV2/HiAutoInventory.aspx'
r = requests.get(url)
soup = BeautifulSoup(r.text, 'html.parser')
tag = soup.select('#LblSelect')
vehicles = int(tag[0].text[8:11])
leftover = vehicles % 25
pages = (math.ceil(vehicles/25))

opts = Options()
opts.add_argument('--incognito')
# opts.add_argument('--start-maximized')
opts.add_argument('--headless')
opts.add_argument('--ignore-certicate-errors')
opts.add_argument('--ignore-ssl-errors')

browser = webdriver.Chrome('./chromedriver', options=opts)

browser.get(url)
vins = []
for i in range(pages):
    pageSource = browser.page_source
    soup = BeautifulSoup(pageSource, 'html.parser')
    n = 25
    if i == (pages - 1):
        n = leftover
    for i in range(n):
        id = "#DataList1_LblItemLic_" + str(i)
        tag = soup.select(id)
        vin = (tag[0].contents[0])
        vins.append(vin)
    element = browser.find_element_by_id('ImageButtonNext')
    element.click()

print("Total number of vehicles: " + str(len(vins)))

toyotas = []
passed = []


def decodeVin(vin):
    url = 'https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVin/' + vin + '?format=json'
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            year = data['Results'][9]['Value']
            make = data['Results'][6]['Value']
            model = data['Results'][8]['Value']
            if make == 'TOYOTA' or make == 'LEXUS' or make == 'SCION':
                toyotas.append([vin, year, make, model])
        else:
            passed.append(vin)
    except:
        passed.append(vin)

for vin in vins:
    decodeVin(vin)


print("Number of failed VIN decodes: " + str(len(passed)))
print("Number of Toyotas/Lexus/Scions to check: " + str(len(toyotas)))

recalls = []
timeout = []

def checkRecall(vehicle):
    url = 'https://one.nhtsa.gov/webapi/api/Recalls/vehicle/modelyear/' + vehicle[1] + '/make/' + vehicle[2] + '/model/' + vehicle[3] + '?format=json'
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data['Count'] > 0:
                recalls.append(vehicle)
        else:
            timeout.append(vehicle)
    except:
        timeout.append(vehicle)

for toyota in tqdm(toyotas):
    checkRecall(toyota)
    #print(str(int(round(i/len(toyotas),2)*100)) + "%") #progress checker


print("Number of Toyotas/Lexus/Scions with recalls: " + str(len(recalls)))
print("Number of failed recall checks: " + str(len(timeout)))

for i,recall in enumerate(recalls,1):
    print(i, recall)

from datetime import datetime
import sys
from time import sleep
from dateutil.relativedelta import relativedelta
import requests

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver import Edge
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By

import os
from bs4 import BeautifulSoup

if 'data' not in os.listdir('.'):
    os.mkdir('./data')
os.chdir('./data')


STATE_NO = int(sys.argv[1])
DIST_NO = int(sys.argv[2])
YEAR_DIFF = 10

def ue(s):
    return requests.utils.quote(str(s))


def dc(s):
    d = datetime.strptime(s, r"%d %b %Y")
    return d.strftime(r"%Y,%B,%d")


# then = ue("{:%d-%b-%Y}".format(now - relativedelta(years=YEAR_DIFF)))
then = "01-Jan-2014"
now = ue("{:%d-%b-%Y}".format(datetime.now()))
print(now)

def marketgetter(markets):
    b = dict()
    a = [i.split('">') for i in markets.get_attribute('innerHTML').split('</option>')]
    for i in a:
        if len(i) > 1:
            val =  i[0].split('value="')[1]
            if val != '0':
                b[i[1]] = val
    return b

comms = {
    "Food Grains": {
        "Rice": 3,
        "Wheat": 1,
        "Wheat Atta": 287,
        "Maida": 288
    },
    "Pulses": {
        "Gram": 263, "Tur": 260, "Urad": 264, "Moong": 265, "Masur": 259
    },
    "Edible Oils": {
        "Groundnut oil": 267,
        "Mustard Oil": 324,
        "Vanaspati": 273,
        # "Soya oil",
        # "Sunflower oil",
        # "Palm oil"
    },
    "Vegetables": {
        "Potato": 24,
        "Onion": 23,
        "Tomato": 78
    },
    "Others": {
        "Sugar": 48,
        "Gur": 74,
        # "Milk",
        "Tea": 44,
        # "Salt"
    }
}

def fnc(s):
    a = s.strip().replace('/','--')
    return a[:-1] if (a.endswith('.')) else a


if __name__ == '__main__':

    opts = Options()
    browser = Edge(options=opts)
    browser.get('https://agmarknet.gov.in/')
    sleep(2)

    states = Select(browser.find_element(by=By.ID, value='ddlState'))
    stname = states.options[STATE_NO].text
    stcode = states.options[STATE_NO].get_attribute('value')
    states.select_by_index(STATE_NO)

    sleep(1)

    districts = Select(browser.find_element(by=By.ID, value='ddlDistrict'))
    for i in range(DIST_NO, len(districts.options)):
        try:
            distname = districts.options[i].text
            distcode = districts.options[i].get_attribute('value')
        
            districts.select_by_index(i)
        except StaleElementReferenceException:
            print("\n\n\tstale element reference\n\n")
            districts = Select(browser.find_element(by=By.ID, value='ddlDistrict'))
            markets = browser.find_element(by=By.ID, value='ddlMarket')
            i -= 1
            continue

        sleep(0.5)
        
        districts = Select(browser.find_element(by=By.ID, value='ddlDistrict'))
        markets = browser.find_element(by=By.ID, value='ddlMarket')

        for k,v in marketgetter(markets).items():
            mrname = k
            mrcode = v
            for category in comms.keys():
                for commodity in comms[category].keys():
                    url = rf'https://agmarknet.gov.in/SearchCmmMkt.aspx?Tx_Commodity={ue(comms[category][commodity])}&Tx_State={ue(stcode)}&Tx_District={ue(distcode)}&Tx_Market={ue(mrcode)}&DateFrom={then}&DateTo={now}&Fr_Date={then}&To_Date={now}&Tx_Trend=2&Tx_CommodityHead={ue(commodity)}&Tx_StateHead={ue(stname)}&Tx_DistrictHead={ue(distname)}&Tx_MarketHead={ue(mrname)}'
                    req = requests.get(url)
                    reqdata = BeautifulSoup(req.text, 'html.parser')
                    reslabel = reqdata.find(id="cphBody_Label_Result")
                    if " Not Available" in reslabel.text:
                        print(f'NOT FOUND {stname} {STATE_NO} > {distname} {i} > {mrname} > {commodity}')
                        continue
                    elif not reslabel.text:
                        table = reqdata.find(id="cphBody_GridViewBoth")
                        filedata = 'year,month,date,arrival,min,max,modal\n'
                        for row in tuple(table.children)[2:-3]:
                            cols = tuple(row.children)
                            try:
                                ymd = dc(cols[10].text)
                                filedata += f'{ymd},{cols[6].text},{cols[7].text},{cols[8].text},{cols[9].text}\n'
                            except ValueError:
                                continue

                        stname = fnc(stname)
                        distname = fnc(distname)
                        mrname = fnc(mrname)

                        if stname not in os.listdir(): os.mkdir(stname)
                        os.chdir(stname)
                        if distname not in os.listdir():  os.mkdir(distname)
                        os.chdir(distname)
                        if mrname not in os.listdir(): os.mkdir(mrname)
                        os.chdir(mrname)
                        if category not in os.listdir():  os.mkdir(category)
                        os.chdir(category)
                        if commodity not in os.listdir():  os.mkdir(commodity)
                        os.chdir(commodity)

                        with open('data.csv', 'w') as f:
                            f.write(filedata)
                            print(f'DATA WRITTEN {stname} > {distname} > {mrname} > {commodity}')
                        os.chdir('../../../../..')
                            
    sleep(2)
import yfinance as yf
import time
import pandas as pd
import os
import requests
from datetime import datetime

# Getting DW API key from GH repo secrets
ACCESS_TOKEN = os.getenv('DW_API_KEY')

# Function used to add new data to datawrapper chart via a pandas dataframe and 
# places the latest update date in the chart notes
def updateChart(dw_chart_id, dataSet, metadataJSON, dw_api_key):

    headers = {
    "Accept": "*/*",
    "Content-Type": "application/json",
    "Authorization": f"Bearer {dw_api_key}"
    }

    stringDataSet = dataSet.to_csv(path_or_buf=None, index=False, header=True)   

    dataRefresh = requests.put(url=f"https://api.datawrapper.de/v3/charts/{dw_chart_id}/data", 
    data=stringDataSet,
    headers={"Authorization": f"Bearer {dw_api_key}"}
    )

    dataRefresh.raise_for_status()

    time.sleep(2)

    notesRes = requests.patch(url=f"https://api.datawrapper.de/v3/charts/{dw_chart_id}",
    json=metadataJSON,
    headers=headers)

    notesRes.raise_for_status()

    time.sleep(2)

    publishRes = requests.post(url=f"https://api.datawrapper.de/v3/charts/{dw_chart_id}/publish",
    headers=headers)

    publishRes.raise_for_status()

    time.sleep(2)

    imgHeaders = {
        "Accept": "image/png",
        "Authorization": f"Bearer {dw_api_key}"
        }
    pngDwnldRes = requests.get(url=f"https://api.datawrapper.de/v3/charts/{dw_chart_id}/export/png?unit=px&mode=rgb&width=700&height=auto&plain=false&scale=1&zoom=2&download=false&fullVector=false&ligatures=true&transparent=false&logo=auto&dark=false",
    headers=imgHeaders)

    pngDwnldRes.raise_for_status()
    latestPNG = pngDwnldRes.content

    file = open('latestCryptoMarketImage.png', 'wb')
    file.write(latestPNG)
    file.close()

# Function to use yfinance to get ticker data
def getYFinance(ticker):
    yfRes = yf.Ticker(ticker)
    tickerDF = yfRes.history(period='5d', interval='1d', prepost=False, auto_adjust=False, actions=False)
    time.sleep(0.25)
    tickerDF.reset_index(level=0, inplace=True)
    tickerDFSorted = tickerDF.sort_values(by=['Date'], ascending=False).reset_index(drop=True)
    todayPrice = float(tickerDFSorted['Close'][0])
    yesterdayPrice = float(tickerDFSorted['Close'][1])
    dayChangePrice = todayPrice - yesterdayPrice
    dodChgYF = round(((todayPrice - yesterdayPrice) / yesterdayPrice) * 100, 2)
    
    return(todayPrice, dayChangePrice, dodChgYF)

# cm = yf.Tickers("BTC-USD ETH-USD BNB-USD XRP-USD ADA-USD")
cm_tickers = ["BTC-USD", "ETH-USD", "BNB-USD", "XRP-USD", "ADA-USD"]

latestIndexList = []
idxChgList = []
pctCngList = []
colorsList = []

for ticker in cm_tickers:
    time.sleep(3)
    stock = getYFinance(ticker=ticker)
    idxVal = stock[0]
    idxChg = stock[1]
    pctCng = stock[2]
    latestIndexList.append(idxVal)
    idxChgList.append(idxChg)
    pctCngList.append(pctCng)

    if idxChg < 0:
        colorsList.append("#de2d26")
    else:
        colorsList.append("#31a354")

cmDict = {'Index': ['Bitcoin (BTC)',
                    'Ethereum (ETH)',
                    'Binance Coin (BNB)',
                    'Ripple (XRP)',
                    'Cardano (ADA)'], 
            'Level': latestIndexList,
            'Change': idxChgList,
            '% Change': pctCngList}

cmDF = pd.DataFrame(data=cmDict)

cmDF.to_csv("cryptoMarketIndices.csv", index=False)

fileDate = str(datetime.today().strftime('%B %d, %Y'))

# Formerly had notes of Data from Yahoo Finance. Updated {fileDate} in f-string on line 102
callBack = {"metadata": {
                    "annotate": {
                        "notes": f""
                    },
                    "visualize": {
                        "columns": {
                            "Change": {
                                "customColorText": {
                                    "Bitcoin (BTC)": colorsList[0], 
                                    "Ethereum (ETH)": colorsList[1],
                                    "Binance Coin (BNB)": colorsList[2],
                                    "Ripple (XRP)": colorsList[3],  
                                    "Cardano (ADA)": colorsList[4]
                                    }
                                },
                            "% Change": {
                                "customColorText": {
                                    "Bitcoin (BTC)": colorsList[0], 
                                    "Ethereum (ETH)": colorsList[1],
                                    "Binance Coin (BNB)": colorsList[2],
                                    "Ripple (XRP)": colorsList[3],  
                                    "Cardano (ADA)": colorsList[4]
                                    }
                                }
                            }
                        }
                }
            }

updateChart("MNC6j", cmDF, callBack, ACCESS_TOKEN)
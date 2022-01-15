import hmac
import time
import hashlib
import requests
import json
from urllib.parse import urlencode
from values import *
import sys
import traceback
from configparser import ConfigParser
from binance.client import Client

file = "config.ini"
config = ConfigParser()
config.read(file)

client = Client(apikey[0], secretkey[0])

# api key: MWdFl06XvjKBdZxVJDwOORlv6xvnICiDQXtleKLjdq46LuvtsKVNbR16h7qe10Zr
# secret: eNVNnb87eYzLeHpHbcuujplvZmQpkZqED4d5WGOmKa7bFGBiWbLLuRY8f1JC1XEU

''' ======  begin of functions, you don't need to touch ====== '''
def hashing(query_string):
    SECRET = secretkey[0]

    return hmac.new(SECRET.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

def get_timestamp():
    return int(time.time() * 1000)

def dispatch_request(http_method):
    KEY = apikey[0]

    session = requests.Session()
    session.headers.update({
        'Content-Type': 'application/json;charset=utf-8',
        'X-MBX-APIKEY': KEY
    })
    return {
        'GET': session.get,
        'DELETE': session.delete,
        'PUT': session.put,
        'POST': session.post,
    }.get(http_method, 'GET')

# used for sending request requires the signature
def send_signed_request(http_method, url_path, payload={}):
    BASE_URL = 'https://testnet.binance.vision'  # testnet base url

    query_string = urlencode(payload)
    # replace single quote to double quote
    query_string = query_string.replace('%27', '%22')
    if query_string:
        query_string = "{}&timestamp={}".format(query_string, get_timestamp())
    else:
        query_string = 'timestamp={}'.format(get_timestamp())

    url = BASE_URL + url_path + '?' + query_string + '&signature=' + hashing(query_string)
    print("{} {}".format(http_method, url))
    params = {'url': url, 'params': {}}
    response = dispatch_request(http_method)(**params)
    return response.json()

# used for sending public data request
def send_public_request(url_path, payload={}):
    KEY = apikey[0]
    SECRET = secretkey[0]
    BASE_URL = 'https://testnet.binance.vision'  # testnet base url

    query_string = urlencode(payload, True)
    url = BASE_URL + url_path
    if query_string:
        url = url + '?' + query_string
    print("{}".format(url))
    response = dispatch_request('GET')(url=url)
    return response.json()

def convertvalues():
    try:
        if len(str(fromconvert[0])) == 4:
            print("starting to convert....")

            params = {
                "symbol": toconvert[0] + fromconvert[0],
                "side": "BUY",
                "type": "MARKET",
                "quantity": quantityconvert[0],
            }

            response = send_signed_request('POST', '/api/v3/order', params)

            time.sleep(1)

            if "status" in response:
                if response["status"] == "FILLED":
                    print("Conversion completed")
            elif "code" in response:
                print(f" Conversion error: {response}. Exiting program")
                sys.exit()

        elif len(str(fromconvert[0])) == 3:
            print("starting to convert....")

            params = {
                "symbol": fromconvert[0] + toconvert[0],
                "side": "SELL",
                "type": "MARKET",
                "quantity": quantityconvert[0],
            }

            response = send_signed_request('POST', '/api/v3/order', params)

            time.sleep(1)

            if "status" in response:
                if response["status"] == "FILLED":
                    print("Conversion completed")
            elif "code" in response:
                print(f" Conversion error: {response}. Exiting program")
                sys.exit()

    except Exception as e:
        print("Cannot convert: {0}".format(e))
        traceback.print_exc()
        sys.exit()

def createorder():
    try:
        if symbol[0] and quant[0] and stoploss[0] and targetpercent[0] and limitmarket[0]:
            if buysell[0] == "BUY":
                print("buying instrument")

                if limitmarket[0] == "MARKET":
                    params = {
                        "symbol": symbol[0],
                        "side": buysell[0],
                        "type": limitmarket[0],
                        "quantity": quant[0],

                    }
                elif limitmarket[0] == "LIMIT":
                    params = {
                        "symbol": symbol[0],
                        "side": buysell[0],
                        "type": limitmarket[0],
                        "quantity": quant[0],
                        "timeInForce": "FOK",
                        "price": limitprice[0],

                    }

                response = send_signed_request('POST', '/api/v3/order', params)

                print(response)
                time.sleep(1)

                if "status" in response:
                    if response["status"] == "FILLED":
                        print("order is filled.. processing to create stoploss/takeprofit")

                        tickerprice = getprice()

                        percentincrease = tickerprice + (targetpercent[0] * tickerprice) / 100

                        percentdecrease = tickerprice - (stoploss[0] * tickerprice) / 100

                        print(percentdecrease)
                        print(percentincrease)

                        params = {
                            "symbol": symbol[0],
                            "side": buysell[0],
                            "quantity": quant[0],
                            "price": percentincrease,  # take profit
                            "stopPrice": percentdecrease,  # stop loss
                        }

                        response = send_signed_request('POST', '/api/v3/order/oco', params)

                        if "listOrderStatus" in response:
                            print("stoploss/takeprofit order placed sucessfully")
                        elif "code" in response:
                            print(f"OCO error: {response}. Exiting program")
                            sys.exit()

                elif "code" in response:
                            print(f"OCO error: {response['code']}. Exiting program")
                            sys.exit()

            elif buysell[0] == "SELL":

                print("Executing sell order")

                if limitmarket[0] == "MARKET":
                    params = {
                        "symbol": symbol[0],
                        "side": buysell[0],
                        "type": limitmarket[0],
                        "quantity": quant[0],

                    }
                elif limitmarket[0] == "LIMIT":
                    params = {
                        "symbol": symbol[0],
                        "side": buysell[0],
                        "type": limitmarket[0],
                        "quantity": quant[0],
                        "timeInForce": "FOK",
                        "price": limitprice[0],

                    }

                response = send_signed_request('POST', '/api/v3/order', params)

                time.sleep(2)

                print(response)

                if "status" in response:
                    if response["status"] == "FILLED":
                        print("order executed sucessfully")
                elif "code" in response:
                            print(f" OCO error: {response}. Exiting program")
                            sys.exit()
        else:
            print("Cannot place order. One of the labels is not filled")
            sys.exit()

    except Exception as e:
        print("Cannot place order. make sure to click the checkboxes: {0}".format(e))
        traceback.print_exc()
        sys.exit()

def getprice():
    try:
        if symbol[0]:

            params = {
                "symbol": str(symbol[0]),
            }

            response = send_public_request("/api/v3/ticker/price", params)

            if "price" in response:
                return float(response["price"])
            elif "code" in response:
                            print(f"Error: Cannot get price...: {response['code']}. Exiting program")
                            sys.exit()
    except Exception as e:
        print("Cannot get instrument price. please fill the symbol label: {0}".format(e))
        traceback.print_exc()
        sys.exit()

def getbalances():
    try:
        response = send_signed_request('GET', '/api/v3/account')

        if "code" in response:
            print(f"Convert error: {response}. Exiting program")
            sys.exit()

        if "balances" in response:
                for balance in response['balances']:
                    print(balance)
    except:
        print("cannot retrieve balance: exiting...")
        sys.exit()
def mainfunction():
    apikey.append(config['trading']['apikey'])
    secretkey.append(config['trading']['secret'])

    getbalances()

    myinput = int(input("Trade: 1: Exchange: 2: 3: withdraw"))

    if myinput == 1:
        symbol.append(input("Enter symbol: ").upper())
        quant.append(float(input("Enter quantity: ")))
        stoploss.append(int(input("Enter Stoploss %: ")))
        targetpercent.append(int(input("Enter Take-profit %: ")))
        buysell.append(input("Buying an instrument: Buy: Selling an intrument: Sell: ").upper())
        limitmarket.append(input("Limit order: limit: market order: market: ").upper())

        print(limitmarket)

        if limitmarket[0] == "LIMIT":
            limitprice.append(float(input("Enter a limit price: "))) # value should have four 0 in price. example price is 121: Then the price should be 1210000

        createorder()

    elif myinput == 2:
        # collecting info
        fromasset = input("Enter asset you want to convert from: ").upper()
        toasset = input("Enter asset you want to convert to: ").upper()
        quanitites = int(input("Enter quantity of the conversion: ").upper())

        fromconvert.append(fromasset)
        toconvert.append(toasset)
        quantityconvert.append(quanitites)


        #converting
        convertvalues()
    elif myinput == 3:

        asset = str(input("Enter asset you want to transfer: ").upper())
        adress = str(input("Enter adress you want to transfer to: ").upper())
        quantity = float(input("Enter Quantity you want to transfer: ").upper())

        try:
            # name parameter will be set to the asset value by the client if not passed
            result = client.withdraw(
                asset=asset,
                address=adress,
                amount=quantity)
        except:
            print(result)
        else:
            print("Success")

''' ======  end of functions ====== '''
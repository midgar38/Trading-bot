import ccxt 
import time
#from pandas import DataFrame
import pandas as pd
import numpy as np
from datetime import datetime
#to handle connection error
import requests
#to read and write csv files
import csv
#import pandas-ta
import pandas_ta as ta


#Handle writing in a csv file
def append_list_as_row(file_name, list_of_elem):
    # Open file in append mode
    with open(file_name, 'a+', newline='') as write_obj:
        # Create a writer object from csv module
        csv_writer = csv.writer(write_obj)
        # Add contents of list as last row in the csv file
        csv_writer.writerow(list_of_elem)

#LIVE
exchange = ccxt.binance({
    'apiKey': 'YOUR KEY',
    'secret': 'YOUR SECRET',
    'enableRateLimit': True,
})

#To handle connection errors
url='https://api.binance.com/api/v3/exchangeInfo'
max_retries=50

try:
    r = requests.get(url,timeout=5)
    r.raise_for_status()
except requests.exceptions.HTTPError as errh:
    print ("Http Error:",errh)
    raise SystemExit(err)
except requests.exceptions.ConnectionError as errc:
    print ("Error Connecting:",errc)
    for i in range(max_retries):
        try:
            print("Trying to reconnect")
            time.sleep(30)
            r = requests.get(url,timeout=5)
            r.raise_for_status()
            break
        except Exception:
            pass
    else:
        print("Max retries reached")
    print("Connection successful")
except requests.exceptions.Timeout as errt:
    print ("Timeout Error:",errt)
    for i in range(max_retries):
        try:
            print("Trying to reconnect")
            time.sleep(30)
            r = requests.get(url,timeout=5)
            r.raise_for_status()
            break
        except Exception:
            pass
    else:
        print("Max retries reached, please restart manually")
    print("Connection successful")
except requests.exceptions.RequestException as err:
    print ("OOps: Something Else",err)
    raise SystemExit(e)
else:
    print('The request got executed')

print("The routine can now start")

#Loading markets
exchange.load_markets()
#print(exchange.has)

#Handling dates:
now = datetime.now()
print("Welcome, today, it is", now)


pairs = ['ETH/BTC', 'LINK/BTC', 'XTZ/BTC', 'LTC/BTC', 'ADA/BTC', 'ATOM/BTC', 'EOS/BTC', 'XMR/BTC']
symbol= ['ETH', 'LINK', 'XTZ', 'LTC', 'ADA', 'ATOM', 'EOS', 'XMR']
type = 'market'  # or 'market'
# side = 'buy'  # or 'sell' or 'trailing-stop'
# amount = 0.01
price = None  # or None

period=18
period_slope=10

check_balance=exchange.fetch_balance()


#For production
params = {}

#For testing purpose only
# params = {
#     'test': True,  # test if it's valid, but don't actually place it
# }

# Creating an empty dictionary 
myDict_1d = {} 
myDict_4h = {} 

total_open_orders=[]
for i in pairs:
    open_orders=exchange.fetch_open_orders(str(i))
    if len(open_orders) != 0:
        for j in range(len(open_orders)):
            total_open_orders.append(open_orders[j].get("info").get("orderId"))
            
print("There is in total {} open orders".format(len(total_open_orders)))

#Loop through pairs
for i in pairs:
    open_orders=exchange.fetch_open_orders(str(i))
    candles_1d = exchange.fetch_ohlcv(i, '1d')
    myDict_1d[i] = candles_1d
    df=pd.DataFrame(candles_1d).from_dict(myDict_1d) 
    pairs_lists=df[i].tolist()
    df=pd.DataFrame(pairs_lists, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
    df.insert(0, "Pair", [str(i) for j in range(len(df))], True) 
    
    bbands = df.ta.bbands(length=20)
    print("bbands is", bbands)

    adx = df.ta.adx(length=18)
    print("adx is", adx)

    x=[i for i in range(1,period_slope+1)]
    
    last_price_1d=df['close'].tail(period).to_list() 
    print("Prix sur les 18 derniers jours", last_price_1d)

    y=adx.tail(period_slope)['ADX_18'].to_list()
    last_DMP=adx.tail(1)['DMP_18'].item()
    last_DMN=adx.tail(1)['DMN_18'].item()
    last_ADX=adx.tail(1)['ADX_18'].item()
    # print("y is", y)
    model = np.polyfit(x, y, 1)
    #print("Linear model is", model)
    print("The ADX slope is", (str(i), model[0]))
    if model[0]>0:
        print("The market is trending on the daily timeframe.")
    else:
        print("The maket is trendless based on the daily timeframe.")

    candles_4h = exchange.fetch_ohlcv(i, '4h')
    myDict_4h[i] = candles_4h
    df=pd.DataFrame(candles_4h).from_dict(myDict_4h) 
    pairs_lists=df[i].tolist()
    df=pd.DataFrame(pairs_lists, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
    df.insert(0, "Pair", [str(i) for j in range(len(df))], True) 
    
    bbands_4h = df.ta.bbands(length=20)

    last_bbl_4h=bbands_4h.tail(1)['BBL_20_2.0'].item()
    last_bbu_4h=bbands_4h.tail(1)['BBU_20_2.0'].item()

    last_price_4h=df['close'].tail(1).item()
    print("Last price is", last_price_4h)

    amount_buy=round((0.1*check_balance['BTC']['free'])/last_price_4h,7)
    
    amount_sell=round(0.9*amount_buy,7)

    #stop lower BBANDS
    stop_price=round(0.9*last_bbl_4h,7)
    limit_price=round(float(0.99*stop_price),7)
    print("Limit price is", (str(i), round(limit_price,7)))

    #params2 specific to the stoploss order (buy order)
    params2 = {'stopPrice': stop_price}

    # Actual trading
    #Trendless markets --> ADX slope negative
    if model[0]<0 and last_price_4h<1.009*last_bbl_4h and check_balance['BTC']['free'] > 0.0002 and len(total_open_orders)<=12:
        
        order1 = exchange.create_order(str(i), type, 'buy', amount_buy, price, params)
        time.sleep(5)
        order2 = exchange.create_order(str(i), 'STOP_LOSS_LIMIT', side='sell', amount=amount_sell, price = limit_price, params=params2)
        append_list_as_row('test.csv', [now, str(i), 'buy', last_price_4h, round(limit_price,7)])
        print("Pair {}: buy initial order sent on {} at a price of {} BTC with a stop-loss at {}".format(str(i), now, last_price_4h, stop_price))

    elif model[0]<0 and last_price_4h>0.995*last_bbu_4h:

        if check_balance[str(i).split("/")[0]]['free'] != 0.0:
            amount_sell2=round(0.95*check_balance[str(i).split("/")[0]]['free'],7)
            #Empty=False!
            if len(open_orders) != 0:
                for j in range(len(open_orders)):
                    print(open_orders[j].get("info").get("orderId"))
                    order1= exchange.cancel_order(open_orders[j].get("info").get("orderId"), str(i), params)
                    time.sleep(10)
                    order2 = exchange.create_order(str(i), type, 'sell', amount_sell2, price, params)
                    append_list_as_row('test.csv', [now, str(i), 'sell', last_price_4h])
                    print("Pair {}: sell initial order sent on {} at {} BTC.".format(str(i), now, last_price_4h))
            else:
                print("No open orders found.")
                order2 = exchange.create_order(str(i), type, 'sell', amount_sell2, price, params)
                append_list_as_row('test.csv', [now, str(i), 'sell', last_price_4h])
                print("Pair {}: sell initial order sent on {} at {} BTC.".format(str(i), now, last_price_4h)) 
        else:
            print("Pair {}: no initial position taken on {}. The last price is {} BTC".format(str(i), now, last_price_4h))

    #Trending markets --> ADX slope positive
    elif model[0]>0 and last_DMN>last_DMP and last_ADX>15:
        print("Strong downtrend: no more trading, just selling possible rallies.")
        if check_balance[str(i).split("/")[0]]['free'] != 0.0 and last_price_4h>0.995*last_bbu_4h:
            amount_sell2=round(0.95*check_balance[str(i).split("/")[0]]['free'],7)
            order2 = exchange.create_order(str(i), type, 'sell', amount_sell2, price, params)
            append_list_as_row('test.csv', [now, str(i), 'sell', last_price_4h])
            print("Pair {}: sell initial order sent on {} at {} BTC.".format(str(i), now, last_price_4h))
        else:
            print("Pair {}: no initial position taken on {}. The last price is {} BTC".format(str(i), now, last_price_4h))
    #ADX>15 --> strong trend underway
    elif model[0]>0 and last_DMP>last_DMN and last_ADX>15:

        print("Strong uptrend: trading authorized. Channel breakouts strategy to be used")
        if last_price_4h>max(last_price_1d) and check_balance['BTC']['free'] > 0.0002 and len(total_open_orders)<=12:
            order1 = exchange.create_order(str(i), type, 'buy', amount_buy, price, params)
            time.sleep(5)
            order2 = exchange.create_order(str(i), 'STOP_LOSS_LIMIT', side='sell', amount=amount_sell, price = limit_price, params=params2)
            append_list_as_row('test.csv', [now, str(i), 'buy', last_price_4h, round(limit_price,7)])
            print("Pair {}: buy initial order sent on {} at a price of {} BTC with a stop-loss at {}".format(str(i), now, last_price_4h, stop_price))

        elif model[0] < 0.1:
            if check_balance[str(i).split("/")[0]]['free'] != 0.0:
                amount_sell2=round(0.95*check_balance[str(i).split("/")[0]]['free'],7)
                #Empty=False!
                if len(open_orders) != 0:
                    for j in range(len(open_orders)):
                        print(open_orders[j].get("info").get("orderId"))
                        order1= exchange.cancel_order(open_orders[j].get("info").get("orderId"), str(i), params)
                        time.sleep(10)
                        order2 = exchange.create_order(str(i), type, 'sell', amount_sell2, price, params)
                        append_list_as_row('test.csv', [now, str(i), 'sell', last_price_4h])
                        print("Pair {}: sell initial order sent on {} at {} BTC.".format(str(i), now, last_price_4h))
                else:
                    print("No open orders found.")
                    order2 = exchange.create_order(str(i), type, 'sell', amount_sell2, price, params)
                    append_list_as_row('test.csv', [now, str(i), 'sell', last_price_4h])
                    print("Pair {}: sell initial order sent on {} at {} BTC.".format(str(i), now, last_price_4h)) 

        else:
            print("Not the time yet to buy or sell. We need more confirmations of the beginning or the end of the current uptrend")
    
    else:
        print("Pair {}: no initial position taken on {}. The last price is {} BTC".format(str(i), now, last_price_4h))


#Start of the while loop

#handle keyboard interrupt
try: 
    count=0
    while True:

        #To handle connection errors
        url='https://api.binance.com/api/v3/exchangeInfo'
        max_retries=50

        try:
            r = requests.get(url,timeout=5)
            r.raise_for_status()
        except requests.exceptions.HTTPError as errh:
            print ("Http Error:",errh)
            raise SystemExit(err)
        except requests.exceptions.ConnectionError as errc:
            print ("Error Connecting:",errc)
            for i in range(max_retries):
                try:
                    print("Trying to reconnect")
                    time.sleep(30)
                    r = requests.get(url,timeout=5)
                    r.raise_for_status()
                    break
                except Exception:
                    pass
            else:
                print("Max retries reached")
            print("Connection successful")
        except requests.exceptions.Timeout as errt:
            print ("Timeout Error:",errt)
            for i in range(max_retries):
                try:
                    print("Trying to reconnect")
                    time.sleep(30)
                    r = requests.get(url,timeout=5)
                    r.raise_for_status()
                    break
                except Exception:
                    pass
            else:
                print("Max retries reached, please restart manually")
            print("Connection successful")
        except requests.exceptions.RequestException as err:
            print ("OOps: Something Else",err)
            raise SystemExit(e)
        else:
            print('The request got executed')

        print("The routine can now start for count {}".format(count))
        now = datetime.now()

        time.sleep(3600)

        for i in pairs:
            open_orders=exchange.fetch_open_orders(str(i))
            if len(open_orders) != 0:
                for j in range(len(open_orders)):
                    total_open_orders.append(open_orders[j].get("info").get("orderId"))
                    
        print("There is in total {} open orders".format(len(total_open_orders)))

        #Loop through pairs
        for i in pairs:
            open_orders=exchange.fetch_open_orders(str(i))
            candles_1d = exchange.fetch_ohlcv(i, '1d')
            myDict_1d[i] = candles_1d
            df=pd.DataFrame(candles_1d).from_dict(myDict_1d) 
            pairs_lists=df[i].tolist()
            df=pd.DataFrame(pairs_lists, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
            df.insert(0, "Pair", [str(i) for j in range(len(df))], True) 
            
            bbands = df.ta.bbands(length=20)
            print("bbands is", bbands)

            adx = df.ta.adx(length=18)
            print("adx is", adx)

            x=[i for i in range(1,period_slope+1)]
            
            last_price_1d=df['close'].tail(period).to_list() 
            print("Prix sur les 18 derniers jours", last_price_1d)

            y=adx.tail(period_slope)['ADX_18'].to_list()
            last_DMP=adx.tail(1)['DMP_18'].item()
            last_DMN=adx.tail(1)['DMN_18'].item()
            last_ADX=adx.tail(1)['ADX_18'].item()
            model = np.polyfit(x, y, 1)
            print("The ADX slope is", (str(i), model[0]))
            if model[0]>0:
                print("The market is trending on the daily timeframe.")
            else:
                print("The maket is trendless based on the daily timeframe.")


            candles_4h = exchange.fetch_ohlcv(i, '4h')
            myDict_4h[i] = candles_4h
            df=pd.DataFrame(candles_4h).from_dict(myDict_4h) 
            pairs_lists=df[i].tolist()
            df=pd.DataFrame(pairs_lists, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
            df.insert(0, "Pair", [str(i) for j in range(len(df))], True) 
            
            bbands_4h = df.ta.bbands(length=20)

            last_bbl_4h=bbands_4h.tail(1)['BBL_20_2.0'].item()
            last_bbu_4h=bbands_4h.tail(1)['BBU_20_2.0'].item()

            last_price_4h=df['close'].tail(1).item()
            print("Last price is", last_price_4h)
            amount_buy=round((0.1*check_balance['BTC']['free'])/last_price_4h,7)

            
            amount_sell=round(0.9*amount_buy,7)

            #stop lower BBANDS
            stop_price=round(0.9*last_bbl_4h,7)
            limit_price=round(float(0.99*stop_price),7)
            print("Limit price is", (str(i), round(limit_price,7)))

            #params2 specific to the stoploss order (buy order)
            params2 = {'stopPrice': stop_price}

            # Actual trading
            #Trendless markets --> ADX slope negative
            if model[0]<0 and last_price_4h<1.009*last_bbl_4h and check_balance['BTC']['free'] > 0.0002 and len(total_open_orders)<=12:
                
                order1 = exchange.create_order(str(i), type, 'buy', amount_buy, price, params)
                time.sleep(5)
                order2 = exchange.create_order(str(i), 'STOP_LOSS_LIMIT', side='sell', amount=amount_sell, price = limit_price, params=params2)
                append_list_as_row('test.csv', [now, str(i), 'buy', last_price_4h, round(limit_price,6)])
                print("Pair {}: buy order sent on {} at a price of {} BTC with a stop-loss at {}".format(str(i), now, last_price_4h, stop_price))

            elif model[0]<0 and last_price_4h>0.995*last_bbu_4h:

                if check_balance[str(i).split("/")[0]]['free'] != 0.0:
                    amount_sell2=round(0.95*check_balance[str(i).split("/")[0]]['free'],7)
                    #Empty=False!
                    if len(open_orders) != 0:
                        for j in range(len(open_orders)):
                            print(open_orders[j].get("info").get("orderId"))
                            order1= exchange.cancel_order(open_orders[j].get("info").get("orderId"), str(i), params)
                            time.sleep(10)
                            order2 = exchange.create_order(str(i), type, 'sell', amount_sell2, price, params)
                            append_list_as_row('test.csv', [now, str(i), 'sell', last_price_4h])
                            print("Pair {}: sell initial order sent on {} at {} BTC.".format(str(i), now, last_price_4h))
                    else:
                        print("No open orders found.")
                        order2 = exchange.create_order(str(i), type, 'sell', amount_sell2, price, params)
                        append_list_as_row('test.csv', [now, str(i), 'sell', last_price_4h])
                        print("Pair {}: sell initial order sent on {} at {} BTC.".format(str(i), now, last_price_4h)) 

            #Trending markets --> ADX slope positive
            elif model[0]>0 and last_DMN>last_DMP and last_ADX>15:
                print("Strong downtrend: no more trading except selling possible rallies.")
                if check_balance[str(i).split("/")[0]]['free'] != 0.0 and last_price_4h>0.995*last_bbu_4h:
                    amount_sell2=round(0.95*check_balance[str(i).split("/")[0]]['free'],7)
                    order2 = exchange.create_order(str(i), type, 'sell', amount_sell2, price, params)
                    append_list_as_row('test.csv', [now, str(i), 'sell', last_price_4h])
                    print("Pair {}: sell initial order sent on {} at {} BTC.".format(str(i), now, last_price_4h))
                else:
                    print("Pair {}: no initial position taken on {}. The last price is {} BTC".format(str(i), now, last_price_4h))

            #ADX>15 --> strong trend underway
            elif model[0]>0 and last_DMP>last_DMN and last_ADX>15:

                print("Strong uptrend: trading authorized. Channel breakouts strategy to be used")
                if last_price_4h>max(last_price_1d) and check_balance['BTC']['free'] > 0.0002 and len(total_open_orders)<=12:
                    order1 = exchange.create_order(str(i), type, 'buy', amount_buy, price, params)
                    time.sleep(5)
                    order2 = exchange.create_order(str(i), 'STOP_LOSS_LIMIT', side='sell', amount=amount_sell, price = limit_price, params=params2)
                    append_list_as_row('test.csv', [now, str(i), 'buy', last_price_4h, round(limit_price,7)])
                    print("Pair {}: buy order sent on {} at a price of {} BTC with a stop-loss at {}".format(str(i), now, last_price_4h, stop_price))

                elif model[0] < 0.1:
                    if check_balance[str(i).split("/")[0]]['free'] != 0.0:
                        amount_sell2=round(0.95*check_balance[str(i).split("/")[0]]['free'],7)
                        #Empty=False!
                        if len(open_orders) != 0:
                            for j in range(len(open_orders)):
                                print(open_orders[j].get("info").get("orderId"))
                                order1= exchange.cancel_order(open_orders[j].get("info").get("orderId"), str(i), params)
                                time.sleep(10)
                                order2 = exchange.create_order(str(i), type, 'sell', amount_sell2, price, params)
                                append_list_as_row('test.csv', [now, str(i), 'sell', last_price_4h])
                                print("Pair {}: sell initial order sent on {} at {} BTC.".format(str(i), now, last_price_4h))
                        else:
                            print("No open orders found.")
                            order2 = exchange.create_order(str(i), type, 'sell', amount_sell2, price, params)
                            append_list_as_row('test.csv', [now, str(i), 'sell', last_price_4h])
                            print("Pair {}: sell initial order sent on {} at {} BTC.".format(str(i), now, last_price_4h)) 

                else:
                    print("Not the time yet to buy or sell. We need more confirmation of the beginning or the end of the current uptrend")
            
            else:
                print("Pair {}: no initial position taken on {}. The last price is {} BTC".format(str(i), now, last_price_4h))

        count=count+1

except KeyboardInterrupt:

    print("\nYou are now exiting the program")

    raise SystemExit
    sys.exit()

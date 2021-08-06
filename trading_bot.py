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
print(ta.version)

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
print("Welcome, today, it is ", now)

#You can add as many pairs/symbols as necesary
pairs = ['ETH/BTC', 'LINK/BTC', 'XTZ/BTC', 'LTC/BTC', 'ADA/BTC', 'ATOM/BTC', 'EOS/BTC', 'XMR/BTC','BNB/BTC', 'NANO/BTC', 'VET/BTC', 'BCH/BTC', 'XRP/BTC']
symbol= ['ETH', 'LINK', 'XTZ', 'LTC', 'ADA', 'ATOM', 'EOS', 'XMR', 'BNB', 'NANO', 'VET','BCH', 'XRP']
type = 'market'  # or 'market'

price = None  # or None

#The user can adjust these periods. Careful here, this is often exchange dependant.
#Breakout period
period=18
#Period of the slope overwhich the ADX and the CMF slope are calculated
period_long=10
period_short=5
#Total number of orders
MAX_NUM_ALGO_ORDERS=20
#Number of orders per coin
MAX_NUM_ORDERS=5
#Trading fees in %
trading_fees=0.075

check_balance=exchange.fetch_balance()
# print(check_balance['ETH'])
# print(check_balance['ETH']['free'])
print("BTC left for trading: ", check_balance['BTC']['free'])
# print("used fund", check_balance['BTC']['used'])

#For production, standard buy/sell order
params = {}

#For testing purpose only
# params = {
#     'test': True,  # test if it's valid, but don't actually place it
# }

# Creating an empty dictionary 
myDict_1d = {} 
myDict_4h = {} 

#How many open orders in total? 
total_open_orders=[]
for i in pairs:
    open_orders=exchange.fetch_open_orders(str(i))
    #How many open orders in total?
    if len(open_orders) != 0:
        for j in range(len(open_orders)):
            # print(open_orders[j].get("info").get("orderId"))
            total_open_orders.append(open_orders[j].get("info").get("orderId"))
        print("There is {} open orders for {}".format(len(open_orders), str(i)))
          
print("There is in total {} open orders".format(len(total_open_orders)))

#Loop through pairs
for i in pairs:
    #Fetch open orders
    open_orders=exchange.fetch_open_orders(str(i))
    try:
        candles_1d = exchange.fetch_ohlcv(i, '1d')
    except IndexError:
        None
    myDict_1d[i] = candles_1d
    df_1d=pd.DataFrame(candles_1d).from_dict(myDict_1d) 
    pairs_lists_1d=df_1d[i].tolist()
    #data frames toujours mais en se debarassant des listes
    df_1d=pd.DataFrame(pairs_lists_1d, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
    #insertion of a pair column (first one here)
    df_1d.insert(0, "Pair", [str(i) for j in range(len(df_1d))], True) 
    # print(df)
    
    # print("\n")
    last_price_1d=df_1d['Close'].tail(1).item()
    print("\nThe latest price for the pair {} is {}.".format(str(i), last_price_1d))

    #calculation of the daily adx
    adx = df_1d.ta.adx(length=18)
    # print("adx is", adx)

    #calculation of the daily CMF
    cmf = df_1d.ta.cmf(length=20)
    #Conversion from a pandas series to a pandas dataframe
    cmf_frame=cmf.to_frame()
    # print("CMF is", cmf_frame)

    x=[i for i in range(1,period_long+1)]
    #Only over 3 days for example.
    # x2=[1,2,3]
    x2=[i for i in range(1,period_short+1)]

    #last prices over a period of a certain number of days
    last_price_1d_period=df_1d['close'].tail(period).to_list() 
    print("Price over the last 18 days:", last_price_1d_period)

    #Latest 10 values of ADX
    y=adx.tail(period_long)['ADX_18'].to_list()
    y1=cmf_frame.tail(period_long)['CMF_20'].to_list()

    last_DMP=adx.tail(1)['DMP_18'].item()
    last_DMN=adx.tail(1)['DMN_18'].item()
    last_ADX=adx.tail(1)['ADX_18'].item()
    last_CMF=cmf_frame.tail(1)['CMF_20'].item()

    #Latest "period_short" values of ADX
    y2=adx.tail(period_short)['ADX_18'].to_list()
    #Latest "period_short" values of CMF
    y3=cmf_frame.tail(period_short)['CMF_20'].to_list()

    # print("y is", y)
    model = np.polyfit(x, y, 1)
    model1 = np.polyfit(x, y1, 1)
    model2 = np.polyfit(x2, y2, 1)
    model3 = np.polyfit(x2, y3, 1)


    #print("Linear model is", model)
    print("The ADX slope longer term is", (str(i), model[0]))
    print("The ADX slope shorter term is", (str(i), model2[0]))

    if model[0]>0:
        print("The market is trending on the daily timeframe for the longer term model.")
    else:
        print("The maket is trendless based on the daily timeframe.")

    if model2[0]>0:
        print("The market is trending on the daily timeframe for the shorter term model.")
    else:
        print("The maket is trendless based on the daily timeframe.")

    print("The CMF slope longer term is", (str(i), model1[0]))
    print("The CMF slope shorter term is", (str(i), model3[0]))

    if model1[0]>0:
        print("The CMF is positive over the past 10 days based on the daily timeframe.")
    else:
        print("The CMF is negative over the past 10 days based on the daily timeframe.")

    if model3[0]>0:
        print("The CMF is positive over the past 5 days based on the daily timeframe.")
    else:
        print("The CMF is negative over the past 5 days based on the daily timeframe.")

    #candles_4h is a list of lists!
    try:
        candles_4h = exchange.fetch_ohlcv(i, '4h')
    except IndexError:
        None
    #Definition of a dictionary to separate pairs
    myDict_4h[i] = candles_4h

    #Back to dataframes of lists
    df_4h=pd.DataFrame(candles_4h).from_dict(myDict_4h) 
    pairs_lists=df_4h[i].tolist()
    #Still dataframes but with no lists.
    df_4h=pd.DataFrame(pairs_lists, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
    #insertion of a pair column (first one here) en position 0 donc.
    df_4h.insert(0, "Pair", [str(i) for j in range(len(df_4h))], True) 
    # print(df)

    last_price_4h=df_4h['Close'].tail(1).item()
    print("Last price is", last_price_4h)

    #calculation of the 4h ATR
    #calculation ATR: to manage risk. How many ATR are you risking per trade? To be used for posiiton sizing.
    atr = df_4h.ta.atr(length=18)
    # print("atr is", atr)
    #Conversion from a pandas series to a pandas dataframe
    atr_frame=atr.to_frame()
    # print("ATR is", atr_frame)
    last_atr=atr_frame.tail(1)['ATR_18'].item()
    print("The latest ATR is:", last_atr)
    stop_value_trend=3*last_atr
    stop_value_trendless=2*last_atr

    stop_loss_trend=last_price_4h-stop_value_trend
    stop_loss_trendless=last_price_4h-stop_value_trendless
    
    #calculation of the 4h bbands, stdev = 2 by default ON A 4H BASIS this time.
    bbands_4h = df_4h.ta.bbands(length=20)
    # print("bbands is", bbands_4h)
    #bbands stdev=4

    last_bbl_4h=bbands_4h.tail(1)['BBL_20_2.0'].item()
    last_bbu_4h=bbands_4h.tail(1)['BBU_20_2.0'].item()
    last_bbm_4h=bbands_4h.tail(1)['BBM_20_2.0'].item()
    # bbw_2stdev=(last_bbu_4h-last_bbl_4h)/last_bbm_4h
    #bbw_4stdev=

    print("Last bbl 4h is", last_bbl_4h)
    print("Last bbu 4h is", last_bbu_4h)
    print("Last bbm 4h is", last_bbm_4h)
    # print("Last bbw_2stdev is", bbw_2stdev)
    print("Total number of open orders: ", len(total_open_orders))
    print("Total number of open orders for the pairs: ", len(open_orders))

    # last_price_4h=df['close'].tail(1).item()
    # print("Last price is", last_price_4h)

    # if check_balance['BTC']['free'] > 0.00015 #0.00015 is to ensure that when we sell we will be above the
    #bare minimum in value i.e. 0.0001 BTC.

    #ATR based stop-losses and limit prices
    params_atr_trend = {'stopPrice': stop_loss_trend}
    limit_price_atr_trend=round(float(0.99*stop_loss_trend),7)

    params_atr_trendless = {'stopPrice': stop_loss_trendless}
    limit_price_atr_trendless=round(float(0.99*stop_loss_trendless),7)

    #Position sizing
    #Percentage risked on each trade: 0.5% of what is left of BTC on your account.
    risk_percentage=0.005*check_balance['BTC']['free']

    amount_buy_trend=round(risk_percentage/stop_value_trend,7)
    amount_buy_trendless=round(risk_percentage/stop_value_trendless,7)

    #amount sell for the stop loss
    amount_sell_trend=round(0.95*amount_buy_trend,7)
    amount_sell_trendless=round(0.95*amount_buy_trendless,7)

    #Actual trading
    #Trendless markets --> ADX slope negative, longer term model
    if model[0]<0 and last_ADX<25 and last_price_4h<1.009*last_bbl_4h and check_balance['BTC']['free'] > 0.0015 and amount_buy_trendless*last_price_4h<check_balance['BTC']['free'] and len(total_open_orders)+1<=MAX_NUM_ALGO_ORDERS and len(open_orders)+1<=MAX_NUM_ORDERS:
        
        print("Trendless market, opportunity to buy on the bbl.")
        order1 = exchange.create_order(str(i), type, 'buy', amount_buy_trendless, price, params)
        time.sleep(10)
        order2 = exchange.create_order(str(i), 'STOP_LOSS_LIMIT', side='sell', amount=amount_sell_trendless, price = limit_price_atr_trendless, params=params_atr_trendless)
        append_list_as_row('test.csv', [now, str(i), 'buy', last_price_4h, round(limit_price_atr_trendless,7)])
        print("Pair {}: buy initial order sent on {} at a price of {} BTC with a stop-loss at {}".format(str(i), now, last_price_4h, stop_loss_trendless))

    #Longer term model (=10 days). 
    elif model[0]<0 and last_ADX<25 and last_price_4h>0.995*last_bbu_4h: #and bbw_2stdev>0.1 else do not sell everyhting (half and then another half)
        print("Trendless market, opportunity to sell on the bbu.")
        amount_sell2=round(0.95*check_balance[str(i).split("/")[0]]['free'],7)

        #First checking if there is any open order to cancel. 
        if len(open_orders) == 0 and amount_sell2*last_price_4h > 0.00015:
            order2 = exchange.create_order(str(i), type, 'sell', amount_sell2, price, params)
            time.sleep(10)
        
        elif len(open_orders) == 0 and amount_sell2*last_price_4h < 0.00015:
            print("Pair {}: not enough funds for selling {}. The last price is {} BTC".format(str(i), now, last_price_4h))

        elif len(open_orders) != 0 :
            print("Canceling open orders")
            for j in range(len(open_orders)):
                print(open_orders[j].get("info").get("orderId"))
                order1= exchange.cancel_order(open_orders[j].get("info").get("orderId"), str(i), params)
                time.sleep(10)

            if amount_sell2*last_price_4h > 0.00015:
                order2 = exchange.create_order(str(i), type, 'sell', amount_sell2, price, params)
                append_list_as_row('test.csv', [now, str(i), 'sell', last_price_4h])
                time.sleep(10)
            
            else:
                print("Pair {}: not enough funds for selling {}. The last price is {} BTC".format(str(i), now, last_price_4h))

        elif len(open_orders) != 0 and amount_sell2*last_price_4h < 0.00015:
            print("Pair {}: not enough funds for selling {}. The last price is {} BTC".format(str(i), now, last_price_4h))

        else:
            print("Pair {}, no option here on {}. The last price is {} BTC".format(str(i), now, last_price_4h))

    #Trending markets --> ADX slope positive 
    #Strong downtrend underway, longer term model, no more trading.
    elif model[0]>0 and model1[0]<0 and last_DMN>last_DMP and last_ADX>25:
        print("Strong downtrend: no more trading, selling what is left.")
        amount_sell2=round(0.95*check_balance[str(i).split("/")[0]]['free'],7)

        #First, we look at if there is any open orders to cancel.
        if len(open_orders) == 0 and amount_sell2*last_price_4h > 0.00015:
            order2 = exchange.create_order(str(i), type, 'sell', amount_sell2, price, params)
            time.sleep(10)
        
        elif len(open_orders) == 0 and amount_sell2*last_price_4h < 0.00015:
            print("Pair {}: not enough funds for selling {}. The last price is {} BTC".format(str(i), now, last_price_4h))

        elif len(open_orders) != 0 :
            print("Canceling open orders")
            for j in range(len(open_orders)):
                print(open_orders[j].get("info").get("orderId"))
                order1= exchange.cancel_order(open_orders[j].get("info").get("orderId"), str(i), params)
                time.sleep(10)

            if amount_sell2*last_price_4h > 0.00015:
                order2 = exchange.create_order(str(i), type, 'sell', amount_sell2, price, params)
                append_list_as_row('test.csv', [now, str(i), 'sell', last_price_4h])
                time.sleep(10)
            
            else:
                print("Pair {}: not enough funds for selling {}. The last price is {} BTC".format(str(i), now, last_price_4h))

        elif len(open_orders) != 0 and amount_sell2*last_price_4h < 0.00015:
            print("Pair {}: not enough funds for selling {}. The last price is {} BTC".format(str(i), now, last_price_4h))

        else:
            print("Pair {}, no option here on {}. The last price is {} BTC".format(str(i), now, last_price_4h))
            
    #ADX>15 --> strong uptrend underway (longer term model, 10 days slope)
    elif last_DMP>last_DMN:

        print("Strong uptrend: trading authorized. Channel breakouts strategy to be used")
        if model[0]>0 and last_price_4h>max(last_price_1d_period) and check_balance['BTC']['free'] > 0.0015 and amount_buy_trend*last_price_4h<check_balance['BTC']['free'] and len(total_open_orders)+1<=MAX_NUM_ALGO_ORDERS and last_ADX>25 and len(open_orders)+1<=MAX_NUM_ORDERS and model1[0]>0:
            order1 = exchange.create_order(str(i), type, 'buy', amount_buy_trend, price, params)
            #time.sleep to prevent any errors on the exchange.
            time.sleep(10)
            order2 = exchange.create_order(str(i), 'STOP_LOSS_LIMIT', side='sell', amount=amount_sell_trend, price = limit_price_atr_trend, params=params_atr_trend)
            append_list_as_row('test.csv', [now, str(i), 'buy', last_price_4h, round(limit_price_atr_trend,7)])
            print("Pair {}: buy initial order sent on {} at a price of {} BTC with a stop-loss at {}".format(str(i), now, last_price_4h, stop_loss_trend))
        #Overheated market
        elif model[0]>0 and model[0] < 0.1 and model1[0]<0 and last_ADX>last_DMP and last_ADX>last_DMN:
            print("Strong uptrend but time to sell, ADX is turning down as well as CMF, overheated market.")
            amount_sell2=round(0.95*check_balance[str(i).split("/")[0]]['free'],7)

            if len(open_orders) == 0 and amount_sell2*last_price_4h > 0.00015:
                order2 = exchange.create_order(str(i), type, 'sell', amount_sell2, price, params)
                time.sleep(10)
        
            elif len(open_orders) == 0 and amount_sell2*last_price_4h < 0.00015:
                print("Pair {}: not enough funds for selling {}. The last price is {} BTC".format(str(i), now, last_price_4h))

            elif len(open_orders) != 0 :
                print("Canceling open orders")
                for j in range(len(open_orders)):
                    print(open_orders[j].get("info").get("orderId"))
                    order1= exchange.cancel_order(open_orders[j].get("info").get("orderId"), str(i), params)
                    time.sleep(10)

                if amount_sell2*last_price_4h > 0.00015:
                    order2 = exchange.create_order(str(i), type, 'sell', amount_sell2, price, params)
                    append_list_as_row('test.csv', [now, str(i), 'sell', last_price_4h])
                    time.sleep(10)
                
                else:
                    print("Pair {}: not enough funds for selling {}. The last price is {} BTC".format(str(i), now, last_price_4h))

            elif len(open_orders) != 0 and amount_sell2*last_price_4h < 0.00015:
                print("Pair {}: not enough funds for selling {}. The last price is {} BTC".format(str(i), now, last_price_4h))

            else:
                print("Pair {}, no option here on {}. The last price is {} BTC".format(str(i), now, last_price_4h))

        #If bounce on the bbl --> BUY
        elif model[0]>0.1 and last_price_4h<1.009*last_bbl_4h and check_balance['BTC']['free'] > 0.0015 and amount_buy_trend*last_price_4h<check_balance['BTC']['free'] and len(total_open_orders)+1<=MAX_NUM_ALGO_ORDERS and last_ADX>25 and len(open_orders)+1<=MAX_NUM_ORDERS and model1[0]>0:
            print("Strong uptrend underway, dip, opportunity to buy the bbl.")
            order1 = exchange.create_order(str(i), type, 'buy', amount_buy_trend, price, params)
            time.sleep(10)
            order2 = exchange.create_order(str(i), 'STOP_LOSS_LIMIT', side='sell', amount=amount_sell_trend, price = limit_price_atr_trend, params=params_atr_trend)
            append_list_as_row('test.csv', [now, str(i), 'buy', last_price_4h, round(limit_price_atr_trend,7)])
            print("Pair {}: buy initial order sent on {} at a price of {} BTC with a stop-loss at {}".format(str(i), now, last_price_4h, stop_loss_trend))

        else:
            print("Not the time yet to buy or sell. We need more confirmations of the beginning or the end of the current uptrend")
    
    else:
        print("Pair {}: no initial position taken on {}. The last price is {} BTC".format(str(i), now, last_price_4h))

#Start of the while loop
#handle keyboard interrupt
try: 
#Initializing count
    count=0
    # for i in range(2):
    #while loop to connect every one hour or so
    while True:
        # print("\n")
        print("\nCounter is", count)
        time.sleep(1800)

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

        check_balance=exchange.fetch_balance()
        print("BTC left for trading: ", check_balance['BTC']['free'])
        # print("used fund", check_balance['BTC']['used'])

        #How many open orders in total? 
        total_open_orders=[]
        for i in pairs:
            open_orders=exchange.fetch_open_orders(str(i))
            #How many open orders in total?
            if len(open_orders) != 0:
                for j in range(len(open_orders)):
                    # print(open_orders[j].get("info").get("orderId"))
                    total_open_orders.append(open_orders[j].get("info").get("orderId"))
                print("There is {} open orders for {}".format(len(open_orders), str(i)))
                
        print("There is in total {} open orders".format(len(total_open_orders)))
        #Loop through pairs
        for i in pairs:
            #Fetch open orders
            open_orders=exchange.fetch_open_orders(str(i))
            #candles_1d is a list of lists! # Sometimes error here, how to handle it ? If list is empty, return an error.
            try:
                candles_1d = exchange.fetch_ohlcv(i, '1d')
            except IndexError:
                None
            #Definition of a dictionary to separate pairs
            myDict_1d[i] = candles_1d
            #Back to dataframes with lists inside
            df_1d=pd.DataFrame(candles_1d).from_dict(myDict_1d) 
            pairs_lists=df_1d[i].tolist()
            #Dataframes with no lists anymore.
            df_1d=pd.DataFrame(pairs_lists, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
            #insertion of a pair column (first one here)
            df_1d.insert(0, "Pair", [str(i) for j in range(len(df_1d))], True) 
            # print(df)

            # print("\n")
            last_price_1d=df_1d['Close'].tail(1).item()
            print("\nLast price is", last_price_1d)

            #Calculation of the daily adx
            adx = df_1d.ta.adx(length=18)
            # print("adx is", adx)

            #Calculation of the daily CMF
            cmf = df_1d.ta.cmf(length=20)
            #Conversion from a pandas series to a pandas dataframe
            cmf_frame=cmf.to_frame()
            # print("CMF is", cmf_frame)

            x=[i for i in range(1,period_long+1)]
            x2=[i for i in range(1,period_short+1)]

            
            #last prices over a period of a certain number of days
            last_price_1d_period=df_1d['close'].tail(period).to_list() 
            print("Price over the last 18 days:", last_price_1d_period)

            #Latest "period_slope" values of ADX
            y=adx.tail(period_long)['ADX_18'].to_list()
            y1=cmf_frame.tail(period_long)['CMF_20'].to_list()

            last_DMP=adx.tail(1)['DMP_18'].item()
            last_DMN=adx.tail(1)['DMN_18'].item()
            last_ADX=adx.tail(1)['ADX_18'].item()
            last_CMF=cmf_frame.tail(1)['CMF_20'].item()


            #Latest "period_short" values of ADX
            y2=adx.tail(period_short)['ADX_18'].to_list()
            #Latest "period_short" values of CMF
            y3=cmf_frame.tail(period_short)['CMF_20'].to_list()

            # print("y is", y)
            model = np.polyfit(x, y, 1)
            model1 = np.polyfit(x, y1, 1)
            model2 = np.polyfit(x2, y2, 1)
            model3 = np.polyfit(x2, y3, 1)

            #print("Linear model is", model)
            print("The ADX slope is", (str(i), model[0]))
            if model[0]>0:
                print("The market is trending on the daily timeframe.")
            else:
                print("The maket is trendless based on the daily timeframe.")

            print("The CMF slope is", (str(i), model1[0]))
            if model1[0]>0:
                print("The CMF is positive over the past 10 days based on the daily timeframe.")
            else:
                print("The CMF is negative over the past 10 days based on the daily timeframe.")

            #candles_4h is a list of lists
            try:
                candles_4h = exchange.fetch_ohlcv(i, '4h')
            except IndexError:
                None
        
            myDict_4h[i] = candles_4h
            df_4h=pd.DataFrame(candles_4h).from_dict(myDict_4h) 
            pairs_lists_4h=df_4h[i].tolist()
            df_4h=pd.DataFrame(pairs_lists_4h, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
            #insertion of a pair column (first one here) en position 0 donc.
            df_4h.insert(0, "Pair", [str(i) for j in range(len(df_4h))], True) 
            # print(df)

            last_price_4h=df_4h['Close'].tail(1).item()
            print("Last price is", last_price_4h)

            #calculation of the 4h ATR
            #calculation ATR: to manage risk. How many ATR are you risking per trade? To be used for posiiton sizing.
            atr = df_4h.ta.atr(length=18)
            # print("atr is", atr)
            #Conversion from a pandas series to a pandas dataframe
            atr_frame=atr.to_frame()
            # print("ATR is", atr_frame)
            last_atr=atr_frame.tail(1)['ATR_18'].item()
            print("The latest ATR is:", last_atr)
            stop_value_trend=3*last_atr
            stop_value_trendless=2*last_atr

            stop_loss_trend=last_price_1d-stop_value_trend
            stop_loss_trendless=last_price_1d-stop_value_trendless
            
            #calculation of the 4h bbands
            bbands_4h = df_4h.ta.bbands(length=20)
            # print("bbands is", bbands_4h)

            last_bbl_4h=bbands_4h.tail(1)['BBL_20_2.0'].item()
            last_bbu_4h=bbands_4h.tail(1)['BBU_20_2.0'].item()
            last_bbm_4h=bbands_4h.tail(1)['BBM_20_2.0'].item()
            print("Total number of open orders: ", len(total_open_orders))
            print("Total number of open orders for the pairs: ", len(open_orders))

            # last_price_4h=df['close'].tail(1).item()
            # print("Last price is", last_price_4h)

            #ATR based stop-losses and limit prices
            params_atr_trend = {'stopPrice': stop_loss_trend}
            limit_price_atr_trend=round(float(0.99*stop_loss_trend),7)

            params_atr_trendless = {'stopPrice': stop_loss_trendless}
            limit_price_atr_trendless=round(float(0.99*stop_loss_trendless),7)

            #Position sizing
            #Percentage risked on each trade: 0.5% of what is left of BTC on your account
            risk_percentage=0.005*check_balance['BTC']['free']

            amount_buy_trend=round(risk_percentage/stop_value_trend,7)
            amount_buy_trendless=round(risk_percentage/stop_value_trendless,7)

            #amount sell for the stop loss
            amount_sell_trend=round(0.95*amount_buy_trend,7)
            amount_sell_trendless=round(0.95*amount_buy_trendless,7)

            # Actual trading
            #Trendless markets --> ADX slope negative
            if model[0]<0 and last_ADX<25 and last_price_4h<1.009*last_bbl_4h and check_balance['BTC']['free'] > 0.0015 and amount_buy_trendless*last_price_4h<check_balance['BTC']['free'] and len(total_open_orders)+1<=MAX_NUM_ALGO_ORDERS and len(open_orders)+1<=MAX_NUM_ORDERS:
                print("Trendless market, opportunity to buy on the bbl.")
                order1 = exchange.create_order(str(i), type, 'buy', amount_buy_trendless, price, params)
                time.sleep(10)
                order2 = exchange.create_order(str(i), 'STOP_LOSS_LIMIT', side='sell', amount=amount_sell_trendless, price = limit_price_atr_trendless, params=params_atr_trendless)
                append_list_as_row('test.csv', [now, str(i), 'buy', last_price_4h, round(limit_price_atr_trendless,7)])
                print("Pair {}: buy order sent on {} at a price of {} BTC with a stop-loss at {}".format(str(i), now, last_price_4h, stop_loss_trendless))

            elif model[0]<0 and last_ADX<25 and last_price_4h>0.995*last_bbu_4h:
                print("Trendless market, opportunity to sell on the bbu.")

                amount_sell2=round(0.95*check_balance[str(i).split("/")[0]]['free'],7)
                #First checking if there is any open order to cancel. 
                if len(open_orders) == 0 and amount_sell2*last_price_4h > 0.00015:
                    order2 = exchange.create_order(str(i), type, 'sell', amount_sell2, price, params)
                    time.sleep(10)
                
                elif len(open_orders) == 0 and amount_sell2*last_price_4h < 0.00015:
                    print("Pair {}: not enough funds for selling {}. The last price is {} BTC".format(str(i), now, last_price_4h))

                elif len(open_orders) != 0 :
                    print("Canceling open orders")
                    for j in range(len(open_orders)):
                        print(open_orders[j].get("info").get("orderId"))
                        order1= exchange.cancel_order(open_orders[j].get("info").get("orderId"), str(i), params)
                        time.sleep(10)

                    if amount_sell2*last_price_4h > 0.00015:
                        order2 = exchange.create_order(str(i), type, 'sell', amount_sell2, price, params)
                        append_list_as_row('test.csv', [now, str(i), 'sell', last_price_4h])
                        time.sleep(10)
                    
                    else:
                        print("Pair {}: not enough funds for selling {}. The last price is {} BTC".format(str(i), now, last_price_4h))

                elif len(open_orders) != 0 and amount_sell2*last_price_4h < 0.00015:
                    print("Pair {}: not enough funds for selling {}. The last price is {} BTC".format(str(i), now, last_price_4h))

                else:
                    print("Pair {}, no option here on {}. The last price is {} BTC".format(str(i), now, last_price_4h))

            #Trending markets --> ADX slope positive
            elif model[0]>0 and model1[0]<0 and last_DMN>last_DMP and last_ADX>25:
                print("Strong downtrend: no more trading, just selling what is left.")
                amount_sell2=round(0.95*check_balance[str(i).split("/")[0]]['free'],7)

                if len(open_orders) == 0 and amount_sell2*last_price_4h > 0.00015:
                    order2 = exchange.create_order(str(i), type, 'sell', amount_sell2, price, params)
                    time.sleep(10)
                
                elif len(open_orders) == 0 and amount_sell2*last_price_4h < 0.00015:
                    print("Pair {}: not enough funds for selling {}. The last price is {} BTC".format(str(i), now, last_price_4h))

                elif len(open_orders) != 0 :
                    print("Canceling open orders")
                    for j in range(len(open_orders)):
                        print(open_orders[j].get("info").get("orderId"))
                        order1= exchange.cancel_order(open_orders[j].get("info").get("orderId"), str(i), params)
                        time.sleep(10)

                    if amount_sell2*last_price_4h > 0.00015:
                        order2 = exchange.create_order(str(i), type, 'sell', amount_sell2, price, params)
                        append_list_as_row('test.csv', [now, str(i), 'sell', last_price_4h])
                        time.sleep(10)
                    
                    else:
                        print("Pair {}: not enough funds for selling {}. The last price is {} BTC".format(str(i), now, last_price_4h))

                elif len(open_orders) != 0 and amount_sell2*last_price_4h < 0.00015:
                    print("Pair {}: not enough funds for selling {}. The last price is {} BTC".format(str(i), now, last_price_4h))

                else:
                    print("Pair {}, no option here on {}. The last price is {} BTC".format(str(i), now, last_price_4h))

            #ADX>15 --> strong trend underway, ADX>30 --> very strong trend underway
            elif model[0]>0 and last_DMP>last_DMN:

                print("Strong uptrend: trading authorized. Channel breakouts strategy to be used")
                if last_price_4h>max(last_price_1d_period) and check_balance['BTC']['free'] > 0.0015 and amount_buy_trend*last_price_4h<check_balance['BTC']['free'] and len(total_open_orders)+1<=MAX_NUM_ALGO_ORDERS and last_ADX>25 and len(open_orders)+1<=MAX_NUM_ORDERS and model1[0]>0:
                    order1 = exchange.create_order(str(i), type, 'buy', amount_buy_trend, price, params)
                    time.sleep(10)
                    order2 = exchange.create_order(str(i), 'STOP_LOSS_LIMIT', side='sell', amount=amount_sell_trend, price = limit_price_atr_trend, params=params_atr_trend)
                    append_list_as_row('test.csv', [now, str(i), 'buy', last_price_4h, round(limit_price_atr_trend,7)])
                    print("Pair {}: buy order sent on {} at a price of {} BTC with a stop-loss at {}".format(str(i), now, last_price_4h, stop_loss_trend))
                #Overheated market
                elif model[0]>0 and model[0] < 0.1 and model1[0]<0 and last_ADX>last_DMP and last_ADX>last_DMN:
                    print("Strong uptrend but ADX turning down as well as CMF, time to sell.")
                    amount_sell2=round(0.95*check_balance[str(i).split("/")[0]]['free'],7)

                    if len(open_orders) == 0 and amount_sell2*last_price_4h > 0.00015:
                        order2 = exchange.create_order(str(i), type, 'sell', amount_sell2, price, params)
                        time.sleep(10)
                    
                    elif len(open_orders) == 0 and amount_sell2*last_price_4h < 0.00015:
                        print("Pair {}: not enough funds for selling {}. The last price is {} BTC".format(str(i), now, last_price_4h))

                    elif len(open_orders) != 0 :
                        print("Canceling open orders")
                        for j in range(len(open_orders)):
                            print(open_orders[j].get("info").get("orderId"))
                            order1= exchange.cancel_order(open_orders[j].get("info").get("orderId"), str(i), params)
                            time.sleep(10)

                        if amount_sell2*last_price_4h > 0.00015:
                            order2 = exchange.create_order(str(i), type, 'sell', amount_sell2, price, params)
                            append_list_as_row('test.csv', [now, str(i), 'sell', last_price_4h])
                            time.sleep(10)
                        
                        else:
                            print("Pair {}: not enough funds for selling {}. The last price is {} BTC".format(str(i), now, last_price_4h))

                    elif len(open_orders) != 0 and amount_sell2*last_price_4h < 0.00015:
                        print("Pair {}: not enough funds for selling {}. The last price is {} BTC".format(str(i), now, last_price_4h))

                    else:
                        print("Pair {}, no option here on {}. The last price is {} BTC".format(str(i), now, last_price_4h))

                #If bounce on the bbl --> BUY
                elif last_price_4h<1.009*last_bbl_4h and check_balance['BTC']['free'] > 0.0015 and amount_buy_trend*last_price_4h<check_balance['BTC']['free'] and len(total_open_orders)+1<=MAX_NUM_ALGO_ORDERS and last_ADX>25 and model[0] > 0.1 and len(open_orders)+1<=MAX_NUM_ORDERS and model1[0]>0:
                    print("Strong uptrend, temporary dip, buying the bbl.")
                    order1 = exchange.create_order(str(i), type, 'buy', amount_buy_trend, price, params)
                    #temporisation pour eviter des erreurs?
                    time.sleep(10)
                    order2 = exchange.create_order(str(i), 'STOP_LOSS_LIMIT', side='sell', amount=amount_sell_trend, price = limit_price_atr_trend, params=params_atr_trend)
                    append_list_as_row('test.csv', [now, str(i), 'buy', last_price_4h, round(limit_price_atr_trend,7)])
                    print("Pair {}: buy initial order sent on {} at a price of {} BTC with a stop-loss at {}".format(str(i), now, last_price_4h, stop_loss_trend))
                
                else:
                    print("Not the time yet to buy or sell. We need more confirmation of the beginning or the end of the current uptrend")
            
            else:
                print("Pair {}: no position taken on {}. The last price is {} BTC".format(str(i), now, last_price_4h))

        count=count+1


except KeyboardInterrupt:

    print("\nYou are now exiting the program")

    raise SystemExit
    sys.exit()

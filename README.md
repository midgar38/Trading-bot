# Trading-bot

The present trading bot is using the Bollinger band, ADX and CMF indicators. It is using both the values and the slope of the ADX on the daily timeframe to assess whether or not a trend is developping. The slope of the CMF is also calculated and taken into account to further filter out trades. The Bollinger Bands are only used in a trendless envrionment. In a trending one, a price break of the past 18 days is implemented.

The algorithm isfully using the CCXT trading library as well as the technical analysis library "Pandas TA". Those two are really well documented and flexible. Kudos on their respective authors. 

Please not it is ONLY operating on the Binance exchange at the moment. 

It goes without saying that you this code at your own risk. It is ALL experimenteal and I am still refining it on a regular basis.

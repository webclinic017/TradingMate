from Utils.TaskThread import TaskThread
import os
import sys
import inspect
import urllib.request
import json

currentdir = os.path.dirname(os.path.abspath(
    inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)


class StockPriceGetter(TaskThread):

    def __init__(self, configurationManager, onNewPriceDataCallback, updatePeriod):
        TaskThread.__init__(self, updatePeriod)
        self.onNewPriceDataCallback = onNewPriceDataCallback
        self.configurationManager = configurationManager
        self._read_configuration()
        self.lastData = {}
        self.symbolList = []

    def _read_configuration(self):
        try:
            self.alphaVantageAPIKey = self.configurationManager.get_alpha_vantage_api_key()
            self.alphaVantageBaseURL = self.configurationManager.get_alpha_vantage_base_url()
        except Exception as e:
            print("LivePricesWebThread: _read_configuration() {0}".format(e))
            sys.exit(1)

    def task(self):
        priceDict = {}
        for symbol in self.symbolList:
            if not self._finished.isSet():
                value = self._fetch_price_data(symbol)
                # Wait 1 sec as suggested by AlphaVantage support
                self._timeout.wait(1)
                if value is not None:
                    priceDict[symbol] = value
        if not self._finished.isSet():
            self.lastData = priceDict  # Store internally
            self.onNewPriceDataCallback()  # Notify the model

    def _fetch_price_data(self, symbol):
        try:
            url = self._build_url("TIME_SERIES_DAILY",
                                  symbol, "5min", self.alphaVantageAPIKey)
            request = urllib.request.urlopen(url, timeout=10)
            content = request.read()
            data = json.loads(content.decode('utf-8'))
            timeSerie = data["Time Series (Daily)"]
            last = next(iter(timeSerie.values()))
            value = float(last["4. close"])
        except Exception:
            print("LivePricesWebThread: _fetch_price_data(): {0}".format(url))
            value = None
        return value

    def _build_url(self, aLength, aSymbol, anInterval, anApiKey):
        function = "function=" + aLength
        symbol = "symbol=" + aSymbol
        apiKey = "apikey=" + anApiKey
        url = self.alphaVantageBaseURL + "?" + function + "&" + symbol + "&" + apiKey
        return url

    def get_last_data(self):
        return self.lastData

    def set_symbol_list(self, aList):
        self.symbolList = aList

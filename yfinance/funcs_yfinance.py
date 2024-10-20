#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec  7 18:05:52 2022

@author: Alex
"""

import yfinance as yf
import pandas as pd
import datetime as dt


# ticker = "NTGY.MC"
def get_actions(ticker, start=0, end=0):
    if start==0 and end == 0:
        return yf.Ticker(ticker).actions
    else:
        # Adding the two extra lines to remove the warning about the timezones:
        # FutureWarning: Indexing a timezone-aware DatetimeIndex
        #  Solution: https://stackoverflow.com/questions/16628819/convert-pandas-timezone-aware-datetimeindex-to-naive-timestamp-but-in-certain-t
        df = yf.Ticker(ticker).actions.tz_convert(None)
        df_sliced = df[start:end]
        return df_sliced



def get_info(tick):
    # Getting all that from:
    # https://pypi.org/project/yfinance/
    
    # Get all info of the product
    product = yf.Ticker(tick)
    
    # Create an empty dictionary and fill it
    product_dict={}
    product_dict["info"] = product.info
    product_dict["history"] = product.history
    product_dict["dividends"] = product.dividends
    product_dict["actions"] = product.actions
    product_dict["splits"] = product.splits
    product_dict["financials"] = product.financials
    product_dict["quarterly_financials"] = product.quarterly_financials
    product_dict["major_holders"] = product.major_holders
    product_dict["institutional_holders"] = product.institutional_holders
    product_dict["balance_sheet"] = product.balance_sheet
    product_dict["quarterly_balance_sheet"] = product.quarterly_balance_sheet
    product_dict["cashflow"] = product.cashflow
    product_dict["quarterly_cashflow"] = product.quarterly_cashflow
    product_dict["earnings"] = product.earnings
    product_dict["quarterly_earnings"] = product.quarterly_earnings
    product_dict["sustainability"] = product.sustainability
    product_dict["recommendations"] = product.recommendations
    product_dict["calendar"] = product.calendar
    product_dict["earnings_dates"] = product.earnings_dates
    product_dict["isin"] = product.isin
    product_dict["options"] = product.options
    product_dict["news"] = product.news
    
    return product_dict


def get_Currency_exchangeRate(currency1,currency2, start_date, end_date):
    ratio=yf.download(f"{currency1}{currency2}=X", start_date, end_date)['Close'].values[-1]
    return ratio

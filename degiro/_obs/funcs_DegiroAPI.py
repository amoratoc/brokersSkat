import degiroapi
from datetime import datetime
import pandas as pd

from yfinance.funcs_yfinance import get_actions, get_Currency_exchangeRate

"""
Based on the:
    https://github.com/lolokraus/DegiroAPI/blob/master/examples/examples.py
"""

degiro = degiroapi.DeGiro()
degiro.login("amorato", """^!^M"c3Y=mC5At^n""")

        
def get_cash_funds():
    cashfunds = degiro.getdata(degiroapi.Data.Type.CASHFUNDS)
    for data in cashfunds:
        print(data)
    return cashfunds
    

############### Create a DF with the portfolio ###########################

def get_portfolio_df():
    # Read portfolio from degiro
    portfolio = degiro.getdata(degiroapi.Data.Type.PORTFOLIO, True)
    
    # Create empty DF
    PF_df = pd.DataFrame(columns=['Product','Currency','Symbol','Size','Price',
                                  'MarketValue','BEP','P/L','P/L (%)'])
    
    # iterate through the portfolio and fill the DF
    for i, ele in enumerate(portfolio[:-1]): # [:-1]
        if ele["positionType"] == "PRODUCT":
            # Find product with this ID
            prod = degiro.product_info(ele['id'])
            
            profit = (ele["size"]*ele["price"]) - (ele["size"]*ele["breakEvenPrice"])
            profit_perc = (ele["price"]-ele["breakEvenPrice"])/ele["breakEvenPrice"]*100
            
            # Fill dataframe
            PF_df.loc[i] = [prod["productType"],
                            prod["symbol"],
                            prod["currency"],
                            ele["size"],
                            ele["price"],
                            ele["value"], 
                            ele["breakEvenPrice"],
                            profit,
                            profit_perc
                            ]
    return PF_df
    

PF_df = get_portfolio_df()
Total = PF_df["MarketValue"].sum()


############### Let´s look at TRANSACTIONS ###########################

def get_trans_ticks_in_PF():
    # Read portfolio from degiro
    portfolio = degiro.getdata(degiroapi.Data.Type.PORTFOLIO, True)
    # Load all transactions
    transactions = degiro.transactions(datetime(2019, 1, 1), datetime.now())
    # Create a dictionary that will contain all transactions by product in the portfolio
    Trans_dict ={}
    # Iterate through the portfolio
    for i, ele in enumerate(portfolio[:-1]): # [:-1]
        # Get symbol of the product 
        ele_id = ele['id']
        
        # General info of the product by ID
        ele_info = degiro.product_info(ele_id)
        
        # Get product symbol
        ele_symb = ele_info["symbol"]
        print(ele_symb)
        
        # Create empty list of transactions
        Trans_dict[ele_symb] = []
        
        for trans in transactions:
            # print(f"{trans['id']} {int(ele_id)}")
            if trans['productId'] == int(ele_id):
                Trans_dict[ele_symb].append(trans)
    return Trans_dict
    

# Get a DF with the all-time transactions
def get_all_trans_in_df():
    # Load all transactions
    transactions = degiro.transactions(datetime(2019, 1, 1), datetime.now())
    # Create a DF that will contain all transactions
    cols = list(transactions[0].keys())
    cols.insert(2,'symbol')
    cols.insert(3,'name')
    all_trans_df = pd.DataFrame(columns=cols)    
    
    for i, trans in enumerate(transactions):
        ele_info = degiro.product_info(trans['productId'])
        for prop in cols:
            
            if prop =='name':
                all_trans_df.at[i, prop] = ele_info['name']
                
            elif prop =='symbol':
                all_trans_df.at[i, prop] = ele_info['symbol']
                
            else:
                try:
                    all_trans_df.at[i, prop] = trans[prop]
                except KeyError:
                    continue
    return all_trans_df
    

all_trans_df = get_all_trans_in_df()
# Tesla_trans = all_trans_df[all_trans_df['symbol']=='TSLA']



def get_all_trans_PL(drops=[101]):
    # Load all transactions
    transactions = degiro.transactions(datetime(2019, 1, 1), datetime.now())
    # Create a DF that will contain all transactions
    cols = list(transactions[0].keys())
    cols.insert(2,'symbol')
    cols.insert(3,'name')
    tik_trans_df = pd.DataFrame(columns=cols)    
    
    # Let's convert all the lists of transactions to a Dataframe
    for i, trans in enumerate(transactions):
        ele_info = degiro.product_info(trans['productId'])
        # if ele_info['symbol']==tik:
        for prop in cols:
            
            if prop =='name':
                tik_trans_df.at[i, prop] = ele_info['name']
                
            elif prop =='symbol':
                tik_trans_df.at[i, prop] = ele_info['symbol']
                
            else:
                try:
                    tik_trans_df.at[i, prop] = trans[prop]
                except KeyError:
                        continue
    
    tik_trans_df = tik_trans_df.reset_index(drop=True)
    # for num in drops:
    tik_trans_df=tik_trans_df[tik_trans_df['transactionTypeId']==0]
    
    # Now we have a DF with all the transactions, let´s add the columns with the
    # adjusted profit loss for each one that is a proper buy/sell
    
    tik_trans_df[["split_ratio", "AdjustedQuantity", "AdjustedPrice",
               "adj_BEP_originCurr", "adj_BEP_baseCurr",
               "inOriginPL%","inOriginPL","currencyPL%","currencyPL",
               "basePL%","basePL","unitPL",
               "positionValue_origin", "positionValue_base"]] = None
    
    for i, trans in tik_trans_df.iterrows():
        try:
            tik = degiro.product_info(trans['productId'])['symbol']
            tik_yf = tik
            print(tik)
            # Get info of the project
            tik_info = degiro.search_products(tik)[0]
            if tik_info["currency"]=="EUR": tik_yf = tik_yf + ".MC"
            elif tik=="CLN.D": tik_yf = "CLNX.MC"
        
            # Cost without fees
            cost_origin_NoFees = trans["total"]
            
            if trans['grossFxRate'] != 0:
                # Amount in base currency to by the position
                cost_base_NoFees = cost_origin_NoFees/trans['grossFxRate']
                
                # Fee in % - autoFX for currency exchange (0.1 - 0.25%)
                fee_AutoFx_perc = trans['autoFxFeeInBaseCurrency']/cost_base_NoFees
                
                # Fee - autoFX for currency exchange (check as it's in the DF)
                fee_AutoFx_base = cost_base_NoFees*fee_AutoFx_perc
                
                # Net exchange rate - check
                nettFxRate = cost_origin_NoFees/(cost_base_NoFees+fee_AutoFx_base)
            else:
                cost_base_NoFees = 0
                
            # Fee - transaction and others
            fee_trans_base = trans['feeInBaseCurrency']
            
            # Total fees
            fees_total_base = trans['autoFxFeeInBaseCurrency'] + trans['feeInBaseCurrency']
            
            # Net cost of operation
            cost_base_nett = cost_base_NoFees+fees_total_base
            
            # Adjusted price considering splits
            trade_date = trans["date"]
            # trade_date = "2015-05-05T15:34:15+02:00"
            today = pd.to_datetime('today').normalize().utcoffset()
            start = pd.to_datetime(trade_date, format="%Y-%m-%dT%H:%M:%S")
            actions = get_actions(tik_yf, start, today)
            split_ratio = actions['Stock Splits'].replace(0,1).prod()
            acc_dividend = actions['Dividends'].sum()
            adj_quant = split_ratio * trans["quantity"]
            tik_trans_df.at[i, "AdjustedQuantity"] = adj_quant
            
            # Store split ratio
            tik_trans_df.at[i, "split_ratio"] = split_ratio
            # Adjusted price without currency fee nor buying fee
            tik_trans_df.at[i, "AdjustedPrice"] = trans["price"]/split_ratio
            
            # Adjusted Break Even price including ALL fees - in origin and base currency
            adj_BEP_baseCurr = abs(trans["totalPlusAllFeesInBaseCurrency"])/trans["quantity"]/split_ratio
            adj_BEP_originCurr = adj_BEP_baseCurr*trans["fxRate"]
            tik_trans_df.at[i, "adj_BEP_baseCurr"] = adj_BEP_baseCurr
            tik_trans_df.at[i, "adj_BEP_originCurr"] = adj_BEP_originCurr
            
            # Add columns with currency P/L and position P/L
            curr_price = degiro.search_products(tik)[0]['closePrice']
            
            # Get current exchange rate
            originCurrency = tik_info['currency']
            baseCurrency = "EUR"
            current_rate = get_Currency_exchangeRate(baseCurrency,originCurrency, start, today)
            
            # Compute PL for the position - origin currency
            pos_PL_perc_origin = (curr_price-adj_BEP_originCurr)/adj_BEP_originCurr*100
            pos_PL_origin = adj_quant * curr_price - abs(trans["totalPlusAllFeesInBaseCurrency"]) * trans["fxRate"] 
            
            # Compute PL for the position - base currency
            pos_PL_perc_base = (curr_price/current_rate - adj_BEP_baseCurr) / adj_BEP_baseCurr*100
            pos_PL_base = adj_quant * curr_price / current_rate - abs(trans["totalPlusAllFeesInBaseCurrency"])
            
            # Get the PL of the position due to change of currency exchange rate
            if trans['grossFxRate'] != 0:
                currencyPL_perc = (trans["fxRate"] - current_rate)/trans["fxRate"]*100
                currencyPL = adj_quant * curr_price * (1/current_rate - 1/trans["fxRate"])
                currencyPL = pos_PL_base-pos_PL_origin
            else:
                currencyPL_perc = 0
                currencyPL = 0
            
            # Market value of the position
            mkt_value_origin = adj_quant*curr_price
            mkt_value_base = adj_quant*curr_price/current_rate
            
            # PL per unit - to produce averages afterwards
            tik_trans_df.at[i, "unitPL"] = pos_PL_base/adj_quant
            
            
            # Fill the DF
            tik_trans_df.at[i, "currentPrice"] = curr_price
            
            tik_trans_df.at[i, "inOriginPL%"] = pos_PL_perc_origin
            tik_trans_df.at[i, "inOriginPL"] = pos_PL_origin
            
            tik_trans_df.at[i, "currencyPL%"] = currencyPL_perc
            tik_trans_df.at[i, "currencyPL"] = currencyPL
            
            tik_trans_df.at[i, "basePL%"] = pos_PL_perc_base
            tik_trans_df.at[i, "basePL"] = pos_PL_base
            
            tik_trans_df.at[i, "positionValue_origin"] = mkt_value_origin
            tik_trans_df.at[i, "positionValue_base"] = mkt_value_base
        except:
            continue
    
    
    return tik_trans_df


Trans_df = get_all_trans_PL()

tik = "TSLA"
tik = "CLNX"
Trans_tik_df = Trans_df[Trans_df["symbol"]==tik]

Trans_tik_df["basePL"].sum()
Trans_tik_df["currencyPL"].sum()
Trans_tik_df["inOriginPL"].sum()

(Trans_tik_df["basePL%"]*Trans_tik_df["AdjustedQuantity"]).sum() / Trans_tik_df["AdjustedQuantity"].sum()


(Trans_tik_df["positionValue_base"].sum() - abs(Trans_tik_df["totalPlusAllFeesInBaseCurrency"].sum())) / abs(Trans_tik_df["totalPlusAllFeesInBaseCurrency"].sum())*100







# tik = 'TSLA'

# tik_info1 = degiro.search_products(tik)[0]
# tik_info2 = degiro.product_info(tik_info1['id'])


# # tik = 'GOOGL'
# tik_trans = get_trans_by_sym(tik, drops=[101])

# tik_trans[["split_ratio", "AdjustedQuantity", "AdjustedPrice",
#            "adj_BEP_originCurr", "adj_BEP_baseCurr",
#            "inOriginPL%","inOriginPL","currencyPL%","currencyPL",
#            "basePL%","basePL","unitPL",
#            "positionValue_origin", "positionValue_base"]] = None
# for i, trans in tik_trans.iterrows():
#     # Get info of the project
#     tik_info = degiro.search_products(tik)[0]

#     # Cost without fees
#     cost_origin_NoFees = trans["total"]
    
#     # Amount in base currency to by the position
#     cost_base_NoFees = cost_origin_NoFees/trans['grossFxRate']
    
#     # Fee in % - autoFX for currency exchange (0.1 - 0.25%)
#     fee_AutoFx_perc = trans['autoFxFeeInBaseCurrency']/cost_base_NoFees
    
#     # Fee - autoFX for currency exchange (check as it's in the DF)
#     fee_AutoFx_base = cost_base_NoFees*fee_AutoFx_perc
    
#     # Net exchange rate - check
#     nettFxRate = cost_origin_NoFees/(cost_base_NoFees+fee_AutoFx_base)
    
#     # Fee - transaction and others
#     fee_trans_base = trans['feeInBaseCurrency']
    
#     # Total fees
#     fees_total_base = trans['autoFxFeeInBaseCurrency'] + trans['feeInBaseCurrency']
    
#     # Net cost of operation
#     cost_base_nett = cost_base_NoFees+fees_total_base
    
#     # Adjusted price considering splits
#     trade_date = trans["date"]
#     # trade_date = "2015-05-05T15:34:15+02:00"
#     today = pd.to_datetime('today').normalize().utcoffset()
#     start = pd.to_datetime(trade_date, format="%Y-%m-%dT%H:%M:%S")
#     actions = get_actions(tik, start, today)
#     slplit_ratio = actions['Stock Splits'].replace(0,1).prod()
#     acc_dividend = actions['Dividends'].sum()
#     adj_quant = slplit_ratio * trans["quantity"]
#     tik_trans.at[i, "AdjustedQuantity"] = adj_quant
    
#     # Store split ratio
#     tik_trans.at[i, "split_ratio"] = slplit_ratio
#     # Adjusted price without currency fee nor buying fee
#     tik_trans.at[i, "AdjustedPrice"] = trans["price"]/slplit_ratio
    
#     # Adjusted Break Even price including ALL fees - in origin and base currency
#     adj_BEP_baseCurr = abs(trans["totalPlusAllFeesInBaseCurrency"])/trans["quantity"]/slplit_ratio
#     adj_BEP_originCurr = adj_BEP_baseCurr*trans["fxRate"]
#     tik_trans.at[i, "adj_BEP_baseCurr"] = adj_BEP_baseCurr
#     tik_trans.at[i, "adj_BEP_originCurr"] = adj_BEP_originCurr
    
#     # Add columns with currency P/L and position P/L
#     curr_price = degiro.search_products(tik)[0]['closePrice']
    
#     # Get current exchange rate
#     originCurrency = tik_info['currency']
#     baseCurrency = "EUR"
#     current_rate = get_Currency_exchangeRate(baseCurrency,originCurrency, start, today)
    
#     # Compute PL for the position - origin currency
#     pos_PL_perc_origin = (curr_price-adj_BEP_originCurr)/adj_BEP_originCurr*100
#     pos_PL_origin = adj_quant * curr_price - abs(trans["totalPlusAllFeesInBaseCurrency"]) * trans["fxRate"] 
    
#     # Compute PL for the position - base currency
#     pos_PL_perc_base = (curr_price/current_rate - adj_BEP_baseCurr) / adj_BEP_baseCurr*100
#     pos_PL_base = adj_quant * curr_price / current_rate - abs(trans["totalPlusAllFeesInBaseCurrency"])
    
#     # Get the PL of the position due to change of currency exchange rate 
#     currencyPL_perc = (trans["fxRate"] - current_rate)/trans["fxRate"]*100
#     currencyPL = adj_quant * curr_price * (1/current_rate - 1/trans["fxRate"])
#     currencyPL = pos_PL_base-pos_PL_origin
    
#     # Market value of the position
#     mkt_value_origin = adj_quant*curr_price
#     mkt_value_base = adj_quant*curr_price/current_rate
    
#     # PL per unit - to produce averages afterwards
#     tik_trans.at[i, "unitPL"] = pos_PL_base/adj_quant
    
    
#     # Fill the DF
#     tik_trans.at[i, "currentPrice"] = curr_price
    
#     tik_trans.at[i, "inOriginPL%"] = pos_PL_perc_origin
#     tik_trans.at[i, "inOriginPL"] = pos_PL_origin
#     pos_PL_origin
#     tik_trans.at[i, "currencyPL%"] = currencyPL_perc
#     tik_trans.at[i, "currencyPL"] = currencyPL
    
#     tik_trans.at[i, "basePL%"] = pos_PL_perc_base
#     tik_trans.at[i, "basePL"] = pos_PL_base
    
#     tik_trans.at[i, "positionValue_origin"] = mkt_value_origin
#     tik_trans.at[i, "positionValue_base"] = mkt_value_base
    
   

# tik_trans["basePL"].sum()
# tik_trans["currencyPL"].sum()
# tik_trans["inOriginPL"].sum()


# (tik_trans["basePL%"]*tik_trans["AdjustedQuantity"]).sum() / tik_trans["AdjustedQuantity"].sum()


# (tik_trans["positionValue_base"].sum() - abs(tik_trans["totalPlusAllFeesInBaseCurrency"].sum())) / abs(tik_trans["totalPlusAllFeesInBaseCurrency"].sum())*100



# ##########################
# tik_trans = get_trans_by_sym(tik, drops=[101])

# tik_trans[["split_ratio", "AdjustedQuantity", "AdjustedPrice",
#            "adj_BEP_originCurr", "adj_BEP_baseCurr",
#            "inOriginPL%","inOriginPL","currencyPL%","currencyPL",
#            "basePL%","basePL","unitPL",
#            "positionValue_origin", "positionValue_base"]] = None
# for i, trans in tik_trans.iterrows():
#     # Get info of the project
#     tik_info = degiro.search_products(tik)[0]

#     # Cost without fees
#     cost_origin_NoFees = trans["total"]
    
#     # Amount in base currency to by the position
#     cost_base_NoFees = cost_origin_NoFees/trans['grossFxRate']
    
#     # Fee in % - autoFX for currency exchange (0.1 - 0.25%)
#     fee_AutoFx_perc = trans['autoFxFeeInBaseCurrency']/cost_base_NoFees
    
#     # Fee - autoFX for currency exchange (check as it's in the DF)
#     fee_AutoFx_base = cost_base_NoFees*fee_AutoFx_perc
    
#     # Net exchange rate - check
#     nettFxRate = cost_origin_NoFees/(cost_base_NoFees+fee_AutoFx_base)
    
#     # Fee - transaction and others
#     fee_trans_base = trans['feeInBaseCurrency']
    
#     # Total fees
#     fees_total_base = trans['autoFxFeeInBaseCurrency'] + trans['feeInBaseCurrency']
    
#     # Net cost of operation
#     cost_base_nett = cost_base_NoFees+fees_total_base
    
#     # Adjusted price considering splits
#     trade_date = trans["date"]
#     # trade_date = "2015-05-05T15:34:15+02:00"
#     today = pd.to_datetime('today').normalize().utcoffset()
#     start = pd.to_datetime(trade_date, format="%Y-%m-%dT%H:%M:%S")
#     actions = get_actions(tik, start, today)
#     slplit_ratio = actions['Stock Splits'].replace(0,1).prod()
#     acc_dividend = actions['Dividends'].sum()
#     adj_quant = slplit_ratio * trans["quantity"]
#     tik_trans.at[i, "AdjustedQuantity"] = adj_quant
    
#     # Store split ratio
#     tik_trans.at[i, "split_ratio"] = slplit_ratio
#     # Adjusted price without currency fee nor buying fee
#     tik_trans.at[i, "AdjustedPrice"] = trans["price"]/slplit_ratio
    
#     # Adjusted Break Even price including ALL fees - in origin and base currency
#     adj_BEP_baseCurr = abs(trans["totalPlusAllFeesInBaseCurrency"])/trans["quantity"]/slplit_ratio
#     adj_BEP_originCurr = adj_BEP_baseCurr*trans["fxRate"]
#     tik_trans.at[i, "adj_BEP_baseCurr"] = adj_BEP_baseCurr
#     tik_trans.at[i, "adj_BEP_originCurr"] = adj_BEP_originCurr
    
#     # Add columns with currency P/L and position P/L
#     curr_price = degiro.search_products(tik)[0]['closePrice']
    
#     # Get current exchange rate
#     originCurrency = tik_info['currency']
#     baseCurrency = "EUR"
#     current_rate = get_Currency_exchangeRate(baseCurrency,originCurrency, start, today)
    
#     # Compute PL for the position - origin currency
#     pos_PL_perc_origin = (curr_price-adj_BEP_originCurr)/adj_BEP_originCurr*100
#     pos_PL_origin = adj_quant * curr_price - abs(trans["totalPlusAllFeesInBaseCurrency"]) * trans["fxRate"] 
    
#     # Compute PL for the position - base currency
#     pos_PL_perc_base = (curr_price/current_rate - adj_BEP_baseCurr) / adj_BEP_baseCurr*100
#     pos_PL_base = adj_quant * curr_price / current_rate - abs(trans["totalPlusAllFeesInBaseCurrency"])
    
#     # Get the PL of the position due to change of currency exchange rate 
#     currencyPL_perc = (trans["fxRate"] - current_rate)/trans["fxRate"]*100
#     currencyPL = adj_quant * curr_price * (1/current_rate - 1/trans["fxRate"])
#     currencyPL = pos_PL_base-pos_PL_origin
    
#     # Market value of the position
#     mkt_value_origin = adj_quant*curr_price
#     mkt_value_base = adj_quant*curr_price/current_rate
    
#     # PL per unit - to produce averages afterwards
#     tik_trans.at[i, "unitPL"] = pos_PL_base/adj_quant
    
    
#     # Fill the DF
#     tik_trans.at[i, "currentPrice"] = curr_price
    
#     tik_trans.at[i, "inOriginPL%"] = pos_PL_perc_origin
#     tik_trans.at[i, "inOriginPL"] = pos_PL_origin
#     pos_PL_origin
#     tik_trans.at[i, "currencyPL%"] = currencyPL_perc
#     tik_trans.at[i, "currencyPL"] = currencyPL
    
#     tik_trans.at[i, "basePL%"] = pos_PL_perc_base
#     tik_trans.at[i, "basePL"] = pos_PL_base
    
#     tik_trans.at[i, "positionValue_origin"] = mkt_value_origin
#     tik_trans.at[i, "positionValue_base"] = mkt_value_base
    
   

# tik_trans["basePL"].sum()
# tik_trans["currencyPL"].sum()
# tik_trans["inOriginPL"].sum()


# (tik_trans["basePL%"]*tik_trans["AdjustedQuantity"]).sum() / tik_trans["AdjustedQuantity"].sum()


# (tik_trans["positionValue_base"].sum() - abs(tik_trans["totalPlusAllFeesInBaseCurrency"].sum())) / abs(tik_trans["totalPlusAllFeesInBaseCurrency"].sum())*100















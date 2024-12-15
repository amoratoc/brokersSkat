import json
import pandas as pd
from degiro_connector.trading.models.transaction import HistoryRequest
from datetime import date
import yfinance as yf
from utils.currency_conversion import euro_to_dkk


def get_transactions(session, year: int):
    # Transaction history
    transactions_history = session.get_transactions_history(
        transaction_request=HistoryRequest(
            from_date=date(year, 1, 1),
            to_date=date(year, 12, 31)
        ),
        raw=False,
    )

    # Convert the list of models to a list of dictionaries, excluding unset fields
    data_dicts = [item.dict(exclude_unset=True) for item in transactions_history.data]

    # Create a DataFrame from the list of dictionaries
    return pd.DataFrame(data_dicts)


def add_product_details_to_transactions(session, transactions: pd.DataFrame):
    # Get product information for all products
    products_info = session.get_products_info(
        product_list=list(set(transactions.product_id.to_list())),
        raw=False,
    ).data

    # Add product information and cost in dkk
    for i, row in transactions.iterrows():
        product = products_info[row.product_id]
        amount_eur = row['total_plus_all_fees_in_base_currency']
        date = row['date']
        transactions.at[i, 'product_name'] = product.name
        transactions.at[i, 'product_ticker'] = product.symbol
        transactions.at[i, 'product_isin'] = product.isin
        transactions.at[i, 'total_plus_all_fees_in_dkk'] = euro_to_dkk(amount_eur, date)

    return transactions


def get_transactions_skat(session, year: int, ticker: str = None):
    transactions = get_transactions(session, year)

    if transactions.empty:
        print(f"No transactions in year {year}")
        return transactions

    df_details = add_product_details_to_transactions(
        session=session,
        transactions=transactions,
    )

    # Create 'date_skat' in the format 'ddmmyy'
    df_details['date_skat'] = df_details['date'].dt.strftime('%d-%m-%Y')

    # Create 'time_skat' in the format 'HH:mm:ss'
    df_details['time_skat'] = df_details['date'].dt.strftime('%H:%M:%S')

    # Get price in dkk as string with ',' separated decimals
    df_details['price_skat'] = df_details['total_plus_all_fees_in_dkk'].apply(lambda x: f"{abs(x):,.2f}".replace(',','').replace('.', ','))

    # Filter by ticker if requested
    if ticker:
        df_details = df_details[df_details['product_ticker'] == ticker]

    df = df_details[['product_ticker','buysell','date_skat','time_skat','quantity','price_skat']]

    return df


def get_products_by_year(session, year: int):
    # Get transactions
    transactions = get_transactions(session, year)

    if transactions.empty:
        print(f"No transactions in year {year}")
        return

    # Get product information for all products
    products_info = session.get_products_info(
        product_list=list(set(transactions.product_id.to_list())),
        raw=False,
    ).data

    prod_dict = {}
    for prod_id, prod_info in products_info.items():
        prod_dict[prod_info.symbol] = {
            'name': prod_info.name,
            'isin': prod_info.isin,
            'currency': prod_info.currency,
        }
    print(json.dumps(prod_dict, indent=2, sort_keys=True))
    return prod_dict


def get_client_details(session):
    return session.get_client_details()




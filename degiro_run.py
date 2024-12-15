import json
from degiro_connector.trading.api import API as TradingAPI
from degiro_connector.trading.models.credentials import build_credentials
from degiro.dg_wrappers.wrappers import get_products_by_year, get_transactions_skat

credentials = build_credentials(location="config/config.json",)
trading_api = TradingAPI(credentials=credentials)
trading_api.connect()

year = 2020


# Get products traded in a specific year
products = get_products_by_year(
    session=trading_api,
    year=year,
)
print(json.dumps(products, indent=2, sort_keys=True))

# Get transactions with Skat requested columns
transactions_skat = get_transactions_skat(
    session=trading_api,
    year=year,
    ticker='TSLA'
)
print(transactions_skat)

print("completed")





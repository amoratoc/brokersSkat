from datetime import timedelta
import yfinance as yf


def euro_to_dkk(amount_eur, date):
    date_start_string = date.strftime('%Y-%m-%d')
    date_end_string = (date + timedelta(days=1)).strftime('%Y-%m-%d')
    eur_dkk = yf.download("EURDKK=X", start=date_start_string, end=date_end_string)
    exchange_rate = eur_dkk['Close'].iloc[0]
    return amount_eur * exchange_rate
import requests
import os

def get_company_ticker(company_name):
    try:
        api_endpoint = f'https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords={company_name}&apikey={os.getenv("ALPHA_VANTAGE")}'
        response = requests.get(api_endpoint)
        data = response.json()
        print(data)
    except Exception as e:
        raise Exception(e)
    
    
def get_company_news_sentiments(ticker_symbol):
    try:
        api_endpoint = f'https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={ticker_symbol}&apikey={os.getenv("ALPHA_VANTAGE")}'
        response = requests.get(api_endpoint)
        data = response.json()
        print(data)
    except Exception as e:
        raise Exception(e)
    
get_company_news_sentiments("VBL.BSE")

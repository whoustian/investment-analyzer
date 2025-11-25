import os
import datetime
import plaid
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.investments_holdings_get_request import InvestmentsHoldingsGetRequest
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.sandbox_public_token_create_request import SandboxPublicTokenCreateRequest
from plaid.model.sandbox_public_token_create_request_options import SandboxPublicTokenCreateRequestOptions
from dotenv import load_dotenv

load_dotenv()

PLAID_CLIENT_ID = os.getenv('PLAID_CLIENT_ID')
PLAID_SECRET = os.getenv('PLAID_SECRET')
PLAID_ENV = os.getenv('PLAID_ENV', 'sandbox')

def get_plaid_client():
    if PLAID_ENV == 'sandbox':
        host = plaid.Environment.Sandbox
    elif PLAID_ENV == 'development':
        host = plaid.Environment.Development
    elif PLAID_ENV == 'production':
        host = plaid.Environment.Production
    else:
        host = plaid.Environment.Sandbox

    if not PLAID_CLIENT_ID or not PLAID_SECRET:
        raise ValueError("PLAID_CLIENT_ID and PLAID_SECRET must be set in the environment variables.")

    configuration = plaid.Configuration(
        host=host,
        api_key={
            'clientId': PLAID_CLIENT_ID,
            'secret': PLAID_SECRET,
        }
        # verify_ssl=False # Uncomment if SSL issues suspected
    )
    api_client = plaid.ApiClient(configuration)
    return plaid_api.PlaidApi(api_client)

def create_link_token(user_id):
    client = get_plaid_client()
    request = LinkTokenCreateRequest(
        products=[Products('investments'), Products('transactions')],
        client_name="Investment Analyzer",
        country_codes=[CountryCode('US')],
        language='en',
        user=LinkTokenCreateRequestUser(
            client_user_id=user_id
        )
    )
    response = client.link_token_create(request)
    return response['link_token']

def exchange_public_token(public_token):
    client = get_plaid_client()
    request = ItemPublicTokenExchangeRequest(
        public_token=public_token
    )
    response = client.item_public_token_exchange(request)
    return response['access_token']

def get_holdings(access_token):
    client = get_plaid_client()
    request = InvestmentsHoldingsGetRequest(
        access_token=access_token
    )
    response = client.investments_holdings_get(request)
    return response.to_dict()

def get_transactions(access_token, start_date, end_date):
    client = get_plaid_client()
    request = TransactionsGetRequest(
        access_token=access_token,
        start_date=start_date,
        end_date=end_date
    )
    response = client.transactions_get(request)
    return response.to_dict()

def create_sandbox_public_token(institution_id='ins_109508', initial_products=[Products('investments'), Products('transactions')], override_username='user_good', override_password='pass_good'):
    client = get_plaid_client()
    request = SandboxPublicTokenCreateRequest(
        institution_id=institution_id,
        initial_products=initial_products,
        options=SandboxPublicTokenCreateRequestOptions(
            override_username=override_username,
            override_password=override_password
        )
    )
    response = client.sandbox_public_token_create(request)
    return response['public_token']

import os
import json
import urllib.request
import urllib.error
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv('PLAID_CLIENT_ID')
SECRET = os.getenv('PLAID_SECRET')
ENV = os.getenv('PLAID_ENV', 'sandbox')

if ENV == 'sandbox':
    URL = 'https://sandbox.plaid.com'
else:
    URL = 'https://development.plaid.com'

print(f"Using Environment: {ENV}")
print(f"URL: {URL}")

def make_request(endpoint, data):
    url = f"{URL}{endpoint}"
    data['client_id'] = CLIENT_ID
    data['secret'] = SECRET
    
    json_data = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(url, data=json_data, headers={'Content-Type': 'application/json'})
    
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} {e.reason}")
        print(e.read().decode('utf-8'))
        return {}
    except Exception as e:
        print(f"Error: {e}")
        return {}

def create_public_token():
    print("Creating public token...")
    payload = {
        "institution_id": "ins_109508",
        "initial_products": ["investments", "transactions"],
        "options": {
            "override_username": "user_good",
            "override_password": "pass_good"
        }
    }
    return make_request("/sandbox/public_token/create", payload)

def exchange(public_token):
    print("Exchanging public token...")
    payload = {
        "public_token": public_token
    }
    return make_request("/item/public_token/exchange", payload)

def get_holdings(access_token):
    print("Fetching holdings...")
    payload = {
        "access_token": access_token
    }
    return make_request("/investments/holdings/get", payload)

def get_transactions(access_token):
    print("Fetching transactions...")
    # Get dates for last year
    import datetime
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=365)
    
    payload = {
        "access_token": access_token,
        "start_date": start_date.strftime('%Y-%m-%d'),
        "end_date": end_date.strftime('%Y-%m-%d')
    }
    return make_request("/transactions/get", payload)

def main():
    pt_resp = create_public_token()
    if 'public_token' not in pt_resp:
        print("Failed to get public token")
        return

    pt = pt_resp['public_token']
    at_resp = exchange(pt)
    
    if 'access_token' not in at_resp:
        print("Failed to get access token")
        return

    access_token = at_resp['access_token']
    print(f"Access Token obtained: {access_token}")

    holdings = get_holdings(access_token)
    transactions = get_transactions(access_token)

    data = {
        "access_token": access_token,
        "holdings": holdings,
        "transactions": transactions
    }

    with open('plaid_test_data.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    print("Successfully saved Plaid test data to plaid_test_data.json")

if __name__ == "__main__":
    main()

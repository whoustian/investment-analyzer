import plaid_service
import json
import datetime
from datetime import timedelta

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        return super(DateTimeEncoder, self).default(obj)

def main():
    print("Generating Plaid Sandbox Test Data...", flush=True)

    try:
        # 1. Create Sandbox Public Token
        # We use 'ins_109512' (Houndstooth Bank) because it provides rich investment data
        # with the default 'user_good' credentials.
        print("Creating Sandbox Public Token (Houndstooth Bank)...", flush=True)
        public_token = plaid_service.create_sandbox_public_token(
            institution_id='ins_109512',
            override_username='user_good',
            override_password='pass_good'
        )
        print(f"Public Token: {public_token}", flush=True)

        # 2. Exchange for Access Token
        print("Exchanging for Access Token...", flush=True)
        access_token = plaid_service.exchange_public_token(public_token)
        print(f"Access Token: {access_token}", flush=True)

        # 3. Get Holdings
        print("Fetching Holdings...", flush=True)
        holdings = plaid_service.get_holdings(access_token)
        print(f"Fetched {len(holdings.get('holdings', []))} holdings.", flush=True)

        # 4. Get Transactions (last 365 days)
        print("Fetching Transactions...", flush=True)
        end_date = datetime.datetime.now().date()
        start_date = end_date - timedelta(days=365)
        transactions = plaid_service.get_transactions(access_token, start_date, end_date)
        print(f"Fetched {len(transactions.get('transactions', []))} transactions.", flush=True)

        # 5. Save to JSON
        data = {
            "access_token": access_token,
            "holdings": holdings,
            "transactions": transactions
        }

        output_file = "plaid_test_data.json"
        with open(output_file, "w") as f:
            json.dump(data, f, cls=DateTimeEncoder, indent=2)
        
        print(f"Successfully saved test data to {output_file}")

    except Exception as e:
        print(f"Error generating test data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

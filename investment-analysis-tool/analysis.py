import pandas as pd
import numpy as np
from datetime import datetime

class PortfolioAnalyzer:
    def __init__(self, filepath):
        self.filepath = filepath
        self.df = None
        self.holdings = {}
        self.cash_balance = 0.0
        self.performance = {}

    def load_data(self):
        try:
            # Fidelity CSVs often have a few header lines or specific encoding
            self.df = pd.read_csv(self.filepath)
            # Basic cleaning
            self.df.columns = [c.strip() for c in self.df.columns]
            
            # Check for misaligned columns (Fidelity export quirk)
            # If 'Quantity' column contains 'USD', it's likely the Currency column
            # and the actual Price/Quantity are shifted.
            if 'Quantity' in self.df.columns and self.df['Quantity'].astype(str).str.contains('USD').any():
                print("Detected misaligned columns. Adjusting...")
                # The observed pattern: Header "Quantity" -> Data "Currency" (USD)
                # Header "Currency" -> Data "Price"
                # Header "Price" -> Data "Quantity"
                # We need to swap/rename.
                # Let's rename them to what they actually contain
                self.df = self.df.rename(columns={
                    'Quantity': 'CurrencyCode',
                    'Currency': 'RealPrice',
                    'Price': 'RealQuantity'
                })
                # Now map back to standard names expected by the rest of the script
                self.df['Quantity'] = self.df['RealQuantity']
                self.df['Price'] = self.df['RealPrice']

            # Filter out footer/empty rows
            # Run Date should be a valid date.
            self.df['Run Date'] = pd.to_datetime(self.df['Run Date'], errors='coerce')
            self.df = self.df.dropna(subset=['Run Date'])
            self.df['Date'] = self.df['Run Date']
            
            # Clean Amount column (remove $ and ,)
            if 'Amount' in self.df.columns:
                self.df['Amount'] = self.df['Amount'].replace(r'[\$,]', '', regex=True).astype(float)
                
            self.df = self.df.sort_values('Date')
        except Exception as e:
            print(f"Error loading data: {e}")
            return False
        return True

    def calculate_holdings(self):
        # Simple reconstruction of holdings over time
        # This is an approximation assuming the CSV contains full history or we start from 0
        
        current_holdings = {}
        
        for _, row in self.df.iterrows():
            action = str(row.get('Action', '')).upper()
            symbol = str(row.get('Symbol', ''))
            qty = row.get('Quantity', 0)
            try:
                if isinstance(qty, str):
                    qty = float(qty.replace(',', ''))
                if pd.isna(qty): qty = 0
                qty = float(qty)
            except ValueError:
                # print(f"Skipping row with invalid quantity: {qty} in row {row}")
                qty = 0
            
            # Handle different Fidelity actions
            if 'BOUGHT' in action or 'REINVESTMENT' in action:
                current_holdings[symbol] = current_holdings.get(symbol, 0) + qty
            elif 'SOLD' in action:
                current_holdings[symbol] = current_holdings.get(symbol, 0) + qty # qty is usually negative or we subtract
                if current_holdings[symbol] <= 0:
                    del current_holdings[symbol]
            
        self.holdings = current_holdings
        return self.holdings

    def analyze_performance(self):
        # Calculate realized gains/losses and income
        total_invested = 0
        current_value = 0 # We would need current prices for this, which we might not have in history
        # For this summary, we'll focus on realized P&L and Dividends from the history
        
        dividends = self.df[self.df['Action'].str.contains('DIVIDEND', case=False, na=False)]['Amount'].sum()
        
        # Simple realized P&L estimate (Amount sum usually gives net cash flow, not P&L directly without current value)
        # But for a "letter", we can summarize activity.
        
        return {
            "total_dividends": dividends,
            "transaction_count": len(self.df)
        }

    def get_concentration_risk(self):
        # Calculate weights based on estimated cost basis (since we don't have live prices)
        total_basis = 0
        holding_basis = {}
        
        # Re-scan to get cost basis of current holdings
        # This is complex with FIFO/LIFO, we'll do a simple average cost approximation for the "tool" demo
        # or just count positions.
        
        return self.holdings

    def get_factor_exposure(self):
        # Simple heuristic classification
        factors = {
            "Growth/Tech": ["NVDA", "QQQ", "ARKK", "SOFI", "HOOD", "NET", "ZETA", "ONTO", "AMZN", "GOOG", "MSFT", "AAPL", "TSM", "NBIS", "OSCR", "PYPL", "JD", "BABA", "BIDU", "REGN"],
            "Market/Core": ["VOO", "SPY", "BRKB", "VUG"],
            "Income/Yield": ["JEPI", "JEPQ", "TLT", "EPD", "ET", "MPLX", "DKL", "PALL"],
            "Defensive": ["COST", "UPS", "UNH"],
            "Cash/Equivalents": ["SPAXX", "FDRXX"]
        }
        
        exposure = {"Unclassified": 0}
        for f in factors:
            exposure[f] = 0
            
        for symbol, qty in self.holdings.items():
            found = False
            for factor, symbols in factors.items():
                if symbol in symbols:
                    exposure[factor] += qty
                    found = True
                    break
            if not found:
                exposure["Unclassified"] += qty
                
        # Remove empty
        return {k: v for k, v in exposure.items() if v > 0}

    def generate_tweaks(self):
        tweaks = []
        if len(self.holdings) < 5:
            tweaks.append("Consider diversifying your portfolio. You hold fewer than 5 positions.")
        
        # Check for single stock concentration
        total_shares = sum(self.holdings.values())
        if total_shares > 0:
            # Sort holdings by quantity for better reporting
            sorted_holdings = sorted(self.holdings.items(), key=lambda x: x[1], reverse=True)
            self.holdings = dict(sorted_holdings) # Update internal state to sorted
            
            for symbol, qty in self.holdings.items():
                weight = qty / total_shares
                # Ignore cash in concentration alert
                if symbol not in ["SPAXX", "FDRXX"] and weight > 0.20:
                    tweaks.append(f"Concentration Alert: {symbol} makes up {weight:.1%} of your share count.")
        
        # Factor tweaks
        exposures = self.get_factor_exposure()
        if "Growth/Tech" in exposures and exposures["Growth/Tech"] > total_shares * 0.5:
             tweaks.append("High exposure to Growth/Tech. Consider balancing with Defensive or Income assets.")

        return tweaks

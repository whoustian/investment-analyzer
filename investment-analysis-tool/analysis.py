import pandas as pd
import numpy as np
from datetime import datetime

class PortfolioAnalyzer:
    def __init__(self, history_filepath, positions_filepath=None):
        self.history_filepath = history_filepath
        self.positions_filepath = positions_filepath
        self.history_df = None
        self.positions_df = None
        self.holdings = {} # Symbol -> Quantity
        self.holdings_data = {} # Symbol -> Full Data Row
        self.cash_balance = 0.0
        self.performance = {}

    def load_data(self):
        # Load History
        try:
            self.history_df = pd.read_csv(self.history_filepath)
            self.history_df.columns = [c.strip() for c in self.history_df.columns]
            
            # Fix misaligned columns in history if needed
            if 'Quantity' in self.history_df.columns and self.history_df['Quantity'].astype(str).str.contains('USD').any():
                # print("Detected misaligned columns in history. Adjusting...")
                self.history_df = self.history_df.rename(columns={
                    'Quantity': 'CurrencyCode',
                    'Currency': 'RealPrice',
                    'Price': 'RealQuantity'
                })
                self.history_df['Quantity'] = self.history_df['RealQuantity']
                self.history_df['Price'] = self.history_df['RealPrice']

            self.history_df['Run Date'] = pd.to_datetime(self.history_df['Run Date'], errors='coerce')
            self.history_df = self.history_df.dropna(subset=['Run Date'])
            self.history_df['Date'] = self.history_df['Run Date']
            
            if 'Amount' in self.history_df.columns:
                self.history_df['Amount'] = self.history_df['Amount'].replace(r'[\$,]', '', regex=True).astype(float)
                
            self.history_df = self.history_df.sort_values('Date')
        except Exception as e:
            print(f"Error loading history data: {e}")
            return False

        # Load Positions if provided
        if self.positions_filepath:
            try:
                self.positions_df = pd.read_csv(self.positions_filepath)
                self.positions_df.columns = [c.strip() for c in self.positions_df.columns]
                
                # Clean up positions data
                # Remove footer rows (where Account Number is NaN or empty)
                self.positions_df = self.positions_df.dropna(subset=['Account Number'])
                
                # Convert numeric columns
                cols_to_clean = ['Quantity', 'Last Price', 'Current Value', 'Total Gain/Loss Dollar', 'Percent Of Account', 'Total Gain/Loss Percent', "Today's Gain/Loss Percent"]
                for col in cols_to_clean:
                    if col in self.positions_df.columns:
                        self.positions_df[col] = self.positions_df[col].astype(str).str.replace(r'[,\$\%]', '', regex=True)
                        self.positions_df[col] = pd.to_numeric(self.positions_df[col], errors='coerce').fillna(0)
                        
            except Exception as e:
                print(f"Error loading positions data: {e}")
                # We can continue without positions, just falling back to history
        
        return True
    def load_robinhood_data(self):
        try:
            # Robinhood CSVs usually have: provider_id, period, begin_execution_date, end_execution_date, settlement_date, id, instrument_url, symbol, side, quantity, price, state, type, trigger, price_arg, stop_price, fees, amount
            # Or simpler: symbol, name, price, quantity, etc. depending on export type.
            # We'll assume "orders" export.
            self.history_df = pd.read_csv(self.history_filepath)
            self.history_df.columns = [c.strip().lower().replace(' ', '_') for c in self.history_df.columns]
            
            # Normalize columns
            # Check if it's an orders file
            if 'side' in self.history_df.columns and 'symbol' in self.history_df.columns:
                # Filter for filled orders
                if 'state' in self.history_df.columns:
                    self.history_df = self.history_df[self.history_df['state'] == 'filled']
                
                # Sort by date
                if 'date' in self.history_df.columns:
                    self.history_df['Date'] = pd.to_datetime(self.history_df['date'])
                elif 'updated_at' in self.history_df.columns:
                    self.history_df['Date'] = pd.to_datetime(self.history_df['updated_at'])
                else:
                    # Fallback
                    self.history_df['Date'] = datetime.now()
                
                self.history_df = self.history_df.sort_values('Date')
                
                # Reconstruct holdings
                self.holdings = {}
                self.holdings_data = {}
                
                for _, row in self.history_df.iterrows():
                    symbol = str(row.get('symbol', '')).upper()
                    side = str(row.get('side', '')).lower()
                    qty = float(row.get('quantity', 0))
                    price = float(row.get('average_price', row.get('price', 0)))
                    
                    if side == 'buy':
                        self.holdings[symbol] = self.holdings.get(symbol, 0) + qty
                    elif side == 'sell':
                        self.holdings[symbol] = self.holdings.get(symbol, 0) - qty
                        if self.holdings[symbol] <= 0.0001: # Float tolerance
                             if symbol in self.holdings: del self.holdings[symbol]
                    
                    # Update "Current Value" estimate using last transaction price (imperfect but functional for history-only)
                    if symbol in self.holdings:
                        current_qty = self.holdings[symbol]
                        # Mock current value based on last known price
                        self.holdings_data[symbol] = {
                            'Current Value': current_qty * price,
                            'Total Gain/Loss Percent': 0.0, # Cannot calculate without live price
                            'Investment Type': 'Stocks' # Default
                        }
                
                # Clean up small residuals
                self.holdings = {k: v for k, v in self.holdings.items() if v > 0.001}
                
                # Set positions_df to mock structure for other methods
                self.positions_df = pd.DataFrame([
                    {'Symbol': k, 'Current Value': self.holdings_data[k]['Current Value'], 'Investment Type': 'Stocks'}
                    for k in self.holdings
                ])
                
                return True
            else:
                print("Unknown Robinhood CSV format.")
                return False
                
        except Exception as e:
            print(f"Error loading Robinhood data: {e}")
            return False

    def calculate_holdings(self):
        if self.positions_df is not None:
            # Use the accurate positions file
            # If holdings were already calculated (e.g. by load_robinhood_data), skip
            if not self.holdings:
                self.holdings = {}
                self.holdings_data = {}
                for _, row in self.positions_df.iterrows():
                    symbol = str(row.get('Symbol', ''))
                    if not symbol or symbol == 'nan' or 'Pending activity' in symbol: 
                        continue
                    
                    # Clean symbol (remove ** or similar artifacts)
                    symbol = symbol.replace('*', '')
                    
                    qty = row.get('Quantity', 0)
                    self.holdings[symbol] = qty
                    self.holdings_data[symbol] = row.to_dict()
        else:
            # Fallback to history reconstruction
            current_holdings = {}
            for _, row in self.history_df.iterrows():
                action = str(row.get('Action', '')).upper()
                symbol = str(row.get('Symbol', ''))
                qty = row.get('Quantity', 0)
                try:
                    if isinstance(qty, str):
                        qty = float(qty.replace(',', ''))
                    if pd.isna(qty): 
                        qty = 0
                    qty = float(qty)
                except ValueError:
                    qty = 0
                
                if 'BOUGHT' in action or 'REINVESTMENT' in action:
                    current_holdings[symbol] = current_holdings.get(symbol, 0) + qty
                elif 'SOLD' in action:
                    current_holdings[symbol] = current_holdings.get(symbol, 0) + qty
                    if current_holdings[symbol] <= 0:
                        if symbol in current_holdings: 
                            del current_holdings[symbol]
            
            self.holdings = current_holdings
            
        return self.holdings

    def analyze_performance(self):
        # Dividends from history
        dividends = 0
        if self.history_df is not None:
            dividends = self.history_df[self.history_df['Action'].str.contains('DIVIDEND', case=False, na=False)]['Amount'].sum()
        
        # Portfolio Value and P&L from Positions
        total_value = 0
        total_gain_loss = 0
        total_gain_loss_pct = 0
        
        if self.positions_df is not None:
            total_value = self.positions_df['Current Value'].sum()
            if 'Total Gain/Loss Dollar' in self.positions_df.columns:
                total_gain_loss = self.positions_df['Total Gain/Loss Dollar'].sum()
                if total_value - total_gain_loss != 0:
                    total_gain_loss_pct = (total_gain_loss / (total_value - total_gain_loss)) * 100
        
        return {
            "total_dividends": dividends,
            "transaction_count": len(self.history_df) if self.history_df is not None else 0,
            "total_value": total_value,
            "total_gain_loss": total_gain_loss,
            "total_gain_loss_pct": total_gain_loss_pct
        }

    def get_asset_allocation(self):
        if self.positions_df is None:
            return {}
            
        # Group by 'Investment Type' (e.g., Stocks, ETFs, Cash)
        # Note: The CSV column might be 'Investment Type' or just inferred.
        # Based on file view: "Investment Type" column exists.
        if 'Investment Type' in self.positions_df.columns:
            allocation = self.positions_df.groupby('Investment Type')['Current Value'].sum().to_dict()
            return allocation
        return {}

    def get_factor_exposure(self):
        factors = {
            "Growth/Tech": ["NVDA", "QQQ", "ARKK", "SOFI", "HOOD", "NET", "ZETA", "ONTO", "AMZN", "GOOG", "MSFT", "AAPL", "TSM", "NBIS", "OSCR", "PYPL", "JD", "BABA", "BIDU", "REGN"],
            "Market/Core": ["VOO", "SPY", "BRKB", "VUG", "VTI", "VXUS", "ALLW"],
            "Income/Yield": ["JEPI", "JEPQ", "TLT", "EPD", "ET", "MPLX", "DKL", "PALL"],
            "Defensive": ["COST", "UPS", "UNH"],
            "Cash/Equivalents": ["SPAXX", "FDRXX"]
        }
        
        exposure = {"Unclassified": 0}
        for f in factors:
            exposure[f] = 0
            
        # Use Value if available, otherwise Quantity
        use_value = self.positions_df is not None
        
        for symbol, qty in self.holdings.items():
            val = qty
            if use_value and symbol in self.holdings_data:
                val = self.holdings_data[symbol].get('Current Value', 0)
                
            found = False
            for factor, symbols in factors.items():
                if symbol in symbols:
                    exposure[factor] += val
                    found = True
                    break
            if not found:
                exposure["Unclassified"] += val
                
        return {k: v for k, v in exposure.items() if v > 0}

    def generate_tweaks(self):
        tweaks = []
        if len(self.holdings) < 5:
            tweaks.append("Consider diversifying your portfolio. You hold fewer than 5 positions.")
        
        # Concentration Risk (by Value if possible)
        total_exposure = sum(self.get_factor_exposure().values())
        
        if total_exposure > 0:
            # Sort by value/qty
            sorted_holdings = []
            for s, q in self.holdings.items():
                val = q
                if self.positions_df is not None and s in self.holdings_data:
                    val = self.holdings_data[s].get('Current Value', 0)
                sorted_holdings.append((s, val))
            
            sorted_holdings.sort(key=lambda x: x[1], reverse=True)
            
            for symbol, val in sorted_holdings:
                weight = val / total_exposure
                if symbol not in ["SPAXX", "FDRXX"] and weight > 0.15:
                    tweaks.append(f"Concentration Alert: {symbol} makes up {weight:.1%} of your portfolio value.")
        
        # Factor tweaks
        exposures = self.get_factor_exposure()
        if "Growth/Tech" in exposures and exposures["Growth/Tech"] > total_exposure * 0.5:
             tweaks.append("High exposure to Growth/Tech (>50%). Consider balancing with Defensive or Income assets.")

        return tweaks

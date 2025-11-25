import sys
import os
from datetime import datetime
from analysis import PortfolioAnalyzer
from writer import render_letter

def main():
    # Check for file'?????????;./////
    history_path = 'c:/Users/whous/.gemini/antigravity/scratch/investment-analysis-tool/Accounts_History.csv'
    positions_path = 'c:/Users/whous/.gemini/antigravity/scratch/investment-analysis-tool/Portfolio_Positions_Nov-22-2025.csv'
    
    if not os.path.exists(history_path):
        print(f"History file not found at {history_path}. Using mock data for demonstration.")
        history_path = 'c:/Users/whous/.gemini/antigravity/scratch/investment-analysis-tool/mock_data.csv'

    analyzer = PortfolioAnalyzer(history_path, positions_path)
    if analyzer.load_data():
        print("Data loaded successfully.")
        holdings = analyzer.calculate_holdings()
        perf = analyzer.analyze_performance()
        tweaks = analyzer.generate_tweaks()
        factors = analyzer.get_factor_exposure()
        allocation = analyzer.get_asset_allocation()
        
        data = {
            "date": datetime.now().strftime("%B %Y"),
            "transaction_count": perf['transaction_count'],
            "performance": perf,
            "holdings": holdings,
            "holdings_data": analyzer.holdings_data,
            "factors": factors,
            "allocation": allocation,
            "tweaks": tweaks
        }
        
        letter_content = render_letter(data)
        
        output_path = 'c:/Users/whous/.gemini/antigravity/scratch/Monthly_Letter.md'
        with open(output_path, 'w') as f:
            f.write(letter_content)
            
        print(f"Letter generated at: {output_path}")
        print("-" * 20)
        print(letter_content)
    else:
        print("Failed to load data.")

if __name__ == "__main__":
    main()

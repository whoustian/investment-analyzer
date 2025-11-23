import sys
import os
from datetime import datetime
from analysis import PortfolioAnalyzer
from writer import render_letter

def main():
    # Check for file
    file_path = 'c:/Users/whous/.gemini/antigravity/scratch/investment-analysis-toolAccounts_History.csv'
    if not os.path.exists(file_path):
        print(f"File not found at {file_path}. Using mock data for demonstration.")
        file_path = 'c:/Users/whous/.gemini/antigravity/scratch/investment-analysis-tool/mock_data.csv'

    analyzer = PortfolioAnalyzer(file_path)
    if analyzer.load_data():
        print("Data loaded successfully.")
        holdings = analyzer.calculate_holdings()
        perf = analyzer.analyze_performance()
        tweaks = analyzer.generate_tweaks()
        factors = analyzer.get_factor_exposure()
        
        data = {
            "date": datetime.now().strftime("%B %Y"),
            "transaction_count": perf['transaction_count'],
            "performance": perf,
            "holdings": holdings,
            "factors": factors,
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

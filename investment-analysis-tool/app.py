from flask import Flask, render_template, request, send_file, Response, jsonify
import os
import markdown
from datetime import datetime, timedelta
from analysis import PortfolioAnalyzer
from writer import render_letter
import plaid_service

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/', methods=['GET'])
def index():
    return render_template('landing.html')

@app.route('/fidelity', methods=['GET'])
def fidelity():
    return render_template('fidelity.html')

@app.route('/robinhood', methods=['GET'])
def robinhood():
    return render_template('robinhood.html')

@app.route('/plaid', methods=['GET'])
def plaid_page():
    plaid_env = os.getenv('PLAID_ENV', 'sandbox')
    return render_template('plaid.html', plaid_env=plaid_env)

@app.route('/create_link_token', methods=['POST'])
def create_link_token():
    try:
        # In a real app, use a unique user ID from session/db
        user_id = "user_good" 
        link_token = plaid_service.create_link_token(user_id)
        return jsonify({'link_token': link_token})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/exchange_public_token', methods=['POST'])
def exchange_public_token():
    try:
        public_token = request.json.get('public_token')
        access_token = plaid_service.exchange_public_token(public_token)
        return jsonify({'success': True, 'access_token': access_token})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/analyze_plaid', methods=['POST'])
def analyze_plaid():
    try:
        access_token = request.json.get('access_token')
        if not access_token:
            return "Missing access token", 400
            
        # Fetch data
        holdings_response = plaid_service.get_holdings(access_token)
        
        # Fetch transactions for the last year
        start_date = (datetime.now() - timedelta(days=365)).date()
        end_date = datetime.now().date()
        transactions_response = plaid_service.get_transactions(access_token, start_date, end_date)
        
        # Analyze
        analyzer = PortfolioAnalyzer(None, None) # No files needed
        if analyzer.load_plaid_data(holdings_response, transactions_response):
            return generate_report(analyzer)
        else:
            return "Error processing Plaid data.", 500
            
    except Exception as e:
        print(f"Analysis error: {e}")
        return f"Analysis error: {e}", 500

@app.route('/analyze_fidelity', methods=['POST'])
def analyze_fidelity():
    if 'history_file' not in request.files or 'positions_file' not in request.files:
        return "No file part", 400
    
    history_file = request.files['history_file']
    positions_file = request.files['positions_file']
    
    if history_file.filename == '' or positions_file.filename == '':
        return "No selected file", 400
        
    if history_file and positions_file:
        # Save files temporarily
        history_path = os.path.join(app.config['UPLOAD_FOLDER'], 'history.csv')
        positions_path = os.path.join(app.config['UPLOAD_FOLDER'], 'positions.csv')
        
        history_file.save(history_path)
        positions_file.save(positions_path)
        
        # Run Analysis
        analyzer = PortfolioAnalyzer(history_path, positions_path)
        if analyzer.load_data():
            return generate_report(analyzer)
        else:
            return "Error processing files. Please check the format.", 500

    return "Unknown error", 500

@app.route('/analyze_robinhood', methods=['POST'])
def analyze_robinhood():
    if 'robinhood_file' not in request.files:
        return "No file part", 400
        
    rh_file = request.files['robinhood_file']
    
    if rh_file.filename == '':
        return "No selected file", 400
        
    if rh_file:
        rh_path = os.path.join(app.config['UPLOAD_FOLDER'], 'robinhood.csv')
        rh_file.save(rh_path)
        
        # Initialize analyzer with RH file as history, no separate positions file
        # We will need to tell the analyzer this is Robinhood data
        analyzer = PortfolioAnalyzer(rh_path, None)
        # We'll add a specific method or flag for RH loading
        if analyzer.load_robinhood_data():
             return generate_report(analyzer)
        else:
             return "Error processing Robinhood file.", 500

    return "Unknown error", 500

def generate_report(analyzer):
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
    
    letter_md = render_letter(data)
    letter_html = markdown.markdown(letter_md)
    
    return render_template('result.html', letter_html=letter_html, letter_md=letter_md)

@app.route('/download', methods=['POST'])
def download():
    content = request.form.get('content')
    return Response(
        content,
        mimetype="text/markdown",
        headers={"Content-disposition": "attachment; filename=Monthly_Letter.md"}
    )

if __name__ == '__main__':
    app.run(debug=True, port=5000)

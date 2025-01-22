from flask import Flask, send_from_directory, request, jsonify
import requests
import csv
from io import StringIO

app = Flask(__name__)

def clean_price(price_str):
    try:
        # '원' 제거하고 쉼표 제거
        return int(price_str.replace('원', '').replace(',', ''))
    except:
        return 0

def load_products():
    try:
        csv_url = "https://raw.githubusercontent.com/alisyos/shopping_gpt/main/tailor_product_20250121.csv"
        response = requests.get(csv_url)
        csv_data = StringIO(response.text)
        reader = csv.DictReader(csv_data)
        return list(reader)
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return []

@app.route('/')
def home():
    return send_from_directory('static', 'index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/search', methods=['POST'])
def search():
    try:
        data = request.json
        query = data.get('query', '').strip().lower()
        
        if not query:
            return jsonify({'results': [], 'total_count': 0})
        
        # CSV 파일에서 데이터 로드
        products = load_products()
        
        # 검색어로 필터링
        results = []
        for product in products:
            if query in product['product_name'].lower():
                current_price = clean_price(product['current_price'])
                original_price = clean_price(product['original_price']) if product['original_price'] else None
                
                results.append({
                    'product_name': product['product_name'],
                    'mall_name': product['mall_name'],
                    'current_price': f"{current_price:,}원",
                    'original_price': f"{original_price:,}원" if original_price else None,
                    'thumbnail_img_url': product['thumbnail_img_url'],
                    'product_url_path': product['product_url_path']
                })
                if len(results) >= 10:  # 최대 10개 결과
                    break
        
        return jsonify({
            'results': results,
            'total_count': len(results)
        })
        
    except Exception as e:
        print(f"Search error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/test')
def test():
    return {"message": "Hello from Flask!"}

# Vercel requires this
app.debug = True

if __name__ == '__main__':
    app.run()
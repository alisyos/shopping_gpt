from flask import Flask, send_from_directory, request, jsonify
from openai import OpenAI
import os
import requests
import csv
from io import StringIO
import json

app = Flask(__name__)
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

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

def clean_price(price_str):
    try:
        return int(price_str.replace(',', '').replace('원', ''))
    except:
        return 0

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
        filtered_products = []
        for product in products:
            if query in product['product_name'].lower():
                try:
                    current_price = clean_price(product['current_price'])
                    original_price = clean_price(product['original_price']) if product['original_price'] else None
                    
                    filtered_products.append({
                        'product_name': product['product_name'],
                        'mall_name': product['mall_name'],
                        'current_price': f"{current_price:,}원",
                        'original_price': f"{original_price:,}원" if original_price else None,
                        'thumbnail_img_url': product['thumbnail_img_url'],
                        'product_url_path': product['product_url_path']
                    })
                    
                    if len(filtered_products) >= 10:  # 최대 10개 결과
                        break
                except Exception as e:
                    print(f"상품 처리 중 오류: {str(e)}")
                    continue
        
        return jsonify({
            'results': filtered_products,
            'total_count': len(filtered_products)
        })
        
    except Exception as e:
        print(f"Search error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/recommend', methods=['POST'])
def recommend():
    try:
        data = request.json
        query = data.get('query', '')
        products = data.get('products', [])
        
        if not products:
            return jsonify({
                'recommendations': [],
                'message': '추천할 상품이 없습니다.'
            })
            
        prompt = f"""
사용자 질문: {query}

다음은 검색된 상품 목록입니다:
{json.dumps(products[:3], ensure_ascii=False, indent=2)}

위 상품들 중에서 사용자의 요구사항에 가장 적합한 상품들을 선택하고, 각각에 대해 추천 이유와 스타일링 제안을 해주세요.
"""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful shopping assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        recommendations = []
        for product in products[:3]:
            recommendations.append({
                'product_name': product['product_name'],
                'reason': "이 상품은 귀하의 검색 조건과 잘 맞는 제품입니다.",
                'styling_tip': response.choices[0].message.content,
                'thumbnail_img_url': product['thumbnail_img_url'],
                'product_url_path': product['product_url_path'],
                'price': product['current_price'],
                'mall_name': product['mall_name']
            })
        
        return jsonify({
            'recommendations': recommendations
        })
        
    except Exception as e:
        print(f"Recommend error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run()
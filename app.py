from flask import Flask, send_from_directory, request, jsonify
import requests
import csv
from io import StringIO
import json
import re
import math
import ast

app = Flask(__name__)

# 전역 변수로 style_mapping 정의
style_mapping = {
    '스포츠': ['스포츠', '운동', '애슬레저', '스포츠웨어'],
    '캐주얼': ['캐주얼', '데일리룩', '일상복', '편한'],
    '데일리': ['데일리', '일상', '평상복', '기본'],
    '페미닌': ['페미닌', '여성스러운', '로맨틱', '걸리시'],
    '포멀': ['포멀', '정장', '비즈니스', '격식'],
    '섹시': ['섹시', '글래머', '섹시한', '볼륨'],
    '미니멀': ['미니멀', '심플', '단순한', '깔끔한'],
    '스포티': ['스포티', '스포티브', '액티브', '활동적인'],
    '럭셔리': ['럭셔리', '고급스러운', '명품', '프리미엄'],
    '스트릿': ['스트릿', '길거리', '힙합', '스케이터'],
    '트렌디': ['트렌디', '유행', '최신', '인기'],
    '클래식': ['클래식', '고전적인', '전통적인', '베이직'],
    '빈티지': ['빈티지', '레트로', '구제', '올드스쿨'],
    '보헤미안': ['보헤미안', '보헤미안룩', '자유로운', '히피'],
    '글래머러스': ['글래머러스', '화려한', '돋보이는', '세련된'],
    '프레피': ['프레피', '학생룩', '아카데믹', '교복'],
    '아웃도어': ['아웃도어', '등산복', '야외활동', '캠핑'],
    '유니크': ['유니크', '독특한', '개성있는', '특이한'],
    '컨템포러리': ['컨템포러리', '현대적인', '모던한', '세련된']
}

# 카테고리 매핑 정의
CATEGORY_MAPPING = {
    'TOP': ['셔츠&블라우스', '반팔티', '니트', '후드/맨투맨', '긴팔티', '트레이닝', '나시'],
    'PANTS': ['롱팬츠', '슬랙스', '레깅스', '숏팬츠', '트레이닝'],
    'DRESS&SKIRT': ['스커트'],
    'OUTER': ['가디건', '베스트', '자켓', '점퍼', '집업'],
    'BEST': ['펌프스', '샌들/뮬', '스니커즈', '플랫/로퍼', '부츠/앵클', '슬링백', '블로퍼/슬리퍼'],
    'BAG': ['크로스백', '미니백', '숄더백', '토드백', '캔버스/백팩', '클러치/파우치'],
    'ACC': ['모자', '귀걸이', '목걸이'],
    'UNDERWEAR': ['브라', '팬티', '보정']
}

# 검색어 매핑 정의
SEARCH_KEYWORD_MAPPING = {
    '모자': {
        'categories': ['모자', '볼캡', '버킷햇'],
        'keywords': ['모자', '볼캡', '버킷햇', '캡'],
        'description_keywords': ['모자', '볼캡', '버킷햇', '캡', '햇', '비니']
    },
    '바지': {
        'categories': ['PANTS', '팬츠', '바지', '슬랙스', '진'],
        'keywords': ['바지', '팬츠', '슬랙스', '진', '청바지', '데님'],
        'description_keywords': ['바지', '팬츠', '슬랙스', '진', '청바지', '데님', '와이드', '스트레이트']
    }
}

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
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'results': [], 'total_count': 0})
        
        # CSV 파일에서 데이터 로드
        products = load_products()
        
        # 검색어로 필터링 (상품명에서 검색)
        filtered_products = []
        for product in products:
            if query.lower() in product['product_name'].lower():
                try:
                    filtered_products.append({
                        'product_name': product['product_name'],
                        'mall_name': product['mall_name'],
                        'current_price': f"{int(float(product['current_price'].replace(',', '').replace('원', ''))):,}원",
                        'original_price': f"{int(float(product['original_price'].replace(',', '').replace('원', ''))):,}원" if product['original_price'] else None,
                        'thumbnail_img_url': product['thumbnail_img_url'],
                        'product_url_path': product['product_url_path']
                    })
                except Exception as e:
                    print(f"상품 처리 중 오류: {str(e)}")
                    continue
                
                if len(filtered_products) >= 10:  # 최대 10개 결과
                    break
        
        return jsonify({
            'results': filtered_products,
            'total_count': len(filtered_products)
        })
        
    except Exception as e:
        print(f"Search error: {e}")
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
        
        # 간단한 추천 로직 (첫 3개 상품 반환)
        recommendations = []
        for product in products[:3]:
            recommendations.append({
                'product_name': product['product_name'],
                'reason': f"{product['product_name']}은(는) 검색하신 '{query}'와(과) 잘 어울리는 상품입니다.",
                'styling_tip': "다른 기본 아이템들과 매치하여 스타일리시하게 연출해보세요.",
                'thumbnail_img_url': product['thumbnail_img_url'],
                'product_url_path': product['product_url_path'],
                'price': product['current_price'],
                'mall_name': product['mall_name']
            })
        
        return jsonify({
            'recommendations': recommendations
        })
        
    except Exception as e:
        print(f"Recommend error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/test')
def test():
    return {"message": "Hello from Flask!"}

# Vercel requires this
app.debug = True

if __name__ == '__main__':
    app.run()
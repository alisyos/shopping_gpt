from flask import Flask, send_from_directory, request, jsonify
from openai import OpenAI
import os
import requests
import csv
from io import StringIO
import json
import re
import math
import ast
import traceback

app = Flask(__name__)
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

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
        
        # 필터 값 분석
        filter_values = analyze_query(query)
        print(f"분석된 필터 값: {filter_values}")
        
        # CSV 파일에서 데이터 로드
        products = load_products()
        filtered_products = products.copy()
        
        # 키워드 필터링
        if filter_values and filter_values.get('keywords'):
            filtered_products = [
                product for product in filtered_products
                if any(keyword.lower() in product['product_name'].lower() 
                      for keyword in filter_values['keywords'])
            ]
        
        # 가격 필터링
        if filter_values and filter_values.get('price_limit'):
            price_limit = filter_values['price_limit']
            filtered_products = [
                product for product in filtered_products
                if float(product['current_price'].replace(',', '').replace('원', '')) <= price_limit
            ]
        
        # 스타일 필터링
        if filter_values and filter_values.get('style'):
            filtered_products = [
                product for product in filtered_products
                if 'style' in product and any(
                    filter_values['style'].lower() in style.lower()
                    for style in ast.literal_eval(product['style'])
                )
            ]
        
        # 색상 필터링
        if filter_values and filter_values.get('color'):
            filtered_products = [
                product for product in filtered_products
                if 'color_option' in product and 
                filter_values['color'].lower() in product['color_option'].lower()
            ]
        
        # 시즌 필터링
        if filter_values and filter_values.get('season'):
            seasons = filter_values['season'] if isinstance(filter_values['season'], list) else [filter_values['season']]
            filtered_products = [
                product for product in filtered_products
                if 'season' in product and any(
                    season in ast.literal_eval(product['season'])
                    for season in seasons
                )
            ]
        
        # 결과 포맷팅
        formatted_results = []
        for product in filtered_products[:10]:  # 최대 10개 결과
            try:
                formatted_results.append({
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
        
        return jsonify({
            'results': formatted_results,
            'total_count': len(formatted_results)
        })
        
    except Exception as e:
        print(f"Search error: {str(e)}")
        traceback.print_exc()
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
        
        # AI 추천 결과 생성
        recommendations = get_ai_recommendations(query, products)
        
        if recommendations:
            return jsonify(recommendations)
        else:
            return jsonify({
                'recommendations': [],
                'message': '추천 생성 중 오류가 발생했습니다.'
            })
        
    except Exception as e:
        print(f"Recommend error: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/test')
def test():
    return {"message": "Hello from Flask!"}

def analyze_query(query):
    try:
        prompt = f"""
사용자의 쇼핑 관련 질문을 분석하여 다음 필터 값들을 JSON 형식으로 추출해주세요.

분석 규칙:
1. 실제 검색하고자 하는 상품 키워드만 'keywords'에 포함
2. 색상은 별도로 추출하여 'color' 필드에 포함
   - 예시: "검정색 바지" → color: "블랙"
   - 색상 매핑: 검정/검은색 → 블랙, 하얀/흰색 → 화이트, 빨간색 → 레드 등
3. 가격 제한은 다음 규칙을 따라 추출:
   - "5만원 이하" → 50000
   - 항상 원 단위로 변환하여 숫자만 반환

입력: {query}

JSON 형식으로만 응답해주세요:
{{
    "style": "다음 중 하나만 선택 [스포츠, 캐주얼, 데일리, 페미닌, 포멀, 섹시, 미니멀, 스포티, 럭셔리, 스트릿, 트렌디, 클래식, 빈티지, 보헤미안, 글래머러스, 프레피, 아웃도어, 유니크, 컨템포러리]",
    "gender": "명시적인 성별 언급이 있는 경우에만 [여성, 남성, 공용] 중 선택, 없으면 null",
    "age_group": "다음 중 하나만 선택 [10대, 20대, 30대, 40대, 50대 이상], 없으면 null",
    "price_limit": "가격 제한이 있는 경우 원 단위 숫자로 변환, 없으면 null",
    "season": "다음 중 선택 [봄, 여름, 가을, 겨울, 간절기] (여러 개 가능), 없으면 null",
    "keywords": "실제 검색하고자 하는 상품 키워드만 포함 (배열)",
    "color": "색상 언급이 있는 경우 매핑된 색상명, 없으면 null"
}}"""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful shopping assistant that analyzes user queries and extracts structured filter values. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        content = response.choices[0].message.content.strip()
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0].strip()
        elif '```' in content:
            content = content.split('```')[1].strip()

        return json.loads(content)

    except Exception as e:
        print(f"Query analysis error: {str(e)}")
        return None

def get_ai_recommendations(query, products, top_n=3):
    try:
        if not products:
            return {
                "recommendations": [],
                "message": "검색 결과가 없어 추천을 생성할 수 없습니다."
            }

        prompt = f"""
사용자 질문: {query}

다음은 검색된 상품 목록입니다:
{json.dumps(products[:10], ensure_ascii=False, indent=2)}

위 상품들 중에서 사용자의 요구사항에 가장 적합한 상품 3개를 선택하고, 아래 가이드라인에 따라 상세한 추천 이유와 스타일링 제안을 해주세요:

1. 사용자의 요구사항 분석
2. 상품 추천 시 포함할 내용
3. 스타일링 제안

반드시 아래 형식의 유효한 JSON으로 응답해주세요:

{{
    "recommendations": [
        {{
            "product_name": "상품명",
            "reason": "상세한 추천 이유",
            "styling_tip": "스타일링 제안",
            "thumbnail_img_url": "이미지URL",
            "product_url_path": "상품URL",
            "price": "가격",
            "mall_name": "쇼핑몰명"
        }}
    ]
}}"""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful shopping assistant that provides personalized product recommendations. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        content = response.choices[0].message.content.strip()
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0].strip()
        elif '```' in content:
            content = content.split('```')[1].strip()

        return json.loads(content)

    except Exception as e:
        print(f"AI recommendation error: {str(e)}")
        return None

# Vercel requires this
app.debug = True

if __name__ == '__main__':
    app.run()
from flask import Flask, send_from_directory, request, jsonify
import pandas as pd
import requests
from io import StringIO

app = Flask(__name__)

def load_products():
    try:
        # 정확한 Raw URL 사용
        csv_url = "https://raw.githubusercontent.com/alisyos/shopping_gpt/main/tailor_product_20250121.csv"
        response = requests.get(csv_url)
        df = pd.read_csv(StringIO(response.text))
        return df
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return pd.DataFrame()

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
        df = load_products()
        
        # 검색어로 필터링
        mask = df['product_name'].str.contains(query, case=False, na=False)
        filtered_df = df[mask].head(10)
        
        # 결과 포맷팅
        results = []
        for _, row in filtered_df.iterrows():
            results.append({
                'product_name': str(row['product_name']),
                'mall_name': str(row['mall_name']),
                'current_price': f"{row['current_price']:,}원",
                'original_price': f"{row['original_price']:,}원" if pd.notna(row['original_price']) else None,
                'thumbnail_img_url': str(row['thumbnail_img_url']),
                'product_url_path': str(row['product_url_path'])
            })
        
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
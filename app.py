from flask import Flask, send_from_directory, request, jsonify
import pandas as pd
import re

app = Flask(__name__)

# CSV 파일 로드
def load_products():
    try:
        df = pd.read_csv('tailor_product_20250121.csv')
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
        
        # 검색어로 필터링 (상품명에서 검색)
        mask = df['product_name'].str.contains(query, case=False, na=False)
        filtered_df = df[mask].head(10)  # 상위 10개 결과만
        
        # 결과 포맷팅
        results = []
        for _, row in filtered_df.iterrows():
            results.append({
                'product_name': row['product_name'],
                'mall_name': row['mall_name'],
                'current_price': f"{row['current_price']:,}원",
                'original_price': f"{row['original_price']:,}원" if pd.notna(row['original_price']) else None,
                'thumbnail_img_url': row['thumbnail_img_url'],
                'product_url_path': row['product_url_path']
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
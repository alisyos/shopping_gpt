from flask import Flask, send_from_directory, request, jsonify

app = Flask(__name__)

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
        query = data.get('query', '')
        
        # 테스트용 응답
        return jsonify({
            'results': [
                {
                    'product_name': '테스트 상품',
                    'mall_name': '테스트몰',
                    'current_price': '10,000원',
                    'original_price': '12,000원',
                    'thumbnail_img_url': '/static/no-image.png',
                    'product_url_path': '#'
                }
            ],
            'total_count': 1
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/test')
def test():
    return {"message": "Hello from Flask!"}

# Vercel requires this
app.debug = True

if __name__ == '__main__':
    app.run()
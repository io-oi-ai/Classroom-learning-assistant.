from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return jsonify({"status": "success", "message": "API is running"})

@app.route('/api/status')
def status():
    return jsonify({
        "status": "online",
        "version": "1.0.0",
        "service": "classroom-learning-assistant"
    })

# 添加一个通配符路由来处理不存在的路径
@app.errorhandler(404)
def not_found(e):
    return jsonify({"status": "error", "message": "Route not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)

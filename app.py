# app.py (最終版 - 整合 ads.txt 路由)

import os
# 新增引入 send_from_directory
from flask import Flask, request, jsonify, send_from_directory 
from flask_cors import CORS

# 嘗試從 imars_core 引入，確保 imars_core.py 存在
try:
    from imars_core import start_imars_refinement
except ImportError:
    start_imars_refinement = None
    print("FATAL ERROR: Could not import start_imars_refinement from imars_core. Is imars_core.py present?")

app = Flask(__name__)
# 解決 CORS 的關鍵：允許所有來源（*）
print("IMARS Flask App Initializing...") 
CORS(app, supports_credentials=True, origins='*') 

# ---------------------------------------------
# 👇 新增：ads.txt 路由
# ---------------------------------------------
@app.route('/ads.txt', methods=['GET'])
def serve_ads_txt():
    """
    處理 /ads.txt 請求，直接提供 ads.txt 檔案。
    """
    # 這會讓 Render 在訪問 http://yourdomain.com/ads.txt 時，提供該檔案
    # 假設 ads.txt 放在應用程式的根目錄 (與 app.py 同層)
    return send_from_directory(app.root_path, 'ads.txt', mimetype='text/plain')
# ---------------------------------------------
# 👆 新增結束
# ---------------------------------------------


@app.route('/', methods=['GET'])
def home():
    if not start_imars_refinement:
        return "FATAL ERROR: imars_core not loaded.", 500
        
    return "IMARS Backend is running! (API endpoint is /api/distill)", 200

@app.route('/api/distill', methods=['POST'])
def handle_distillation():
    data = request.json
    
    user_prompt = data.get('prompt')
    api_keys_pool = data.get('api_keys_pool', []) 

    if not user_prompt:
        return jsonify({"error": "Missing prompt"}), 400
        
    if not api_keys_pool or not isinstance(api_keys_pool, list) or not api_keys_pool[0].get('key'):
        return jsonify({
            "success": False,
            "error": "Missing required API key pool. Please provide at least one key."
        }), 400

    try:
        final_answer, process_history = start_imars_refinement(user_prompt, api_keys_pool)
        
        if final_answer is None:
             return jsonify({
                "success": False,
                "error": "AI 服務啟動或精煉失敗。請檢查 API Keys 或供應商名稱是否正確。",
                "log": process_history
            }), 500

        return jsonify({
            "success": True,
            "final_answer": final_answer,
            "log": process_history
        })
    
    except Exception as e:
        print(f"Unhandled Error during distillation: {e}")
        return jsonify({"error": f"Internal distillation error: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
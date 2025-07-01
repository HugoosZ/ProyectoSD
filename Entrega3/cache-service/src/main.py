from flask import Flask, request, jsonify
import json
from cache_manager import RedisCache

app = Flask(__name__)
cache = RedisCache()

@app.route('/set', methods=['POST'])
def set_cache():
    """Endpoint para guardar datos en caché"""
    try:
        data = request.get_json()
        key = data.get('key')
        value = data.get('value')
        ttl = data.get('ttl')
        
        if not key or value is None:
            return jsonify({'error': 'key y value son requeridos'}), 400
            
        cache.set(key, value, ttl)
        return jsonify({'success': True, 'message': f'Datos guardados en clave: {key}'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get/<key>', methods=['GET'])
def get_cache(key):
    """Endpoint para obtener datos del caché"""
    try:
        value = cache.get(key)
        if value is not None:
            return jsonify({'found': True, 'key': key, 'value': value})
        else:
            return jsonify({'found': False, 'key': key})
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/clear', methods=['POST'])
def clear_cache():
    """Endpoint para limpiar el caché"""
    try:
        cache.limpiar_cache()
        return jsonify({'success': True, 'message': 'Cache limpiado'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Endpoint de salud"""
    try:
        # Test Redis connection
        cache.client.ping()
        return jsonify({'status': 'healthy', 'redis': 'connected'})
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Iniciando API del servicio de caché...")
    app.run(host='0.0.0.0', port=8000, debug=False)  

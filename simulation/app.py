from flask import Flask
from simulation.api.endpoints import api_bp
from flask_compress import Compress

from simulation.simulation.simulation import start_simulation

from flask_cors import CORS
app = Flask(__name__)
Compress(app)
CORS(app)

# Register API routes
app.register_blueprint(api_bp)

if __name__ == '__main__':
    print("✅ Simulation initialized.")
    start_simulation()
    print("🚀 Simulation running. Fetch state via /getstate.")
    app.run(host='127.0.0.1', port=5000, threaded=True)


from flask import Flask
from api.endpoints import api_bp
from simulation.simulation import start_simulation

app = Flask(__name__)

# Register API routes
app.register_blueprint(api_bp)

if __name__ == '__main__':
    print("✅ Simulation initialized.")
    start_simulation()
    print("🚀 Simulation running. Fetch state via /getstate.")
    app.run(host='127.0.0.1', port=5000, threaded=True)


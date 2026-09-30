from flask import Flask
from flask_cors import CORS
from config import Config
from database.database import db
from database import models
from routes.health import health_bp
from routes.queue import queue_bp
from routes.dashboard import analytics_bp
from routes.food import food_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app)
    db.init_app(app)
    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(queue_bp, url_prefix="/api")
    app.register_blueprint(analytics_bp, url_prefix="/api")
    app.register_blueprint(food_bp, url_prefix="/api")
    with app.app_context():
        db.create_all()
    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5001)

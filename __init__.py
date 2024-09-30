from flask import Flask
from pymongo import MongoClient
from config import Config
from flask_jwt_extended import JWTManager
from flask_cors import CORS

jwt = JWTManager()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app, resources={r"/*": {"origins": "http://localhost:4200"}}, supports_credentials=True)

    client = MongoClient('localhost', 27017)
    app.db = client.flask_database
    jwt.init_app(app)

    from predictor.routes import predictor
    from predictor.kafka_consumer import kafka_consumer
    from manipulation_with_set_of_rules.routes import blood_analysis_rules

    app.register_blueprint(predictor)
    app.register_blueprint(kafka_consumer)
    app.register_blueprint(blood_analysis_rules)

    return app

from flask import Blueprint, jsonify, current_app
from bson.objectid import ObjectId
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

predictor = Blueprint('predictor', __name__)


@predictor.route('/predict_associated_condition/<string:report_id>', methods=['GET'])
@jwt_required()
def predict_associated_condition(report_id):
    try:
        laboratory_reports = current_app.db.laboratory_reports

        report_object_id = ObjectId(report_id)

        report = laboratory_reports.find_one({"_id": report_object_id})
        if report:
            if report.get('associated_condition'):
                return jsonify({'message': f"Associated condition for given report is {report['condition']}",
                                'condition': report['condition']}), 200
            else:
                return jsonify({'message': 'Condition not available yet'}), 202
        else:
            return jsonify({"error": "Report not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

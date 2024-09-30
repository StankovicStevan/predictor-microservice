from flask import Blueprint, jsonify, current_app, request
import pandas as pd
from bson import ObjectId
from flask_jwt_extended import jwt_required

blood_analysis_rules = Blueprint('blood_analysis_rules', __name__)


@blood_analysis_rules.route('/add_rules_from_csv_to_db', methods=['POST'])
@jwt_required()
def upload_csv():
    # Ensure a file is provided
    if 'blood_analysis_rules' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['blood_analysis_rules']

    try:
        rules = current_app.db.blood_analysis_rules
        # Read the CSV file into a pandas DataFrame
        df = pd.read_csv(file, encoding='windows-1252', encoding_errors='replace')

        # Ensure the CSV has exactly 3 columns
        if df.shape[1] != 3:
            return jsonify({'error': 'CSV must have exactly 3 columns'}), 400

        # Convert DataFrame to list of dictionaries
        data = df.to_dict(orient='records')

        # Insert the data into MongoDB
        result = rules.insert_many(data)

        return jsonify({
            'message': 'Data uploaded successfully!',
            'inserted_ids': str(result.inserted_ids)
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@blood_analysis_rules.route('/rules', methods=['GET'])
@jwt_required()
def get_all_rules():
    rules = current_app.db.blood_analysis_rules
    rules = list(rules.find())
    for rule in rules:
        rule['_id'] = str(rule['_id'])

    return jsonify(rules), 200


@blood_analysis_rules.route('/rules/<rule_id>', methods=['GET'])
@jwt_required()
def get_single_rules(rule_id):
    rules = current_app.db.blood_analysis_rules
    rule = rules.find_one({'_id': ObjectId(rule_id)})

    if rule is None:
        return jsonify({'error': f'Rule with ID {rule_id} not found.'}), 404

    return jsonify(rule), 200


@blood_analysis_rules.route('/rules/<rule_id>', methods=['PUT'])
def update_rule(rule_id):
    rules = current_app.db.blood_analysis_rules
    rule_data = request.json  # Get the rule data from the request body
    result = rules.replace_one({'_id': ObjectId(rule_id)}, rule_data)

    if result.matched_count > 0:
        return jsonify({'message': f'Rule with ID {rule_id} updated successfully'}), 200
    else:
        return jsonify({'error': f'Rule with ID {rule_id} not found'}), 404


@blood_analysis_rules.route('/rules', methods=['POST'])
def insert_rules():
    rules = current_app.db.blood_analysis_rules
    requested_rules = request.json.get('rules', [])  # Get the list of rules from the request body
    inserted_rule_ids = []

    for rule in requested_rules:
        result = rules.insert_one(rule)
        inserted_rule_ids.append(str(result.inserted_id))

    return jsonify({'message': 'Rules inserted successfully', 'inserted_rule_ids': inserted_rule_ids}), 201


@blood_analysis_rules.route('/rules/<rule_id>', methods=['DELETE'])
def delete_rule(rule_id):
    try:
        rules = current_app.db.blood_analysis_rules
        result = rules.delete_one({'_id': ObjectId(rule_id)})
        if result.deleted_count > 0:
            return jsonify({'message': f'Rule with ID {rule_id} deleted successfully'}), 200
        else:
            return jsonify({'error': f'Rule with ID {rule_id} not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400

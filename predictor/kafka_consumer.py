import json
from flask import current_app, Blueprint, jsonify
from kafka import KafkaConsumer
from bson.objectid import ObjectId
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

kafka_consumer = Blueprint('kafka_consumer', __name__)

consumer = KafkaConsumer(
    'microservice-topic',  # Replace with your Kafka topic name
    bootstrap_servers='localhost:9092',  # Kafka broker address
    auto_offset_reset='latest',  # Start reading at the earliest message
    enable_auto_commit=True,
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))  # Decode the message as a UTF-8 string
)


@kafka_consumer.route('/consume', methods=['GET'])
@jwt_required()
def consume_kafka():
    current_app.logger.info("Hello")
    laboratory_reports = current_app.db.laboratory_reports

    for message in consumer:
        data = message.value
        current_app.logger.info(f"Message: {data}")
        object_id = ObjectId(data['report_id']['$oid'])
        current_app.logger.info(object_id)
        conditions = predict_condition(data['values_out_of_range'])
        laboratory_reports.update_one({"_id": object_id},
                                      {'$set': {'associated_condition': conditions}})
        break

    return jsonify({'message': f'{condition_to_string(conditions)}'}), 200


def condition_to_string(conditions):
    if not conditions:
        return "No associated conditions found for the given report."

    messages = []

    for condition in conditions:
        blood_parameter = condition.get('Blood Parameter', 'Unknown parameter')
        status = condition.get('Status', 'Unknown status')
        associated_condition = condition.get('Associated Condition', 'Unknown condition')

        if associated_condition == 'doctor check':
            message = f" For the blood parameter {blood_parameter} with {status}ER values than allowed, " \
                      f"you should consult your doctor as this case is not in our database;"
        else:
            # Construct the individual condition message
            message = f" The blood parameter {blood_parameter} with {status}ER values " \
                      f"than allowed indicates {associated_condition};"
        messages.append(message)

    # Join all messages for the final report message
    final_message = "Given report indicates the following conditions: " + "\n".join(messages)

    return final_message


def predict_condition(values):
    rules = current_app.db.blood_analysis_rules
    potential_problems = []
    for value in values:
        name = value['analysis']
        status = value['status']

        # Search for a rule with the given name and status
        rule = rules.find_one({
            'Blood Parameter': name,
            'Status': status
        })

        if rule:
            potential_problems.append({
                "Blood Parameter": value["analysis"],
                "Status": value["status"],
                "Associated Condition": rule['Associated Condition']
            })
        else:
            potential_problems.append({
                "Blood Parameter": value["analysis"],
                "Status": value["status"],
                "Associated Condition": "doctor check"
            })

    return potential_problems


@kafka_consumer.route('/predict_associated_condition/<string:report_id>', methods=['GET'])
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

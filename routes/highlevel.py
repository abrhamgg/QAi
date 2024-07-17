from flask import Blueprint, request, jsonify
from services.highlevel_service import HighlevelService
from flask_login import login_required, current_user

highlevel_bp = Blueprint('highlevel', __name__)


@highlevel_bp.route('/highlevel/customValues', methods=['GET'])
@login_required
def get_custom_values():
    token = current_user.token
    location_id = current_user.location_id
    highlevel_service = HighlevelService(token=token, location_id=location_id)
    custom_values = highlevel_service.get_customValue()
    return jsonify(custom_values)


@highlevel_bp.route('/highlevel/customValues/<custom_value_id>', methods=['PUT'])
@login_required
def update_custom_value(custom_value_id):
    token = current_user.token
    location_id = current_user.location_id
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    highlevel_service = HighlevelService(token=token, location_id=location_id)
    highlevel_service.update_custom_value(data, custom_value_id)
    return jsonify({'message': 'Custom value updated'})


@highlevel_bp.route('/highlevel', methods=['GET'])
@login_required
def get_custom_fields():
    token = current_user.token
    location_id = current_user.location_id
    try:
        highlevel_service = HighlevelService(
            token=token, location_id=location_id)

        custom_fields = highlevel_service.get_custom_fields()
        return jsonify(custom_fields)
    except Exception as e:
        print(e)
        return jsonify({'error': 'No custom fields found'}), 404


@highlevel_bp.route('/highlevel/contact/<contact_id>', methods=['GET'])
@login_required
def get_contact_by_id(contact_id):
    if not contact_id:
        return jsonify({'error': 'No contact_id provided'}), 400
    token = current_user.token
    location_id = current_user.location_id
    highlevel_service = HighlevelService(token=token, location_id=location_id)
    contact = highlevel_service.get_contact_by_id(contact_id)
    return jsonify(contact)


@highlevel_bp.route('/highlevel/custom-field/<field_id>', methods=['GET'])
@login_required
def get_custom_field_by_id(field_id):
    if not field_id:
        return jsonify({'error': 'No field_id provided'}), 400

    try:
        token = current_user.token
        location_id = current_user.location_id
        highlevel_service = HighlevelService(
            token=token, location_id=location_id)
        custom_field = highlevel_service.get_custom_field_by_id(field_id)
        if not custom_field:
            return jsonify({'error': 'No custom field found'}), 404
        return jsonify(custom_field)
    except:
        return jsonify({'error': 'No custom field found'}), 404

# Update the custom field


@highlevel_bp.route('/highlevel/contact/<contact_id>/custom-fields', methods=['PUT'])
@login_required
def update_custom_fields_by_name(contact_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No id or value provided'}), 400
    token = current_user.token
    location_id = current_user.location_id
    highlevel_service = HighlevelService(token=token, location_id=location_id)
    response = highlevel_service.update_custom_fields_by_id(
        contact_id, data)
    return jsonify(response)

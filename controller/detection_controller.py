import os
from flask import Blueprint, request, jsonify, current_app 
from werkzeug.utils import secure_filename 
from werkzeug.security import generate_password_hash
from models.db import db
from services.detection_service import detect_image_type 
from controller.auth.auth_middleware import token_required
from models.user_model import User
from models.detection import Detection
from datetime import datetime
from sqlalchemy import select 
from sqlalchemy.orm import joinedload, selectinload 

detection_bp = Blueprint('detection_bp', __name__, url_prefix='/detections')

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png','jpg','jpeg','gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# GET — List all organization users
@detection_bp.route('/organizations', methods=['GET'])
def get_organizations(): #Return all registered organization users with their details.
    organizations = User.query.filter_by(role="organization").all()
    org_data = []
    for org in organizations:
        org_data.append({
            "id": org.id,
            "name": org.name,
            "email": org.email,
            "organization_name": org.organization_name,
            "created_at": org.created_at.strftime("%Y-%m-%d %H:%M:%S") if org.created_at else None
        })
    
    return jsonify({
        "message": "Organization users registered",
        "count": len(org_data),
        "organizations": org_data
    }), 200

# POST — Detect and Save
@detection_bp.route('/create', methods=['POST'])
@token_required
def create_detection(current_user):
    # Organization cannot create detections
    if current_user.role == "organization":
        return jsonify({"error": "Organizations cannot upload detections"}), 403
    
    image = request.files.get('image')
    lat = request.form.get('latitude')
    lon = request.form.get('longitude')
    location = request.form.get('location')
    
    if not image or not lat or not lon or not location:
        return jsonify({'error': 'Missing required fields (image, latitude, longitude, or location)'}), 400
    
    if image.filename == '':
        return jsonify({'error': 'No file selected for upload'}), 400
        
    if not allowed_file(image.filename):
        return jsonify({'error': 'Image file type not allowed'}), 400
        
    try:
        latitude = float(lat)
        longitude = float(lon)
    except ValueError:
        return jsonify({'error': 'Invalid latitude/longitude'}), 400

    # --- Detect and save detection inside detect_image_type ---
    detection_type, result_data, image_name, actual_image_path, detection_record = detect_image_type(
        image, current_user.id, latitude, longitude, location
    ) 
    
    if detection_type is None:
        return jsonify({'message': 'No pothole or waste detected, file discarded.'}), 200
    
    if not detection_record:
        return jsonify({'error': 'Detection saved in service but failed to retrieve record.'}), 500

    #response
    result_data.update({
        "id": detection_record.id,
        "user": {
            "id": current_user.id,
            "name": getattr(current_user, 'name', None),
            "email": current_user.email,
            "role": getattr(current_user, 'role', None),
        },
        "organization_id": detection_record.organization_id,
        "organization_name": detection_record.organization.organization_name if detection_record.organization else "Not Assigned",
        "department": detection_record.department
    })

    return jsonify({
        'message': f'{detection_type.capitalize()} detected successfully.',
        'data': result_data
    }), 201


#    # --- Dynamic organization assignment based on detection type ---
#     def assign_organization(detection_type):
#         mapping = {
#             "pothole": "Department of Roads",
#             "waste": "Department of Sanitation"
       
#         }
#         org_name = mapping.get(detection_type)
#         if org_name:
#             organization = User.query.filter_by(role="organization", name=org_name).first()
#             if organization:
#                 return organization.id
#         return None

#     organization_id = assign_organization(detection_type)
    

    

# GET — All detections (current user detections only)ani tespaxi organization le afulai assigned vako detections herne
@detection_bp.route('/my', methods=['GET'])
@token_required
def get_my_detections(current_user):

    # If normal user -> show only detections uploaded by them
    if current_user.role == "user":
        detections = Detection.query.filter_by(user_id=current_user.id).order_by(Detection.id.desc()).all()

    # If organization -> show detections assigned to that organization
    elif current_user.role == "organization":
        detections = Detection.query.filter_by(organization_id=current_user.id).order_by(Detection.id.desc()).all()

    else:
        return jsonify({"error": "Invalid role"}), 403
    data = [d.to_dict() for d in detections]

    return jsonify({
        "count": len(data),
        "detections": data
    }), 200


#  GET — All by type(like pthole/waste) for current user
@detection_bp.route('/type/<string:detection_type>', methods=['GET'])
@token_required
def get_my_by_type(current_user, detection_type):
    if detection_type not in ['pothole', 'waste']:
        return jsonify({'error': 'Invalid detection type'}), 400
    records = Detection.query.filter_by(
        user_id=current_user.id, detection_type=detection_type).all()
    return jsonify([r.to_dict() for r in records]), 200


# GET — single detection by id of the image for current user
@detection_bp.route('/my/<int:id>', methods=['GET'])
@token_required
def get_my_single(current_user, id): 
    record = Detection.query.filter_by(user_id=current_user.id, id=id).first_or_404()
    return jsonify(record.to_dict()), 200


#GET= detectins by user using user_id 
@detection_bp.route("/user/<string:user_id>", methods=["GET"])
@token_required
def get_detections_by_user(current_user, user_id): 
    stmt = (
        select(Detection)
        .where(Detection.user_id == user_id)
        .options(joinedload(Detection.user))
        .options(joinedload(Detection.organization))
        .order_by(Detection.timestamp.desc())
    )
    records = db.session.execute(stmt).scalars().all() 
    if not records:
        return jsonify({"message": "No detections found for this user"}), 404
    data = []
    for det in records:
        user = det.user
        org = det.organization         
        det_dict = {
            "id": det.id,
            "detection_type": det.detection_type,
            "image_name": det.image_name,
            "image_path": det.image_path,
            "detected_image_path": det.detected_image_path,
            "latitude": det.latitude,
            "longitude": det.longitude,
            "location": det.location,
            "detection_status": getattr(det, "detection_status", None),
            "area_pct": getattr(det, "area_pct", None),
            "est_depth_m": getattr(det, "est_depth_m", None),
            "department": getattr(det, "department", None),
            "pothole_severity": getattr(det, "pothole_severity", None),
            "waste_category": getattr(det, "waste_category", None),

            # Organization fields
            "organization_id": det.organization_id,
            "organization_name": org.organization_name if org else None,

            #user info
            "user": {
                "id": user.id,
                "name": getattr(user, 'name', None),
                "email": user.email,
                "role": getattr(user, 'role', None),
            }
        }
        data.append(det_dict)

    return jsonify({"detections": data}), 200


# GET — Full user details with detections (admin only)
@detection_bp.route("/user/details/<string:user_id>", methods=["GET"])
@token_required
def get_user_full_details(current_user, user_id):
    if getattr(current_user, "role", "user") != "admin":
        return jsonify({"error": "Unauthorized"}), 403
    user = (
        User.query.options(
            joinedload(User.detections)
            .joinedload(Detection.departments)
            .joinedload("department"),
            joinedload(User.detections)
            .joinedload(Detection.tags)
            .joinedload("tag")
        )
        .filter(User.id == user_id)
        .first()
    )
    if not user:
        return jsonify({"error": "User not found"}), 404
    data = {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "organization_name": user.organization_name,
        "created_at": user.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": user.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
        "detections": []
    }
    for det in user.detections:
        # Here Detection.departments and Detection.tags are relationships
        departments = [dept.department.name for dept in det.departments if hasattr(dept, 'department') and dept.department]
        tags = [tag.tag.name for tag in det.tags if hasattr(tag, 'tag') and tag.tag]
        
        data["detections"].append({
            "id": det.id,
            "detection_type": det.detection_type,
            "image_name": det.image_name,
            "latitude": det.latitude,
            "longitude": det.longitude,
            "location": det.location,
            "timestamp": det.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "detection_status": det.detection_status,
            "departments": departments,
            "tags": tags
        })

    return jsonify(data), 200


#PUT — Update detection location for current user
@detection_bp.route('/my/update/<string:id>', methods=['PUT'])
@token_required
def update_my_detection(current_user, id):
    data = request.json
    new_location = data.get('location')
    if not new_location:
        return jsonify({'error': 'Location is required'}), 400
    record = Detection.query.filter_by(user_id=current_user.id, id=id).first()
    if not record:
        return jsonify({'error': 'Record not found'}), 404
    record.location = new_location
    db.session.commit()
    return jsonify({
        'message': f'{record.detection_type.capitalize()} location updated',
        'data': {
            'id': record.id,
            'detection_type': record.detection_type,
            'image_name': record.image_name,
            'image_path': record.image_path,
            'detected_image_path': record.detected_image_path,
            'latitude': record.latitude,
            'longitude': record.longitude,
            'location': record.location,
            'timestamp': record.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            'detection_status': record.detection_status
        }
    }), 200

# DELETE — Delete detection by id for current user
@detection_bp.route('/my/delete/<string:image_id>', methods=['DELETE'])
@token_required
def delete_my_detection(current_user, id):
    record = Detection.query.filter_by(user_id=current_user.id, id=id).first()
    if not record:
        return jsonify({'error': 'Record not found'}), 404
    
    original_path_to_delete = record.image_path
    annotated_path_to_delete = record.detected_image_path
    
    # to delete original image
    if original_path_to_delete and os.path.exists(original_path_to_delete):
        os.remove(original_path_to_delete)
        
    # to delete annotated image
    if annotated_path_to_delete and os.path.exists(annotated_path_to_delete):
        os.remove(annotated_path_to_delete)
            
    db.session.delete(record)
    db.session.commit()
    return jsonify({'message': f'{record.detection_type.capitalize()} deleted successfully'}), 200


# DELETE — Delete all detections by type for current user
@detection_bp.route('/my/type/<string:id>', methods=['DELETE'])
@token_required
def delete_all_my_by_type(current_user, detection_type):
    if detection_type not in ['pothole', 'waste']:
        return jsonify({'error': 'Invalid detection type'}), 400
        
    records = Detection.query.filter_by(
        user_id=current_user.id, detection_type=detection_type).all()
        
    for record in records:
        original_path_to_delete = record.image_path
        annotated_path_to_delete = record.detected_image_path
        
        # to delete original image
        if original_path_to_delete and os.path.exists(original_path_to_delete):
            os.remove(original_path_to_delete)
        
        # to delete annotated image
        if annotated_path_to_delete and os.path.exists(annotated_path_to_delete):
            os.remove(annotated_path_to_delete)
                
        db.session.delete(record)
        
    db.session.commit()
    return jsonify({
        "message": f"All {detection_type} records deleted successfully.",
        "count": len(records)
    }), 200
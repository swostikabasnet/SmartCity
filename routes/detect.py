from flask import Blueprint, request, jsonify, current_app
import logging
import os
import uuid 
from utils.file_utils import save_upload
from services.inference_service import InferenceService
from model_loader import ModelLoader     

# Initializing ModelLoader and InferenceService 
try:
    model_loader = ModelLoader(
        waste_model_path="runs/detect/waste_yolo_fast/weights/waste.pt",
        pothole_model_path="runs/pothole_yolov8/weights/best.pt"
    )
    inference_service = InferenceService(model_loader)
except Exception as e:
   
    logging.error(f"Failed to initialize ModelLoader: {e}")
    inference_service = None 

logger = logging.getLogger(__name__)
detect_bp = Blueprint("detect", __name__)


@detect_bp.route("/detect", methods=["POST"])
def detect():
    data = {}
    if request.form:
        data.update(request.form)
    
    json_data = request.get_json(silent=True)
    if json_data:
        data.update(json_data)

    #Input Extraction and Validation
    default_user_id = current_app.config.get("DEFAULT_USER_ID", str(uuid.uuid4()))
    user_id = data.get("user_id", default_user_id)
    task_type = data.get("task_type", "waste")
    
    image = request.files.get("image")
    image_path = data.get("image_path")
    saved_path = None

    if inference_service is None:
        return jsonify({"success": False, "error": "ML services failed to load at startup."}), 503

    try:
        if image:
            # Case 1: User uploaded image
            saved_path = save_upload(image)
        elif image_path:
            # Case 2: Image path already on server
            if not os.path.exists(image_path):
                return jsonify({"success": False, "error": "File not found on server"}), 404
            saved_path = image_path
        else:
            # Case 3: Nothing provided
            return jsonify({"success": False, "error": "No image file or path provided"}), 400

        # Run Inference
        result = inference_service.run(
            image_path=saved_path,
            user_id=user_id,
            task_type=task_type
        )

        # Check for inference success
        if not result.get("success"):
             return jsonify({
                "success": False, 
                "error": "Inference service failed", 
                "details": result.get("error", "Unknown inference error")
            }), 500

        # Success Response
        return jsonify({
            "success": True,
            "detection_type": result.get("task_type"),
            "result": result
        }), 200

    except Exception as e:
        logger.exception("Detection API error")
        return jsonify({"success": False, "error": str(e)}), 500
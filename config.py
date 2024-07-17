import secrets


app_secret_key = "my_secret_key"
# app_secret_key = secrets.token_hex(16)

face_detection_onnx_model_path = "models/det_10g.onnx"
age_gender_estimation_onnx_model_path = "models/genderage.onnx"
object_detection_onnx_model_path = "models/yolov8n.onnx"

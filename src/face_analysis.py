import argparse
import cv2
from src.face_detection import RetinaFace
from src.age_gender_estimation import AgeGenderEstimator


class FaceAnalysis:
    def __init__(self, face_detection_onnx_model_path, age_gender_estimation_onnx_model_path):
        self.face_detection_model = RetinaFace(face_detection_onnx_model_path)
        self.age_gender_estimation_model = AgeGenderEstimator(age_gender_estimation_onnx_model_path)

    def postprocess(self, image):
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return image

    def __call__(self, input_image):
        faces = self.face_detection_model(input_image)
        genders = []
        ages = []
        output_image = input_image.copy()
        for face in faces:
            bbox = face.bbox.astype(int)
            gender, age = self.age_gender_estimation_model(input_image, face)
            genders.append(gender)
            ages.append(age)
            # Draw bounding box and labels on the image
            cv2.rectangle(output_image, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 2)
            label = f"Gender: {'Male' if gender == 1 else 'Female'}, Age: {int(age)}"
            cv2.putText(
                output_image,
                label,
                (bbox[0], bbox[1] - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (36, 255, 12),
                2,
            )
        
        output_image = self.postprocess(output_image)
        return output_image, genders, ages


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--image", type=str, required=True ,help="Input image path",
    )
    parser.add_argument(
        "--face-detection-model", type=str, default="models/det_10g.onnx", help="ONNX model path"
    )
    parser.add_argument(
        "--age-gender-estimation-model", type=str, default="models/genderage.onnx", help="ONNX model path"
    )
    args = parser.parse_args()

    input_image = cv2.imread(args.image)
    if input_image is not None:
        face_analysis = FaceAnalysis(args.face_detection_model, args.age_gender_estimation_model)
        output_image, genders, ages = face_analysis(input_image)
        cv2.imshow("Age and Gender Detection", output_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    else:
        print("Could not read image:", args.image)

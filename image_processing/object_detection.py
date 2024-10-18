from ultralytics import YOLO
import cv2
import logging

class ObjectDetector:
    def __init__(self, model_path):
        self.model = YOLO(model_path)

    def detect_objects(self, image_path, user_settings):
        try:
            image = cv2.imread(image_path)
            results = self.model(image)
            
            detections = {
                'person': [],
                'vehicle': [],
                'animal': []
            }
            
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    class_name = self.model.names[cls]
                    
                    if class_name == 'person' and user_settings['ENABLE_PERSON_DETECTION'] and conf > user_settings['PERSON_CONFIDENCE_THRESHOLD']:
                        detections['person'].append((box.xyxy[0].tolist(), conf))
                    elif class_name in ['car', 'truck', 'bus', 'vehicle'] and user_settings['ENABLE_VEHICLE_DETECTION'] and conf > user_settings['VEHICLE_CONFIDENCE_THRESHOLD']:
                        detections['vehicle'].append((box.xyxy[0].tolist(), conf))
                    elif class_name in ['cow', 'sheep', 'horse', 'dog', 'cat', 'animal'] and user_settings['ENABLE_ANIMAL_DETECTION'] and conf > user_settings['ANIMAL_CONFIDENCE_THRESHOLD']:
                        detections['animal'].append((box.xyxy[0].tolist(), conf))
            
            return detections, image
        except Exception as e:
            logging.error(f"Error during object detection: {str(e)}")
            return None, None
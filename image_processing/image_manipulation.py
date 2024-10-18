import cv2
from datetime import datetime

def add_watermark(image, user_settings):
    height, width = image.shape[:2]
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1
    font_thickness = 2
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    watermark_text = user_settings.get('WATERMARK_TEXT', GLOBAL_WATERMARK_TEXT)
    watermark_text = watermark_text.format(username=user_settings['FTP_USER'], timestamp=timestamp)
    
    text_size = cv2.getTextSize(watermark_text, font, font_scale, font_thickness)[0]
    
    position = (width - text_size[0] - 10, height - 10)
    
    overlay = image.copy()
    cv2.rectangle(overlay, (position[0] - 5, position[1] - text_size[1] - 5),
                  (width, height), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.5, image, 0.5, 0, image)
    
    cv2.putText(image, watermark_text, position, font, font_scale, (255, 255, 255), font_thickness)
    
    return image

def draw_detections(image, detections):
    for category, objects in detections.items():
        for (bbox, conf) in objects:
            x1, y1, x2, y2 = map(int, bbox)
            if category == 'person':
                color = (0, 255, 0)  # Green for persons
            elif category == 'vehicle':
                color = (255, 0, 0)  # Blue for vehicles
            else:
                color = (0, 0, 255)  # Red for animals
            
            cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
            cv2.putText(image, f"{category} {conf:.2f}", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
    
    return image
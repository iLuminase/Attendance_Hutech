import cv2
import numpy as np
from typing import Optional, Tuple, List, Dict
import base64
import io
from PIL import Image
import os

class SimpleFaceService:
    def __init__(self):
        # Load Haar cascade for face detection - but don't fail if not available
        try:
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            if not self.face_cascade.empty():
                print("✅ Face detection models loaded")
            else:
                raise Exception("Cascade classifier is empty")
        except Exception as e:
            print(f"⚠️  Warning: Face detection unavailable: {e}")
            self.face_cascade = None
        
    def preprocess_image(self, image_bytes: bytes) -> Optional[np.ndarray]:
        """Tiền xử lý ảnh để tối ưu hóa tốc độ"""
        try:
            # Convert bytes to numpy array
            np_img = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
            
            if img is None:
                return None
                
            # Resize image if too large (for speed)
            height, width = img.shape[:2]
            if width > 800:
                scale = 800 / width
                new_width = 800
                new_height = int(height * scale)
                img = cv2.resize(img, (new_width, new_height))
                
            return img
            
        except Exception:
            return None
    
    def detect_faces(self, img: np.ndarray) -> List[Dict]:
        """Phát hiện khuôn mặt nhanh"""
        if self.face_cascade is None:
            return []
            
        try:
            # Convert to grayscale for detection
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Try multiple detection passes with different parameters for better coverage
            faces = []
            
            # First pass: standard detection
            faces1 = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=3,
                minSize=(30, 30),
                maxSize=(600, 600)
            )
            faces.extend(faces1)
            
            # Second pass: more relaxed detection if no faces found
            if len(faces) == 0:
                faces2 = self.face_cascade.detectMultiScale(
                    gray,
                    scaleFactor=1.05,
                    minNeighbors=2,
                    minSize=(20, 20),
                    maxSize=(800, 800)
                )
                faces.extend(faces2)
            
            # Third pass: very relaxed if still no faces
            if len(faces) == 0:
                faces3 = self.face_cascade.detectMultiScale(
                    gray,
                    scaleFactor=1.03,
                    minNeighbors=1,
                    minSize=(15, 15),
                    maxSize=(1000, 1000),
                    flags=cv2.CASCADE_SCALE_IMAGE
                )
                faces.extend(faces3)
            
            # Convert to numpy array for processing
            if len(faces) > 0:
                faces = np.array(faces)
            
            # If still no faces found, use fallback method
            if len(faces) == 0:
                faces = self._fallback_face_detection(gray)
            
            face_list = []
            for i, (x, y, w, h) in enumerate(faces):
                # Add margin around face
                margin = int(w * 0.1)
                x1 = max(0, x - margin)
                y1 = max(0, y - margin)
                x2 = min(img.shape[1], x + w + margin)
                y2 = min(img.shape[0], y + h + margin)
                
                face_list.append({
                    'id': int(i),
                    'x': int(x1),
                    'y': int(y1),
                    'w': int(x2 - x1),
                    'h': int(y2 - y1),
                    'confidence': float(0.7)  # Lower confidence for fallback
                })
                
            return face_list
            
        except Exception:
            return []
    
    def _fallback_face_detection(self, gray: np.ndarray) -> List:
        """Phương pháp dự phòng: tìm vùng có thể là khuôn mặt dựa trên gradient"""
        try:
            # Use edge detection to find face-like regions
            edges = cv2.Canny(gray, 50, 150)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            faces = []
            for contour in contours:
                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(contour)
                
                # Filter by aspect ratio and size (face-like criteria)
                aspect_ratio = w / h if h > 0 else 0
                area = w * h
                
                if (0.6 <= aspect_ratio <= 1.4 and  # Face-like aspect ratio
                    area > 1000 and  # Minimum size
                    w > 30 and h > 30):  # Minimum dimensions
                    
                    faces.append([int(x), int(y), int(w), int(h)])
                    
            # Limit to first 3 detections
            return faces[:3]
            
        except Exception:
            # Last resort: return center region of image
            h, w = gray.shape
            if h > 100 and w > 100:
                center_x = w // 2
                center_y = h // 2
                face_size = min(h, w) // 3
                return [[int(center_x - face_size//2), int(center_y - face_size//2), int(face_size), int(face_size)]]
            return []
    
    def extract_face_encoding(self, img: np.ndarray, face_box: Dict) -> Optional[np.ndarray]:
        """Trích xuất đặc trưng khuôn mặt nhanh"""
        try:
            x, y, w, h = face_box['x'], face_box['y'], face_box['w'], face_box['h']
            
            # Extract face region
            face_roi = img[y:y+h, x:x+w]
            if face_roi.size == 0:
                return None
                
            # Convert to grayscale
            face_gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
            
            # Resize to standard size (smaller for speed)
            face_resized = cv2.resize(face_gray, (32, 32))  # Even smaller for speed
            
            # Simple feature extraction - just flatten the resized image
            features = face_resized.flatten().astype(np.float32)
            
            # Normalize
            features = features / 255.0
            
            return features
            
        except Exception:
            return None
    
    def compare_faces(self, encoding1: np.ndarray, encoding2: np.ndarray, threshold: float = 0.8) -> Tuple[bool, float]:
        """So sánh khuôn mặt nhanh"""
        try:
            if encoding1 is None or encoding2 is None:
                return False, 0.0
                
            if len(encoding1) != len(encoding2):
                return False, 0.0
            
            # Calculate simple correlation
            correlation = np.corrcoef(encoding1, encoding2)[0, 1]
            if np.isnan(correlation):
                correlation = 0.0
            
            # Convert to similarity score (0-1)
            similarity = abs(correlation)
            
            is_match = similarity >= threshold
            return is_match, float(similarity)
            
        except Exception:
            return False, 0.0
    
    def draw_face_boxes(self, img: np.ndarray, faces: List[Dict], student_info: List[Dict] = None) -> np.ndarray:
        """Vẽ khung nhận diện khuôn mặt trên ảnh"""
        result_img = img.copy()
        
        for i, face in enumerate(faces):
            x, y, w, h = face['x'], face['y'], face['w'], face['h']
            
            # Determine color and label
            if student_info and i < len(student_info) and student_info[i]:
                # Recognized student - green box
                color = (0, 255, 0)
                student = student_info[i]
                label = f"{student['name']} ({student.get('similarity', 0):.2f})"
            else:
                # Unknown face - red box
                color = (0, 0, 255)
                label = "Unknown"
            
            # Draw rectangle
            cv2.rectangle(result_img, (x, y), (x + w, y + h), color, 2)
            
            # Draw label background
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            cv2.rectangle(result_img, (x, y - 25), (x + label_size[0], y), color, -1)
            
            # Draw label text
            cv2.putText(result_img, label, (x, y - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return result_img

# Global instance
try:
    face_service = SimpleFaceService()
    print("✅ Face recognition service initialized")
except Exception as e:
    print(f"❌ Face service initialization failed: {e}")
    face_service = None

# Compatibility functions for existing code
def extract_face_encoding(image_bytes: bytes) -> Optional[np.ndarray]:
    """Wrapper function for compatibility"""
    if face_service is None:
        return None
        
    try:
        img = face_service.preprocess_image(image_bytes)
        if img is None:
            return None
            
        faces = face_service.detect_faces(img)
        if not faces:
            return None
            
        return face_service.extract_face_encoding(img, faces[0])
    except Exception as e:
        return None

def compare_faces(encoding1: np.ndarray, encoding2: np.ndarray, threshold: float = 0.8) -> Tuple[bool, float]:
    """Wrapper function for compatibility"""
    if face_service is None:
        return False, 0.0
    return face_service.compare_faces(encoding1, encoding2, threshold)

def detect_faces_in_image(image_bytes: bytes) -> Tuple[List[Dict], np.ndarray]:
    """Phát hiện khuôn mặt và trả về cả danh sách và ảnh"""
    if face_service is None:
        return [], None
        
    try:
        img = face_service.preprocess_image(image_bytes)
        if img is None:
            return [], None
            
        faces = face_service.detect_faces(img)
        return faces, img
    except Exception as e:
        print(f"Error in detect_faces_in_image: {e}")
        return [], None
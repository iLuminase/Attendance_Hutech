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
        """Phát hiện khuôn mặt với khả năng nhận diện đeo kính tốt hơn"""
        if self.face_cascade is None:
            return []
            
        try:
            # Convert to grayscale for detection
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Improve contrast and reduce reflection from glasses
            # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
            gray = clahe.apply(gray)
            
            # Apply Gaussian blur to reduce noise from glass reflection
            gray = cv2.GaussianBlur(gray, (3, 3), 0)
            
            # Strict face detection to avoid false positives
            faces = []
            
            # Single pass with conservative parameters to reduce false positives
            faces1 = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,   # Standard scale factor
                minNeighbors=5,    # Higher neighbors to reduce false positives
                minSize=(40, 40),  # Larger minimum size
                maxSize=(400, 400), # Reasonable maximum size
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            
            # Filter faces by quality metrics
            filtered_faces = []
            for (x, y, w, h) in faces1:
                # Quality check: aspect ratio should be face-like
                aspect_ratio = w / h if h > 0 else 0
                if 0.7 <= aspect_ratio <= 1.3:  # More strict face ratio
                    
                    # Quality check: face region shouldn't be too uniform or too noisy
                    face_roi = gray[y:y+h, x:x+w]
                    if face_roi.size > 0:
                        std_dev = np.std(face_roi)
                        if 15 < std_dev < 70:  # Good contrast range
                            filtered_faces.append([x, y, w, h])
            
            faces = filtered_faces
            
            # Only try fallback if no good faces found
            if len(faces) == 0:
                # More conservative fallback with glasses preprocessing
                gray_blur = cv2.bilateralFilter(gray, 9, 75, 75)
                
                faces2 = self.face_cascade.detectMultiScale(
                    gray_blur,
                    scaleFactor=1.08,
                    minNeighbors=4,    # Still conservative
                    minSize=(35, 35),
                    maxSize=(500, 500),
                    flags=cv2.CASCADE_SCALE_IMAGE
                )
                
                # Apply same filtering
                for (x, y, w, h) in faces2:
                    aspect_ratio = w / h if h > 0 else 0
                    if 0.7 <= aspect_ratio <= 1.3:
                        face_roi = gray_blur[y:y+h, x:x+w] 
                        if face_roi.size > 0:
                            std_dev = np.std(face_roi)
                            if 15 < std_dev < 70:
                                faces.append([x, y, w, h])
            
            # Convert to numpy array for processing
            if len(faces) > 0:
                faces = np.array(faces)
            
            # If still no faces found, use fallback method
            if len(faces) == 0:
                faces = self._fallback_face_detection(gray)
            
            # Remove overlapping faces (Non-Maximum Suppression)
            if len(faces) > 1:
                faces = self._remove_overlapping_faces(faces)
            
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
        """Conservative fallback detection - only when really needed"""
        try:
            # More conservative edge detection
            edges = cv2.Canny(gray, 80, 200)
            
            # Apply morphology to clean up edges
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            faces = []
            for contour in contours:
                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(contour)
                
                # Much stricter criteria
                aspect_ratio = w / h if h > 0 else 0
                area = w * h
                
                if (0.75 <= aspect_ratio <= 1.25 and  # Stricter face ratio
                    area > 2500 and  # Much larger minimum size
                    w > 50 and h > 50 and  # Larger minimum dimensions
                    area < gray.shape[0] * gray.shape[1] * 0.3):  # Not too large
                    
                    # Additional quality check
                    roi = gray[y:y+h, x:x+w]
                    if roi.size > 0:
                        std_dev = np.std(roi)
                        if 20 < std_dev < 60:  # Good contrast
                            faces.append([int(x), int(y), int(w), int(h)])
                    
            # Only return the best candidate (largest)
            if faces:
                faces.sort(key=lambda f: f[2] * f[3], reverse=True)
                return faces[:1]  # Only return 1 best face
            
            return []  # No fallback to center region - too unreliable
            
        except Exception:
            return []
    
    def _remove_overlapping_faces(self, faces: List) -> List:
        """Remove overlapping face detections using Non-Maximum Suppression"""
        if len(faces) <= 1:
            return faces
            
        # Convert to numpy array for easier processing
        faces_array = np.array(faces)
        
        # Calculate areas
        areas = faces_array[:, 2] * faces_array[:, 3]
        
        # Sort by area (largest first)
        indices = np.argsort(areas)[::-1]
        
        keep = []
        for i in indices:
            x1, y1, w1, h1 = faces_array[i]
            
            # Check overlap with already selected faces
            overlap = False
            for j in keep:
                x2, y2, w2, h2 = faces_array[j]
                
                # Calculate intersection
                ix1 = max(x1, x2)
                iy1 = max(y1, y2)
                ix2 = min(x1 + w1, x2 + w2)
                iy2 = min(y1 + h1, y2 + h2)
                
                if ix1 < ix2 and iy1 < iy2:
                    intersection = (ix2 - ix1) * (iy2 - iy1)
                    union = w1 * h1 + w2 * h2 - intersection
                    iou = intersection / union if union > 0 else 0
                    
                    if iou > 0.3:  # 30% overlap threshold
                        overlap = True
                        break
            
            if not overlap:
                keep.append(i)
                
        return [faces[i] for i in keep]
    
    def _preprocess_for_glasses(self, gray: np.ndarray) -> np.ndarray:
        """Preprocessing chuyên biệt cho khuôn mặt đeo kính"""
        # Remove glasses reflection using morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        
        # Close small gaps and holes (like in glasses frames)
        closed = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
        
        # Reduce bright spots (glass reflection)
        # Find bright areas and tone them down
        bright_mask = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)[1]
        bright_areas = cv2.dilate(bright_mask, kernel, iterations=1)
        
        # Replace bright spots with surrounding area average
        result = gray.copy()
        result[bright_areas == 255] = cv2.blur(gray, (5, 5))[bright_areas == 255]
        
        return result
    
    def extract_face_encoding(self, img: np.ndarray, face_box: Dict) -> Optional[np.ndarray]:
        """Trích xuất đặc trưng khuôn mặt với khả năng xử lý kính tốt hơn"""
        try:
            x, y, w, h = face_box['x'], face_box['y'], face_box['w'], face_box['h']
            
            # Extract face region
            face_roi = img[y:y+h, x:x+w]
            if face_roi.size == 0:
                return None
                
            # Convert to grayscale
            face_gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
            
            # Apply glasses-specific preprocessing
            face_gray = self._preprocess_for_glasses(face_gray)
            
            # Apply CLAHE to improve contrast (especially around eyes with glasses)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4,4))
            face_gray = clahe.apply(face_gray)
            
            # Resize to standard size 
            face_resized = cv2.resize(face_gray, (64, 64))  # Larger size for better glasses details
            
            # Extract multiple types of features for robustness
            # 1. Raw pixel features
            pixel_features = face_resized.flatten().astype(np.float32)
            
            # 2. LBP (Local Binary Pattern) features - robust to glasses
            lbp = self._extract_lbp_features(face_resized)
            
            # 3. HOG features for structural information
            hog = self._extract_hog_features(face_resized)
            
            # Combine all features
            features = np.concatenate([pixel_features, lbp, hog])
            
            # Normalize
            features = features / (np.linalg.norm(features) + 1e-7)
            
            return features
            
        except Exception:
            return None
    
    def _extract_lbp_features(self, img: np.ndarray) -> np.ndarray:
        """Trích xuất LBP features - robust với kính"""
        try:
            # Simple LBP implementation
            lbp = np.zeros_like(img)
            for i in range(1, img.shape[0]-1):
                for j in range(1, img.shape[1]-1):
                    center = img[i,j]
                    binary_string = ''
                    # 8 neighbors
                    neighbors = [img[i-1,j-1], img[i-1,j], img[i-1,j+1],
                                img[i,j+1], img[i+1,j+1], img[i+1,j], 
                                img[i+1,j-1], img[i,j-1]]
                    for neighbor in neighbors:
                        binary_string += '1' if neighbor >= center else '0'
                    lbp[i,j] = int(binary_string, 2)
            
            # Create histogram of LBP values
            hist, _ = np.histogram(lbp, bins=32, range=(0, 255))
            return hist.astype(np.float32)
        except:
            return np.zeros(32, dtype=np.float32)
    
    def _extract_hog_features(self, img: np.ndarray) -> np.ndarray:
        """Trích xuất HOG features đơn giản"""
        try:
            # Simple gradient-based features
            grad_x = cv2.Sobel(img, cv2.CV_64F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(img, cv2.CV_64F, 0, 1, ksize=3)
            
            # Magnitude and direction
            magnitude = np.sqrt(grad_x**2 + grad_y**2)
            
            # Create histogram of gradient magnitudes
            hist, _ = np.histogram(magnitude, bins=16, range=(0, 255))
            return hist.astype(np.float32)
        except:
            return np.zeros(16, dtype=np.float32)

    def compare_faces(self, encoding1: np.ndarray, encoding2: np.ndarray, threshold: float = 0.7) -> Tuple[bool, float]:
        """So sánh khuôn mặt với threshold thấp hơn cho kính"""
        try:
            if encoding1 is None or encoding2 is None:
                return False, 0.0
                
            if len(encoding1) != len(encoding2):
                return False, 0.0
            
            # Multiple similarity metrics for robustness with glasses
            # 1. Cosine similarity
            cosine_sim = np.dot(encoding1, encoding2) / (np.linalg.norm(encoding1) * np.linalg.norm(encoding2) + 1e-7)
            
            # 2. Correlation
            correlation = np.corrcoef(encoding1, encoding2)[0, 1]
            if np.isnan(correlation):
                correlation = 0.0
            
            # 3. Euclidean distance (inverted)
            euclidean_dist = np.linalg.norm(encoding1 - encoding2)
            euclidean_sim = 1 / (1 + euclidean_dist)
            
            # Combine similarities with weights
            similarity = (0.5 * abs(cosine_sim) + 0.3 * abs(correlation) + 0.2 * euclidean_sim)
            
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

def compare_faces(encoding1: np.ndarray, encoding2: np.ndarray, threshold: float = 0.7) -> Tuple[bool, float]:
    """Wrapper function for compatibility - lowered threshold for glasses"""
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
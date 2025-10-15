"""
Computer Vision Detection Service
Detects plumbing fixtures and equipment in drawings
"""
import cv2
import numpy as np
from config import Config

def detect_plumbing_symbols(img):
    """
    Detect plumbing fixtures using computer vision
    
    Args:
        img: OpenCV image (BGR format)
    
    Returns:
        list: Detected items with coordinates, type, and confidence
    
    Detection methods:
    - Hough Circle Detection for circular fixtures (toilets, sinks, drains)
    - Contour detection for rectangular equipment (water heaters, tanks)
    """
    detected = []
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Detect circular fixtures
    detected.extend(_detect_circular_fixtures(gray))
    
    # Detect rectangular equipment
    detected.extend(_detect_rectangular_equipment(gray))
    
    # Limit results to prevent overload
    return detected[:50]

def _detect_circular_fixtures(gray_img):
    """
    Detect circular plumbing fixtures (toilets, sinks, drains)
    
    Args:
        gray_img: Grayscale image
    
    Returns:
        list: Detected circular fixtures
    """
    detected = []
    
    circles = cv2.HoughCircles(
        gray_img, 
        cv2.HOUGH_GRADIENT, 
        dp=1, 
        minDist=50,
        param1=50, 
        param2=30, 
        minRadius=Config.DETECTION_MIN_RADIUS, 
        maxRadius=Config.DETECTION_MAX_RADIUS
    )
    
    if circles is not None:
        circles = np.uint16(np.around(circles))
        for circle in circles[0, :]:
            x, y, r = circle
            detected.append({
                'type': 'fixture_unknown',
                'x': float(x),
                'y': float(y),
                'width': float(r * 2),
                'height': float(r * 2),
                'confidence': 0.6
            })
    
    return detected

def _detect_rectangular_equipment(gray_img):
    """
    Detect rectangular equipment (water heaters, tanks, panels)
    
    Args:
        gray_img: Grayscale image
    
    Returns:
        list: Detected rectangular equipment
    """
    detected = []
    
    # Edge detection
    edges = cv2.Canny(gray_img, 50, 150)
    
    # Find contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        area = cv2.contourArea(contour)
        
        # Filter by size and aspect ratio
        if 500 < area < 5000 and 0.5 < w/h < 2.0:
            detected.append({
                'type': 'equipment',
                'x': float(x),
                'y': float(y),
                'width': float(w),
                'height': float(h),
                'confidence': 0.5
            })
    
    return detected

def classify_fixture_type(img, x, y, width, height):
    """
    Classify detected fixture into specific type
    
    Args:
        img: Original image
        x, y, width, height: Bounding box of detected item
    
    Returns:
        str: Fixture type (toilet, sink, urinal, etc.)
    
    Note: This is a placeholder. Full implementation would use:
    - Template matching for known symbols
    - Machine learning classifier trained on plumbing symbols
    - Feature extraction (shape, size ratios, context)
    """
    # TODO: Implement classification
    # For now, return generic types based on size
    area = width * height
    
    if area > 2000:
        return 'water_heater'
    elif width / height > 1.5:
        return 'sink'
    else:
        return 'toilet'
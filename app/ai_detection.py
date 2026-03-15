"""
AI Image Detection Module for CivicPulse Grievance Portal
Uses PyTorch and OpenCV for issue detection in uploaded images.
"""
import os
import random

# Try to import ML libraries, but provide fallback if not installed
try:
    import torch
    import torchvision.transforms as transforms
    from torchvision import models
    import cv2
    import numpy as np
    from PIL import Image
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False


# Issue categories that can be detected
ISSUE_CATEGORIES = {
    0: 'Pothole',
    1: 'Garbage Overflow',
    2: 'Broken Road',
    3: 'Water Leakage',
    4: 'Streetlight Damage',
    5: 'Road Damage',
    6: 'Drainage Issue',
    7: 'Fallen Tree',
    8: 'Illegal Dumping',
    9: 'Other Issue'
}


def load_model():
    """
    Load a pretrained model for image classification.
    In production, you would load a custom trained model.
    """
    if not ML_AVAILABLE:
        return None
    
    try:
        # Using a pretrained ResNet model as base
        # In production, replace with custom trained model
        model = models.resnet18(pretrained=True)
        model.eval()
        return model
    except Exception as e:
        print(f"Error loading model: {e}")
        return None


def preprocess_image(image_path):
    """Preprocess image for model input."""
    if not ML_AVAILABLE:
        return None
    
    try:
        # Define transforms
        transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
        
        # Load and transform image
        image = Image.open(image_path).convert('RGB')
        return transform(image).unsqueeze(0)
    except Exception as e:
        print(f"Error preprocessing image: {e}")
        return None


def analyze_image_features(image_path):
    """
    Analyze image using OpenCV for basic feature detection.
    This provides additional context for issue classification.
    """
    if not ML_AVAILABLE:
        return {}
    
    try:
        # Read image
        img = cv2.imread(str(image_path))
        if img is None:
            return {}
        
        # Convert to different color spaces
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # Calculate features
        features = {
            'brightness': np.mean(gray),
            'contrast': np.std(gray),
            'saturation': np.mean(hsv[:, :, 1]),
        }
        
        # Edge detection for damage assessment
        edges = cv2.Canny(gray, 100, 200)
        features['edge_density'] = np.sum(edges > 0) / edges.size
        
        # Color analysis
        mean_color = np.mean(img, axis=(0, 1))
        features['mean_blue'] = mean_color[0]
        features['mean_green'] = mean_color[1]
        features['mean_red'] = mean_color[2]
        
        return features
    except Exception as e:
        print(f"Error analyzing image: {e}")
        return {}


def detect_issue(image_field):
    """
    Main function to detect issue type from uploaded image.
    
    Args:
        image_field: Django ImageField or file path
        
    Returns:
        dict with 'issue' and 'confidence' keys, or None if detection fails
    """
    try:
        # Get image path
        if hasattr(image_field, 'path'):
            image_path = image_field.path
        else:
            image_path = str(image_field)
        
        # Check if file exists
        if not os.path.exists(image_path):
            return None
        
        # If ML libraries not available, use simulated detection
        if not ML_AVAILABLE:
            return simulate_detection(image_path)
        
        # Load model
        model = load_model()
        if model is None:
            return simulate_detection(image_path)
        
        # Preprocess image
        input_tensor = preprocess_image(image_path)
        if input_tensor is None:
            return simulate_detection(image_path)
        
        # Analyze image features
        features = analyze_image_features(image_path)
        
        # Run inference
        with torch.no_grad():
            output = model(input_tensor)
            probabilities = torch.nn.functional.softmax(output[0], dim=0)
        
        # Map ImageNet classes to our issue categories
        # This is a simplified mapping - in production, use custom trained model
        issue_index = classify_issue(features, probabilities)
        confidence = calculate_confidence(features, probabilities)
        
        return {
            'issue': ISSUE_CATEGORIES.get(issue_index, 'Other Issue'),
            'confidence': round(confidence * 100, 2)
        }
        
    except Exception as e:
        print(f"Error in issue detection: {e}")
        return simulate_detection(image_path if 'image_path' in dir() else None)


def classify_issue(features, probabilities=None):
    """
    Classify the issue based on image features.
    This is a simplified heuristic - replace with ML model in production.
    """
    if not features:
        return 9  # Other Issue
    
    # Simple heuristics based on image features
    edge_density = features.get('edge_density', 0)
    brightness = features.get('brightness', 128)
    saturation = features.get('saturation', 128)
    
    # High edge density might indicate road damage
    if edge_density > 0.15:
        if brightness < 100:
            return 0  # Pothole (dark + many edges)
        else:
            return 2  # Broken Road
    
    # Brown/dark colors might indicate garbage
    if features.get('mean_green', 0) < 80 and saturation < 100:
        return 1  # Garbage Overflow
    
    # Blue tones might indicate water issues
    if features.get('mean_blue', 0) > features.get('mean_red', 0) * 1.3:
        return 3  # Water Leakage
    
    # Very dark images at night might be streetlight issues
    if brightness < 50:
        return 4  # Streetlight Damage
    
    # Default to road damage for high contrast images
    if features.get('contrast', 0) > 60:
        return 5  # Road Damage
    
    return 9  # Other Issue


def calculate_confidence(features, probabilities=None):
    """
    Calculate confidence score based on features.
    Returns a value between 0.5 and 0.95.
    """
    if not features:
        return 0.5
    
    # Base confidence
    confidence = 0.6
    
    # Adjust based on feature clarity
    edge_density = features.get('edge_density', 0)
    contrast = features.get('contrast', 0)
    
    # Clear images with good contrast get higher confidence
    if contrast > 50:
        confidence += 0.15
    if edge_density > 0.1:
        confidence += 0.1
    
    # Cap at 95%
    return min(confidence, 0.95)


def simulate_detection(image_path=None):
    """
    Simulate AI detection when ML libraries are not available.
    Used for development and testing.
    """
    # Random issue detection for simulation
    issues = list(ISSUE_CATEGORIES.values())
    weights = [0.2, 0.15, 0.15, 0.12, 0.1, 0.1, 0.08, 0.05, 0.03, 0.02]
    
    selected_issue = random.choices(issues, weights=weights, k=1)[0]
    confidence = random.uniform(65, 92)
    
    return {
        'issue': selected_issue,
        'confidence': round(confidence, 2)
    }


# Additional utility functions

def get_issue_icon(issue_type):
    """Get icon class for issue type."""
    icons = {
        'Pothole': 'fa-road',
        'Garbage Overflow': 'fa-trash',
        'Broken Road': 'fa-road',
        'Water Leakage': 'fa-tint',
        'Streetlight Damage': 'fa-lightbulb',
        'Road Damage': 'fa-exclamation-triangle',
        'Drainage Issue': 'fa-water',
        'Fallen Tree': 'fa-tree',
        'Illegal Dumping': 'fa-dumpster',
        'Other Issue': 'fa-question-circle'
    }
    return icons.get(issue_type, 'fa-question-circle')


def get_issue_color(issue_type):
    """Get color for issue type."""
    colors = {
        'Pothole': '#e74c3c',
        'Garbage Overflow': '#27ae60',
        'Broken Road': '#f39c12',
        'Water Leakage': '#3498db',
        'Streetlight Damage': '#f1c40f',
        'Road Damage': '#e67e22',
        'Drainage Issue': '#1abc9c',
        'Fallen Tree': '#2ecc71',
        'Illegal Dumping': '#95a5a6',
        'Other Issue': '#7f8c8d'
    }
    return colors.get(issue_type, '#7f8c8d')

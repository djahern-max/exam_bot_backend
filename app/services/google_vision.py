from google.cloud import vision
import os
import io
from PIL import Image
from typing import Dict, List, Any, Optional
from app.models.models import QuestionType
from google.oauth2 import service_account


class GoogleVisionService:
    def __init__(self):
        try:
            # Try using environment variable first
            if os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
                self.client = vision.ImageAnnotatorClient()
            else:
                # Explicitly use the credentials file as fallback
                credentials_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                            "credentials", "exam_bot_google_cloud.json")
                print(f"Loading credentials from: {credentials_path}")
                if os.path.exists(credentials_path):
                    credentials = service_account.Credentials.from_service_account_file(credentials_path)
                    self.client = vision.ImageAnnotatorClient(credentials=credentials)
                else:
                    print(f"Error: Credentials file not found at {credentials_path}")
                    self.client = None
        except Exception as e:
            print(f"Error initializing Google Vision client: {e}")
            self.client = None

    def detect_text(self, image_path: str) -> str:
        """
        Detects text in an image using Google Cloud Vision API.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Extracted text from the image
        """
        if self.client is None:
            return "Error: Google Vision API client not initialized. Please check credentials."
            
        # Read the image file
        with io.open(image_path, 'rb') as image_file:
            content = image_file.read()

        image = vision.Image(content=content)

        # Perform text detection
        response = self.client.text_detection(image=image)
        
        if response.error.message:
            raise Exception(f"Error detecting text: {response.error.message}")
            
        # Extract the text
        texts = response.text_annotations
        if not texts:
            return ""
            
        # The first annotation contains the complete detected text
        return texts[0].description

    def process_screenshot(self, image_path: str, question_type: QuestionType) -> Dict[str, Any]:
        """
        Process a screenshot of an exam question using Google Cloud Vision API
        
        Args:
            image_path: Path to the screenshot
            question_type: Type of question (multiple choice or open-ended)
            
        Returns:
            Dictionary containing extracted text and structured question data
        """
        # Extract text from image
        extracted_text = self.detect_text(image_path)
        
        return {
            "image_path": image_path,
            "extracted_text": extracted_text,
            "question_type": question_type
        }

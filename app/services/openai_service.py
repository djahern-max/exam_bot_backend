from openai import OpenAI
from typing import Dict, Any, Optional, List
import json
import re
from app.core.config import settings
from app.models.models import QuestionType


class OpenAIService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL

    def analyze_multiple_choice_question(self, extracted_text: str, show_explanation: bool = False) -> Dict[str, Any]:
        """
        Analyze a multiple choice question using OpenAI.
        
        Args:
            extracted_text: Text extracted from the image
            show_explanation: Whether to include an explanation for the answer
            
        Returns:
            Dictionary containing the structured question, options, answer, and optional explanation
        """
        # Prompt for multiple choice question analysis
        prompt = f"""
        Analyze this multiple choice question and provide the following information in JSON format:
        
        Extracted text:
        {extracted_text}
        
        Please extract:
        1. The question text (without options)
        2. The options (labeled as A, B, C, D, etc. or 1, 2, 3, 4, etc.)
        3. The correct answer (just the option letter or number)
        
        Format your response as a valid JSON object with these keys:
        question_text, options (as a dictionary with option letters/numbers as keys), answer (just the letter/number)
        
        {"4. Provide a brief explanation for why this is the correct answer" if show_explanation else ""}
        
        Respond ONLY with the JSON, no other text.
        """
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert at analyzing exam questions. Your task is to extract the question, options, and determine the correct answer."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        # Parse the response
        analysis_json = json.loads(response.choices[0].message.content)
        
        # Ensure consistent key presence
        result = {
            "question_text": analysis_json.get("question_text", ""),
            "options": analysis_json.get("options", {}),
            "answer": analysis_json.get("answer", ""),
            "explanation": analysis_json.get("explanation", "") if show_explanation else None
        }
        
        return result

    def analyze_open_ended_question(self, extracted_text: str, show_explanation: bool = False) -> Dict[str, Any]:
        """
        Analyze an open-ended question using OpenAI.
        
        Args:
            extracted_text: Text extracted from the image
            show_explanation: Whether to include an explanation for the answer
            
        Returns:
            Dictionary containing the structured question, answer, and optional explanation
        """
        # Prompt for open-ended question analysis
        prompt = f"""
        Analyze this open-ended question and provide the following information in JSON format:
        
        Extracted text:
        {extracted_text}
        
        Please extract:
        1. The question text
        2. A comprehensive, accurate answer to the question
        
        Format your response as a valid JSON object with these keys:
        question_text, answer
        
        {"3. Provide a detailed explanation of the answer with key concepts and reasoning" if show_explanation else ""}
        
        Respond ONLY with the JSON, no other text.
        """
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert at answering exam questions. Your task is to extract the question and provide a comprehensive, accurate answer."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        # Parse the response
        analysis_json = json.loads(response.choices[0].message.content)
        
        # Ensure consistent key presence
        result = {
            "question_text": analysis_json.get("question_text", ""),
            "options": None,  # No options for open-ended questions
            "answer": analysis_json.get("answer", ""),
            "explanation": analysis_json.get("explanation", "") if show_explanation else None
        }
        
        return result

    def analyze_question(self, extracted_text: str, question_type: QuestionType, show_explanation: bool = False) -> Dict[str, Any]:
        """
        Analyze an exam question based on its type.
        
        Args:
            extracted_text: Text extracted from the image
            question_type: Type of question (multiple choice or open-ended)
            show_explanation: Whether to include an explanation for the answer
            
        Returns:
            Dictionary containing the analysis results
        """
        if question_type == QuestionType.MULTIPLE_CHOICE:
            return self.analyze_multiple_choice_question(extracted_text, show_explanation)
        else:
            return self.analyze_open_ended_question(extracted_text, show_explanation)
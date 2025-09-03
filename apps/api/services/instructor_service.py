"""LLM structured output service with Instructor for intelligent data extraction"""

import os
import logging
from typing import Dict, List, Any, Optional, Type, TypeVar
from pydantic import BaseModel, Field
import instructor
from openai import OpenAI
from litellm import completion

logger = logging.getLogger(__name__)
T = TypeVar('T', bound=BaseModel)

class InstructorService:
    """Service for structured LLM output using Instructor"""
    
    def __init__(self):
        self._client = None
        self._enabled = None
        
    @property
    def client(self):
        if self._client is None:
            self._initialize()
        return self._client
        
    @property
    def enabled(self):
        if self._enabled is None:
            self._initialize()
        return self._enabled
        
    def _initialize(self):
        """Lazy initialization"""
        if self._client is None:
            self._client = self._initialize_client()
            self._enabled = self._client is not None
        
    def _initialize_client(self):
        """Initialize OpenAI client with Instructor patch"""
        try:
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                logger.warning("OPENAI_API_KEY not found. Instructor service will be disabled.")
                return None
            
            # Initialize OpenAI client with explicit configuration to avoid proxy issues
            # Create a custom HTTP client without proxy support
            import httpx
            
            # Create a custom HTTP client that explicitly disables proxies
            http_client = httpx.Client(
                proxies=None,  # Explicitly disable proxies
                transport=httpx.HTTPTransport(retries=3)
            )
            
            openai_client = OpenAI(
                api_key=api_key,
                http_client=http_client,
                max_retries=3
            )
            
            # Patch with Instructor
            client = instructor.patch(openai_client)
            
            logger.info("Instructor service initialized successfully")
            return client
            
        except Exception as e:
            logger.error(f"Failed to initialize Instructor: {e}")
            return None
    
    def extract_structured_data(self, 
                              text: str, 
                              response_model: Type[T],
                              model: str = "gpt-4o",
                              max_retries: int = 3,
                              **kwargs) -> Optional[T]:
        """Extract structured data from text using Pydantic models"""
        
        if not self.enabled:
            logger.warning("Instructor service not enabled")
            return None
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                response_model=response_model,
                max_retries=max_retries,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a expert data extraction assistant. Extract structured information from the provided text."
                    },
                    {
                        "role": "user", 
                        "content": f"Extract structured information from this text:\n\n{text}"
                    }
                ],
                **kwargs
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Structured extraction failed: {e}")
            return None
    
    def extract_with_fallback(self,
                            text: str,
                            response_model: Type[T],
                            models: List[str] = None,
                            **kwargs) -> Optional[T]:
        """Extract data with model fallback strategy"""
        
        if models is None:
            models = ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]
        
        for model in models:
            try:
                result = self.extract_structured_data(text, response_model, model=model, **kwargs)
                if result:
                    logger.info(f"Successfully extracted with model: {model}")
                    return result
            except Exception as e:
                logger.warning(f"Model {model} failed: {e}")
                continue
        
        logger.error("All models failed for extraction")
        return None
    
    def batch_extract(self,
                     texts: List[str],
                     response_model: Type[T],
                     **kwargs) -> List[Optional[T]]:
        """Batch extract structured data from multiple texts"""
        
        results = []
        for text in texts:
            result = self.extract_structured_data(text, response_model, **kwargs)
            results.append(result)
        
        return results
    
    def classify_text(self,
                     text: str,
                     categories: List[str],
                     model: str = "gpt-4o") -> Optional[Dict[str, Any]]:
        """Classify text into predefined categories"""
        
        class Classification(BaseModel):
            category: str = Field(description="The most relevant category")
            confidence: float = Field(description="Confidence score between 0-1")
            reasoning: str = Field(description="Reasoning for the classification")
            alternative_categories: List[str] = Field(description="Alternative relevant categories")
        
        try:
            categories_str = ", ".join(categories)
            
            response = self.client.chat.completions.create(
                model=model,
                response_model=Classification,
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a classification expert. Classify the text into one of these categories: {categories_str}"
                    },
                    {
                        "role": "user",
                        "content": f"Classify this text:\n\n{text}"
                    }
                ]
            )
            
            return {
                'category': response.category,
                'confidence': response.confidence,
                'reasoning': response.reasoning,
                'alternatives': response.alternative_categories
            }
            
        except Exception as e:
            logger.error(f"Text classification failed: {e}")
            return None
    
    def summarize_document(self,
                          text: str,
                          model: str = "gpt-4o",
                          max_length: int = 500) -> Optional[str]:
        """Generate document summary with structured output"""
        
        class Summary(BaseModel):
            summary: str = Field(description="Concise document summary")
            key_points: List[str] = Field(description="List of key points")
            tone: str = Field(description="Tone of the document")
            urgency: str = Field(description="Urgency level: low, medium, high")
        
        try:
            response = self.extract_structured_data(text, Summary, model=model)
            if response:
                key_points_str = "\n".join(f"- {point}" for point in response.key_points)
                return f"""Summary: {response.summary}

Key Points:
{key_points_str}

Tone: {response.tone}
Urgency: {response.urgency}"""
            
            return None
            
        except Exception as e:
            logger.error(f"Document summarization failed: {e}")
            return None
    
    def extract_entities_advanced(self,
                                text: str,
                                entity_types: List[str] = None,
                                model: str = "gpt-4o") -> Optional[Dict[str, List[str]]]:
        """Advanced entity extraction with type validation"""
        
        if entity_types is None:
            entity_types = ['PERSON', 'ORGANIZATION', 'LOCATION', 'DATE', 'MONEY', 'PRODUCT']
        
        class Entity(BaseModel):
            text: str = Field(description="The entity text")
            type: str = Field(description=f"Entity type from: {', '.join(entity_types)}")
            confidence: float = Field(description="Confidence score")
        
        class EntityExtraction(BaseModel):
            entities: List[Entity] = Field(description="List of extracted entities")
        
        try:
            response = self.extract_structured_data(text, EntityExtraction, model=model)
            if response:
                # Group entities by type
                entities_by_type = {}
                for entity in response.entities:
                    if entity.type not in entities_by_type:
                        entities_by_type[entity.type] = []
                    entities_by_type[entity.type].append({
                        'text': entity.text,
                        'confidence': entity.confidence
                    })
                
                return entities_by_type
            
            return None
            
        except Exception as e:
            logger.error(f"Advanced entity extraction failed: {e}")
            return None
    
    def validate_extraction(self,
                          text: str,
                          response_model: Type[T],
                          expected_fields: List[str] = None,
                          **kwargs) -> Dict[str, Any]:
        """Validate extraction results with confidence scoring"""
        
        result = self.extract_structured_data(text, response_model, **kwargs)
        
        if not result:
            return {
                'success': False,
                'error': 'Extraction failed',
                'confidence': 0.0
            }
        
        # Calculate basic validation metrics
        validation_result = {
            'success': True,
            'result': result.dict(),
            'confidence': self._calculate_confidence(result, expected_fields),
            'fields_extracted': len(result.dict()),
            'has_all_expected_fields': True
        }
        
        if expected_fields:
            result_dict = result.dict()
            missing_fields = [field for field in expected_fields if field not in result_dict or not result_dict[field]]
            validation_result['has_all_expected_fields'] = len(missing_fields) == 0
            validation_result['missing_fields'] = missing_fields
        
        return validation_result
    
    def _calculate_confidence(self, result: BaseModel, expected_fields: List[str] = None) -> float:
        """Calculate confidence score for extraction results"""
        
        result_dict = result.dict()
        total_fields = len(result_dict)
        
        if total_fields == 0:
            return 0.0
        
        # Count non-empty fields
        non_empty_count = sum(1 for value in result_dict.values() if value not in [None, "", [], {}])
        
        # Base confidence
        confidence = non_empty_count / total_fields
        
        # Penalty for missing expected fields
        if expected_fields:
            missing_expected = sum(1 for field in expected_fields if field not in result_dict or not result_dict[field])
            expected_penalty = missing_expected / len(expected_fields) * 0.3  # 30% penalty max
            confidence = max(0.0, confidence - expected_penalty)
        
        return round(confidence, 2)
    
    def health_check(self) -> Dict[str, Any]:
        """Check service health and capabilities"""
        
        return {
            'enabled': self.enabled,
            'openai_configured': bool(os.getenv('OPENAI_API_KEY')),
            'model_availability': self._check_model_availability(),
            'service_status': 'healthy' if self.enabled else 'disabled'
        }
    
    def _check_model_availability(self) -> List[str]:
        """Check available models (simplified check)"""
        
        # This is a simplified check - in production you'd want to use
        # the OpenAI API to list available models
        available_models = []
        
        # Common models that are typically available
        common_models = ["gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"]
        
        for model in common_models:
            available_models.append(model)
        
        return available_models

# Global instance
instructor_service = InstructorService()
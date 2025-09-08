"""
Error Recovery Guide for StudioOps API

This module provides comprehensive error recovery guidance and common
error resolution patterns for users and developers.
"""

from typing import Dict, List, Optional
from enum import Enum
from pydantic import BaseModel

class ErrorCode(str, Enum):
    """Common error codes with recovery guidance"""
    
    # Database errors
    DATABASE_CONNECTION_ERROR = "DATABASE_CONNECTION_ERROR"
    DATABASE_CONSTRAINT_ERROR = "DATABASE_CONSTRAINT_ERROR"
    FOREIGN_KEY_VIOLATION = "FOREIGN_KEY_VIOLATION"
    
    # Validation errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    REQUIRED_FIELD_MISSING = "REQUIRED_FIELD_MISSING"
    INVALID_FORMAT = "INVALID_FORMAT"
    
    # File operation errors
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    FILE_TYPE_NOT_ALLOWED = "FILE_TYPE_NOT_ALLOWED"
    FILE_UPLOAD_FAILED = "FILE_UPLOAD_FAILED"
    
    # External service errors
    TRELLO_API_ERROR = "TRELLO_API_ERROR"
    AI_SERVICE_ERROR = "AI_SERVICE_ERROR"
    EXTERNAL_SERVICE_UNAVAILABLE = "EXTERNAL_SERVICE_UNAVAILABLE"
    
    # Authentication/Authorization errors
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    
    # System errors
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"

class RecoveryStep(BaseModel):
    """Individual recovery step"""
    step_number: int
    title: str
    title_he: Optional[str] = None
    description: str
    description_he: Optional[str] = None
    is_technical: bool = False  # Whether this step requires technical knowledge

class ErrorRecoveryGuide(BaseModel):
    """Complete error recovery guide"""
    error_code: str
    title: str
    title_he: Optional[str] = None
    description: str
    description_he: Optional[str] = None
    severity: str
    user_steps: List[RecoveryStep]
    technical_steps: Optional[List[RecoveryStep]] = None
    prevention_tips: Optional[List[str]] = None
    prevention_tips_he: Optional[List[str]] = None

class ErrorRecoveryService:
    """Service for providing error recovery guidance"""
    
    def __init__(self):
        self.recovery_guides = self._initialize_recovery_guides()
    
    def get_recovery_guide(self, error_code: str) -> Optional[ErrorRecoveryGuide]:
        """Get recovery guide for specific error code"""
        return self.recovery_guides.get(error_code)
    
    def get_all_guides(self) -> Dict[str, ErrorRecoveryGuide]:
        """Get all available recovery guides"""
        return self.recovery_guides
    
    def _initialize_recovery_guides(self) -> Dict[str, ErrorRecoveryGuide]:
        """Initialize all recovery guides"""
        guides = {}
        
        # Database Connection Error
        guides[ErrorCode.DATABASE_CONNECTION_ERROR] = ErrorRecoveryGuide(
            error_code=ErrorCode.DATABASE_CONNECTION_ERROR,
            title="Database Connection Failed",
            title_he="חיבור למסד הנתונים נכשל",
            description="The system cannot connect to the database. This may be temporary.",
            description_he="המערכת לא יכולה להתחבר למסד הנתונים. זה עשוי להיות זמני.",
            severity="high",
            user_steps=[
                RecoveryStep(
                    step_number=1,
                    title="Wait and Retry",
                    title_he="המתן ונסה שוב",
                    description="Wait 30 seconds and try your request again",
                    description_he="המתן 30 שניות ונסה את הבקשה שוב"
                ),
                RecoveryStep(
                    step_number=2,
                    title="Check Internet Connection",
                    title_he="בדוק חיבור לאינטרנט",
                    description="Ensure you have a stable internet connection",
                    description_he="ודא שיש לך חיבור יציב לאינטרנט"
                ),
                RecoveryStep(
                    step_number=3,
                    title="Contact Support",
                    title_he="צור קשר עם התמיכה",
                    description="If the problem persists, contact technical support",
                    description_he="אם הבעיה נמשכת, צור קשר עם התמיכה הטכנית"
                )
            ],
            technical_steps=[
                RecoveryStep(
                    step_number=1,
                    title="Check Database Status",
                    description="Verify database server is running and accessible",
                    is_technical=True
                ),
                RecoveryStep(
                    step_number=2,
                    title="Check Connection String",
                    description="Verify DATABASE_URL environment variable is correct",
                    is_technical=True
                ),
                RecoveryStep(
                    step_number=3,
                    title="Check Network Connectivity",
                    description="Test network connectivity to database server",
                    is_technical=True
                )
            ],
            prevention_tips=[
                "Ensure database server has adequate resources",
                "Monitor database connection pool usage",
                "Set up database health monitoring"
            ],
            prevention_tips_he=[
                "ודא שלשרת מסד הנתונים יש משאבים מספקים",
                "עקוב אחר שימוש במאגר חיבורי מסד הנתונים",
                "הגדר ניטור בריאות מסד הנתונים"
            ]
        )
        
        # File Too Large Error
        guides[ErrorCode.FILE_TOO_LARGE] = ErrorRecoveryGuide(
            error_code=ErrorCode.FILE_TOO_LARGE,
            title="File Too Large",
            title_he="קובץ גדול מדי",
            description="The uploaded file exceeds the maximum allowed size",
            description_he="הקובץ שהועלה חורג מהגודל המקסימלי המותר",
            severity="medium",
            user_steps=[
                RecoveryStep(
                    step_number=1,
                    title="Compress the File",
                    title_he="דחוס את הקובץ",
                    description="Use file compression software to reduce file size",
                    description_he="השתמש בתוכנת דחיסת קבצים כדי להקטין את גודל הקובץ"
                ),
                RecoveryStep(
                    step_number=2,
                    title="Split Large Files",
                    title_he="פצל קבצים גדולים",
                    description="Break large files into smaller parts and upload separately",
                    description_he="פצל קבצים גדולים לחלקים קטנים יותר והעלה בנפרד"
                ),
                RecoveryStep(
                    step_number=3,
                    title="Use Alternative Format",
                    title_he="השתמש בפורמט חלופי",
                    description="Convert to a more efficient file format if possible",
                    description_he="המר לפורמט קובץ יעיל יותר אם אפשר"
                )
            ],
            prevention_tips=[
                "Check file sizes before uploading",
                "Use appropriate file formats for your content",
                "Compress files when possible"
            ],
            prevention_tips_he=[
                "בדוק גדלי קבצים לפני העלאה",
                "השתמש בפורמטי קבצים מתאימים לתוכן שלך",
                "דחוס קבצים כשאפשר"
            ]
        )
        
        # Trello API Error
        guides[ErrorCode.TRELLO_API_ERROR] = ErrorRecoveryGuide(
            error_code=ErrorCode.TRELLO_API_ERROR,
            title="Trello Integration Error",
            title_he="שגיאת אינטגרציית Trello",
            description="There's an issue with the Trello integration. The system will use mock data temporarily.",
            description_he="יש בעיה עם אינטגרציית Trello. המערכת תשתמש בנתונים מדומים זמנית.",
            severity="medium",
            user_steps=[
                RecoveryStep(
                    step_number=1,
                    title="Continue with Mock Data",
                    title_he="המשך עם נתונים מדומים",
                    description="The system will create mock Trello boards and cards for now",
                    description_he="המערכת תיצור לוחות וכרטיסי Trello מדומים לעת עתה"
                ),
                RecoveryStep(
                    step_number=2,
                    title="Try Again Later",
                    title_he="נסה שוב מאוחר יותר",
                    description="Trello integration may be restored automatically",
                    description_he="אינטגרציית Trello עשויה להתחדש אוטומטית"
                ),
                RecoveryStep(
                    step_number=3,
                    title="Manual Trello Setup",
                    title_he="הגדרת Trello ידנית",
                    description="You can manually create Trello boards using the mock data as reference",
                    description_he="אתה יכול ליצור לוחות Trello ידנית באמצעות הנתונים המדומים כהפניה"
                )
            ],
            technical_steps=[
                RecoveryStep(
                    step_number=1,
                    title="Check API Credentials",
                    description="Verify TRELLO_API_KEY and TRELLO_TOKEN are correctly configured",
                    is_technical=True
                ),
                RecoveryStep(
                    step_number=2,
                    title="Test API Connection",
                    description="Test direct connection to Trello API endpoints",
                    is_technical=True
                ),
                RecoveryStep(
                    step_number=3,
                    title="Check Rate Limits",
                    description="Verify if API rate limits have been exceeded",
                    is_technical=True
                )
            ]
        )
        
        # AI Service Error
        guides[ErrorCode.AI_SERVICE_ERROR] = ErrorRecoveryGuide(
            error_code=ErrorCode.AI_SERVICE_ERROR,
            title="AI Service Unavailable",
            title_he="שירות הבינה המלאכותית לא זמין",
            description="The AI service is temporarily unavailable. Enhanced mock responses will be used.",
            description_he="שירות הבינה המלאכותית אינו זמין זמנית. ישמשו תגובות מדומות משופרות.",
            severity="medium",
            user_steps=[
                RecoveryStep(
                    step_number=1,
                    title="Use Enhanced Responses",
                    title_he="השתמש בתגובות משופרות",
                    description="The system provides contextual mock responses based on your project",
                    description_he="המערכת מספקת תגובות מדומות הקשריות על בסיס הפרויקט שלך"
                ),
                RecoveryStep(
                    step_number=2,
                    title="Try Again Later",
                    title_he="נסה שוב מאוחר יותר",
                    description="AI service may be restored automatically",
                    description_he="שירות הבינה המלאכותית עשוי להתחדש אוטומטית"
                ),
                RecoveryStep(
                    step_number=3,
                    title="Manual Planning",
                    title_he="תכנון ידני",
                    description="You can create project plans manually using the system's tools",
                    description_he="אתה יכול ליצור תוכניות פרויקט ידנית באמצעות הכלים של המערכת"
                )
            ]
        )
        
        # Validation Error
        guides[ErrorCode.VALIDATION_ERROR] = ErrorRecoveryGuide(
            error_code=ErrorCode.VALIDATION_ERROR,
            title="Input Validation Failed",
            title_he="אימות קלט נכשל",
            description="The provided data doesn't meet the required format or constraints",
            description_he="הנתונים שסופקו אינם עומדים בפורמט או באילוצים הנדרשים",
            severity="low",
            user_steps=[
                RecoveryStep(
                    step_number=1,
                    title="Check Highlighted Fields",
                    title_he="בדוק שדות מסומנים",
                    description="Review the fields marked with errors and correct them",
                    description_he="בדוק את השדות המסומנים עם שגיאות ותקן אותם"
                ),
                RecoveryStep(
                    step_number=2,
                    title="Follow Format Requirements",
                    title_he="עקוב אחר דרישות הפורמט",
                    description="Ensure all fields follow the required format (dates, emails, etc.)",
                    description_he="ודא שכל השדות עוקבים אחר הפורמט הנדרש (תאריכים, אימיילים וכו')"
                ),
                RecoveryStep(
                    step_number=3,
                    title="Fill Required Fields",
                    title_he="מלא שדות חובה",
                    description="Make sure all required fields are filled",
                    description_he="ודא שכל שדות החובה מלאים"
                )
            ],
            prevention_tips=[
                "Double-check data before submitting",
                "Use the correct format for dates and numbers",
                "Fill all required fields"
            ],
            prevention_tips_he=[
                "בדוק שוב נתונים לפני שליחה",
                "השתמש בפורמט הנכון לתאריכים ומספרים",
                "מלא את כל שדות החובה"
            ]
        )
        
        return guides

# Global instance
error_recovery_service = ErrorRecoveryService()

def get_recovery_guide(error_code: str) -> Optional[ErrorRecoveryGuide]:
    """Get recovery guide for specific error code"""
    return error_recovery_service.get_recovery_guide(error_code)

def get_user_friendly_error_message(error_code: str, language: str = "en") -> str:
    """Get user-friendly error message in specified language"""
    guide = get_recovery_guide(error_code)
    if not guide:
        return "An error occurred. Please try again or contact support."
    
    if language == "he" and guide.description_he:
        return guide.description_he
    return guide.description

def get_recovery_steps(error_code: str, include_technical: bool = False) -> List[RecoveryStep]:
    """Get recovery steps for specific error code"""
    guide = get_recovery_guide(error_code)
    if not guide:
        return []
    
    steps = guide.user_steps.copy()
    if include_technical and guide.technical_steps:
        steps.extend(guide.technical_steps)
    
    return steps
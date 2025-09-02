"""Database models for StudioOps AI"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

def generate_ulid():
    return str(uuid.uuid4())

class ChatMessage(Base):
    """Chat message storage for memory"""
    __tablename__ = "chat_messages"
    
    id = Column(String, primary_key=True, default=generate_ulid)
    session_id = Column(String, index=True, nullable=False)
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    is_user = Column(Boolean, default=True)
    project_context = Column(JSON, nullable=True)
    meta_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<ChatMessage(session_id={self.session_id}, message={self.message[:50]}...)>"

class ChatSession(Base):
    """Chat session management"""
    __tablename__ = "chat_sessions"
    
    id = Column(String, primary_key=True, default=generate_ulid)
    user_id = Column(String, index=True, nullable=True)
    project_id = Column(String, index=True, nullable=True)
    title = Column(String, nullable=True)
    context = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<ChatSession(id={self.id}, title={self.title})>"

class RAGDocument(Base):
    """RAG document storage"""
    __tablename__ = "rag_documents"
    
    id = Column(String, primary_key=True, default=generate_ulid)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    source = Column(String, nullable=True)  # e.g., 'manual', 'upload', 'web'
    document_type = Column(String, nullable=True)  # e.g., 'spec', 'manual', 'guide'
    meta_data = Column(JSON, nullable=True)
    embedding = Column(JSON, nullable=True)  # Store vector embeddings
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<RAGDocument(title={self.title}, type={self.document_type})>"

class ProjectKnowledge(Base):
    """Project-specific knowledge base"""
    __tablename__ = "project_knowledge"
    
    id = Column(String, primary_key=True, default=generate_ulid)
    project_id = Column(String, index=True, nullable=False)
    category = Column(String, nullable=False)  # e.g., 'materials', 'techniques', 'pricing'
    key = Column(String, nullable=False)
    value = Column(Text, nullable=False)
    confidence = Column(Float, default=1.0)
    source = Column(String, nullable=True)
    meta_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<ProjectKnowledge(project={self.project_id}, key={self.key})>"
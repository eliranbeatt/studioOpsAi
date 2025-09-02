"""RAG service for document retrieval and knowledge enhancement"""

import os
from typing import List, Dict, Any
import chromadb
from sentence_transformers import SentenceTransformer
import numpy as np
try:
    from .database import get_db
    from .models import RAGDocument
except ImportError:
    # Fallback for direct import
    from database import get_db
    from models import RAGDocument
import json

class RAGService:
    def __init__(self):
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.chroma_client = chromadb.Client()
        self.collection = self._initialize_collection()
        self._load_existing_documents()
    
    def _initialize_collection(self):
        """Initialize ChromaDB collection"""
        collection_name = os.getenv('RAG_COLLECTION_NAME', 'studioops_documents')
        
        try:
            # Try to get existing collection
            collection = self.chroma_client.get_collection(collection_name)
            print(f"Loaded existing RAG collection: {collection_name}")
            return collection
        except:
            # Create new collection
            collection = self.chroma_client.create_collection(collection_name)
            print(f"Created new RAG collection: {collection_name}")
            
            # Add initial knowledge documents
            self._add_initial_documents(collection)
            return collection
    
    def _load_existing_documents(self):
        """Load existing documents from database into ChromaDB"""
        try:
            db = next(get_db())
            documents = db.query(RAGDocument).filter(RAGDocument.is_active == True).all()
            
            for doc in documents:
                if doc.embedding:
                    # Add to ChromaDB if not already there
                    self.collection.add(
                        ids=[doc.id],
                        embeddings=[doc.embedding],
                        documents=[doc.content],
                        metadatas=[{
                            'title': doc.title,
                            'source': doc.source,
                            'type': doc.document_type
                        }]
                    )
            
            print(f"Loaded {len(documents)} documents into RAG system")
            
        except Exception as e:
            print(f"Error loading documents from database: {e}")
            print("Continuing with initial documents only")
        finally:
            try:
                db.close()
            except:
                pass
    
    def _add_initial_documents(self, collection):
        """Add initial knowledge base documents"""
        initial_docs = [
            {
                'title': 'Woodworking Material Guide',
                'content': '''Common woodworking materials and their uses:
- Plywood: General construction, cabinets, furniture. Standard size 4x8 feet.
- 2x4 Lumber: Framing, structural elements. Actual dimensions 1.5x3.5 inches.
- Pine Boards: Furniture, trim, decorative elements. Various sizes available.
- MDF: Smooth surface for painting, cabinets. Not moisture resistant.
- Hardwood: Fine furniture, high-end projects. Includes oak, maple, walnut.''',
                'source': 'manual',
                'type': 'material_guide'
            },
            {
                'title': 'Project Estimation Guidelines',
                'content': '''Project estimation best practices:
- Always add 15-20% waste factor for materials
- Labor estimates: Basic carpentry $50-75/hr, Fine woodworking $75-125/hr
- Painting: $2-4 per square foot depending on complexity
- Standard project margins: 25-40% for custom work
- Always account for setup and cleanup time''',
                'source': 'manual', 
                'type': 'estimation_guide'
            },
            {
                'title': 'Cabinet Construction Standards',
                'content': '''Standard cabinet dimensions and construction:
- Base cabinets: 34.5" height, 24" depth
- Wall cabinets: 12-15" depth, various heights
- Standard widths: 12", 15", 18", 24", 30", 36"
- Materials: 3/4" plywood for boxes, 1/4" for backs
- Hardware: Soft-close hinges, full-extension slides''',
                'source': 'manual',
                'type': 'construction_standard'
            }
        ]
        
        for doc_data in initial_docs:
            # Generate embedding
            embedding = self.embedding_model.encode(doc_data['content']).tolist()
            
            # Add to ChromaDB
            doc_id = str(len(collection.get()['ids']) + 1) if collection.get()['ids'] else '1'
            collection.add(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[doc_data['content']],
                metadatas=[{
                    'title': doc_data['title'],
                    'source': doc_data['source'],
                    'type': doc_data['type']
                }]
            )
            
            # Save to database
            db = next(get_db())
            try:
                rag_doc = RAGDocument(
                    id=doc_id,
                    title=doc_data['title'],
                    content=doc_data['content'],
                    source=doc_data['source'],
                    document_type=doc_data['type'],
                    embedding=embedding
                )
                db.add(rag_doc)
                db.commit()
                print(f"Added initial document: {doc_data['title']}")
                
            except Exception as e:
                db.rollback()
                print(f"Error saving initial document: {e}")
            finally:
                db.close()
    
    def add_document(self, title: str, content: str, source: str = 'manual', document_type: str = None):
        """Add document to RAG system"""
        # Generate embedding
        embedding = self.embedding_model.encode(content).tolist()
        
        # Add to ChromaDB
        doc_id = str(len(self.collection.get()['ids']) + 1) if self.collection.get()['ids'] else '1'
        self.collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[content],
            metadatas=[{
                'title': title,
                'source': source,
                'type': document_type
            }]
        )
        
        # Save to database if available
        try:
            db = next(get_db())
            rag_doc = RAGDocument(
                id=doc_id,
                title=title,
                content=content,
                source=source,
                document_type=document_type,
                embedding=embedding
            )
            db.add(rag_doc)
            db.commit()
            print(f"Added document to RAG: {title}")
            
        except Exception as e:
            print(f"Error saving document to database: {e}")
            print("Document added to ChromaDB only")
        finally:
            try:
                db.close()
            except:
                pass
    
    def search_documents(self, query: str, n_results: int = 3) -> List[Dict]:
        """Search for relevant documents"""
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Search ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    'id': results['ids'][0][i],
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i]
                })
            
            return formatted_results
            
        except Exception as e:
            print(f"Error searching documents: {e}")
            return []
    
    def enhance_prompt(self, user_message: str, max_context: int = 1000) -> str:
        """Enhance prompt with relevant context from RAG"""
        relevant_docs = self.search_documents(user_message)
        
        if not relevant_docs:
            return user_message
        
        # Build context string
        context_parts = []
        total_length = 0
        
        for doc in relevant_docs:
            doc_content = f"From {doc['metadata']['title']}: {doc['content']}"
            if total_length + len(doc_content) <= max_context:
                context_parts.append(doc_content)
                total_length += len(doc_content)
            else:
                break
        
        if context_parts:
            context_str = "\n\nRelevant knowledge:\n" + "\n".join(context_parts)
            return user_message + context_str
        
        return user_message

# Global instance
rag_service = RAGService()
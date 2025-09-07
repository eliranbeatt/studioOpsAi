"""RAG service for document retrieval and knowledge enhancement"""

import os
import uuid
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
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            self.chroma_client = chromadb.Client()
            self.collection = self._initialize_collection()
            
            if self.collection is not None:
                self._load_existing_documents()
                print("RAG service initialized successfully")
            else:
                print("Warning: RAG service initialized without ChromaDB collection")
                
        except Exception as e:
            print(f"Error initializing RAG service: {e}")
            self.collection = None
    
    def _initialize_collection(self):
        """Initialize ChromaDB collection with proper error handling"""
        collection_name = os.getenv('RAG_COLLECTION_NAME', 'studioops_documents')
        
        try:
            # Try to get existing collection
            collection = self.chroma_client.get_collection(collection_name)
            print(f"Loaded existing RAG collection: {collection_name}")
            return collection
        except Exception as e:
            print(f"Could not load existing collection: {e}")
            try:
                # Create new collection
                collection = self.chroma_client.create_collection(collection_name)
                print(f"Created new RAG collection: {collection_name}")
                
                # Add initial knowledge documents
                self._add_initial_documents(collection)
                return collection
            except Exception as create_error:
                print(f"Error creating ChromaDB collection: {create_error}")
                # Return None to handle gracefully
                return None
    
    def reinitialize_collection(self):
        """Reinitialize ChromaDB collection (useful for recovery)"""
        collection_name = os.getenv('RAG_COLLECTION_NAME', 'studioops_documents')
        
        try:
            # Delete existing collection if it exists
            try:
                self.chroma_client.delete_collection(collection_name)
                print(f"Deleted existing collection: {collection_name}")
            except:
                pass  # Collection might not exist
            
            # Create new collection
            collection = self.chroma_client.create_collection(collection_name)
            print(f"Created new RAG collection: {collection_name}")
            
            # Reload all documents from database
            self.collection = collection
            self._load_existing_documents()
            
            # Add initial documents if none exist
            if not collection.get()['ids']:
                self._add_initial_documents(collection)
            
            return collection
            
        except Exception as e:
            print(f"Error reinitializing collection: {e}")
            return None
    
    def _load_existing_documents(self):
        """Load existing documents from database into ChromaDB"""
        try:
            db = next(get_db())
            documents = db.query(RAGDocument).filter(RAGDocument.is_active == True).all()
            
            # Get existing ChromaDB document IDs to avoid duplicates
            existing_chroma_ids = set()
            try:
                existing_data = self.collection.get()
                existing_chroma_ids = set(existing_data['ids'])
            except Exception as e:
                print(f"Warning: Could not get existing ChromaDB documents: {e}")
            
            loaded_count = 0
            for doc in documents:
                if doc.embedding and doc.id not in existing_chroma_ids:
                    try:
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
                        loaded_count += 1
                    except Exception as e:
                        print(f"Error adding document {doc.id} to ChromaDB: {e}")
                        continue
            
            print(f"Loaded {loaded_count} documents into RAG system")
            
        except Exception as e:
            print(f"Error loading documents from database: {e}")
            print("Continuing with initial documents only")
        finally:
            try:
                db.close()
            except:
                pass
    
    def _add_initial_documents(self, collection):
        """Add initial knowledge base documents with deduplication"""
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
            # Check if document already exists in database
            db = next(get_db())
            try:
                existing_doc = db.query(RAGDocument).filter(
                    RAGDocument.title == doc_data['title'],
                    RAGDocument.source == doc_data['source'],
                    RAGDocument.is_active == True
                ).first()
                
                if existing_doc:
                    print(f"Document already exists: {doc_data['title']}")
                    continue
                
                # Generate proper UUID for document ID
                doc_id = str(uuid.uuid4())
                
                # Generate embedding
                embedding = self.embedding_model.encode(doc_data['content']).tolist()
                
                # Check if document exists in ChromaDB
                try:
                    existing_chroma_data = collection.get()
                    existing_titles = [meta.get('title') for meta in existing_chroma_data.get('metadatas', [])]
                    if doc_data['title'] in existing_titles:
                        print(f"Document already exists in ChromaDB: {doc_data['title']}")
                        continue
                except Exception as e:
                    print(f"Warning: Could not check existing ChromaDB documents: {e}")
                
                # Add to ChromaDB
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
                print(f"Error processing document {doc_data['title']}: {e}")
            finally:
                db.close()
    
    def add_document(self, title: str, content: str, source: str = 'manual', document_type: str = None):
        """Add document to RAG system with deduplication"""
        # Check if document already exists
        db = next(get_db())
        try:
            existing_doc = db.query(RAGDocument).filter(
                RAGDocument.title == title,
                RAGDocument.source == source,
                RAGDocument.is_active == True
            ).first()
            
            if existing_doc:
                print(f"Document already exists: {title}")
                return existing_doc.id
            
            # Generate proper UUID for document ID
            doc_id = str(uuid.uuid4())
            
            # Generate embedding
            embedding = self.embedding_model.encode(content).tolist()
            
            # Add to ChromaDB
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
            
            # Save to database
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
            return doc_id
            
        except Exception as e:
            db.rollback()
            print(f"Error saving document to database: {e}")
            print("Document not added")
            raise e
        finally:
            try:
                db.close()
            except:
                pass
    
    def update_document(self, doc_id: str, title: str = None, content: str = None, 
                       source: str = None, document_type: str = None):
        """Update existing document in RAG system"""
        db = next(get_db())
        try:
            # Get existing document
            existing_doc = db.query(RAGDocument).filter(RAGDocument.id == doc_id).first()
            if not existing_doc:
                raise ValueError(f"Document with ID {doc_id} not found")
            
            # Update fields if provided
            if title is not None:
                existing_doc.title = title
            if content is not None:
                existing_doc.content = content
                # Regenerate embedding for new content
                existing_doc.embedding = self.embedding_model.encode(content).tolist()
            if source is not None:
                existing_doc.source = source
            if document_type is not None:
                existing_doc.document_type = document_type
            
            # Update in database
            db.commit()
            
            # Update in ChromaDB
            if content is not None:
                self.collection.update(
                    ids=[doc_id],
                    embeddings=[existing_doc.embedding],
                    documents=[existing_doc.content],
                    metadatas=[{
                        'title': existing_doc.title,
                        'source': existing_doc.source,
                        'type': existing_doc.document_type
                    }]
                )
            else:
                # Update metadata only
                self.collection.update(
                    ids=[doc_id],
                    metadatas=[{
                        'title': existing_doc.title,
                        'source': existing_doc.source,
                        'type': existing_doc.document_type
                    }]
                )
            
            print(f"Updated document: {existing_doc.title}")
            return doc_id
            
        except Exception as e:
            db.rollback()
            print(f"Error updating document: {e}")
            raise e
        finally:
            try:
                db.close()
            except:
                pass
    
    def delete_document(self, doc_id: str):
        """Delete document from RAG system"""
        db = next(get_db())
        try:
            # Get existing document
            existing_doc = db.query(RAGDocument).filter(RAGDocument.id == doc_id).first()
            if not existing_doc:
                raise ValueError(f"Document with ID {doc_id} not found")
            
            # Soft delete in database
            existing_doc.is_active = False
            db.commit()
            
            # Remove from ChromaDB
            try:
                self.collection.delete(ids=[doc_id])
            except Exception as e:
                print(f"Warning: Could not remove document from ChromaDB: {e}")
            
            print(f"Deleted document: {existing_doc.title}")
            return True
            
        except Exception as e:
            db.rollback()
            print(f"Error deleting document: {e}")
            raise e
        finally:
            try:
                db.close()
            except:
                pass
    
    def search_documents(self, query: str, n_results: int = 3) -> List[Dict]:
        """Search for relevant documents with enhanced error handling"""
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Search ChromaDB with error handling
            try:
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=n_results
                )
            except Exception as e:
                print(f"ChromaDB query error: {e}")
                return []
            
            # Validate results structure
            if not results or 'ids' not in results or not results['ids']:
                print("No search results found")
                return []
            
            # Format results with validation
            formatted_results = []
            try:
                for i in range(len(results['ids'][0])):
                    result_data = {
                        'id': results['ids'][0][i],
                        'content': results['documents'][0][i] if 'documents' in results and results['documents'] else '',
                        'metadata': results['metadatas'][0][i] if 'metadatas' in results and results['metadatas'] else {},
                        'distance': results['distances'][0][i] if 'distances' in results and results['distances'] else 1.0
                    }
                    formatted_results.append(result_data)
            except (IndexError, KeyError) as e:
                print(f"Error formatting search results: {e}")
                return []
            
            return formatted_results
            
        except Exception as e:
            print(f"Error searching documents: {e}")
            return []
    
    def get_document_by_id(self, doc_id: str) -> Dict:
        """Get specific document by ID"""
        db = next(get_db())
        try:
            doc = db.query(RAGDocument).filter(
                RAGDocument.id == doc_id,
                RAGDocument.is_active == True
            ).first()
            
            if not doc:
                return None
            
            return {
                'id': doc.id,
                'title': doc.title,
                'content': doc.content,
                'source': doc.source,
                'document_type': doc.document_type,
                'created_at': doc.created_at.isoformat() if doc.created_at else None,
                'updated_at': doc.updated_at.isoformat() if doc.updated_at else None
            }
            
        except Exception as e:
            print(f"Error getting document by ID: {e}")
            return None
        finally:
            try:
                db.close()
            except:
                pass
    
    def list_documents(self, source: str = None, document_type: str = None) -> List[Dict]:
        """List all active documents with optional filtering"""
        db = next(get_db())
        try:
            query = db.query(RAGDocument).filter(RAGDocument.is_active == True)
            
            if source:
                query = query.filter(RAGDocument.source == source)
            if document_type:
                query = query.filter(RAGDocument.document_type == document_type)
            
            documents = query.all()
            
            return [{
                'id': doc.id,
                'title': doc.title,
                'source': doc.source,
                'document_type': doc.document_type,
                'created_at': doc.created_at.isoformat() if doc.created_at else None,
                'updated_at': doc.updated_at.isoformat() if doc.updated_at else None
            } for doc in documents]
            
        except Exception as e:
            print(f"Error listing documents: {e}")
            return []
        finally:
            try:
                db.close()
            except:
                pass
    
    def enhance_prompt(self, user_message: str, max_context: int = 1000) -> str:
        """Enhance prompt with relevant context from RAG"""
        if self.collection is None:
            print("Warning: ChromaDB collection not available, returning original message")
            return user_message
            
        relevant_docs = self.search_documents(user_message)
        
        if not relevant_docs:
            return user_message
        
        # Build context string
        context_parts = []
        total_length = 0
        
        for doc in relevant_docs:
            metadata = doc.get('metadata', {})
            title = metadata.get('title', 'Unknown')
            content = doc.get('content', '')
            
            doc_content = f"From {title}: {content}"
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
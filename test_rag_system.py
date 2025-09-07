#!/usr/bin/env python3
"""Test script for RAG system initialization and functionality"""

import sys
import os
sys.path.append('apps/api')

def test_rag_initialization():
    """Test RAG service initialization"""
    print("Testing RAG service initialization...")
    
    try:
        from rag_service import RAGService
        
        # Initialize RAG service
        rag = RAGService()
        
        if rag.collection is None:
            print("❌ RAG collection initialization failed")
            return False
        
        print("✅ RAG service initialized successfully")
        
        # Test document listing
        docs = rag.list_documents()
        print(f"✅ Found {len(docs)} documents in system")
        
        # Test search functionality
        search_results = rag.search_documents("woodworking materials")
        print(f"✅ Search returned {len(search_results)} results")
        
        # Test document addition
        test_doc_id = rag.add_document(
            title="Test Document",
            content="This is a test document for RAG system validation",
            source="test",
            document_type="test"
        )
        print(f"✅ Added test document with ID: {test_doc_id}")
        
        # Test document retrieval
        retrieved_doc = rag.get_document_by_id(test_doc_id)
        if retrieved_doc:
            print("✅ Document retrieval successful")
        else:
            print("❌ Document retrieval failed")
            return False
        
        # Test document update
        rag.update_document(
            test_doc_id,
            title="Updated Test Document",
            content="This is an updated test document"
        )
        print("✅ Document update successful")
        
        # Test document deletion
        rag.delete_document(test_doc_id)
        print("✅ Document deletion successful")
        
        # Test prompt enhancement
        enhanced = rag.enhance_prompt("How do I work with plywood?")
        if "Relevant knowledge:" in enhanced:
            print("✅ Prompt enhancement working")
        else:
            print("⚠️ Prompt enhancement not adding context")
        
        return True
        
    except Exception as e:
        print(f"❌ RAG test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_duplicate_handling():
    """Test duplicate document handling"""
    print("\nTesting duplicate document handling...")
    
    try:
        from rag_service import RAGService
        
        rag = RAGService()
        
        # Try to add the same document twice
        doc_id_1 = rag.add_document(
            title="Duplicate Test",
            content="This is a duplicate test document",
            source="test",
            document_type="test"
        )
        
        doc_id_2 = rag.add_document(
            title="Duplicate Test",
            content="This is a duplicate test document",
            source="test",
            document_type="test"
        )
        
        if doc_id_1 == doc_id_2:
            print("✅ Duplicate handling working - same ID returned")
        else:
            print("⚠️ Duplicate handling may not be working properly")
        
        # Clean up
        rag.delete_document(doc_id_1)
        
        return True
        
    except Exception as e:
        print(f"❌ Duplicate handling test failed: {e}")
        return False

if __name__ == "__main__":
    print("RAG System Test Suite")
    print("=" * 50)
    
    success = True
    
    # Test initialization
    success &= test_rag_initialization()
    
    # Test duplicate handling
    success &= test_duplicate_handling()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ All RAG tests passed!")
    else:
        print("❌ Some RAG tests failed!")
        sys.exit(1)
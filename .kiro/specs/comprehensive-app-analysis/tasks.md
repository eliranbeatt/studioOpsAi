# Implementation Plan - Critical Bug Fixes

Based on comprehensive codebase analysis, these are the confirmed critical issues that need immediate fixing:


- [-] 1. Fix API Server Dependency and Connectivity Issues
  - Resolve WeasyPrint and instructor dependency issues preventing main API from starting
  - Consolidate three API entry points into one working unified server
  - Fix database schema ID type mismatches causing 500 errors on /projects endpoint
  - Ensure frontend can successfully connect to all API endpoints
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ] 1.1 Fix API server dependency issues
  - Install or make optional WeasyPrint dependencies for Windows
  - Make instructor router optional when dependencies are missing
  - Create unified API server that starts successfully
  - Test all API endpoints return correct responses
  - _Requirements: 1.1, 1.2, 1.4_

- [ ] 1.2 Fix database schema ID type mismatches
  - Update minimal_api.py to handle UUID primary keys correctly
  - Fix projects endpoint to return proper UUID strings
  - Ensure all CRUD operations work with correct ID types
  - Test project creation, retrieval, update, and deletion
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [ ] 1.3 Fix frontend-backend connectivity
  - Verify API endpoints work with frontend API client
  - Fix any CORS or request format issues
  - Test project management from web interface
  - Ensure error handling works correctly
  - _Requirements: 1.3, 1.5, 2.5_

- [ ] 2. Implement Missing Trello MCP Integration
  - Create Trello MCP server implementation in apps/trello-mcp
  - Implement task export functionality to Trello boards
  - Add Trello board creation and management
  - Test end-to-end task export workflow
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ] 2.1 Create Trello MCP server structure
  - Set up basic MCP server in apps/trello-mcp directory
  - Implement Trello API client with authentication
  - Create board and card management functions
  - Add proper error handling and logging
  - _Requirements: 9.2, 9.3, 9.4_

- [ ] 2.2 Implement task export functionality
  - Create task-to-Trello card mapping logic
  - Implement project-to-board creation
  - Add task status synchronization
  - Test with real Trello API credentials
  - _Requirements: 9.1, 9.5_

- [ ] 3. Fix AI Services and RAG System Issues
  - Resolve RAG system duplicate key errors on startup
  - Fix LLM service to use real OpenAI integration
  - Ensure chat functionality works end-to-end
  - Test AI responses and memory persistence
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 3.1 Fix RAG system initialization issues
  - Resolve duplicate key constraint violations
  - Implement proper document deduplication
  - Fix ChromaDB collection initialization
  - Test document upload and retrieval
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 3.2 Enable real OpenAI integration
  - Fix OpenAI client initialization with proper API key
  - Remove fallback mode and enable real AI responses
  - Test chat functionality with context and memory
  - Verify conversation persistence works
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ] 4. Comprehensive Testing and Validation
  - Create automated tests for all fixed functionality
  - Test complete user workflows end-to-end
  - Verify all critical issues are resolved
  - Document any remaining known issues
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ] 4.1 Test API functionality
  - Write integration tests for all API endpoints
  - Test project CRUD operations work correctly
  - Verify vendor and material management works
  - Test chat and AI functionality
  - _Requirements: 10.2, 10.5_

- [ ] 4.2 Test Trello integration
  - Test task export to Trello boards
  - Verify board creation works
  - Test task status synchronization
  - Validate error handling for API failures
  - _Requirements: 10.3, 10.5_

- [ ] 4.3 Test frontend integration
  - Test web app can load and display projects
  - Verify project creation from frontend works
  - Test chat interface functionality
  - Validate error handling and user feedback
  - _Requirements: 10.3, 10.4, 10.5_
// Test frontend API integration using actual frontend code
import { checkConnection, projectsApi, API_BASE_URL } from './apps/web/src/lib/api.ts';

async function testFrontendApiIntegration() {
  console.log('Testing Frontend API Integration...');
  console.log('API Base URL:', API_BASE_URL);
  
  try {
    // Test connection check function
    console.log('\n1. Testing connection check function...');
    const isConnected = await checkConnection();
    console.log('Connection check result:', isConnected ? '✅ Connected' : '❌ Not connected');
    
    // Test projects API
    console.log('\n2. Testing projects API...');
    const projectsResponse = await projectsApi.getAll();
    console.log('✅ Projects loaded:', projectsResponse.data.length, 'projects');
    console.log('First project:', projectsResponse.data[0]?.name || 'No projects');
    
    // Test error handling
    console.log('\n3. Testing error handling...');
    try {
      await projectsApi.getById('non-existent-id');
    } catch (error) {
      console.log('✅ Error handling working:', error.message);
    }
    
    return true;
  } catch (error) {
    console.error('❌ Frontend API integration failed:', error);
    return false;
  }
}

// Run the test
testFrontendApiIntegration().then(success => {
  console.log('\n=== Frontend API Integration Test Results ===');
  console.log('Status:', success ? '✅ SUCCESS' : '❌ FAILED');
});
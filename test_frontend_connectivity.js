// Test script to verify frontend-backend connectivity
const API_BASE_URL = 'http://localhost:8000';

async function testApiConnection() {
  console.log('Testing API connectivity...');
  
  try {
    // Test health endpoint
    console.log('1. Testing health endpoint...');
    const healthResponse = await fetch(`${API_BASE_URL}/api/health`);
    const healthData = await healthResponse.json();
    console.log('✅ Health check:', healthData);
    
    // Test projects endpoint
    console.log('2. Testing projects endpoint...');
    const projectsResponse = await fetch(`${API_BASE_URL}/projects`);
    if (projectsResponse.ok) {
      const projectsData = await projectsResponse.json();
      console.log('✅ Projects endpoint working, count:', projectsData.length);
    } else {
      console.log('❌ Projects endpoint failed:', projectsResponse.status, projectsResponse.statusText);
    }
    
    // Test CORS headers
    console.log('3. Testing CORS headers...');
    const corsResponse = await fetch(`${API_BASE_URL}/projects`, {
      method: 'OPTIONS'
    });
    console.log('✅ CORS preflight status:', corsResponse.status);
    
    return true;
  } catch (error) {
    console.error('❌ API connection failed:', error);
    return false;
  }
}

// Run the test
testApiConnection().then(success => {
  console.log('\n=== Test Results ===');
  console.log('API Connection:', success ? '✅ SUCCESS' : '❌ FAILED');
});
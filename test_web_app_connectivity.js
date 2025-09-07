// Test web app connectivity using Node.js fetch
const API_BASE_URL = 'http://localhost:8000';

// Simulate the frontend's checkConnection function
async function checkConnection() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/health`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    return response.ok;
  } catch (error) {
    console.error('API connection check failed:', error);
    return false;
  }
}

// Simulate the frontend's projectsApi.getAll function
async function getProjects() {
  try {
    const response = await fetch(`${API_BASE_URL}/projects`, {
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include'
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    return { data, status: response.status };
  } catch (error) {
    throw error;
  }
}

async function testWebAppConnectivity() {
  console.log('=== Testing Web App Connectivity ===');
  console.log('API Base URL:', API_BASE_URL);
  
  let allTestsPassed = true;
  
  // Test 1: API connection check
  console.log('\n1. Testing API connection check...');
  try {
    const isConnected = await checkConnection();
    if (isConnected) {
      console.log('✅ API connection check: PASSED');
    } else {
      console.log('❌ API connection check: FAILED');
      allTestsPassed = false;
    }
  } catch (error) {
    console.log('❌ API connection check: ERROR -', error.message);
    allTestsPassed = false;
  }
  
  // Test 2: Project loading
  console.log('\n2. Testing project loading...');
  try {
    const projectsResponse = await getProjects();
    console.log('✅ Project loading: PASSED');
    console.log('   - Projects count:', projectsResponse.data.length);
    console.log('   - Response status:', projectsResponse.status);
    if (projectsResponse.data.length > 0) {
      console.log('   - First project:', projectsResponse.data[0].name);
    }
  } catch (error) {
    console.log('❌ Project loading: FAILED -', error.message);
    allTestsPassed = false;
  }
  
  // Test 3: CORS validation
  console.log('\n3. Testing CORS handling...');
  try {
    const corsResponse = await fetch(`${API_BASE_URL}/projects`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Origin': 'http://localhost:3000'
      }
    });
    
    if (corsResponse.ok) {
      console.log('✅ CORS handling: PASSED');
    } else {
      console.log('❌ CORS handling: FAILED - Status:', corsResponse.status);
      allTestsPassed = false;
    }
  } catch (error) {
    console.log('❌ CORS handling: ERROR -', error.message);
    allTestsPassed = false;
  }
  
  // Test 4: Error handling
  console.log('\n4. Testing error handling...');
  try {
    const errorResponse = await fetch(`${API_BASE_URL}/projects/non-existent-id`, {
      headers: {
        'Content-Type': 'application/json',
      }
    });
    
    if (errorResponse.status === 404) {
      console.log('✅ Error handling: PASSED (404 for non-existent resource)');
    } else {
      console.log('⚠️  Error handling: Unexpected status -', errorResponse.status);
    }
  } catch (error) {
    console.log('❌ Error handling: ERROR -', error.message);
    allTestsPassed = false;
  }
  
  console.log('\n=== Test Summary ===');
  console.log('Overall Status:', allTestsPassed ? '✅ ALL TESTS PASSED' : '❌ SOME TESTS FAILED');
  
  return allTestsPassed;
}

// Run the test
testWebAppConnectivity();
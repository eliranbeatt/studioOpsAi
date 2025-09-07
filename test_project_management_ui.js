// Test project management UI functionality
const API_BASE_URL = 'http://localhost:8000';

// Test data for project creation
const testProject = {
  name: 'Test Project UI',
  client_name: 'Test Client',
  status: 'draft',
  start_date: '2025-01-01',
  due_date: '2025-12-31',
  budget_planned: 50000
};

async function testProjectManagementUI() {
  console.log('=== Testing Project Management UI ===');
  
  let allTestsPassed = true;
  let createdProjectId = null;
  
  // Test 1: Project creation through API (simulating form submission)
  console.log('\n1. Testing project creation...');
  try {
    const createResponse = await fetch(`${API_BASE_URL}/projects`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(testProject)
    });
    
    if (createResponse.ok) {
      const createdProject = await createResponse.json();
      createdProjectId = createdProject.id;
      console.log('✅ Project creation: PASSED');
      console.log('   - Project ID:', createdProject.id);
      console.log('   - Project name:', createdProject.name);
    } else {
      const errorData = await createResponse.json();
      console.log('❌ Project creation: FAILED -', createResponse.status, errorData);
      allTestsPassed = false;
    }
  } catch (error) {
    console.log('❌ Project creation: ERROR -', error.message);
    allTestsPassed = false;
  }
  
  // Test 2: Project list retrieval
  console.log('\n2. Testing project list display...');
  try {
    const listResponse = await fetch(`${API_BASE_URL}/projects`);
    
    if (listResponse.ok) {
      const projects = await listResponse.json();
      console.log('✅ Project list display: PASSED');
      console.log('   - Total projects:', projects.length);
      
      // Find our test project
      const testProjectInList = projects.find(p => p.id === createdProjectId);
      if (testProjectInList) {
        console.log('   - Test project found in list: ✅');
      } else {
        console.log('   - Test project NOT found in list: ❌');
        allTestsPassed = false;
      }
    } else {
      console.log('❌ Project list display: FAILED -', listResponse.status);
      allTestsPassed = false;
    }
  } catch (error) {
    console.log('❌ Project list display: ERROR -', error.message);
    allTestsPassed = false;
  }
  
  // Test 3: Project editing (if project was created)
  if (createdProjectId) {
    console.log('\n3. Testing project editing...');
    try {
      const updatedData = {
        ...testProject,
        name: 'Updated Test Project UI',
        client_name: 'Updated Test Client',
        budget_planned: 75000
      };
      
      const updateResponse = await fetch(`${API_BASE_URL}/projects/${createdProjectId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updatedData)
      });
      
      if (updateResponse.ok) {
        const updatedProject = await updateResponse.json();
        console.log('✅ Project editing: PASSED');
        console.log('   - Updated name:', updatedProject.name);
        console.log('   - Updated budget:', updatedProject.budget_planned);
      } else {
        const errorData = await updateResponse.json();
        console.log('❌ Project editing: FAILED -', updateResponse.status, errorData);
        allTestsPassed = false;
      }
    } catch (error) {
      console.log('❌ Project editing: ERROR -', error.message);
      allTestsPassed = false;
    }
  }
  
  // Test 4: Form validation (simulating invalid data)
  console.log('\n4. Testing form validation...');
  try {
    const invalidProject = {
      name: '', // Empty name should fail validation
      client_name: 'Test Client',
      status: 'invalid_status'
    };
    
    const validationResponse = await fetch(`${API_BASE_URL}/projects`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(invalidProject)
    });
    
    if (validationResponse.status === 422) {
      console.log('✅ Form validation: PASSED (422 validation error returned)');
      const errorData = await validationResponse.json();
      console.log('   - Validation errors detected:', errorData.detail?.length || 'Yes');
    } else {
      console.log('❌ Form validation: FAILED - Expected 422, got', validationResponse.status);
      allTestsPassed = false;
    }
  } catch (error) {
    console.log('❌ Form validation: ERROR -', error.message);
    allTestsPassed = false;
  }
  
  // Test 5: Project deletion (cleanup)
  if (createdProjectId) {
    console.log('\n5. Testing project deletion...');
    try {
      const deleteResponse = await fetch(`${API_BASE_URL}/projects/${createdProjectId}`, {
        method: 'DELETE'
      });
      
      if (deleteResponse.ok) {
        console.log('✅ Project deletion: PASSED');
        
        // Verify project is actually deleted
        const verifyResponse = await fetch(`${API_BASE_URL}/projects/${createdProjectId}`);
        if (verifyResponse.status === 404) {
          console.log('   - Project successfully removed from database: ✅');
        } else {
          console.log('   - Project still exists after deletion: ❌');
          allTestsPassed = false;
        }
      } else {
        console.log('❌ Project deletion: FAILED -', deleteResponse.status);
        allTestsPassed = false;
      }
    } catch (error) {
      console.log('❌ Project deletion: ERROR -', error.message);
      allTestsPassed = false;
    }
  }
  
  // Test 6: Error handling for non-existent project
  console.log('\n6. Testing error handling...');
  try {
    const nonExistentResponse = await fetch(`${API_BASE_URL}/projects/non-existent-id`);
    
    if (nonExistentResponse.status === 404 || nonExistentResponse.status === 422) {
      console.log('✅ Error handling: PASSED (proper error status for non-existent project)');
    } else {
      console.log('❌ Error handling: FAILED - Unexpected status:', nonExistentResponse.status);
      allTestsPassed = false;
    }
  } catch (error) {
    console.log('❌ Error handling: ERROR -', error.message);
    allTestsPassed = false;
  }
  
  console.log('\n=== Project Management UI Test Summary ===');
  console.log('Overall Status:', allTestsPassed ? '✅ ALL TESTS PASSED' : '❌ SOME TESTS FAILED');
  
  return allTestsPassed;
}

// Run the test
testProjectManagementUI();
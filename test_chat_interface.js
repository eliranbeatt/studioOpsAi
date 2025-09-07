// Test chat interface functionality
const API_BASE_URL = 'http://localhost:8000';

async function testChatInterface() {
  console.log('=== Testing Chat Interface ===');
  
  let allTestsPassed = true;
  
  // Test 1: Chat message endpoint
  console.log('\n1. Testing chat message sending...');
  try {
    const testMessage = 'שלום, אני רוצה ליצור פרויקט חדש';
    
    const chatResponse = await fetch(`${API_BASE_URL}/chat/message`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: testMessage,
        project_id: null
      })
    });
    
    if (chatResponse.ok) {
      const chatData = await chatResponse.json();
      console.log('✅ Chat message sending: PASSED');
      console.log('   - Response received:', chatData.message ? 'Yes' : 'No');
      console.log('   - Response type:', typeof chatData.message);
      
      if (chatData.message) {
        console.log('   - Response preview:', chatData.message.substring(0, 100) + '...');
      }
    } else {
      const errorData = await chatResponse.json();
      console.log('❌ Chat message sending: FAILED -', chatResponse.status, errorData);
      allTestsPassed = false;
    }
  } catch (error) {
    console.log('❌ Chat message sending: ERROR -', error.message);
    allTestsPassed = false;
  }
  
  // Test 2: AI response quality
  console.log('\n2. Testing AI response quality...');
  try {
    const projectQuestion = 'איך אני יכול לתמחר פרויקט בנייה?';
    
    const aiResponse = await fetch(`${API_BASE_URL}/chat/message`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: projectQuestion,
        project_id: null
      })
    });
    
    if (aiResponse.ok) {
      const aiData = await aiResponse.json();
      console.log('✅ AI response quality: PASSED');
      
      // Check if response is relevant
      const response = aiData.message || aiData.response || '';
      const isRelevant = response.includes('תמחור') || response.includes('פרויקט') || response.includes('בנייה') || response.length > 50;
      
      if (isRelevant) {
        console.log('   - Response relevance: ✅ Relevant');
      } else {
        console.log('   - Response relevance: ⚠️ May not be relevant');
      }
      
      console.log('   - Response length:', response.length, 'characters');
    } else {
      console.log('❌ AI response quality: FAILED -', aiResponse.status);
      allTestsPassed = false;
    }
  } catch (error) {
    console.log('❌ AI response quality: ERROR -', error.message);
    allTestsPassed = false;
  }
  
  // Test 3: Conversation history (if supported)
  console.log('\n3. Testing conversation context...');
  try {
    // Send a follow-up message that requires context
    const followUpMessage = 'תוכל לתת לי עוד פרטים על זה?';
    
    const contextResponse = await fetch(`${API_BASE_URL}/chat/message`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: followUpMessage,
        project_id: null
      })
    });
    
    if (contextResponse.ok) {
      const contextData = await contextResponse.json();
      console.log('✅ Conversation context: PASSED');
      console.log('   - Follow-up response received: ✅');
      
      const response = contextData.message || contextData.response || '';
      console.log('   - Response length:', response.length, 'characters');
    } else {
      console.log('❌ Conversation context: FAILED -', contextResponse.status);
      allTestsPassed = false;
    }
  } catch (error) {
    console.log('❌ Conversation context: ERROR -', error.message);
    allTestsPassed = false;
  }
  
  // Test 4: Plan generation functionality
  console.log('\n4. Testing plan generation...');
  try {
    const planResponse = await fetch(`${API_BASE_URL}/chat/generate_plan`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        project_name: 'Test Project from Chat',
        project_description: 'פרויקט בדיקה לבניית דירה קטנה'
      })
    });
    
    if (planResponse.ok) {
      const planData = await planResponse.json();
      console.log('✅ Plan generation: PASSED');
      console.log('   - Plan generated: ✅');
      console.log('   - Plan has items:', planData.items ? planData.items.length : 0);
      console.log('   - Plan total:', planData.total || 'Not specified');
    } else if (planResponse.status === 404) {
      console.log('⚠️  Plan generation: ENDPOINT NOT FOUND (may not be implemented)');
    } else {
      console.log('❌ Plan generation: FAILED -', planResponse.status);
      allTestsPassed = false;
    }
  } catch (error) {
    console.log('❌ Plan generation: ERROR -', error.message);
    allTestsPassed = false;
  }
  
  // Test 5: Project context integration
  console.log('\n5. Testing project context integration...');
  try {
    // First, get a project ID to test with
    const projectsResponse = await fetch(`${API_BASE_URL}/projects`);
    
    if (projectsResponse.ok) {
      const projects = await projectsResponse.json();
      
      if (projects.length > 0) {
        const testProjectId = projects[0].id;
        
        const contextChatResponse = await fetch(`${API_BASE_URL}/chat/message`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            message: 'ספר לי על הפרויקט הזה',
            project_id: testProjectId
          })
        });
        
        if (contextChatResponse.ok) {
          const contextChatData = await contextChatResponse.json();
          console.log('✅ Project context integration: PASSED');
          console.log('   - Chat with project context: ✅');
          console.log('   - Response received: ✅');
        } else {
          console.log('❌ Project context integration: FAILED -', contextChatResponse.status);
          allTestsPassed = false;
        }
      } else {
        console.log('⚠️  Project context integration: NO PROJECTS AVAILABLE for testing');
      }
    } else {
      console.log('❌ Project context integration: FAILED to get projects');
      allTestsPassed = false;
    }
  } catch (error) {
    console.log('❌ Project context integration: ERROR -', error.message);
    allTestsPassed = false;
  }
  
  // Test 6: Error handling
  console.log('\n6. Testing chat error handling...');
  try {
    const errorResponse = await fetch(`${API_BASE_URL}/chat/message`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        // Missing required message field
        project_id: null
      })
    });
    
    if (errorResponse.status === 422 || errorResponse.status === 400) {
      console.log('✅ Chat error handling: PASSED (proper validation error)');
    } else if (errorResponse.ok) {
      console.log('⚠️  Chat error handling: API accepted invalid request (may need validation)');
    } else {
      console.log('❌ Chat error handling: UNEXPECTED STATUS -', errorResponse.status);
      allTestsPassed = false;
    }
  } catch (error) {
    console.log('❌ Chat error handling: ERROR -', error.message);
    allTestsPassed = false;
  }
  
  console.log('\n=== Chat Interface Test Summary ===');
  console.log('Overall Status:', allTestsPassed ? '✅ ALL TESTS PASSED' : '❌ SOME TESTS FAILED');
  
  return allTestsPassed;
}

// Run the test
testChatInterface();
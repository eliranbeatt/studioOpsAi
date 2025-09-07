// Test Next.js server startup and connectivity
const { spawn } = require('child_process');
const path = require('path');

async function testNextJSServer() {
  console.log('=== Testing Next.js Server ===');
  
  // Start Next.js server
  console.log('Starting Next.js development server...');
  const nextProcess = spawn('npm', ['run', 'dev'], {
    cwd: path.join(__dirname, 'apps', 'web'),
    stdio: 'pipe',
    shell: true
  });
  
  let serverReady = false;
  let serverError = null;
  
  // Listen for server output
  nextProcess.stdout.on('data', (data) => {
    const output = data.toString();
    console.log('Next.js:', output.trim());
    
    if (output.includes('Ready in') || output.includes('Local:')) {
      serverReady = true;
    }
  });
  
  nextProcess.stderr.on('data', (data) => {
    const error = data.toString();
    console.error('Next.js Error:', error.trim());
    serverError = error;
  });
  
  // Wait for server to be ready
  await new Promise((resolve) => {
    const checkReady = setInterval(() => {
      if (serverReady || serverError) {
        clearInterval(checkReady);
        resolve();
      }
    }, 1000);
    
    // Timeout after 30 seconds
    setTimeout(() => {
      clearInterval(checkReady);
      resolve();
    }, 30000);
  });
  
  if (serverError) {
    console.log('❌ Next.js server failed to start:', serverError);
    nextProcess.kill();
    return false;
  }
  
  if (!serverReady) {
    console.log('❌ Next.js server timeout');
    nextProcess.kill();
    return false;
  }
  
  console.log('✅ Next.js server started successfully');
  
  // Test server connectivity
  console.log('\nTesting server connectivity...');
  try {
    const response = await fetch('http://localhost:3000');
    if (response.ok) {
      console.log('✅ Next.js app accessible - Status:', response.status);
      console.log('✅ Content-Type:', response.headers.get('content-type'));
    } else {
      console.log('❌ Next.js app returned error status:', response.status);
    }
  } catch (error) {
    console.log('❌ Failed to connect to Next.js app:', error.message);
  }
  
  // Clean up
  console.log('\nStopping Next.js server...');
  nextProcess.kill();
  
  return true;
}

// Run the test
testNextJSServer().catch(console.error);
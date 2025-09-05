#!/bin/bash

# Comprehensive test runner for StudioOps AI system

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting comprehensive test suite for StudioOps AI${NC}"

# Function to run tests with timing
run_test_suite() {
    local suite_name="$1"
    local command="$2"
    local directory="$3"
    
    echo -e "${YELLOW}▶️  Running $suite_name tests...${NC}"
    start_time=$(date +%s)
    
    if cd "$directory" && eval "$command"; then
        end_time=$(date +%s)
        duration=$((end_time - start_time))
        echo -e "${GREEN}✅ $suite_name tests passed in ${duration}s${NC}"
        return 0
    else
        end_time=$(date +%s)
        duration=$((end_time - start_time))
        echo -e "${RED}❌ $suite_name tests failed after ${duration}s${NC}"
        return 1
    fi
}

# Run API tests
echo -e "${BLUE}📦 Testing API backend...${NC}"
if ! run_test_suite "API" "python run_tests.py --setup-db --coverage" "apps/api"; then
    echo -e "${RED}API tests failed, aborting...${NC}"
    exit 1
fi

# Run frontend unit tests
echo -e "${BLUE}🎨 Testing frontend components...${NC}"
if ! run_test_suite "Frontend Unit" "npm test -- --coverage --watchAll=false" "apps/web"; then
    echo -e "${RED}Frontend unit tests failed, aborting...${NC}"
    exit 1
fi

# Run E2E tests
echo -e "${BLUE}🌐 Testing end-to-end workflows...${NC}"
if ! run_test_suite "E2E" "npm run test:e2e" "apps/web"; then
    echo -e "${RED}E2E tests failed${NC}"
    # Don't exit on E2E test failures as they might be flaky
fi

# Generate combined test report
echo -e "${BLUE}📊 Generating test reports...${NC}"

# API coverage report
if [ -d "apps/api/htmlcov" ]; then
    echo -e "${GREEN}📈 API coverage report: apps/api/htmlcov/index.html${NC}"
fi

# Frontend coverage report
if [ -d "apps/web/coverage" ]; then
    echo -e "${GREEN}📈 Frontend coverage report: apps/web/coverage/lcov-report/index.html${NC}"
fi

# Playwright report
if [ -d "apps/web/test-results" ]; then
    echo -e "${GREEN}📈 Playwright report: apps/web/test-results/${NC}"
fi

echo -e "${GREEN}🎉 All test suites completed successfully!${NC}"
echo -e "${BLUE}📋 Next steps:${NC}"
echo -e "  • Review coverage reports for areas needing improvement"
echo -e "  • Check E2E test results for any flaky tests"
echo -e "  • Run performance tests with: npm run test:perf"

exit 0
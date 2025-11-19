#!/bin/bash

# Complete Branch Verification Script
# Checks all essential files for the bot

echo "=========================================="
echo "Complete Branch Verification"
echo "=========================================="
echo ""

cd "$(dirname "$0")"

ERRORS=0
WARNINGS=0

check_file() {
    if [ -f "$1" ]; then
        echo "✅ $1"
        return 0
    else
        echo "❌ $1 - MISSING"
        ((ERRORS++))
        return 1
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        echo "✅ $1/ (directory exists)"
        return 0
    else
        echo "❌ $1/ - MISSING"
        ((ERRORS++))
        return 1
    fi
}

echo "=== BACKEND FILES ==="
check_file "backend/app/config.yml"
check_file "backend/app/domain.yml"
check_file "backend/app/endpoints.yml"
check_file "backend/app/credentials.yml"
check_file "backend/app/data/nlu.yml"
check_file "backend/app/data/stories.yml"
check_file "backend/app/data/rules.yml"
check_file "backend/app/actions/actions.py"
check_file "backend/app/actions/aws_intelligence.py"
check_file "backend/app/actions/rag_system.py"
check_file "backend/app/requirements.txt"
check_file "backend/app/Dockerfile"
check_file "backend/wrapper_server.py"
check_file "backend/requirements.txt"
check_file "backend/.env.template"

echo ""
echo "=== FRONTEND FILES ==="
check_dir "frontend"
check_file "frontend/package.json"
check_file "frontend/src/App.tsx"
check_file "frontend/src/components/Chat.tsx"
check_file "frontend/src/components/MessageItems.tsx"
check_file "frontend/src/api/index.ts"
check_file "frontend/src/api/axiosConfig.ts"
check_dir "frontend/src/UI"

echo ""
echo "=== SETUP & SCRIPTS ==="
check_file "setup_backend.sh"
check_file "setup_and_run.sh"

echo ""
echo "=== DOCKER FILES ==="
check_file "backend/app/Dockerfile"
check_file "frontend/Dockerfile" || echo "⚠️  frontend/Dockerfile - Optional"

echo ""
echo "=== DEPLOYMENT SCRIPTS ==="
check_file "backend/deploy_to_aws.sh" || echo "⚠️  deploy_to_aws.sh - Optional"
check_file "backend/FINAL_DEPLOY.sh" || echo "⚠️  FINAL_DEPLOY.sh - Optional"

echo ""
echo "=== DOCUMENTATION ==="
check_file "README.md"
check_file "DEVELOPER_SETUP_GUIDE.md" || echo "⚠️  DEVELOPER_SETUP_GUIDE.md - Optional"
check_file "DEVELOPER_QUICK_START.md" || echo "⚠️  DEVELOPER_QUICK_START.md - Optional"

echo ""
echo "=== CONFIGURATION ==="
check_file ".gitignore"
check_file "backend/.env.template"

echo ""
echo "=========================================="
echo "Summary:"
echo "  Errors: $ERRORS"
echo "  Warnings: $WARNINGS"
echo "=========================================="

if [ $ERRORS -eq 0 ]; then
    echo "✅ All essential files present!"
    exit 0
else
    echo "❌ Some essential files are missing"
    exit 1
fi


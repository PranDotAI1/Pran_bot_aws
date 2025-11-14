#!/bin/bash

# Repository Verification Script
# Checks all files before pushing to GitHub

echo "=========================================="
echo "New Pran Bot AWS - Repository Verification"
echo "=========================================="
echo ""

ERRORS=0
WARNINGS=0

# Check for emojis in code files (exclude domain.yml which may have user-facing responses)
echo "1. Checking for emojis in code files..."
# Use Python to check for actual emojis (grep may have issues with unicode)
EMOJI_FILES=$(python3 -c "
import re
import os
emoji_pattern = re.compile(r'[✅❌⚠️🔌📊🗄️📦🔍💡🚀🎯📝👩🏥💰📋📞🌱📅💳👥🏃📱]')
files = []
for root, dirs, filenames in os.walk('.'):
    for f in filenames:
        if f.endswith(('.py', '.yml', '.yaml')) and f != 'domain.yml':
            path = os.path.join(root, f)
            try:
                with open(path, 'r', encoding='utf-8') as file:
                    if emoji_pattern.search(file.read()):
                        files.append(path)
            except:
                pass
print('\n'.join(files))
" 2>/dev/null)
if [ -n "$EMOJI_FILES" ]; then
    echo "   ❌ ERROR: Found emojis in code files:"
    echo "$EMOJI_FILES"
    ERRORS=$((ERRORS + 1))
else
    echo "   ✅ No emojis found in code files"
    # Check domain.yml separately (may have user-facing responses)
    DOMAIN_EMOJIS=$(grep -c "[✅❌⚠️🔌📊🗄️📦🔍💡🚀🎯📝👩🏥💰📋📞🌱📅💳👥🏃📱]" backend/app/domain.yml 2>/dev/null || echo "0")
    if [ "$DOMAIN_EMOJIS" -gt 0 ]; then
        echo "   ⚠️  WARNING: Found emojis in domain.yml (training data - may be acceptable)"
        WARNINGS=$((WARNINGS + 1))
    fi
fi
echo ""

# Check for hardcoded passwords
echo "2. Checking for hardcoded passwords..."
PASSWORD_FILES=$(grep -r "Pranchatbot123\|yopOQY7bZlCkRyxH4UMe11rkg" --include="*.py" backend/ 2>/dev/null)
if [ -n "$PASSWORD_FILES" ]; then
    echo "   ❌ ERROR: Found hardcoded passwords:"
    echo "$PASSWORD_FILES"
    ERRORS=$((ERRORS + 1))
else
    echo "   ✅ No hardcoded passwords found"
fi
echo ""

# Check for hardcoded IPs (except localhost)
echo "3. Checking for hardcoded IP addresses..."
IP_FILES=$(grep -r "13\.201\.185\|database-1\.cluster\|pran-chatbot-postgres" --include="*.py" backend/ 2>/dev/null)
if [ -n "$IP_FILES" ]; then
    echo "   ❌ ERROR: Found hardcoded IPs:"
    echo "$IP_FILES"
    ERRORS=$((ERRORS + 1))
else
    echo "   ✅ No hardcoded IPs found"
fi
echo ""

# Check essential files exist
echo "4. Checking essential files..."
ESSENTIAL_FILES=(
    "backend/wrapper_server.py"
    "backend/app/actions/actions.py"
    "backend/app/actions/aws_intelligence.py"
    "backend/app/actions/rag_system.py"
    "backend/app/config.yml"
    "backend/app/domain.yml"
    "backend/app/endpoints.yml"
    "backend/app/Dockerfile"
    "Dockerfile.backend"
    "docker-compose.yml"
    ".env.template"
    ".gitignore"
    "README.md"
)

MISSING_FILES=()
for file in "${ESSENTIAL_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        MISSING_FILES+=("$file")
    fi
done

if [ ${#MISSING_FILES[@]} -gt 0 ]; then
    echo "   ❌ ERROR: Missing essential files:"
    printf "   - %s\n" "${MISSING_FILES[@]}"
    ERRORS=$((ERRORS + ${#MISSING_FILES[@]}))
else
    echo "   ✅ All essential files present"
fi
echo ""

# Check environment template
echo "5. Checking environment template..."
if [ -f ".env.template" ] || [ -f "deployment/config/.env.template" ]; then
    TEMPLATE_FILE=".env.template"
    if [ ! -f "$TEMPLATE_FILE" ]; then
        TEMPLATE_FILE="deployment/config/.env.template"
    fi
    REQUIRED_VARS=("MONGODB_URI" "AWS_REGION" "DB_HOST" "DB_PASSWORD")
    MISSING_VARS=()
    for var in "${REQUIRED_VARS[@]}"; do
        if ! grep -q "$var" "$TEMPLATE_FILE" 2>/dev/null; then
            MISSING_VARS+=("$var")
        fi
    done
    if [ ${#MISSING_VARS[@]} -gt 0 ]; then
        echo "   ⚠️  WARNING: Missing variables in template:"
        printf "   - %s\n" "${MISSING_VARS[@]}"
        WARNINGS=$((WARNINGS + ${#MISSING_VARS[@]}))
    else
        echo "   ✅ Environment template complete"
    fi
else
    echo "   ❌ ERROR: Environment template not found (.env.template or deployment/config/.env.template)"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Check Docker files
echo "6. Checking Docker configurations..."
DOCKER_FILES=("Dockerfile.backend" "backend/app/Dockerfile" "docker-compose.yml")
MISSING_DOCKER=()
for file in "${DOCKER_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        MISSING_DOCKER+=("$file")
    fi
done

if [ ${#MISSING_DOCKER[@]} -gt 0 ]; then
    echo "   ❌ ERROR: Missing Docker files:"
    printf "   - %s\n" "${MISSING_DOCKER[@]}"
    ERRORS=$((ERRORS + ${#MISSING_DOCKER[@]}))
else
    echo "   ✅ All Docker files present"
fi
echo ""

# Check Python syntax
echo "7. Checking Python syntax..."
PYTHON_FILES=$(find backend -name "*.py" -type f)
SYNTAX_ERRORS=0
for file in $PYTHON_FILES; do
    if ! python3 -m py_compile "$file" 2>/dev/null; then
        echo "   ❌ Syntax error in: $file"
        SYNTAX_ERRORS=$((SYNTAX_ERRORS + 1))
    fi
done

if [ $SYNTAX_ERRORS -eq 0 ]; then
    echo "   ✅ All Python files have valid syntax"
else
    echo "   ❌ Found $SYNTAX_ERRORS syntax errors"
    ERRORS=$((ERRORS + SYNTAX_ERRORS))
fi
echo ""

# Summary
echo "=========================================="
echo "Verification Summary"
echo "=========================================="
echo "Errors: $ERRORS"
echo "Warnings: $WARNINGS"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo "✅ Repository is ready to push!"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo "⚠️  Repository has warnings but is ready to push"
    exit 0
else
    echo "❌ Repository has errors. Please fix before pushing."
    exit 1
fi


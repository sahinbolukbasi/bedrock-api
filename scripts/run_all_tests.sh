#!/bin/bash
set -e

echo "========================================================"
echo "🚀 AWS BEDROCK AI GATEWAY - AUTOMATED TEST & QUALITY SUITE"
echo "========================================================"

WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$WORKSPACE_DIR"

echo ""
echo "📦 1. RUNNING BACKEND PYTEST SUITE..."
PYTHONPATH=backend ./venv/bin/pytest backend/tests/ -v --tb=short

echo ""
echo "🎨 2. VALIDATING FRONTEND NEXT.JS PRODUCTION BUILD..."
cd frontend
npm run build
cd "$WORKSPACE_DIR"

echo ""
echo "========================================================"
echo "✅ ALL AUTOMATED TESTS & BUILDS PASSED SUCCESSFULLY (100%)"
echo "========================================================"

#!/bin/bash
# 🧁 LabsBakery Core - Setup Script
# Run this script to set up the development environment

set -e

echo "🧁 LabsBakery Core - Setup"
echo "=========================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "✅ Created .env file (please review and update as needed)"
fi

# Create logs directory
echo ""
echo "Creating logs directory..."
mkdir -p logs

# Initialize database
echo ""
echo "Initializing database..."
python3 -c "from backend.database import init_db; init_db()"

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the application:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Run the application: uvicorn backend.main:app --reload"
echo "  3. Open browser: http://localhost:8000"
echo ""
echo "To view API documentation:"
echo "  - Swagger UI: http://localhost:8000/docs"
echo "  - ReDoc: http://localhost:8000/redoc"
echo ""

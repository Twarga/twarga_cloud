#!/usr/bin/env python3
"""
Twarga Cloud MVP - Setup Script
Sets up virtual environment and installs dependencies
"""

import os
import sys
import subprocess
import venv
from pathlib import Path
import shutil

def create_virtual_environment():
    """Create Python virtual environment"""
    print("🔧 Creating virtual environment...")
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("✅ Virtual environment already exists")
        return True
    
    try:
        venv.create(venv_path, with_pip=True)
        print("✅ Virtual environment created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to create virtual environment: {e}")
        return False

def get_venv_python():
    """Get the Python executable path in the virtual environment"""
    if sys.platform == "win32":
        return Path("venv/Scripts/python.exe")
    else:
        return Path("venv/bin/python")

def install_dependencies():
    """Install project dependencies"""
    print("📦 Installing dependencies...")
    venv_python = get_venv_python()
    
    if not venv_python.exists():
        print("❌ Virtual environment not found")
        return False
    
    try:
        # Upgrade pip
        subprocess.run([str(venv_python), "-m", "pip", "install", "--upgrade", "pip"], 
                      check=True, capture_output=True)
        
        # Install requirements
        subprocess.run([str(venv_python), "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def create_env_file():
    """Create .env file from example"""
    env_example = Path(".env.example")
    env_file = Path(".env")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    if env_example.exists():
        try:
            import shutil
            shutil.copy(env_example, env_file)
            print("✅ .env file created from example")
            print("⚠️  Please update the .env file with your configuration")
            return True
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")
            return False
    else:
        print("⚠️  .env.example not found, creating basic .env file")
        basic_env = """# Twarga Cloud MVP - Environment Configuration
APP_NAME="Twarga Cloud MVP"
DEBUG=True
SECRET_KEY="your-secret-key-here-change-in-production"
DATABASE_URL="sqlite:///./twarga_cloud.db"
"""
        try:
            with open(env_file, 'w') as f:
                f.write(basic_env)
            print("✅ Basic .env file created")
            return True
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")
            return False

def create_directories():
    """Create necessary directories"""
    directories = ["logs", "vms"]
    
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            try:
                dir_path.mkdir(exist_ok=True)
                print(f"✅ Created directory: {directory}")
            except Exception as e:
                print(f"❌ Failed to create directory {directory}: {e}")
                return False
        else:
            print(f"✅ Directory already exists: {directory}")
    
    return True

def detect_shell():
    """Detect the current shell type"""
    shell = os.environ.get('SHELL', '')
    if 'fish' in shell:
        return 'fish'
    elif 'bash' in shell or 'sh' in shell:
        return 'bash'
    elif 'zsh' in shell:
        return 'zsh'
    elif 'csh' in shell or 'tcsh' in shell:
        return 'csh'
    else:
        return 'unknown'

def get_activation_command():
    """Get the appropriate activation command based on shell and platform"""
    shell_type = detect_shell()
    
    if sys.platform == "win32":
        return "venv\\Scripts\\activate"
    else:
        if shell_type == 'fish':
            return "source venv/bin/activate.fish"
        elif shell_type == 'csh':
            return "source venv/bin/activate.csh"
        else:  # bash, zsh, or unknown
            return "source venv/bin/activate"

def print_next_steps():
    """Print next steps for the user"""
    shell_type = detect_shell()
    activation_cmd = get_activation_command()
    
    print("\n🎉 Setup completed successfully!")
    print(f"\n🐚 Detected shell: {shell_type}")
    print("\n� Next steps:")
    print("1. Update the .env file with your configuration")
    print("2. Activate the virtual environment:")
    print(f"   {activation_cmd}")
    print("3. Run the application:")
    print("   cd backend && python main.py")
    print("4. Open your browser and navigate to:")
    print("   http://localhost:8000")
    print("5. View API documentation at:")
    print("   http://localhost:8000/docs")
    
    # Print additional shell-specific instructions
    if shell_type == 'fish':
        print("\n🐠 Fish shell detected!")
        print("   If you encounter issues, you can also use:")
        print("   venv/bin/python -m pip install -r requirements.txt")
        print("   venv/bin/python backend/main.py")
    elif shell_type == 'unknown':
        print(f"\n⚠️  Unknown shell detected: {os.environ.get('SHELL', 'not set')}")
        print("   If the activation command doesn't work, try:")
        print("   source venv/bin/activate")
        print("   or run Python directly:")
        print("   venv/bin/python backend/main.py")

def main():
    """Main setup function"""
    print("🚀 Twarga Cloud MVP Setup")
    print("=" * 40)
    
    # Change to the correct directory if needed
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Create virtual environment
    if not create_virtual_environment():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Create .env file
    create_env_file()
    
    # Create necessary directories
    if not create_directories():
        sys.exit(1)
    
    # Print next steps
    print_next_steps()

if __name__ == "__main__":
    main()
"""
Setup Script for Plumbing Estimator
Creates necessary folders and __init__.py files
"""
import os

def create_directory_structure():
    """Create all necessary directories"""
    directories = [
        'database',
        'routes',
        'services',
        'templates',
        'middleware',
        'data',
        'uploads'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ Created directory: {directory}/")
    
    # Create __init__.py files for Python packages
    packages = ['database', 'routes', 'services', 'middleware']
    for package in packages:
        init_file = os.path.join(package, '__init__.py')
        if not os.path.exists(init_file):
            with open(init_file, 'w') as f:
                f.write(f'"""\n{package.capitalize()} package\n"""\n')
            print(f"✓ Created: {init_file}")

def main():
    print("=" * 60)
    print("Plumbing Estimator - Project Setup")
    print("=" * 60)
    print("\nCreating project structure...\n")
    
    create_directory_structure()
    
    print("\n" + "=" * 60)
    print("✓ Setup complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Make sure all Python files are in their correct folders")
    print("2. Make sure all HTML files are in the templates/ folder")
    print("3. Run: python app.py")
    print("=" * 60)

if __name__ == '__main__':
    main()
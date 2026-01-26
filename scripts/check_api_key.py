"""
Helper script to check and set API key.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Get project root
project_root = Path(__file__).parent.parent
env_file = project_root / ".env"

print("=" * 60)
print("API Key Checker")
print("=" * 60)
print(f"\nProject root: {project_root}")
print(f".env file path: {env_file}")
print(f".env file exists: {env_file.exists()}")

if env_file.exists():
    print(f"\n.env file contents:")
    print("-" * 60)
    with open(env_file, 'r', encoding='utf-8') as f:
        content = f.read()
        print(repr(content))  # Shows exact content including whitespace
        print("\nFormatted:")
        print(content)
    print("-" * 60)
    
    # Try to load it
    load_dotenv(env_file)
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if api_key:
        if api_key == "your_api_key_here":
            print("\nSTATUS: Still has placeholder!")
            print("Please replace 'your_api_key_here' with your actual API key")
        elif api_key.startswith("sk-ant-api03-"):
            print(f"\nSTATUS: Valid API key found!")
            print(f"Key starts with: {api_key[:20]}...")
            print(f"Key length: {len(api_key)} characters")
        else:
            print(f"\nSTATUS: API key found but format looks wrong")
            print(f"Key starts with: {api_key[:30]}...")
            print("Expected format: sk-ant-api03-...")
    else:
        print("\nSTATUS: No API key found in environment")
else:
    print("\n.env file not found! Creating template...")
    with open(env_file, 'w') as f:
        f.write("ANTHROPIC_API_KEY=your_api_key_here\n")
    print("Created .env file. Please add your API key.")

print("\n" + "=" * 60)

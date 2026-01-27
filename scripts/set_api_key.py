"""
Interactive script to set your API key.
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
env_file = project_root / ".env"

print("=" * 60)
print("Set Anthropic API Key")
print("=" * 60)

if len(sys.argv) > 1:
    api_key = sys.argv[1].strip()
else:
    print("\nPlease enter your Anthropic API key:")
    print("(It should start with 'sk-ant-api03-')")
    api_key = input("API Key: ").strip()

if not api_key:
    print("\nError: No API key provided")
    sys.exit(1)

if not api_key.startswith("sk-ant-api03-"):
    print(f"\nWarning: API key doesn't start with 'sk-ant-api03-'")
    print(f"Your key starts with: {api_key[:20]}...")
    response = input("Continue anyway? (y/n): ").strip().lower()
    if response != 'y':
        print("Cancelled.")
        sys.exit(1)

# Write to .env file
try:
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(f"ANTHROPIC_API_KEY={api_key}\n")
    
    print(f"\nSuccess! API key saved to: {env_file}")
    print(f"Key: {api_key[:20]}...{api_key[-10:]}")
    print("\nYou can now run: python scripts/quick_test.py")
except Exception as e:
    print(f"\nError saving API key: {e}")
    sys.exit(1)

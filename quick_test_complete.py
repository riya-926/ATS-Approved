"""
Quick test script for the complete rewrite system.
Run this with: python quick_test_complete.py
"""
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("ATS-Approved: Complete System Test")
print("=" * 80)
print()

# Check if files are provided
if len(sys.argv) >= 3:
    resume_path = sys.argv[1]
    jd_path = sys.argv[2]
else:
    print("Usage: python quick_test_complete.py <resume.docx> <job_description.txt>")
    print("\nOr run without arguments to test just the analysis features:")
    print("  python quick_test_complete.py")
    print()
    
    # Test just the analysis features
    print("Testing analysis features (no files needed)...")
    print()
    try:
        from scripts.test_new_features import test_bullet_analysis, test_length_analysis, test_imports
        
        test_imports()
        test_bullet_analysis()
        test_length_analysis()
        
        print("=" * 80)
        print("[SUCCESS] Analysis features work correctly!")
        print("=" * 80)
        print("\nTo test with real files, run:")
        print("  python quick_test_complete.py resume.docx job_description.txt")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

# Full test with files
print(f"Resume: {resume_path}")
print(f"Job Description: {jd_path}")
print()

try:
    from scripts.test_rewrite import main as test_rewrite_main
    
    # Override sys.argv for the test script
    original_argv = sys.argv
    sys.argv = ["test_rewrite.py", resume_path, jd_path]
    
    test_rewrite_main()
    
    sys.argv = original_argv
    
except FileNotFoundError as e:
    print(f"❌ File not found: {e}")
    print("\nMake sure the files exist:")
    print(f"  - Resume: {resume_path}")
    print(f"  - Job Description: {jd_path}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

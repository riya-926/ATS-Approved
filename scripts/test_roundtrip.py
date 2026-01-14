#!/usr/bin/env python3
"""
Standalone script to test the DOCX parse → edit → patch round-trip.

This script validates the core constraint: editing content without changing layout.

Usage:
    python scripts/test_roundtrip.py <path_to_resume.docx>
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.docx.parser import parse_docx
from app.docx.patcher import patch_docx
from app.models.content_unit import ContentUnit


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_roundtrip.py <path_to_resume.docx>")
        sys.exit(1)

    docx_path = Path(sys.argv[1])
    if not docx_path.exists():
        print(f"Error: File not found: {docx_path}")
        sys.exit(1)

    if not docx_path.suffix == ".docx":
        print(f"Error: File must be a .docx file: {docx_path}")
        sys.exit(1)

    print(f"Testing round-trip with: {docx_path}")
    print("-" * 60)

    # Step 1: Parse DOCX
    print("\n[1/3] Parsing DOCX...")
    try:
        parsed = parse_docx(docx_path)
        print(f"✓ Parsed {len(parsed.content_units)} content units")
        print(f"  Metadata: {parsed.metadata}")

        if not parsed.content_units:
            print("  ⚠ Warning: No content units found!")
            print("  Ensure the resume has Experience/Skills/Summary sections.")
            sys.exit(1)

        # Show first few units
        print("\n  First 3 content units:")
        for unit in parsed.content_units[:3]:
            print(f"    - {unit.id}: {unit.content[:60]}...")

    except Exception as e:
        print(f"✗ Error parsing: {e}")
        sys.exit(1)

    # Step 2: Edit one content unit
    print("\n[2/3] Editing first content unit...")
    first_unit = parsed.content_units[0]
    print(f"  Original: {first_unit.content[:60]}...")

    updated_units = []
    updated_unit = ContentUnit(
        id=first_unit.id,
        type=first_unit.type,
        content=first_unit.content + " [TESTED]",
        section_index=first_unit.section_index,
        paragraph_index=first_unit.paragraph_index,
        bullet_index=first_unit.bullet_index,
    )
    updated_units.append(updated_unit)
    print(f"  Updated: {updated_unit.content[:60]}...")

    # Keep all other units unchanged
    for unit in parsed.content_units[1:]:
        updated_units.append(unit)

    # Step 3: Apply edit back to DOCX
    print("\n[3/3] Patching DOCX...")
    output_path = docx_path.parent / f"{docx_path.stem}_patched.docx"

    try:
        success = patch_docx(docx_path, output_path, updated_units, parsed)
        if success:
            print(f"✓ Successfully patched: {output_path}")
            print("\n" + "=" * 60)
            print("Round-trip test completed!")
            print(f"\nCompare the original and patched files:")
            print(f"  Original: {docx_path}")
            print(f"  Patched:  {output_path}")
            print("\nVerify that:")
            print("  - Only the first content unit text changed")
            print("  - Layout, styles, and formatting are preserved")
            print("  - Document structure is unchanged")
        else:
            print("✗ Failed to patch document")
            sys.exit(1)

    except Exception as e:
        print(f"✗ Error patching: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()


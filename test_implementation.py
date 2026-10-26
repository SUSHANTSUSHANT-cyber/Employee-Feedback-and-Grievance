#!/usr/bin/env python3
"""
Test script to validate employeeCodeRequired implementation
Run from project root: python test_implementation.py
"""

import sys
sys.path.insert(0, 'api')

print("Testing employeeCodeRequired implementation...")
print("=" * 60)

# Test 1: Import models and schemas
print("\n1. Testing imports...")
try:
    from app.models import Category
    from app.schemas import CategoryIn, CategoryOut
    print("   ✓ Models and schemas import successfully")
except Exception as e:
    print(f"   ✗ Import error: {e}")
    sys.exit(1)

# Test 2: Create CategoryIn with employeeCodeRequired=True
print("\n2. Testing CategoryIn with employeeCodeRequired=True...")
try:
    category_true = CategoryIn(
        name='Salary',
        iconName='payments',
        colorHex='#173D72',
        displayOrder=1,
        email='salary@example.com',
        nameHi='वेतन',
        nameJa='給与',
        employeeCodeRequired=True
    )
    data = category_true.model_dump()
    assert data['employeeCodeRequired'] == True, "Expected True"
    print(f"   ✓ CategoryIn with employeeCodeRequired=True: {data}")
except Exception as e:
    print(f"   ✗ Error: {e}")
    sys.exit(1)

# Test 3: Create CategoryIn with employeeCodeRequired=False
print("\n3. Testing CategoryIn with employeeCodeRequired=False...")
try:
    category_false = CategoryIn(
        name='General',
        iconName='info',
        colorHex='#4CAF50',
        displayOrder=2,
        email='general@example.com',
        nameHi='सामान्य',
        nameJa='一般',
        employeeCodeRequired=False
    )
    data = category_false.model_dump()
    assert data['employeeCodeRequired'] == False, "Expected False"
    print(f"   ✓ CategoryIn with employeeCodeRequired=False: {data}")
except Exception as e:
    print(f"   ✗ Error: {e}")
    sys.exit(1)

# Test 4: Create CategoryIn without employeeCodeRequired (should default to False)
print("\n4. Testing CategoryIn without employeeCodeRequired (default)...")
try:
    category_default = CategoryIn(
        name='HR',
        iconName='people',
        colorHex='#FF9800',
        displayOrder=3,
        email='hr@example.com',
        nameHi='एचआर',
        nameJa='人事'
    )
    data = category_default.model_dump()
    assert data['employeeCodeRequired'] == False, "Expected False (default)"
    print(f"   ✓ CategoryIn default employeeCodeRequired=False: {data}")
except Exception as e:
    print(f"   ✗ Error: {e}")
    sys.exit(1)

# Test 5: Check field types
print("\n5. Testing field types...")
try:
    assert isinstance(category_true.employeeCodeRequired, bool), "Should be bool"
    assert isinstance(category_false.employeeCodeRequired, bool), "Should be bool"
    assert isinstance(category_default.employeeCodeRequired, bool), "Should be bool"
    print("   ✓ All employeeCodeRequired values are boolean type")
except Exception as e:
    print(f"   ✗ Error: {e}")
    sys.exit(1)

# Test 6: Test JSON serialization
print("\n6. Testing JSON serialization...")
try:
    import json
    json_str = category_true.model_dump_json()
    json_data = json.loads(json_str)
    assert json_data['employeeCodeRequired'] == True, "JSON should contain true"
    assert isinstance(json_data['employeeCodeRequired'], bool), "JSON should be boolean not string"
    print(f"   ✓ JSON serialization correct: employeeCodeRequired={json_data['employeeCodeRequired']}")
except Exception as e:
    print(f"   ✗ Error: {e}")
    sys.exit(1)

# Test 7: Verify SQLAlchemy model has the field
print("\n7. Testing SQLAlchemy Category model...")
try:
    from sqlalchemy.orm import class_mapper
    mapper = class_mapper(Category)
    columns = [col.key for col in mapper.columns]
    assert 'employeeCodeRequired' in columns, "Model should have employeeCodeRequired column"
    col = mapper.columns['employeeCodeRequired']
    print(f"   ✓ Category model has employeeCodeRequired column")
    print(f"     - Type: {col.type}")
    print(f"     - Nullable: {col.nullable}")
    print(f"     - Default: {col.default}")
except Exception as e:
    print(f"   ✗ Error: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ All tests passed!")
print("=" * 60)
print("\nNext steps:")
print("1. Apply database migration:")
print("   psql -U postgres -d your_db -f database/migrations/20261005_category_employee_code_required.sql")
print("2. Rebuild frontend:")
print("   cd admin-ui && npm run build && Copy-Item -Recurse -Force dist\\* ..\\api\\static\\")
print("3. Restart API server")
print("4. Test in browser admin UI")

#!/usr/bin/env python3
"""
n8n Workflow JSON Validator
Validates n8n workflow JSON files for common issues
"""

import json
import sys
import os
from typing import List, Dict, Any

def validate_json_syntax(file_path: str) -> tuple[bool, str]:
    """Validate JSON syntax"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            json.load(f)
        return True, "Valid JSON syntax"
    except json.JSONDecodeError as e:
        return False, f"JSON syntax error: {e}"
    except FileNotFoundError:
        return False, f"File not found: {file_path}"

def validate_n8n_structure(data: Dict[str, Any]) -> tuple[bool, List[str]]:
    """Validate n8n workflow structure"""
    errors = []
    
    # Check required top-level fields
    required_fields = ['name', 'nodes']
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")
    
    # Check nodes structure
    if 'nodes' in data and isinstance(data['nodes'], list):
        for i, node in enumerate(data['nodes']):
            if not isinstance(node, dict):
                errors.append(f"Node {i} is not a dictionary")
                continue
                
            # Check required node fields
            required_node_fields = ['id', 'name', 'type']
            for field in required_node_fields:
                if field not in node:
                    errors.append(f"Node {i} missing required field: {field}")
    else:
        errors.append("'nodes' field must be a list")
    
    return len(errors) == 0, errors

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 validate_n8n_json.py <workflow.json>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    print(f"🔍 Validating n8n workflow: {file_path}")
    print("=" * 50)
    
    # Validate JSON syntax
    is_valid, message = validate_json_syntax(file_path)
    if not is_valid:
        print(f"❌ {message}")
        sys.exit(1)
    
    print(f"✅ {message}")
    
    # Load and validate n8n structure
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    is_valid, errors = validate_n8n_structure(data)
    
    if is_valid:
        print("✅ Valid n8n workflow structure")
        print(f"📊 Workflow: {data.get('name', 'Unnamed')}")
        print(f"📊 Nodes: {len(data.get('nodes', []))}")
        if 'tags' in data:
            print(f"📊 Tags: {', '.join([tag.get('name', '') for tag in data['tags']])}")
    else:
        print("❌ n8n workflow structure issues:")
        for error in errors:
            print(f"   • {error}")
        sys.exit(1)
    
    print("\n🎉 Workflow is ready to import into n8n!")

if __name__ == "__main__":
    main()
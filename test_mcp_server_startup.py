#!/usr/bin/env python3
"""
Test that the MCP server can be imported and has the correct structure.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))


def test_server_structure():
    """Test that the server module has the correct structure."""
    print("\n" + "="*60)
    print("MCP SERVER STRUCTURE TEST")
    print("="*60)
    
    try:
        # Test 1: Import the server module
        print("\n1. Testing server module import...")
        from mcp_servers.strategy_builder import server
        print("✅ Server module imported successfully")
        
        # Test 2: Verify server app exists
        print("\n2. Testing server app exists...")
        assert hasattr(server, 'app'), "Server module missing 'app' attribute"
        print("✅ Server app exists")
        
        # Test 3: Verify handler functions exist
        print("\n3. Testing handler functions exist...")
        handlers = [
            'handle_validate_dsl_strategy',
            'handle_save_dsl_strategy',
            'handle_list_dsl_strategies'
        ]
        for handler in handlers:
            assert hasattr(server, handler), f"Server module missing '{handler}' function"
            print(f"✅ {handler} exists")
        
        # Test 4: Verify main function exists
        print("\n4. Testing main function exists...")
        assert hasattr(server, 'main'), "Server module missing 'main' function"
        print("✅ main function exists")
        
        # Test 5: Verify server name
        print("\n5. Testing server name...")
        assert server.app.name == "strategy-builder", f"Expected server name 'strategy-builder', got '{server.app.name}'"
        print(f"✅ Server name is correct: {server.app.name}")
        
        # Test 6: Verify validators module
        print("\n6. Testing validators module...")
        from mcp_servers.strategy_builder import validators
        assert hasattr(validators, 'validate_dsl_json'), "Validators module missing 'validate_dsl_json'"
        print("✅ Validators module is correct")
        
        # Test 7: Verify file_operations module
        print("\n7. Testing file_operations module...")
        from mcp_servers.strategy_builder import file_operations
        assert hasattr(file_operations, 'save_dsl_strategy_to_file'), "file_operations missing 'save_dsl_strategy_to_file'"
        assert hasattr(file_operations, 'list_dsl_strategies'), "file_operations missing 'list_dsl_strategies'"
        print("✅ File operations module is correct")
        
        print("\n" + "="*60)
        print("✅ MCP SERVER STRUCTURE TEST PASSED")
        print("="*60)
        print("\nThe server module is correctly structured:")
        print("  ✅ All required modules are present")
        print("  ✅ All handler functions are defined")
        print("  ✅ Server app is properly configured")
        print("  ✅ Ready for MCP protocol communication")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(test_server_structure())

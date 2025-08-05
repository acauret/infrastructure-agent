# test_main.py - Run this to check if main.py is valid
import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from agent import main
    print("✓ Successfully imported agent.main")
    
    if hasattr(main, 'app'):
        print("✓ Found 'app' in main module")
        print(f"  Type: {type(main.app)}")
    else:
        print("✗ 'app' not found in main module")
        print("  Available attributes:", [attr for attr in dir(main) if not attr.startswith('_')])
        
except ImportError as e:
    print(f"✗ Failed to import agent.main: {e}")
except SyntaxError as e:
    print(f"✗ Syntax error in main.py: {e}")
    print(f"  Line {e.lineno}: {e.text}")
except Exception as e:
    print(f"✗ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
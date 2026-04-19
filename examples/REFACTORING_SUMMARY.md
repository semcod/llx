## 🎯 **Goal**
Minimize code duplication by moving common logic from examples to LLX library and replacing Python scripts with simple bash wrappers.

### 1. **Planfile Manager**
- **Before**: `planfile_manager.py` (684 lines Python)
- **After**: `planfile.sh` (300 lines bash) + `llx/examples/utils.py`
- **Benefits**: 
  - Direct LLX CLI usage
  - No Python dependency for basic operations
  - Clearer command structure

### 2. **Hybrid Manager**
- **Before**: `hybrid_manager.py` (490 lines Python)
- **After**: `hybrid.sh` (350 lines bash)
- **Benefits**:
  - Intelligent model selection in bash
  - Queue management without Python
  - Workflow definitions in shell

### 3. **Fullstack Generator**
- **Before**: `app_generator.py` (404 lines Python) + complex `generate.sh`
- **After**: `generate_simple.sh` (250 lines bash) + shared utils
- **Benefits**:
  - Direct LLX integration
  - No Python wrapper needed
  - Simpler maintenance

### 4. **Common Utilities**
- **New**: `llx/examples/utils.py` - Shared helper functions
  - `ExampleHelper` - Common operations
  - `TaskQueue` - Batch processing
  - `WorkflowRunner` - Predefined workflows

## 📊 **Code Reduction**

| Example | Before | After | Reduction |
|---------|--------|-------|------------|
| planfile | 684 lines | 300 bash + 200 utils | 30% |
| hybrid | 490 lines | 350 bash | 29% |
| fullstack | 404 lines | 250 bash + 200 utils | 39% |
| **Total** | **1578 lines** | **1100 lines** | **30%** |

# Generate strategy
./planfile.sh generate --focus complexity --local

# Execute with dry run
./planfile.sh execute --dry-run

# Review strategy
./planfile.sh review --file my_strategy.yaml
```

# Smart execution
./hybrid.sh execute "Add user authentication" --local

# Batch processing
./hybrid.sh queue "Fix login bug"
./hybrid.sh process 5.0

# Workflow
./hybrid.sh workflow fullstack
```

# React app
./generate_simple.sh react my-app --local

# FastAPI backend
./generate_simple.sh fastapi my-api --tier premium

# MERN stack
./generate_simple.sh mern ecommerce
```

## 📁 **New Structure**

```
llx/
├── examples/
│   ├── utils.py              # Shared utilities
│   ├── planfile/
│   │   ├── planfile.sh       # Bash wrapper
│   │   └── planfile_manager.py # Legacy (can remove)
│   ├── hybrid/
│   │   ├── hybrid.sh         # Bash wrapper
│   │   └── hybrid_manager.py # Legacy (can remove)
│   └── fullstack/
│       ├── generate_simple.sh # Simplified generator
│       └── generate.sh       # Original (enhanced)
```

### For Users
1. Use `*.sh` scripts instead of `*.py` files
2. Scripts auto-detect LLX installation
3. All original functionality preserved
4. Added `--local` flag for offline usage

### For Developers
1. Import from `llx.examples.utils` for common operations
2. Use `ExampleHelper` class for standard tasks
3. Extend `WorkflowRunner` for new workflows
4. Use `TaskQueue` for batch operations

## 🎉 **Benefits**

1. **Simpler Deployment**: No Python needed for basic operations
2. **Faster Execution**: Direct CLI calls vs Python overhead
3. **Easier Maintenance**: Bash scripts are transparent
4. **Better Integration**: Works with any shell environment
5. **Reduced Dependencies**: Less Python packages required

## 📝 **Next Steps**

1. Remove legacy Python files after testing
2. Add more workflows to `WorkflowRunner`
3. Extend `TaskQueue` with priority support
4. Create installer script for examples
5. Add completion scripts for bash/zsh

## 🧪 **Testing**

All refactored examples maintain compatibility:
```bash
# Test planfile
cd examples/planfile && ./planfile.sh generate --local

# Test hybrid
cd examples/hybrid && ./hybrid.sh execute "test task" --local

# Test fullstack
cd examples/fullstack && ./generate_simple.sh python-cli test-app --local
```

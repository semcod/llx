# System Architecture Analysis

## Overview

- **Project**: /home/tom/github/semcod/llx/examples/cli-tools
- **Primary Language**: shell
- **Languages**: shell: 2
- **Analysis Mode**: static
- **Total Functions**: 4
- **Total Classes**: 0
- **Modules**: 2
- **Entry Points**: 4

## Architecture by Module

### quick_cli
- **Functions**: 4
- **File**: `quick_cli.sh`

## Key Entry Points

Main execution flows into the system:

### quick_cli.print_usage

### quick_cli.generate_tool

### quick_cli.setup_tool

### quick_cli.quick_generate

## Process Flows

Key execution flows identified:

### Flow 1: print_usage
```
print_usage [quick_cli]
```

### Flow 2: generate_tool
```
generate_tool [quick_cli]
```

### Flow 3: setup_tool
```
setup_tool [quick_cli]
```

### Flow 4: quick_generate
```
quick_generate [quick_cli]
```

## Data Transformation Functions

Key functions that process and transform data:

## Public API Surface

Functions exposed as public API (no underscore prefix):

- `quick_cli.print_usage` - 0 calls
- `quick_cli.generate_tool` - 0 calls
- `quick_cli.setup_tool` - 0 calls
- `quick_cli.quick_generate` - 0 calls

## System Interactions

How components interact:

```mermaid
graph TD
```

## Reverse Engineering Guidelines

1. **Entry Points**: Start analysis from the entry points listed above
2. **Core Logic**: Focus on classes with many methods
3. **Data Flow**: Follow data transformation functions
4. **Process Flows**: Use the flow diagrams for execution paths
5. **API Surface**: Public API functions reveal the interface

## Context for LLM

Maintain the identified architectural patterns and public API surface when suggesting changes.
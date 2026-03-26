# System Architecture Analysis

## Overview

- **Project**: /home/tom/github/semcod/llx/examples
- **Primary Language**: shell
- **Languages**: shell: 21
- **Analysis Mode**: static
- **Total Functions**: 36
- **Total Classes**: 0
- **Modules**: 21
- **Entry Points**: 36

## Architecture by Module

### docker.docker
- **Functions**: 14
- **File**: `docker.sh`

### filtering.filtering
- **Functions**: 7
- **File**: `filtering.sh`

### fullstack.generate_simple
- **Functions**: 6
- **File**: `generate_simple.sh`

### run
- **Functions**: 4
- **File**: `run.sh`

### hybrid.hybrid
- **Functions**: 3
- **File**: `hybrid.sh`

### planfile.planfile
- **Functions**: 2
- **File**: `planfile.sh`

## Key Entry Points

Main execution flows into the system:

### run.show_help

### run.list_examples

### run.run_example

### run.check_dependencies

### fullstack.generate_simple.print_error

### fullstack.generate_simple.print_success

### fullstack.generate_simple.print_status

### fullstack.generate_simple.show_help

### fullstack.generate_simple.get_app_prompt

### fullstack.generate_simple.main

### docker.docker.show_help

### docker.docker.build_docker_cmd

### docker.docker.check_service_health

### docker.docker.check_redis

### docker.docker.check_postgres

### docker.docker.docker_start

### docker.docker.docker_stop

### docker.docker.docker_status

### docker.docker.docker_logs

### docker.docker.docker_exec

### docker.docker.docker_test

### docker.docker.docker_clean

### docker.docker.create_compose_file

### docker.docker.main

### planfile.planfile.show_help

### planfile.planfile.build_llx_cmd

### filtering.filtering.show_help

### filtering.filtering.select_model

### filtering.filtering.demo_cost_filtering

### filtering.filtering.demo_speed_priority

## Process Flows

Key execution flows identified:

### Flow 1: show_help
```
show_help [run]
```

### Flow 2: list_examples
```
list_examples [run]
```

### Flow 3: run_example
```
run_example [run]
```

### Flow 4: check_dependencies
```
check_dependencies [run]
```

### Flow 5: print_error
```
print_error [fullstack.generate_simple]
```

### Flow 6: print_success
```
print_success [fullstack.generate_simple]
```

### Flow 7: print_status
```
print_status [fullstack.generate_simple]
```

### Flow 8: get_app_prompt
```
get_app_prompt [fullstack.generate_simple]
```

### Flow 9: main
```
main [fullstack.generate_simple]
```

### Flow 10: build_docker_cmd
```
build_docker_cmd [docker.docker]
```

## Data Transformation Functions

Key functions that process and transform data:

## Public API Surface

Functions exposed as public API (no underscore prefix):

- `run.show_help` - 0 calls
- `run.list_examples` - 0 calls
- `run.run_example` - 0 calls
- `run.check_dependencies` - 0 calls
- `fullstack.generate_simple.print_error` - 0 calls
- `fullstack.generate_simple.print_success` - 0 calls
- `fullstack.generate_simple.print_status` - 0 calls
- `fullstack.generate_simple.show_help` - 0 calls
- `fullstack.generate_simple.get_app_prompt` - 0 calls
- `fullstack.generate_simple.main` - 0 calls
- `docker.docker.show_help` - 0 calls
- `docker.docker.build_docker_cmd` - 0 calls
- `docker.docker.check_service_health` - 0 calls
- `docker.docker.check_redis` - 0 calls
- `docker.docker.check_postgres` - 0 calls
- `docker.docker.docker_start` - 0 calls
- `docker.docker.docker_stop` - 0 calls
- `docker.docker.docker_status` - 0 calls
- `docker.docker.docker_logs` - 0 calls
- `docker.docker.docker_exec` - 0 calls
- `docker.docker.docker_test` - 0 calls
- `docker.docker.docker_clean` - 0 calls
- `docker.docker.create_compose_file` - 0 calls
- `docker.docker.main` - 0 calls
- `planfile.planfile.show_help` - 0 calls
- `planfile.planfile.build_llx_cmd` - 0 calls
- `filtering.filtering.show_help` - 0 calls
- `filtering.filtering.select_model` - 0 calls
- `filtering.filtering.demo_cost_filtering` - 0 calls
- `filtering.filtering.demo_speed_priority` - 0 calls
- `filtering.filtering.demo_provider_filter` - 0 calls
- `filtering.filtering.interactive_demo` - 0 calls
- `filtering.filtering.main` - 0 calls
- `hybrid.hybrid.show_help` - 0 calls
- `hybrid.hybrid.determine_task_type` - 0 calls
- `hybrid.hybrid.build_llx_cmd` - 0 calls

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
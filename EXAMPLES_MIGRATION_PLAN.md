### ✅ Already Migrated
1. **python-api** - API type - ✅ Refactored to simple form

#### Category: API Examples
| Example | Current Status | Target Type | Priority | Notes |
|---------|----------------|-------------|----------|-------|
| basic | Complex script | api | High | Basic API example |
| filtering | Custom logic | api | Medium | API with filtering |
| multi-provider | Provider selection | api | Medium | Multiple API providers |
| planfile | Plan generation | api | High | Core planfile example |

#### Category: CLI Examples  
| Example | Current Status | Target Type | Priority | Notes |
|---------|----------------|-------------|----------|-------|
| cli-tools | CLI workflow | cli | High | CLI tool example |
| local | Local models | cli | Medium | Local CLI usage |

#### Category: Web App Examples
| Example | Current Status | Target Type | Priority | Notes |
|---------|----------------|-------------|----------|-------|
| fullstack | Full stack app | webapp | High | React/FastAPI stack |
| cloud-local | Cloud deployment | webapp | Medium | Web app with cloud |

#### Category: Tool Integration Examples
| Example | Current Status | Target Type | Priority | Notes |
|---------|----------------|-------------|----------|-------|
| aider | Aider integration | tool | High | AI pair programming |
| ai-tools | AI tools suite | tool | Medium | Multiple AI tools |
| vscode-roocode | VS Code extension | tool | Low | VS Code integration |
| hybrid | Hybrid approach | tool | Medium | Multiple tools |

#### Category: Infrastructure Examples
| Example | Current Status | Target Type | Priority | Notes |
|---------|----------------|-------------|----------|-------|
| docker | Docker setup | infra | Medium | Container deployment |
| proxy | Proxy setup | infra | Medium | LiteLLM proxy |

### Phase 1: Core Examples (Week 1)
1. **basic** - Fundamental API example
2. **cli-tools** - CLI tool example  
3. **fullstack** - Web application example
4. **planfile** - Core planfile usage

### Phase 2: Advanced Examples (Week 2)
5. **multi-provider** - API with providers
6. **filtering** - API with filtering
7. **local** - Local models CLI
8. **docker** - Infrastructure example

### Phase 3: Integration Examples (Week 3)
9. **aider** - Tool integration
10. **ai-tools** - AI tools suite
11. **cloud-local** - Web app deployment
12. **proxy** - Infrastructure

### Phase 4: Specialized Examples (Week 4)
13. **hybrid** - Multiple tools
14. **vscode-roocode** - VS Code specific

# Analyze current example
cd examples/[example-name]
find . -name "*.sh" -exec wc -l {} \;  # Count script lines
grep -r "llx plan" .                    # Current LLX usage
cat run.sh                             # Review current script
```

### 2. Categorization
- Determine project type (api, webapp, cli, tool, infra)
- Identify unique features
- Note any special requirements

# New run.sh template
#!/bin/bash
set -e
DESCRIPTION="${1:-}"
PROJECT_TYPE="[type]"  # api, webapp, cli, etc.
FRAMEWORK="[framework]"  # optional

if [ -n "$DESCRIPTION" ]; then
    llx plan all "$DESCRIPTION" --type "$PROJECT_TYPE" ${FRAMEWORK:+--framework "$FRAMEWORK"} --run
else
    echo "Usage: $0 \"description\""
    echo ""
    echo "Example:"
    echo "  $0 \"REST API for user management\""
fi
```

# Test migration
./run.sh "Test description"
### basic Example
- **Type**: api
- **Framework**: fastapi (default)
- **Special**: None
- **Target**: Simple API generation demo

### cli-tools Example  
- **Type**: cli
- **Framework**: click
- **Special**: Show CLI-specific features
- **Target**: CLI tool generation demo

### fullstack Example
- **Type**: webapp
- **Framework**: react + fastapi
- **Special**: Full stack with API
- **Target**: Full stack application demo

### aider Example
- **Type**: tool
- **Framework**: aider
- **Special**: External tool integration
- **Target**: Show tool integration pattern

### docker Example
- **Type**: infra
- **Framework**: docker
- **Special**: Infrastructure as code
- **Target**: Deployment configuration demo

### Technical Criteria
- [ ] run.sh < 30 lines
- [ ] Uses `llx plan all` or simple LLX commands
- [ ] No complex logic in script
- [ ] All configuration in LLX or .env

### Functional Criteria
- [ ] Generated code works correctly
- [ ] All original features preserved
- [ ] Documentation updated
- [ ] Example is self-contained

### User Experience Criteria
- [ ] Clear usage instructions
- [ ] Helpful error messages
- [ ] Good example output
- [ ] Easy to understand

### Pre-Migration
- [ ] Document current behavior
- [ ] Identify all features
- [ ] Note special requirements
- [ ] Create test cases

### Migration
- [ ] Create new run.sh
- [ ] Update README.md
- [ ] Test basic functionality
- [ ] Test edge cases

### Post-Migration
- [ ] Update documentation
- [ ] Add to examples index
- [ ] Verify all tests pass
- [ ] Code review

### Risk 1: Lost Functionality
- **Mitigation**: Comprehensive testing before/after
- **Recovery**: Keep original script as backup

### Risk 2: Example-Specific Requirements
- **Mitigation**: Document special cases
- **Solution**: Extend LLX to support edge cases

### Risk 3: User Confusion
- **Mitigation**: Clear documentation
- **Solution**: Migration guide and examples

## Timeline

| Week | Goals | Deliverables |
|-------|-------|--------------|
| 1 | Core examples | basic, cli-tools, fullstack, planfile |
| 2 | Advanced examples | multi-provider, filtering, local, docker |
| 3 | Integration examples | aider, ai-tools, cloud-local, proxy |
| 4 | Specialized examples | hybrid, vscode-roocode, documentation |

## Next Steps

1. **Review and approve** this migration plan
2. **Implement LLX enhancements** from LLX_ENHANCEMENT_PLAN.md
3. **Begin Phase 1 migrations** starting with `basic`
4. **Daily progress tracking** and review
5. **Weekly retrospectives** to adjust approach

This migration will result in a consistent, maintainable set of examples that are easy to understand and extend.

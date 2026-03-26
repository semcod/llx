# System Architecture Analysis

## Overview

- **Project**: /home/tom/github/semcod/llx
- **Primary Language**: python
- **Languages**: python: 128, shell: 20
- **Analysis Mode**: static
- **Total Functions**: 1113
- **Total Classes**: 174
- **Modules**: 148
- **Entry Points**: 912

## Architecture by Module

### llx.tools.config_manager
- **Functions**: 43
- **Classes**: 1
- **File**: `config_manager.py`

### llx.orchestration.routing.engine
- **Functions**: 38
- **Classes**: 1
- **File**: `engine.py`

### llx.tools.model_manager
- **Functions**: 33
- **Classes**: 1
- **File**: `model_manager.py`

### llx.prellm.trace
- **Functions**: 29
- **Classes**: 2
- **File**: `trace.py`

### llx.orchestration.vscode.orchestrator
- **Functions**: 27
- **Classes**: 1
- **File**: `orchestrator.py`

### llx.tools.vscode_manager
- **Functions**: 25
- **Classes**: 1
- **File**: `vscode_manager.py`

### llx.orchestration.llm.orchestrator
- **Functions**: 25
- **Classes**: 1
- **File**: `orchestrator.py`

### llx.tools.ai_tools_manager
- **Functions**: 22
- **Classes**: 1
- **File**: `ai_tools_manager.py`

### llx.analysis.collector
- **Functions**: 21
- **Classes**: 1
- **File**: `collector.py`

### llx.tools.docker_manager
- **Functions**: 21
- **Classes**: 1
- **File**: `docker_manager.py`

### llx.orchestration.queue.manager
- **Functions**: 21
- **Classes**: 1
- **File**: `manager.py`

### llx.orchestration.session.manager
- **Functions**: 20
- **Classes**: 1
- **File**: `manager.py`

### examples.planfile.planfile_manager
- **Functions**: 20
- **Classes**: 6
- **File**: `planfile_manager.py`

### llx.prellm.pipeline
- **Functions**: 18
- **Classes**: 5
- **File**: `pipeline.py`

### llx.orchestration.instances.manager
- **Functions**: 18
- **Classes**: 1
- **File**: `manager.py`

### llx.prellm.env_config
- **Functions**: 17
- **Classes**: 1
- **File**: `env_config.py`

### llx.cli.app
- **Functions**: 17
- **File**: `app.py`

### llx.orchestration.ratelimit.limiter
- **Functions**: 17
- **Classes**: 1
- **File**: `limiter.py`

### examples.fullstack.app_generator
- **Functions**: 16
- **Classes**: 2
- **File**: `app_generator.py`

### examples.hybrid.hybrid_manager
- **Functions**: 16
- **Classes**: 3
- **File**: `hybrid_manager.py`

## Key Entry Points

Main execution flows into the system:

### examples.ai-tools.main.main
- **Calls**: docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, examples.ai-tools.main.check_docker_services, services.items

### examples.basic.main.main
> Main example execution
- **Calls**: docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, LlxConfig.load, docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print

### llx.orchestration.instances.manager.InstanceManager.load_instances
> Load instances from configuration file.
- **Calls**: self.config_file.exists, data.get, docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, open, json.load, InstanceConfig

### examples.aider.aider_demo.main
- **Calls**: docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, Path, project_dir.mkdir, py_file.write_text, docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print

### examples.vscode-roocode.demo.RooCodeDemo.run_demo
> Run complete RooCode demonstration.
- **Calls**: docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, self.check_services, docker.ai-tools.entrypoint.print, services.items, self.get_available_models

### examples.fullstack.app_generator.main
- **Calls**: argparse.ArgumentParser, parser.add_subparsers, subparsers.add_parser, gen_parser.add_argument, gen_parser.add_argument, gen_parser.add_argument, gen_parser.add_argument, gen_parser.add_argument

### llx.tools.vscode_manager.VSCodeManager.print_quick_start
> Print quick start guide.
- **Calls**: docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print

### llx.tools.model_manager.ModelManager.print_model_summary
> Print comprehensive model summary.
- **Calls**: docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, self.check_ollama_running, self.check_llx_running, docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, self.get_system_resources, docker.ai-tools.entrypoint.print

### llx.orchestration.vscode.orchestrator.VSCodeOrchestrator.load_config
> Load VS Code orchestration configuration.
- **Calls**: self.config_file.exists, self.config.update, data.get, data.get, data.get, docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, self._create_default_config

### llx.orchestration.ratelimit.limiter.RateLimiter.load_limits
> Load rate limits from configuration file.
- **Calls**: self.config_file.exists, data.get, docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, self._create_default_limits, docker.ai-tools.entrypoint.print, open, json.load

### examples.planfile.generate_strategy.main
> Generate a complete strategy using the fixed generator.
- **Calls**: console.print, Path, Panel, examples.planfile.generate_strategy.generate_strategy_with_fix, examples.planfile.generate_strategy.save_fixed_strategy, console.print, console.print, console.print

### examples.filtering.advanced_filters.demonstrate_filtering
> Demonstrate various filtering scenarios.
- **Calls**: docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, SmartLLXClient, docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, client.chat_with_constraints, docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print

### llx.orchestration.session.manager.SessionManager.load_sessions
> Load sessions from configuration file.
- **Calls**: self.config_file.exists, data.get, docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, open, json.load, SessionConfig

### llx.orchestration.queue.manager.QueueManager.load_queues
> Load queues from configuration file.
- **Calls**: self.config_file.exists, data.get, docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, open, json.load, QueueConfig

### llx.tools.ai_tools_manager.AIToolsManager.print_usage_examples
> Print usage examples.
- **Calls**: docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print

### llx.tools.health_checker.HealthChecker.monitor_services
> Monitor services over time.
- **Calls**: docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, time.time, docker.ai-tools.entrypoint.print, None.analyze_monitoring_data, docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print

### llx.orchestration.llm.orchestrator.LLMOrchestrator.load_config
> Load LLM orchestration configuration.
- **Calls**: llx.orchestration._utils.load_json, self.config.update, data.get, docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, self._create_default_config, docker.ai-tools.entrypoint.print, data.get

### llx.orchestration.queue.manager.QueueManager.print_status_summary
> Print comprehensive status summary.
- **Calls**: docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, len, sum, sum, sum, docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print

### examples.hybrid.hybrid_manager.main
- **Calls**: argparse.ArgumentParser, parser.add_subparsers, subparsers.add_parser, exec_parser.add_argument, exec_parser.add_argument, exec_parser.add_argument, exec_parser.add_argument, exec_parser.add_argument

### llx.prellm.cli_commands.decompose
> [v0.2] Decompose a query using small LLM without calling the large model.
- **Calls**: typer.Argument, typer.Option, typer.Option, typer.Option, PreLLM, DecompositionStrategy, asyncio.run, engine.decompose_only

### llx.tools.config_manager.ConfigManager.print_config_summary
> Print comprehensive configuration summary.
- **Calls**: self.get_config_summary, docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, None.items, docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print

### llx.orchestration.ratelimit.limiter.RateLimiter.print_status_summary
> Print comprehensive status summary.
- **Calls**: docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, len, sum, docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print

### llx.tools.health_checker._dispatch
- **Calls**: checker.run_comprehensive_health_check, checker.run_quick_health_check, open, json.dump, checker.monitor_services, checker.check_service_health, docker.ai-tools.entrypoint.print, open

### llx.prellm.pipeline_ops.execute_v3_pipeline
> Two-agent execution path — PreprocessorAgent + ExecutorAgent + PromptPipeline.

v0.4 refactor: uses context_ops and pipeline_ops modules to reduce com
- **Calls**: kwargs.pop, kwargs.pop, LLMProviderConfig, LLMProviderConfig, LLMProvider, LLMProvider, PromptRegistry, PromptPipeline.from_yaml

### llx.tools.docker_manager.DockerManager.print_status_summary
> Print comprehensive status summary.
- **Calls**: docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, self.get_service_status, docker.ai-tools.entrypoint.print, status.items, docker.ai-tools.entrypoint.print, self.services.keys, self.get_resource_usage

### examples.filtering.advanced_filters.interactive_filtering
> Interactive filtering demo.
- **Calls**: docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, SmartLLXClient, docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print

### llx.tools.ai_tools_manager._dispatch
- **Calls**: manager.start_ai_tools, manager.stop_ai_tools, manager.restart_ai_tools, manager.access_shell, manager.print_status_summary, manager.get_logs, docker.ai-tools.entrypoint.print, manager.test_connectivity

### llx.orchestration.session.manager.SessionManager.print_status_summary
> Print comprehensive status summary.
- **Calls**: docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, len, self.session_states.values, self.sessions.values, docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print, docker.ai-tools.entrypoint.print

### examples.planfile.planfile_manager.PlanfileManager.monitor_execution
> Monitor strategy execution in real-time.
- **Calls**: Table, table.add_column, table.add_column, table.add_column, table.add_column, data.get, data.get, Panel

### llx.prellm.cli_config.config_show_cmd
> Show effective configuration (resolved from all sources).

Example:
    prellm config show
- **Calls**: config_app.command, llx.prellm.env_config.get_env_config, typer.echo, typer.echo, typer.echo, typer.echo, typer.echo, typer.echo

## Process Flows

Key execution flows identified:

### Flow 1: main
```
main [examples.ai-tools.main]
  └─ →> print
  └─ →> print
```

### Flow 2: load_instances
```
load_instances [llx.orchestration.instances.manager.InstanceManager]
  └─ →> print
  └─ →> print
```

### Flow 3: run_demo
```
run_demo [examples.vscode-roocode.demo.RooCodeDemo]
  └─ →> print
  └─ →> print
```

### Flow 4: print_quick_start
```
print_quick_start [llx.tools.vscode_manager.VSCodeManager]
  └─ →> print
  └─ →> print
```

### Flow 5: print_model_summary
```
print_model_summary [llx.tools.model_manager.ModelManager]
  └─ →> print
  └─ →> print
```

### Flow 6: load_config
```
load_config [llx.orchestration.vscode.orchestrator.VSCodeOrchestrator]
```

### Flow 7: load_limits
```
load_limits [llx.orchestration.ratelimit.limiter.RateLimiter]
  └─ →> print
  └─ →> print
```

### Flow 8: demonstrate_filtering
```
demonstrate_filtering [examples.filtering.advanced_filters]
  └─ →> print
  └─ →> print
```

### Flow 9: load_sessions
```
load_sessions [llx.orchestration.session.manager.SessionManager]
  └─ →> print
  └─ →> print
```

### Flow 10: load_queues
```
load_queues [llx.orchestration.queue.manager.QueueManager]
  └─ →> print
  └─ →> print
```

## Key Classes

### llx.orchestration.routing.engine.RoutingEngine
> Intelligent routing engine for LLM and VS Code requests.
- **Methods**: 38
- **Key Methods**: llx.orchestration.routing.engine.RoutingEngine.__init__, llx.orchestration.routing.engine.RoutingEngine.load_config, llx.orchestration.routing.engine.RoutingEngine.save_config, llx.orchestration.routing.engine.RoutingEngine.route_request, llx.orchestration.routing.engine.RoutingEngine._get_candidates, llx.orchestration.routing.engine.RoutingEngine._get_llm_candidates, llx.orchestration.routing.engine.RoutingEngine._get_vscode_candidates, llx.orchestration.routing.engine.RoutingEngine._get_ai_tools_candidates, llx.orchestration.routing.engine.RoutingEngine._filter_candidates, llx.orchestration.routing.engine.RoutingEngine._filter_by_rate_limits

### llx.orchestration.vscode.orchestrator.VSCodeOrchestrator
> Orchestrates multiple VS Code instances with intelligent management.
- **Methods**: 27
- **Key Methods**: llx.orchestration.vscode.orchestrator.VSCodeOrchestrator.__init__, llx.orchestration.vscode.orchestrator.VSCodeOrchestrator.load_config, llx.orchestration.vscode.orchestrator.VSCodeOrchestrator.save_config, llx.orchestration.vscode.orchestrator.VSCodeOrchestrator._create_default_config, llx.orchestration.vscode.orchestrator.VSCodeOrchestrator.start, llx.orchestration.vscode.orchestrator.VSCodeOrchestrator.stop, llx.orchestration.vscode.orchestrator.VSCodeOrchestrator.add_account, llx.orchestration.vscode.orchestrator.VSCodeOrchestrator.remove_account, llx.orchestration.vscode.orchestrator.VSCodeOrchestrator.create_instance, llx.orchestration.vscode.orchestrator.VSCodeOrchestrator.remove_instance

### llx.orchestration.llm.orchestrator.LLMOrchestrator
> Orchestrates multiple LLM providers and models with intelligent routing.
- **Methods**: 25
- **Key Methods**: llx.orchestration.llm.orchestrator.LLMOrchestrator.__init__, llx.orchestration.llm.orchestrator.LLMOrchestrator.load_config, llx.orchestration.llm.orchestrator.LLMOrchestrator.save_config, llx.orchestration.llm.orchestrator.LLMOrchestrator._create_default_config, llx.orchestration.llm.orchestrator.LLMOrchestrator.start, llx.orchestration.llm.orchestrator.LLMOrchestrator.stop, llx.orchestration.llm.orchestrator.LLMOrchestrator.add_provider, llx.orchestration.llm.orchestrator.LLMOrchestrator.remove_provider, llx.orchestration.llm.orchestrator.LLMOrchestrator.add_model, llx.orchestration.llm.orchestrator.LLMOrchestrator.complete_request

### llx.tools.config_manager.ConfigManager
> Manages llx configuration files and settings.
- **Methods**: 24
- **Key Methods**: llx.tools.config_manager.ConfigManager.__init__, llx.tools.config_manager.ConfigManager.load_config, llx.tools.config_manager.ConfigManager.save_config, llx.tools.config_manager.ConfigManager._load_env_file, llx.tools.config_manager.ConfigManager._save_env_file, llx.tools.config_manager.ConfigManager.create_default_env, llx.tools.config_manager.ConfigManager.update_env_var, llx.tools.config_manager.ConfigManager.get_env_var, llx.tools.config_manager.ConfigManager.validate_env_config, llx.tools.config_manager.ConfigManager.get_llx_config

### llx.tools.vscode_manager.VSCodeManager
> Manages VS Code server with AI extensions.
- **Methods**: 22
- **Key Methods**: llx.tools.vscode_manager.VSCodeManager.__init__, llx.tools.vscode_manager.VSCodeManager.is_vscode_running, llx.tools.vscode_manager.VSCodeManager.start_vscode, llx.tools.vscode_manager.VSCodeManager.stop_vscode, llx.tools.vscode_manager.VSCodeManager.restart_vscode, llx.tools.vscode_manager.VSCodeManager.wait_for_vscode_ready, llx.tools.vscode_manager.VSCodeManager.check_vscode_health, llx.tools.vscode_manager.VSCodeManager.get_vscode_url, llx.tools.vscode_manager.VSCodeManager.get_vscode_password, llx.tools.vscode_manager.VSCodeManager.install_extensions

### llx.prellm.trace.TraceRecorder
> Records execution trace and generates markdown documentation.
- **Methods**: 21
- **Key Methods**: llx.prellm.trace.TraceRecorder.start, llx.prellm.trace.TraceRecorder.stop, llx.prellm.trace.TraceRecorder.step, llx.prellm.trace.TraceRecorder.set_result, llx.prellm.trace.TraceRecorder.total_duration_ms, llx.prellm.trace.TraceRecorder._generate_markdown_header, llx.prellm.trace.TraceRecorder._generate_markdown_config, llx.prellm.trace.TraceRecorder._generate_markdown_step_details, llx.prellm.trace.TraceRecorder._generate_markdown_decision_path, llx.prellm.trace.TraceRecorder._generate_markdown_result

### llx.orchestration.queue.manager.QueueManager
> Manages multiple request queues with intelligent prioritization.
- **Methods**: 21
- **Key Methods**: llx.orchestration.queue.manager.QueueManager.__init__, llx.orchestration.queue.manager.QueueManager.load_queues, llx.orchestration.queue.manager.QueueManager.save_queues, llx.orchestration.queue.manager.QueueManager.start, llx.orchestration.queue.manager.QueueManager.stop, llx.orchestration.queue.manager.QueueManager.add_queue, llx.orchestration.queue.manager.QueueManager.remove_queue, llx.orchestration.queue.manager.QueueManager.enqueue_request, llx.orchestration.queue.manager.QueueManager.dequeue_request, llx.orchestration.queue.manager.QueueManager.complete_request

### llx.orchestration.session.manager.SessionManager
> Manages multiple sessions with intelligent scheduling and rate limiting.
- **Methods**: 20
- **Key Methods**: llx.orchestration.session.manager.SessionManager.__init__, llx.orchestration.session.manager.SessionManager.load_sessions, llx.orchestration.session.manager.SessionManager.save_sessions, llx.orchestration.session.manager.SessionManager.create_session, llx.orchestration.session.manager.SessionManager.remove_session, llx.orchestration.session.manager.SessionManager.get_available_session, llx.orchestration.session.manager.SessionManager.request_session, llx.orchestration.session.manager.SessionManager.release_session, llx.orchestration.session.manager.SessionManager.get_session_status, llx.orchestration.session.manager.SessionManager.list_sessions

### llx.tools.ai_tools_manager.AIToolsManager
> Manages AI tools container and operations.
- **Methods**: 19
- **Key Methods**: llx.tools.ai_tools_manager.AIToolsManager.__init__, llx.tools.ai_tools_manager.AIToolsManager.is_container_running, llx.tools.ai_tools_manager.AIToolsManager.start_ai_tools, llx.tools.ai_tools_manager.AIToolsManager.stop_ai_tools, llx.tools.ai_tools_manager.AIToolsManager.restart_ai_tools, llx.tools.ai_tools_manager.AIToolsManager.access_shell, llx.tools.ai_tools_manager.AIToolsManager.execute_command, llx.tools.ai_tools_manager.AIToolsManager.get_status, llx.tools.ai_tools_manager.AIToolsManager.test_connectivity, llx.tools.ai_tools_manager.AIToolsManager.run_chat_test

### llx.tools.model_manager.ModelManager
> Manages local Ollama models and llx configurations.
- **Methods**: 19
- **Key Methods**: llx.tools.model_manager.ModelManager.__init__, llx.tools.model_manager.ModelManager.check_ollama_running, llx.tools.model_manager.ModelManager.check_llx_running, llx.tools.model_manager.ModelManager.get_ollama_models, llx.tools.model_manager.ModelManager.get_llx_models, llx.tools.model_manager.ModelManager.pull_model, llx.tools.model_manager.ModelManager.remove_model, llx.tools.model_manager.ModelManager.test_model, llx.tools.model_manager.ModelManager.test_llx_model, llx.tools.model_manager.ModelManager.get_model_info

### llx.prellm.pipeline.PromptPipeline
> Generic pipeline — executes a sequence of LLM + algorithmic steps.

Usage:
    pipeline = PromptPipe
- **Methods**: 18
- **Key Methods**: llx.prellm.pipeline.PromptPipeline.__init__, llx.prellm.pipeline.PromptPipeline.from_yaml, llx.prellm.pipeline.PromptPipeline.execute, llx.prellm.pipeline.PromptPipeline._execute_llm_step, llx.prellm.pipeline.PromptPipeline._execute_algo_step, llx.prellm.pipeline.PromptPipeline._gather_inputs, llx.prellm.pipeline.PromptPipeline._build_user_message, llx.prellm.pipeline.PromptPipeline._evaluate_condition, llx.prellm.pipeline.PromptPipeline.register_algo_handler, llx.prellm.pipeline.PromptPipeline._algo_domain_rule_matcher

### llx.tools.docker_manager.DockerManager
> Manages Docker containers for llx ecosystem.
- **Methods**: 18
- **Key Methods**: llx.tools.docker_manager.DockerManager.__init__, llx.tools.docker_manager.DockerManager.get_compose_cmd, llx.tools.docker_manager.DockerManager.run_compose_cmd, llx.tools.docker_manager.DockerManager.start_environment, llx.tools.docker_manager.DockerManager.stop_environment, llx.tools.docker_manager.DockerManager.restart_service, llx.tools.docker_manager.DockerManager.get_service_status, llx.tools.docker_manager.DockerManager.get_service_logs, llx.tools.docker_manager.DockerManager.check_service_health, llx.tools.docker_manager.DockerManager.wait_for_service

### llx.orchestration.instances.manager.InstanceManager
> Manages multiple Docker instances with intelligent allocation and monitoring.
- **Methods**: 18
- **Key Methods**: llx.orchestration.instances.manager.InstanceManager.__init__, llx.orchestration.instances.manager.InstanceManager.load_instances, llx.orchestration.instances.manager.InstanceManager.save_instances, llx.orchestration.instances.manager.InstanceManager.create_instance, llx.orchestration.instances.manager.InstanceManager.start_instance, llx.orchestration.instances.manager.InstanceManager.stop_instance, llx.orchestration.instances.manager.InstanceManager.remove_instance, llx.orchestration.instances.manager.InstanceManager.get_available_instance, llx.orchestration.instances.manager.InstanceManager.use_instance, llx.orchestration.instances.manager.InstanceManager.get_instance_status

### llx.orchestration.ratelimit.limiter.RateLimiter
> Manages rate limiting for multiple providers and accounts.
- **Methods**: 17
- **Key Methods**: llx.orchestration.ratelimit.limiter.RateLimiter.__init__, llx.orchestration.ratelimit.limiter.RateLimiter.load_limits, llx.orchestration.ratelimit.limiter.RateLimiter.save_limits, llx.orchestration.ratelimit.limiter.RateLimiter._create_default_limits, llx.orchestration.ratelimit.limiter.RateLimiter.add_limit, llx.orchestration.ratelimit.limiter.RateLimiter.remove_limit, llx.orchestration.ratelimit.limiter.RateLimiter.check_rate_limit, llx.orchestration.ratelimit.limiter.RateLimiter.record_request, llx.orchestration.ratelimit.limiter.RateLimiter.release_request, llx.orchestration.ratelimit.limiter.RateLimiter.get_status

### llx.prellm.context.user_memory.UserMemory
> Stores user query history and learned preferences.

Usage:
    # SQLite (default, no extra deps)
   
- **Methods**: 15
- **Key Methods**: llx.prellm.context.user_memory.UserMemory.__init__, llx.prellm.context.user_memory.UserMemory._init_sqlite, llx.prellm.context.user_memory.UserMemory._init_chromadb, llx.prellm.context.user_memory.UserMemory.add_interaction, llx.prellm.context.user_memory.UserMemory.get_recent_context, llx.prellm.context.user_memory.UserMemory.get_user_preferences, llx.prellm.context.user_memory.UserMemory.set_preference, llx.prellm.context.user_memory.UserMemory.clear, llx.prellm.context.user_memory.UserMemory.export_session, llx.prellm.context.user_memory.UserMemory.import_session

### examples.planfile.planfile_manager.PlanfileManager
> Advanced manager for planfile-driven refactoring strategies.
- **Methods**: 15
- **Key Methods**: examples.planfile.planfile_manager.PlanfileManager.__init__, examples.planfile.planfile_manager.PlanfileManager.generate_strategy, examples.planfile.planfile_manager.PlanfileManager.review_strategy, examples.planfile.planfile_manager.PlanfileManager.execute_strategy, examples.planfile.planfile_manager.PlanfileManager.monitor_execution, examples.planfile.planfile_manager.PlanfileManager._analyze_project, examples.planfile.planfile_manager.PlanfileManager._select_model_for_focus, examples.planfile.planfile_manager.PlanfileManager._show_strategy_summary, examples.planfile.planfile_manager.PlanfileManager._display_review, examples.planfile.planfile_manager.PlanfileManager._execute_sprints_sequential

### llx.prellm.context.sensitive_filter.SensitiveDataFilter
> Classifies and filters sensitive data from context before LLM calls.
- **Methods**: 14
- **Key Methods**: llx.prellm.context.sensitive_filter.SensitiveDataFilter.__init__, llx.prellm.context.sensitive_filter.SensitiveDataFilter._load_rules, llx.prellm.context.sensitive_filter.SensitiveDataFilter.classify_key, llx.prellm.context.sensitive_filter.SensitiveDataFilter.classify_value, llx.prellm.context.sensitive_filter.SensitiveDataFilter.filter_dict, llx.prellm.context.sensitive_filter.SensitiveDataFilter.filter_context_for_large_llm, llx.prellm.context.sensitive_filter.SensitiveDataFilter.sanitize_text, llx.prellm.context.sensitive_filter.SensitiveDataFilter.get_filter_report, llx.prellm.context.sensitive_filter.SensitiveDataFilter._filter_dict_item, llx.prellm.context.sensitive_filter.SensitiveDataFilter._filter_env_var_item

### llx.prellm.context.codebase_indexer.CodebaseIndexer
> Index a codebase using tree-sitter for AST-based symbol extraction.

Usage:
    indexer = CodebaseIn
- **Methods**: 14
- **Key Methods**: llx.prellm.context.codebase_indexer.CodebaseIndexer.__init__, llx.prellm.context.codebase_indexer.CodebaseIndexer._check_tree_sitter, llx.prellm.context.codebase_indexer.CodebaseIndexer.index_directory, llx.prellm.context.codebase_indexer.CodebaseIndexer._index_file, llx.prellm.context.codebase_indexer.CodebaseIndexer._extract_with_tree_sitter, llx.prellm.context.codebase_indexer.CodebaseIndexer._get_parser, llx.prellm.context.codebase_indexer.CodebaseIndexer._walk_tree, llx.prellm.context.codebase_indexer.CodebaseIndexer._get_line, llx.prellm.context.codebase_indexer.CodebaseIndexer._extract_with_regex, llx.prellm.context.codebase_indexer.CodebaseIndexer._extract_imports

### llx.prellm.analyzers.context_engine.ContextEngine
> Collects context from environment, git, and system for prompt enrichment.

Used by both core Prellm 
- **Methods**: 13
- **Key Methods**: llx.prellm.analyzers.context_engine.ContextEngine.__init__, llx.prellm.analyzers.context_engine.ContextEngine.gather, llx.prellm.analyzers.context_engine.ContextEngine.enrich_prompt, llx.prellm.analyzers.context_engine.ContextEngine.gather_runtime, llx.prellm.analyzers.context_engine.ContextEngine._auto_collect_env, llx.prellm.analyzers.context_engine.ContextEngine._gather_process, llx.prellm.analyzers.context_engine.ContextEngine._gather_locale, llx.prellm.analyzers.context_engine.ContextEngine._gather_network, llx.prellm.analyzers.context_engine.ContextEngine._gather_env, llx.prellm.analyzers.context_engine.ContextEngine._gather_git

### examples.hybrid.hybrid_manager.HybridManager
> Manages hybrid cloud-local development workflow.
- **Methods**: 12
- **Key Methods**: examples.hybrid.hybrid_manager.HybridManager.__init__, examples.hybrid.hybrid_manager.HybridManager._analyze_project, examples.hybrid.hybrid_manager.HybridManager._load_usage_log, examples.hybrid.hybrid_manager.HybridManager._save_usage_log, examples.hybrid.hybrid_manager.HybridManager._log_usage, examples.hybrid.hybrid_manager.HybridManager.execute_task, examples.hybrid.hybrid_manager.HybridManager._estimate_cost, examples.hybrid.hybrid_manager.HybridManager._get_provider_for_tier, examples.hybrid.hybrid_manager.HybridManager._execute_generated_code, examples.hybrid.hybrid_manager.HybridManager.batch_process

## Data Transformation Functions

Key functions that process and transform data:

### llx.prellm.cli_config._format_config_sections
> Group config entries into categorized sections for display.
- **Output to**: entries.items, None.append, None.append, var.startswith, None.append

### llx.prellm.cli.process
> Execute a DevOps process chain.
- **Output to**: app.command, typer.Argument, typer.Option, typer.Option, typer.Option

### llx.prellm.env_config._parse_env_line
> Parse a single .env line. Returns (key, value) or None if invalid.
- **Output to**: line.strip, line.partition, key.strip, None.strip, line.startswith

### llx.prellm.trace._format_tree_value
> Format a value for display in the decision tree — no truncation.
- **Output to**: isinstance, str, isinstance, json.dumps, val.replace

### llx.prellm._get_process_chain

### llx.prellm.pipeline_ops.run_preprocessing
> Run the small-LLM preprocessing step. Returns (prep_result, duration_ms).
- **Output to**: time.time, preprocessor.preprocess, time.time

### llx.prellm.prompt_registry.PromptRegistry.validate
> Validate that all prompts have non-empty templates. Returns list of error messages.
- **Output to**: self._ensure_loaded, set, self._entries.items, self._entries.keys, errors.append

### llx.prellm.cli_query._execute_and_format_result
> Execute the query and format output.
- **Output to**: asyncio.run, llx.prellm.core.preprocess_and_execute, recorder.stop, typer.echo, recorder.save

### llx.prellm.validators.ResponseValidator.validate
> Validate a dict against a named schema.

Args:
    data: The data dict to validate (typically parsed
- **Output to**: self._ensure_loaded, self._schemas.get, schema.types.items, schema.constraints.items, ValidationResult

### llx.prellm.validators.ResponseValidator.validate_or_retry
> Validate, and if invalid, call retry_fn and try again.

Args:
    data: Initial data to validate.
  
- **Output to**: self.validate, logger.info, retry_fn, self.validate

### llx.prellm.core.preprocess_and_execute
> One function to preprocess and execute — like litellm.completion() but with small LLM decomposition.
- **Output to**: logger.info, llx.prellm.trace.get_current_trace, PreLLM._load_config, trace.step, pipeline_ops.execute_v3_pipeline

### llx.prellm.core.preprocess_and_execute_sync
> Synchronous version of preprocess_and_execute() — runs the async function in an event loop.

Usage:

- **Output to**: asyncio.run, llx.prellm.core.preprocess_and_execute

### llx.prellm.llm_provider.LLMProvider._parse_json
> Best-effort JSON extraction from LLM output.
- **Output to**: text.strip, logger.warning, json.loads, text.split, text.find

### llx.prellm.extractors.format_classification_context
> Extract and format classification context from preprocessing result.
- **Output to**: state.get, isinstance, state.get, classification.get, classification.get

### llx.prellm.extractors.format_context_schema
> Extract and format context schema information.
- **Output to**: extra_context.get, schema_data.get, schema_data.get, schema_data.get, isinstance

### llx.prellm.extractors.format_runtime_context
> Extract and format runtime context information.
- **Output to**: extra_context.get, runtime.get, runtime.get, sys_info.get, sys_info.get

### llx.prellm.extractors.format_user_context
> Extract and format user context information.
- **Output to**: extra_context.get, parts.append

### llx.prellm.server._parse_model_pair
> Parse 'prellm:qwen→claude' or 'prellm:small→large' into (small, large) model strings.

Special cases
- **Output to**: model_str.split, None.lower, pair.split, len, pair.split

### llx.prellm.server.batch_process
> Process multiple queries in parallel.
- **Output to**: app.post, HTTPException, asyncio.gather, list, llx.prellm.core.preprocess_and_execute

### llx.prellm.cli_commands.process
> Execute a DevOps process chain.
- **Output to**: typer.Argument, typer.Option, typer.Option, typer.Option, typer.Option

### llx.prellm.pipeline.PromptPipeline._algo_yaml_formatter
> Format pipeline state into structured executor input.
- **Output to**: inputs.get, state.get, state.get, isinstance, str

### llx.analysis.collector._parse_map_stats_line
> Parse: # stats: 814 func | 0 cls | 108 mod | CC̄=4.6
- **Output to**: line.split, part.strip, re.search, re.search, re.search

### llx.analysis.collector._parse_map_alerts_line
> Parse: # alerts[5]: CC _extract=65; fan-out _extract=45
- **Output to**: re.finditer, re.finditer, max, max, int

### llx.analysis.collector._parse_map_hotspots_line
> Parse: # hotspots[5]: _extract fan=45; ...
- **Output to**: re.search, re.finditer, max, max, int

### llx.tools.ai_tools_manager._build_parser
- **Output to**: argparse.ArgumentParser, parser.add_argument, parser.add_argument, parser.add_argument, parser.add_argument

## Behavioral Patterns

### recursion__sanitize
- **Type**: recursion
- **Confidence**: 0.90
- **Functions**: llx.prellm.trace._sanitize

### state_machine_LlxClient
- **Type**: state_machine
- **Confidence**: 0.70
- **Functions**: llx.routing.client.LlxClient.__init__, llx.routing.client.LlxClient.chat, llx.routing.client.LlxClient.chat_with_context, llx.routing.client.LlxClient._build_payload, llx.routing.client.LlxClient._parse_response

### state_machine_ProxymClient
- **Type**: state_machine
- **Confidence**: 0.70
- **Functions**: llx.integrations.proxym.ProxymClient.__init__, llx.integrations.proxym.ProxymClient.is_available, llx.integrations.proxym.ProxymClient.status, llx.integrations.proxym.ProxymClient.chat, llx.integrations.proxym.ProxymClient.chat_with_analysis

## Public API Surface

Functions exposed as public API (no underscore prefix):

- `examples.ai-tools.main.main` - 58 calls
- `llx.prellm.cli_context.context` - 49 calls
- `examples.planfile.generate_strategy.generate_strategy_with_fix` - 47 calls
- `examples.basic.main.main` - 44 calls
- `llx.orchestration.instances.manager.InstanceManager.load_instances` - 43 calls
- `examples.aider.aider_demo.main` - 42 calls
- `examples.vscode-roocode.demo.RooCodeDemo.run_demo` - 42 calls
- `examples.fullstack.app_generator.main` - 37 calls
- `llx.tools.vscode_manager.VSCodeManager.print_quick_start` - 36 calls
- `llx.tools.model_manager.ModelManager.print_model_summary` - 36 calls
- `llx.orchestration.vscode.orchestrator.VSCodeOrchestrator.load_config` - 36 calls
- `llx.orchestration.ratelimit.limiter.RateLimiter.load_limits` - 36 calls
- `examples.planfile.generate_strategy.main` - 35 calls
- `examples.filtering.advanced_filters.demonstrate_filtering` - 35 calls
- `llx.orchestration.session.manager.SessionManager.load_sessions` - 34 calls
- `llx.orchestration.queue.manager.QueueManager.load_queues` - 34 calls
- `llx.tools.ai_tools_manager.AIToolsManager.print_usage_examples` - 31 calls
- `llx.tools.health_checker.HealthChecker.monitor_services` - 30 calls
- `llx.orchestration.llm.orchestrator.LLMOrchestrator.load_config` - 30 calls
- `llx.orchestration.queue.manager.QueueManager.print_status_summary` - 30 calls
- `examples.planfile.async_refactor_demo.demonstrate_async_refactoring` - 30 calls
- `examples.hybrid.hybrid_manager.main` - 30 calls
- `llx.prellm.cli_commands.decompose` - 29 calls
- `llx.tools.config_manager.ConfigManager.print_config_summary` - 29 calls
- `llx.orchestration.ratelimit.limiter.RateLimiter.print_status_summary` - 29 calls
- `examples.ai-tools.main.show_usage_examples` - 29 calls
- `llx.prellm.env_config.get_env_config` - 27 calls
- `llx.prellm.pipeline_ops.execute_v3_pipeline` - 27 calls
- `llx.tools.docker_manager.DockerManager.print_status_summary` - 27 calls
- `examples.filtering.advanced_filters.interactive_filtering` - 27 calls
- `llx.orchestration.session.manager.SessionManager.print_status_summary` - 26 calls
- `examples.planfile.planfile_manager.PlanfileManager.monitor_execution` - 26 calls
- `llx.prellm.cli_config.config_show_cmd` - 25 calls
- `llx.prellm.cli_commands.budget` - 25 calls
- `llx.orchestration.vscode.orchestrator.VSCodeOrchestrator.print_status_summary` - 25 calls
- `examples.docker.main.main` - 25 calls
- `llx.tools.vscode_manager.VSCodeManager.install_extensions` - 24 calls
- `examples.local.main.demonstrate_local_model_selection` - 24 calls
- `examples.multi-provider.main.main` - 24 calls
- `llx.config.LlxConfig.load` - 23 calls

## System Interactions

How components interact:

```mermaid
graph TD
    main --> print
    main --> load
    load_instances --> exists
    load_instances --> get
    load_instances --> print
    main --> Path
    main --> mkdir
    main --> write_text
    run_demo --> print
    run_demo --> check_services
    main --> ArgumentParser
    main --> add_subparsers
    main --> add_parser
    main --> add_argument
    print_quick_start --> print
    print_model_summary --> print
    print_model_summary --> check_ollama_running
    print_model_summary --> check_llx_running
    load_config --> exists
    load_config --> update
    load_config --> get
    load_limits --> exists
    load_limits --> get
    load_limits --> print
    load_limits --> _create_default_limi
    main --> Panel
    main --> generate_strategy_wi
    main --> save_fixed_strategy
    demonstrate_filterin --> print
    demonstrate_filterin --> SmartLLXClient
```

## Reverse Engineering Guidelines

1. **Entry Points**: Start analysis from the entry points listed above
2. **Core Logic**: Focus on classes with many methods
3. **Data Flow**: Follow data transformation functions
4. **Process Flows**: Use the flow diagrams for execution paths
5. **API Surface**: Public API functions reveal the interface

## Context for LLM

Maintain the identified architectural patterns and public API surface when suggesting changes.
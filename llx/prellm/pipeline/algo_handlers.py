from __future__ import annotations

from typing import Any


class AlgoHandlersMixin:
    def _build_algo_handlers(self, validators: dict[str, Any] | None = None) -> dict[str, Any]:
        handlers: dict[str, Any] = {
            "domain_rule_matcher": self._algo_domain_rule_matcher,
            "field_validator": self._algo_field_validator,
            "yaml_formatter": self._algo_yaml_formatter,
            "runtime_collector": self._algo_runtime_collector,
            "sensitive_filter": self._algo_sensitive_filter,
            "session_injector": self._algo_session_injector,
            "shell_context_collector": self._algo_shell_context_collector,
            "folder_compressor": self._algo_folder_compressor,
            "context_schema_generator": self._algo_context_schema_generator,
        }
        if validators:
            handlers.update(validators)
        return handlers

    def _execute_algo_step(self, step: Any, state: dict[str, Any]) -> Any:
        handler = self._algo_handlers.get(step.type)
        if not handler:
            raise KeyError(f"Unknown algorithmic step type: {step.type}")

        config = step.config or {}
        inputs = self._resolve_step_input(step.input, state)
        return handler(inputs, config=config, state=state)

    def _resolve_step_input(self, step_input: str | list[str], state: dict[str, Any]) -> Any:
        if isinstance(step_input, list):
            return {key: state.get(key) for key in step_input}
        return state.get(step_input)

    def _algo_domain_rule_matcher(self, inputs: Any, config: dict[str, Any], state: dict[str, Any]) -> Any:
        return {"matched": False, "inputs": inputs, "config": config}

    def _algo_field_validator(self, inputs: Any, config: dict[str, Any], state: dict[str, Any]) -> Any:
        return {"valid": True, "inputs": inputs, "config": config}

    def _algo_yaml_formatter(self, inputs: Any, config: dict[str, Any], state: dict[str, Any]) -> Any:
        return inputs

    def _algo_runtime_collector(self, inputs: Any, config: dict[str, Any], state: dict[str, Any]) -> Any:
        return state

    def _algo_sensitive_filter(self, inputs: Any, config: dict[str, Any], state: dict[str, Any]) -> Any:
        return inputs

    def _algo_session_injector(self, inputs: Any, config: dict[str, Any], state: dict[str, Any]) -> Any:
        return inputs

    def _algo_shell_context_collector(self, inputs: Any, config: dict[str, Any], state: dict[str, Any]) -> Any:
        return inputs

    def _algo_folder_compressor(self, inputs: Any, config: dict[str, Any], state: dict[str, Any]) -> Any:
        return inputs

    def _algo_context_schema_generator(self, inputs: Any, config: dict[str, Any], state: dict[str, Any]) -> Any:
        return config.get("schema", {})

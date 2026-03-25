"""CLI entry point for llx.

Lesson from preLLM: cli.py was 999 lines with CC=30 in main() and CC=27 in query().
llx splits CLI into app.py (commands) + formatters.py (output). Each function ≤ CC 10.
"""

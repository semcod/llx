#!/usr/bin/env python3
"""
Full-stack application generator with LLX integration.
Generates complete applications based on natural language descriptions.
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import shutil

# Add llx to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from llx.config import LlxConfig
from llx.routing.client import LlxClient, ChatMessage


class AppGenerator:
    """Generates full-stack applications using LLX."""
    
    def __init__(self):
        self.config = LlxConfig.load()
        
    def generate_app(
        self,
        description: str,
        output_dir: str,
        *,
        tier: str = "balanced",
        provider: Optional[str] = None,
        prefer_local: bool = False,
        tool: Optional[str] = None,
        execute: bool = False
    ) -> bool:
        """
        Generate a complete application.
        
        Args:
            description: Natural language description of the app
            output_dir: Directory to create the app
            tier: Model tier to use
            provider: Specific provider to use
            prefer_local: Use local models
            tool: Development tool to integrate
            execute: Execute build/run commands after generation
            
        Returns:
            True if successful
        """
        print(f"🚀 Generating application in {output_dir}")
        print(f"📝 Description: {description[:100]}...")
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        os.chdir(output_path)
        
        # Build enhanced prompt
        prompt = self._build_prompt(description, execute)
        
        # Build LLX command
        cmd = ["llx", "chat", "--model", tier, "--task", "refactor"]
        
        if provider:
            cmd.extend(["--provider", provider])
            
        if prefer_local:
            cmd.append("--local")
            
        cmd.extend(["--prompt", prompt])
        
        # Execute generation
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            print("✅ Generation successful!")
            
            # Post-process generated files
            self._post_process()
            
            # Execute if requested
            if execute:
                self._execute_app()
                
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Generation failed: {e}")
            print(f"Output: {e.output}")
            return False
    
    def _build_prompt(self, description: str, execute: bool) -> str:
        """Build comprehensive prompt for app generation."""
        base_prompt = f"""
Generate a complete, working application based on this description:
{description}

Requirements:
1. Create ALL necessary files and directories
2. Include proper configuration files (package.json, requirements.txt, etc.)
3. Add comprehensive README.md with setup and run instructions
4. Include error handling and validation
5. Follow best practices and modern patterns
6. Make it production-ready with proper structure
7. Include unit tests where appropriate
8. Add environment configuration
9. Include Docker/docker-compose if applicable
10. Ensure the app can run immediately after setup

"""
        
        if execute:
            base_prompt += """
11. After generation, the app should be ready to run with standard commands
12. Include all necessary build scripts and dependencies
"""
        
        return base_prompt
    
    def _post_process(self):
        """Post-process generated files."""
        print("🔧 Post-processing generated files...")
        
        # Find and format common files
        for pattern in ["package.json", "requirements.txt", "go.mod", "Cargo.toml"]:
            for file in Path(".").rglob(pattern):
                self._format_file(file)
                
        # Check for common directories and create if missing
        essential_dirs = ["src", "tests", "docs", "config"]
        for dir_name in essential_dirs:
            dir_path = Path(dir_name)
            if not dir_path.exists():
                dir_path.mkdir(exist_ok=True)
                # Create .gitkeep
                (dir_path / ".gitkeep").touch()
    
    def _format_file(self, file_path: Path):
        """Format a file if possible."""
        try:
            if file_path.name == "package.json":
                # Format JSON
                with open(file_path, 'r') as f:
                    data = json.load(f)
                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=2)
                print(f"  Formatted {file_path}")
        except Exception as e:
            print(f"  Warning: Could not format {file_path}: {e}")
    
    def _execute_app(self):
        """Execute common setup and run commands."""
        print("🏃 Executing setup commands...")
        
        # Detect project type and run appropriate commands
        if Path("package.json").exists():
            self._execute_node_app()
        elif Path("requirements.txt").exists():
            self._execute_python_app()
        elif Path("go.mod").exists():
            self._execute_go_app()
        elif Path("Cargo.toml").exists():
            self._execute_rust_app()
        else:
            print("  Unknown project type, skipping execution")
    
    def _execute_node_app(self):
        """Execute Node.js app setup."""
        commands = [
            ("npm install", "Installing dependencies"),
            ("npm run build", "Building application" if Path("webpack.config.js").exists() or Path("tsconfig.json").exists() else None),
            ("npm test", "Running tests" if Path("test").exists() or Path("__tests__").exists() else None),
            ("npm start", "Starting application" if Path("package.json").exists() else None)
        ]
        
        for cmd, desc in commands:
            if desc:
                print(f"  {desc}...")
                try:
                    subprocess.run(cmd.split(), check=True, capture_output=True)
                    print(f"  ✓ {desc} completed")
                except subprocess.CalledProcessError:
                    print(f"  ⚠ {desc} failed (optional)")
    
    def _execute_python_app(self):
        """Execute Python app setup."""
        commands = [
            ("python -m venv venv", "Creating virtual environment"),
            ("source venv/bin/activate && pip install -r requirements.txt", "Installing dependencies"),
            ("source venv/bin/activate && python -m pytest", "Running tests" if Path("tests").exists() else None),
            ("source venv/bin/activate && python main.py", "Running app" if Path("main.py").exists() else None)
        ]
        
        for cmd, desc in commands:
            if desc:
                print(f"  {desc}...")
                try:
                    subprocess.run(cmd, shell=True, check=True, capture_output=True)
                    print(f"  ✓ {desc} completed")
                except subprocess.CalledProcessError:
                    print(f"  ⚠ {desc} failed (optional)")
    
    def _execute_go_app(self):
        """Execute Go app setup."""
        commands = [
            ("go mod download", "Downloading dependencies"),
            ("go build", "Building application"),
            ("go test ./...", "Running tests"),
            ("./app", "Running application" if Path("app").exists() else None)
        ]
        
        for cmd, desc in commands:
            if desc:
                print(f"  {desc}...")
                try:
                    subprocess.run(cmd.split(), check=True, capture_output=True)
                    print(f"  ✓ {desc} completed")
                except subprocess.CalledProcessError:
                    print(f"  ⚠ {desc} failed (optional)")
    
    def _execute_rust_app(self):
        """Execute Rust app setup."""
        commands = [
            ("cargo build", "Building application"),
            ("cargo test", "Running tests"),
            ("cargo run", "Running application")
        ]
        
        for cmd, desc in commands:
            if desc:
                print(f"  {desc}...")
                try:
                    subprocess.run(cmd.split(), check=True, capture_output=True)
                    print(f"  ✓ {desc} completed")
                except subprocess.CalledProcessError:
                    print(f"  ⚠ {desc} failed (optional)")


class TemplateGenerator:
    """Generates reusable app templates."""
    
    def __init__(self):
        self.templates_dir = Path.home() / ".llx" / "templates"
        self.templates_dir.mkdir(parents=True, exist_ok=True)
    
    def save_template(self, app_dir: str, template_name: str):
        """Save an app as a reusable template."""
        print(f"💾 Saving template: {template_name}")
        
        src = Path(app_dir)
        dst = self.templates_dir / template_name
        
        if dst.exists():
            shutil.rmtree(dst)
            
        shutil.copytree(src, dst)
        
        # Create template metadata
        metadata = {
            "name": template_name,
            "created": str(Path.cwd()),
            "type": self._detect_app_type(src)
        }
        
        with open(dst / ".template.json", "w") as f:
            json.dump(metadata, f, indent=2)
            
        print(f"✅ Template saved to {dst}")
    
    def list_templates(self):
        """List available templates."""
        print("📋 Available templates:")
        
        for template in self.templates_dir.iterdir():
            if template.is_dir():
                meta_file = template / ".template.json"
                if meta_file.exists():
                    with open(meta_file) as f:
                        meta = json.load(f)
                    print(f"  • {meta['name']} ({meta['type']})")
                else:
                    print(f"  • {template.name}")
    
    def use_template(self, template_name: str, output_dir: str):
        """Use a template to create a new app."""
        template_path = self.templates_dir / template_name
        
        if not template_path.exists():
            print(f"❌ Template '{template_name}' not found")
            return False
            
        print(f"📋 Using template: {template_name}")
        
        output = Path(output_dir)
        if output.exists():
            print(f"❌ Directory '{output_dir}' already exists")
            return False
            
        shutil.copytree(template_path, output)
        
        # Remove template metadata
        meta_file = output / ".template.json"
        if meta_file.exists():
            meta_file.remove()
            
        print(f"✅ Template applied to {output_dir}")
        return True
    
    def _detect_app_type(self, path: Path) -> str:
        """Detect application type from files."""
        if (path / "package.json").exists():
            return "node"
        elif (path / "requirements.txt").exists():
            return "python"
        elif (path / "go.mod").exists():
            return "go"
        elif (path / "Cargo.toml").exists():
            return "rust"
        else:
            return "unknown"


def main():
    parser = argparse.ArgumentParser(description="LLX Full-Stack App Generator")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate an application")
    gen_parser.add_argument("description", help="App description")
    gen_parser.add_argument("output", help="Output directory")
    gen_parser.add_argument("-t", "--tier", choices=["cheap", "balanced", "premium"], 
                          default="balanced", help="Model tier")
    gen_parser.add_argument("-p", "--provider", help="LLM provider")
    gen_parser.add_argument("-l", "--local", action="store_true", help="Use local models")
    gen_parser.add_argument("--execute", action="store_true", help="Execute after generation")
    
    # Template commands
    tpl_parser = subparsers.add_parser("template", help="Template management")
    tpl_subparsers = tpl_parser.add_subparsers(dest="template_cmd")
    
    save_parser = tpl_subparsers.add_parser("save", help="Save as template")
    save_parser.add_argument("app_dir", help="App directory")
    save_parser.add_argument("name", help="Template name")
    
    use_parser = tpl_subparsers.add_parser("use", help="Use template")
    use_parser.add_argument("template", help="Template name")
    use_parser.add_argument("output", help="Output directory")
    
    list_parser = tpl_subparsers.add_parser("list", help="List templates")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == "generate":
        generator = AppGenerator()
        success = generator.generate_app(
            args.description,
            args.output,
            tier=args.tier,
            provider=args.provider,
            prefer_local=args.local,
            execute=args.execute
        )
        
        if success:
            print("\n✨ Application generated successfully!")
            print(f"📁 Location: {Path(args.output).absolute()}")
            print("\nNext steps:")
            print("1. Review the generated code")
            print("2. Customize as needed")
            print("3. Run the application")
        else:
            print("\n❌ Failed to generate application")
            sys.exit(1)
            
    elif args.command == "template":
        template_mgr = TemplateGenerator()
        
        if args.template_cmd == "save":
            template_mgr.save_template(args.app_dir, args.name)
        elif args.template_cmd == "use":
            template_mgr.use_template(args.template, args.output)
        elif args.template_cmd == "list":
            template_mgr.list_templates()
        else:
            tpl_parser.print_help()


if __name__ == "__main__":
    main()

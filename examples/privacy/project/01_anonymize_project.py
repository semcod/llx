"""Project-level anonymization example.

Demonstrates anonymizing an entire codebase.
"""

import tempfile
from pathlib import Path

from llx.privacy.project import AnonymizationContext, ProjectAnonymizer


def create_sample_project(base_path: Path):
    """Create a sample Python project for demonstration."""
    
    # Create project structure
    src_dir = base_path / "src"
    src_dir.mkdir()
    
    # main.py
    (src_dir / "main.py").write_text("""
\"\"\"Main application module.\"\"\"
from database import get_connection
from models import User, Order

def process_user_order(user_id: int, order_data: dict) -> Order:
    \"\"\"Process an order for a user.\"\"\"
    user = User.get_by_id(user_id)
    order = Order.create(user=user, data=order_data)
    return order

def main():
    connection = get_connection()
    initialize_database(connection)
    
def initialize_database(conn):
    \"\"\"Setup database tables.\"\"\"
    conn.execute("CREATE TABLE IF NOT EXISTS users ...")
""")
    
    # models.py
    (src_dir / "models.py").write_text("""
\"\"\"Data models.\"\"\"
from dataclasses import dataclass
from typing import Optional

@dataclass
class User:
    id: int
    email: str
    full_name: str
    phone: Optional[str] = None
    
    @classmethod
    def get_by_id(cls, user_id: int) -> "User":
        # Fetch from database
        pass

@dataclass
class Order:
    id: int
    user_id: int
    total_amount: float
    items: list
    
    @classmethod
    def create(cls, user: User, data: dict) -> "Order":
        return cls(
            id=data["id"],
            user_id=user.id,
            total_amount=sum(item["price"] for item in data["items"]),
            items=data["items"]
        )
""")
    
    # database.py
    (src_dir / "database.py").write_text("""
\"\"\"Database connection management.\"\"\"
import os

DATABASE_URL = "postgresql://admin:secret123@localhost:5432/myapp"

def get_connection():
    \"\"\"Get database connection.\"\"\"
    import psycopg2
    return psycopg2.connect(DATABASE_URL)

def close_connection(conn):
    \"\"\"Close database connection.\"\"\"
    conn.close()
""")
    
    # config.yaml
    (base_path / "config.yaml").write_text("""
database:
  host: db.internal.company.com
  port: 5432
  username: dbadmin
  password: SuperSecretPassword!

api:
  endpoint: https://api.company.com/v1
  key: sk-abcdefghijklmnop
  timeout: 30
""")


def main():
    print("=" * 70)
    print("LLX Privacy: Project-Level Anonymization Example")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir) / "my_project"
        project_path.mkdir()
        
        # Create sample project
        print("\n1. CREATING SAMPLE PROJECT")
        print("-" * 40)
        create_sample_project(project_path)
        
        # List files
        print(f"Project structure:")
        for f in project_path.rglob("*"):
            if f.is_file():
                print(f"  {f.relative_to(project_path)}")
        
        # Show original content
        print("\n2. ORIGINAL SOURCE CODE (main.py snippet):")
        print("-" * 40)
        original_code = (project_path / "src" / "main.py").read_text()
        print(original_code[:500] + "...")
        
        # Create context and anonymizer
        print("\n3. ANONYMIZING PROJECT")
        print("-" * 40)
        
        ctx = AnonymizationContext(project_path=project_path)
        anonymizer = ProjectAnonymizer(ctx)
        
        # Anonymize entire project
        result = anonymizer.anonymize_project(
            include_patterns=["*.py", "*.yaml"],
            exclude_patterns=["__pycache__/*"],
        )
        
        print(f"Files processed: {len(result.files)}")
        print(f"\nSymbol mappings created:")
        print(f"  Variables: {len(ctx.variables)}")
        print(f"  Functions: {len(ctx.functions)}")
        print(f"  Classes: {len(ctx.classes)}")
        print(f"  Modules: {len(ctx.modules)}")
        print(f"  Paths: {len(ctx.paths)}")
        
        # Show anonymized content
        print("\n4. ANONYMIZED CODE (main.py):")
        print("-" * 40)
        print(result.files.get("src/main.py", "N/A")[:500])
        
        # Save context for later deanonymization
        context_path = project_path / ".anonymization_context.json"
        ctx.save(context_path)
        print(f"\nContext saved to: {context_path}")
        
        # Show mapping example
        print("\n5. EXAMPLE SYMBOL MAPPINGS:")
        print("-" * 40)
        for i, (original, mapping) in enumerate(list(ctx.functions.items())[:5]):
            print(f"  {mapping.anonymized} -> {original}")
        
        print("\n" + "=" * 70)
        print("Project anonymization complete!")
        print("Next: Run 02_deanonymize_project.py to restore original names")
        print("=" * 70)


if __name__ == "__main__":
    main()

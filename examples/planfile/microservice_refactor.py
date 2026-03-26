#!/usr/bin/env python3
"""
Example: Microservice Refactoring with Planfile
Demonstrates refactoring a monolithic service into microservices
"""

import asyncio
import json
import subprocess
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree

console = Console()


async def create_monolith_sample():
    """Create a sample monolithic service for refactoring."""
    
    monolith_code = '''
"""
Monolithic E-commerce Service
Contains multiple responsibilities that should be split
"""

from datetime import datetime
from typing import Dict, List, Optional
import sqlite3
import hashlib
import jwt

class ECommerceService:
    """Monolithic service doing everything"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.secret_key = "secret123"
        self.init_database()
    
    def init_database(self):
        """Initialize all tables in one place"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                email TEXT UNIQUE,
                password_hash TEXT,
                created_at TIMESTAMP
            )
        """)
        
        # Products table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                name TEXT,
                price DECIMAL(10,2),
                stock INTEGER
            )
        """)
        
        # Orders table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                total DECIMAL(10,2),
                status TEXT,
                created_at TIMESTAMP
            )
        """)
        
        # Order items table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY,
                order_id INTEGER,
                product_id INTEGER,
                quantity INTEGER,
                price DECIMAL(10,2)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def register_user(self, email: str, password: str) -> Optional[Dict]:
        """User registration"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Hash password
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        try:
            cursor.execute(
                "INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, ?)",
                (email, password_hash, datetime.now())
            )
            conn.commit()
            
            user_id = cursor.lastrowid
            token = self.generate_token(user_id)
            
            return {"user_id": user_id, "token": token}
        except sqlite3.IntegrityError:
            return None
        finally:
            conn.close()
    
    def login_user(self, email: str, password: str) -> Optional[Dict]:
        """User login"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        cursor.execute(
            "SELECT id FROM users WHERE email = ? AND password_hash = ?",
            (email, password_hash)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result:
            token = self.generate_token(result[0])
            return {"user_id": result[0], "token": token}
        return None
    
    def generate_token(self, user_id: int) -> str:
        """Generate JWT token"""
        payload = {"user_id": user_id, "exp": datetime.now().timestamp() + 3600}
        return jwt.encode(payload, self.secret_key, algorithm="HS256")
    
    def create_product(self, name: str, price: float, stock: int) -> Dict:
        """Product management"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO products (name, price, stock) VALUES (?, ?, ?)",
            (name, price, stock)
        )
        conn.commit()
        
        product_id = cursor.lastrowid
        conn.close()
        
        return {"product_id": product_id, "name": name, "price": price, "stock": stock}
    
    def list_products(self) -> List[Dict]:
        """List all products"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM products")
        products = []
        
        for row in cursor.fetchall():
            products.append({
                "id": row[0],
                "name": row[1],
                "price": row[2],
                "stock": row[3]
            })
        
        conn.close()
        return products
    
    def create_order(self, user_id: int, items: List[Dict]) -> Optional[Dict]:
        """Order creation - complex business logic"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Calculate total
        total = 0.0
        order_items = []
        
        for item in items:
            cursor.execute("SELECT price, stock FROM products WHERE id = ?", (item["product_id"],))
            product = cursor.fetchone()
            
            if not product:
                conn.close()
                return None
            
            price, stock = product
            if stock < item["quantity"]:
                conn.close()
                return None
            
            # Update stock
            cursor.execute(
                "UPDATE products SET stock = ? WHERE id = ?",
                (stock - item["quantity"], item["product_id"])
            )
            
            total += price * item["quantity"]
            order_items.append((item["product_id"], item["quantity"], price))
        
        # Create order
        cursor.execute(
            "INSERT INTO orders (user_id, total, status, created_at) VALUES (?, ?, ?, ?)",
            (user_id, total, "pending", datetime.now())
        )
        order_id = cursor.lastrowid
        
        # Create order items
        for product_id, quantity, price in order_items:
            cursor.execute(
                "INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?)",
                (order_id, product_id, quantity, price)
            )
        
        conn.commit()
        conn.close()
        
        return {"order_id": order_id, "total": total, "status": "pending"}
    
    def get_user_orders(self, user_id: int) -> List[Dict]:
        """Get user's order history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT o.*, COUNT(oi.id) as item_count
            FROM orders o
            LEFT JOIN order_items oi ON o.id = oi.order_id
            WHERE o.user_id = ?
            GROUP BY o.id
            ORDER BY o.created_at DESC
        """, (user_id,))
        
        orders = []
        for row in cursor.fetchall():
            orders.append({
                "id": row[0],
                "user_id": row[1],
                "total": row[2],
                "status": row[3],
                "created_at": row[4],
                "item_count": row[5]
            })
        
        conn.close()
        return orders


# API endpoints mixed with business logic
from flask import Flask, request, jsonify

app = Flask(__name__)
service = ECommerceService("ecommerce.db")

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    result = service.register_user(data["email"], data["password"])
    return jsonify(result or {"error": "Registration failed"})

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    result = service.login_user(data["email"], data["password"])
    return jsonify(result or {"error": "Login failed"})

@app.route("/products", methods=["GET"])
def list_products():
    return jsonify(service.list_products())

@app.route("/orders", methods=["POST"])
def create_order():
    # No authentication for simplicity
    data = request.get_json()
    result = service.create_order(data["user_id"], data["items"])
    return jsonify(result or {"error": "Order creation failed"})

if __name__ == "__main__":
    app.run(debug=True)
'''
    
    # Write monolith code
    monolith_path = Path("monolith_service.py")
    monolith_path.write_text(monolith_code)
    
    console.print(Panel(
        "[green]✓ Created monolithic service sample[/green]",
        title="Monolith Created"
    )
    
    return monolith_path


async def demonstrate_microservice_refactoring():
    """Demonstrate refactoring monolith to microservices using planfile."""
    
    console.print("\n[bold cyan]Microservice Refactoring Demo[/bold cyan]")
    console.print("=" * 50)
    
    # Create sample monolith
    monolith_path = await create_monolith_sample()
    
    # Generate refactoring strategy
    console.print("\n[blue]Step 1: Generating microservice extraction strategy...[/blue]")
    
    strategy_cmd = [
        "python3", "-m", "llx", "plan", "generate",
        ".",
        "--model", "qwen2.5-coder:7b",  # Use local model if available
        "--sprints", "4",
        "--focus", "complexity",
        "--output", "microservice-strategy.yaml"
    ]
    
    try:
        result = subprocess.run(strategy_cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            console.print("[green]✓ Strategy generated successfully[/green]")
            
            # Show strategy structure
            if Path("microservice-strategy.yaml").exists():
                console.print("\n[blue]Strategy Overview:[/blue]")
                
                # Read and display key parts of strategy
                with open("microservice-strategy.yaml") as f:
                    content = f.read()
                
                # Extract sprint information
                lines = content.split('\n')
                in_sprints = False
                sprint_count = 0
                
                for line in lines:
                    if 'sprints:' in line:
                        in_sprints = True
                    elif in_sprints and line.strip().startswith('id:'):
                        sprint_count += 1
                        console.print(f"  Sprint {sprint_count}: {line.strip()}")
                
        else:
            console.print(f"[red]✗ Strategy generation failed: {result.stderr}[/red]")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
    
    # Show what the refactoring should achieve
    console.print("\n[blue]Expected Refactoring Outcome:[/blue]")
    
    tree = Tree("Target Architecture")
    
    user_service = tree.add("🟦 user-service")
    user_service.add("• User registration/login")
    user_service.add("• JWT token management")
    user_service.add("• User profile management")
    
    product_service = tree.add("🟩 product-service")
    product_service.add("• Product CRUD")
    product_service.add("• Inventory management")
    product_service.add("• Product search")
    
    order_service = tree.add("🟨 order-service")
    order_service.add("• Order creation")
    order_service.add("• Order history")
    order_service.add("• Order status tracking")
    
    api_gateway = tree.add("🟪 api-gateway")
    api_gateway.add("• Request routing")
    api_gateway.add("• Authentication middleware")
    api_gateway.add("• Rate limiting")
    
    console.print(tree)
    
    # Create expected directory structure
    console.print("\n[blue]Creating target directory structure...[/blue]")
    
    directories = [
        "microservices/user-service/src",
        "microservices/product-service/src",
        "microservices/order-service/src",
        "microservices/api-gateway/src",
        "microservices/shared"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    console.print("[green]✓ Directory structure created[/green]")
    
    # Provide manual refactoring guidance
    console.print("\n[yellow]Manual Refactoring Steps:[/yellow]")
    console.print("""
1. Extract user management to user-service:
   - Move User class and auth methods
   - Create /auth, /users endpoints
   - Add user database

2. Extract product management to product-service:
   - Move Product class and methods
   - Create /products endpoints
   - Add product database

3. Extract order management to order-service:
   - Move Order class and methods
   - Create /orders endpoints
   - Add order database

4. Create API Gateway:
   - Implement request routing
   - Add authentication middleware
   - Handle cross-service communication

5. Add shared libraries:
   - Common models
   - Database utilities
   - Authentication helpers
""")


async def main():
    """Main demonstration function."""
    
    console.print(Panel(
        "[bold cyan]Planfile Microservice Refactoring Example[/bold cyan]\n"
        "This demo shows how to use planfile to refactor a monolith to microservices",
        title="Microservice Demo"
    ))
    
    await demonstrate_microservice_refactoring()
    
    console.print("\n[green]Demo completed![/green]")
    console.print("\nNext steps:")
    console.print("1. Review the generated strategy")
    console.print("2. Execute the refactoring sprint by sprint")
    console.print("3. Test each microservice independently")
    console.print("4. Set up service discovery and communication")


if __name__ == "__main__":
    asyncio.run(main())

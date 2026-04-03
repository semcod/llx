"""Project deanonymization example.

Demonstrates restoring original values from anonymized content.
"""

import tempfile
from pathlib import Path

from llx.privacy.project import AnonymizationContext, ProjectAnonymizer
from llx.privacy.deanonymize import ProjectDeanonymizer, quick_project_deanonymize


def main():
    print("=" * 70)
    print("LLX Privacy: Project Deanonymization Example")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup: Create and anonymize a project
        project_path = Path(tmpdir) / "my_project"
        project_path.mkdir()
        
        # Create source file
        src_file = project_path / "calculator.py"
        src_file.write_text("""
def calculate_total(items):
    subtotal = sum(item.price for item in items)
    tax = subtotal * 0.20
    return subtotal + tax

def apply_discount(total, percentage):
    return total * (1 - percentage / 100)

class ShoppingCart:
    def __init__(self):
        self.items = []
    
    def add_product(self, product):
        self.items.append(product)
    
    def get_total(self):
        return calculate_total(self.items)
""")
        
        # Anonymize
        print("\n1. ANONYMIZING SOURCE CODE")
        print("-" * 40)
        
        ctx = AnonymizationContext(project_path=project_path)
        anonymizer = ProjectAnonymizer(ctx)
        anon_result = anonymizer.anonymize_file(src_file)
        
        print("Original function names:")
        for name in ["calculate_total", "apply_discount"]:
            if name in ctx.functions:
                print(f"  {ctx.functions[name].anonymized}")
        
        print("\nAnonymized code:")
        print(anon_result)
        
        # Save context
        context_path = project_path / "context.json"
        ctx.save(context_path)
        
        # Simulate LLM response using anonymized names
        calculate_anon = ctx.functions["calculate_total"].anonymized
        cart_anon = ctx.classes["ShoppingCart"].anonymized
        
        llm_response = f"""
To optimize your code, I suggest refactoring the {calculate_anon} function:
1. Use a more efficient algorithm for summing
2. Cache the tax calculation
3. Consider making the {cart_anon} class immutable
"""
        
        print("\n2. SIMULATED LLM RESPONSE")
        print("-" * 40)
        print(llm_response)
        
        # Method 1: Deanonymize using context object
        print("\n3. DEANONYMIZING (Method 1: Context Object)")
        print("-" * 40)
        
        deanonymizer = ProjectDeanonymizer(ctx)
        result = deanonymizer.deanonymize_text(llm_response)
        print(result.text)
        
        # Method 2: Deanonymize using saved context file
        print("\n4. DEANONYMIZING (Method 2: Context File)")
        print("-" * 40)
        
        restored = quick_project_deanonymize(llm_response, context_path)
        print(restored)
        
        # Deanonymize entire file
        print("\n5. DEANONYMIZING ENTIRE FILE")
        print("-" * 40)
        
        file_result = deanonymizer.deanonymize_file(anon_result, str(src_file))
        print(file_result.text[:500])
        
        # Show symbol info
        print("\n6. SYMBOL INFORMATION")
        print("-" * 40)
        
        anon_name = ctx.functions["calculate_total"].anonymized
        info = deanonymizer.get_symbol_info(anon_name)
        
        if info:
            print(f"Anonymized: {info['anonymized']}")
            print(f"Original: {info['original']}")
            print(f"Type: {info['type']}")
            print(f"File: {info['file']}")
            print(f"Line: {info['line']}")
        
        print("\n" + "=" * 70)
        print("Deanonymization complete!")
        print("=" * 70)


if __name__ == "__main__":
    main()

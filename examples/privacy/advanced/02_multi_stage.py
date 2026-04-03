"""Multi-stage anonymization example.

Demonstrates different anonymization levels for different audiences:
1. Level 1: Internal review (minimal anonymization)
2. Level 2: External contractor (moderate anonymization)  
3. Level 3: Public LLM API (full anonymization)
"""

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from llx.privacy.project import AnonymizationContext, ProjectAnonymizer
from llx.privacy.deanonymize import ProjectDeanonymizer
from llx.privacy import Anonymizer


@dataclass
class AnonymizationLevel:
    """Configuration for a specific anonymization level."""
    name: str
    description: str
    enable_ast: bool
    enable_content: bool
    exclude_patterns: list[str]


class MultiStageAnonymizer:
    """Manages multiple anonymization levels for different use cases."""
    
    LEVELS = {
        "internal": AnonymizationLevel(
            name="Internal Review",
            description="Minimal anonymization - only secrets and PII",
            enable_ast=False,
            enable_content=True,
            exclude_patterns=["email", "phone"]  # Keep contact info
        ),
        "contractor": AnonymizationLevel(
            name="External Contractor",
            description="Moderate anonymization - AST symbols + secrets",
            enable_ast=True,
            enable_content=True,
            exclude_patterns=[]
        ),
        "public": AnonymizationLevel(
            name="Public LLM API",
            description="Full anonymization - everything",
            enable_ast=True,
            enable_content=True,
            exclude_patterns=[]
        ),
    }
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.contexts: dict[str, AnonymizationContext] = {}
    
    def anonymize_for_level(
        self, 
        level: Literal["internal", "contractor", "public"],
        files: dict[str, str]
    ) -> tuple[dict[str, str], AnonymizationContext]:
        """Anonymize files for specific level."""
        config = self.LEVELS[level]
        
        print(f"\nApplying: {config.name}")
        print(f"Description: {config.description}")
        
        # Create context for this level
        ctx = AnonymizationContext(
            project_path=self.project_path,
            salt=f"salt_{level}_2024"  # Different salt per level
        )
        
        # Disable certain patterns for internal level
        if config.exclude_patterns:
            for pattern_name in config.exclude_patterns:
                ctx.content_anonymizer.disable_pattern(pattern_name)
        
        result_files = {}
        
        for file_path, content in files.items():
            # AST anonymization
            if config.enable_ast and file_path.endswith('.py'):
                # Use AST-based transformation
                anonymizer = ProjectAnonymizer(ctx)
                result = anonymizer.anonymize_string(content, file_path)
                result_files[file_path] = result
            else:
                # Content-only anonymization
                result = ctx.content_anonymizer.anonymize(content)
                result_files[file_path] = result.text
        
        self.contexts[level] = ctx
        return result_files, ctx
    
    def get_comparison(self, original: dict[str, str], level: str) -> dict:
        """Get comparison statistics."""
        ctx = self.contexts.get(level)
        if not ctx:
            return {}
        
        total_symbols = len(ctx.variables) + len(ctx.functions) + len(ctx.classes)
        
        return {
            "level": level,
            "level_name": self.LEVELS[level].name,
            "total_symbols": total_symbols,
            "variables": len(ctx.variables),
            "functions": len(ctx.functions),
            "classes": len(ctx.classes),
            "paths": len(ctx.paths),
        }


def create_business_logic_project(base_path: Path) -> None:
    """Create project with sensitive business logic."""
    
    (base_path / "src").mkdir(parents=True)
    
    # Core business logic with proprietary algorithms
    (base_path / "src" / "pricing_engine.py").write_text("""
\"\"\"Proprietary pricing algorithm - CONFIDENTIAL.\"\"\"
from decimal import Decimal
from typing import List, Dict

# Margin thresholds - business secret
MIN_MARGIN_PERCENT = 15.0
TARGET_MARGIN_PERCENT = 25.0
MAX_DISCOUNT_PERCENT = 10.0

class PricingEngine:
    \"\"\"Core pricing algorithm with margin optimization.\"\"\"
    
    def __init__(self, supplier_costs: Dict[str, Decimal]):
        self.supplier_costs = supplier_costs
        self.margin_cache = {}
    
    def calculate_optimal_price(
        self, 
        product_id: str,
        competitor_prices: List[Decimal],
        customer_segment: str
    ) -> Decimal:
        \"\"\"Calculate optimal price based on multiple factors.\"\"\"
        base_cost = self.supplier_costs.get(product_id, Decimal('0'))
        
        # Algorithm: cost + margin - competitive adjustment
        target_margin = Decimal(str(TARGET_MARGIN_PERCENT / 100))
        target_price = base_cost * (Decimal('1') + target_margin)
        
        # Adjust based on competition
        if competitor_prices:
            min_competitor = min(competitor_prices)
            if target_price > min_competitor * Decimal('1.05'):
                # We can be slightly more expensive if premium brand
                target_price = min_competitor * Decimal('1.03')
        
        # Segment-based adjustment
        segment_multipliers = {
            'enterprise': Decimal('1.2'),
            'smb': Decimal('1.0'),
            'startup': Decimal('0.85'),
        }
        multiplier = segment_multipliers.get(customer_segment, Decimal('1.0'))
        
        final_price = target_price * multiplier
        
        # Ensure minimum margin
        min_acceptable = base_cost * Decimal(str(1 + MIN_MARGIN_PERCENT / 100))
        if final_price < min_acceptable:
            final_price = min_acceptable
        
        return final_price.quantize(Decimal('0.01'))
    
    def apply_volume_discount(self, quantity: int, base_price: Decimal) -> Decimal:
        \"\"\"Apply volume-based discount tiers.\"\"\"
        # Secret discount tiers
        tiers = [
            (100, Decimal('0.95')),   # 5% for 100+
            (500, Decimal('0.90')),   # 10% for 500+
            (1000, Decimal('0.85')),  # 15% for 1000+
        ]
        
        discount = Decimal('1.0')
        for tier_qty, tier_discount in tiers:
            if quantity >= tier_qty:
                discount = tier_discount
        
        discounted = base_price * discount
        max_discounted = base_price * Decimal(str(1 - MAX_DISCOUNT_PERCENT / 100))
        
        # Never exceed max discount
        if discounted < max_discounted:
            discounted = max_discounted
        
        return discounted

class CompetitorMonitor:
    \"\"\"Monitor competitor pricing (scraper).\"\"\"
    
    COMPETITOR_URLS = [
        'https://api.competitor-a.com/prices',
        'https://api.competitor-b.com/v2/products',
    ]
    
    def fetch_competitor_prices(self, sku_list: List[str]) -> Dict[str, Decimal]:
        \"\"\"Fetch current prices from competitors.\"\"\"
        results = {}
        for url in self.COMPETITOR_URLS:
            # API calls to competitors
            prices = self._scrape_prices(url, sku_list)
            results.update(prices)
        return results
    
    def _scrape_prices(self, url: str, skus: List[str]) -> Dict[str, Decimal]:
        \"\"\"Internal scraping method.\"\"\"
        # Implementation would use API keys, etc.
        return {sku: Decimal('99.99') for sku in skus}
""")
    
    # Customer data handler
    (base_path / "src" / "customer_data.py").write_text("""
\"\"\"Customer data management with PII.\"\"\"
from typing import Optional
from datetime import datetime

class CustomerProfile:
    \"\"\"Complete customer profile with sensitive data.\"\"\"
    
    def __init__(
        self,
        customer_id: str,
        email: str,
        phone: str,
        billing_address: str,
        credit_card_last4: str,
        credit_score: Optional[int] = None
    ):
        self.customer_id = customer_id
        self.email = email
        self.phone = phone
        self.billing_address = billing_address
        self.credit_card_last4 = credit_card_last4
        self.credit_score = credit_score
        self.created_at = datetime.now()
    
    def get_risk_score(self) -> float:
        \"\"\"Calculate credit risk score.\"\"\"
        if not self.credit_score:
            return 0.5  # Unknown risk
        
        # Risk calculation algorithm
        if self.credit_score > 750:
            return 0.1  # Low risk
        elif self.credit_score > 650:
            return 0.3  # Medium risk
        else:
            return 0.7  # High risk
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        \"\"\"Export to dictionary.\"\"\"
        data = {
            'customer_id': self.customer_id,
            'created_at': self.created_at.isoformat(),
        }
        
        if include_sensitive:
            data['email'] = self.email
            data['phone'] = self.phone
            data['billing_address'] = self.billing_address
            data['credit_card_last4'] = self.credit_card_last4
            data['credit_score'] = self.credit_score
        
        return data

class CustomerRepository:
    \"\"\"Database access for customers.\"\"\"
    
    DB_CONNECTION = "postgresql://crm_user:SecretPassword@db.company.com:5432/customers"
    
    def find_by_email(self, email: str) -> Optional[CustomerProfile]:
        \"\"\"Find customer by email.\"\"\"
        # Database query
        if email == "vip@enterprise.com":
            return CustomerProfile(
                customer_id="CUST-12345",
                email=email,
                phone="+1 555 123 4567",
                billing_address="123 Corporate Blvd, New York, NY 10001",
                credit_card_last4="4242",
                credit_score=780
            )
        return None
    
    def get_vip_customers(self) -> list:
        \"\"\"Get list of VIP customers.\"\"\"
        # Internal VIP list
        return ["vip@enterprise.com", "ceo@bigcorp.com"]
""")


def main():
    print("=" * 80)
    print("LLX Privacy: Multi-Stage Anonymization Example")
    print("=" * 80)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir) / "business_platform"
        project_path.mkdir()
        
        # Create project
        print("\n1. CREATING BUSINESS PLATFORM PROJECT")
        print("-" * 60)
        create_business_logic_project(project_path)
        
        # Read original files
        files = {}
        for py_file in project_path.rglob("*.py"):
            rel_path = str(py_file.relative_to(project_path))
            files[rel_path] = py_file.read_text()
        
        print(f"Loaded {len(files)} Python files")
        
        # Show original
        print("\n2. ORIGINAL CODE (pricing_engine.py snippet):")
        print("-" * 60)
        original_snippet = files["src/pricing_engine.py"][:800]
        print(original_snippet)
        print("...")
        
        # Initialize multi-stage anonymizer
        multi_anon = MultiStageAnonymizer(project_path)
        
        # Level 1: Internal Review
        print("\n" + "=" * 80)
        print("LEVEL 1: INTERNAL REVIEW")
        print("=" * 80)
        
        internal_files, internal_ctx = multi_anon.anonymize_for_level(
            "internal", files
        )
        
        print("\nAnonymized (secrets only, code names preserved):")
        print(internal_files["src/pricing_engine.py"][:600])
        
        stats = multi_anon.get_comparison(files, "internal")
        print(f"\nStats: {stats}")
        
        # Level 2: External Contractor
        print("\n" + "=" * 80)
        print("LEVEL 2: EXTERNAL CONTRACTOR")
        print("=" * 80)
        
        contractor_files, contractor_ctx = multi_anon.anonymize_for_level(
            "contractor", files
        )
        
        print("\nAnonymized (AST + secrets, code structure visible):")
        print(contractor_files["src/pricing_engine.py"][:600])
        
        stats = multi_anon.get_comparison(files, "contractor")
        print(f"\nStats: {stats['total_symbols']} symbols anonymized")
        
        # Show some mappings
        print("\nSample symbol mappings:")
        for i, (orig, mapping) in enumerate(list(contractor_ctx.functions.items())[:3]):
            print(f"  {mapping.anonymized} -> {orig}")
        
        # Level 3: Public LLM API
        print("\n" + "=" * 80)
        print("LEVEL 3: PUBLIC LLM API (Maximum Protection)")
        print("=" * 80)
        
        public_files, public_ctx = multi_anon.anonymize_for_level(
            "public", files
        )
        
        print("\nAnonymized (full protection):")
        print(public_files["src/pricing_engine.py"][:600])
        
        stats = multi_anon.get_comparison(files, "public")
        print(f"\nStats: {stats['total_symbols']} symbols anonymized")
        
        # Compare levels
        print("\n" + "=" * 80)
        print("COMPARISON OF ALL LEVELS")
        print("=" * 80)
        
        comparison_data = []
        for level in ["internal", "contractor", "public"]:
            stats = multi_anon.get_comparison(files, level)
            comparison_data.append(stats)
        
        print(f"\n{'Level':<20} {'Symbols':<10} {'Functions':<10} {'Classes':<10}")
        print("-" * 50)
        for data in comparison_data:
            print(f"{data['level_name']:<20} {data['total_symbols']:<10} "
                  f"{data['functions']:<10} {data['classes']:<10}")
        
        # Simulate contractor review
        print("\n" + "=" * 80)
        print("SIMULATING CONTRACTOR REVIEW WORKFLOW")
        print("=" * 80)
        
        # Contractor sends anonymized feedback
        contractor_feedback = """
The PricingEngine class needs refactoring:
1. fn_a1b2c3 is too complex - split into smaller functions
2. var_d4e5f6 cache is never invalidated
3. CompetitorMonitor should use dependency injection
"""
        
        print("Contractor feedback (anonymized):")
        print(contractor_feedback)
        
        # Deanonymize for internal team
        deanonymizer = ProjectDeanonymizer(contractor_ctx)
        internal_feedback = deanonymizer.deanonymize_text(contractor_feedback)
        
        print("\nDeanonymized for internal team:")
        print(internal_feedback.text)
        
        print("\n" + "=" * 80)
        print("Example completed!")
        print("=" * 80)
        print("\nUse cases for each level:")
        print("  • Internal: Team code review, documentation")
        print("  • Contractor: External consultants (NDA required)")
        print("  • Public: StackOverflow, open forums, public LLMs")


if __name__ == "__main__":
    main()

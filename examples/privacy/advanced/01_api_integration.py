"""Complex example: Real-world API with anonymization layer.

Simulates a complete workflow:
1. Create realistic project with sensitive data
2. Anonymize before sending to external LLM API
3. Simulate LLM API request/response
4. Deanonymize the response
5. Apply changes back to project
"""

import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from llx.privacy.project import AnonymizationContext, ProjectAnonymizer
from llx.privacy.deanonymize import ProjectDeanonymizer


@dataclass
class SimulatedLLMResponse:
    """Simulated LLM API response."""
    request_id: str
    model: str
    anonymized_content: str
    tokens_used: int


class SimulatedLLMAPI:
    """Simulates external LLM API (like OpenAI, Anthropic, etc.)."""
    
    def __init__(self, model: str = "claude-sonnet-4"):
        self.model = model
        self.request_count = 0
    
    def send_prompt(self, anonymized_code: str, prompt: str) -> SimulatedLLMResponse:
        """Simulate sending anonymized code to LLM API."""
        self.request_count += 1
        
        # Simulate LLM analyzing code and providing suggestions
        # Note: LLM only sees anonymized names (fn_*, var_*, etc.)
        
        # Extract some anonymized function names for the response
        import re
        fn_names = re.findall(r'fn_[a-f0-9]{6}', anonymized_code)[:3]
        var_names = re.findall(r'var_[a-f0-9]{6}', anonymized_code)[:2]
        cls_names = re.findall(r'cls_[a-f0-9]{6}', anonymized_code)[:1]
        
        # Generate suggestion using anonymized names
        suggestions = f"""
Code Review Results:

1. Function `{fn_names[0] if fn_names else 'fn_xxx'}` has high complexity.
   Recommendation: Extract helper functions from `{fn_names[0] if fn_names else 'fn_xxx'}`.

2. Variable `{var_names[0] if var_names else 'var_xxx'}` is reassigned multiple times.
   Consider making it immutable or using `{var_names[1] if len(var_names) > 1 else 'var_yyy'}` pattern.

3. Class `{cls_names[0] if cls_names else 'cls_xxx'}` has tight coupling.
   Suggestion: Apply dependency injection to `{cls_names[0] if cls_names else 'cls_xxx'}`.

Refactoring priority: HIGH for `{fn_names[0] if fn_names else 'fn_xxx'}`.
Estimated effort: 2-3 hours.
"""
        
        return SimulatedLLMResponse(
            request_id=f"req_{self.request_count:04d}",
            model=self.model,
            anonymized_content=suggestions,
            tokens_used=len(anonymized_code.split()) + len(prompt.split()),
        )


def create_realistic_project(base_path: Path) -> None:
    """Create a realistic e-commerce project structure."""
    
    # Project structure
    (base_path / "src" / "services").mkdir(parents=True)
    (base_path / "src" / "models").mkdir(parents=True)
    (base_path / "src" / "utils").mkdir(parents=True)
    (base_path / "tests").mkdir(parents=True)
    (base_path / "config").mkdir(parents=True)
    
    # Payment service with sensitive data
    (base_path / "src" / "services" / "payment_service.py").write_text("""
\"\"\"Payment processing service with Stripe integration.\"\"\"
import stripe
from datetime import datetime
from typing import Optional

STRIPE_API_KEY = "sk_live_EXAMPLE_DUMMY_KEY_NOT_REAL"
WEBHOOK_SECRET = "whsec_1234567890abcdef"

class PaymentProcessor:
    \"\"\"Handles payment processing and refunds.\"\"\"
    
    def __init__(self, merchant_id: str):
        self.merchant_id = merchant_id
        self.stripe_client = stripe.Client(STRIPE_API_KEY)
        self.processed_count = 0
    
    def process_payment(
        self, 
        customer_email: str, 
        amount_cents: int,
        payment_method_id: str
    ) -> dict:
        \"\"\"Process a single payment transaction.\"\"\"
        customer = self._find_or_create_customer(customer_email)
        
        payment_intent = self.stripe_client.payment_intents.create(
            amount=amount_cents,
            currency='usd',
            customer=customer.id,
            payment_method=payment_method_id,
            confirm=True
        )
        
        self.processed_count += 1
        
        return {
            'success': payment_intent.status == 'succeeded',
            'transaction_id': payment_intent.id,
            'amount': amount_cents,
            'customer_email': customer_email
        }
    
    def _find_or_create_customer(self, email: str) -> stripe.Customer:
        \"\"\"Find existing customer or create new one.\"\"\"
        customers = self.stripe_client.customers.list(email=email)
        if customers.data:
            return customers.data[0]
        return self.stripe_client.customers.create(email=email)
    
    def handle_webhook(self, payload: bytes, signature: str) -> bool:
        \"\"\"Validate and process Stripe webhook.\"\"\"
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, WEBHOOK_SECRET
            )
            
            if event['type'] == 'payment_intent.succeeded':
                self._handle_successful_payment(event['data']['object'])
            
            return True
        except stripe.error.SignatureVerificationError:
            return False
    
    def _handle_successful_payment(self, payment_data: dict) -> None:
        \"\"\"Internal handler for successful payments.\"\"\"
        transaction_id = payment_data['id']
        amount_received = payment_data['amount_received']
        
        # Update database
        self._update_transaction_status(transaction_id, 'completed')
        self._send_confirmation_email(payment_data['receipt_email'])
    
    def _update_transaction_status(self, tx_id: str, status: str) -> None:
        \"\"\"Update transaction in database.\"\"\"
        pass  # Implementation omitted
    
    def _send_confirmation_email(self, email: str) -> None:
        \"\"\"Send email confirmation to customer.\"\"\"
        pass  # Implementation omitted

class RefundManager:
    \"\"\"Handles refund processing.\"\"\"
    
    def __init__(self, processor: PaymentProcessor):
        self.processor = processor
        self.refund_threshold = 10000  # $100.00
    
    def process_refund(self, transaction_id: str, reason: str) -> dict:
        \"\"\"Process refund for a transaction.\"\"\"
        transaction = self._get_transaction(transaction_id)
        
        if transaction['amount'] > self.refund_threshold:
            # Requires manual approval
            return {'status': 'pending_approval', 'transaction_id': transaction_id}
        
        refund = self.processor.stripe_client.refunds.create(
            payment_intent=transaction['payment_intent_id'],
            reason=reason
        )
        
        return {
            'success': refund.status == 'succeeded',
            'refund_id': refund.id,
            'amount': transaction['amount']
        }
    
    def _get_transaction(self, tx_id: str) -> dict:
        \"\"\"Fetch transaction from database.\"\"\"
        return {
            'id': tx_id,
            'amount': 5000,
            'payment_intent_id': 'pi_1234567890'
        }
""")
    
    # User model with PII
    (base_path / "src" / "models" / "user.py").write_text("""
\"\"\"User model with PII handling.\"\"\"
from dataclasses import dataclass
from typing import Optional
import hashlib

@dataclass
class User:
    \"\"\"User account with sensitive information.\"\"\"
    id: int
    email: str
    full_name: str
    phone_number: Optional[str] = None
    pesel: Optional[str] = None  # Polish national ID
    
    def __post_init__(self):
        self._validate_pesel()
    
    def _validate_pesel(self) -> None:
        \"\"\"Validate Polish PESEL number checksum.\"\"\"
        if not self.pesel:
            return
        
        if len(self.pesel) != 11:
            raise ValueError("PESEL must be 11 digits")
        
        weights = [1, 3, 7, 9, 1, 3, 7, 9, 1, 3]
        checksum = sum(int(self.pesel[i]) * weights[i] for i in range(10))
        checksum = (10 - (checksum % 10)) % 10
        
        if checksum != int(self.pesel[10]):
            raise ValueError("Invalid PESEL checksum")
    
    def get_masked_email(self) -> str:
        \"\"\"Return email with masked domain.\"\"\"
        local, domain = self.email.split('@')
        return f\"{local[:2]}***@{domain}\"
    
    def to_dict(self, secure: bool = True) -> dict:
        \"\"\"Convert to dictionary.\"\"\"
        data = {
            'id': self.id,
            'email': self.get_masked_email() if secure else self.email,
            'full_name': self.full_name,
        }
        if not secure:
            data['phone_number'] = self.phone_number
            data['pesel'] = self._mask_pesel()
        return data
    
    def _mask_pesel(self) -> str:
        \"\"\"Mask PESEL for display.\"\"\"
        if not self.pesel:
            return ''
        return f\"{self.pesel[:2]}******{self.pesel[-2:]}\"

class UserRepository:
    \"\"\"Database repository for users.\"\"\"
    
    def __init__(self, db_connection_string: str):
        self.db_url = db_connection_string
    
    def find_by_email(self, email: str) -> Optional[User]:
        \"\"\"Find user by email address.\"\"\"
        # Simulated database query
        if email == "admin@company.com":
            return User(
                id=1,
                email="admin@company.com",
                full_name="Admin User",
                phone_number="+48 123 456 789",
                pesel="90010112345"
            )
        return None
    
    def find_by_pesel(self, pesel: str) -> Optional[User]:
        \"\"\"Find user by PESEL number.\"\"\"
        # This is sensitive - PESEL lookup
        pass
""")
    
    # Configuration with secrets
    (base_path / "config" / "production.yaml").write_text("""
# Production configuration - SENSITIVE
database:
  host: prod-db-01.internal.company.com
  port: 5432
  username: app_user
  password: SuperSecretDBPassword123!
  ssl_mode: require

api_keys:
  stripe: sk_live_EXAMPLE_DUMMY_KEY_NOT_REAL
  sendgrid: SG.1234567890.abcdef
  sentry: https://abc123@sentry.company.com/1

encryption:
  master_key: aes256-gcm-master-key-here
  salt: random_salt_value_123

endpoints:
  internal_api: https://api.internal.company.com/v2
  payment_gateway: https://payments.stripe.com/api/v1
""")
    
    # Utils with sensitive paths
    (base_path / "src" / "utils" / "helpers.py").write_text("""
\"\"\"Utility functions.\"\"\"
import os
from pathlib import Path

HOME_DIR = "/home/appuser"
LOG_PATH = "/var/log/myapp"
CONFIG_PATH = "/etc/myapp/config"

class FileManager:
    \"\"\"File management utilities.\"\"\"
    
    def __init__(self, base_path: str = HOME_DIR):
        self.base_path = Path(base_path)
    
    def get_user_file(self, user_id: int, filename: str) -> Path:
        \"\"\"Get path to user-specific file.\"\"\"
        return self.base_path / "users" / str(user_id) / filename
    
    def get_log_file(self, date: str) -> Path:
        \"\"\"Get log file for specific date.\"\"\"
        return Path(LOG_PATH) / f\"app-{date}.log\"
""")
    
    # Main application
    (base_path / "src" / "main.py").write_text("""
\"\"\"Main application entry point.\"\"\"
from services.payment_service import PaymentProcessor, RefundManager
from models.user import User, UserRepository
import os

def main():
    \"\"\"Initialize and run the application.\"\"\"
    # Load configuration
    db_url = os.getenv('DATABASE_URL', 'postgresql://localhost/myapp')
    
    # Initialize services
    user_repo = UserRepository(db_url)
    payment_processor = PaymentProcessor(merchant_id="merch_1234567890")
    refund_manager = RefundManager(payment_processor)
    
    # Example workflow
    user = user_repo.find_by_email("customer@example.com")
    if user:
        result = payment_processor.process_payment(
            customer_email=user.email,
            amount_cents=9999,  # $99.99
            payment_method_id="pm_1234567890"
        )
        print(f"Payment result: {result}")

if __name__ == "__main__":
    main()
""")
    
    # Test file
    (base_path / "tests" / "test_payment.py").write_text("""
\"\"\"Tests for payment service.\"\"\"
import pytest
from services.payment_service import PaymentProcessor

def test_process_payment():
    processor = PaymentProcessor(merchant_id="test_merch")
    result = processor.process_payment(
        customer_email="test@example.com",
        amount_cents=1000,
        payment_method_id="pm_test"
    )
    assert 'success' in result
""")


def main():
    print("=" * 80)
    print("LLX Privacy: Complex Real-World API Integration Example")
    print("=" * 80)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir) / "ecommerce_platform"
        project_path.mkdir()
        
        # Step 1: Create realistic project
        print("\n1. CREATING REALISTIC E-COMMERCE PROJECT")
        print("-" * 60)
        create_realistic_project(project_path)
        
        # List created structure
        print("Project structure:")
        for f in sorted(project_path.rglob("*")):
            if f.is_file():
                rel = f.relative_to(project_path)
                size = f.stat().st_size
                print(f"  {rel} ({size} bytes)")
        
        # Show sensitive content
        print("\n2. SENSITIVE DATA IN PROJECT (before anonymization):")
        print("-" * 60)
        
        config_content = (project_path / "config" / "production.yaml").read_text()
        print("Config file contains:")
        for line in config_content.split("\n"):
            if any(x in line.lower() for x in ["password", "secret", "key", "token", "api"]):
                print(f"  ⚠️  {line.strip()}")
        
        payment_content = (project_path / "src" / "services" / "payment_service.py").read_text()
        if "sk_live_" in payment_content:
            print("  ⚠️  Payment service contains Stripe live API key!")
        
        user_content = (project_path / "src" / "models" / "user.py").read_text()
        if "pesel" in user_content:
            print("  ⚠️  User model handles PESEL (Polish national ID)")
        
        # Step 2: Anonymize project
        print("\n3. ANONYMIZING ENTIRE PROJECT")
        print("-" * 60)
        
        ctx = AnonymizationContext(project_path=project_path)
        anonymizer = ProjectAnonymizer(ctx)
        
        result = anonymizer.anonymize_project(
            include_patterns=["*.py", "*.yaml", "*.yml", "*.json"],
            exclude_patterns=["**/__pycache__/**", "**/.git/**"],
        )
        
        print(f"Files processed: {len(result.files)}")
        print(f"\nSymbol mappings created:")
        print(f"  Variables: {len(ctx.variables)}")
        print(f"  Functions: {len(ctx.functions)}")
        print(f"  Classes: {len(ctx.classes)}")
        
        # Verify sensitive data is masked
        print("\n4. VERIFYING ANONYMIZATION")
        print("-" * 60)
        
        anon_config = result.files.get("config/production.yaml", "")
        if "SuperSecretDBPassword123!" not in anon_config and "[PASSWORD_" in anon_config:
            print("  ✅ Database password anonymized")
        
        if "sk_live_EXAMPLE_DUMMY_KEY_NOT_REAL" not in anon_config:
            print("  ✅ Stripe API key anonymized in config")
        
        anon_payment = result.files.get("src/services/payment_service.py", "")
        if "sk_live_" not in anon_payment:
            print("  ✅ Stripe API key anonymized in payment service")
        
        anon_user = result.files.get("src/models/user.py", "")
        if "90010112345" not in anon_user and "[PESEL_" in anon_user:
            print("  ✅ PESEL numbers anonymized")
        
        # Save context for API request
        context_path = project_path / "anonymization_context.json"
        ctx.save(context_path)
        
        # Step 3: Simulate API request to LLM
        print("\n5. SIMULATING LLM API REQUEST")
        print("-" * 60)
        
        # Prepare anonymized payload
        payment_code = result.files["src/services/payment_service.py"]
        user_code = result.files["src/models/user.py"]
        
        prompt = f"""Review the following code for security issues and refactoring opportunities:

Payment Service:
```python
{payment_code[:2000]}
```

User Model:
```python
{user_code[:1500]}
```

Please identify:
1. Security vulnerabilities
2. Code smells and refactoring opportunities  
3. Performance issues
"""
        
        print("Sending anonymized code to LLM API...")
        print(f"Prompt size: {len(prompt)} characters")
        
        # Simulate API call
        llm_api = SimulatedLLMAPI(model="claude-sonnet-4")
        api_response = llm_api.send_prompt(
            anonymized_code=payment_code,
            prompt="Review for security issues"
        )
        
        print(f"API Response received:")
        print(f"  Request ID: {api_response.request_id}")
        print(f"  Model: {api_response.model}")
        print(f"  Tokens used: {api_response.tokens_used}")
        
        # Step 4: Deanonymize response
        print("\n6. DEANONYMIZING API RESPONSE")
        print("-" * 60)
        
        print("LLM Response (with anonymized names):")
        print(api_response.anonymized_content[:500])
        
        deanonymizer = ProjectDeanonymizer(ctx)
        restored_response = deanonymizer.deanonymize_text(api_response.anonymized_content)
        
        print(f"\nDeanonymized Response (with original names):")
        print(restored_response.text)
        
        # Show some restorations
        print(f"\nRestorations made ({len(restored_response.restorations)}):")
        for token, original in restored_response.restorations[:5]:
            print(f"  {token} → {original}")
        
        # Step 5: Apply to project
        print("\n7. APPLYING SUGGESTIONS TO PROJECT")
        print("-" * 60)
        print("In a real scenario, you would:")
        print("  1. Review deanonymized suggestions")
        print("  2. Apply relevant changes to original code")
        print("  3. Run tests to verify correctness")
        print("  4. Commit changes to version control")
        
        print("\n" + "=" * 80)
        print("Example completed successfully!")
        print("=" * 80)
        print("\nKey takeaways:")
        print("  • Sensitive data never leaves your system in raw form")
        print("  • LLM receives only anonymized code (fn_*, var_*, etc.)")
        print("  • Response is deanonymized before human review")
        print("  • Context file allows secure round-trip conversion")


if __name__ == "__main__":
    main()

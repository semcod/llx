"""CI/CD integration example.

Demonstrates integrating privacy anonymization into CI/CD pipeline:
1. Pre-commit: Scan for sensitive data
2. Pre-deploy: Anonymize for external security audit
3. Post-audit: Deanonymize and apply fixes
"""

import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from llx.privacy.project import AnonymizationContext, ProjectAnonymizer
from llx.privacy.deanonymize import ProjectDeanonymizer
from llx.privacy import Anonymizer


@dataclass
class SecurityScanResult:
    """Result of security scan."""
    file_path: str
    findings: dict[str, list[str]]
    risk_level: str  # low, medium, high, critical


class CICDPrivacyPipeline:
    """Privacy pipeline for CI/CD integration."""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.scan_results: list[SecurityScanResult] = []
        self.context: Optional[AnonymizationContext] = None
        self.anon_result: Optional[Any] = None
    
    def step1_pre_commit_scan(self) -> bool:
        """Step 1: Scan for sensitive data before commit."""
        print("\n" + "=" * 60)
        print("STEP 1: Pre-Commit Security Scan")
        print("=" * 60)
        
        anonymizer = Anonymizer()
        has_critical_findings = False
        
        # Scan all source files
        for py_file in self.project_path.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            
            content = py_file.read_text()
            findings = anonymizer.scan(content)
            
            if findings:
                # Determine risk level
                risk = self._assess_risk(findings)
                
                if risk in ["high", "critical"]:
                    has_critical_findings = True
                
                result = SecurityScanResult(
                    file_path=str(py_file.relative_to(self.project_path)),
                    findings=findings,
                    risk_level=risk
                )
                self.scan_results.append(result)
                
                print(f"\n⚠️  {result.file_path} [{result.risk_level.upper()}]")
                for pattern, matches in findings.items():
                    print(f"   Found: {pattern}")
                    for match in matches[:3]:  # Limit output
                        print(f"     - {match[:50]}...")
        
        if has_critical_findings:
            print("\n❌ CRITICAL: Sensitive data detected!")
            print("   Commit blocked. Run: python anonymize_secrets.py")
            return False
        
        if self.scan_results:
            print(f"\n⚠️  Found {len(self.scan_results)} files with sensitive data")
            print("   Consider anonymizing before commit")
        else:
            print("\n✅ No sensitive data detected")
        
        return True
    
    def _assess_risk(self, findings: dict) -> str:
        """Assess risk level based on findings."""
        critical_patterns = ['api_key', 'password', 'secret', 'token']
        high_patterns = ['credit_card', 'pesel', 'email']
        
        for pattern in findings.keys():
            if any(crit in pattern.lower() for crit in critical_patterns):
                return 'critical'
        
        for pattern in findings.keys():
            if any(high in pattern.lower() for high in high_patterns):
                return 'high'
        
        return 'medium'
    
    def step2_anonymize_for_audit(self, output_dir: Path) -> Path:
        """Step 2: Anonymize project for external security audit."""
        print("\n" + "=" * 60)
        print("STEP 2: Anonymize for External Security Audit")
        print("=" * 60)
        
        self.context = AnonymizationContext(project_path=self.project_path)
        anonymizer = ProjectAnonymizer(self.context)
        
        result = anonymizer.anonymize_project(
            include_patterns=["*.py", "*.yaml", "*.yml", "*.json"],
            exclude_patterns=[
                "**/__pycache__/**",
                "**/node_modules/**",
                "**/.git/**",
                "**/tests/**",  # Skip tests for audit
            ],
        )
        
        self.anon_result = result  # Store for reporting
        
        # Save anonymized files
        output_dir.mkdir(parents=True, exist_ok=True)
        for file_path, content in result.files.items():
            target = output_dir / file_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
        
        # Save context
        context_path = output_dir / ".audit_context.json"
        self.context.save(context_path)
        
        print(f"✅ Anonymized {len(result.files)} files to {output_dir}")
        print(f"✅ Context saved to {context_path}")
        print(f"\nStatistics:")
        print(f"  Variables: {len(self.context.variables)}")
        print(f"  Functions: {len(self.context.functions)}")
        print(f"  Classes: {len(self.context.classes)}")
        
        return context_path
    
    def step3_simulate_audit_response(self, audit_findings: str) -> str:
        """Step 3: Simulate external audit findings."""
        print("\n" + "=" * 60)
        print("STEP 3: Simulate External Audit Response")
        print("=" * 60)
        
        print("Raw audit findings (anonymized):")
        print(audit_findings[:500])
        
        if not self.context:
            raise ValueError("Context not available. Run step 2 first.")
        
        deanonymizer = ProjectDeanonymizer(self.context)
        restored = deanonymizer.deanonymize_text(audit_findings)
        
        print("\nDeanonymized findings (for internal team):")
        print(restored.text[:500])
        
        return restored.text
    
    def step4_generate_report(self, output_path: Path) -> None:
        """Step 4: Generate audit report."""
        print("\n" + "=" * 60)
        print("STEP 4: Generate Audit Report")
        print("=" * 60)
        
        report = {
            "pipeline_version": "1.0.0",
            "scan_summary": {
                "total_files_scanned": len(self.scan_results),
                "critical_findings": sum(1 for r in self.scan_results if r.risk_level == "critical"),
                "high_findings": sum(1 for r in self.scan_results if r.risk_level == "high"),
            },
            "anonymization_summary": {
                "total_files": len(self.anon_result.files) if self.anon_result else 0,
                "variables_anonymized": len(self.context.variables) if self.context else 0,
                "functions_anonymized": len(self.context.functions) if self.context else 0,
                "classes_anonymized": len(self.context.classes) if self.context else 0,
            },
            "recommendations": [
                "Move secrets to environment variables",
                "Use secret management service (Vault, AWS Secrets Manager)",
                "Implement pre-commit hooks for secret detection",
            ]
        }
        
        output_path.write_text(json.dumps(report, indent=2))
        print(f"✅ Report generated: {output_path}")


def create_cicd_project(base_path: Path) -> None:
    """Create sample project for CI/CD demo."""
    
    (base_path / "src" / "app").mkdir(parents=True)
    (base_path / "config").mkdir(parents=True)
    
    # Application code with secrets (BAD PRACTICE - for demo)
    (base_path / "src" / "app" / "database.py").write_text("""
\"\"\"Database configuration - DO NOT COMMIT SECRETS.\"\"\"

# WARNING: This is for demonstration - never hardcode secrets!
DB_CONFIG = {
    'host': 'prod-db-01.company.com',
    'port': 5432,
    'username': 'app_user',
    'password': 'SuperSecretPassword123!',  # CRITICAL: Hardcoded password
    'database': 'production'
}

# API Keys - should be in environment variables
STRIPE_API_KEY = "sk_live_EXAMPLE_DUMMY_KEY_NOT_REAL"
SENDGRID_API_KEY = "SG.1234567890.abcdef"

class DatabaseConnection:
    def __init__(self):
        self.connection_string = f"postgresql://{DB_CONFIG['username']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}"
    
    def connect(self):
        import psycopg2
        return psycopg2.connect(self.connection_string)
""")
    
    # Customer model with PII
    (base_path / "src" / "app" / "customer.py").write_text("""
\"\"\"Customer management with PII.\"\"\"
from typing import Optional

class Customer:
    def __init__(
        self, 
        customer_id: int,
        email: str,
        phone: str,
        ssn: str,  # US Social Security Number
        credit_card: str
    ):
        self.customer_id = customer_id
        self.email = email  # PII
        self.phone = phone  # PII
        self.ssn = ssn      # HIGH RISK
        self.credit_card = credit_card  # CRITICAL
    
    def to_dict(self) -> dict:
        return {
            'id': self.customer_id,
            'email': self.email,
            'phone': self.phone,
            'ssn': self.ssn,  # Never expose in API!
            'credit_card': self.credit_card  # Never expose!
        }
""")
    
    # Config with secrets
    (base_path / "config" / "secrets.yaml").write_text("""
# PRODUCTION SECRETS - DO NOT COMMIT
database:
  password: AnotherSecretPassword456!
  encryption_key: AES256-KEY-HERE

api_keys:
  stripe: sk_live_EXAMPLE_DUMMY_KEY_NOT_REAL
  aws_access_key: AKIAIOSFODNN7EXAMPLE
  aws_secret_key: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
""")
    
    # Good example - no secrets
    (base_path / "src" / "app" / "utils.py").write_text("""
\"\"\"Utility functions - no secrets here.\"\"\"
import os

def get_db_url():
    \"\"\"Get database URL from environment.\"\"\"
    return os.getenv('DATABASE_URL')

def format_currency(amount):
    \"\"\"Format amount as currency.\"\"\"
    return f"${amount:.2f}"
""")


def main():
    print("=" * 80)
    print("LLX Privacy: CI/CD Pipeline Integration Example")
    print("=" * 80)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir) / "webapp"
        project_path.mkdir()
        
        # Create project with secrets
        print("\n1. SETTING UP PROJECT WITH SECRETS")
        print("-" * 60)
        create_cicd_project(project_path)
        
        # List files
        print("Project structure:")
        for f in sorted(project_path.rglob("*.py")):
            print(f"  {f.relative_to(project_path)}")
        
        # Initialize pipeline
        pipeline = CICDPrivacyPipeline(project_path)
        
        # Step 1: Pre-commit scan
        can_commit = pipeline.step1_pre_commit_scan()
        
        if not can_commit:
            print("\n🚫 Commit blocked due to critical security issues!")
            print("\nRemediation steps:")
            print("  1. Move secrets to environment variables")
            print("  2. Use secret management service")
            print("  3. Add secrets to .gitignore")
        
        # Step 2: Anonymize for external audit
        audit_dir = Path(tmpdir) / "audit_package"
        context_path = pipeline.step2_anonymize_for_audit(audit_dir)
        
        print("\n📦 Audit package created:")
        for f in audit_dir.rglob("*"):
            if f.is_file():
                print(f"  {f.relative_to(audit_dir)}")
        
        # Step 3: Simulate audit response
        print("\n2. SIMULATING EXTERNAL SECURITY AUDIT")
        print("-" * 60)
        
        # Simulated audit findings using anonymized names
        anon_db = pipeline.context.variables.get('DB_CONFIG')
        db_token = anon_db.anonymized if anon_db else "var_xxx"
        
        anon_stripe = pipeline.context.variables.get('STRIPE_API_KEY')
        stripe_token = anon_stripe.anonymized if anon_stripe else "var_yyy"
        
        audit_findings = f"""
Security Audit Findings:

CRITICAL [CWE-798]: Hardcoded credentials detected in {db_token}.
  Location: src/app/database.py:6
  Risk: Credentials exposed in source control
  Remediation: Move to environment variables immediately

CRITICAL [CWE-798]: API key {stripe_token} is hardcoded.
  Location: src/app/database.py:13
  Risk: Production API key in source code
  Remediation: Use secret management service

HIGH [CWE-311]: Sensitive data exposure in Customer class.
  Fields: ssn, credit_card are returned in to_dict()
  Remediation: Remove sensitive fields from API responses
"""
        
        restored_findings = pipeline.step3_simulate_audit_response(audit_findings)
        
        # Step 4: Generate report
        report_path = Path(tmpdir) / "security_report.json"
        pipeline.step4_generate_report(report_path)
        
        print("\n📊 Report content:")
        print(report_path.read_text())
        
        # Summary
        print("\n" + "=" * 80)
        print("CI/CD INTEGRATION SUMMARY")
        print("=" * 80)
        
        print("""
Integration points:

1. Pre-commit hook (.git/hooks/pre-commit):
   
   #!/bin/bash
   python -m llx.privacy.scan --path . --fail-on-critical
   
2. GitHub Actions (.github/workflows/security.yml):
   
   - name: Security Scan
     run: |
       llx privacy scan --path src/
       llx privacy anonymize --output audit/
   
3. GitLab CI (.gitlab-ci.yml):
   
   security_scan:
     script:
       - llx privacy scan --json > findings.json
       - llx privacy anonymize --for-audit
   
4. Pre-deployment check:
   
   - Verify no hardcoded secrets
   - Anonymize for external auditors
   - Save context for post-audit restoration

Benefits:
  ✅ Prevents secrets from reaching git history
  ✅ Enables external audits without data exposure
  ✅ Maintains full round-trip capability
  ✅ Generates compliance reports automatically
""")


if __name__ == "__main__":
    main()

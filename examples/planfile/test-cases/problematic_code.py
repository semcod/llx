"""
Test module for planfile refactoring examples.
Contains various code smells and issues to fix.
"""

import json
import os
import sys
from typing import Any, Dict, List, Optional

class DataProcessor:
    """A class with multiple responsibilities and high complexity."""
    
    def __init__(self, config_file: str, api_key: str, db_url: str):
        self.config_file = config_file
        self.api_key = api_key
        self.db_url = db_url
        self.data = []
        self.processed_data = []
        self.errors = []
        self.cache = {}
        
    def load_data(self, file_path: str) -> bool:
        """Load data from file with minimal error handling."""
        try:
            with open(file_path, 'r') as f:
                self.data = json.load(f)
            return True
        except:
            return False
    
    def process_data(self) -> List[Dict]:
        """Complex method with multiple responsibilities."""
        results = []
        
        # First pass: validation
        for item in self.data:
            if not item.get('id'):
                self.errors.append("Missing ID")
                continue
                
            if item.get('value', 0) < 0:
                self.errors.append(f"Negative value for ID {item['id']}")
                continue
                
            # Duplicate validation logic
            if item.get('type') not in ['A', 'B', 'C']:
                self.errors.append(f"Invalid type for ID {item['id']}")
                continue
        
        # Second pass: transformation
        for item in self.data:
            if item.get('id') and item.get('value', 0) >= 0:
                # Complex nested conditions
                if item.get('type') == 'A':
                    if item.get('value') > 100:
                        new_item = {
                            'id': item['id'],
                            'processed_value': item['value'] * 1.1,
                            'category': 'high',
                            'metadata': {
                                'original_type': item['type'],
                                'processing_date': '2024-01-01',
                                'flags': ['important', 'review_needed']
                            }
                        }
                    else:
                        new_item = {
                            'id': item['id'],
                            'processed_value': item['value'] * 1.05,
                            'category': 'normal',
                            'metadata': {
                                'original_type': item['type'],
                                'processing_date': '2024-01-01',
                                'flags': ['standard']
                            }
                        }
                elif item.get('type') == 'B':
                    if item.get('value') > 200:
                        new_item = {
                            'id': item['id'],
                            'processed_value': item['value'] * 1.2,
                            'category': 'premium',
                            'metadata': {
                                'original_type': item['type'],
                                'processing_date': '2024-01-01',
                                'flags': ['premium', 'priority']
                            }
                        }
                    else:
                        new_item = {
                            'id': item['id'],
                            'processed_value': item['value'] * 1.15,
                            'category': 'standard',
                            'metadata': {
                                'original_type': item['type'],
                                'processing_date': '2024-01-01',
                                'flags': ['standard']
                            }
                        }
                else:  # type C
                    new_item = {
                        'id': item['id'],
                        'processed_value': item['value'] * 1.0,
                        'category': 'basic',
                        'metadata': {
                            'original_type': item['type'],
                            'processing_date': '2024-01-01',
                            'flags': ['basic']
                        }
                    }
                
                results.append(new_item)
        
        self.processed_data = results
        return results
    
    def save_data(self, output_path: str) -> bool:
        """Save processed data with basic error handling."""
        try:
            with open(output_path, 'w') as f:
                json.dump(self.processed_data, f)
            return True
        except:
            return False
    
    def generate_report(self) -> str:
        """Generate a simple text report."""
        report = f"Data Processing Report\n"
        report += f"======================\n"
        report += f"Total items: {len(self.data)}\n"
        report += f"Processed items: {len(self.processed_data)}\n"
        report += f"Errors: {len(self.errors)}\n"
        
        if self.errors:
            report += "\nErrors:\n"
            for error in self.errors:
                report += f"- {error}\n"
        
        return report


class UserManager:
    """Another class with duplicated validation logic."""
    
    def __init__(self):
        self.users = []
        self.active_users = []
    
    def add_user(self, user_data: Dict) -> bool:
        """Add user with validation - notice duplicated logic."""
        if not user_data.get('id'):
            return False
            
        if not user_data.get('email') or '@' not in user_data['email']:
            return False
            
        if user_data.get('age', 0) < 18:
            return False
            
        self.users.append(user_data)
        return True
    
    def validate_user(self, user_data: Dict) -> bool:
        """Separate validation method with duplicated checks."""
        if not user_data.get('id'):
            return False
            
        if not user_data.get('email') or '@' not in user_data['email']:
            return False
            
        if user_data.get('age', 0) < 18:
            return False
            
        return True


# Global variables and functions (no organization)
API_CONFIG = {
    'endpoint': 'https://api.example.com',
    'timeout': 30,
    'retries': 3
}

def process_api_data(data):
    """Global function with no error handling."""
    import requests
    response = requests.post(API_CONFIG['endpoint'], json=data)
    return response.json()

def calculate_metrics(data_list):
    """Another global function with complex logic."""
    total = 0
    count = 0
    maximum = 0
    minimum = float('inf')
    
    for item in data_list:
        if isinstance(item, dict) and 'value' in item:
            total += item['value']
            count += 1
            if item['value'] > maximum:
                maximum = item['value']
            if item['value'] < minimum:
                minimum = item['value']
    
    average = total / count if count > 0 else 0
    
    return {
        'total': total,
        'count': count,
        'average': average,
        'max': maximum,
        'min': minimum if minimum != float('inf') else 0
    }


# Duplicate utility function
def format_currency(amount):
    """Format currency value."""
    return f"${amount:.2f}"

def format_price(value):
    """Duplicate of format_currency."""
    return f"${value:.2f}"


# Main execution with no structure
if __name__ == "__main__":
    # Create test data
    test_data = [
        {'id': 1, 'value': 150, 'type': 'A'},
        {'id': 2, 'value': 50, 'type': 'B'},
        {'id': 3, 'value': 250, 'type': 'A'},
        {'id': 4, 'value': -10, 'type': 'C'},  # Invalid
        {'id': 5, 'value': 75, 'type': 'D'},  # Invalid type
        {'value': 100, 'type': 'A'},  # Missing ID
    ]
    
    # Process data
    processor = DataProcessor('config.json', 'api-key-123', 'sqlite:///data.db')
    processor.data = test_data
    
    results = processor.process_data()
    report = processor.generate_report()
    
    print(report)
    print(f"Processed {len(results)} items")

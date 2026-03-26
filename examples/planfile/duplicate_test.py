
def validate_user(user):
    if not user.get('email'):
        return False
    if '@' not in user['email']:
        return False
    if not user.get('name'):
        return False
    if len(user['name']) < 2:
        return False
    return True

def validate_admin(admin):
    if not admin.get('email'):
        return False
    if '@' not in admin['email']:
        return False
    if not admin.get('name'):
        return False
    if len(admin['name']) < 2:
        return False
    if not admin.get('role'):
        return False
    return True

def validate_customer(customer):
    if not customer.get('email'):
        return False
    if '@' not in customer['email']:
        return False
    if not customer.get('name'):
        return False
    if len(customer['name']) < 2:
        return False
    return True

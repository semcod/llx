class UserService:
    def __init__(self, db, cache, email_service, logger, config):
        self.db = db
        self.cache = cache
        self.email_service = email_service
        self.logger = logger
        self.config = config
    
    def process_user(self, user_id, data):
        if user_id is None:
            return None
        
        user = self.db.get_user(user_id)
        if user is None:
            return None
        
        if data.get('email') and user.email != data['email']:
            if self.validate_email(data['email']):
                user.email = data['email']
                self.email_service.send_verification(user)
        
        if data.get('name'):
            user.name = data['name']
        
        if data.get('preferences'):
            for key, value in data['preferences'].items():
                if key in user.preferences:
                    user.preferences[key] = value
        
        self.db.save_user(user)
        self.cache.invalidate(f"user:{user_id}")
        self.logger.info(f"User {user_id} updated")
        return user
    
    def validate_email(self, email):
        return '@' in email and '.' in email.split('@')[1]

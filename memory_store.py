class UserMemoryStore:
    def __init__(self):
        self.profiles = {}

    def add_user(self, profile):
        self.profiles[profile.user_id] = profile

    def get_profile(self, user_id):
        return self.profiles.get(user_id)

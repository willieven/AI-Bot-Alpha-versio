from config import USERS

def authenticate_user(username, password):
    for user_id, user_data in USERS.items():
        if user_data['FTP_USER'] == username and user_data['FTP_PASS'] == password:
            return user_id, user_data
    return None, None

def get_user_directory(user_id):
    return os.path.join(MAIN_FTP_DIRECTORY, user_id)
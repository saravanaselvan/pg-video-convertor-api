
from werkzeug.security import safe_str_cmp, check_password_hash

from models.user import UserModel


def authenticate(email, password):
    user = UserModel.find_by_email(email)
    if user and check_password_hash(str(user.password), str(password)):
        return user

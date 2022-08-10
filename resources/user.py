from flask_restful import Resource, reqparse

from models.user import UserModel
from flask_jwt_extended import create_access_token


class UserRegister(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('email', type=str, required=True,
                        help="Email required")
    parser.add_argument('username', type=str, required=True,
                        help="Username required")
    parser.add_argument('password', type=str, required=True,
                        help="Password required")

    def post(self):
        data = UserRegister.parser.parse_args()

        if UserModel.find_by_email(data['email']):
            return {"message": "Email already exists."}, 400

        user = UserModel(**data)

        user.save_to_db()

        access_token = create_access_token(identity=user.id)
        return {'user_info': {'userName': user.username, 'email': user.email, 'accessToken': access_token}}, 201


class UserList(Resource):

    def get(self):
        return {'users': [user.json() for user in UserModel.query.all()]}

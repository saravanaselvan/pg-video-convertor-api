from flask import jsonify, request
from flask_restful import Resource, reqparse
from flask_jwt_extended import create_access_token
from resources.user import UserModel

from security import authenticate


class Login(Resource):

    def post(self):
        request_data = request.get_json()
        user = authenticate(request_data['email'], request_data['password'])

        if user:
            access_token = create_access_token(identity=user.id)
            return {'user_info': {'userName': user.username, 'email': user.email, 'accessToken': access_token}}

        return {"message": "Invalid credentials"}, 401

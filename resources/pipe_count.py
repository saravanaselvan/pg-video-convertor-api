from flask_restful import Resource, reqparse
from flask_jwt_extended import jwt_required, get_jwt_identity
import services.predict_detect.predict_det2 as predict_det2
import werkzeug


class PipeCount(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('file', type=werkzeug.datastructures.FileStorage, location='files', required=True,
                        help="File is required")

    @jwt_required()
    def post(self):
        data = PipeCount.parser.parse_args()
        file = data['file'].read()
        np_image = predict_det2.input_fn(file, "application/octet-stream")
        predictor = predict_det2.model_fn("services/predict_detect")
        print(predictor)

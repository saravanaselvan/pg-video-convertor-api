from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from models.video_conversion import VideoConversionModel
from services.video_report.video_report import generate_panorama_img, generate_yaml_params, generate_pdf_report, exif_info

import os
import werkzeug
import datetime
from flask_restful import Resource, reqparse
from flask import request, current_app, json, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from db import db
import subprocess as sp
import cv2


ALLOWED_EXTENSIONS = {'mp4', 'mov'}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


class VideoConversion(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('file', type=werkzeug.datastructures.FileStorage, location='files', required=True,
                        help="File is required")
    parser.add_argument('frame_rate', type=str, required=True,
                        help="Framerate required")
    parser.add_argument('output_format', type=str, required=True,
                        help="Output Format required")
    parser.add_argument('is_exif_info_captured', type=str)

    @jwt_required()
    def post(self):
        data = VideoConversion.parser.parse_args()
        file = data['file']

        param_frame_rate = data['frame_rate']
        param_output_format = data['output_format']
        param_is_exif_info_captured = data['is_exif_info_captured'] == 'true'

        if allowed_file(file.filename):
            original_uploaded_file_name = secure_filename(file.filename)
            uploaded_file_name = f'{original_uploaded_file_name.split(".")[0]}_{datetime.datetime.now().strftime("%d_%m_%Y_%H:%M:%S")}.{original_uploaded_file_name.rsplit(".", 1)[1]}'
            input_file_path = os.path.join(
                current_app.config['UPLOAD_FOLDER'], uploaded_file_name)
            file.save(input_file_path)

            try:
                video_conversion = VideoConversionModel(
                    original_uploaded_file_name=original_uploaded_file_name,
                    uploaded_file_name=uploaded_file_name,
                    output_yaml_file_name="params.yaml",
                    param_output_format=param_output_format,
                    param_frame_rate=param_frame_rate,
                    param_is_exif_info_captured=param_is_exif_info_captured,
                )
                video_conversion.save_to_db()
            except BaseException as e:
                return f'{e}'

            video_conversion.process_video()

            return {
                "id": video_conversion.id
            }

        return "Only mp4 or wav file type is accepted", 500


class VideoConversionsList(Resource):
    parser = reqparse.RequestParser()

    @jwt_required()
    def get(self):
        video_conversions = VideoConversionModel.query.filter_by(
            user_id=get_jwt_identity()).order_by(VideoConversionModel.created_at.desc())
        return {'video_conversions': [video_conversion.json() for video_conversion in video_conversions]}


class DownloadReport(Resource):

    @jwt_required()
    def get(self, id):
        args = request.args
        type = args.get('type')

        video_conversion = VideoConversionModel.query.filter_by(
            id=id, user_id=get_jwt_identity()).first()

        if type == 'pdf' or type == None:
            file_path = video_conversion.output_pdf_file_path
        elif type == 'yaml':
            file_path = video_conversion.output_yaml_file_path

        return send_file(file_path, as_attachment=True)

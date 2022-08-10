from flask import send_file
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from models.video_conversion import VideoConversionModel

import os
import werkzeug
import datetime
from flask_restful import Resource, reqparse
from flask import request, current_app, json, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from db import db
import subprocess as sp

ALLOWED_EXTENSIONS = {'mp4', 'mov'}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


class VideoConversion(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('file', type=werkzeug.datastructures.FileStorage, location='files', required=True,
                        help="File is required")

    @jwt_required()
    def post(self):
        data = VideoConversion.parser.parse_args()
        file = data['file']
        if allowed_file(file.filename):
            original_uploaded_file_name = secure_filename(file.filename)
            uploaded_file_name = f'{original_uploaded_file_name.split(".")[0]}_{datetime.datetime.now().strftime("%d_%m_%Y_%H:%M:%S")}.{original_uploaded_file_name.rsplit(".", 1)[1]}'
            input_file_path = os.path.join(
                current_app.config['UPLOAD_FOLDER'], uploaded_file_name)
            file.save(input_file_path)

            output_path = os.path.join(
                current_app.config['OUTPUT_FOLDER'], uploaded_file_name)

            inputF = os.path.join(
                current_app.config['UPLOAD_FOLDER'], uploaded_file_name)  # Build input path
            # Build output path and add file
            outputF = os.path.join(
                current_app.config['OUTPUT_FOLDER'], "out%d.png")
            # Ffmpeg is flexible enough to handle wildstar conversions
            convertCMD = ["ffmpeg",
                          '-i', inputF, '-vf', 'fps=0.25', outputF]

            executeOrder66 = sp.Popen(convertCMD)

            try:
                outs, errs = executeOrder66.communicate()  # tell program to wait
            except TimeoutError:  # Kill if it takes too long
                proc.kill()

            try:
                video_conversion = VideoConversionModel(
                    original_uploaded_file_name=original_uploaded_file_name,
                    uploaded_file_name=uploaded_file_name,
                    output_yaml_file_name="test",
                    output_yaml_file_path="test",
                    output_pdf_file_name="test",
                    output_pdf_file_path="test",
                    param_output_format="png",
                    param_frame_rate=1,
                    param_is_exif_info_captured=False,
                )
                video_conversion.save_to_db()
            except BaseException as e:
                return f'{e}'

            return {
                "id": video_conversion.id
            }

        return "Only JSON file type is accepted", 500

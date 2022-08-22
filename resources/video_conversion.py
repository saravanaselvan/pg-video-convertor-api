from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from models.video_conversion import VideoConversionModel

import os
import werkzeug
import datetime
from flask_restful import Resource, reqparse
from flask import request, current_app, json, jsonify, send_file, render_template
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from db import db
import subprocess as sp
import cv2
from tasks.video_conversion_task import process_video
import base64
import pdfkit


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
    parser.add_argument('quality', type=str)

    @jwt_required()
    def post(self):
        data = VideoConversion.parser.parse_args()
        file = data['file']

        param_frame_rate = data['frame_rate']
        param_output_format = data['output_format']
        param_is_exif_info_captured = data['is_exif_info_captured'] == 'true'
        param_quality = data['quality']

        if allowed_file(file.filename):
            original_uploaded_file_name = secure_filename(file.filename)
            uploaded_file_name = f'{original_uploaded_file_name.split(".")[0]}_{datetime.datetime.now().strftime("%d_%m_%Y_%H:%M:%S")}.{original_uploaded_file_name.rsplit(".", 1)[1]}'
            input_file_path = os.path.join(
                current_app.config['UPLOAD_FOLDER'], uploaded_file_name)
            file.save(input_file_path)

            try:
                video_conversion = VideoConversionModel(
                    status="PENDING",
                    original_uploaded_file_name=original_uploaded_file_name,
                    uploaded_file_name=uploaded_file_name,
                    output_yaml_file_name="params.yaml",
                    param_output_format=param_output_format,
                    param_frame_rate=param_frame_rate,
                    param_is_exif_info_captured=param_is_exif_info_captured,
                    param_quality=param_quality
                )
                video_conversion.save_to_db()
            except BaseException as e:
                return f'{e}'

            process_video.delay(
                video_conversion.id, current_app.config['OUTPUT_FOLDER'], current_app.config['UPLOAD_FOLDER'])

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
        return {
                    'video_conversions': [video_conversion.json() for video_conversion in video_conversions]
                }


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
        elif type == 'json':
            file_path = video_conversion.output_exif_file_path

        return send_file(file_path, as_attachment=True)


class DownloadVideo(Resource):

    @jwt_required()
    def get(self, id):
        video_conversion = VideoConversionModel.query.filter_by(
            id=id, user_id=get_jwt_identity()).first()

        input_file_path = os.path.join(
            current_app.config['UPLOAD_FOLDER'], video_conversion.uploaded_file_name)

        return send_file(input_file_path, as_attachment=True)


class SingleVideoConversion(Resource):

    @jwt_required()
    def get(self, id):
        video_conversion = VideoConversionModel.query.filter_by(
            id=id, user_id=get_jwt_identity()).first()

        return {'video_conversion': video_conversion.json()}

def image_file_path_to_base64_string(filepath: str) -> str:
    with open(filepath, 'rb') as f:
        return base64.b64encode(f.read()).decode()

def generate_pdf_report(
        panorama_img_path,
        folder_name,
        original_uploaded_file_name,
        param_frame_rate,
        param_output_format,
        param_quality,
        param_is_exif_info_captured,
        created_at):
    exif_json = f"{current_app.config['OUTPUT_FOLDER']}/{folder_name}/exif.json"
    exif_json_dict = {}
    if param_is_exif_info_captured:
        with open(exif_json, 'r') as file:
            exif_json_dict = json.loads(file.read())

    key_list = ["FileType", "Duration", "FileSize", "BitDepth", "VideoFrameRate", "Rotation", "XResolution", "YResolution"]
    rendered = render_template(
        "report_template.html",
        img_string=image_file_path_to_base64_string(panorama_img_path),
        logo=image_file_path_to_base64_string("templates/pg-icon.png"),
        original_uploaded_file_name=original_uploaded_file_name,
        param_frame_rate=param_frame_rate,
        param_output_format=param_output_format,
        param_is_exif_info_captured=param_is_exif_info_captured,
        param_quality=param_quality,
        exif_json_dict=exif_json_dict,
        key_list=key_list,
        created_at=created_at)

    return pdfkit.from_string(rendered, f"{current_app.config['OUTPUT_FOLDER']}/{folder_name}/report_preview.pdf")

class ReportPreview(Resource):

    def get(self, id):
        video_conversion = VideoConversionModel.query.filter_by(id=id).first()
        output_dir = f"{current_app.config['OUTPUT_FOLDER']}/{video_conversion.id}"
        file_name = f"{video_conversion.id}.{video_conversion.param_output_format}"
        pdf = generate_pdf_report(
            f"{output_dir}/{file_name}",
            video_conversion.id,
            video_conversion.original_uploaded_file_name,
            video_conversion.param_frame_rate,
            video_conversion.param_output_format,
            video_conversion.param_quality,
            video_conversion.param_is_exif_info_captured,
            video_conversion.created_at
        )

        preview_report_path = os.path.join(
            current_app.config['OUTPUT_FOLDER'], f"{video_conversion.id}/report_preview.pdf")

        return send_file(preview_report_path, as_attachment=True)
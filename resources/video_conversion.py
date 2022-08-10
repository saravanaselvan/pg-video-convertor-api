from flask import send_file, render_template
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
import cv2
import pdfkit
import base64

ALLOWED_EXTENSIONS = {'mp4', 'mov'}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def image_file_path_to_base64_string(filepath: str) -> str:
    with open(filepath, 'rb') as f:
        return base64.b64encode(f.read()).decode()


def generate_panorama_img(output_dir, file_name):
    image_names = os.listdir(output_dir)
    images = []
    for image_name in image_names:
        img = cv2.imread(f"{output_dir}/{image_name}")
        img = cv2.resize(img, (0, 0), None, 0.2, 0.2)
        images.append(img)

    stitcher = cv2.Stitcher.create(cv2.STITCHER_PANORAMA)
    # stitcher.setPanoConfidenceThresh(0.0)
    (status, result) = stitcher.stitch(images)

    if status == cv2.STITCHER_OK:
        print("Panorama success")
        cv2.imwrite(f"{output_dir}/{file_name}", result)
    else:
        print("Panorama failed" + str(status))


def generate_pdf_report(
        panorama_img_path,
        folder_name,
        original_uploaded_file_name,
        param_frame_rate,
        param_output_format,
        param_is_exif_info_captured):
    rendered = render_template(
        "report_template.html",
        img_string=image_file_path_to_base64_string(panorama_img_path),
        original_uploaded_file_name=original_uploaded_file_name,
        param_frame_rate=param_frame_rate,
        param_output_format=param_output_format,
        param_is_exif_info_captured=param_is_exif_info_captured)
    pdf = pdfkit.from_string(
        rendered, f"{current_app.config['OUTPUT_FOLDER']}/{folder_name}/report.pdf")


class VideoConversion(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('file', type=werkzeug.datastructures.FileStorage, location='files', required=True,
                        help="File is required")
    parser.add_argument('frame_rate', type=str, required=True,
                        help="Framerate required")
    parser.add_argument('output_format', type=str, required=True,
                        help="Output Format required")
    parser.add_argument('is_exif_info_captured', type=bool)

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
                    output_yaml_file_name="test",
                    output_yaml_file_path="test",
                    output_pdf_file_name="test",
                    output_pdf_file_path="test",
                    param_output_format=param_output_format,
                    param_frame_rate=param_frame_rate,
                    param_is_exif_info_captured=param_is_exif_info_captured,
                )
                video_conversion.save_to_db()
            except BaseException as e:
                return f'{e}'

            output_path = os.path.join(
                current_app.config['OUTPUT_FOLDER'], uploaded_file_name)

            inputF = os.path.join(
                current_app.config['UPLOAD_FOLDER'], uploaded_file_name)  # Build input path
            # Build output path and add file
            output_dir = f"{current_app.config['OUTPUT_FOLDER']}/{video_conversion.id}"
            os.makedirs(output_dir, exist_ok=True)
            outputF = os.path.join(output_dir, f"out%d.{param_output_format}")

            print(f"Started processing {original_uploaded_file_name}")
            # Ffmpeg is flexible enough to handle wildstar conversions
            convertCMD = ["ffmpeg",
                          '-i', inputF, '-vf', f'fps={1}', outputF]

            executeOrder66 = sp.Popen(convertCMD)

            try:
                outs, errs = executeOrder66.communicate()  # tell program to wait
            except TimeoutError:  # Kill if it takes too long
                proc.kill()

            file_name = f"{video_conversion.id}.{param_output_format}"
            generate_panorama_img(output_dir, file_name)
            generate_pdf_report(
                f"{output_dir}/{file_name}",
                video_conversion.id,
                original_uploaded_file_name=original_uploaded_file_name,
                param_frame_rate=param_frame_rate,
                param_output_format=param_output_format,
                param_is_exif_info_captured=param_is_exif_info_captured
            )

            return {
                "id": video_conversion.id
            }

        return "Only JSON file type is accepted", 500

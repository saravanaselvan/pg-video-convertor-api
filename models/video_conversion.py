from db import db
from flask_jwt_extended import get_jwt_identity
from datetime import datetime
import os
from .user import UserModel
from flask import current_app

from services.video_report.video_report import generate_panorama_img, generate_yaml_params, generate_pdf_report, extract_frames_from_video, exif_info


class VideoConversionModel(db.Model):
    __tablename__ = 'video_conversions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('UserModel')
    status = db.Column(db.String(50))
    original_uploaded_file_name = db.Column(db.String(255))
    uploaded_file_name = db.Column(db.String(255))
    output_yaml_file_name = db.Column(db.String(255))
    output_yaml_file_path = db.Column(db.String(255))
    output_pdf_file_name = db.Column(db.String(255))
    output_pdf_file_path = db.Column(db.String(255))
    param_output_format = db.Column(db.String(255))
    param_frame_rate = db.Column(db.Float(precision=2))
    param_is_exif_info_captured = db.Column(db.Boolean)
    output_exif_file_name = db.Column(db.String(255))
    output_exif_file_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)

    def __init__(self,
                 status,
                 original_uploaded_file_name,
                 uploaded_file_name,
                 output_yaml_file_name,
                 param_output_format,
                 param_frame_rate,
                 param_is_exif_info_captured,
                 output_yaml_file_path="",
                 output_pdf_file_name="",
                 output_pdf_file_path=""
                 ):
        self.user_id = get_jwt_identity()
        self.status = status
        self.original_uploaded_file_name = original_uploaded_file_name
        self.uploaded_file_name = uploaded_file_name
        self.output_yaml_file_name = output_yaml_file_name
        self.output_yaml_file_path = output_yaml_file_path
        self.output_pdf_file_name = output_pdf_file_name
        self.output_pdf_file_path = output_pdf_file_path
        self.param_output_format = param_output_format
        self.param_frame_rate = param_frame_rate
        self.param_is_exif_info_captured = param_is_exif_info_captured
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def json(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'status': self.status,
            'original_uploaded_file_name': self.original_uploaded_file_name,
            'uploaded_file_name': self.uploaded_file_name,
            'output_yaml_file_name': self.output_yaml_file_name,
            'output_yaml_file_path': self.output_yaml_file_path,
            'output_pdf_file_name': self.output_pdf_file_name,
            'output_pdf_file_path': self.output_pdf_file_path,
            'param_output_format': self.param_output_format,
            'param_frame_rate': self.param_frame_rate,
            'param_is_exif_info_captured': self.param_is_exif_info_captured,
            'output_exif_file_path': self.output_exif_file_path,
            'created_at': str(self.created_at)
        }

    def params_dict(self):
        return {
            "input_file_name": self.original_uploaded_file_name,
            "params": {
                "frame_rate": self.param_frame_rate,
                "output_format": self.param_output_format,
                "exif_info_captured": "Yes" if self.param_is_exif_info_captured == 'true' else "No"
            }
        }

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

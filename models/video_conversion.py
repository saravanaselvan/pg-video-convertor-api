from db import db
from flask_jwt_extended import get_jwt_identity
from datetime import datetime


class VideoConversionModel(db.Model):
    __tablename__ = 'video_conversions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('UserModel')
    original_uploaded_file_name = db.Column(db.String(255))
    uploaded_file_name = db.Column(db.String(255))
    output_yaml_file_name = db.Column(db.String(255))
    output_yaml_file_path = db.Column(db.String(255))
    output_pdf_file_name = db.Column(db.String(255))
    output_pdf_file_path = db.Column(db.String(255))
    param_output_format = db.Column(db.String(255))
    param_frame_rate = db.Column(db.Float(precision=2))
    param_is_exif_info_captured = db.Column(db.Boolean)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)

    def __init__(self,
                 original_uploaded_file_name,
                 uploaded_file_name,
                 output_yaml_file_name,
                 output_yaml_file_path,
                 output_pdf_file_name,
                 output_pdf_file_path,
                 param_output_format,
                 param_frame_rate,
                 param_is_exif_info_captured
                 ):
        self.user_id = get_jwt_identity()
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

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

import os
from services.video_report.video_report import generate_panorama_img, generate_yaml_params, generate_pdf_report, extract_frames_from_video, exif_info
from models.video_conversion import VideoConversionModel
from base import celery as celery_app


@celery_app.task(name="pg_video_conversion.process_video")
def process_video(id, output_folder, upload_folder):
    video_conversion = VideoConversionModel.query.filter_by(id=id).first()
    video_conversion.status = "IN PROGRESS"
    video_conversion.save_to_db()
    output_dir = f"{output_folder}/{video_conversion.id}"
    frames_dir = f"{output_dir}/frames"
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(frames_dir, exist_ok=True)

    input_video_path = os.path.join(
        upload_folder, video_conversion.uploaded_file_name)
    output_frames_path = os.path.join(
        frames_dir, f"out%d.{video_conversion.param_output_format}")

    # Create params.yaml
    yaml_file_path = generate_yaml_params(
        video_conversion.params_dict(), video_conversion.id)

    print(f"Started processing {video_conversion.original_uploaded_file_name}")

    exif_file_path = ""
    if video_conversion.param_is_exif_info_captured:
        exif_file_path = exif_info(input_video_path, output_dir)

    extract_frames_from_video(
        input_video_path, output_frames_path, video_conversion.param_frame_rate)

    file_name = f"{video_conversion.id}.{video_conversion.param_output_format}"
    generate_panorama_img(frames_dir, output_dir, file_name)
    generate_pdf_report(
        f"{output_dir}/{file_name}",
        video_conversion.id,
        video_conversion.original_uploaded_file_name,
        video_conversion.param_frame_rate,
        video_conversion.param_output_format,
        video_conversion.param_is_exif_info_captured
    )

    video_conversion.output_pdf_file_name = "report.pdf"
    video_conversion.output_pdf_file_path = f"{output_folder}/{video_conversion.id}/report.pdf"
    video_conversion.output_yaml_file_path = yaml_file_path
    video_conversion.output_exif_file_name = "exif.json"
    video_conversion.output_exif_file_path = exif_file_path
    video_conversion.status = "COMPLETED"

    video_conversion.save_to_db()

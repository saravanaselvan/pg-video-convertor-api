import os
import cv2
import yaml
import pdfkit
import base64
import subprocess as sp
import json

from flask import current_app, render_template


def exif_info(input_video_path, output_dir):
    exif_file_path = f"{output_dir}/exif.json"
    exif_tool_cmd = ["exiftool", "-j", input_video_path,
                     ">>", exif_file_path]

    output = sp.run(exif_tool_cmd, capture_output=True)
    json_dict = json.loads(output.stdout.decode("utf-8"))[0]

    with open(exif_file_path, 'w') as file:
        file.write(json.dumps(json_dict, indent=2))
        file.close()

    return exif_file_path


def extract_frames_from_video(
        input_video_path, 
        output_frames_path, 
        fps, 
        quality):
    convertCMD = ["ffmpeg", '-i', input_video_path,
                  '-vf', f'fps={fps}', '-qscale:v', str(quality), output_frames_path]

    proc = sp.Popen(convertCMD)

    try:
        outs, errs = proc.communicate()
    except TimeoutError:
        proc.kill()


def generate_panorama_img(frames_dir, output_dir, file_name):
    image_names = os.listdir(frames_dir)
    images = []

    for image_name in image_names:
        img = cv2.imread(f"{frames_dir}/{image_name}")
        img = cv2.resize(img, (0, 0), None, 0.2, 0.2)
        images.append(img)

    stitcher = cv2.Stitcher.create(cv2.STITCHER_PANORAMA)
    # stitcher.setPanoConfidenceThresh(0.0)

    (status, result) = stitcher.stitch(images)

    error = ''
    if status == cv2.STITCHER_OK:
        print("Panorama success")
        cv2.imwrite(f"{output_dir}/{file_name}", result)
    else:
        if status == cv2.STITCHER_ERR_NEED_MORE_IMGS:
            error = "Need more images - ERR_NEED_MORE_IMGS"
        elif status == cv2.STITCHER_ERR_HOMOGRAPHY_EST_FAIL:
            error = "Failed - ERR_NEED_MORE_IMGS"
        elif  status == cv2.STITCHER_ERR_CAMERA_PARAMS_ADJUST_FAIL:
            error = "Failed - STITCHER_ERR_CAMERA_PARAMS_ADJUST_FAIL"

    return error

def generate_yaml_params(params_dict, folder_name):
    yaml_file_path = f"{current_app.config['OUTPUT_FOLDER']}/{folder_name}/params.yaml"

    with open(yaml_file_path, 'w') as file:
        documents = yaml.dump(params_dict, file, sort_keys=False)

    return yaml_file_path


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
    pdf = pdfkit.from_string(
        rendered, f"{current_app.config['OUTPUT_FOLDER']}/{folder_name}/report.pdf")

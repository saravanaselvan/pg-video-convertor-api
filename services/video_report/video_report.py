import os
import cv2
import yaml
import pdfkit
import base64
import subprocess as sp
import json

from flask import current_app, render_template


def exif_info(input_video_path, output_dir):
    exif_tool_cmd = ["exiftool", "-j", input_video_path,
                     ">>", f"{output_dir}/exif.json"]

    output = sp.run(exif_tool_cmd, capture_output=True)
    json_dict = json.loads(output.stdout.decode("utf-8"))[0]

    with open(f"{output_dir}/exif.json", 'w') as file:
        file.write(json.dumps(json_dict, indent=2))
        file.close()


def extract_frames_from_video(input_video_path, output_frames_path, fps):
    convertCMD = ["ffmpeg", '-i', input_video_path,
                  '-vf', f'fps={fps}', output_frames_path]

    executeOrder66 = sp.Popen(convertCMD)

    try:
        outs, errs = executeOrder66.communicate()
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

    if status == cv2.STITCHER_OK:
        print("Panorama success")
        cv2.imwrite(f"{output_dir}/{file_name}", result)
    else:
        print("Panorama failed" + str(status))


def generate_yaml_params(params_dict, folder_name):
    yaml_file_path = f"{current_app.config['OUTPUT_FOLDER']}/{folder_name}/params.yaml"

    with open(yaml_file_path, 'w') as file:
        documents = yaml.dump(params_dict, file)

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
        param_is_exif_info_captured):
    exif_json = f"{current_app.config['OUTPUT_FOLDER']}/{folder_name}/exif.json"

    with open(exif_json, 'r') as file:
        exif_json_dict = json.loads(file.read())

    rendered = render_template(
        "report_template.html",
        img_string=image_file_path_to_base64_string(panorama_img_path),
        original_uploaded_file_name=original_uploaded_file_name,
        param_frame_rate=param_frame_rate,
        param_output_format=param_output_format,
        param_is_exif_info_captured=param_is_exif_info_captured,
        exif_json_dict=exif_json_dict)
    pdf = pdfkit.from_string(
        rendered, f"{current_app.config['OUTPUT_FOLDER']}/{folder_name}/report.pdf")
from flask_restful import Resource, reqparse
from flask_jwt_extended import jwt_required, get_jwt_identity
import services.predict_detect.predict_det2 as predict_det2
import werkzeug
from detectron2.utils.visualizer import Visualizer
from detectron2.data import MetadataCatalog, DatasetCatalog
import cv2
from werkzeug.utils import secure_filename
import datetime
import os
from flask import current_app
from detectron2.config import get_cfg


class PipeCount(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('file', type=werkzeug.datastructures.FileStorage, location='files', required=True,
                        help="File is required")

    @jwt_required()
    def post(self):
        data = PipeCount.parser.parse_args()
        file = data['file'].read()
        uploaded_file = data['file']
        original_file_name = secure_filename(uploaded_file.filename)
        uploaded_file_name = f'{original_file_name.split(".")[0]}_{datetime.datetime.now().strftime("%d_%m_%Y_%H:%M:%S")}.{original_file_name.rsplit(".", 1)[1]}'

        cfg = get_cfg()
        np_image = predict_det2.input_fn(file, "application/octet-stream")
        predictor = predict_det2.model_fn("services/predict_detect")
        predictions = predict_det2.predict_fn(np_image, predictor)
        predictions_json = predict_det2.output_fn(
            predictions, "application/json")

        # get image
        # img = Image.fromarray(np.uint8(v.get_image()[:, :, ::-1]))

        # Create the image with bounding boxes
        # print(predictions)
        # input_file_path = os.path.join(
        #     current_app.config['UPLOAD_FOLDER'], uploaded_file_name)

        # with open(input_file_path, 'wb') as fw:
        #     fw.write(file)
        #     fw.close()
        # v = Visualizer(
        #     cv2.imread(input_file_path)[:, :, :])
        # out = v.draw_instance_predictions(predictions["instances"].to(
        #     "cpu"))
        # cv2.imwrite(input_file_path, out.get_image()[:, :, ::-1])

        return {"preditions": predictions_json}

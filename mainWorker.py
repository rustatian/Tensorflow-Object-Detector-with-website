import base64
import os
import re
import ssl

import tornado
import tornado.httpserver
from io import BytesIO
from multiprocessing import Process
from multiprocessing import Queue
from multiprocessing.pool import Pool

import numpy as np
import tensorflow as tf
from PIL import Image
from tornado import websocket, gen, web

import label_map_util
import visualization_utils as vis_util

CWD_PATH = os.getcwd()

# Path to frozen detection graph. This is the actual model that is used for the object detection
MODEL_NAME = 'ssd_mobilenet_v1_coco_11_06_2017'
PATH_TO_CKPT = os.path.join(CWD_PATH, 'object_detection', MODEL_NAME, 'frozen_inference_graph.pb')

# List of the strings that is used to add correct label for each box.
PATH_TO_LABELS = os.path.join(CWD_PATH, 'object_detection', 'data', 'mscoco_label_map.pbtxt')

NUM_CLASSES = 90

# Loading label map
label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=NUM_CLASSES,
                                                            use_display_name=True)
category_index = label_map_util.create_category_index(categories)


def detect_objects(image_np, sess, detection_graph):
    # Expand dimensions since the model expects images to have shape: [mscoco_label_map.pbtxt, None, None, 3]
    image_np_expanded = np.expand_dims(image_np, axis=0)
    image_tensor = detection_graph.get_tensor_by_name('image_tensor:0')

    # Each box represents a part of the image where a particular object was detected.
    boxes = detection_graph.get_tensor_by_name('detection_boxes:0')

    # Each score represent how level of confidence for each of the objects.
    # Score is shown on the result image, together with the class label.
    scores = detection_graph.get_tensor_by_name('detection_scores:0')
    classes = detection_graph.get_tensor_by_name('detection_classes:0')
    num_detections = detection_graph.get_tensor_by_name('num_detections:0')

    # Actual detection.
    (boxes, scores, classes, num_detections) = sess.run(
        [boxes, scores, classes, num_detections],
        feed_dict={image_tensor: image_np_expanded})

    # Visualization of the results of a detection.
    vis_util.visualize_boxes_and_labels_on_image_array(
        image_np,
        np.squeeze(boxes),
        np.squeeze(classes).astype(np.int32),
        np.squeeze(scores),
        category_index,
        use_normalized_coordinates=True,
        line_thickness=8)
    return image_np


def worker(input_q, output_q):
    # Load a (frozen) Tensorflow model into memory.
    detection_graph = tf.Graph()
    with detection_graph.as_default():
        od_graph_def = tf.GraphDef()
        with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
            serialized_graph = fid.read()
            od_graph_def.ParseFromString(serialized_graph)
            tf.import_graph_def(od_graph_def, name='', )
        sess = tf.Session(graph=detection_graph)
    while True:
        frame = input_q.get()
        output_q.put(detect_objects(frame, sess, detection_graph))
        # sess.close()


class EchoWebSocket(tornado.websocket.WebSocketHandler):
    def __init__(self, app, request, **kwargs):
        super().__init__(app, request, **kwargs)
        self.regex = re.compile('base64,(.*)')

    def data_received(self, chunk):
        pass

    def check_origin(self, origin):
        return True

    def open(self):
        print("WebSocket opened")

    @gen.coroutine
    def on_message(self, message):
        imgstr = re.search(self.regex, message).group(1)
        image = Image.open(BytesIO(base64.b64decode(imgstr)))
        imnp = np.array(image)

        input_q.put(imnp)
        out = output_q.get()

        converted = Image.fromarray(out)
        buffer = BytesIO()
        converted.save(buffer, format="JPEG")
        img_str = base64.b64encode(buffer.getvalue())
        buffer.flush()
        self.write_message(img_str)

    def on_close(self):
        print("WebSocket closed")


if __name__ == "__main__":
    input_q = Queue(maxsize=30)
    output_q = Queue(maxsize=30)

    process = Process(target=worker, args=(input_q, output_q))
    process.daemon = True
    pool = Pool(processes=1, initializer=worker, initargs=(input_q, output_q))

    application = tornado.web.Application([
        (r"/", EchoWebSocket),
    ])

    data_dir = "<path/to/ssl>"

    ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_ctx.load_cert_chain(os.path.join(data_dir, "<filename>.crt"),
                            os.path.join(data_dir, "<filename>"))

    http_server = tornado.httpserver.HTTPServer(application, ssl_options=ssl_ctx)

    http_server.listen(443)
    tornado.ioloop.IOLoop.current().start()

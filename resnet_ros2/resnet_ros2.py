import numpy
from transformers import AutoFeatureExtractor, ResNetForImageClassification
import torch
from PIL import Image as PilImage
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge


def predict(image: Image):
    feature_extractor = AutoFeatureExtractor.from_pretrained('microsoft/resnet-101')
    model = ResNetForImageClassification.from_pretrained('microsoft/resnet-101')

    inputs = feature_extractor(image, return_tensors="pt")

    with torch.no_grad():
        logits = model(**inputs).logits

    # model predicts one of the 1000 ImageNet classes
    predicted_label = logits.argmax(-1).item()

    return predicted_label, model.config.id2label[predicted_label]


class RosIO(Node):
    def __init__(self):
        super().__init__('minimal_subscriber')
        self.image_subscription = self.create_subscription(
            Image,
            '/resnet/sub/image_raw',
            self.listener_callback,
            10
        )

        self.result_publisher = self.create_publisher(
            String,
            '/resnet/pub/result',
            1
        )

    def listener_callback(self, msg: Image):
        # self.get_logger().info(msg.data)
        bridge = CvBridge()
        cv_image: numpy.ndarray = bridge.imgmsg_to_cv2(msg)
        # print(cv_image)
        # cv2.imshow('image', cv_image)
        # cv2.waitKey(0)
        converted_image = PilImage.fromarray(numpy.uint8(cv_image), 'RGB')
        # converted_image.show('image')
        result = str(predict(converted_image))
        print(f'Result: {result}')
        self.result_publisher.publish(result)


def main(args=None):
    print('Resnet Started')

    rclpy.init(args=args)

    minimal_subscriber = RosIO()

    rclpy.spin(minimal_subscriber)

    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    minimal_subscriber.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

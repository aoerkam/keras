# Copyright 2018 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Integration tests for Keras applications."""

import tensorflow.compat.v2 as tf

from absl.testing import parameterized

from keras import backend
from keras.applications import densenet
from keras.applications import efficientnet
from keras.applications import inception_resnet_v2
from keras.applications import inception_v3
from keras.applications import mobilenet
from keras.applications import mobilenet_v2
from keras.applications import mobilenet_v3
from keras.applications import nasnet
from keras.applications import resnet
from keras.applications import resnet_v2
from keras.applications import vgg16
from keras.applications import vgg19
from keras.applications import xception


MODEL_LIST_NO_NASNET = [
    (resnet.ResNet50, 2048),
    (resnet.ResNet101, 2048),
    (resnet.ResNet152, 2048),
    (resnet_v2.ResNet50V2, 2048),
    (resnet_v2.ResNet101V2, 2048),
    (resnet_v2.ResNet152V2, 2048),
    (vgg16.VGG16, 512),
    (vgg19.VGG19, 512),
    (xception.Xception, 2048),
    (inception_v3.InceptionV3, 2048),
    (inception_resnet_v2.InceptionResNetV2, 1536),
    (mobilenet.MobileNet, 1024),
    (mobilenet_v2.MobileNetV2, 1280),
    (mobilenet_v3.MobileNetV3Small, 576),
    (mobilenet_v3.MobileNetV3Large, 960),
    (densenet.DenseNet121, 1024),
    (densenet.DenseNet169, 1664),
    (densenet.DenseNet201, 1920),
    (efficientnet.EfficientNetB0, 1280),
    (efficientnet.EfficientNetB1, 1280),
    (efficientnet.EfficientNetB2, 1408),
    (efficientnet.EfficientNetB3, 1536),
    (efficientnet.EfficientNetB4, 1792),
    (efficientnet.EfficientNetB5, 2048),
    (efficientnet.EfficientNetB6, 2304),
    (efficientnet.EfficientNetB7, 2560),
]

NASNET_LIST = [
    (nasnet.NASNetMobile, 1056),
    (nasnet.NASNetLarge, 4032),
]

MODEL_LIST = MODEL_LIST_NO_NASNET + NASNET_LIST

# Parameters for loading weights for MobileNetV3.
# (class, alpha, minimalistic, include_top)
MOBILENET_V3_FOR_WEIGHTS = [
    (mobilenet_v3.MobileNetV3Large, 0.75, False, False),
    (mobilenet_v3.MobileNetV3Large, 1.0, False, False),
    (mobilenet_v3.MobileNetV3Large, 1.0, True, False),
    (mobilenet_v3.MobileNetV3Large, 0.75, False, True),
    (mobilenet_v3.MobileNetV3Large, 1.0, False, True),
    (mobilenet_v3.MobileNetV3Large, 1.0, True, True),
    (mobilenet_v3.MobileNetV3Small, 0.75, False, False),
    (mobilenet_v3.MobileNetV3Small, 1.0, False, False),
    (mobilenet_v3.MobileNetV3Small, 1.0, True, False),
    (mobilenet_v3.MobileNetV3Small, 0.75, False, True),
    (mobilenet_v3.MobileNetV3Small, 1.0, False, True),
    (mobilenet_v3.MobileNetV3Small, 1.0, True, True),
]


class ApplicationsTest(tf.test.TestCase, parameterized.TestCase):

  def assertShapeEqual(self, shape1, shape2):
    if len(shape1) != len(shape2):
      raise AssertionError(
          'Shapes are different rank: %s vs %s' % (shape1, shape2))
    for v1, v2 in zip(shape1, shape2):
      if v1 != v2:
        raise AssertionError('Shapes differ: %s vs %s' % (shape1, shape2))

  @parameterized.parameters(*MODEL_LIST)
  def test_application_base(self, app, _):
    # Can be instantiated with default arguments
    model = app(weights=None)
    # Can be serialized and deserialized
    config = model.get_config()
    reconstructed_model = model.__class__.from_config(config)
    self.assertEqual(len(model.weights), len(reconstructed_model.weights))
    backend.clear_session()

  @parameterized.parameters(*MODEL_LIST)
  def test_application_notop(self, app, last_dim):
    if 'NASNet' in app.__name__:
      only_check_last_dim = True
    else:
      only_check_last_dim = False
    output_shape = _get_output_shape(
        lambda: app(weights=None, include_top=False))
    if only_check_last_dim:
      self.assertEqual(output_shape[-1], last_dim)
    else:
      self.assertShapeEqual(output_shape, (None, None, None, last_dim))
    backend.clear_session()

  @parameterized.parameters(MODEL_LIST)
  def test_application_pooling(self, app, last_dim):
    output_shape = _get_output_shape(
        lambda: app(weights=None, include_top=False, pooling='avg'))
    self.assertShapeEqual(output_shape, (None, last_dim))

  @parameterized.parameters(*MODEL_LIST_NO_NASNET)
  def test_application_variable_input_channels(self, app, last_dim):
    if backend.image_data_format() == 'channels_first':
      input_shape = (1, None, None)
    else:
      input_shape = (None, None, 1)
    output_shape = _get_output_shape(
        lambda: app(weights=None, include_top=False, input_shape=input_shape))
    self.assertShapeEqual(output_shape, (None, None, None, last_dim))
    backend.clear_session()

    if backend.image_data_format() == 'channels_first':
      input_shape = (4, None, None)
    else:
      input_shape = (None, None, 4)
    output_shape = _get_output_shape(
        lambda: app(weights=None, include_top=False, input_shape=input_shape))
    self.assertShapeEqual(output_shape, (None, None, None, last_dim))
    backend.clear_session()

  @parameterized.parameters(*MOBILENET_V3_FOR_WEIGHTS)
  def test_mobilenet_v3_load_weights(
      self,
      mobilenet_class,
      alpha,
      minimalistic,
      include_top):
    mobilenet_class(
        input_shape=(224, 224, 3),
        weights='imagenet',
        alpha=alpha,
        minimalistic=minimalistic,
        include_top=include_top)


def _get_output_shape(model_fn):
  model = model_fn()
  return model.output_shape


if __name__ == '__main__':
  tf.test.main()

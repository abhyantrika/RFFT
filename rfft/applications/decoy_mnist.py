from __future__ import absolute_import
from __future__ import print_function

try:
    from io import BytesIO
except ImportError:
    import cStringIO

import array
import base64
import gzip
import os
import random
import struct

from celery import Celery

from PIL import Image

import autograd.numpy as np
import autograd.numpy.random as npr

try:
    from urllib.request import urlretrieve
except ImportError:
    from urllib2 import urlopen

# from lime import lime_image
# from skimage.segmentation import mark_boundaries

from rfft.experiment import Dataset
from rfft.experiment import Experiment
from rfft.experiment import ExperimentType

from rfft.hypothesis import Hypothesis
from rfft.multilayer_perceptron import MultilayerPerceptron

ANNOTATIONS_DIR = 'tagging/decoy_mnist'


class DecoyMNIST(Experiment):

    def __init__(self):
        Experiment.__init__(self)
        self.annotation_idxs = []

    def get_status(self):
        return self.status

    def domain(self):
        return ExperimentType.IMAGE

    def pretty_name(self):
        return 'Decoy MNIST'

    def description(self):
        return 'Handwritten digits'

    def generate_dataset(self, cachefile='data/decoy-mnist.npz'):
        if cachefile and os.path.exists(cachefile):
            cache = np.load(cachefile)
            data = tuple([cache[f] for f in sorted(cache.files)])
        else:
            data = self._generate_dataset(os.path.dirname(cachefile))
            if cachefile:
                np.savez(cachefile, *data)
        self.Xr, self.X, self.y, self.E, self.Xtr, self.Xt, self.yt, self.Et = data
        self.status.initialized = True

    def get_sample(self, dataset, idx):
        if not self.status.initialized:
            raise AttributeError('Generate dataset before fetching samples.')
        if dataset == Dataset.TRAIN:
            return Xr[idx]
        elif dataset == Dataset.TEST:
            return Xtr[idx]

    def load_annotations(self, **hypothesis_params):
        annotation_files = [os.path.join(ANNOTATIONS_DIR, x)
                            for x in os.listdir(ANNOTATIONS_DIR)
                            if x.endswith('.npy')]

        A = np.zeros(self.X.shape).astype(bool)
        affected_indices = []
        for f in annotation_files:
            index = int(f.split('/')[-1].split('.')[0])
            mask = np.load(f)
            affected_indices.append(index)
            A[index] = mask

        self.affected_indices = affected_indices
        self.hypothesis = Hypothesis(A, **hypothesis_params)
        self.status.annotations_loaded = True


    def unload_annotations(self):
        self.hypothesis = None
        self.status.annotations_loaded = False


    def set_annotation(self, idx, mask):
        mask = np.array(mask)
        if idx < len(self.annotation_idxs):
            annotation_idx = self.annotation_idxs[idx]
            np.save(os.path.join(ANNOTATIONS_DIR, str(annotation_idx)), mask)
        else:
            raise IndexError('idx must be less than the current number of annotations')


    def _get_mask_from_idx(self, idx):
        annotation_path = os.path.join(ANNOTATIONS_DIR, str(idx) + '.npy')
        print(annotation_path)
        if os.path.exists(annotation_path):
            return np.load(annotation_path).tolist()
        return None


    def _convert_image_to_base64(self, image):
        try:
            buffered = BytesIO()
        except:
            buffered = cStringIO.StringIO()
        image.save(buffered, format='JPEG')
        return base64.b64encode(buffered.getvalue())


    def get_annotation(self, idx):
        if idx < len(self.annotation_idxs):
            annotation_idx = self.annotation_idxs[idx]
            image = self.get_image(self.X[annotation_idx])
            mask = self._get_mask_from_idx(annotation_idx)
        elif idx == len(self.annotation_idxs):
            while True:
                annotation_idx = random.randint(0, len(self.X) - 1)
                if annotation_idx in self.annotation_idxs:
                    continue
                self.annotation_idxs.append(annotation_idx)
                image = self.get_image(self.X[annotation_idx])
                mask = []
                break
        else:
            raise IndexError('idx must be less than or equal to the current number of annotations')
        return {
            'annotation_idx': idx,
            'data': 'data:image/jpg;base64,' + str(self._convert_image_to_base64(image)),
            'mask': mask
        }


    def delete_annotation(self, idx):
        if idx < len(self.annotation_idxs):
            annotation_idx = self.annotation_idxs[idx]
            annotation_path = os.path.join(ANNOTATIONS_DIR, str(annotation_idx) + '.npy')
            try:
                os.remove(annotation_path)
            except FileNotFoundError:
                pass
        else:
            raise IndexError('idx must be less than the current number of annotations')


    def train(self, num_epochs=6):
        self.model = MultilayerPerceptron()
        if self.status.annotations_loaded:
            self.model.fit(self.X,
                           self.y,
                           hypothesis=self.hypothesis,
                           num_epochs=num_epochs,
                           always_include=self.affected_indices)
        else:
            self.model.fit(self.X, self.y, num_epochs=num_epochs)
        self.status.trained = True

    def explain(self, sample, **explanation_params):
        if not self.status.trained:
            raise AttributeError(
                'You must have trained the model to be able to generate explanations.')
        explainer = lime_image.LimeImageExplainer()
        explanation = explainer.explain_instance(image,
                                                 self.model,
                                                 top_labels=5,
                                                 hide_color=0,
                                                 num_samples=1000)
        temp, mask = explanation.get_image_and_mask(
            240, positive_only=True, num_features=5, hide_rest=True)
        masked_image = mark_boundaries(temp / 2 + 0.5, mask)
        return masked_image

    def score_model(self):
        return (
            self.model.score(self.X, self.y),
            self.model.score(self.Xt, self.yt)
        )

    def download_mnist(self, datadir):
        if not os.path.exists(datadir):
            os.makedirs(datadir)

        base_url = 'http://yann.lecun.com/exdb/mnist/'

        def parse_labels(filename):
            with gzip.open(filename, 'rb') as fh:
                magic, num_data = struct.unpack(">II", fh.read(8))
                return np.array(array.array("B", fh.read()), dtype=np.uint8)

        def parse_images(filename):
            with gzip.open(filename, 'rb') as fh:
                magic, num_data, rows, cols = struct.unpack(
                    ">IIII", fh.read(16))
                return np.array(array.array("B", fh.read()), dtype=np.uint8).reshape(num_data, rows, cols)

        for filename in ['train-images-idx3-ubyte.gz', 'train-labels-idx1-ubyte.gz',
                         't10k-images-idx3-ubyte.gz', 't10k-labels-idx1-ubyte.gz']:
            if not os.path.exists(os.path.join(datadir, filename)):
                try:
                    urlretrieve(base_url + filename,
                                os.path.join(datadir, filename))
                except:
                    with open(os.path.join(datadir, filename), 'w') as f:
                        f.write(urlopen(base_url + filename).read())

        train_images = parse_images(os.path.join(
            datadir, 'train-images-idx3-ubyte.gz'))
        train_labels = parse_labels(os.path.join(
            datadir, 'train-labels-idx1-ubyte.gz'))
        test_images = parse_images(os.path.join(
            datadir, 't10k-images-idx3-ubyte.gz'))
        test_labels = parse_labels(os.path.join(
            datadir, 't10k-labels-idx1-ubyte.gz'))

        return train_images, train_labels, test_images, test_labels

    def Bern(self, p):
        return np.random.rand() < p

    def augment(self, image, digit, randomize=False, mult=25, all_digits=range(10)):
        if randomize:
            return self.augment(image, np.random.choice(all_digits))

        img = image.copy()
        expl = np.zeros_like(img)

        fwd = [0, 1, 2, 3]
        rev = [-1, -2, -3, -4]
        dir1 = fwd if self.Bern(0.5) else rev
        dir2 = fwd if self.Bern(0.5) else rev
        for i in dir1:
            for j in dir2:
                img[i][j] = 255 - mult * digit
                expl[i][j] = 1

        return img.ravel(), expl.astype(bool).ravel()

    def _generate_dataset(self, datadir):
        X_raw, y, Xt_raw, yt = self.download_mnist(datadir)
        all_digits = list(set(y))

        X = []
        E = []
        Xt = []
        Et = []

        for image, digit in zip(X_raw, y):
            x, e = self.augment(image, digit, all_digits=all_digits)
            X.append(x)
            E.append(e)

        for image, digit in zip(Xt_raw, yt):
            x, e = self.augment(
                image, digit, all_digits=all_digits, randomize=True)
            Xt.append(x)
            Et.append(e)

        X = np.array(X)
        E = np.array(E)
        Xt = np.array(Xt)
        Et = np.array(Et)
        Xr = np.array([x.ravel() for x in X_raw])
        Xtr = np.array([x.ravel() for x in Xt_raw])

        return Xr, X, y, E, Xtr, Xt, yt, Et

    def get_image(self, array):
        img = array.reshape((28, 28))
        img = Image.fromarray(img)
        return img

    def generate_tagging_set(self, Xtr, size=20):
        indices = []
        for i in range(size):
            index = npr.randint(0, len(Xtr))
            if index in indices:
                continue
            indices.append(index)
            image = self.get_image(Xtr[index], index)
            image.save('tagging/decoy_mnist/' + str(index) + '.png')


if __name__ == '__main__':
    print('Training with annotations')
    decoy_mnist = DecoyMNIST()
    decoy_mnist.generate_dataset()
    decoy_mnist.load_annotations(weight=10, per_annotation=True)
    decoy_mnist.train(num_epochs=1)
    print(decoy_mnist.score_model())

    print('Training without annotations')
    decoy_mnist.unload_annotations()
    decoy_mnist.train(num_epochs=2)
    print(decoy_mnist.score_model())

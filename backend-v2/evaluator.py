from __future__ import print_function
import evaluator_pb2
import evaluator_pb2_grpc
import numpy as np
np.random.seed(1337)

from keras.datasets import mnist
from keras.models import Sequential
from keras.layers import Dense, Dropout, Activation, Flatten
from keras.layers import Conv2D, MaxPooling2D
from keras.utils import np_utils

from keras import backend as K

batch_size = 128
nb_classes = 10
nb_epoch = 5

img_rows, img_cols = 28, 28

nb_filters = 32

pool_size = (2, 2)

kernel_size = (3, 3)

(X_train, y_train), (X_test, y_test) = mnist.load_data()

if K.image_dim_ordering() == 'th':
	X_train = X_train.reshape(X_train.shape[0], 1, img_rows, img_cols)
	X_test = X_test.reshape(X_test.shape[0], 1, img_rows, img_cols)
	input_shape = (1, img_rows, img_cols)
else:
	X_train = X_train.reshape(X_train.shape[0], img_rows, img_cols, 1)
	X_test = X_test.reshape(X_test.shape[0], img_rows, img_cols, 1)
	input_shape = (img_rows, img_cols, 1)

X_train = X_train.astype('float32')
X_test = X_test.astype('float32')
X_train /= 255
X_test /= 255
print('X_train shape:', X_train.shape)
print(X_train.shape[0], 'train samples')
print(X_test.shape[0], 'test samples')

# convert class vectors to binary class matrices
Y_train = np_utils.to_categorical(y_train, nb_classes)
Y_test = np_utils.to_categorical(y_test, nb_classes)

class Evaluator(evaluator_pb2_grpc.EvaluatorServicer):
    def Evaluate(self, request, context):
        K.clear_session()
        # build Keras model
        print("received evaluate request")
        model = Sequential()
        model.add(Conv2D(nb_filters, kernel_size, input_shape=input_shape))
        model.add(Activation('relu'))
        print(request.layers)
        for layer in request.layers:
	#the size of pic is reduced by half each we add a maxpooling layer, original size is 28*28, can't have maxpooling more than 2 times.
            typ = layer.WhichOneof("definition")
            print("> adding layer: " + typ)
            if (typ == None):
                continue
            if (typ == "convolution"):
                # do something here
                conv = layer.convolution
                model.add(Conv2D(conv.filters, kernel_size))
                model.add(Activation('relu'))
            elif (typ == "dropout"):
                dropout = layer.dropout
                model.add(Dropout(dropout.dimension))
                # do something here
            elif (typ == "flatten"):
                model.add(Flatten())
            elif (typ == "dense"):
                dense = layer.dense
                model.add(Dense(dense.neurons))
                model.add(Activation('relu'))
            elif (typ == "maxpooling"):
                model.add(MaxPooling2D(pool_size=pool_size))
        # classification layer
        model.add(Dense(nb_classes))
        model.add(Activation('softmax'))
        # train the model and send progress updates
        model.compile(loss='categorical_crossentropy',optimizer='adadelta',metrics=['accuracy'])
        print("> model compiled")
        print("> training")
        model_log = model.fit(X_train, Y_train, batch_size=batch_size, epochs = nb_epoch, verbose=1, validation_data=(X_test, Y_test))
        print(model.summary())
        score = model.evaluate(X_test, Y_test, verbose=0)
        return evaluator_pb2.ProgressUpdate(accuracy=score[1])
        # save the weights
        # model_digit_json = model.to_json()
        # with open('/project/hackathon/hackers03/shared/model_digit.json','w') as json_file:
        #     json_file.write(model_digit_json)
        #     model.save_weights('/project/hackathon/hackers03/shared/model_digit.h5')


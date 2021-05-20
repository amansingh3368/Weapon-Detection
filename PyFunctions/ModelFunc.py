from tensorflow import  keras
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import Dense, Dropout, Flatten, Input
from tensorflow.keras.layers import Conv2D, MaxPooling2D, BatchNormalization, AveragePooling2D
from tensorflow.keras.optimizers import Adam
from tensorflow.keras import regularizers
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.applications.vgg16 import VGG16


def get_vgg16(dim):
    model = Sequential()
    baseModel = VGG16(weights="imagenet", include_top=False,
                      input_tensor=Input(shape=dim))

    model.add(baseModel)
    headModel = model.add(AveragePooling2D(pool_size=(7, 7)))
    headModel = model.add(Flatten(name="flatten"))
    headModel = model.add(Dense(128, activation="relu"))
    headModel = model.add(Dropout(0.3))
    headModel = model.add(Dense(3, activation="softmax", name='Output'))

    # place the head FC model on top of the base model (this will become
    # the actual model we will train)

    # loop over all layers in the base model and freeze them so they will
    # *not* be updated during the first training process
    for layer in baseModel.layers:
        layer.trainable = False

    model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
    return model


def get_conv_model(dim):
    '''This function will create and compile a CNN given the input dimension'''
    inp_shape = dim
    act = 'relu'
    drop = .25
    kernal_reg = regularizers.l1(.001)
    optimizer = Adam(lr=.0001)

    model = Sequential()

    model.add(Conv2D(64, kernel_size=(3, 3), activation=act, input_shape=inp_shape,
                     kernel_regularizer=kernal_reg,
                     kernel_initializer='he_uniform', padding='same', name='Input_Layer'))
    model.add(MaxPooling2D(pool_size=(2, 2), strides=(3, 3)))

    model.add(Conv2D(64, (3, 3), activation=act, kernel_regularizer=kernal_reg,
                     kernel_initializer='he_uniform', padding='same'))
    model.add(MaxPooling2D(pool_size=(2, 2), strides=(3, 3)))

    model.add(Conv2D(128, (3, 3), activation=act, kernel_regularizer=kernal_reg,
                     kernel_initializer='he_uniform', padding='same'))
    model.add(Conv2D(128, (3, 3), activation=act, kernel_regularizer=kernal_reg,
                     kernel_initializer='he_uniform', padding='same'))
    model.add(MaxPooling2D(pool_size=(2, 2), strides=(3, 3)))

    model.add(Flatten())
    model.add(Dense(512, activation='relu'))
    model.add(Dense(128, activation='relu'))
    model.add(Dense(64, activation='relu'))
    model.add(Dense(32, activation='relu'))

    model.add(Dropout(drop))

    model.add(Dense(3, activation='softmax', name='Output_Layer'))

    model.compile(loss='categorical_crossentropy', optimizer=optimizer, metrics=['accuracy'])
    return model


def get_mobilenet(dim):
    '''This function will create, compile and return the mobilenet neural network given the input dimensions.  '''
    model = Sequential()
    optimizer = Adam(lr=.0005)
    baseModel = MobileNetV2(weights="imagenet", include_top=False,
                            input_tensor=Input(shape=dim))

    model.add(baseModel)
    model.add(AveragePooling2D(pool_size=(7, 7)))
    model.add(Flatten(name="flatten"))
    model.add(Dense(256, activation="relu"))
    model.add(Dropout(0.3))
    model.add(Dense(3, activation="softmax", name='Output'))

    for layer in baseModel.layers:
        layer.trainable = False

    model.compile(loss='categorical_crossentropy', optimizer=optimizer, metrics=['accuracy'])
    return model

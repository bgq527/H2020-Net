import efficientnet.tfkeras as efn
# from tensorflow.keras.applications.nasnet import preprocess_input
from tensorflow.keras.preprocessing import image
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D
from tensorflow.keras.models import Model, load_model
from sklearn.utils import shuffle
import tensorflow as tf
import numpy as np
import tensorflow.keras
import tensorflow.keras.backend as K
from tensorflow.keras.optimizers import Optimizer
import pandas as pd
import pickle
import os

os.environ['TF_KERAS'] = '1'
from keras_gradient_accumulation import AdamAccumulated


batch_size = 8
image_fp = np.load("data/image_fps.npy")
labels = np.load("data/labels.npy")
print(min(labels), max(labels))
labels = np.array(labels, dtype=np.str)
# labels = to_categorical(labels, dtype=np.int)
# print(len(labels[0]))
# image_fp, labels = shuffle(image_fp, labels)

file_df = pd.DataFrame(list(zip(image_fp, labels)), columns=["filename", "class"])
print(file_df.head())

datagen = image.ImageDataGenerator(horizontal_flip=True, zoom_range=[0.85, 0.85], preprocessing_function=efn.preprocess_input)
train_gen = datagen.flow_from_dataframe(file_df, target_size=(320, 320), shuffle=True, class_mode="categorical", batch_size=batch_size)
pickled_classes = open('eb3_traingen_classes', 'wb')
pickle.dump(train_gen.class_indices, pickled_classes)
pickled_classes.close()
# train_gen = Custom_Generator(image_fp, labels, batch_size)
# print(train_gen.class_indices)

"""
https://stackoverflow.com/questions/37340129/tensorflow-training-on-my-own-image
"""
acc_opt = AdamAccumulated(accumulation_steps=64)

model_checkpoint_callback = tensorflow.keras.callbacks.ModelCheckpoint(
    filepath="cp/efficientnetb3-6-{epoch:02d}",
    save_weights_only=False,
    monitor='loss',
    mode='min',
    save_best_only=True)

'''
Load model
'''
# model = load_model("cp/efficientnetb3-5-bottleneck-01", custom_objects={'AdamAccumulate': AdamAccumulate}, compile=False)

'''
Without bottleneck
'''
model = efn.EfficientNetB3(weights=None, include_top=True, input_shape=(320, 320, 3), classes=32093)
# en_model = efn.EfficientNetB3(weights='noisy-student', include_top=False, input_shape=(320, 320, 3), pooling='avg')
# model_output = Dense(32093, activation='softmax')(en_model.output)
# model = Model(inputs=en_model.input, outputs=model_output)

'''
With bottleneck
'''
# en_model = efn.EfficientNetB3(weights='noisy-student', include_top=False, input_shape=(320, 320, 3), pooling='avg')
# model_output = Dense(512, activation='relu')(en_model.output)
# model_output = Dense(32093, activation='softmax')(model_output)
# model = Model(inputs=en_model.input, outputs=model_output)


# model = Model(inputs=en_model.input, outputs=model_output)
model.compile(optimizer=acc_opt, loss="categorical_crossentropy")
model.summary()

model.fit_generator(generator=train_gen,
                    steps_per_epoch=int(image_fp.shape[0] // batch_size),
                    epochs=12,
                    verbose=1,
                    callbacks=[model_checkpoint_callback])

model.save("models\\efficientnetb3-6")
import os
import json
import shutil
import kagglehub
import tensorflow as tf

from tensorflow.keras import layers, models
from tensorflow.keras.callbacks import (
    ModelCheckpoint,
    EarlyStopping,
    ReduceLROnPlateau,
)


DATASET_NAME = "kamal01/top-agriculture-crop-disease"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_DIR = os.path.join(BASE_DIR, "disease_detection")

MODEL_PATH = os.path.join(APP_DIR, "crop_disease_model.keras")
CLASS_NAMES_PATH = os.path.join(APP_DIR, "class_names.json")
DATASET_DIR = os.path.join(APP_DIR, "dataset")

IMG_SIZE = 224
BATCH_SIZE = 16
EPOCHS_STAGE_1 = 10
EPOCHS_STAGE_2 = 15
SEED = 42


def download_dataset():
    print("Downloading dataset from Kaggle...")
    path = kagglehub.dataset_download(DATASET_NAME)
    print("Dataset downloaded at:", path)
    return path


def prepare_dataset(dataset_path):
    os.makedirs(APP_DIR, exist_ok=True)

    if os.path.exists(DATASET_DIR):
        print("Dataset already exists:", DATASET_DIR)
        return DATASET_DIR

    shutil.copytree(dataset_path, DATASET_DIR)
    print("Dataset copied to:", DATASET_DIR)
    return DATASET_DIR


def has_class_folders(path):
    if not os.path.isdir(path):
        return False

    folders = [
        name for name in os.listdir(path)
        if os.path.isdir(os.path.join(path, name))
    ]

    return len(folders) >= 2


def find_train_dir(base_dir):
    possible_names = ["train", "Train", "training", "Training"]

    for root, dirs, files in os.walk(base_dir):
        for name in possible_names:
            possible_path = os.path.join(root, name)
            if name in dirs and has_class_folders(possible_path):
                return possible_path

    if has_class_folders(base_dir):
        return base_dir

    raise FileNotFoundError(
        "Training directory not found. Dataset must contain class folders."
    )


def save_class_names(class_names):
    with open(CLASS_NAMES_PATH, "w", encoding="utf-8") as f:
        json.dump(class_names, f, ensure_ascii=False, indent=4)

    print("Class names saved:", CLASS_NAMES_PATH)


def build_datasets(train_dir):
    train_ds = tf.keras.utils.image_dataset_from_directory(
        train_dir,
        validation_split=0.2,
        subset="training",
        seed=SEED,
        image_size=(IMG_SIZE, IMG_SIZE),
        batch_size=BATCH_SIZE,
        label_mode="categorical",
        shuffle=True,
    )

    val_ds = tf.keras.utils.image_dataset_from_directory(
        train_dir,
        validation_split=0.2,
        subset="validation",
        seed=SEED,
        image_size=(IMG_SIZE, IMG_SIZE),
        batch_size=BATCH_SIZE,
        label_mode="categorical",
        shuffle=False,
    )

    class_names = train_ds.class_names
    save_class_names(class_names)

    AUTOTUNE = tf.data.AUTOTUNE

    train_ds = train_ds.cache().shuffle(1000).prefetch(AUTOTUNE)
    val_ds = val_ds.cache().prefetch(AUTOTUNE)

    return train_ds, val_ds, class_names


def build_model(num_classes):
    data_augmentation = tf.keras.Sequential(
        [
            layers.RandomFlip("horizontal"),
            layers.RandomRotation(0.15),
            layers.RandomZoom(0.15),
            layers.RandomContrast(0.15),
        ],
        name="data_augmentation",
    )

    base_model = tf.keras.applications.EfficientNetB0(
        include_top=False,
        weights="imagenet",
        input_shape=(IMG_SIZE, IMG_SIZE, 3),
    )

    base_model.trainable = False

    inputs = layers.Input(shape=(IMG_SIZE, IMG_SIZE, 3))

    x = data_augmentation(inputs)
    x = tf.keras.applications.efficientnet.preprocess_input(x)
    x = base_model(x, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.35)(x)

    outputs = layers.Dense(num_classes, activation="softmax")(x)

    model = models.Model(inputs, outputs, name="crop_disease_efficientnetb0")

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    return model, base_model


def get_callbacks():
    return [
        ModelCheckpoint(
            MODEL_PATH,
            monitor="val_accuracy",
            save_best_only=True,
            mode="max",
            verbose=1,
        ),
        EarlyStopping(
            monitor="val_loss",
            patience=6,
            restore_best_weights=True,
            verbose=1,
        ),
        ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.3,
            patience=3,
            min_lr=1e-7,
            verbose=1,
        ),
    ]


def train():
    os.makedirs(APP_DIR, exist_ok=True)

    dataset_path = download_dataset()
    local_dataset = prepare_dataset(dataset_path)
    train_dir = find_train_dir(local_dataset)

    print("Training folder:", train_dir)

    train_ds, val_ds, class_names = build_datasets(train_dir)

    num_classes = len(class_names)

    if num_classes < 2:
        raise ValueError("At least 2 classes are required for training.")

    model, base_model = build_model(num_classes)
    callbacks = get_callbacks()

    print("\nSTAGE 1: Training classifier head...")
    model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=EPOCHS_STAGE_1,
        callbacks=callbacks,
    )

    print("\nSTAGE 2: Fine tuning EfficientNet...")
    base_model.trainable = True

    for layer in base_model.layers[:-40]:
        layer.trainable = False

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-5),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=EPOCHS_STAGE_2,
        callbacks=callbacks,
    )

    model.save(MODEL_PATH)

    print("\nTraining complete.")
    print("Model saved:", MODEL_PATH)
    print("Class names saved:", CLASS_NAMES_PATH)


if __name__ == "__main__":
    train()
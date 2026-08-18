import os
import json
import shutil
import kagglehub
import tensorflow as tf

from tensorflow.keras import layers
from tensorflow.keras import models

from tensorflow.keras.callbacks import (
    ModelCheckpoint,
    EarlyStopping,
    ReduceLROnPlateau,
)


DATASET_NAME = "rtlmhjbn/ip02-dataset"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATASET_DIR = os.path.join(BASE_DIR, "dataset", "ip02_dataset")
CLASSIFICATION_DIR = os.path.join(DATASET_DIR, "classification", "train")

MODEL_DIR = os.path.join(BASE_DIR, "models")
MODEL_PATH = os.path.join(MODEL_DIR, "pest_model.keras")
CLASS_NAMES_PATH = os.path.join(MODEL_DIR, "pest_class_names.json")

IMG_SIZE = 224
BATCH_SIZE = 16
EPOCHS = 50
FINE_TUNE_EPOCHS = 5
SEED = 42


PEST_NAME_MAP = {
    "1": "rice leaf roller",
    "2": "rice leaf caterpillar",
    "3": "paddy stem maggot",
    "4": "asiatic rice borer",
    "5": "yellow rice borer",
    "6": "rice gall midge",
    "7": "Rice Stemfly",
    "8": "brown plant hopper",
    "9": "white backed plant hopper",
    "10": "small brown plant hopper",
    "11": "rice water weevil",
    "12": "rice leafhopper",
    "13": "grain spreader thrips",
    "14": "rice shell pest",
    "15": "grub",
    "16": "mole cricket",
    "17": "wireworm",
    "18": "white margined moth",
    "19": "black cutworm",
    "20": "large cutworm",
    "21": "yellow cutworm",
    "22": "red spider",
    "23": "corn borer",
    "24": "army worm",
    "25": "aphids",
    "26": "Potosiabre vitarsis",
    "27": "peach borer",
    "28": "english grain aphid",
    "29": "green bug",
    "30": "bird cherry-oat aphid",
    "31": "wheat blossom midge",
    "32": "penthaleus major",
    "33": "longlegged spider mite",
    "34": "wheat phloeothrips",
    "35": "wheat sawfly",
    "36": "cerodonta denticornis",
    "37": "beet fly",
    "38": "flea beetle",
    "39": "cabbage army worm",
    "40": "beet army worm",
    "41": "Beet spot flies",
    "42": "meadow moth",
    "43": "beet weevil",
    "44": "sericaorient alismots chulsky",
    "45": "alfalfa weevil",
    "46": "flax budworm",
    "47": "alfalfa plant bug",
    "48": "tarnished plant bug",
    "49": "Locustoidea",
    "50": "lytta polita",
    "51": "legume blister beetle",
    "52": "blister beetle",
    "53": "therioaphis maculata Buckton",
    "54": "odontothrips loti",
    "55": "Thrips",
    "56": "alfalfa seed chalcid",
    "57": "Pieris canidia",
    "58": "Apolygus lucorum",
    "59": "Limacodidae",
    "60": "Viteus vitifoliae",
    "61": "Colomerus vitis",
    "62": "Brevipoalpus lewisi McGregor",
    "63": "oides decempunctata",
    "64": "Polyphagotarsonemus latus",
    "65": "Pseudococcus comstocki Kuwana",
    "66": "parathrene regalis",
    "67": "Ampelophaga",
    "68": "Lycorma delicatula",
    "69": "Xylotrechus",
    "70": "Cicadella viridis",
    "71": "Miridae",
    "72": "Trialeurodes vaporariorum",
    "73": "Erythroneura apicalis",
    "74": "Papilio xuthus",
    "75": "Panonchus citri McGregor",
    "76": "Phyllocoptes oleiverus ashmead",
    "77": "Icerya purchasi Maskell",
    "78": "Unaspis yanonensis",
    "79": "Ceroplastes rubens",
    "80": "Chrysomphalus aonidum",
    "81": "Parlatoria zizyphus Lucus",
    "82": "Nipaecoccus vastalor",
    "83": "Aleurocanthus spiniferus",
    "84": "Tetradacus c Bactrocera minax",
    "85": "Dacus dorsalis(Hendel)",
    "86": "Bactrocera tsuneonis",
    "87": "Prodenia litura",
    "88": "Adristyrannus",
    "89": "Phyllocnistis citrella Stainton",
    "90": "Toxoptera citricidus",
    "91": "Toxoptera aurantii",
    "92": "Aphis citricola Vander Goot",
    "93": "Scirtothrips dorsalis Hood",
    "94": "Dasineura sp",
    "95": "Lawana imitata Melichar",
    "96": "Salurnis marginella Guerr",
    "97": "Deporaus marginatus Pascoe",
    "98": "Chlumetia transversa",
    "99": "Mango flat beak leafhopper",
    "100": "Rhytidodera bowrinii white",
    "101": "Sternochetus frigidus",
    "102": "Cicadellidae",
}


def download_dataset():
    print("Downloading dataset from Kaggle...")
    path = kagglehub.dataset_download(DATASET_NAME)
    print("Dataset downloaded at:", path)
    return path


def prepare_dataset(dataset_path):
    os.makedirs(os.path.dirname(DATASET_DIR), exist_ok=True)

    if os.path.exists(DATASET_DIR):
        print("Dataset already exists:", DATASET_DIR)
        return DATASET_DIR

    shutil.copytree(dataset_path, DATASET_DIR)
    print("Dataset copied to:", DATASET_DIR)
    return DATASET_DIR


def find_classification_train_dir():
    if os.path.exists(CLASSIFICATION_DIR):
        return CLASSIFICATION_DIR

    raise FileNotFoundError(
        f"Training folder not found: {CLASSIFICATION_DIR}"
    )


def convert_class_names(number_class_names):
    pest_names = []

    for class_id in number_class_names:
        pest_name = PEST_NAME_MAP.get(str(class_id), f"Pest-{class_id}")
        pest_names.append(pest_name)

    return pest_names


def save_class_names(number_class_names):
    os.makedirs(MODEL_DIR, exist_ok=True)

    pest_names = convert_class_names(number_class_names)

    with open(CLASS_NAMES_PATH, "w", encoding="utf-8") as f:
        json.dump(pest_names, f, ensure_ascii=False, indent=4)

    print("Class names saved:", CLASS_NAMES_PATH)
    print("Mapped Pest Names:", pest_names)


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

    number_class_names = train_ds.class_names

    save_class_names(number_class_names)

    AUTOTUNE = tf.data.AUTOTUNE

    train_ds = train_ds.prefetch(AUTOTUNE)
    val_ds = val_ds.prefetch(AUTOTUNE)

    pest_names = convert_class_names(number_class_names)

    return train_ds, val_ds, pest_names


def build_model(num_classes):
    data_augmentation = tf.keras.Sequential(
        [
            layers.RandomFlip("horizontal"),
            layers.RandomRotation(0.15),
            layers.RandomZoom(0.15),
            layers.RandomContrast(0.15),
        ]
    )

    base_model = tf.keras.applications.EfficientNetB3(
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

    model = models.Model(inputs, outputs, name="pest_detection_mobilenetv2")

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
            patience=5,
            restore_best_weights=True,
            verbose=1,
        ),
        ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.3,
            patience=2,
            min_lr=1e-7,
            verbose=1,
        ),
    ]


def train():
    os.makedirs(MODEL_DIR, exist_ok=True)

    dataset_path = download_dataset()
    prepare_dataset(dataset_path)

    train_dir = find_classification_train_dir()

    print("Training folder:", train_dir)

    train_ds, val_ds, pest_names = build_datasets(train_dir)

    num_classes = len(pest_names)

    if num_classes < 2:
        raise ValueError("At least 2 pest classes are required.")

    print("Total Classes:", num_classes)
    print("Pest Names:", pest_names)

    model, base_model = build_model(num_classes)

    print("\nStage 1: Training classifier head...")
    model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=EPOCHS,
        callbacks=get_callbacks(),
    )

    print("\nStage 2: Fine tuning MobileNetV2...")
    base_model.trainable = True

    for layer in base_model.layers[:-30]:
        layer.trainable = False

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-5),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=FINE_TUNE_EPOCHS,
        callbacks=get_callbacks(),
    )

    model.save(MODEL_PATH)

    print("\nTraining complete.")
    print("Model saved:", MODEL_PATH)
    print("Class names saved:", CLASS_NAMES_PATH)


if __name__ == "__main__":
    train()
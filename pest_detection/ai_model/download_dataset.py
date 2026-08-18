import os
import shutil
import kagglehub


def download_dataset():

    print("Downloading dataset...")

    # Download dataset from Kaggle
    dataset_path = kagglehub.dataset_download(
        "rtlmhjbn/ip02-dataset"
    )

    print("\nOriginal Dataset Path:")
    print(dataset_path)

    # Create local dataset folder
    target_folder = "dataset/ip02_dataset"

    os.makedirs("dataset", exist_ok=True)

    # Delete old dataset if already exists
    if os.path.exists(target_folder):
        shutil.rmtree(target_folder)

    # Copy dataset to project folder
    shutil.copytree(dataset_path, target_folder)

    print("\nDataset copied successfully!")

    print("\nProject Dataset Location:")
    print(os.path.abspath(target_folder))

    # Show folder structure
    print("\nFolder Structure:")
    print("dataset/")
    print("└── ip02_dataset/")
    print("    ├── train/")
    print("    │   ├── images/")
    print("    │   └── labels/")
    print("    │")
    print("    ├── valid/")
    print("    │   ├── images/")
    print("    │   └── labels/")
    print("    │")
    print("    ├── test/")
    print("    │   ├── images/")
    print("    │   └── labels/")
    print("    │")
    print("    └── data.yaml")


if __name__ == "__main__":
    download_dataset()
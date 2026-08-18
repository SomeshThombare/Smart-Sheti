import kagglehub


def download_dataset():
    path = kagglehub.dataset_download("kamal01/top-agriculture-crop-disease")
    print("Dataset downloaded at:", path)
    return path


if __name__ == "__main__":
    download_dataset()
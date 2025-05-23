import os
from typing import Tuple

import cv2 as cv
import pandas as pd
import torch
from torch.utils.data import DataLoader, Dataset, Subset
from torchvision.transforms import v2


####################
# Dataset Class
####################
class PolypDataset(Dataset):
    def __init__(
        self,
        annotations_file: str = None,
        img_transform=None,
        msk_transform=None,
        mode: str = "train",  # 'train', 'valid', 'test'
        device=None,  # 'cuda' or 'cpu'
    ):
        self.annotations_file = pd.read_csv(annotations_file)
        self.mode = mode  # 'train', 'valid', 'test'
        self.device = device  # 'cuda' or 'cpu'
        self.img_tf = img_transform.to(self.device) if img_transform else None
        self.mask_tf = msk_transform.to(self.device) if msk_transform else None
        self.image_normalize = v2.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        self.mask_normalize = v2.Normalize(mean=[0.5], std=[0.5])  # Assuming binary masks

    def __len__(self):
        return len(self.annotations_file)

    def __getitem__(self, index):
        return self._get_item_from_csv(index)

    def _get_item_from_csv(self, index):
        img_path = self.annotations_file.iloc[index, 0]
        mask_path = self.annotations_file.iloc[index, 1]

        if not os.path.exists(img_path):
            raise FileNotFoundError(f"The image file {img_path} does not exist.")
        if not os.path.exists(mask_path):
            raise FileNotFoundError(f"The mask file {mask_path} does not exist.")

        # Load image and mask from paths
        image = cv.imread(img_path)
        image = cv.cvtColor(image, cv.COLOR_BGR2RGB)
        mask = cv.imread(mask_path, cv.IMREAD_GRAYSCALE)

        image = torch.from_numpy(image).permute(2, 0, 1).float() / 255.0
        mask = torch.from_numpy(mask).unsqueeze(0).float() / 255.0

        if self.img_tf:
            image = self.img_tf(image)
        if self.mask_tf:
            mask = self.mask_tf(mask)
        return image, mask


############################################
# Return a dataloader for the given dataset.
############################################
def get_data_loaders(
    annotations_path: str = None,
    transform_image=None,  # transforms.Compose([transforms.ToTensor()]) or None
    transform_mask=None,
    batch_size: int = 16,
    num_workers: int = 4,
    device: str = "cuda",
) -> Tuple[DataLoader, DataLoader, DataLoader]:
    """Returns a dataloader for the given dataset."""

    main_dataset = PolypDataset(
        annotations_path,
        img_transform=transform_image,
        msk_transform=transform_mask,
        device=device,
    )

    # indicies dataset
    size_dataset = len(main_dataset)
    indices = list(range(size_dataset))

    split1 = int(0.8 * size_dataset)  # 80% for training
    split2 = int(0.9 * size_dataset)  # 10% for validation, 10% for testing

    train_indices = indices[:split1]
    val_indices = indices[split1:split2]
    test_indices = indices[split2:]

    # Split data
    train_dataset = Subset(main_dataset, train_indices)
    val_dataset = Subset(main_dataset, val_indices)
    test_dataset = Subset(main_dataset, test_indices)
    train_data_loader = DataLoader(
        train_dataset, batch_size=batch_size, shuffle=True, num_workers=num_workers
    )
    val_data_loader = DataLoader(
        val_dataset, batch_size=batch_size, shuffle=False, num_workers=num_workers
    )

    test_data_loader = DataLoader(
        test_dataset, batch_size=batch_size, shuffle=False, num_workers=num_workers
    )

    return train_data_loader, val_data_loader, test_data_loader


################
# Example usage
################
# if __name__ == "__main__":
#     # Example usage
#     annotations_file_path = "../data/external/data.csv"

#     transforms = v2.Compose(
#         [
#             v2.Resize(size=(640, 640)),
#             v2.ToDtype(torch.float32, scale=True),
#         ]
#     )

#     train_loader, val_loader, test_loader = get_data_loaders(
#         annotations_path=annotations_file_path,
#         transform=transforms,
#         batch_size=16,
#         num_workers=4,
#         device="cpu",
#     )

import torch
import torch.nn as nn
from torch.utils.data import Dataset

class Custom_Dataset(Dataset):

    def __init__(self, features, labels, transform):  

        self.features = features
        self.labels = labels
        self.transform = transform

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):

        self.image = self.features[idx]    # 100x100 one channel
        self.steer = self.labels[idx]       # 0 ~ 0.png steer

        # for transform  input:img
        if self.transform:
            self.image = self.transform(self.image)
        return self.image, self.steer



class AutoPilot2Net(nn.Module):
    def __init__(self, output: int = 1, dropout: float = 0.5) -> None: 
        super().__init__()
        
        # for loss function
        self.criteria = nn.MSELoss(reduction='mean')

        # input = N x C x W x H
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, stride=1, padding=1),   # in_ch=3  out_ch=32 size:3x3,stride, padding=same
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2, padding=1),     # size:2x2, stride=2, padding=valid
            nn.Conv2d(32, 32, kernel_size=3, stride=1, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2, padding=1), 
            nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2, padding=1), 
            nn.Conv2d(64, 64, kernel_size=3, stride=1, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2, padding=1), 
            nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2, padding=1), 
            nn.Conv2d(128, 128, kernel_size=3, stride=1, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2, padding=1), 
        )

        self.avgpool = nn.AdaptiveAvgPool2d((6, 6))

        self.mlp = nn.Sequential(
            nn.Dropout(p=dropout),
            nn.Linear(128 * 6 * 6, 1024),
            nn.ReLU(inplace=True),
            nn.Linear(1024, 256),
            nn.ReLU(inplace=True),
            nn.Linear(256, 64),
            nn.ReLU(inplace=True),            
            nn.Linear(64, output),
        )
        # 分别对应的位置初始化
        torch.nn.init.kaiming_normal_(self.features[0].weight)
        torch.nn.init.kaiming_normal_(self.features[3].weight)
        torch.nn.init.kaiming_normal_(self.features[6].weight)
        torch.nn.init.kaiming_normal_(self.features[9].weight)
        torch.nn.init.kaiming_normal_(self.features[12].weight)
        torch.nn.init.kaiming_normal_(self.features[15].weight)
        torch.nn.init.kaiming_normal_(self.mlp[1].weight)
        torch.nn.init.kaiming_normal_(self.mlp[3].weight)
        torch.nn.init.kaiming_normal_(self.mlp[5].weight)
        torch.nn.init.kaiming_normal_(self.mlp[7].weight)


    def forward(self, x: torch.Tensor) -> torch.Tensor:
        self.beta_x = 1.0/0.0382
        x = self.features(x)
        x = self.avgpool(x)
        x = torch.flatten(x, 1)
        x = self.mlp(x)
        # (0.0382 * x): [-1.57, 1.57]
        x = self.beta_x * torch.tanh(1.0 /self.beta_x * x)
        return x

    def steering_acc_loss(self, net_out, train_label):
        loss = self.criteria(net_out, train_label)
        return loss
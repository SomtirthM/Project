# -*- coding: utf-8 -*-
# author: somtirtha_mukherjee

import torch
import torch.nn as nn
import math
import logging
import torch.utils.model_zoo as model_zoo
import torchvision.models.resnet

from models.gat import GATModel

logger = logging.getLogger('project')

__all__ = ['ResNet', 'resnet50', 'resnet101',
           'resnet152']

model_urls = {
    'resnet18': 'https://download.pytorch.org/models/resnet18-5c106cde.pth',
    'resnet34': 'https://download.pytorch.org/models/resnet34-333f7ec4.pth',
    'resnet50': 'https://download.pytorch.org/models/resnet50-19c8e357.pth',
    'resnet101': 'https://download.pytorch.org/models/resnet101-5d3b4d8f.pth',
    'resnet152': 'https://download.pytorch.org/models/resnet152-b121ed2d.pth',
}


def conv3x3(in_planes, out_planes, stride=1):
    """3x3 convolution with padding"""
    return nn.Conv2d(in_planes, out_planes, kernel_size=3, stride=stride,
                     padding=1, bias=False)


class BasicBlock(nn.Module):
    expansion = 1

    def __init__(self, inplanes, planes, stride=1, downsample=None):
        super(BasicBlock, self).__init__()
        self.conv1 = conv3x3(inplanes, planes, stride)
        self.bn1 = nn.BatchNorm2d(planes)
        self.relu = nn.ReLU(inplace=True)
        self.conv2 = conv3x3(planes, planes)
        self.bn2 = nn.BatchNorm2d(planes)
        self.downsample = downsample
        self.stride = stride

    def forward(self, x):
        residual = x

        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)

        out = self.conv2(out)
        out = self.bn2(out)

        if self.downsample is not None:
            residual = self.downsample(x)

        out += residual
        out = self.relu(out)

        return out


class Bottleneck(nn.Module):
    expansion = 4

    def __init__(self, inplanes, planes, stride=1, downsample=None):
        super(Bottleneck, self).__init__()
        self.conv1 = nn.Conv2d(inplanes, planes, kernel_size=1, bias=False)
        self.bn1 = nn.BatchNorm2d(planes)
        self.conv2 = nn.Conv2d(planes, planes, kernel_size=3, stride=stride,
                               padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(planes)
        self.conv3 = nn.Conv2d(planes, planes * 4, kernel_size=1, bias=False)
        self.bn3 = nn.BatchNorm2d(planes * 4)
        self.relu = nn.ReLU(inplace=True)
        self.downsample = downsample
        self.stride = stride

    def forward(self, x):
        residual = x

        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)

        out = self.conv2(out)
        out = self.bn2(out)
        out = self.relu(out)

        out = self.conv3(out)
        out = self.bn3(out)

        if self.downsample is not None:
            residual = self.downsample(x)

        out += residual
        out = self.relu(out)

        return out


class ResNet(nn.Module):

    def __init__(self, block, layers, out):
        self.inplanes = 64
        super(ResNet, self).__init__()
        self.conv1 = nn.Conv2d(3, 64, kernel_size=7, stride=2, padding=3,
                               bias=False)
        self.bn1 = nn.BatchNorm2d(64)
        self.relu = nn.ReLU(inplace=True)
        self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        self.layer1 = self._make_layer(block, 64, layers[0])
        self.layer2 = self._make_layer(block, 128, layers[1], stride=2)
        self.layer3 = self._make_layer(block, 256, layers[2], stride=2)
        self.gatlayer3 = GATModel(out[-2], (10, 10))
        self.layer4 = self._make_layer(block, 512, layers[3], stride=2)
        self.gatlayer4 = GATModel(out[-1], (10, 10))

        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                n = m.kernel_size[0] * m.kernel_size[1] * m.out_channels
                m.weight.data.normal_(0, math.sqrt(2. / n))
            elif isinstance(m, nn.BatchNorm2d):
                m.weight.data.fill_(1)
                m.bias.data.zero_()

    def _make_layer(self, block, planes, blocks, stride=1):
        downsample = None
        if stride != 1 or self.inplanes != planes * block.expansion:
            downsample = nn.Sequential(
                nn.Conv2d(self.inplanes, planes * block.expansion,
                          kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm2d(planes * block.expansion),
            )

        layers = []
        layers.append(block(self.inplanes, planes, stride, downsample))
        self.inplanes = planes * block.expansion
        for i in range(1, blocks):
            layers.append(block(self.inplanes, planes))

        return nn.Sequential(*layers)

    def _load_pretrained_model(self, model_url):
        pretrain_dict = model_zoo.load_url(model_url)
        model_dict = {}
        state_dict = self.state_dict()
        for k, v in pretrain_dict.items():
            if k in state_dict:
                model_dict[k] = v
        state_dict.update(model_dict)
        self.load_state_dict(state_dict)
        logger.info('load pretrained models from imagenet')

    def forward(self, input):
        x = self.conv1(input)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)
        import numpy as np
        c2 = self.layer1(x)
        np.save("npy_files_gat/c2.npy", c2.cpu().numpy())
        c3 = self.layer2(c2)
        np.save("npy_files_gat/c3.npy", c3.cpu().numpy())
        c4 = self.layer3(c3)
        np.save("npy_files_gat/c4.npy", c4.cpu().numpy())
        c4_ = self.gatlayer3(c4) # GAT layer introduced
        np.save("npy_files_gat/c4_gat.npy", c4_.cpu().numpy())
        c5 = self.layer4(c4_)
        np.save("npy_files_gat/c5.npy", c5.cpu().numpy())
        c5_ = self.gatlayer4(c5) # GAT layer introduced
        np.save("npy_files_gat/c5_gat.npy", c5_.cpu().numpy())
        return c2, c3, c4_, c5_

def resnet18(pretrained=False, **kwargs):
    """Constructs a ResNet-18 models.

    Args:
        pretrained (bool): If True, returns a models pre-trained on ImageNet
    """
    model = ResNet(BasicBlock, [2, 2, 2, 2], **kwargs)
    if pretrained:
        model._load_pretrained_model(model_urls['resnet18'])
    return model


def resnet34(pretrained=False, **kwargs):
    """Constructs a ResNet-34 models.

    Args:
        pretrained (bool): If True, returns a models pre-trained on ImageNet
    """
    model = ResNet(BasicBlock, [3, 4, 6, 3], **kwargs)
    if pretrained:
        model._load_pretrained_model(model_urls['resnet34'])
    return model

def resnet50(pretrained=False, **kwargs):
    """Constructs a ResNet-50 models.

    Args:
        pretrained (bool): If True, returns a models pre-trained on ImageNet
    """
    model = ResNet(Bottleneck, [3, 4, 6, 3], **kwargs)
    if pretrained:
        model._load_pretrained_model(model_urls['resnet50'])
    return model


def resnet101(pretrained=False, out=[256, 512, 1024, 2048], **kwargs):
    """Constructs a ResNet-101 models.

    Args:
        pretrained (bool): If True, returns a models pre-trained on ImageNet
    """
    model = ResNet(Bottleneck, [3, 4, 23, 3], out, **kwargs)
    if pretrained:
        model._load_pretrained_model(model_urls['resnet101'])
    return model


def resnet152(pretrained=False, **kwargs):
    """Constructs a ResNet-152 models.

    Args:
        pretrained (bool): If True, returns a models pre-trained on ImageNet
    """
    model = ResNet(Bottleneck, [3, 8, 36, 3], **kwargs)
    if pretrained:
        model._load_pretrained_model(model_urls['resnet152'])
    return model


if __name__ == '__main__':
    x = torch.zeros(1, 3, 640, 640)
    net = resnet50()
    y = net(x)
    for u in y:
        print(u.shape)
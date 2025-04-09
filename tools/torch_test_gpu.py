#!/usr/bin/env python
import torch
dev = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
print(repr(dev))

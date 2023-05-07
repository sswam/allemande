#!/usr/bin/env python3
import numpy as np
print("\n".join('#'+f"{int(x):02x}"*3 for x in np.arange(0., 256.5, 255.999/7.)))

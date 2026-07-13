import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".." ))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
import config
from data import loaders
from analysis import returns as R, regression, regimes, risk, robustness, valuation, profitability, synthesis, scorecard

app = FastAPI(title = "Space Economy Thesis API")
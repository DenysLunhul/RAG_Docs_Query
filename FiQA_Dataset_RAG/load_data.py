from beir import util
from beir.datasets.data_loader import GenericDataLoader
import pathlib

url = (f"https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/fiqa.zip")
out_dir = "datasets"
data_path = util.download_and_unzip(url, out_dir)
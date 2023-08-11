import logging.config

import yaml
from dotenv import load_dotenv

load_dotenv()

from app.path_utils import root_path  # noqa: E402

with open(root_path() / "logging-conf.yaml") as f:
    config = yaml.safe_load(f.read())

logging.config.dictConfig(config)

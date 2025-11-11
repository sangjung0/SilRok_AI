import os

from pathlib import Path
from logging import Logger

from sjpy.reference import get_top_package_root
from sjpy.file.yaml import read_yaml
from sjpy.logger import generate
from sjpy.decorator import generate_simple_decorator
from sjpy.collection import to_namespace

DEFAULT_CONFIG_FILE = "default_config.yml"
DEFAULT_HEAD = "SilRok"
DEFAULT_NAME = "SilRok"

package_path = get_top_package_root()
working_dir = Path.cwd()


def __core() -> tuple[dict, Logger]:
    candidate = [
        Path(os.getenv("CONFIG_PATH")),
        working_dir / DEFAULT_CONFIG_FILE,
        package_path.parent / DEFAULT_CONFIG_FILE,
    ]

    config = None
    for path in candidate:
        if path and path.exists() and path.is_file():
            if DEFAULT_HEAD in (config := read_yaml(path)):
                config = config[DEFAULT_HEAD]
                break
    else:
        raise FileNotFoundError("No valid configuration file found.")

    config["log"]["path"] = Path(config["log"]["path"])
    logger = generate(DEFAULT_NAME, **config["log"])

    return config, logger


config, logger = __core()
config, config_dict = to_namespace(config), config
default_logger = generate_simple_decorator("logger", logger)
default_config = generate_simple_decorator("config", config)

__all__ = [
    "config",
    "config_dict",
    "logger",
    "working_dir",
    "package_path",
    "default_logger",
    "default_config",
]

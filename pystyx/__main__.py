import json
import os
from pathlib import Path
from typing import Dict

from .mapper import Mapper
from . import create_maps


def main():
    def _get_json():
        cwd = Path(os.getcwd())
        path = cwd / "blob.json"
        with path.open(encoding="utf-8") as infile:
            return json.load(infile)

    maps: Dict[str, Mapper] = create_maps()
    blob = _get_json()

    customer_mapper = maps.get("customer")
    mapped_object = customer_mapper(blob)

    print(mapped_object)


if __name__ == "__main__":
    main()

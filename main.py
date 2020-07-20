import json
from pathlib import Path
from typing import Dict, Generator

import toml
from munch import munchify

from .functions import TomlFunction
from .mapper import Mapper

__all__ = ["create_maps"]


def get_cwd() -> str:
    return Path(__file__).parent


def create_maps(
    maps_location="maps", functions_location="functions.styx"
) -> Dict[str, Mapper]:
    cwd = get_cwd()
    styx_files: Generator[Path] = cwd.glob(f"{maps_location}/*.styx")
    functions_file: Path = cwd.path(functions_location)
    functions_toml = (
        munchify(toml.load(functions_file)) if functions_file.exists() else None
    )
    functions = TomlFunction.parse_functions(functions_toml)
    map_objects = (munchify(toml.load(path)) for path in styx_files)
    mappers = (Mapper(map_, functions) for map_ in map_objects)
    maps = {mapper.type: mapper for mapper in mappers}
    # Mutation. Add maps to Mappers
    for map_ in maps.values():
        map_.maps = maps
    return maps


def main():
    def _get_json():
        cwd = get_cwd()
        path = cwd / "blob.json"
        with path.open(encoding="utf-8") as infile:
            return json.load(infile)

    maps: Dict[str, Mapper] = create_maps()
    blob = _get_json()

    creature_mapper = maps.get("Creature")
    mapped_object = creature_mapper(blob)

    print(mapped_object)


if __name__ == "__main__":
    main()

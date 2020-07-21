import os
from pathlib import Path
from typing import Dict, Generator

import toml
from munch import munchify

from .functions import TomlFunction, styx_function
from .mapper import Mapper

__all__ = ["create_maps", "styx_function"]


def empty_functions():
    return munchify({"functions": []})


def create_maps(
    maps_location="maps", functions_location="functions.styx"
) -> Dict[str, Mapper]:
    cwd = Path(os.getcwd())
    styx_files: Generator[Path] = cwd.glob(f"{maps_location}/*.styx")
    functions_file: Path = cwd / functions_location
    functions_toml = (
        munchify(toml.load(functions_file))
        if functions_file.exists()
        else empty_functions()
    )
    functions = TomlFunction.parse_functions(functions_toml)
    map_objects = (munchify(toml.load(path)) for path in styx_files)
    mappers = (Mapper(map_, functions) for map_ in map_objects)
    maps = {mapper.type: mapper for mapper in mappers}
    # Mutation. Add "definitions" to Mappers
    for map_ in maps.values():
        map_.update_definitions(maps)
    return maps

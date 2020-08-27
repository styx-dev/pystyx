# pystyx

Python implementation of Styx ETL declarative TOML.

For more information about Styx, [please see the definition here](https://github.com/styx-dev/styx).

## Quick Start

1. In your Python project, `mkdir` maps
2. `touch` functions.styx (TODD: Add init for this) and functions.py (if you want to write custom functions)
3. In `functions.styx`, add an array called `functions`, with the names of any functions you plan on using in your mappings:

    ```toml
    # functions.styx
   
    functions = ["to_upper_case"]
    ```

4. In `functions.py` implement your custom function. Ensure that your function takes the same number of arguments as your expected `input_paths`, or use `*args`. The 

    ```python
    # functions.py
   
    from pystyx.functions import styx_function
   
    @styx_function
    def to_upper_case(value):
       return value.upper()
       
    ```
3. Add any of your Styx Definitions to the `maps/` directory. For example,
    ```toml
    from_type = "erp_address"
    to_type = "Address"

    [fields]

        [fields.address1]
        input_paths = ["addr1"]

        [fields.address2]
        input_paths = ["addr2"]

        [fields.city]
        input_paths= ["city"]

        [fields.state]
        input_paths = ["province"]
        function = "to_upper_case"

        [fields.zip]
        input_paths = ["postalCode"]

   ```
   
4. Initialize maps in your Python code:
    ```json
    // blob.json
    {
       "addr1": "123 Street",
       "addr2": "Ste. 800",
       "city": "Dallas",
       "province": "tx",
       "postalCode": "75080",
    }
    ```
   
    ```python
    # main.py
    import json
    import pathlib
   
    import pystyx
   
    # Ensure that your decorated functions are evaluated
    from functions import *  
   
    with pathlib.Path("blob.json").open() as json_file:
        blob = json.load(json_file)
        maps = pystyx.create_maps()  # Defaults to `/maps` and `functions.styx`
        mapper = maps.get("erp_address")  # 'from_type` from the Definition above
        mapped_obj = mapper(blob)
        print(mapped_obj)
    ```
   
   Prints:
   ```json
    {
       "address1": "123 Street",
       "address2": "Ste. 800",
       "city": "Dallas",
       "state": "TX",  // Upper case now
       "zip": "75080"
    }
   ```

## Styx Validation

`pystyx.create_maps()` parses (and thereby validates) the Styx files before loading them. I hope to extract this validation as a CLI tool (along with generating Styx structures).

## Styx Implementation

I wanted this to be a good first example of a Styx implementation, so I believe it currently implements all features of the Styx standard.
Parsing and validation I would like to extract into its own library eventually.

| Feature                  | Implemented        |
| ------------------------ | ------------------ |
| **Structures**           |                    |
| -  JSON objects          | :heavy_check_mark: |
| **Validation/Parsing**   |                    |
| - Full parsing           | :heavy_check_mark: |
| **Preprocessing**        |                    |
| -  input_paths           | :heavy_check_mark: |
| -  output_paths          | :heavy_check_mark: |
| -  function              | :heavy_check_mark: |
| -  or_else               | :heavy_check_mark: |
| -  on_throw              | :heavy_check_mark: |
| **Fields**               |                    |
| -  field header          | :heavy_check_mark: |
| -  input_paths           | :heavy_check_mark: |
| -  possible_paths        | :heavy_check_mark: |
| -  const                 | :heavy_check_mark: |
| -  from_type             | :heavy_check_mark: |
| -  or_else               | :heavy_check_mark: |
| -  on_throw              | :heavy_check_mark: |
| -  many                  | :heavy_check_mark: |
| **Postprocessing**       |                    |
| -  input_paths           | :heavy_check_mark: |
| -  output_paths          | :heavy_check_mark: |
| -  function              | :heavy_check_mark: |
| -  or_else               | :heavy_check_mark: |
| -  on_throw              | :heavy_check_mark: |

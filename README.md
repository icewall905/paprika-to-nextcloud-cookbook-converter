# Paprika to Nextcloud Cookbook Converter

This repository contains a Python script to convert Paprika export files into a format compatible with [Nextcloud Cookbook](https://apps.nextcloud.com/apps/cookbook).

## Supported Export Types

The script supports two export types from Paprika:

* **Individual Recipe Files**: Files ending with .paprikarecipe (each is a gzip-compressed JSON file)
* **Bulk Export File**: A single file (typically with extension .paprikarecipes) that is a zip archive containing multiple .paprikarecipe files



### Before you begin, please export the .paprikarecipe file from the app on your phone or computer.

## Usage

1. Clone this repository:
   ```bash

   git clone https://github.com/icewall905/paprika-to-nextcloud-cookbook-converter.git
   cd paprika-to-nextcloud-cookbook-converter/

2. Run the conversion script:
      ```bash

   python3 convert_paprika_to_nextcloud.py export.paprikarecipes output_folder

To complete the import, simply copy the resulting folder structure into your recipe folder in Nextcloud and let it scan.

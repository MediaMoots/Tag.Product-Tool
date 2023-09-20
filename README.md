# Tag.Product Tool
The final piece of the puzzle for standalone armor, item sorting, and more.

## Usage
### Setup
1. Download the latest Tag.Product-Tool release.
2. Download https://github.com/ArchLeaders/byml_to_yaml/releases/tag/1.0.0-rc1
3. Dump your `zs.dict`
4. Extract all three files (`TagProductTool.exe`, `byml-to-yaml.exe`, `zs.zsdic`) into the same folder.

### GUI Usage
1. Either run `TagProductTool.exe`, or drag a byml, byml.zs or json on it.
2. Select the output folder.

### CMD Usage
`TagProductTool.exe INPUT_FILE OUTPUT_PATH`

# Notes
## Possible Issues
- Using this tool will blank the RankTable value in the file, however, it does not seem to affect anything.
## Other
- The release executable was made with pyinstaller.
#### Special Thanks
- https://github.com/TotkMods/oead
- https://github.com/ArchLeaders/byml_to_yaml
- https://pypi.org/project/pyinstaller/

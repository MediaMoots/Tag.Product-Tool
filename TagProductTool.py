import os
import sys
import json
import yaml
import oead
import time
import string
import base64
import zstandard
import subprocess
from bitarray import bitarray
from tkinter import filedialog as fd

## pyinstaller TagProductTool.py --onefile

## Program Functions
def get_script_path():
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(os.path.abspath(__file__)) 
    return application_path
        
def initialize_needed_file_paths():
    
    # Input File
    if len(sys.argv) > 1:
        input_file_path = sys.argv[1]
    else:
        input_file_path = fd.askopenfilename(title="Open file", filetypes =[('Tag Product', ['*.rstbl.byml.zs', '*.rstbl.byml', '*.json'])])
        
    if input_file_path == '':
        sys.exit()

    ## Output directory   
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
    else:
        output_path = fd.askdirectory(title="Output folder...")
        
    if output_path == '':
        sys.exit()
 
    return input_file_path, output_path

def get_file_bytes(input_file_path):
    
    # Debug
    print(f'INFO: Getting file from: {input_file_path}')
    
    with open(input_file_path, "rb") as input_f:
        # Decompress zs to bytes
        input_file_bytes = input_f.read()
    input_f.close()
    return input_file_bytes
def save_file_bytes(output_file_path, file_bytes):
    
    # Debug
    print(f'INFO: Saving file to: {output_file_path}')
    
    with open(output_file_path, 'wb') as output_f:
        output_f.write(file_bytes) 
def save_file_str(output_file_path, file_str):
    
    # Debug
    print(f'INFO: Saving file to: {output_file_path}')
    
    with open(output_file_path, 'w') as output_f:
        output_f.write(file_str)       
          
def proccess_input_file(input_file_path, output_path):
    
    # Debug
    print('INFO: Processing Input File.')
    
    input_file_name = os.path.basename(input_file_path)
    input_file_bytes = get_file_bytes(input_file_path)
    zs_dict = load_zs_dict()
    
    # If is json, convert to compressed byml
    if input_file_name.endswith('.json'):
        
        # Convert json to yml
        yml_file_path, yml_file_str = json_to_yml_str(input_file_name, input_file_bytes, output_path)
        save_file_str(yml_file_path, yml_file_str)
        
        # Convert yml to byml
        byml_file_path, byml_file_bytes = yml_to_byml_bytes(yml_file_path)
        
        # Compress byml
        compressed_file_bytes = compress_zs(byml_file_bytes, zs_dict)
        byml_zs_file_path = byml_file_path + '.zs'
        save_file_bytes(byml_zs_file_path, compressed_file_bytes)
        
        # Cleanup workspace
        os.remove(yml_file_path)
        os.remove(byml_file_path)
        
        # Debug
        print('INFO: Conversion Complete.')
        time.sleep(3)
        return
    
    # If is compressed, decompress it
    if input_file_name.endswith('.zs'):
        
        # Decompress byml
        input_file_bytes = decompress_zs(input_file_bytes, zs_dict)

    # If is byml, convert to json
    if input_file_name.endswith('.byml') or input_file_name.endswith('.byml.zs'):
        
        # Convert byml to json
        json_file_path, json_file_bytes = byml_to_json_bytes(input_file_name, input_file_bytes, output_path)
        save_file_bytes(json_file_path, json_file_bytes)
        
        # Debug
        print('INFO: Conversion Complete.')
        time.sleep(3)
        return
        

## ZS Functions 
def load_zs_dict():
    
    # Debug
    print('INFO: Loading zs dict.')
    
    # Init path
    zsdic_path = os.path.join(get_script_path(), 'zs.zsdic')

    # Check if zs dict exists
    if not os.path.isfile(zsdic_path):
        print(f'ERROR: No ZS Dict found. Searching in path: {zsdic_path}')
        time.sleep(3)
        sys.exit()

    # Load the dict
    with open(zsdic_path, "rb") as zsdic_f:
        zs_dict = zstandard.ZstdCompressionDict(zsdic_f.read())
    zsdic_f.close()
    
    return zs_dict
def compress_zs(input_bytes, zs_dict):
    
    # Debug
    print('INFO: Compressing file with zs.')
    
    zstd_compressor = zstandard.ZstdCompressor(dict_data=zs_dict, level=22)
    return zstd_compressor.compress(input_bytes)
def decompress_zs(input_bytes, zs_dict):
    
    # Debug
    print('INFO: Decompressing file with zs.')
    
    zstd_decompressor = zstandard.ZstdDecompressor(dict_data=zs_dict)
    return zstd_decompressor.decompress(input_bytes)

## BYML TO JSON
def byml_to_json_bytes(file_name, byml_file_bytes, output_path):
    
    # Debug
    print('INFO: Converting byml to json.')
    
    # Parse byml with oead
    byml_data = oead.byml.from_binary(byml_file_bytes)

    # Get Path list
    path_list = byml_data['PathList']
    path_list_count = len(path_list)
    
    # Get Tag list
    tag_list = list(byml_data['TagList'])
    tag_list_count = len(tag_list)

    # Get Bit Table
    bit_table_bytes = byml_data['BitTable']
    
    # Valid Check
    if bit_table_bytes == '':
        print('ERROR: Bit Table is empty!')
        time.sleep(3)
        sys.exit()
    
    # Get Bit Table
    rank_table = byml_data['RankTable']

    # Get bit array from bytes
    bit_table_bits = bitarray()
    bit_table_bits.frombytes(bit_table_bytes)
    bit_table_bits.bytereverse() # Reverse the order
    bit_array_count = len(bit_table_bits)
    
    # Debug
    print(f'INFO: Parsed Bits Count: {bit_array_count}')

    # Get Actors and Tags
    actor_tag_data_map = {}
    for path_list_idx in range(0, path_list_count // 3):
        actor_path = f'{path_list[path_list_idx * 3 + 0]}|{path_list[path_list_idx * 3 + 1]}|{path_list[path_list_idx * 3 + 2]}'
        actor_tag_list = []
        for tag_list_idx in range(0, tag_list_count):
            if bit_table_bits[path_list_idx * tag_list_count + tag_list_idx]:
                actor_tag_list.append(tag_list[tag_list_idx])

        # Save actor tags
        actor_tag_data_map[actor_path] = actor_tag_list

    # Make json data
    json_data = {}
    json_data['FileName'] = file_name
    json_data['ActorTagData'] = actor_tag_data_map
    json_data['CachedTagList'] = tag_list
    json_data['CachedRankTable'] = bytes(rank_table).hex() if rank_table != '' else '' # Save the ranktable for future use

    # Return dumped data
    json_output_path = os.path.join(output_path, f'{file_name}.json')
    json_bytes = json.dumps(json_data, indent=2).encode()
    return json_output_path, json_bytes

## JSON TO YML
def json_to_yml_str(file_name, json_file_data, output_path):
    
    # Debug
    print('INFO: Converting json to yml.')
    
    # Helper Function
    def create_path_list_from_json(actor_tag_data):
        path_list = []
        
        for element in actor_tag_data.keys():
            path_block = element.split('|')
            path_list += path_block
        
        return path_list

    # Load json data
    json_data = json.loads(json_file_data)
    
    # Parse data
    actor_tag_data = json_data['ActorTagData']
    
    # Sort Actor Tags
    # Define a custom translation table to assign weights to characters
    custom_translation = str.maketrans('', '', string.punctuation + string.whitespace)

    # Define a custom sorting key function
    def custom_sort_key(item):
        key = item[0]
        # Check if '|' exists in the key
        if '|' in key:
            # Split the key into parts before and after the '|'
            parts = key.split('|')
            # Return a tuple with the '|' character as the first element
            # and the rest of the string as the second element for sorting
            return (parts[0], parts[1])
        else:
            # If '|' doesn't exist in the key, treat it as a regular string
            return (key,)
    
    actor_tag_data = dict(sorted(actor_tag_data.items(), key=custom_sort_key))
    
    # Get Tag list
    cached_tag_list = json_data['CachedTagList']
    cached_tag_list.sort()
    
    # Get Rank Table
    cached_rank_table = json_data['CachedRankTable']
    
    # Get formatted path list  
    path_list = create_path_list_from_json(actor_tag_data)

    # Create bit table
    bit_table_bits = []
    index = -1
    for actor_tag in actor_tag_data:
        index += 1
        for tag in cached_tag_list:
            bit = 0
            if tag in actor_tag_data[actor_tag]:
                bit = 1
            bit_table_bits.append(bit)
    
    # Bits to Bytes
    bit_table_bit_array = bitarray(bit_table_bits)
    bit_table_bit_array.bytereverse() # Reverse the order
    bit_table_bytes = bit_table_bit_array.tobytes()

    # Make yml data
    yml_data_dict = {}
    yml_data_dict['BitTable'] = bit_table_bytes
    yml_data_dict['PathList'] = path_list
    # yml_data_dict['RankTable'] = bytes.fromhex(cached_rank_table)
    yml_data_dict['RankTable'] = '' # RankTable dosen't seem to be used anywhere, and including it makes the game be unable to start, so blanking it for now
    yml_data_dict['TagList'] = cached_tag_list
    
    # Prepare yml dumper
    class YamlDumper(yaml.Dumper):
        def increase_indent(self, flow=False, indentless=False):
            return super(YamlDumper, self).increase_indent(flow, False)

    # Custom dumper to output !!binary and binary data in one line
    def binary_representer(dumper, data):
        encoded_data = base64.b64encode(data).decode('utf-8')
        return dumper.represent_scalar('tag:yaml.org,2002:binary', encoded_data, style='|')

    # Register the custom representer
    yaml.add_representer(bytes, binary_representer)
    
    # Make yml str
    yml_output_path = os.path.join(output_path, file_name.replace('.json', '.yml'))
    yml_str = yaml.dump(yml_data_dict, Dumper=YamlDumper)
    return yml_output_path, yml_str

## YML TO BYML
def yml_to_byml_bytes(yml_file_path):
    
    # Debug
    print('INFO: Converting yml to byml.')
    
    # Get tool path
    byml_tool_path = os.path.join(get_script_path(), 'byml-to-yaml.exe')
    
    # Check if zs dict exists
    if not os.path.isfile(byml_tool_path):
        print(f'ERROR: No byml-to-yaml.exe found. Searching in path: {byml_tool_path}')
        time.sleep(3)
        sys.exit()
    
    # Convert yml to byml using Arch's tool https://github.com/ArchLeaders/byml_to_yaml
    byml_file_path = yml_file_path.replace('.zs.yml', '')
    subprocess.check_call([byml_tool_path, 'to-byml', yml_file_path, '-o', byml_file_path])
    
    # Load converted byml file
    byml_file_bytes = get_file_bytes(byml_file_path)
    
    return byml_file_path, byml_file_bytes

# Program Main
if __name__ == '__main__':
    input_file_path, output_path = initialize_needed_file_paths()
    proccess_input_file(input_file_path, output_path)
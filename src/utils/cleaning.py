import os
import time
import shutil
from utils.reporter import get_jar_file

def clear_old_assets_and_cache(original_cwd, current_session_id):

    '''
    It navigates to the "assets" and "cache-dir" directory, iterates through its contents, and removes any files or folders that are not in the list_to_retain and are older than a specified time limit (11 minutes in this case). The function then returns to the original working directory.
    
    Param
    -------
    original_cwd: str
    current_session_id: str

    Returns
    -------
    none
    
    '''
    def clear_directory(directory, list_to_retain):
        current_time = time.time()
        limit_11_min = 660

        for item in os.listdir(directory):
            if item not in list_to_retain:
                item_location = os.path.join(os.getcwd(), item)
                item_time = os.stat(item_location).st_mtime

                if os.path.isdir(item):
                    if(item_time < current_time - limit_11_min):
                        shutil.rmtree(item_location)
                elif os.path.isfile(item):
                    os.remove(item)

    jar_file = get_jar_file()

    cwd = os.getcwd()
    assets_directory = os.path.join(cwd, "assets/")
    os.chdir(assets_directory)

    # Clear assets directory
    assets_to_retain = [
    'favicons',
    'icons',
    'placeholders',
    'style.css',
    'parsing_illustration.jpeg',
    'parrot.svg',
    'parrot.png',
    'cytoscape-legend.jpg',
    'circular_tree-legend.jpg',
    'bubbles.svg',
    'arial.ttf',
    'arial.pkl',
    'arial.cw127.pkl',
    'LORA-scheme-01.jpg',
    'TOC.jpg',
    'manual_images',
    'data'
    ] + [jar_file]

    clear_directory(assets_directory, assets_to_retain)

    # Clear cache directory
    os.chdir(original_cwd)
    cache_directory = os.path.join(cwd, "cache-dir/")
    os.chdir(cache_directory)

    cache_to_retain = [current_session_id]

    clear_directory(cache_directory, cache_to_retain)

    os.chdir(original_cwd)
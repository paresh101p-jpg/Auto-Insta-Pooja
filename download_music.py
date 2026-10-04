import urllib.request
import os
import shutil

url = 'https://raw.githubusercontent.com/rafaelreis-hotmart/Audio-Sample-files/master/sample.mp3'
dest_dir = 'music'

if not os.path.exists(dest_dir):
    os.makedirs(dest_dir)

base_file = os.path.join(dest_dir, 'base.mp3')
print('Downloading sample music...')
try:
    urllib.request.urlretrieve(url, base_file)
    print('Download complete.')
    
    print('Generating 50 copies...')
    for i in range(1, 51):
        shutil.copy(base_file, os.path.join(dest_dir, f'music_{i}.mp3'))
    print('Successfully created 50 music files in the music folder!')
    os.remove(base_file)
except Exception as e:
    print(f'Error: {e}')

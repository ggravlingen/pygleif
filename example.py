from pygleif.const import URL_LEVEL2_CONCAT_FILES
import arrow
import wget
from zipfile import ZipFile
import os
import xml.etree.ElementTree as ET

debug = 1

today = arrow.now().format('YYYYMMDD')
level_2_url = URL_LEVEL2_CONCAT_FILES.replace('%date%', today)
save_name = 'file'+today+'.zip'
extracted_file = today+'-gleif-concatenated-file-rr.xml'

if debug == 0:

    #  Make sure there is no file already
    os.remove(save_name)

    #  Download file
    wget.download(level_2_url, save_name)

    # opening the zip file in READ mode
    with ZipFile(save_name, 'r') as zip:
        print('Extracting all the files now...')
        zip.extractall()
        os.remove(save_name)


tree = ET.parse(extracted_file)
root = tree.getroot()

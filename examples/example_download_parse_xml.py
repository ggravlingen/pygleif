# Hack to allow relative import above top level package
import os
import sys

folder = os.path.dirname(os.path.abspath(__file__))  # noqa
sys.path.insert(0, os.path.normpath("%s/.." % folder))  # noqa

import os
import xml.etree.ElementTree as ET
from zipfile import ZipFile

import arrow
import wget

from pygleif import GLEIFParseRelationshipRecord
from pygleif.const import URL_LEVEL2_CONCAT_FILES

debug = 1

today = arrow.now().format("YYYYMMDD")
level_2_url = URL_LEVEL2_CONCAT_FILES.replace("%date%", today)
save_name = "file" + today + ".zip"
extracted_file = today + "-gleif-concatenated-file-rr.xml"

if debug == 0:

    #  Make sure there is no file already
    os.remove(save_name)

    #  Download file
    wget.download(level_2_url, save_name)

    # opening the zip file in READ mode
    with ZipFile(save_name, "r") as zip:
        print("Extracting all the files now...")
        zip.extractall()
        os.remove(save_name)

tree = ET.parse(extracted_file)
root = tree.getroot()

#  for i in range(len(root[1])):
for i in range(5):
    xml_data = ET.tostring(root[1][i], encoding="utf8", method="xml")
    data = GLEIFParseRelationshipRecord(xml_data)

    relationship_type = data.raw.Relationship.RelationshipType.text
    parent = data.raw.Relationship.StartNode.NodeID.text
    child = data.raw.Relationship.EndNode.NodeID.text

    print("Relationship type: " + relationship_type)
    print("Parent: " + parent)
    print("Child: " + child)
    print("")

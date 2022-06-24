[![PyPI version](https://badge.fury.io/py/pygleif.svg)](https://badge.fury.io/py/pygleif)

This library queries the API of GLEIF.org to return data about a specific entity company. The result is typed using `Pydantic`.

It can also parse the XML-files provided by GLEIF. It is also possible to search for organisation id to find LEI codes and also to get child notes for a specific LEI code.

Usage if you query the API:

```
from pygleif import GLEIF

data = GLEIF('8RS0AKOLN987042F2V04')
print(data.registration.initial_registration_date)
```

## 1. How to use

Usage if you use the XML files:

```
from pygleif import GLEIFParseRelationshipRecord

# XML is the content (converted to text) of a <RelationshipRecord>
data = GLEIFParseRelationshipRecord(XML)
print(data.raw.Relationship.StartNode.NodeID.text) #  Uses BeautifulSoup to convert to object

```

There are also some examples available in the sources' example folder.

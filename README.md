[![Coverage Status](https://coveralls.io/repos/github/ggravlingen/pygleif/badge.svg)](https://coveralls.io/github/ggravlingen/pygleif)
[![PyPI version](https://badge.fury.io/py/pygleif.svg)](https://badge.fury.io/py/pygleif)
[![Build Status](https://travis-ci.org/ggravlingen/pygleif.svg?branch=master)](https://travis-ci.org/ggravlingen/pygleif)

This is a Python class that queries the API of GLEIF.org to return data about a specific entity (corporation.) It can also parse the XML-files provided by GLEIF.

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
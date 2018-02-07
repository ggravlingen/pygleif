[![Coverage Status](https://coveralls.io/repos/github/ggravlingen/pygleif/badge.svg)](https://coveralls.io/github/ggravlingen/pygleif)

This is a Python class that queries the API of GLEIF.org to return data about a specific entity (corporation.)

Usage:
```
import pygleif

data = GLEIF('8RS0AKOLN987042F2V04')
print(data.registration.initial_registration_date)
```

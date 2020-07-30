# wificonnection

## Objective

wificonnection is a jupyter notebook extension enabling users connect the Raspberry Pi to wifi.
The wifi button gets displayed in the notebook toolbar. The jupyter notebook IDE must be launched on it's localhost and 
users can access this web server through host web browser like as chrome.

## Installation

You can currently install this directly in Raspberry pi from git:

```
pip3 install git+https://git.luxrobo.net/modi-ai/wificonnection.git --user
jupyter serverextension enable --py wificonnection --user
jupyter nbextension install --py wificonnection --user
```

To enable this extension for all notebooks:

```
jupyter nbextension enable --py wificonnection --user
```
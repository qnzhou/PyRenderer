import json
import numpy as np
import sys

def remove_unicode(config):
    """ Convert every string in config into utf-8 format.
    """
    # This check is necessary because awkward python 3 and 2 compatibility.
    if sys.version_info > (2, 8):
        return config;
    #raise DeprecationWarning("This method is out of date.");
    if isinstance(config, dict):
        return {remove_unicode(key): remove_unicode(value) for key, value in config.items()}
    elif isinstance(config, list):
        return [remove_unicode(element) for element in config]
    elif isinstance(config, unicode):
        return config.encode('utf-8')
    else:
        return config

class NumpyAwareJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist();
        else:
            return json.JSONEncoder.default(self, obj)

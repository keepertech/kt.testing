# This is a namespace package.

import pkgutil

try:
    import pkg_resources
except ImportError:
    __path__ = pkgutil.extend_path(__path__, __name__)
else:
    pkg_resources.declare_namespace(__name__)
    # This breaks when building a debian package; no idea why.
    # del pkg_resources

# This breaks when building a debian package; no idea why.
# del pkgutil

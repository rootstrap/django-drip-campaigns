from pylint.utils import utils


class PylintIgnorePaths:
    def __init__(self, *paths):
        self.paths = paths
        self.original_expand_modules = utils.expand_modules
        utils.expand_modules = self.patched_expand

    def patched_expand(self, *args, **kwargs):
        result, errors = self.original_expand_modules(*args, **kwargs)

        def keep_item(item):
            if any(1 for path in self.paths if item['path'].startswith(path)):
                return False

            return True

        result = list(filter(keep_item, result))

        return result, errors

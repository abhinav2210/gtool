from gtool.core.types.output import TreeOutput
from gtool.core.filewalker import StructureFactory
import json


class Json(TreeOutput):

    def __output__(self, projectstructure, output=None):

        _jsonoutput = super(Json, self).__output__(projectstructure)

        #_jsonoutput = self.outputprocessor(_output)

        if output is None:
            return _jsonoutput
        else:
            with open(output, mode='w') as f:
                f.write(_jsonoutput)
                f.close()
            return True  # TODO inconsistent return json object vs true

    def filter(self, obj):
        return super(Json, self).filter(obj)

    def outputprocessor(self, projectstructure):

        def _sub(tree):
            if isinstance(tree, list):
                return [_sub(item) for item in tree]
            elif isinstance(tree, dict):
                return {k: _sub(v) for k, v in tree.items()}
            else:
                return tree.asdict(filterfunction=self.filter)

        _tree = _sub(projectstructure)
        return json.dumps(_tree, sort_keys=True, indent=4)


def load():
    return Json
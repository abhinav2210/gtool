from gtool.core.types.output import GridOutput


class Excel(GridOutput):

    def __output__(self, projectstructure):
        # TODO call Super and use results
        x = projectstructure.dataasobject
        for i in x:
            print(i)

def load():
    return Excel
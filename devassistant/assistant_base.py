import argparse

from devassistant import settings

class AssistantBase(object):
    # some of these values may be overriden by prepare
    # (e.g. needs_sudo, if prepare finds out that required package is not present)
    name = 'base'
    verbose_name = 'Base'
    needs_sudo = False

    args = []
    usage_string_fmt = 'Usage of {verbose_name}:'

    def get_argument_parser(self):
        parser = argparse.ArgumentParser(usage=self.usage_string_fmt.format(verbose_name=self.verbose_name))
        for arg in self.args:
            if not settings.SUBSETUP_STRING in arg.flags:
                arg.add_argument_to(parser)

        subparsers = parser.add_subparsers()
        for subs_cls in self.get_subsetup_classes():
            subs_cls().add_subparser_to(subparsers)

        return parser

    def add_subparsers_to(self, parser):
        p = parser.add_parser(self.name)
        for arg in self.args:
            if not settings.SUBSETUP_STRING in arg.flags:
                arg.add_argument_to(p)

        if not self.is_leaf:
            subparsers = p.add_subparsers()
            for subs_cls in self.get_subsetup_classes():
                subs_cls().add_subparser_to(subparsers)

    def get_subsetup_classes(self):
        subs_cls_list = []

        for arg in self.args:
            if settings.SUBSETUP_STRING in arg.flags:
                for k, v in arg.subsetups.items():
                    # accept both classes or their names as str
                    if isinstance(v, str):
                        subs_cls_list.append(eval(v))
                    else:
                        subs_cls_list.append(v)
        return subs_cls_list

    def errors(self, **kwargs):
        """Checks whether the command is doable, also checking the arguments
        passed as kwargs.
        Returns:
            List of errors as strings (empty list with no errors.
        """
        return []

    def prepare(self, **kwargs):
        """Prepares the object/gathers info needed to run (e.g. sets needs_sudo).
        """
        pass

    def run(self, **kwargs):
        """Actually carries out the command represented by this object.
        """
        pass
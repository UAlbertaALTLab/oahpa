from .local_conf import LLL1
import importlib

oahpa_module = importlib.import_module(LLL1 + "_oahpa")

from django.core.management.base import BaseCommand

import sys


# # #
#
#  Command class
#
# # #


def findmissing(tfilter=False, count=0):
    Form = oahpa_module.drill.models.Form
    from django.db.models import Count

    missing = (
        Form.objects.filter()
        .annotate(fc=Count("feedback"))
        .filter(fc=0)
        .values("word__lemma", "fullform", "tag__string")
    )

    for m in missing.iterator():
        s = "%(word__lemma)s\t%(fullform)s\t%(tag__string)s" % m
        print(s.encode("utf-8"), file=sys.stdout)


class Command(BaseCommand):
    args = "--tagelement"
    help = """
	Strips tags of an element and then merges them all.
	"""

    def add_arguments(self, parser):
        parser.add_argument(
            "-t",
            "--tagelement",
            dest="tagelement",
            default=False,
            help="Tag element to search for",
        )

        parser.add_argument(
            "-d",
            "--dryrun",
            dest="dryrun",
            default="True",
            help="List tags matching element instead of merging",
        )

        # TODO: question iterations count

    def handle(self, *args, **options):

        tag_element = options["tagelement"]
        dry_run = options["dryrun"]

        findmissing()

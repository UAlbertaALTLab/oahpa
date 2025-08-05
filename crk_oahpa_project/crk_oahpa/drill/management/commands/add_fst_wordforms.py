"""
Like add_static_wordforms, but uses the FST directly instead.
First addition of new code in 2025.
"""

import importlib
from collections import defaultdict

from django.core.management.base import BaseCommand
import hfst

from .local_conf import LLL1

oahpa_module = importlib.import_module(LLL1 + "_oahpa")
Form = oahpa_module.drill.models.Form
Word = oahpa_module.drill.models.Word
Tag = oahpa_module.drill.models.Tag


def install_file(filename, pos):

    # Generate a dictionary from the file, with all the forms by tag (without plus)
    # That is : words_to_install : dict[lemma, dict[tag, form]]
    # where the tag is actually all the rest, it should instead be the generating string for LEMMAs but I don't think this code was yet updated.
    # So we'll assume something around that.

    words_to_install = defaultdict(list)
    with open(filename, "r") as F:
        for l in F.readlines():
            _tag, _, form = l.strip().partition("\t")
            lemma, _, tag = _tag.partition("+")

            if lemma not in words_to_install:
                words_to_install[lemma] = {}

            if tag not in words_to_install[lemma]:
                words_to_install[lemma][tag] = []

            words_to_install[lemma][tag].append(form)

    # Now for each lemma and set of tags, we get the output of the generator fst (form)
    for lemma, forms in words_to_install.items():
        # forms is a dictionary of outputs, by tags used (which should be the tags in the questions)
        print("lemma: ", lemma)
        # for all words already around with this lemma and pos
        ws = Word.objects.filter(lemma=lemma, pos=pos)
        try:
            # There should be at least one
            w = ws[0]
            for tag, wfs in forms.items():
                # tag is the analysis template
                # wfs is wordforms
                # Get all the forms that match (imported from the XML I assume)
                fs = Form.objects.filter(word__lemma=lemma, tag__string=tag)
                # Remove them
                fs.delete()
                print("  ", tag)
                # Create the tag because these should be unique
                t, _c = Tag.objects.get_or_create(string=tag)
                if _c:
                    t.save()
                for new_form in wfs:
                    print("    ", new_form)
                    new = Form.objects.create(
                        word=w,
                        tag=t,
                        fullform=new_form,
                    )
                    new.save()
        except IndexError:
            print("error:", IndexError)


class Command(BaseCommand):
    args = "--tagelement"
    help = """
    Strips tags of an element and then merges them all.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "-f",
            "--filename",
            dest="filename",
            default=False,
            help="Static file to read from",
        )
        parser.add_argument(
            "-p", "--pos", dest="pos", default=False, help="Part of speech"
        )

    def handle(self, *args, **options):
        import sys, os

        filename = options["filename"]
        pos = options["pos"]

        install_file(filename=filename, pos=pos)

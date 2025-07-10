#!/usr/bin/env python
# -*- coding: utf-8 -*-
from local_conf import LLL1
import importlib
oahpa_module = importlib.import_module(LLL1+'_oahpa')

import settings
from os import environ
import os, sys
print(" * Correcting paths")
cur_path = os.getcwd()
parent_path = '/' + '/'.join([a for a in cur_path.split('/') if a][0:-1]) + '/'
sys.path.insert(0, parent_path)
environ['DJANGO_SETTINGS_MODULE'] = LLL1+'_oahpa.settings'

settings.DEBUG = False

from drill.models import *
import sys
from ling import Paradigm
from words_install import Words
from extra_install import Extra
from feedback_install import Feedback_install
from questions_install import Questions
from sahka_install import Sahka  # added by Heli

# TODO: option for oa="yes" only, for crk_
# ota lemma jos on name="oahpa"
# jos on lemma, niin ota käännös jos on oa="yes"

from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Help text goes here'

    def add_arguments(self, parser):
        parser.add_argument("-a", "--append-words", dest="append",
                      action="store_true", default=False,
                      help="Add wordforms to words without deleting existing wordforms")
        parser.add_argument("-b", "--db", dest="add_db",
                      action="store_true", default=False,
                      help="Used for adding tag infoformation to database")
        parser.add_argument("-c", "--comments", dest="commentfile",
                      help="XML-file for comments")
        parser.add_argument("-d", "--delete", dest="delete",
                      action="store_true", default=False,
                      help="delete words that do not appear in the lexicon file of certain pos")
        parser.add_argument("-e", "--feedbackfile", dest="feedbackfile",
                      help="XML-file for feedback")
        parser.add_argument("-f", "--file", dest="infile",
                      help="lexicon file name")
        parser.add_argument("-g", "--grammarfile", dest="grammarfile",
                      help="XML-file for grammar defaults for questions")
        parser.add_argument("-i", "--links", dest="linkfile",
                      help="Text file for grammarlinks")
        parser.add_argument("-s", "--sem", dest="semtypefile",
                      help="XML-file semantic subclasses")
        parser.add_argument("-t", "--tagfile", dest="tagfile",
                      help="List of tags and tagsets")
        parser.add_argument("-m", "--messagefile", dest="messagefile",
                  help="XML-file for feedback messages")
        parser.add_argument("-q", "--questionfile", dest="questionfile",
                  help="XML-file that contains questions")
        parser.add_argument("-k", "--sahka", dest="sahkafile",
                  help="XML-file for Dialogues"),  # added
        parser.add_argument("-w", "--wid", dest="wordid",
                      help="delete word using id or lemma")
        parser.add_argument("-p", "--pos", dest="pos",
                      help="pos of the deleted word")
        parser.add_argument("-r", "--paradigmfile", dest="paradigmfile",
                      help="Generate paradigms")

    def handle(self, **options):
        main(options)

def main(options):

    linginfo = Paradigm()
    words = Words()
    extra = Extra()
    sahka = Sahka() # added by Heli
    feedback = Feedback_install()
    questions = Questions()

    if options['tagfile']:
        linginfo.handle_tags(options['tagfile'], options['add_db'])

    if options['paradigmfile']:
        linginfo.read_paradigms(options['paradigmfile'], options['tagfile'], options['add_db'])

    if options['wordid']:
        words.delete_word(options['wordid'],options.['pos'])
        sys.exit()

    if options['questionfile'] and options['grammarfile']:
        questions.read_questions(options['questionfile'],options['grammarfile'])
        sys.exit()

    if options['semtypefile']:
        extra.read_semtypes(options['semtypefile'])
        sys.exit()

    if options['messagefile']:
        feedback.read_messages(options['messagefile'])
        sys.exit()

    if options['sahkafile']:
        sahka.read_dialogue(options['sahkafile'])
        sys.exit()

    if options['feedbackfile'] and options['infile']:
        feedback.read_feedback(options['feedbackfile'],options['infile'])
        sys.exit()

    if options['linkfile']:
        extra.read_address(options['linkfile'])
        sys.exit()

    if options['infile']:

        if options['append']:
            append_only = True
        else:
            append_only = False

        words.install_lexicon(infile=options['infile'],
                                linginfo=linginfo,
                                delete=options['delete'],
                                paradigmfile=options['paradigmfile'],
                                append_only=append_only)
        sys.exit()


if __name__ == "__main__":
    main(opts=False)
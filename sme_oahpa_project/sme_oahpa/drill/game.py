# -*- coding: utf-8 -*-
from local_conf import LLL1
import importlib
oahpa_module = importlib.import_module(LLL1+'_oahpa')

from models import *
from forms import *

switch_language_code = oahpa_module.conf.tools.switch_language_code

from django.db.models import Q, Count
from django.http import HttpResponse, Http404
from django.shortcuts import get_list_or_404, render_to_response
from django.core.exceptions import ObjectDoesNotExist
from random import randint

import logging
import os
import re
import itertools

settings = oahpa_module.settings
LLL1 = settings.LLL1

from random import choice
from .forms import PRONOUNS_LIST


try:
	LOOKUP_TOOL = settings.LOOKUP_TOOL
except:
	LOOKUP_TOOL = 'lookup'

try:
    HFST_LOOKUP = settings.HFST_LOOKUP
except:
    HFST_LOOKUP = "/usr/bin/hfst-lookup"

try:
	FST_DIRECTORY = settings.FST_DIRECTORY
except:
	FST_DIRECTORY = False

try:
	DEFAULT_DIALECT = settings.DEFAULT_DIALECT
except:
	DEFAULT_DIALECT = None


# FST_DIRECTORY = '/opt/smi/sme/bin' #Just testing. Hardcoded here because it looks like looking it up in settings.py failed
# LOOKUP_TOOL = '/usr/local/bin/lookup'


def parse_tag(tag):
	""" Iterate through a tag string by chunks, and check for tag sets
	and tag names. Return the reassembled tag on success. """

	def fill_out(tags):
		from itertools import product

		def make_list(item):
			if type(item) == list:
				return item
			else:
				return [item]

		return list(product(*map(make_list, tags)))

	tag_string = []
	for item in tag.split('+'):
		if Tagname.objects.filter(tagname=item).count() > 0:
			tag_string.append(item)
		elif Tagset.objects.filter(tagset=item).count() > 0:
			tagnames = Tagname.objects.filter(tagset__tagset=item)
			tag_string.append([t.tagname for t in tagnames])

	if len(tag_string) > 0:
		return ['+'.join(item).replace('++', '+') for item in fill_out(tag_string)]
	else:
		return False

class Info:
	pass

class Game(object):
	def __init__(self, settings):
		self.query_set = False
		self.lemmas_selected = []
		self.form_list = []
		self.count = ""
		self.score = ""
		self.comment = ""
		self.settings = settings
		self.all_correct = ""
		self.show_correct = 0
		self.num_fields = 6
		self.global_targets = {}
		# .has_key deprecated, is there a way to use in with this?
		if not self.settings.has_key('gametype'):
			self.settings['gametype'] = "bare"

		if self.settings['gametype'] == "bare" and self.settings.has_key('pron_type') and self.settings['pron_type'] in ['Rel', 'Dem']:
			self.num_fields = 4


		if self.settings['gametype'] == "bare" and self.settings['pos'] == 'A' and self.settings.has_key('book'):
			if self.settings['book'] == "d1":
				self.num_fields = 4

		if self.settings.has_key('semtype'):
			if self.settings['semtype'] in ('all','All'):  # upper- or lowercase
				# self.settings['semtype'] = self.settings['allsem']
				self.settings['semtype'] = 'all'
			else:
				semtype = self.settings['semtype'][:]
				self.settings['semtype'] = []
				self.settings['semtype'].append(semtype)

	def new_game(self):
		from qagame import QAGame
		self.form_list = []
		word_ids = []
		q_ids = []
		i = 1
		num = 0
		# if self.settings['pos'] == 'Pron':
			# print 'omg'
			# for i in range(self.num_fields):
				# db_info = {}
				# db_info['userans'] = ""
				# db_info['correct'] = ""

				# errormsg = self.get_db_info(db_info)

				# form, word_id = self.create_form(db_info, i, 0)
				# print form
		# else:

		# Use this to make sure that pronouns don't have repeated
		# pronouns
		existing_tags = []

		# Can this be changed? Self.create_form should go without fail.
		tries = 0
		maxtries = 40

		while i < self.num_fields and len(self.form_list) < 5 and tries < maxtries:
			tries += 1
			db_info = {}
			db_info['userans'] = ""
			db_info['correct'] = ""

			errormsg = self.get_db_info(db_info)

			if errormsg and errormsg == "error":
				# i = i+1
				continue
				# raise Http404(errormsg)

			form = None

			try:
				form, word_id = self.create_form(db_info, i, 0)
			except Http404, e:
				raise e
			except ObjectDoesNotExist:
				continue
			possible_max = db_info.get('possible_question_count', 50)
			print possible_max

			# Do not generate same question twice for Morfa-S
			if word_id:
				num = num + 1
				if word_id in set(word_ids):
					#and not (self.settings['gametype'] == "bare"
					# and self.settings['pron_type'] in
					# ['Rel','Dem']): # If there are less than 5
					# different lemmas to choose from then this causes
					# a "No questions were able to be generated."
					continue
				else: word_ids.append(word_id)

			# The following if-clause has been added to avoid repeated
			# MorfaC questions in one set, however, if there are less
			# than 5 possible questions for a particular query, we
			# ignore this, and repeats are fine.
			if isinstance(self, QAGame):
				if db_info.has_key('question_id'):
					q_id = db_info['question_id']
					if possible_max > 5:
						if q_id in set(q_ids):
							continue
					q_ids.append(q_id)
			self.form_list.append(form)
			i = i+1

		# print len(self.form_list)
		if tries == maxtries:
			raise Http404('No questions were able to be generated.')
		if not self.form_list:
			# No questions found, so the quiz_id must have been bad.
			raise Http404('Invalid quiz id.')

	def search_info(self, reObj, string, value, words, t_type):
		matchObj = reObj.search(string)
		if matchObj:
			syntax = matchObj.expand(r'\g<syntaxString>')
			if not words.has_key(syntax):
				words[syntax] = {}

			words[syntax][t_type] = value
		return words


	def check_game(self, data=None):
		db_info = {}

		question_tagObj = re.compile(r'^question_tag_(?P<syntaxString>[\w\-]*)$', re.U)
		question_wordObj = re.compile(r'^question_word_(?P<syntaxString>[\w\-]*)$', re.U)
		question_fullformObj = re.compile(r'^question_fullform_(?P<syntaxString>[\w\-]*)$', re.U)
		answer_tagObj = re.compile(r'^answer_tag_(?P<syntaxString>[\w\-]*)$', re.U)
		answer_wordObj = re.compile(r'^answer_word_(?P<syntaxString>[\w\-]*)$', re.U)
		answer_fullformObj = re.compile(r'^answer_fullform_(?P<syntaxString>[\w\-]*)$', re.U)

		answer_taskwordObj = re.compile(r'^answer_taskword_(?P<syntaxString>[\w\-]*)$', re.U)  # added by Heli

		targetObj = re.compile(r'^target_(?P<syntaxString>[\w\-]*)$', re.U)

		# Collect all the game targets as global variables
		self.global_targets = {}

		# If POST data was data check, regenerate the form using ids.
		# This iterates through forms in list of forms
		for n in range (1, self.num_fields):
			db_info = {}
			qwords = {}
			awords = {}
			tmpawords = {}

			# This compiles a dictionary from all of the form fields
				# {u'answer': u'',
				# u'userans': u'empty',
				# u'correct': u'empty',
				# u'tag_id': u'66',
				# u'word_id': u'628'}

			for fieldname, value in data.items():
				# print >> DEBUG, d, value
				if fieldname.count(str(n) + '-') > 0:
					fieldname = fieldname.lstrip(str(n) + '-')
					qwords = self.search_info(question_tagObj, fieldname, value, qwords, 'tag')
					qwords = self.search_info(question_wordObj, fieldname, value, qwords, 'word')
					qwords = self.search_info(question_fullformObj, fieldname, value, qwords, 'fullform')

					tmpawords = self.search_info(answer_tagObj, fieldname, value, tmpawords, 'tag')
					tmpawords = self.search_info(answer_wordObj, fieldname, value, tmpawords, 'word')
					tmpawords = self.search_info(answer_fullformObj, fieldname, value, tmpawords, 'fullform')
					tmpawords = self.search_info(answer_taskwordObj, fieldname, value, tmpawords, 'taskword')  # added by Heli

					self.global_targets = self.search_info(targetObj, fieldname, value, self.global_targets, 'target')

					db_info[fieldname] = value



			# This appears to not be used for leksa and morfa
			# Or if it is to be used with morfa, last stanza has problem.
			# Furthermore, qwords has no keys, and thus doesn't iterate.
			for syntax in qwords.keys():
				if qwords[syntax].has_key('fullform'):
					qwords[syntax]['fullform'] = [qwords[syntax]['fullform']]

			# This also appears to not be used for leksa and morfa
			# Or else there's a problem in the initial forloop.
			# Dictionary here comes out empty.
			# tmpawords doesn't iterate here; no keys
			for syntax in tmpawords.keys():
				awords[syntax] = []
				info = {}
				if tmpawords[syntax].has_key('word'):
					info['word'] = tmpawords[syntax]['word']
					if tmpawords[syntax].has_key('tag'):
						info['tag'] = tmpawords[syntax]['tag']
					if tmpawords[syntax].has_key('fullform'):
						info['fullform'] = [ tmpawords[syntax]['fullform']]
				if tmpawords[syntax].has_key('taskword'):
					info['taskword'] = tmpawords[syntax]['taskword']  # added by Heli
				awords[syntax].append(info)

			db_info['awords'] = awords
			db_info['qwords'] = qwords
			db_info['global_targets'] = self.global_targets
			#print "db_info['awords'] in check_game "
			#print db_info['awords']

			new_db_info = {}

			# Generate possible answers for contextual Morfa.
			if self.settings.has_key('gametype') and self.settings['gametype'] == 'context':
				new_db_info = self.get_db_info(db_info)
			if not new_db_info:
				new_db_info = db_info
			form, word_id = self.create_form(new_db_info, n, data)
			if form:
				self.form_list.append(form)
                        #print form

	def get_score(self, data):

		# Add correct forms for words to the page
		if "show_correct" in data:
			self.show_correct = 1

			for form in self.form_list:
				form.set_correct()

				self.count = 2

		# Count correct answers:
		self.all_correct = 0
		self.score = ""
		self.comment = ""
		i = 0

		points = sum([1 for form in self.form_list if form.error == "correct"])

		if points == len(self.form_list):
			self.all_correct = 1

		if self.show_correct or self.all_correct:
			self.score = self.score.join([repr(i), "/", repr(len(self.form_list))])

		if (self.show_correct or self.all_correct) and not self.settings['gametype'] == 'qa' :
			if i == 2:
				i = 3
			if i == 1:
				i = 2
			if self.settings.has_key('language'):
				language = switch_language_code(self.settings['language'])

				com_count = Comment.objects.filter(Q(level=i) & Q(lang=language)).count()
				if com_count > 0:
					self.comment = Comment.objects.filter(Q(level=i) & Q(lang=language))[randint(0,com_count-1)].comment

		self.score = '%d/%d' % (points, len(self.form_list))


class BareGame(Game):

	casetable = {
		'NOMPL': 'Nom',
		'ATTR': 'Attr',
		'PRED': 'Pred',
		'N-ILL': 'Ill',
		'N-ESS': 'Ess',
		'N-GEN': 'Gen',
		'N-LOC': 'Loc',
		'N-ACC': 'Acc',
		'N-COM': 'Com',
		'N-NOM': 'Nom',
		'A-ATTR': 'Attr',
		'COMP': 'Comp', # was: A-COMP
		'SUPERL': 'Superl', # was: A-SUPERL
		'POS':'',
		'CARD': '', # CARD, ORD, COLL added for implementing num_type choice
		'ORD': 'A+Ord',
		'COLL': 'N+Coll',
		'N-PX-GROUP1': 'Nom', # TODO: populate case in similar way to pronouns
		'N-PX-GROUP2': 'Acc', # was: Nom TODO: populate case in similar way to pronouns
		'N-PX-GROUP3': 'Nom', # TODO: populate case in similar way to pronouns
		'pers1': '1',
		'pers2': '2',
		'pers3': '3',
		'A-DER-V': 'A+Der/AV+V',
		'V-DER-PASS': '',
		'': '',
	}

	def get_db_info_new(self, db_info):

		from .forms import GAME_TYPE_DEFINITIONS
		from .forms import GAME_FILTER_DEFINITIONS

		if self.settings.has_key('pos'):
			pos = self.settings['pos']

		# Where to find the game type for each POS
		pos_gametype_keys = {
			'N': 'case',
			'V': 'vtype',
			'Der': 'derivation_type',
			'Px': 'possessive_type',
			'A': 'adjcase',
			'Num': 'num_bare',
			'Pron': 'proncase',
		}

		game_type_location = pos_gametype_keys.get(pos, False)
		gametype = self.settings.get(game_type_location, False)

		if not game_type_location:
			raise Http404("Undefined POS-form relationship, or wrong type.")

		if not gametype:
			raise Http404("Game type was not set on the form object.")


		game_types = GAME_TYPE_DEFINITIONS.get(pos, False)
		game_filters = GAME_FILTER_DEFINITIONS.get(pos, False)

		if not game_types:
			raise Http404("Undefined POS in game_type_definitions")


		possible_types = game_types.get(gametype, False)
		if not possible_types:
			raise Http404("Undefined type %s" % gametype)

		question, answer = choice(possible_types)

		answer_tags = parse_tag(answer)

		TAG_QUERY = Q(string__in=answer_tags)

		tags = Tag.objects.filter(TAG_QUERY).order_by('?')

		if len(tags) == 0:
			t_q = str(TAG_QUERY)
			raise Http404("Oops, no tags matching query!\n\n\t\n%s" % t_q)


		# Pronoun type and grade must be filtered here because it affects the
		# set of tags available for the next step.

		# TODO: grade

		if 'pron_type' in game_filters:
			ptype = True and self.settings.get('pron_type') or False
			# print ptype
			if ptype:
				tags = tags.filter(subclass=ptype)
				# print tags

		# select a random tag and set of forms associated with it to begin
		tag = tags[0]
		random_form = tag.form_set.order_by('?')

		no_forms = True
		failure_count = 0

		while no_forms and failure_count < 10:

			for filter_ in game_filters:
				if filter_ == 'semtype':
					possessive_type = True and self.settings.get('possessive_type') or   ""
					if possessive_type:
						semtypes = POSSESSIVE_CHOICE_SEMTYPES[possessive_type]
						random_form = random_form.filter(word__semtype_semtype__in=semtypes)

				if filter_ == 'source':
					source = True and self.settings.get('book') or False
					if source:
						random_form = random_form.filter(word__source__name__in=[source])

				if filter_ == 'stem':
					bisyl = ['2syll', 'bisyllabic']
					trisyl = ['3syll', 'trisyllabic']
					Csyl = ['Csyll', 'contracted'] # added for sme

					syll = True and	self.settings.get('syll') or ['']

					sylls = []
					for item in syll:
						if item in bisyl:
							sylls.append('2syll')
						if item in trisyl:
							sylls.append('3syll')
						if item in Csyl:
							sylls.append('Csyll')

					random_form = random_form.filter(word__stem__in=sylls)

			# If there are forms left, we select one
			if random_form.count() > 0:
				no_forms = False
				break
			else:
				# Otherwise try a new tag and form set and run through the
				# filters again
				tag = tags.order_by('?')[0]
				random_form = tag.form_set.order_by('?')
				failure_count += 1
				continue

		random_form = random_form[0]
		db_info['word_id'] = random_form.word.id
		db_info['tag_id'] = tag.id



	def get_db_info(self, db_info):

		if self.settings.has_key('pos'):
			pos = self.settings['pos']


		syll = True and	self.settings.get('syll')	or ['']
		case = True and	self.settings.get('case')	or   ""
		singular_only = self.settings.get('singular_only', False)  # Make it possible to only generate singular exercises for noun if the user wishes so.
		sg2_only = self.settings.get('sg2_only', False) # Only sg2 exercises can be chosen for Morfa-S verb imperative.
		levels = True and self.settings.get('level')   or   []
		adjcase = True and self.settings.get('adjcase') or   ""
		pron_type = True and self.settings.get('pron_type') or   ""
		proncase = True and self.settings.get('proncase') or   ""
		derivation_type = True and self.settings.get('derivation_type') or   ""
		possessive_case = True and self.settings.get('possessive_case') or   ""
		possessive_type = True and self.settings.get('possessive_type') or   ""
		possessive_number = True and self.settings.get('possessive_number') or   ""
		possessive_person = True and self.settings.get('possessive_person') or   ""

		grade = True and self.settings.get('grade')  or  ""
		num_type = True and self.settings.get('num_type') or ""  # added to get num_type from settings
		source = ""

		mood, tense, infinite, attributive = "", "", "", ""

		num_bare = ""

		if self.settings.has_key('book'):
			source = self.settings['book']
			if source.lower() != 'all':
				try:
					S = Source.objects.filter(name=source)
					source = S
				except Source.DoesNotExist:
					source = False
			else:
				source = False
		if self.settings.has_key('num_bare'):
			num_bare = self.settings['num_bare']
		if self.settings.has_key('num_level'):
			num_level = self.settings['num_level']
		if self.settings.has_key('num_type'):  # added by Heli
			num_type = self.settings['num_type']
		if self.settings.has_key('grade'):
			grade = self.settings['grade']

		pos_tables = {
			"N":	case,
			"A":	adjcase,
			"Num":  num_bare,
			"V":	"",
			"Pron": proncase,
			"Der": derivation_type,
			"Px": possessive_type,  # possessive_type is about semtypes (family, other, all)
		}

		morfas_log = logging.getLogger('morfa-s')
		semtypes = False  # needed for Px
		sylls = []
		bisyl = ['2syll', 'bisyllabic']
		trisyl = ['3syll', 'trisyllabic']
		Csyl = ['Csyll', 'contracted'] # added for sme

		for item in syll:
			if item in bisyl:
				sylls.append('2syll')
			if item in trisyl:
				sylls.append('3syll')
			if item in Csyl:
				sylls.append('Csyll')

		if pos == 'Pron':
			syll = ['']

		if pos == 'Px':
			syll = bisyl + trisyl + Csyl

		if pos == 'Px':
			# Hacky, if possessive_case is not set, then we can assume
			# it's nominative for the one type where nominative exists (FAMILY)
			if not possessive_case:
			     possessive_case = 'N-NOM'
			elif possessive_case == 'N-NOM' and possessive_type == 'N-PX-GROUP2':   # to avoid the crash with case=NOM, type=OTHER
				possessive_case = 'N-ACC'
			case = self.casetable[possessive_case]
			possessive_person = self.casetable[possessive_person]
		else:
			case = self.casetable[pos_tables[pos]]

		grade = self.casetable[grade]
		num_type = self.casetable[num_type] # added by Heli

		pos_mood_tense = {
			"PRS":	("Ind", "Prs", ""),
			"PRT":	("Ind", "Prt", ""),
			"PRF":	("", "", "PrfPrc"),
			"GER":	("", "", "Ger"),
			"COND":   ("Cond", "Prs", ""),
			"IMPRT":  ("Imprt", "", ""),
			"POT":	("Pot", "Prs", "")
		}

		if pos == "V" and self.settings.has_key('vtype'):
			mood, tense, infinite = pos_mood_tense[self.settings['vtype']]

		pos2 = ''
		subclass = ''
		if pos == "Num":
			if num_type == "A+Ord":  # Ordinal numerals have tag A+Ord
				pos = 'A'
				#self.settings['pos'] = 'A'
				pos2 = 'Num'
				subclass='Ord'
			elif num_type == "N+Coll":  # Collective numerals have tag N+Coll
				pos = 'N'
				#self.settings['pos'] = 'N'
				pos2 = 'Num'
				subclass='Coll'

		number = ["Sg","Pl",""]

		if case == "Ess":
			number = [""]
		elif case == "Nom" and pos != "Pron":
			number = ["Pl"]
		else:
			number = ["Sg","Pl"]

		# A+Sg+Nom

		# following values are in grade
		# A+Comp+Sg+Nom
		# A+Superl+Sg+Nom

		# following value is in case
		# A+Attr
		if pos == 'A':
			if "Attr" in [attributive, case]:
				attributive = "Attr"
				case = ""
				number = [""]

		maxnum, i = 20, 0

		TAG_QUERY = Q(pos=pos)

		# Exclude derivations by default
		TAG_EXCLUDES = Q(subclass__contains='Der')
		# TODO: Px ?

		FORM_FILTER = False

		# Query filtering on words
		# SUB_QUERY = Q(word__stem__in=sylls)
		SUB_QUERY = False

		# NOTE: copied this from questions_install, to make it easier to define
		# what kind of exercise it is. It would be nice to extend this to everything
		# because then we can just define a question/answer tag as something like:
		#     question_types = [
		#       ('V+Inf', 'V+Ind+Prs+Person-Number'),
		#       ('V+Inf', 'V+Pot+Tense+Person-Number'),
		#		('A+Sg+Nom', 'A+Der/AV+V+Ind+Prs+Person-Number'),
		#     ]
		#
		# And it will save the need for a lot of lines of code.

		if pos == "Der":
			derivation_types = {
				# 'Der/AV': parse_tag("A+Der/AV+V+Mood+Tense+Person-Number"),
				#'A-DER-V': parse_tag("A+Der/AV+V+Ind+Prs+Person-Number-ConNeg"),
				# generalisation: Tense to enable both Prs and Prt
				'A-DER-V': parse_tag("A+Der/AV+V+Mood+Tense+Person-Number"),
				'V-DER-PASS': parse_tag("V+Der/PassL+V+Ind+Tense+Person-Number-ConNeg"),
			}

			TAG_QUERY = Q(string__in=derivation_types[derivation_type])
			TAG_EXCLUDES = False
			sylls = False
			source = False

		if pos == 'Px':
			from forms import POSSESSIVE_QUESTION_ANSWER, POSSESSIVE_CHOICE_SEMTYPES
			possessive_types = dict(
				[(key, parse_tag(qa[0][1]))
				for key, qa in POSSESSIVE_QUESTION_ANSWER.iteritems()]
			)
			semtypes = POSSESSIVE_CHOICE_SEMTYPES[possessive_type]
			p_type = possessive_types[possessive_type]
                        # Commented the following section out as we are not using possessive_number but possessive_person now.
			"""if 'PXPROPERTY' not in semtypes:
				possessive_number = 'N-SG'
			if possessive_number == 'N-SG':
				if case == 'Nom':
					p_type = [a for a in p_type if 'PxSg1' in a or 'PxSg2' in a]  # there are no forms in the database with case='Nom' and possessive='PxSg3'
				else:
					p_type = [a for a in p_type if 'PxSg' in a]
			elif possessive_number == 'N-DU':
				p_type = [a for a in p_type if 'PxDu' in a]
		        else:
				p_type = [a for a in p_type if 'PxPl' in a]
			"""
                        if possessive_type == 'N-PX-GROUP1':
                                p_number = ['Sg']
				TAG_EXCLUDES = Q(subclass='G3') # There are no FAMILY-words in the lexicon with subclass=G3 that resulted in an empty queryset.
                        else:
                                p_number = ['Sg', 'Pl', 'Du']
				TAG_EXCLUDES = False
			#TAG_QUERY = Q(string__in=p_type)
			TAG_QUERY = Q(possessive__endswith=possessive_person, number__in=p_number)

			sylls = False
			source = False

		if pos in ['Pron', 'N', 'Num']:
			TAG_QUERY = TAG_QUERY & \
						Q(case=case)
						# regardless of whether it's Actor, Coll, etc.

			if pos == 'N':
				if singular_only:   # if the user has checked the box "singular only"
					TAG_QUERY = TAG_QUERY & Q(number='Sg') & Q(possessive="")
				else:
					TAG_QUERY = TAG_QUERY & \
							Q(possessive="") & \
							Q(number__in=number) # number sg or pl; exclude possessive forms

			# 'Pers' subclass for pronouns, otherwise none.
			# TODO: combine all subclasses so forms can be fetched
			if pos == 'Pron':
				sylls = False
				TAG_QUERY = TAG_QUERY & Q(subclass=pron_type) & Q(number__in=['', 'Du', 'Pl', 'Sg'])  # Sg added by Heli
			elif pos2 == 'Num':
				sylls = False
				TAG_QUERY = TAG_QUERY & Q(subclass=subclass)
			else:
				TAG_QUERY = TAG_QUERY & Q(subclass='')

		if pos == 'Num' or pos2 == 'Num':
			if num_level == '1':  # Numerals in Sg on level 1
				TAG_QUERY = TAG_QUERY & Q(number='Sg')
			else:  # Numerals in both Sg and Pl on level 1-2
				TAG_QUERY = TAG_QUERY & Q(number__in=['Sg','Pl'])

		if pos == 'V':
			TAG_QUERY =  TAG_QUERY & \
							Q(tense=tense) & \
							Q(mood=mood) & \
							Q(infinite=infinite)

			if mood == 'Imprt':
				TAG_QUERY = TAG_QUERY & Q(personnumber__contains='2')
				if sg2_only:   # if the user has checked the box "singular 2. person only"
					TAG_QUERY = TAG_QUERY & Q(personnumber='Sg2')

			if tense != 'Prs':
				TAG_EXCLUDES = Q(string__contains='ConNeg')

		if pos == 'A':
			if pos2 == 'Num':
				sylls = False
				TAG_QUERY = TAG_QUERY & Q(subclass=subclass) & Q(case=case) & Q(attributive='') & Q(grade='')
			else:
				TAG_QUERY = TAG_QUERY & \
						Q(subclass='') & \
						Q(attributive=attributive) & \
						Q(grade=grade) & \
						Q(case=case) & \
						Q(number__in=number)
		if pos == 'Px':
			TAG_QUERY = TAG_QUERY & Q(case=case)
			morfas_log.info(pos+" "+case+" ")

		# filter can include several queries, exclude must have only one
		# to work successfully
		if pos != 'Der':
			tags = Tag.objects.exclude(string__contains='Der')\
								.filter(TAG_QUERY)\
								.exclude(subclass='Prop')\
								.exclude(polarity='Neg')
		else:
			tags = Tag.objects.filter(TAG_QUERY)\
								.exclude(subclass='Prop')\
								.exclude(polarity='Neg')

		if TAG_EXCLUDES:
			tags = tags.exclude(TAG_EXCLUDES)

		if pos == 'Px':
			tags = tags.annotate(pxc=Count('form')).exclude(pxc=0)


		if tags.count() == 0:
			keys = ['pos', 'case', 'tense', 'mood', 'attributive', 'grade', 'number']
			values = [pos, case, tense, mood, attributive, grade, number]
			error = """Morfa.get_db_info: Database is improperly loaded.
					No tags for the query were found.\n\n
					%s\n\n
					%s""" % (TAG_QUERY, SUB_QUERY)

			if TAG_EXCLUDES:
				error += "\nexcludes: %s" % TAG_EXCLUDES

			raise Http404(error)

		if pos == 'Num' or pos2 == 'Num':
			QUERY = Q(pos__iexact=pos) & Q(form__tag__subclass=subclass)
		else:
			# levels is not what we're looking for
			QUERY = Q(pos__iexact=pos) & Q(stem__in=syll)
			if source and source not in ['all', 'All']:
				QUERY = QUERY & Q(source__name=source)


		smallnum = ["okta", "guokte", "golbma", "njeallje", "vihtta", "guhtta",
					"čieža", "gávcci","ovcci","logi"]
		smallnum_ord = ["vuosttaš", "nubbi", "goalmmát", "njealját", "viđát",
						"guđát", "čihččet", "gávccát", "ovccát", "logát"]
		smallnum_coll = ["guovttis", "guovttes", "golmmas", "njealjis",
						"viđás", "guđás", "čiežas", "gávccis","ovccis","logis"]

		if pos == 'Num' and subclass == '':
			QUERY = QUERY & Q(lemma__in=smallnum)

		if pos2 == 'Num' and subclass == 'Ord':
			QUERY = QUERY & Q(lemma__in=smallnum_ord)

		error = """Morfa.get_db_info: Database is improperly loaded.
		There are no Words, Tags or Forms, or the query
		is not returning any."""
		NoWordsFound = Http404(error)

		# settings dialect?
		if self.settings.has_key('dialect'):
			UI_Dialect = self.settings['dialect']
		else:
			UI_Dialect = DEFAULT_DIALECT

		try:
			tag = tags.order_by('?')[0]
			morfas_log.info(tag.string)
			no_form = True
			count = 0
			while no_form and count < 10:

				# Pronouns are a bit different, so we need to resort the tags
				if tag.pos == 'Pron':
					tag = tags.order_by('?')[0]

				random_word = tag.form_set.filter(word__language=LLL1)

				if not tag.pos in ['Pron', 'Num'] and \
					tag.string.find('Der') < 0:
					random_word = random_word.filter(word__semtype__semtype="MORFAS")

				if tag.pos == 'Pron':
					random_word = random_word.exclude(word__stem='nubbi')
				if sylls:
					random_word = random_word.filter(word__stem__in=sylls)
				if source:
					random_word = random_word.filter(word__source__in=source)
				if semtypes:
					random_word = random_word.filter(word__semtype__semtype__in=semtypes)
				if pos2 == 'Num':
					if subclass == 'Ord':
						random_word = random_word.filter(word__lemma__in=smallnum_ord)  # added to constrain the set of ordinal numerals
					elif subclass == 'Coll':
						random_word = random_word.filter(word__lemma__in=smallnum_coll) # constrains the set of collective numerals

				if random_word.count() > 0:
					random_form = random_word.order_by('?')[0]
					random_word = random_form.word
					#logfile.write(random_word.lemma)
					no_form = False
					break
				elif random_word.count() == 1:
					random_form = random_word[0]
					random_word = random_form.word
					#logfile.write(random_word.lemma)
					break
				else:
					count += 1
					continue

			morfas_log.info("tag:",tag.string,"random word:",random_word) # for debugging - why we get 'QuerySet' object has no attribute 'id' ?
			db_info['word_id'] = random_word.id
			db_info['tag_id'] = tag.id
			if tag.string.lower().find('conneg') > -1:
				db_info['conneg'] = choice(PRONOUNS_LIST.keys())
			else:
				db_info['conneg'] = False

		except IndexError:
			wc = Word.objects.count()
			tc = Tag.objects.count()
			fc = Form.objects.count()
			wfc = Word.objects.filter(QUERY).count()
			tfc = Tag.objects.filter(TAG_QUERY).count()
			if 0 in [tc, wc, fc, wfc, tfc]:
				# print error
				error += "Word count (%d), Tag count (%d), Form count (%d), Words matching query (%d), Tags matching query (%d)." % (wc, tc, fc, wfc, tfc)
				error += "\n  Query: %s" % repr(QUERY)
				error += "\n  Tag Query: %s" % repr(TAG_QUERY)
				raise Http404(error)
		return


	def create_form(self, db_info, n, data=None):
		if not db_info.has_key('word_id'):
			return None, None

		if self.settings.has_key('dialect'):
			UI_Dialect = self.settings['dialect']
		else:
			UI_Dialect = DEFAULT_DIALECT
		if UI_Dialect == 'KJ':
			wrong_dialect = 'GG'
		else:
			wrong_dialect = 'KJ'

		language = self.settings['language']
		pos = self.settings['pos']
		Q_DIALECT = Dialect.objects.get(dialect=UI_Dialect)

		word = Word.objects.get(id=db_info['word_id'])
		tag = Tag.objects.get(id=db_info['tag_id'])

		# A little exception for derivation, we want to be able to accept PassS
		# and PassL, but show only PassL in the answers.

		# Get the initial form list of forms matching the tag and word id
		if pos == 'Pron':
			# Need to filter by the word lemma for pronouns, otherwise
			# ambiguities arise
			form_list = Form.objects.filter(tag=tag, word__lemma=word.lemma)
		elif pos == 'Der':
			# Search for PassS and PassL forms, filter out later. NB: previous
			# step only searches for PassL, so at this point we know some PassL
			# forms exist for the word.
			tag_strings = [tag.string]
			if 'Der/PassL' in tag.string:
				tag_strings.append(tag.string.replace('PassL', 'PassS'))
			elif 'Der/PassS' in tag.string:
				tag_strings.append(tag.string.replace('PassS', 'PassL'))
			form_list = word.form_set.filter(tag__string__in=tag_strings)
		# TODO: Px
		else:
			form_list = word.form_set.filter(tag=tag)

		form_list = form_list.exclude(word__dialects__dialect=wrong_dialect)  # take into account the dialect information attached to the Word objects

		if not form_list:
			raise Form.DoesNotExist

		if pos == 'Der':
			correct = form_list.filter(tag__string__contains='PassL')

		# TODO: Px

		correct = form_list[0]

		# Due to the pronoun ambiguity potential (gii 'who', gii 'which'),
		# we need to make sure that the word is the right one.
		if pos == 'Pron':
			word = correct.word


		# Get baseform, matching number; except for in essive where
		# there is no number, and with Nominative, where the test is
		# about turning nominative singular into nominative plural,
		# thus all baseforms should be singular.

		if tag.case in ['Ess', 'Nom'] or tag.attributive:
			match_number = False
		else:
			match_number = True

		def baseformFilter(form):
			#   Get baseforms, and filter based on dialects.

			#	NOTE: Need to use getBaseform on Form object, not Word,
			#	because Word.getBaseform doesn't pay attention to number.

			if self.settings.has_key('dialect'):
				UI_Dialect = self.settings['dialect']
			else:
				UI_Dialect = DEFAULT_DIALECT

			# Derived forms need return_all=False otherwise derived infinitive
			# forms may be returned, and we need them to be underived in
			# presentation of the question wordform.
			if pos == 'Der':
				try:
					bfs = form.getBaseform(match_num=match_number, return_all=False)
				except:
					bfs = [form.word]
				return bfs

			if pos == 'Px':
				try:
					bfs = form.getBaseform(match_num=match_number, return_all=False)
				except:
					bfs = [form.word]
				return bfs

			bfs = form.getBaseform(match_num=match_number, return_all=True)

			excluded = bfs.exclude(dialects__dialect='NG')  # added by Heli
			if pos == 'N':
			     excluded = excluded.exclude(tag__string__icontains="Px")  # added to avoid possessive forms N+Sg+Nom+PxSg1 as base forms
			if excluded.count() == 0:
				excluded = bfs
			#print excluded
			filtered = excluded.filter(dialects__dialect=UI_Dialect)

			# If no non-NG forms are found, then we have to display those.
			if filtered.count() == 0 and excluded.count() > 0:
				return list(excluded)
			else:
				return list(filtered)

		base_forms = map(baseformFilter, form_list)

		# Flatten the lists, but if this isn't an iterateable object, don't worry
		try:
			base_forms = sum(base_forms, [])
		except TypeError:
			pass

		# Just in case multiple are returned, get the first.
		# TODO: make sure no forms that are needed are being lost here.
		try:
			baseform = list(set(base_forms))[0]
		except IndexError:
			if len(base_forms) == 0:
				baseform = form.getBaseform(match_num=match_number)

		# All possible form presentations
		accepted_answers = form_list.values_list('fullform', flat=True)

		presentation = filter_set_by_dialect(form_list, Q_DIALECT)

		if pos == 'Der':
			presentation = presentation.filter(tag__string__contains='PassL')

		# TODO: Px
		#if pos == 'Px':
		#	print 'presentation'
		#	print presentation

		# Unless there aren't any ...
		if presentation.count() == 0:
			presentation = form_list

		presentation_ng = presentation.values_list('fullform',flat=True)

		# Get word translations for the tooltip
		target_key = switch_language_code(self.settings['language'][-3::])

		# Derivations are different. For now it is very difficult to keep all
		# things consistent w.r.t. Der/ being part of a word subclass or not,
        # so for Der we need to look at the word it is derived from, and look
        # that word up, then get those translation strings. If this is fixed,
        # then this code should still function.
		if pos == 'Der':
			if isinstance(baseform, Word):
			    root_pos = baseform.pos
			elif isinstance(baseform, Form):
			    root_pos = baseform.word.pos

			trans_word = Word.objects\
			                    .filter(lemma=word.lemma, pos=root_pos)\
								.annotate(tc=Count('wordtranslation'))\
								.filter(tc__gt=0)[0]
			ws = trans_word.translations2(target_key).all()  # was ts
		elif pos == 'Px':
                        if isinstance(baseform, Word):
                                ws = baseform.translations2(target_key).all()
                        elif isinstance(baseform, Form):  # normally, the type of the baseform should be Form
                                ws = baseform.word.translations2(target_key).all()
		else:
			ws = word.translations2(target_key).all()

		translations = sum([w.word_answers for w in ws],[])

		# Check if the form is connegative, if not, set to false.

		# NB: this is part of making sure that since the connegative form is
		# the same for all pronouns, that one pronoun is displayed throughout
		# all of the steps of the user entering answers and checking that they
		# are correct.
		if not db_info.get('conneg', False):
			db_info['conneg'] = False

		morph = (MorfaQuestion(
					word=word,
					tag=tag,
					baseform=baseform,
					correct=correct,
					accepted_answers=accepted_answers,
					answer_presentation=presentation_ng,
					translations=translations,
					question="",
					dialect=Q_DIALECT,
					language=language,
					userans_val=db_info['userans'],  # TODO: userans not in use?
					correct_val=db_info['correct'],
					data=data,
					prefix=n,
					conneg=db_info['conneg'],
					user=self.settings["user"],
					user_country=self.settings["user_country"])
				)
		return morph, word.id




class NumGame(Game):
	generate_fst = "transcriptor-numbers-digit2text.filtered.lookup.hfstol"
	answers_fst = "transcriptor-numbers-text2digit.filtered.lookup.hfstol"

	def get_db_info(self, db_info):
		""" Options supplied by views
			ord, card - obvious
			kl1 - easy clock (half hours only)
			kl2 - medium clock (quarter hours)
			TODO: kl3 - difficult clock (all numbers??)
		"""
		numeral=""
		num_list = []

		random_num = randint(1, int(self.settings['maxnum']))

		db_info['numeral_id'] = str(random_num)

		if self.settings['gametype'] == 'ord':
			db_info['numeral_id'] += "."

		return db_info

	def generate_forms(self, forms, fstfile):
		import subprocess
		from threading import Timer

		lookup = "/usr/bin/hfst-lookup"
		gen_norm_fst = FST_DIRECTORY + "/" + fstfile
		try:
			open(gen_norm_fst)
		except IOError:
			raise Http404("File %s does not exist." % gen_norm_fst)

		gen_norm_command = [lookup, "-q", gen_norm_fst]

		try:
			forms.encode('utf-8')
		except UnicodeDecodeError:
			pass

		num_proc = subprocess.Popen(gen_norm_command,
									stdin=subprocess.PIPE,
									stdout=subprocess.PIPE,
									stderr=subprocess.PIPE)

		#@cip: Do not create zombi processes!
		#def kill_proc(proc=num_proc):
		#	try:
		#		proc.kill()
		#		raise Http404("Process for %s took too long." % ' '.join(gen_norm_command))
		#	except OSError:
		#		pass
		#	return

		#t = Timer(5, kill_proc)
		#t.start()
		output, err = num_proc.communicate(forms)

		return output, err

	def clean_fst_output(self, output):
		num_tmp = output.decode('utf-8').splitlines()
		cleaned = []
		for num in num_tmp:
			line = num.strip()
			# line = line.replace(' ','')
			if line:
				nums = line.split('\t')
				if len(nums) == 3:
					nums = (nums[0], '?')
				else:
					nums = tuple(nums)
			cleaned.append(nums)
		return cleaned

	def clean_hfst_output(self, output):
		lines = output.decode("utf-8").splitlines()
		cleaned = []
		for line in lines:
			line = line.strip()
			if not line:
				continue
			cols = line.split("\t")
			if len(cols) != 3:
				continue
			cleaned.append((cols[0], cols[1]))
		return cleaned

	def strip_unknown(self, analyses):
		return [a for a in analyses if a[1] != '?']

	def check_answer(self, question, useranswer, formanswer):
		print useranswer
		print formanswer
		gametype = self.settings['numgame']
		# print gametype
		if useranswer.strip():
			print "d: 3"
			forms = useranswer.encode('utf-8')

			print "gametype = %s" % gametype
			if gametype == 'string':
				fstfile = self.generate_fst
			elif gametype == 'numeral':
				fstfile = self.answers_fst

			output, err = self.generate_forms(forms, fstfile)
			print output

			num_list = self.clean_hfst_output(output)
			print num_list
			num_list = self.strip_unknown(num_list)
			print num_list
			# print repr([question, useranswer, num_list])

			# 'string' refers to the question here, not the answer
			if gametype == 'string':
				print "d: 4"
				# user answer must match with numeral generated from
				# the question

				if useranswer in [a[0] for a in num_list] and \
					question in [a[1] for a in num_list]:
					print "d: 5"
					return True
				else:
					print "d: 6"
					return False

			elif gametype == 'numeral':
				print "d: 7"
				# Numbers generated from user answer must match up
				# with numeral in the question
				num_list = num_list + formanswer
				try:
					_ = int(useranswer)
					print "d: 8"
					return False
				except ValueError:
					print "d: 9"
					pass
				if question in [a[1] for a in num_list] or \
					useranswer in num_list:
					print "d: 10"
					return True
				else:
					print "d: 11"
					return False



	def create_form(self, db_info, n, data=None):

		if self.settings['gametype'] in ["ord", "card"]:
			language = LLL1
		else:
			language = LLL1

		numstring = ""

		fstfile = self.generate_fst
		q, a = 0, 1

		# production paths
		lookup = "%s\n" % db_info['numeral_id']
		output, err = self.generate_forms(lookup, fstfile)

		num_tmp = output.splitlines()
		num_list = []
		for num in num_tmp:
			line = num.strip()
			line = line.replace(' ','')
			if line:
				nums = line.split('\t')
				num_list.append(nums[a].decode('utf-8'))
		try:
			numstring = num_list[0]
		except IndexError:
			error = "Morfa.NumGame.create_form: Database is improperly loaded, \
					 or Numra is unable to look up words."
			raise Http404(error)

		form = (NumQuestion(
					numeral=db_info['numeral_id'],
					num_string=numstring,
					num_list=num_list,
					gametype=self.settings['numgame'],
					userans_val=db_info['userans'],
					correct_val=db_info['correct'],
					data=data,
					prefix=n,
					game=self,
					user=self.settings["user"],
					user_country=self.settings["user_country"])
				)

		return form, numstring

from forms import KlokkaQuestion

class Klokka(NumGame):

	QuestionForm = KlokkaQuestion

	generate_fst = "transcriptor-clock-digit2text.filtered.lookup.hfstol"
	answers_fst = "transcriptor-clock-text2digit.filtered.lookup.hfstol"

	error_msg = "Morfa.Klokka.create_form: Database is improperly loaded, \
					 or Numra is unable to look up words."

	def get_db_info(self, db_info):

		hour = str(randint(0, 23))

		if len(hour) == 1:
			hour = '0' + hour
		else:
			hour = str(hour)
		if self.settings['gametype'] == "kl1":
			min_options = ['00', '30']
			minutes = choice(min_options)
		elif self.settings['gametype'] == "kl2":
			min_options = ['00', '15', '30', '45']
			minutes = choice(min_options)
		elif self.settings['gametype'] == "kl3":
			mins = str(randint(0, 59))
			if len(mins) == 1:
				mins = '0' + mins
			minutes = mins

		random_num = '%s:%s' % (hour, minutes)

		db_info['numeral_id'] = str(random_num)

		return db_info


	def check_answer(self, question, useranswer, formanswer):
		# TODO: in string->num, need to display the corresponding numeral if
		# it is one that can be 14 hour time
		gametype = self.settings['numgame']
		if useranswer.strip():
			forms = useranswer.encode('utf-8')

			if gametype == 'string':
				fstfile = self.generate_fst
			elif gametype == 'numeral':
				fstfile = self.answers_fst

			output, err = self.generate_forms(forms, fstfile)

			num_list = self.clean_fst_output(output)
			num_list = self.strip_unknown(num_list)
			# print repr([question, useranswer, num_list])

			# 'string' refers to the question here, not the answer
			if gametype == 'string':
				# user answer must match with numeral generated from
				# the question

				if useranswer in [a[0] for a in num_list] and \
					question in [a[1] for a in num_list]:
					return True
				else:
					return False

			elif gametype == 'numeral':
				# Numbers generated from user answer must match up
				# with numeral in the question

				# Bug in numeral game seems to be presenting wrong set of numerals,
				# so if answerset contains 13+, need to remove and take the lower.
				# Or 'militaryrelax' the answer

				num_list = num_list + formanswer
				try:
					_ = int(useranswer)
					return False
				except ValueError:
					pass
				if question in [a[1] for a in num_list] or \
					useranswer in num_list:
					return True
				else:
					return False

	def create_form(self, db_info, n, data=None):
		if self.settings['gametype'] in ["kl1", "kl2", "kl3"]:
			language = LLL1

		numstring = ""

		fstfile = self.generate_fst
		q, a = 0, 1

		lookup = "%s\n" % db_info['numeral_id']

		# lookup = "%s\n" % db_info['numeral_id']
		output, err = self.generate_forms(lookup, fstfile)

		# norm, allnum = output.split('\n\n')[0:2]

		norm_list = []
		for num in output.decode('utf-8').splitlines():
			line = num.strip()
			if line:
				nums = line.split('\t')
				norm_list.append(nums[a])

		try:
			numstring = norm_list[0]
		except IndexError:
			raise Http404(self.error_msg)

		form = (self.QuestionForm(
					numeral=db_info['numeral_id'],
					num_string=numstring,
					present_list=norm_list,
					accept_list=norm_list,
					gametype=self.settings['numgame'],
					userans_val=db_info['userans'],
					correct_val=db_info['correct'],
					data=data,
					prefix=n,
					game=self)
				)

		return form, numstring

##
#
#  Dato
#
##

class Dato(Klokka):
	from forms import DatoQuestion as QuestionForm

	# QuestionForm = DatoQuestion

	generate_fst = "transcriptor-date-digit2text.filtered.lookup.hfstol"
	answers_fst = "transcriptor-date-text2digit.filtered.lookup.hfstol"

	error_msg = "Dato.create_form: Database is improperly loaded, \
					 or Dato is unable to look up forms."

	def get_db_info(self, db_info):
		""" Going to need to subclass this because klokka generates the wrong thing.

			Lookup format is DD.M.

			Dato has no difficulty options.
		"""
		from random import choice

		def dayrange(x):
			return range(1,x+1)

		# List of tuples with all possible days
		# built from (month, maxdays)

		months = [(x, dayrange(y)) for x, y in [(1, 31),
												(2, 29),
												(3, 31),
												(4, 30),
												(5, 31),
												(6, 30),
												(7, 31),
												(8, 31),
												(9, 30),
												(10, 31),
												(11, 30),
												(12, 31)]]

		month, days = choice(months)

		date = '%d.%d.' % (choice(days), month)

		db_info['numeral_id'] = str(date)



class QuizzGame(Game):

	def get_db_info(self, db_info):

		# levels = self.settings['level']
		semtypes = self.settings['semtype']
		geography = self.settings['geography']
		frequency = True and self.settings['frequency'] or False # frequency value or False
		source = self.settings['source']

		source_language = self.settings['transtype'][0:3]
		target_language = self.settings['transtype'][-3::]
		QueryModel = Word

		if self.settings.has_key('dialect'):
			UI_Dialect = self.settings['dialect']
		else:
			UI_Dialect = DEFAULT_DIALECT

		if UI_Dialect == 'KJ':
			wrong_dialect = 'GG'
		else:
			wrong_dialect = 'KJ'

		# Excludes
		excl = ['exclude_' + self.settings['transtype']]

		error = "QuizzGame.get_db_info: Database may be improperly loaded. \
		Query for semantic type %s and book %s returned zero results." % ((semtypes, source))

		# This query is fairly expensive, and must be run once per game-form generation. Thus,
		# on the first generation it is run, and the results are stored to a list.
		# Each successive time this is run after the first query, a word is selected from the list
		# and popped off.

		if not self.query_set:
			leksa_kwargs = {'lang': source_language,
							'tx_lang': target_language,
							'wrong_dialect': wrong_dialect}

			excl.append('mPERSNAME')

			if semtypes and semtypes not in ['all', 'All']:
				leksa_kwargs['semtype_incl'] = semtypes

			if source and source not in ['all', 'All']:
				leksa_kwargs['source'] = source
				leksa_kwargs['semtype_incl'] = False

			if geography:
				leksa_kwargs['geography'] = geography

			if excl:
				leksa_kwargs['semtype_excl'] = excl

			# The following is written by the example of sylls in MorfaS: this
			# can probably be simplified-- with sylls in MorfaS there was a
			# time when there were several possible values (3syll,
			# trisyllabic), but this should be no longer the case...

			kw_frequency = []
			common = ['common', 'common']
			rare = ['rare', 'rare']

			if frequency:
				for item in frequency:
					if item in common:
						kw_frequency.extend(common)
					if item in rare:
						kw_frequency.extend(rare)

				leksa_kwargs['frequency'] = list(set(kw_frequency))

			word_set = leksa_filter(QueryModel, **leksa_kwargs)
			self.query_set = word_set

		try:
			while True:
				random_word = choice(self.query_set)
				if random_word[1] not in self.lemmas_selected:
					break
				else:
					continue
			self.lemmas_selected.append(random_word[1])
			# self.query_set.pop(self.query_set.index(random_word))
		except IndexError:
			if len(self.query_set) == 0:
				raise Http404(error + "  " + repr(leksa_kwargs))

		db_info['word_id'] = random_word[0]
		db_info['question_id'] = ""

		return db_info

	def create_form(self, db_info, n, data=None):
		tr_lemmas = []
		# This is producing an unnecessary query, but it takes a lot of work to switch this
		# to just passing a word model instead of the ID.
		# Ideally should pass the model, so there's no need to query it again.
		word_id = db_info['word_id']

		target_language = self.settings['transtype'][-3::]
		source_language = self.settings['transtype'][0:3]

		word = Word.objects.get(Q(id=word_id))

		translations = word.wordtranslation_set.filter(language=target_language)
		tr_lemmas.extend([w.definition for w in translations])


		# Get correct answers; pick the first (oho!)
		# Need to not pick the first one.
		correct = ""
		preferred = False
		possible = False
		stat_pref = False
		tcomms = False
		if type(word) == Word:
			trans_obj = word.translations2(self.settings['transtype']).all()
			possible = [t.definition for t in trans_obj.filter(tcomm=False)]
			trans = [t.definition for t in trans_obj]

			tcomms = [t.definition for t in trans_obj.filter(tcomm=True)]
			stat_pref = [t.definition for t in trans_obj.filter(tcomm_pref=True)]

			if len(tcomms) > 0:
				preferred = [t.definition for t in trans_obj.filter(tcomm=False)]
			if not correct:
				if len(stat_pref) > 0:
					correct = stat_pref[:]
		elif type(word) == WordTranslation:
			trans_obj = word.word
			trans = [trans_obj.lemma]
			if not correct:
				correct = trans

		question_list = []

		userans_val = ''
		try:
			userans_val = db_info['answer'].strip()
		except KeyError:
			userans_val = db_info['userans']

		form = (LeksaQuestion(
					tcomms,
					stat_pref,
					preferred,
					possible,
					self.settings['transtype'],
					word,
					correct,
					tr_lemmas,
					question_list,
					userans_val,
					db_info['correct'],
					data,
					prefix=n,
					user=self.settings["user"],
					user_country=self.settings["user_country"]))
		return form, word.id

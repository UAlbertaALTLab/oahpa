# -*- coding: utf-8 -*-
import settings
from sms_drill.models import *
# from xml.dom import minidom as _dom
# from django.db.models import Q
import sys
import os
import re
# import string
import codecs

# Using django settings paths, need to make these more central.

# 
# _D = open('/dev/ttys005', 'w')
_D = open('/dev/null', 'w')


try:
	fstdir = settings.FST_DIRECTORY
except:
	fstdir = "/opt/smi/sme/bin"

try:
	lookup = settings.LOOKUP_TOOL
except:
	lookup = "/usr/local/bin/lookup"

try:
	language = settings.MAIN_LANGUAGE[0]
except:
	language = "sms"

numfst = fstdir + "/" + language + "-num.fst"


STDERR = sys.stderr
STDOUT = sys.stdout

#!/usr/bin/env python
# encoding: utf-8

""" Omorfi Daemon
	"""

import subprocess as sp
import os
import sys

def Popen(cmd, data=False, ret_err=False, ret_proc=False):
	"""
		Wrapper around subprocess Popen to save some time.
		Expects command and data, ideally data is already single unicode
		string.
	"""
	PIPE = sp.PIPE
	proc = sp.Popen(cmd.split(' '), shell=False, 
					stdout=PIPE, stderr=PIPE, stdin=PIPE)
	if data:
		if type(data) == str:
			try:
				data = data.encode('utf-8')
			except UnicodeDecodeError:
				pass
			except Exception, e:
				print >> STDERR, "omg, str"
				print >> STDERR, Exception, e
				sys.exit(2)
		if type(data) == unicode:
			try:
				data = str(data)
			except Exception, e:
				print >> STDERR, "omg, unicode"
				print >> STDERR, Exception, e
				sys.exit(2)
		kwargs = {'input': data}
	else:
		kwargs = {}

	output, err = proc.communicate(**kwargs)
	
	try:
		if err:
			raise Exception(cmd + err)
	except:
		pass

	if ret_err:
		return output, err
	else:
		return output


def FSTLookup(data, fst_file):
	gen_fst = fstdir + "/%s" % fst_file 
	# cmd = 'hfst-optimized-lookup /opt/local/share/omorfi/mor-omorfi.apertium.hfst.ol'
	cmd = lookup + " -flags mbTT -utf8 -d " + gen_fst
	
	if type(data) == list:
		data = [a.strip() for a in list(set(data)) if a.strip()]
		data = u'\n'.join(data).encode('utf-8')
	print >> STDOUT, "Generating forms in %s" % gen_fst
	try:
		lookups = Popen(cmd, data)
	except OSError:
		print >> STDERR, "Problem in command: %s" % cmd
		sys.exit(2)
	lookups = lookups.decode('utf-8')
	
	return lookups


if __name__ == "__main__":
	sys.exit(main())



class Entry:
	pass


class Paradigm:

	def __init__(self):
		self.tagset = {}
		self.paradigms = {}
		self.paradigm = []
		self.generate_data = []
		

	def handle_tags(self, tagfile, add_db):

		with open(tagfile, "r") as F:
			# Read tags, remove newlines
			tags = [a.strip() for a in F.readlines()]

		tagclass = ""
		for line in tags:
			if line.startswith("#"):
				tagclass = line.lstrip("#")
			else:
				string = line.strip().replace('*', '')
				self.tagset[string] = tagclass
				if add_db and tagclass and string:
					#print "adding " + tagclass + " " + string
					tagset, created = Tagset.objects.get_or_create(tagset=tagclass)
					pos, created = Tagname.objects.get_or_create(tagname=string, tagset=tagset)
					print "%s added to %s" % (string, tagclass)



	def read_paradigms(self, paradigmfile, tagfile, add_database):
		if not self.tagset:
			self.handle_tags(tagfile)

		fileObj = codecs.open(paradigmfile, "r", "utf-8" )
		posObj = re.compile(r'^(?:\+)?(?P<posString>[\w]+)\+.*$', re.U)
		
		while True:
			line = fileObj.readline()
			
			if not line: break
			if not line.strip(): continue
			
			matchObj = posObj.search(line)
			
			if matchObj:
				pos = matchObj.expand(r'\g<posString>')
			try:
				if not self.paradigms.has_key(pos):
					self.paradigms[pos]=[]
			except UnboundLocalError:
				print >> STDERR, ' * Could not match pos. Check format of paradigm file.'
				print >> STDERR, ' * Error on line: %s' % line
				sys.exit()
			self.paradigms[pos].append(line)

	def create_paradigm_no_gen(self, lemma, pos, baseform, wordforms):
		""" Creates paradigm objects as does create_paradigm, but using data
			stored in XML. This data is already parsed in words_install, for the
			most part, but passed off here. Best way for least work.
		""" 
		
		pos = pos.upper()
		
		if pos == 'PROP':
			pos = 'N'

		if not self.tagset:
			self.handle_tags()

		self.paradigm = []
		
		# instead of lookups, we have wordforms
		
		for wordform in wordforms:
			g = Entry()
			g.classes = {}

			lemma = lemma
			g.form, g.tags = wordform
			for t in g.tags:
				if self.tagset.has_key(t):
					tagclass = self.tagset[t]
					g.classes[tagclass] = t
			self.paradigm.append(g)
			
	def collect_gen_data(self, lemma, pos, hid, wordtype, gen_only, forms):
		"""
			Collects tags and paradigms to be passed off to the FST for generation.
			Tags and items to be generated are filtered based on following parameters
				* gen_only
				* wordtype
				* hid
			so that there is minimal overgeneration. FSTs trim some nongeneratable forms
			as well.
		"""

		pos = pos.capitalize()
		
		# if context is defined as one of these, then we only generate
		# forms that have a tag with one of the following items as a
		# substring of that tag.
		
		# E.g., context='upers' abrodh
		# abrodh	+V+Prs+Sg1	=> NO
		# abrodh	+V+Prs+Sg2	=> NO
		# abrodh	+V+Prs+Sg3	=> YES

		# contexts = {
			# 'upers': ['Sg3'],
			# '3.pers': ['Sg3', 'Du3', 'Pl3'],
			# 'pl': ['Pl1', 'Pl2', 'Pl3', 'Pl'],
			# 'sg': ['Sg'],
		# }

		# Using gen_only now
		
		if not gen_only.strip():
			gen_only = False
		else:
			gen_only = [a.strip() for a in gen_only.split(',') if a.strip()]
			# try:
				# context = contexts[context]
			# except:
				# print >> STDERR, "*** Context (%s) not found" % context.encode('utf-8')
				# context = False

		if pos.upper() == 'PROP':
			pos = 'N'

		if not self.tagset:
			self.handle_tags()

		lookups = ""
		if not hid.strip():
			hid = ""
		else:
			hid = '+' + hid
		
		# If wordtype is defined, then the wordtype is inserted after
		# the first tag element, which should be the part of speech.
		# If hid is defined simultaneously, this should not mess with that.

		if not wordtype.strip():
			wordtype = ""
		else:
			wordtype = '+' + wordtype.capitalize()

		if self.paradigms.has_key(pos):
			for a in self.paradigms[pos]:
				if wordtype.strip():
					if not wordtype in a:
						_pos, _, _rest = a.partition('+')
						tag = "%s%s+%s" % (_pos, wordtype, _rest)
				else:
					tag = a
				
				if gen_only:
					for c in gen_only:
						if c in tag:
							lookups = lookups + lemma + hid + "+" + tag
				else:
					if not lemma:
						raise TypeError
					lookups = lookups + lemma + hid + "+" + tag

		lookups += '\n\n\n'
		self.generate_data.append(lookups)

	
	def generate_all(self, dialects):		
		
		if not self.tagset:
			print >> STDERR, 'No tags generated or supplied'
			self.handle_tags()
		
		data = self.generate_data[:]
		
		# concatenate all data to be run through one gen command
		# isma-SH.restr.fst
		# isma-norm.fst
		# dialects = {'main': ('isma-norm.fst', 'Unrestricted'), etc... }
		gen_dialects = {}
		for dialect, d_data in dialects.items():
			if d_data[0]:
				gen_dialects[dialect] = d_data

		self.master_paradigm = gen_dialects.copy()
		for dialect, gen_file in gen_dialects.items():
			lookups = FSTLookup(data, fst_file=gen_file[0])
			lookup_dictionary = {}
			
			for line in lookups.split('\n\n'):
				items = line.split('\n')
				for item in items:
					result = item.split('\t')
					lemma = result[0].partition('+')[0]
					try:
						lookup_dictionary[lemma] += item + '\n'
					except KeyError:
						lookup_dictionary[lemma] = item + '\n'
		
			self.master_paradigm[dialect] = lookup_dictionary
		
		
	def get_paradigm(self, lemma, pos, forms, dialect=False, wordtype=None):
		if not dialect:
			dialect = 'main'
		
		extraforms = {}

		try:
			lines_tmp = self.master_paradigm[dialect][lemma].split('\n')
		except Exception, e:
			print >> STDERR, 'No forms generated for %s in dialect %s' % (lemma.encode('utf-8'), dialect.encode('utf-8'))
			lines_tmp = False
			if not forms:
				self.paradigm = False
				return
		if forms:
			if forms.getElementsByTagName("form"):
				form_els = forms.getElementsByTagName("form")
				for f in form_els:
					tagstring = f.getAttribute("tag")
					wordform = f.firstChild.data
					extraforms[tagstring] = wordform
					print >> STDOUT, "adding extra wordform..", wordform.encode('utf-8')
		# HIDCHANGES
		if lines_tmp:
			
			self.paradigm = []
			
			for line in lines_tmp:
				
				if not line.strip():
					continue
				else: 
					line = line.strip()
				
				# line: 
				# govledh+2+V+Ind+Prt+Pl3\tgovlin
				# lea+V+Ind+Prt+Pl3\tlij

				lem, _, rest = line.partition('+')
				# ('govledh', '+', '2+V+Ind+Prt+Pl3\tgovlin')
				# ('lea', '+', '2+V+Ind+Prt+Pl3\tlij')

				fullform = line.split('\t')[-1]
				# 'govlin'
				# '?+'
				# 'lij'

				hid_test = rest.partition('+')
				# ('2', '+', 'V+Ind+Prt+Pl3\tgovlin')
				# ('V', '+', 'Ind+Prt+Pl3\tgovlin')

				# If first element of tag is an integer, then
				# it is hid, otherwise it's just part of the tag.
				try:
					hid = int(hid_test[0])
					tag = hid_test[2]
				except ValueError:
					hid = ''
					tag = ''.join(hid_test)
				
				tag = tag.partition('\t')[0]
				# 'V+Ind+Prt+Pl3'
				# Never gets hid number, due to testing above

				if fullform.find('?') == -1:
					g = Entry()
					g.classes={}
					g.dialect = dialect
					lemma = lem
					g.form = fullform
					g.hid = hid
					g.tags = tag

					for t in g.tags.split('+'):
						if self.tagset.has_key(t):
							tagclass=self.tagset[t]
							g.classes[tagclass] = t

					# if wordtype is specified (G3, Actor, etc.,), we want only
					# these forms, otherwise we want only forms without a
					# wordtype
					if wordtype is not None:
						wordtype = wordtype.upper()
						g_wordtype = g.classes.get('Subclass', False)
						if g_wordtype:
							if wordtype == g_wordtype.upper():
								self.paradigm.append(g)
							else:
								continue
						else:
							continue
					else:
						g_wordtype = g.classes.get('Subclass', False)
						if g_wordtype:
							continue
						else:
							self.paradigm.append(g)

					if extraforms.has_key(g.tags):
						g.form = extraforms[g.tags]
				else:
					err_msg = 'No form created: %s+%s' % (lemma.encode('utf-8'), tag.encode('utf-8'))
					if dialect:
						err_msg += ' (%s)' % dialect.encode('utf-8')
					print >> STDERR, err_msg
		else:
			self.paradigm = False

		return self.paradigm

	
	def create_paradigm(self, lemma, pos, forms, dialect=False):
		
		pos = pos.capitalize()
		
		if not self.tagset:
			self.handle_tags()
		
		self.paradigm = []
		
		# TODO: is this preventing matching south sámi forms?
		# How can we do this so we don't need to constantly rewrite this to specify a new alphabet?
		
		# genObj_re = r'^(?P<lemmaString>[\wáŋčžšđŧ]+)\+(?P<tagString>[\w\+]+)[\t\s]+(?P<formString>[\wáŋčžšđŧ]*)$'
		genObj_re = r'^(?P<lemmaString>[\w]+)\+(?P<tagString>[\w\+]+)[\t\s]+(?P<formString>[\w]*)$'
		
		genObj=re.compile(genObj_re, re.U)
		lookups = ""
		
		if self.paradigms.has_key(pos):
			for a in self.paradigms[pos]:
				lookups = lookups + lemma + "+" + a
		
		# generator call
		# Moving paths up
		# fstdir = "/opt/smi/sme/bin"
		# lookup = "/usr/local/bin/lookup"

		gen_norm_fst = fstdir + "/i%s-norm.fst" % language
		
		# None of these dialects in sma. Obs! Dialects! sme-specific!!!
		# gen_gg_restr_fst = fstdir + "/isme-KJ.restr.fst"			
		# gen_kj_restr_fst = fstdir + "/isme-GG.restr.fst"			
		print >> _D, lookups.encode('utf-8')
		gen_norm_lookup = "echo \"" + lookups.encode('utf-8') + "\" | " + lookup + " -flags mbTT -utf8 -d " + gen_norm_fst
		
		# gen_gg_restr_lookup = "echo \"" + lookups.encode('utf-8') + "\" | " + lookup + " -flags mbTT -utf8 -d " + gen_gg_restr_fst
		# gen_kj_restr_lookup = "echo \"" + lookups.encode('utf-8') + "\" | " + lookup + " -flags mbTT -utf8 -d " + gen_kj_restr_fst
		
		# TODO: check where de/code is?
		lines_tmp = [a.decode('utf-8') for a in os.popen(gen_norm_lookup).readlines()]
		
		# lines_gg_restr_tmp = os.popen(gen_gg_restr_lookup).readlines()
		# lines_kj_restr_tmp = os.popen(gen_kj_restr_lookup).readlines()

		extraforms={}
		if forms:
			if forms.getElementsByTagName("form"):
				form_els = forms.getElementsByTagName("form")
				for f in form_els:
					tagstring = f.getAttribute("tag")
					wordform = f.firstChild.data
					extraforms[tagstring] = wordform
					print >> STDOUT, "adding extra wordform..", wordform

		for line in lines_tmp:
			if not line.strip(): continue
			matchObj=genObj.search(line)
			if matchObj:
				g = Entry()
				g.classes={}
				lemma = matchObj.expand(r'\g<lemmaString>')
				g.form = matchObj.expand(r'\g<formString>')
				if re.compile("\?").match(g.form): continue
				g.tags = matchObj.expand(r'\g<tagString>')
				print 'amagad: '
				print repr(g.tags)
				for t in g.tags.split('+'):
					if self.tagset.has_key(t):
						tagclass=self.tagset[t]
						g.classes[tagclass]=t
				print g.classes
				raw_input()
				self.paradigm.append(g)
				#extraforms override generated ones
				if extraforms.has_key(g.tags):
					g.form=extraforms[g.tags]

	def generate_numerals(self):
		"""
		Generate all the cardinal numbers
		Create paradigms and store to db
		"""
		print >> _D, 'generate_numerals called'
		
		# Moving paths up
		# language = "sme"
		# #fstdir = "/opt/smi/" + language + "/bin"
		# #lookup = /usr/local/bin/lookup
		# 
		# fstdir = "/Users/saara/gt/" + language + "/bin"		
		# lookup = "/Users/saara/bin/lookup"
		# 
		# numfst = fstdir + "/" + language + "-num.fst"

		for num in range(1,20):

			num_lookup = "echo \"" + str(num) + "\" | " + lookup + " -flags mbTT -utf8 -d " + numfst
			numerals = os.popen(num_lookup).readlines()

			# Take only first one.
			# Change this if needed!
			num_list=[]
			for num in numerals:
				line = num.strip()
				if line:
					nums = line.split('\t')
					num_list.append(nums[1].decode('utf-8'))
			numstring = num_list[0]

			w, created = Word.objects.get_or_create(wordid=num, lemma=numstring, pos="Num")
			w.save()

			self.create_paradigm(numstring, "Num")
			for form in self.paradigm:
				form.form = form.form.replace("#","")
				g=form.classes
				t,created=Tag.objects.get_or_create(string=form.tags,pos=g.get('Wordclass', ""),\
													number=g.get('Number',""),case=g.get('Case',""),\
													possessive=g.get('Possessive',""),grade=g.get('Grade',""),\
													infinite=g.get('Infinite',""), \
													personnumber=g.get('Person-Number',""),\
													polarity=g.get('Polarity',""),\
													tense=g.get('Tense',""),mood=g.get('Mood',""), \
													subclass=g.get('Subclass',""), \
													attributive=g.get('Attributive',""))
				
				t.save()
				form, created = Form.objects.get_or_create(fullform=form.form,tag=t,word=w)
				form.save()



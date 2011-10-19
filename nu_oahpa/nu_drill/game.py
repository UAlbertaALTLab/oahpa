# -*- coding: utf-8 -*-

from django.template import Context, loader
from nu_oahpa.nu_drill.models import *
from nu_oahpa.nu_drill.forms import *
from django.db.models import Q
from django.http import HttpResponse, Http404
from django.shortcuts import get_list_or_404, render_to_response
from random import randint
#from django.contrib.admin.views.decorators import _encode_post_data, _decode_post_data
import os,codecs,sys,re

def relax(strict):
    """ Returns a list of relaxed possibilities, making changes by relax_pairs.

    Many possibilities are generated in the event that users are
    inconsistent in terms of substituting one letter but not substituting
    another, however, *all* possibilities are not generated.

    E.g., *ryøjnesjäjja is accepted for ryöjnesjæjja
    (user types ø instead of ö consistently)

    ... but ...

      *töølledh is not accepted for töölledh
      (user mixes the two in one word)

      Similarly, directionality is included. <i> is accepted for <ï>, but
      not vice versa.

      E.g.:  *ååjmedïdh is not accepted for ååjmedidh,
      ... but ...
      *miele is accepted for mïele.
      """
    relaxed = strict
    sub_str = lambda _string, _target, _sub: _string.replace(_target, _sub)

    relax_pairs = {
        # key: value
        # key is accepted for value
        u'ø': u'ö',
        u'ä': u'æ',
        u'i': u'ï'
    }

    # Create an iterator. We want to generate as many possibilities as
    # possible (very fast), so more relaxed options are available.
    searches = relax_pairs.items()
    permutations = itertools.chain(itertools.permutations(searches))
    perms_flat = sum([list(a) for a in permutations], [])

    # Individual possibilities
    relaxed_perms = [sub_str(relaxed, R, S) for S, R in perms_flat]

    # Possibilities applied one by one
    for S, R in perms_flat:
        relaxed = sub_str(relaxed, R, S)
        relaxed_perms.append(relaxed)

    # Return list of unique possibilities
    relaxed_perms = list(set(relaxed_perms))
    return relaxed_perms
    
class Info:
    pass

class Game:

    def __init__(self, settings):
        self.form_list = []
        self.count = ""
        self.score = ""
        self.comment = ""
        self.settings = settings
        self.all_correct = ""
        self.show_correct = 0
        self.num_fields = 6
        self.global_targets = {}

        if not self.settings.has_key('gametype'):
            self.settings['gametype'] = "bare"

        if not self.settings.has_key('dialect'):
            self.settings['dialect'] = "GG"

        if self.settings.has_key('semtype'):
            if self.settings['semtype'] == 'all':
                self.settings['semtype']=self.settings['allsem']
            else:
                semtype=self.settings['semtype'][:]
                self.settings['semtype']=[]
                self.settings['semtype'].append(semtype)

        
    def new_game(self):
        self.form_list = []
        word_ids = []
        i=1
        num=0
        while i < self.num_fields and num<30:
            db_info = {}
            db_info['userans'] = ""
            db_info['correct'] = ""

            errormsg = self.get_db_info(db_info)
            if errormsg and errormsg=="error":
                i=i+1
                continue
            form, word_id = self.create_form(db_info, i, 0)

            # Do not generate same question twice
            if word_id:
                num=num+1
                if word_id in set(word_ids): continue
                else: word_ids.append(word_id)

            self.form_list.append(form)
            i=i+1

            
        if not self.form_list:
            # No questions found, so the quiz_id must have been bad.
            raise Http404('Invalid quiz id.')

    def search_info(self, reObj, string, value, words, type):

        matchObj=reObj.search(string) 
        if matchObj:
            syntax = matchObj.expand(r'\g<syntaxString>')
            if not words.has_key(syntax):
                words[syntax] = {}

            words[syntax][type] = value

        return words


    def check_game(self, data=None):

        db_info = {}

        question_tagObj=re.compile(r'^question_tag_(?P<syntaxString>[\w\-]*)$', re.U)
        question_wordObj=re.compile(r'^question_word_(?P<syntaxString>[\w\-]*)$', re.U)
        question_fullformObj=re.compile(r'^question_fullform_(?P<syntaxString>[\w\-]*)$', re.U)
        answer_tagObj=re.compile(r'^answer_tag_(?P<syntaxString>[\w\-]*)$', re.U)
        answer_wordObj=re.compile(r'^answer_word_(?P<syntaxString>[\w\-]*)$', re.U)
        answer_fullformObj=re.compile(r'^answer_fullform_(?P<syntaxString>[\w\-]*)$', re.U)
        targetObj=re.compile(r'^target_(?P<syntaxString>[\w\-]*)$', re.U)

        # Collect all the game targets as global variables
        self.global_targets = {}
           
        # If POST data was data check, regenerate the form using ids.
        for n in range (1, self.num_fields):
            db_info = {}
            qwords = {}
            awords = {}
            tmpawords = {}

            for d, value in data.items():
                if d.count(str(n) + '-')>0:
                    d = d.lstrip(str(n) + '-')
                    qwords = self.search_info(question_tagObj, d, value, qwords, 'tag')
                    qwords = self.search_info(question_wordObj, d, value, qwords, 'word')
                    qwords = self.search_info(question_fullformObj, d, value, qwords, 'fullform')

                    tmpawords = self.search_info(answer_tagObj, d, value, tmpawords, 'tag')
                    tmpawords = self.search_info(answer_wordObj, d, value, tmpawords, 'word')
                    tmpawords = self.search_info(answer_fullformObj, d, value, tmpawords, 'fullform')

                    self.global_targets = self.search_info(targetObj, d, value, self.global_targets, 'target')

                    db_info[d] = value

            
            for syntax in qwords.keys():
                if qwords[syntax].has_key('fullform'):
                    qwords[syntax]['fullform'] = [ qwords[syntax]['fullform']]

            for syntax in tmpawords.keys():
                awords[syntax] = []
                info = {}
                if tmpawords[syntax].has_key('word'):
                    info['word'] = tmpawords[syntax]['word']
                    if tmpawords[syntax].has_key('tag'):
                        info['tag'] = tmpawords[syntax]['tag']
                    if tmpawords[syntax].has_key('fullform'):
                        info['fullform'] = [ tmpawords[syntax]['fullform']]
                            
                    awords[syntax].append(info)
            db_info['awords'] = awords
            db_info['qwords'] = qwords
            db_info['global_targets'] = self.global_targets

            new_db_info = {}

            # Generate possible answers for contextual Morfa.
            if self.settings.has_key('gametype') and self.settings['gametype'] == 'context':
                new_db_info = self.get_db_info(db_info)
            if not new_db_info:
                new_db_info = db_info
            form, word_id = self.create_form(new_db_info, n, data)
            if form:
                self.form_list.append(form)
                
    def get_score(self, data):

        # Add correct forms for words to the page
        if "show_correct" in data:
            self.show_correct = 1
            for form in self.form_list:
                form.set_correct()
                self.count=2

        # Count correct answers:
        self.all_correct=0
        self.score=""
        self.comment=""
        i=0
        for form in self.form_list:
            if form.error == "correct":
                i=i+1
                if i == len(self.form_list):
                    self.all_correct=1

        if self.show_correct or self.all_correct:
            self.score = self.score.join([`i`, "/", `len(self.form_list)`])

        if (self.show_correct or self.all_correct) and not self.settings['gametype']=='qa' :
            if i==2: i=3
            if i==1: i=2
            if self.settings.has_key('language'):
                language = self.settings['language']
                if language == "no" : language = "nob"
                if language == "fi" : language = "fin"
                if language == "en" : language = "eng"
                
                com_count = Comment.objects.filter(Q(level=i) & Q(lang=language)).count()
                if com_count > 0:
                    self.comment = Comment.objects.filter(Q(level=i) & Q(lang=language))[randint(0,com_count-1)].comment


class BareGame(Game):

    casetable = {'NOMPL' : 'Nom', 'ATTR':'Attr', 'N-ILL':'Ill', 'N-ESS':'Ess', 'N-GEN':'Gen', \
                 'N-LOC':'Loc', 'N-ACC':'Acc', 'N-COM':'Com'}

    def get_baseform(self, word_id, tag):

        basetag=None
        if tag.pos=="N" or tag.pos=="A" or tag.pos=="Num":
            if tag.number and tag.case != "Nom":
                tagstring = tag.pos + "+" + tag.number + "+Nom"
            else:
                tagstring = tag.pos + "+Sg" + "+Nom"
            if Form.objects.filter(Q(word__pk=word_id) & Q(tag__string=tagstring)).count()>0:
                basetag = Tag.objects.filter(string=tagstring)[0]

        if tag.pos=="V":
            tagstring = "V+Inf"
            if Form.objects.filter(Q(word__pk=word_id) & Q(tag__string=tagstring)).count()>0:
                basetag = Tag.objects.filter(string=tagstring)[0]

        return basetag

    def get_db_info(self, db_info):

        dialect = self.settings['dialect']
        if self.settings.has_key('pos'):
            pos = self.settings['pos']

        syll=""
        case=""
        books=[]
        adjcase=""
        grade=""
        mood=""
        tense=""
        attributive =""

        if self.settings.has_key('syll'):
            syll = self.settings['syll']
        if self.settings.has_key('case'):
            case=self.settings['case']
        if self.settings.has_key('book'):
            books=self.settings['book']
        if self.settings.has_key('adjcase'):
            adjcase=self.settings['adjcase']
        if self.settings.has_key('num_bare'):
            num_bare=self.settings['num_bare']
        if self.settings.has_key('num_level'):
            num_level=self.settings['num_level']
        if self.settings.has_key('grade'):
            grade=self.settings['grade']

        if pos == "N":
            case = self.casetable[case]
        else:
            if pos=="A":
                case = self.casetable[adjcase]
            else:
                if pos=="Num":
                    case = self.casetable[num_bare]
                else:
                    if pos=="V":
                        case = ""                    
        
        if pos == "V" and self.settings.has_key('vtype'):
            if self.settings['vtype'] == "PRS":
                mood = "Ind"
                tense = "Prs"
            if self.settings['vtype'] == "PRT":
                mood = "Ind"
                tense = "Prt"
            if self.settings['vtype'] == "COND":
                mood = "Cond"
                tense = "Prs"
            if self.settings['vtype'] == "IMPRT":
                mood = "Imprt"
                tense = "Prs"
            if self.settings['vtype'] == "POT":
                mood = "Pot"
                tense = "Prs"

        if case=="Attr":
            attributive = "Attr"
            case =""

        if grade=="POS": grade = ""
        if grade=="COMP": grade = "Comp"
        if grade=="SUPERL": grade = "Superl"
        
        number = ["Sg","Pl",""]
        if case=="Nom": number = ["Pl"]
        maxnum=20
        i=0
        
        #print syll, books, pos, case, tense, mood, attributive, grade

        tag_count=Tag.objects.filter(Q(pos=pos) & Q(possessive="") & Q(case=case) & Q(tense=tense) & Q(mood=mood) & ~Q(personnumber="ConNeg") & Q(attributive=attributive) & Q(grade=grade) & Q(number__in=number)).count()
        if tag_count < 1: raise Http404(pos, case, tense, mood, attributive, grade, number)
        while i<maxnum:
            i=i+1
            tag = Tag.objects.filter(Q(pos=pos) & Q(possessive="") & Q(case=case) & Q(tense=tense) & Q(mood=mood) & ~Q(personnumber="ConNeg") & Q(attributive=attributive) & Q(grade=grade) & Q(number__in=number))[randint(0,tag_count-1)]

            tag_id = tag.id
            if self.settings['pos'] == "Num":
                if self.settings.has_key('num_level') and str(self.settings['num_level'])=="1":
                    smallnum = ["1","2","3","4","5","6","7","8","9","10"]
                    w_count=Word.objects.filter(Q(pos=pos) & Q(presentationform__in=smallnum)).count()
                    word_id=Word.objects.filter(Q(pos=pos)& Q(presentationform__in=smallnum))[randint(0,w_count-1)].id
                else:
                    w_count=Word.objects.filter(Q(pos=pos)).count()
                    word_id=Word.objects.filter(Q(pos=pos))[randint(0,w_count-1)].id
            else:
                w_count=Word.objects.filter(Q(pos=pos) & Q(stem__in=syll) & Q(source__name__in=books) &\
                                            Q(dialects__dialect=dialect)).count()
                word_id=Word.objects.filter(Q(pos=pos) & Q(stem__in=syll) & Q(source__name__in=books) &\
                                            Q(dialects__dialect=dialect))[randint(0,w_count-1)].id
                
            form_count = Form.objects.filter(Q(word__pk=word_id) & Q(tag__pk=tag_id)).count()

            basefound = self.get_baseform(word_id, tag)

            if word_id and form_count>0 and basefound:
                db_info['word_id'] = word_id
                db_info['tag_id'] = tag_id
                return


    def create_form(self, db_info, n, data=None):

        dialect = self.settings['dialect']
        language = self.settings['language']
        if not db_info.has_key('word_id'):
            return None, None            
        word_id = db_info['word_id']
        tag_id = db_info['tag_id']

        tag = Tag.objects.get(Q(id=tag_id))
        basetag = self.get_baseform(word_id, tag)

        form_list=Form.objects.filter(Q(word__pk=word_id) & Q(tag__pk=tag_id))
        if not form_list:
            return HttpResponse("No forms found.")
        dial_form_list = form_list.filter(Q(dialects__dialect=dialect))
        if dial_form_list:
            correct = dial_form_list[0]
        else:
            correct = form_list[0]
                
        word = Word.objects.get(Q(id=word_id))

        baseform_list = Form.objects.filter(Q(word__pk=word_id) & Q(tag=basetag))
        dial_baseform_list = baseform_list.filter(Q(dialects__dialect=dialect))
        if dial_baseform_list:
            baseform = dial_baseform_list[0]
        else:
            baseform = baseform_list[0]

        #print ">>> language: ", language
        #self.settings['transtype'] == "nobsme":
        #the parameter 'translations' seems to suprefuous here
        translations=word.translations2nob.all().values_list('lemma',flat=True)

        fullforms = form_list.values_list('fullform',flat=True)
        morph = (MorfaQuestion(word, tag, baseform, correct, fullforms, translations, "", dialect, language, db_info['userans'], db_info['correct'], data, prefix=n))
        return morph, word_id


class NumGame(Game):

    def get_db_info(self, db_info):

        numeral=""
        num_list = []

        random_num = randint(1, int(self.settings['maxnum']))

        print self.settings['gametype']
        if self.settings['gametype'] == "ord":
            db_info['numeral_id'] = str(random_num) + "."
        else:
            db_info['numeral_id'] = str(random_num)
        return db_info

    def generate_forms(self, forms, fstfile):
        import subprocess
        from threading import Timer

        fstdir="/opt/smi/sme/bin"
        # replaced variable language by sme
        lookup = "/usr/local/bin/lookup"
        gen_norm_fst = fstdir + "/" + fstfile
        try:
            open(gen_norm_fst)
        except IOError:
            raise Http404("File %s does not exist." % gen_norm_fst)

        gen_norm_command = [lookup, "-flags", "mbTT", "-utf8",  "-d", gen_norm_fst]

        num_proc = subprocess.Popen(gen_norm_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        def kill_proc(proc=num_proc):
            try:
                proc.kill()
                raise Http404("Process for %s took too long." % ''.join(gen_norm_command))
            except OSError:
                pass
            return

        t = Timer(5, kill_proc)
        t.start()
        output, err = num_proc.communicate(forms)

        return output, err
                
        
    def create_form(self, db_info, n, data=None):

        dialect = self.settings['dialect']
        if self.settings['gametype'] == "ord":
            language="sme"
        else:
            language=self.settings['numlanguage']
        numstring =""
        # Add generator call here
        #fstdir="/Users/saara/gt/" + language + "/bin"        
        #lookup ="/Users/saara/bin/lookup"
        
        fstdir="/opt/smi/" + language + "/bin"
        lookup = "/usr/local/bin/lookup"
        gen_norm_fst = fstdir + "/" + language + "-num.fst"

        gen_norm_lookup = "echo " + db_info['numeral_id'] + " | " + lookup + " -flags mbTT -utf8 -d " + gen_norm_fst

        num_tmp = os.popen(gen_norm_lookup).readlines()
        num_list=[]
        for num in num_tmp:
            line = num.strip()
            line = line.replace(' ','')
            if line:
                nums = line.split('\t')
                num_list.append(nums[1].decode('utf-8'))
        numstring = num_list[0]
        form = (NumQuestion(db_info['numeral_id'], numstring, num_list, self.settings['numgame'], db_info['userans'], db_info['correct'], data, prefix=n))

        return form, numstring

class Clock(NumGame):

    def get_db_info(self, db_info):
        from random import choice

        hour = str(randint(0, 23))
        mins = '00'

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


    def create_form(self, db_info, n, data=None):
        if self.settings['gametype'] in ["kl1", "kl2", "kl3"]:
            language = 'sme'

            numstring = ""

            fstfile = "iclock-sme.fst"
            q, a = 0, 1

        # # need to extract accepted and nonaccepted, using
        # # an inverted int-clock-sma.fst

        lookupstr = "%s\n\n%s+Use/NG\n" % (db_info['numeral_id'], db_info['numeral_id'])

        # # lookup = "%s\n" % db_info['numeral_id']
        output, err = self.generate_forms(lookupstr,fstfile)

        norm, allnum = output.split('\n\n')[0:2]

        norm_list = []
        for num in norm.splitlines():
            line = num.strip()
            if line:
                nums = line.split('\t')
                norm_list.append(nums[a].decode('utf-8'))

        allnum_list = []
        for num in allnum.splitlines():
            line = num.strip()
            if line:
                if line.find('?') == -1:
                    nums = line.split('\t')
                    allnum_list.append(nums[a].decode('utf-8'))

        allnum_list += norm_list

        try:
            numstring = norm_list[0]
        except IndexError:
            error = "Morfa.Clock.create_form: Database is improperly loaded, or Numra is unable to look up words."
            raise Http404(error)

        form = (KlokkaQuestion(
                    numeral=db_info['numeral_id'],
                    num_string=numstring,
                    present_list=norm_list,
                    accept_list=allnum_list,
                    gametype=self.settings['numgame'],
                    userans_val=db_info['userans'],
                    correct_val=db_info['correct'],
                    data=data,
                    prefix=n)
                )

        return form, numstring
    
class QuizzGame(Game):

    def get_db_info(self, db_info):

        dialect=self.settings['dialect']
        books=self.settings['book']
        semtypes=self.settings['semtype']
        frequency=self.settings['frequency']
        geography=self.settings['geography']

        if semtypes.count("PLACE-NAME-LEKSA")==0:
            frequency=['']
            geography=['']

        maxnum=20
        i=0
        while i<maxnum:
            i=i+1
            
            QUERY =    Q(frequency__in=frequency) & \
                    Q(geography__in=geography)
            
            if self.settings['transtype'].startswith("sme"):            WordObj = Word ; QUERY = QUERY & Q(dialects__dialect=dialect)
            elif self.settings['transtype'] == "nobsme":                WordObj = Wordnob
            elif self.settings['transtype'] == "finsme":                WordObj = Wordfin
            elif self.settings['transtype'] == "swesme":                 WordObj = Wordswe
            elif self.settings['transtype'] == "engsme":                 WordObj = Wordeng
            elif self.settings['transtype'] == "deusme":                 WordObj = Worddeu
            else:                                                        print "Empty else branch!"
            
            if self.settings['book'].count('all') > 0:
                if WordObj != Word:
                    QUERY = QUERY & Q(word__semtype__semtype__in=semtypes)
                else:
                    QUERY = QUERY & Q(semtype__semtype__in=semtypes)

            else:
                semtypes = self.settings['allsem']
                QUERY = QUERY & Q(source__name__in=books)

            words = WordObj.objects.filter(QUERY)
            w_count = words.count()

            # TODO: possibility here is that if there are no words to
            # change the query so it is relative to Word, and return
            # Wordnob/Wordfin words. Problem is that it appears that
            # Word and Wordnob objects have different semantic sets from
            # eachother.

            try:
                random_word = words.order_by('?')[0]
            except IndexError:
                errorstr = 'Query resulted in no words.\n'
                errorstr += str(QUERY)
                raise Http404(errorstr)

            word_id=random_word.id
            if self.settings['transtype'] == "smenob":  
                translations=random_word.translations2nob.all()
            if self.settings['transtype'] == "smefin":  
                translations=random_word.translations2fin.all()
            if self.settings['transtype'] == "smeswe":  
                translations=random_word.translations2swe.all()
            if self.settings['transtype'] == "smeeng":  
                translations=random_word.translations2eng.all()
            if self.settings['transtype'] == "smedeu":  
                translations=random_word.translations2deu.all()
            if self.settings['transtype'].endswith("sme"):  
                translations=random_word.translations.all()

            
            if translations.count()>0:
                db_info['word_id'] = word_id
                db_info['question_id'] = ""
                return db_info

    def create_form(self, db_info, n, data=None):

        dialect = self.settings['dialect']
        tr_lemmas = []

        word_id = db_info['word_id']

        if self.settings['transtype'] == "smenob":
            word=Word.objects.get(Q(id=word_id))
            synwords = Word.objects.filter(lemma=word.lemma)
            # find synonymous words and pick them to the translations
            for s in synwords:
                translations=s.translations2nob.all()
                trs = translations.values_list('lemma',flat=True)
                for t in trs:
                    tr_lemmas.append(t)
                    
        elif self.settings['transtype'] == "smefin":
            word=Word.objects.get(Q(id=word_id))
            synwords = Word.objects.filter(lemma=word.lemma)
            # find synonymous words and pick them to the translations
            for s in synwords:
                translations=s.translations2fin.all()
                trs = translations.values_list('lemma',flat=True)
                for t in trs:
                    tr_lemmas.append(t)
                    
        elif self.settings['transtype'] == "smeswe":
            word=Word.objects.get(Q(id=word_id))
            synwords = Word.objects.filter(lemma=word.lemma)
            # find synonymous words and pick them to the translations
            for s in synwords:
                translations=s.translations2swe.all()
                trs = translations.values_list('lemma',flat=True)
                for t in trs:
                    tr_lemmas.append(t)
                    
        elif self.settings['transtype'] == "smeeng":
            word=Word.objects.get(Q(id=word_id))
            synwords = Word.objects.filter(lemma=word.lemma)
            # find synonymous words and pick them to the translations
            for s in synwords:
                translations=s.translations2eng.all()
                trs = translations.values_list('lemma',flat=True)
                for t in trs:
                    tr_lemmas.append(t)
                    
        elif self.settings['transtype'] == "smedeu":
            word=Word.objects.get(Q(id=word_id))
            synwords = Word.objects.filter(lemma=word.lemma)
            # find synonymous words and pick them to the translations
            for s in synwords:
                translations=s.translations2deu.all()
                trs = translations.values_list('lemma',flat=True)
                for t in trs:
                    tr_lemmas.append(t)
                    
        elif self.settings['transtype'] == "nobsme":
            word=Wordnob.objects.get(id=word_id)
            # find synonymous words and pick them to the translations
            synwords = Wordnob.objects.filter(lemma=word.lemma)
            for s in synwords:
                translations=s.translations.all()
                trs = translations.values_list('lemma',flat=True)
                for t in trs:
                    tr_lemmas.append(t)
                    
        elif self.settings['transtype'] == "finsme":
            word=Wordfin.objects.get(id=word_id)
            # find synonymous words and pick them to the translations
            synwords = Wordfin.objects.filter(lemma=word.lemma)
            for s in synwords:
                translations=s.translations.all()
                trs = translations.values_list('lemma',flat=True)
                for t in trs:
                    tr_lemmas.append(t)
                    
        elif self.settings['transtype'] == "swesme":
            word=Wordswe.objects.get(id=word_id)
            # find synonymous words and pick them to the translations
            synwords = Wordswe.objects.filter(lemma=word.lemma)
            for s in synwords:
                translations=s.translations.all()
                trs = translations.values_list('lemma',flat=True)
                for t in trs:
                    tr_lemmas.append(t)
                    
        elif self.settings['transtype'] == "engsme":
            word=Wordeng.objects.get(id=word_id)
            # find synonymous words and pick them to the translations
            synwords = Wordeng.objects.filter(lemma=word.lemma)
            for s in synwords:
                translations=s.translations.all()
                trs = translations.values_list('lemma',flat=True)
                for t in trs:
                    tr_lemmas.append(t)
                    
        elif self.settings['transtype'] == "deusme":
            word=Worddeu.objects.get(id=word_id)
            # find synonymous words and pick them to the translations
            synwords = Worddeu.objects.filter(lemma=word.lemma)
            for s in synwords:
                translations=s.translations.all()
                trs = translations.values_list('lemma',flat=True)
                for t in trs:
                    tr_lemmas.append(t)
        else:
            print "crap"


        correct = ""
        if self.settings['transtype'].endswith("sme"):
            dial_trans = word.translations.filter(dialects__dialect=dialect)
            if dial_trans:
                correct = dial_trans[0].lemma
            if not correct: correct = word.translations.all()[0].lemma

        if self.settings['transtype'] == "smenob":
            trans =  word.translations2nob.all()[0].lemma
            if not correct: correct = word.translations2nob.all()[0].lemma
            
        if self.settings['transtype'] == "smefin":
            trans =  word.translations2fin.all()[0].lemma
            if not correct: correct = word.translations2fin.all()[0].lemma
            
        if self.settings['transtype'] == "smeswe":
            trans =  word.translations2swe.all()[0].lemma
            if not correct: correct = word.translations2swe.all()[0].lemma
            
        if self.settings['transtype'] == "smeeng":
            trans =  word.translations2eng.all()[0].lemma
            if not correct: correct = word.translations2eng.all()[0].lemma
            
        if self.settings['transtype'] == "smedeu":
            trans =  word.translations2deu.all()[0].lemma
            if not correct: correct = word.translations2deu.all()[0].lemma

        question_list=[]
        
        form = (QuizzQuestion(self.settings['transtype'], word, correct, tr_lemmas, question_list, db_info['userans'], db_info['correct'], data, prefix=n))

        return form, word.id


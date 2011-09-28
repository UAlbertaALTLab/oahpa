# -*- coding: utf-8 -*-

from settings import *
from drill.models import Feedback,Feedbackmsg,Feedbacktext,Dialect,Comment
from xml.dom import minidom as _dom
from django.db.models import Q
import sys
import re
import string
import codecs

class Entry:
    pass

class Feedback_install:

    def __init__(self):
        self.tagset = {}
        self.paradigms = {}
        self.dialects = ["KJ","GG"]

    def read_messages(self,infile):

        xmlfile=file(infile)
        tree = _dom.parse(infile)
        lex = tree.getElementsByTagName("messages")[0]
        lang = lex.getAttribute("xml:lang")        

        for el in tree.getElementsByTagName("message"):
            mid=el.getAttribute("id")
            message = el.firstChild.data
            print message            
            fm, created = Feedbackmsg.objects.get_or_create(msgid=mid)
            fm.save()

            fmtext, created=Feedbacktext.objects.get_or_create(language=lang,feedbackmsg=fm)
            fmtext.message=message
            fmtext.save()

    def set_null(self):

        feedbacks=Feedback.objects.filter(stem='empty')
        for f in feedbacks:
            f.stem=""
            f.save()
        feedbacks=Feedback.objects.filter(gradation='empty')
        for f in feedbacks:
            f.gradation=""
            f.save()
        feedbacks=Feedback.objects.filter(diphthong='empty')
        for f in feedbacks:
            f.diphthong=""
            f.save()
        feedbacks=Feedback.objects.filter(rime='empty')
        for f in feedbacks:
            f.rime=""
            f.save()
        feedbacks=Feedback.objects.filter(soggi='empty')
        for f in feedbacks:
            f.soggi=""
            f.save()
        feedbacks=Feedback.objects.filter(case2='empty')
        for f in feedbacks:
            f.case2=""
            f.save()
        feedbacks=Feedback.objects.filter(number='empty')
        for f in feedbacks:
            f.number=""
            f.save()
        feedbacks=Feedback.objects.filter(personnumber='empty')
        for f in feedbacks:
            f.personnumber=""
            f.save()
        feedbacks=Feedback.objects.filter(tense='empty')
        for f in feedbacks:
            f.tense=""
            f.save()
        feedbacks=Feedback.objects.filter(mood='empty')
        for f in feedbacks:
            f.mood=""
            f.save()
        feedbacks=Feedback.objects.filter(grade='empty')
        for f in feedbacks:
            f.grade=""
            f.save()
        feedbacks=Feedback.objects.filter(attrsuffix='empty')
        for f in feedbacks:
            f.attrsuffix=""
            f.save()
        feedbacks=Feedback.objects.filter(attributive='empty')
        for f in feedbacks:
            f.attributive=""
            f.save()
    
    def insert_feedback(self,cursor,pos,stem,diphthong,gradation,rime,soggi,case,number,personnumber="empty",tense="empty",mood="empty",attributive="empty",grade="empty",attrsuffix="empty"):
        #print pos, stem, diphthong, gradation, rime, soggi,case,number,personnumber,tense,mood,grade
        
        cursor.execute("INSERT INTO nu_oahpa.nu_drill_feedback (pos,stem,diphthong,gradation,rime,soggi,case2,number,personnumber,tense,mood,attributive,grade,attrsuffix) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE pos=%s", (pos,stem,diphthong,gradation,rime,soggi,case,number,personnumber,tense,mood,attributive,grade,attrsuffix,pos))

    def read_feedback(self, infile, wordfile):

        from django.db import connection
        print infile
        print wordfile

        wordfile=file(wordfile)
        wordtree = _dom.parse(wordfile)

        # Find out different values for variables.
        # Others can be listed, but soggi is searched at the moment.
        rimes={}
        gradations={}
        attrsuffixs={}
        compsuffixs={}
        soggis={}
        for el in wordtree.getElementsByTagName("stem"):
            if el.getAttribute("rime"):
                rime = el.getAttribute("rime")
                if rime=="0": rime = "norime"
                rimes[rime] = 1
            if el.getAttribute("gradation"):
                gradation = el.getAttribute("gradation")
                gradations[gradation] = 1
            if el.getAttribute("attrsuffix"):
                attrsuffix = el.getAttribute("attrsuffix")
                if attrsuffix=="0": attrsuffix = "noattr"
                attrsuffixs[attrsuffix] = 1
            if el.getAttribute("compsuffix"):
                compsuffix = el.getAttribute("compsuffix")
                if compsuffix=="0": compsuffix = "nocomp"
                compsuffixs[compsuffix] = 1
            if el.getAttribute("soggi"):
                soggi = el.getAttribute("soggi")
                soggis[soggi] = 1
		
        soggis['empty'] = 1
        attrsuffixs["noattr"] = 1
        compsuffixs["empty"] = 1
        rimes["norime"] = 1

        diphthongs = ["yes","no"]
        stems = ["bisyllabic","trisyllabic","contracted"]
        grades = ["Comp","Superl","Pos"]
        cases = ["Acc", "Gen", "Ill","Loc","Com","Ess","Nom"]
        numbers = ["Sg","Pl"]
        tenses = ["Prs","Prt"]
        moods = ["Ind","Cond","Pot","Imprt"]
        personnumbers = ["Sg1","Sg2","Sg3","Du1","Du2","Du3","Pl1","Pl2","Pl3"]

        messages=[]
        print rimes.keys()
        print soggis.keys()
        print gradations.keys()
        print compsuffixs.keys()
        print attrsuffixs.keys()
        print grades
        print cases
        print numbers 
        print diphthongs

		
        xmlfile=file(infile)
        tree = _dom.parse(infile)

        fb = tree.getElementsByTagName("feedback")[0]
        pos = fb.getAttribute("pos")
        if pos:
            print "Deleting old feedbacks for pos", pos
            oldfs = Feedback.objects.filter(pos=pos)			
            for f in oldfs:
                f.delete()				
        stem_messages = {}
        gradation_messages = {}

        if pos=="V":
            rimes["empty"] = 1	
            diphthongs.append("empty")
        if pos=="Num":
            rimes["empty"] = 1	
            diphthongs.append("empty")

        cursor = connection.cursor()                        

        wordforms = tree.getElementsByTagName("stems")[0]
        for el in wordforms.getElementsByTagName("stem"):
            feedback = None
            stem =""
            diphthong =""
            rime =""
            gradation=""
            soggi =""
            attrsuffix =""

            ftempl = Entry()

            ftempl.pos = pos

            if el.getAttribute("class"):
                stem=el.getAttribute("class")
                if stem: ftempl.stem = [ stem ]
            if not stem:  ftempl.stem = stems

            if el.getAttribute("gradation"):
                gradation=el.getAttribute("gradation")
                if gradation: ftempl.gradation = [ gradation ]
            if not gradation: ftempl.gradation = gradations.keys()
                
            if el.getAttribute("diphthong"):
                diphthong=el.getAttribute("diphthong")
                if diphthong: ftempl.diphthong = [ diphthong ]
            if not diphthong: ftempl.diphthong = diphthongs

            if el.getAttribute("soggi"):
                soggi=el.getAttribute("soggi")
                if soggi: ftempl.soggi = [ soggi ]
            if not soggi: ftempl.soggi = soggis.keys()

            if el.getAttribute("attrsuffix"):
                attrsuffix=el.getAttribute("attrsuffix")
                if attrsuffix: ftempl.attrsuffix = [ attrsuffix ]
            if not attrsuffix: ftempl.attrsuffix = attrsuffixs.keys()

            if el.getAttribute("rime"):
                rime=el.getAttribute("rime")
                if rime:
                    if rime=="0": rime = "norime"
                    ftempl.rime = [ rime ]
            if not rime: ftempl.rime = rimes.keys()

            msgs = el.getElementsByTagName("msg")
            for mel in msgs:

                f = Entry()

                case = ""
                number = ""
                personnumber = ""
                tense = ""
                mood = ""
                grade = ""
                attributive = ""

                f.pos = ftempl.pos[:]
                f.stem = ftempl.stem[:]
                f.gradation = ftempl.gradation[:]
                f.diphthong = ftempl.diphthong[:]
                f.soggi = ftempl.soggi[:]
                f.rime = ftempl.rime[:]
                f.attrsuffix = ftempl.attrsuffix[:]
                f.dialects = self.dialects[:]
				
                msgid = mel.firstChild.data
                #print "Message id", msgid
                f.msgid = msgid

                if el.getAttribute("attribute"):
                    attributive=el.getAttribute("attribute")
                    if attributive: f.attributive = [ 'Attr' ]
                else: f.attributive = ['Attr', 'NoAttr']
                
                if mel.getAttribute("case"):
                    case=mel.getAttribute("case")
                    if case: f.case = [ case ]
                    # Since noattr is not marked, case entails noattr.
                    f.attributive = [ 'NoAttr' ]
                if not case: f.case = cases

                if mel.getAttribute("number"):
                    number=mel.getAttribute("number")
                    if number: f.number = [ number ]
                if not number: f.number = numbers

                if mel.getAttribute("personnumber"):
                    personnumber=mel.getAttribute("personnumber")
                    if personnumber: f.personnumber = [ personnumber ]
                if not personnumber: f.personnumber = personnumbers

                if mel.getAttribute("tense"):
                    tense=mel.getAttribute("tense")
                    if tense: f.tense = [ tense ]
                if not tense: f.tense = tenses

                if mel.getAttribute("mood"):
                    mood=mel.getAttribute("mood")
                    if mood: f.mood = [ mood ]
                if not mood: f.mood = moods

                if mel.getAttribute("grade"):
                    grade=mel.getAttribute("grade")
                    if grade: f.grade = [ grade ]
                if not grade: f.grade = grades

                if mel.getAttribute("dialect"):
                    dialect=mel.getAttribute("dialect")
                    if dialect:
                        invd=dialect.lstrip("NOT-")
                        f.dialects.remove(invd)

                messages.append(f)


        for f in messages:
            print f.msgid
            msgs = Feedbackmsg.objects.filter(msgid=f.msgid)
            dialects = Dialect.objects.filter(dialect__in=f.dialects)

            if f.pos == "N" or pos=="A" or pos=="Num":
                for stem in f.stem:
                    for gradation in f.gradation:
                        for diphthong in f.diphthong:
                            for rime in f.rime:
                                for soggi in f.soggi:
                                    if f.pos == "A":
                                        for grade in f.grade:
                                            for attributive in f.attributive:
                                                if attributive == 'Attr':
                                                    # Attributive forms: no case inflection.
                                                    for attrsuffix in f.attrsuffix:
                                                        case="empty"
                                                        number="empty"
                                                        self.insert_feedback(cursor,pos,stem,diphthong,gradation,rime,soggi,case,number,'empty','empty','empty','Attr',grade,attrsuffix)
                                                        f2, created=Feedback.objects.get_or_create(stem=stem,\
                                                                                                   diphthong=diphthong,\
                                                                                                   gradation=gradation,\
                                                                                                   rime=rime,\
                                                                                                   attributive='Attr',\
                                                                                                   attrsuffix=attrsuffix,\
                                                                                                   pos=pos,\
                                                                                                   number=number,\
                                                                                                   grade=grade,\
                                                                                                   soggi=soggi)
                                                        if msgs:
                                                            f2.messages.add(msgs[0])
                                                        else : print "No messages found:", f.msgid
                                                        for d in dialects:
                                                            f2.dialects.add(d)
                                                        f2.save()
                                    
                                                else:
                                                    for case in f.case:
                                                        #essive without number inflection
                                                        if case == "Ess":
                                                            number="empty"
                                                            self.insert_feedback(cursor,pos,stem,diphthong,gradation,rime,soggi,case,number,'empty','empty','empty','NoAttr',grade)
                                                            f2, created=Feedback.objects.get_or_create(stem=stem,\
                                                                                                       diphthong=diphthong,\
                                                                                                       gradation=gradation,\
                                                                                                       rime=rime,\
                                                                                                       attributive='NoAttr',\
                                                                                                       pos=pos,\
                                                                                                       number=number,\
                                                                                                       case2=case,\
                                                                                                       grade=grade,\
                                                                                                       soggi=soggi)
                                                            if msgs:
                                                                f2.messages.add(msgs[0])
                                                            else : print "No messages found:", f.msgid 
                                                            for d in dialects:
                                                                f2.dialects.add(d)

                                                            f2.save()
                                                            
                                                        else:
                                                            for number in f.number:
                                                                self.insert_feedback(cursor,pos,stem,diphthong,gradation,rime,soggi,case,number,'empty','empty','empty','NoAttr',grade)
                                                                f2, created=Feedback.objects.get_or_create(stem=stem,\
                                                                                                           diphthong=diphthong,\
                                                                                                           gradation=gradation,\
                                                                                                           rime=rime,\
                                                                                                           attributive='NoAttr',\
                                                                                                           pos=pos,\
                                                                                                           case2=case,\
                                                                                                           number=number, \
                                                                                                           grade=grade,\
                                                                                                           soggi=soggi)
                                                                if msgs:
                                                                    f2.messages.add(msgs[0])
                                                                else : print "No messages found:", f.msgid 
                                                                for d in dialects:
                                                                    f2.dialects.add(d)

                                                                f2.save()
                                    if f.pos == "N" or f.pos=="Num":
                                        for case in f.case:
                                            # Essive: no number inflection
                                            if case == "Ess":
                                                number="empty"
                                                self.insert_feedback(cursor,pos,stem,diphthong,gradation,rime,soggi,'Ess',number)
                                                
                                                f2=Feedback.objects.get(stem=stem,\
                                                                        diphthong=diphthong,\
                                                                        gradation=gradation,\
                                                                        rime=rime,\
                                                                        case2='Ess',\
                                                                        number=number,\
                                                                        pos=pos,\
                                                                        soggi=soggi)
                                                if msgs:
                                                    f2.messages.add(msgs[0])
                                                else : print "No messages found:", f.msgid
                                                for d in dialects:
                                                    f2.dialects.add(d)
                                                f2.save()
                                                continue
                                            else:
                                                for number in f.number:
                                                    self.insert_feedback(cursor,pos,stem,diphthong,gradation,rime,soggi,case,number)
                                                    
                                                    f2=Feedback.objects.get(stem=stem,\
                                                                            diphthong=diphthong,\
                                                                            gradation=gradation,\
                                                                            rime=rime,\
                                                                            pos=pos,\
                                                                            case2=case,\
                                                                            number=number, \
                                                                            soggi=soggi)
                                                    
                                                    if msgs:
                                                        f2.messages.add(msgs[0])
                                                    else : print "No messages found:", f.msgid
                                                    for d in dialects:
                                                        f2.dialects.add(d)

                                                    f2.save()

                                                    


            if f.pos == "V":
                messages = Feedbackmsg.objects.filter(msgid=f.msgid)
                for stem in f.stem:
                    for diphthong in f.diphthong:
                        for soggi in f.soggi:                                                           
                            for rime in f.rime:                                                           
                                for gradation in f.gradation:                                                           
                                    for personnumber in f.personnumber:
                                        for tense in f.tense:
                                            for mood in f.mood:
                                        
                                                self.insert_feedback(cursor,pos,stem,diphthong,gradation,rime,soggi,'empty','empty',personnumber,tense,mood)
                                                f2 = Feedback.objects.get(stem=stem,\
																		  diphthong=diphthong,\
																		  gradation=gradation,\
																		  soggi=soggi,\
																		  tense=tense,\
																		  pos=pos,\
																		  rime=rime,\
																		  mood=mood,\
																		  personnumber=personnumber)

                                                if messages:
                                                    f2.messages.add(messages[0])
                                                else : print "No messages found:", f.msgid
                                                for d in dialects:
                                                    f2.dialects.add(d)

                                                f2.save()
        cursor.close()
        connection.close()
        self.set_null()

#!/bin/sh

P="python3"

DATA="crk_data"

DPS="$DATA/src"
INC="$DATA/inc"
META="$DATA/meta_data"
DPF="$DATA/fracrk"
DPW="$DATA/eng2crk"
ENG="$DATA/engsrc"

COMMAND="$P manage.py install"

echo "==================================================="
echo "installing tags and paradigms for Morfa"
$COMMAND -r $META/paradigms.txt -t $META/tags.txt -b 2>error.log
echo " "
echo "done"
echo "==================================================="

##
## Trying to set up Plains Cree Oahpa


##
##  crk->X
##

 echo "==================================================="
 echo "feeding db with $DPS/N_crk.xml"
 $COMMAND --file $DPS/N_crk.xml --tagfile $META/tags.txt --paradigmfile $META/n_paradigms.txt 2>>error.log
 echo " "
 echo "done"
 echo "==================================================="

echo "==================================================="
echo "feeding db with $DPS/Pron_crk.xml"
$COMMAND --file $DPS/Pron_crk.xml --tagfile $META/tags.txt --paradigmfile $META/pron_paradigms.txt 2>error.log
echo " "
echo "done"
echo "==================================================="


echo "==================================================="
echo "feeding db with $DPS/Ipc_crk.xml"
$COMMAND --file $DPS/Ipc_crk.xml 2>>error.log
echo " "
echo "done"
echo "==================================================="

# echo "==================================================="
# echo "feeding db with $DPS/MWE_crk.xml"
# $COMMAND --file $DPS/MWE_crk.xml 2>>error.log
# echo " "
# echo "done"
# echo "==================================================="

# echo "==================================================="
# echo "feeding db with $META/names.xml"
# $COMMAND --file $DPS/names.xml --tagfile $META/tags.txt --paradigmfile $META/n_paradigms.txt 2>>error.log
# echo " "
# echo "done"
# echo "==================================================="

# echo "==================================================="
# echo "feeding db with $DPS/prop_crknob.xml"
# $COMMAND --file $DPS/prop_crknob.xml --tagfile $META/tags.txt --paradigmfile $META/n_paradigms.txt 2>>error.log
# echo " "
# echo "done"
# echo "==================================================="


# echo "==================================================="
# echo "feeding db with $DPS/num_crknob.xml"
# $COMMAND --file $DPS/num_crknob.xml --tagfile $META/tags.txt --paradigmfile $META/num_paradigms.txt 2>>error.log
# echo " "
# echo "done"
# echo "==================================================="

 #echo "==================================================="
 #echo "feeding db with $DPS/A_crk2X.xml"
 #$COMMAND --file $DPS/A_crk2X.xml --tagfile $META/tags.txt --paradigmfile $META/A_paradigms.txt 2>>error.log
 #echo " "
 #echo "done"
 #echo "==================================================="

 # NB: manually specify POS because of preverbs
 echo "==================================================="
 echo "feeding db with $DPS/V_crk.xml"
 $COMMAND --file $DPS/V_crk.xml --tagfile $META/tags.txt --paradigmfile $META/v_paradigms.txt --pos V 2>>error.log
 echo " "
 echo "done"
 echo "==================================================="

# FELIPE: Do we really need this?  This is a tweak for preverbs, but I don't think we should use it in the long term.
# It's quite hacky to go directly into the hfst source.
# Since we have now done some workarounds and can better deal with preverbs, I do think this is inneccessary and can be commented out.
# TODO: Once it is removed from the database, check whether code must also be removed. 
# echo "==================================================="
# echo "feeding db with $META/cnjparadigms.txt"
# $P manage.py add_static_wordforms --filename=$META/cnjparadigms.txt --pos=V
# echo " "
# echo "done"
# echo "==================================================="

# FELIPE: This command is redundant!  Also it breaks some exercises as it replaces the pos of N+A by A.
# The key problem is an incorrect assumption about Tag encodings:  That the name of an annotation is sufficient to know its kind.
# This is not the case, the order matters and usually the position of the annotation usually indicates its kind/type.
#$P manage.py fixtagattributes

# # NOTE: --append here, so that the install only adds the forms, but doesn't delete existing ones.
# echo "==================================================="
# echo "feeding db with $DPS/v_pass.xml"
# $COMMAND --file $META/v_pass.xml --tagfile $META/tags.txt --paradigmfile $META/v_pass_paradigms.txt --append 2>>error.log
# echo " "
# echo "done"
# echo "==================================================="


# echo "==================================================="
# echo "feeding db with $DPS/adv_crknob.xml"
# $COMMAND --file $DPS/adv_crknob.xml 2>>error.log
# echo " "
# echo "done"
# echo "==================================================="

# echo "==================================================="
# echo "feeding db with $DPS/multiword_crknob.xml"
# $COMMAND --file $DPS/multiword_crknob.xml 2>>error.log
# echo " "
# echo "done"
# echo "==================================================="

# ##
# ## nobcrk
# ##

#echo "==================================================="
#echo "feeding db with $DPN/N_nobcrk.xml"
#$COMMAND --file $DPN/N_nobcrk.xml 2>>error.log
#echo " "
#echo "done"
#echo "==================================================="

#echo "==================================================="
#echo "feeding db with $DPN/num_nobcrk.xml"
#$COMMAND --file $DPN/num_nobcrk.xml 2>>error.log
#echo " "
#echo "done"
#echo "==================================================="

 #echo "==================================================="
 #echo "feeding db with $DPN/V_nobcrk.xml"
 #$COMMAND --file $DPN/V_nobcrk.xml 2>>error.log
 #echo " "
 #echo "done"
 #echo "==================================================="

 #echo "==================================================="
 #echo "feeding db with $DPN/A_nobcrk.xml"
 #$COMMAND --file $DPN/A_nobcrk.xml 2>>error.log
 #echo " "
 #echo "done"
 #echo "==================================================="

# echo "==================================================="
# echo "feeding db with $DPN/adv_nobcrk.xml"
# $COMMAND --file $DPN/adv_nobcrk.xml 2>>error.log
# echo " "
# echo "done"
# echo "==================================================="

# echo "==================================================="
# echo "feeding db with $DPN/mwe_nobcrk.xml"
# $COMMAND --file $DPN/mwe_nobcrk.xml 2>>error.log
# echo " "
# echo "done"
# echo "==================================================="

# echo "==================================================="
# echo "feeding db with $DPN/prop_nobcrk.xml"
# $COMMAND --file $DPN/prop_nobcrk.xml 2>>error.log
# echo " "
# echo "done"
# echo "==================================================="

# ##
# ## fracrk
# ##


echo "==================================================="
echo "feeding db with $DPF/N_fracrk.xml"
$COMMAND --file $DPF/N_fracrk.xml 2>>error.log
echo " "
echo "done"
echo "==================================================="

echo "==================================================="
echo "feeding db with $DPF/Ipc_fracrk.xml"
$COMMAND --file $DPF/Ipc_fracrk.xml 2>>error.log
echo " "
echo "done"
echo "==================================================="

# echo "==================================================="
# echo "feeding db with $DPF/MWE_fracrk.xml"
# $COMMAND --file $DPF/MWE_fracrk.xml 2>>error.log
# echo " "
# echo "done"
# echo "==================================================="

# echo "==================================================="
# echo "feeding db with $DPF/num_fracrk.xml"
# $COMMAND --file $DPF/num_fracrk.xml 2>>error.log
# echo " "
# echo "done"
# echo "==================================================="

echo "==================================================="
echo "feeding db with $DPF/V_fracrk.xml"
$COMMAND --file $DPF/V_fracrk.xml 2>>error.log
echo " "
echo "done"
echo "==================================================="

#echo "==================================================="
#echo "feeding db with $DPF/A_fracrk.xml"
#$COMMAND --file $DPF/A_fracrk.xml 2>>error.log
#echo " "
#echo "done"
#echo "==================================================="


# echo "==================================================="
# echo "feeding db with $DPF/adv_fracrk.xml"
# $COMMAND --file $DPF/adv_fracrk.xml 2>>error.log
# echo " "
# echo "done"
# echo "==================================================="

# echo "==================================================="
# echo "feeding db with $DPF/mwe_fracrk.xml"
# $COMMAND --file $DPF/mwe_fracrk.xml 2>>error.log
# echo " "
# echo "done"
# echo "==================================================="

# echo "==================================================="
# echo "feeding db with $DPF/prop_fracrk.xml"
# $COMMAND --file $DPF/prop_fracrk.xml 2>>error.log
# echo " "
# echo "done"
# echo "==================================================="

##
## engcrk
##


echo "==================================================="
echo "feeding db with $DPW/N_engcrk.xml"
$COMMAND --file $DPW/N_engcrk.xml
echo " "
echo "done"
echo "==================================================="

echo "==================================================="
echo "feeding db with $DPW/Ipc_engcrk.xml"
$COMMAND --file $DPW/Ipc_engcrk.xml
echo " "
echo "done"
echo "==================================================="

# echo "==================================================="
# echo "feeding db with $DPW/MWE_engcrk.xml"
# $COMMAND --file $DPW/MWE_engcrk.xml
# echo " "
# echo "done"
# echo "==================================================="


echo "==================================================="
echo "feeding db with $DPW/V_engcrk.xml"
$COMMAND --file $DPW/V_engcrk.xml
echo " "
echo "done"
echo "==================================================="

#echo "==================================================="
#echo "feeding db with $DPW/A_engcrk.xml"
#$COMMAND --file $DPW/A_engcrk.xml
#echo " "
#echo "done"
#echo "==================================================="

# echo "==================================================="
# echo "feeding db with $DPW/adv_swecrk.xml"
# $COMMAND --file $DPW/adv_swecrk.xml
# echo " "
# echo "done"
# echo "==================================================="

# echo "==================================================="
# echo "feeding db with $DPW/multiword_swecrk.xml"
# $COMMAND --file $DPW/multiword_swecrk.xml
# echo " "
# echo "done"
# echo "==================================================="

# echo "==================================================="
# echo "feeding db with $DPW/prop_swecrk.xml"
# $COMMAND --file $DPW/prop_swecrk.xml
# echo " "
# echo "done"
# echo "==================================================="


# echo "==================================================="
# echo "feeding db with $DPS/grammaticalwords_crknob.xml"
# $COMMAND --file $DPS/grammaticalwords_crknob.xml 2>>error.log
# echo " "
# echo "done"
# echo "==================================================="

# echo "==================================================="
# echo "feeding db with $DPS/pron_crk.xml"
# $COMMAND --file $DPS/pron_crk.xml --tagfile $META/tags.txt  2>>error.log
# echo " "
# echo "done"
# echo "==================================================="

# echo "==================================================="
# echo "feeding db with $DPS/derverb_crk.xml"
# $COMMAND --file $DPS/derverb_crk.xml --tagfile $META/tags.txt --append  2>>error.log # TODO: test append with this
# echo " "
# echo "done"
# echo "==================================================="


echo "==================================================="
echo "feeding db with $META/semantic_sets.xml"
$COMMAND --sem $META/semantic_sets.xml 2>>error.log
echo " "
echo "done"
echo "==================================================="

echo "==================================================="
echo "feeding db with messages to feedback"
$COMMAND --messagefile $META/messages.eng.xml 2>>error.log
echo " "
echo "done"
echo "==================================================="

# echo "==================================================="
# echo "feeding db with messages to feedback"
# $COMMAND --messagefile $META/messages.crk.xml 2>>error.log
# echo " "
# echo "done"
# echo "==================================================="

#echo "==================================================="
#echo "feeding db with messages to feedback"
#$COMMAND --messagefile $META/messages.eng.xml 2>>error.log
#echo " "
#echo "done"
#echo "==================================================="

# echo "==================================================="
# echo "feeding db with messages to feedback"
# $COMMAND --messagefile $META/messages.swe.xml 2>>error.log
# echo " "
# echo "done"
# cho "==================================================="

# echo "==================================================="
# echo "feeding db with messages to feedback"
# $COMMAND --messagefile $META/messages.fra.xml 2>>error.log
# echo " "
# echo "done"
# echo "==================================================="


# #  ... for eastern dialect there are additional feedback files feedback_verbs_eastern, feedback_adjectives_eastern that we ignore right now

# # Morfa-C


echo "==================================================="
echo "installing Morfa-C word fillings"
$COMMAND -f $META/fillings.xml --paradigmfile $META/paradigms.txt --tagfile $META/tags.txt 2>>error.log
echo " "
echo "done"
echo "==================================================="

# $P manage.py mergetags
# $P manage.py fixtagattributes

echo "==================================================="
echo "installing Morfa-C questions for nouns" # FELIPE - Encoding issues to compile. Fixed! (Pending TODO: Check multiple preverbs are getting picked up!)
$COMMAND -g $META/grammar_defaults.xml -q $META/noun_questions.xml 2>>error.log
echo " "
echo "done"
echo "==================================================="

echo "==================================================="
echo "installing Morfa-C questions for translation"
$COMMAND -g $META/grammar_defaults.xml -q $META/transl_questions.xml 2>>error.log
echo " "
echo "done"
echo "==================================================="

# echo "==================================================="
# echo "installing Morfa-C questions for object agreement"
# $COMMAND -g $META/grammar_defaults.xml -q $META/obj_agreement_questions.xml 2>>error.log
# echo " "
# echo "done"
# echo "==================================================="

echo "==================================================="
echo "installing Morfa-C questions for V - AI - Prs, Prt, FutDef, FutInt"
$COMMAND -g $META/grammar_defaults.xml -q $META/verb_questions/V-AI-PRS.xml 2>>error.log
$COMMAND -g $META/grammar_defaults.xml -q $META/verb_questions/V-AI-PRT.xml 2>>error.log
$COMMAND -g $META/grammar_defaults.xml -q $META/verb_questions/V-AI-FUTDEF.xml 2>>error.log
$COMMAND -g $META/grammar_defaults.xml -q $META/verb_questions/V-AI-FUTINT.xml 2>>error.log
echo " "
echo "done"
echo "==================================================="

echo "==================================================="
echo "installing Morfa-C questions for V - TA - Prs, Prt, FutDef, FutInt"
$COMMAND -g $META/grammar_defaults.xml -q $META/verb_questions/V-TA-PRS.xml 2>>error.log
$COMMAND -g $META/grammar_defaults.xml -q $META/verb_questions/V-TA-PRT.xml 2>>error.log
$COMMAND -g $META/grammar_defaults.xml -q $META/verb_questions/V-TA-FUTDEF.xml 2>>error.log
$COMMAND -g $META/grammar_defaults.xml -q $META/verb_questions/V-TA-FUTINT.xml 2>>error.log
echo " "
echo "done"
echo "==================================================="

echo "==================================================="
echo "installing Morfa-C questions for V - TI - Prs, Prt, FutDef FutInt"
$COMMAND -g $META/grammar_defaults.xml -q $META/verb_questions/V-TI-PRS.xml 2>>error.log
$COMMAND -g $META/grammar_defaults.xml -q $META/verb_questions/V-TI-PRT.xml 2>>error.log
$COMMAND -g $META/grammar_defaults.xml -q $META/verb_questions/V-TI-FUTDEF.xml 2>>error.log
$COMMAND -g $META/grammar_defaults.xml -q $META/verb_questions/V-TI-FUTINT.xml 2>>error.log
echo " "
echo "done"
echo "==================================================="

echo "==================================================="
echo "installing Morfa-C questions for V - II - Prs"
$COMMAND -g $META/grammar_defaults.xml -q $META/verb_questions/II-PRS.xml 2>>error.log
echo " "
echo "done"
echo "==================================================="

echo "==================================================="
echo "installing Morfa-C questions for V - TA CNJ - Prs, Prt, FutDef FutInt"
$COMMAND -g $META/grammar_defaults.xml -q $META/verb_questions/V-TA-CNJ-PRS.xml  2>>error.log
$COMMAND -g $META/grammar_defaults.xml -q $META/verb_questions/V-TA-CNJ-PRT.xml  2>>error.log
$COMMAND -g $META/grammar_defaults.xml -q $META/verb_questions/V-TA-CNJ-FUTINT.xml  2>>error.log
echo " "
echo "done"
echo "==================================================="

echo "==================================================="
echo "installing Morfa-C questions for TI - CNJ - Prt, Prs"
$COMMAND -g $META/grammar_defaults.xml -q $META/verb_questions/V-TI-CNJ-PRS.xml  2>>error.log
$COMMAND -g $META/grammar_defaults.xml -q $META/verb_questions/V-TI-CNJ-PRT.xml  2>>error.log
$COMMAND -g $META/grammar_defaults.xml -q $META/verb_questions/V-TI-CNJ-FUTINT.xml  2>>error.log
echo " "
echo "done"
echo "==================================================="

echo "==================================================="
echo "installing Morfa-C questions for AI - CNJ - Prt, Prs"
$COMMAND -g $META/grammar_defaults.xml -q $META/verb_questions/V-AI-CNJ-PRS.xml  2>>error.log
$COMMAND -g $META/grammar_defaults.xml -q $META/verb_questions/V-AI-CNJ-PRT.xml  2>>error.log
$COMMAND -g $META/grammar_defaults.xml -q $META/verb_questions/V-AI-CNJ-FUTINT.xml  2>>error.log
echo " "
echo "done"
echo "==================================================="


# echo "==================================================="
# echo "installing grammar links for norwegian"
# $COMMAND -i $META/grammatikklinker.txt 2>>error.log
# echo " "
# echo "done"
# echo "==================================================="

# ###################
# # Vasta and VastaS
# ###################

# FELIPE: We do not have Vasta working anyways, and the eng pronoun tags are not currently encoded to the best of my knowledge.
# TODO: Future work
#echo "==================================================="
#echo "installing Vasta questions"
#$COMMAND -g $META/grammar_defaults.xml -q $META/eng_questions_vasta.xml 2>>error.log
#echo " "
#echo "done"
#echo "==================================================="

# echo "==================================================="
# echo "installing Vasta-S questions"
# $COMMAND -g $META/grammar_defaults.xml -q $META/vastas_questions.xml 2>>error.log
# echo " "
# echo "done"
# echo "==================================================="


# echo "==================================================="
# echo "Installing feedback messages for vasta"
# $COMMAND --messagefile $META/messages_vasta.xml 2>>error.log
# echo " "
# echo "done"
# echo "==================================================="

# echo "==================================================="
# echo "Installing feedback messages for vasta - in English"
# $COMMAND --messagefile $META/messages_vasta.eng.xml 2>>error.log
# echo " "
# echo "done"
# echo "==================================================="

# echo "==================================================="
# echo "Installing feedback messages for vasta - in Finnish"
# $COMMAND --messagefile $META/messages_vasta.fin.xml 2>>error.log
# echo " "
# echo "done"
# echo "==================================================="

# echo "==================================================="
# echo "Installing feedback messages for vasta - in North Sámi"
# $COMMAND --messagefile $META/messages_vasta.crk.xml 2>>error.log
# echo " "
# echo "done"
# echo "==================================================="

# echo "==================================================="
# echo "Installing feedback messages for vasta - in Swedish"
# $COMMAND --messagefile $META/messages_vasta.swe.xml
# echo " "
# echo "done"
# echo "==================================================="

# #####
# # Sahka
# #####
# echo "==================================================="
# echo "Installing dialogues for Sahka - firstmeeting"
# $COMMAND -k $META/dialogue_firstmeeting.xml 2>>error.log
# echo " "
# echo "done"
# echo "==================================================="

# echo "==================================================="
# echo "Installing dialogues for Sahka - firstmeeting - boy"
# $COMMAND -k $META/dialogue_firstmeeting_boy.xml 2>>error.log
# echo " "
# echo "done"
# echo "==================================================="

# echo "==================================================="
# echo "Installing dialogues for Sahka - firstmeeting - girl"
# $COMMAND -k $META/dialogue_firstmeeting_girl.xml 2>>error.log
# echo " "
# echo "done"
# echo "==================================================="

# echo "==================================================="
# echo "Installing dialogues for Sahka - firstmeeting - man"
# $COMMAND -k $META/dialogue_firstmeeting_man.xml 2>>error.log
# echo " "
# echo "done"
# echo "==================================================="

# echo "==================================================="
# echo "Installing dialogues for Sahka - grocery shop"
# $COMMAND -k $META/dialogue_grocery.xml 2>>error.log
# echo " "
# echo "done"
# echo "==================================================="

# echo "==================================================="
# echo "Installing dialogues for Sahka - adjectives in shop"
# $COMMAND -k $META/dialogue_shopadj.xml 2>>error.log
# echo " "
# echo "done"
# echo "==================================================="

# echo "==================================================="
# echo "Installing dialogues for Sahka - visit"
# $COMMAND -k $META/dialogue_visit.xml 2>>error.log
# echo " "
# echo "done"
# echo "==================================================="

# FELIPE: See comment on previous call to fixtagattributes, which should not be needed.
# This method should be eventually eliminated by just having properly extracting the tags in a simpler way, like in itwewina.
#$P manage.py fixtagattributes
$P manage.py mergetags

echo "==================================================="
echo "adding feedback to nouns"
$COMMAND -f $DPS/N_crk.xml --feedbackfile $META/feedback_nouns.xml 2>>error.log
echo " "
echo "done"
echo "==================================================="


echo "==================================================="
echo "adding feedback to verbs"
$COMMAND -f $DPS/V_crk.xml --feedbackfile $META/feedback_verbs.xml 2>>error.log
echo " "
echo "done"
echo "==================================================="

echo "==================================================="
echo "adding feedback to pronouns"
$COMMAND -f $DPS/Pron_crk.xml --feedbackfile $META/feedback_pronouns.xml 2>>error.log
echo " "
echo "done"
echo "==================================================="

# echo "==================================================="
# echo "adding feedback to adjectives"
# $COMMAND -f $DPS/a_crknob.xml --feedbackfile $META/feedback_adjectives.xml
# echo " "
# echo "done"
# echo "==================================================="

# echo "==================================================="
# echo "adding feedback to numerals"
# $COMMAND -f $DPS/num_crknob.xml --feedbackfile $META/feedback_numerals.xml
# echo " "
# echo "done"
# echo "==================================================="

# #echo "==================================================="
# #echo "Optimizing tables"
# #cat optimize_analyze_tables.sql | $P manage.py dbshell
# #echo " "
# #echo "done"
# #echo "==================================================="

echo "stopped at: "
date '+%T'

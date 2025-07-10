# -*- coding: utf-8 -*-
from .local_conf import LLL1
import importlib
oahpa_module = importlib.import_module(LLL1+'_oahpa')

from django.core.management.base import BaseCommand


# # #
#
#  Command class
#
# # #

def fixtags():
	Tag = oahpa_module.drill.models.Tag
	tags = Tag.objects.all()

	print('Fixing attributes...')
	for tag in tags:
		print(tag.string)
		tag.fix_attributes()
		tag.save()

	print('Done')

class Command(BaseCommand):
	help = """
	Sometimes during the install process attributes on tag objects are not
	properly set. This corrects that issue.
	"""
	can_import_settings = True

	def handle(self, *args, **options):
		fixtags()

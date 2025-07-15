from django.urls import re_path
from . import views

# from django.conf import settings

urlpatterns = [
    # (r'^morfa/substantiv/$', 'smaoahpa.smadrill.views.morfa_game', {'pos': 'N'}),
    re_path(r"^morfas/der/$", views.morfa_game, {"pos": "Der"}, name="morfa_s.der"),
    re_path(r"^morfas/v/$", views.morfa_game, {"pos": "V"}, name="morfa_s.verb"),
    re_path(r"^morfas/s/$", views.morfa_game, {"pos": "N"}),
    re_path(r"^morfas/s/px/$", views.morfa_game, {"pos": "Px"}, name="morfa_s.px"),
    re_path(r"^morfas/a/$", views.morfa_game, {"pos": "A"}, name="morfa_s.adj"),
    re_path(r"^morfas/p/$", views.morfa_game, {"pos": "Pron"}, name="morfa_s.pron"),
    re_path(r"^morfas/l/$", views.morfa_game, {"pos": "Num"}, name="morfa_s.num"),
    re_path(r"^morfas/$", views.morfa_game, {"pos": "N"}, name="morfa_s.noun"),
    re_path(r"^leksa/$", views.leksa_game, name="leksa"),
    re_path(r"^leksa/names/$", views.leksa_game, {"place": True}, name="leksa.sted"),
    re_path(r"^numra/$", views.num, name="numra"),
    re_path(r"^numra/ord/$", views.num_ord, name="numra.ord"),
    re_path(r"^numra/klokka/$", views.num_clock, name="numra.klokka"),
    re_path(r"^numra/dato/$", views.dato, name="numra.dato"),
    re_path(r"^numra/money/$", views.money, name="numra.money"),
    # re_path(r'^numra_clock/medium/$', 'num_clock', {'clocktype': 'kl2'}),
    # re_path(r'^numra_clock/hard/$', 'num_clock', {'clocktype': 'kl3'}),
    # Contextual morfas
    re_path(r"^morfac/s/px/$", views.cmgame, {"pos": "Px"}, name="morfa_c.px"),
    re_path(r"^morfac/der/$", views.cmgame, {"pos": "Der"}, name="morfa_c.der"),
    re_path(r"^morfac/s/$", views.cmgame, {"pos": "n"}),
    re_path(r"^morfac/v/$", views.cmgame, {"pos": "v"}, name="morfa_c.verb"),
    re_path(r"^morfac/a/$", views.cmgame, {"pos": "a"}, name="morfa_c.adj"),
    re_path(r"^morfac/p/$", views.cmgame, {"pos": "Pron"}, name="morfa_c.pron"),
    re_path(r"^morfac/l/$", views.cmgame, {"pos": "Num"}, name="morfa_c.num"),
    re_path(r"^morfac/$", views.cmgame, {"pos": "n"}, name="morfa_c.noun"),
    re_path(r"^vastaf/$", views.vasta, name="vasta_f"),
    re_path(r"^vastas/$", views.cealkka, name="vasta_s"),
    re_path(r"^sahka/$", views.sahka, name="sahka"),
]

# # These are for me testing things, otherwise ignore.
# urlpatterns += patterns('smaoahpa.smadrill.new_views',
# 	# (r'^new_morfa/(?P<pos>V)/$', 'smaoahpa.smadrill.new_views.Morfa'),
# 	# (r'^new_morfa/(?P<pos>N|S)/$', 'smaoahpa.smadrill.new_views.Morfa'),
# 	# (r'^new_morfa/V/$', 'Game', {'gametype': 'MORFAV'}),
# 	# (r'^new_morfa/S/$', 'Game', {'gametype': 'MORFAS'}),
# 	# (r'^new_leksa/$', 'Game', {'gametype': 'LEKSA'}),
# )

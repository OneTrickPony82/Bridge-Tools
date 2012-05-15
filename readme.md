Short description of what the files contain:

bridgetools.py:
-definition of BridgeHand object and methods for parsing .lin files to BridgeHand objects
-some tools for calculating bridge scores, minimaxes, best leads etc.
those use dd solver created by Piotr Beling: http://bcalc.w8.pl/

autorever.py:
-tools for auto reverse engineer biddign systems in form of Full Disclosure BBO cards;
 to create one you need first have list of BridgeHands then call reverse_enginner for chosen list of
players and then bss_builder

vuextractor.py:

-some stuff for auto downloading .lins from vugraph arcvhies page,
removing comments from them (there is a lot of junk in them) etc.
unforunately it doesn't automatically work on vugraph arcvhies page
because I am lazy; you need to remove css at the top of the page and
empty lines in the middle of the file to make it workable. I have
sample input for like beginning of 2012 prepared like that and it's
2nd attachment to this email, just put it in same directory as
downloader or adjust paths inside the file

bridgecalc:
-double dummy solver written by Piotr Beling; at the time it didn't
have any API so I wrote methods to interpret cmd human readable output;
it's used to calculate minimaxes, best leads etc etc.

ratingtools.py:

-a lot of stuff to create variosu ratings like pair vs double dummy,
declarer vs double dummy etc etc and then put them in table form and
display;
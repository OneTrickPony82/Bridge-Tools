import re
import subprocess, _subprocess
import os, os.path

BCALCPATH = r"C:\Python31\bridgecalc\bcalconsole.exe"
SUITS = {0:"C", 1:"D", 2:"H", 3:"S", 4:"N"}
REVSUITS = {"C":0, "D":1, "H":2, "S":3, "N":4}
BCPLAYERS = {"N":0, "S":1, "E":2, "W":3}
PLAYERS = {2:"N", 0:"S", 3:"E", 1:"W"}
REVPLAYERS = {"S": 0, "W": 1, "N": 2, "E": 3}


class BridgeHand:
    def __init__(self, pbn, players, contract, declarer, tricks,
                 opleader, oplead, vuln, score, path = None, hh = None):
        self.pbn = pbn
        self.players = players
        self.contract = contract
        self.declarer = declarer
        self.tricks = tricks
        self.opleader = opleader
        self.oplead = oplead
        self.vuln = vuln
        self.score = score
        self.minimax = None
        self.room = None
        self.hh = hh
        self.bcalctable = None
        self.path = path
        self.opener = get_opener(self)
    def __hash__(self):
        return hash(self.pbn + str(self.players))
    def __eq__(self, other):
        if isinstance(other, BridgeHand):
            return (self.pbn == other.pbn) and (str(self.players) == str(other.players))
        else:
            NotImplemented


#The most important method in this file; all the calculations will work on
#BridgeHand objects; it takes linfile text, not path (method to deal with
#encoding will be written separately
def parse_linfile(linfile, lin = None):
    """Returns list of BridgeHand objects corresponding to hands in given linfile"""
    BridgeHands = []
    hhs = extract_hhs(linfile)
    contracts = get_contract_list(linfile)
    playersre = re.compile(r"pn\|([^\|]+)")
    pls = playersre.findall(linfile)
    players = playersre.findall(linfile)[0].split(",")
    dnums = deal_numbers(linfile)
    if len(pls) == len(hhs):
        flag = "bbo"
    else:
        flag = "vu"


    for hh in hhs:
        if get_room(hh).lower() == "o" and flag == "vu":
            aplayers = players[:4]
        elif get_room(hh).lower() == "c" and flag == "vu":
            aplayers = players[4:]
        elif flag == "bbo":
            aplayers = pls[0].split(",")
            pls = pls[1:]
        try:
            pbn = get_pbn(hh)
            vuln = get_vuln(hh)
            contract, declarer, doubled = analyze_bidding(extract_bidding(hh), get_dealer(hh))
        except:
            continue

        parsedc = parse_lin_contract(contracts[hhsnumber(hh, dnums[0])])
        if not parsedc:
            continue
        if contract == parsedc[0]:

            tricks = parsedc[3]
            #print("{0}, {1}, {2}, {3}, {4}".format(contract, tricks, doubled, PLAYERS[declarer], vuln))
            score = calculate_score(contract, tricks, doubled, PLAYERS[declarer] in vuln)
            opleader = PLAYERS[(declarer + 1) % 4]
            oplead = get_oplead(hh)
            score = calculate_score(contract, tricks, doubled, PLAYERS[declarer] in vuln)
            if PLAYERS[declarer].upper() in "WE":
                score = -score
            BridgeHands.append(BridgeHand(pbn, aplayers, (contract, doubled), PLAYERS[declarer], tricks,
                                          opleader, oplead, vuln, score, lin, hh))
        else:
            print("WRONG")
            continue    #couldn't read the hand

    if len(BridgeHands) < 2:
        f = open("log123.txt", "a")
        f.write(lin)
        f.write("\n")
        f.close()
    return BridgeHands


#reads all .lin from path(including subfolders) and returns list of BridgeHand objects
def read_all_lins(path):
    big = []
    lins = get_files(path, ".lin")
    for lin in lins:
        print("{0}".format(lin))
        try:
            textlin = open(lin).read()
        except:
            textlin = open(lin, encoding = 'latin1').read()
        try:
            big.extend(parse_linfile(textlin, lin))
        except:
            continue
    return list(set(big))


def bcalc_for_all(BHs):
    counter = 0
    errors = 0
    for hh in BHs:
        try:
            hh.bcalctable = get_bcalc(hh.pbn)
            counter = counter + 1
        except:
            errors = errors + 1
        if counter % 100 == 0:
            print(counter)
        if errors % 100 == 0 and errors > 0:
            print("ERRORS {0}".format(errors))
    print("{0} DONE, {1} errrs".format(counter, errors))




def deal_numbers(lin):
    """Returns no of contracts in given lin file"""
    numre = re.compile(r"vg\|[^,]*,[^,]*,[^,]*,(\d+),(\d+)")
    nums = numre.findall(lin)[0]
    return (int(nums[0]), int(nums[1]))

#for now it's one liner but useful to have this method in case format of stored hh changes
def get_room(hh):
    try:
        return hh[0]
    except:
        print("{0} not readable".format(hh))
        return None

#Gives position of given hand in a match; use with contract list to assign contracts to
#hands properly
def hhsnumber(hh, first):
    """takes hh and number of 1st hh in file"""
    hhnumre = re.compile(r"[oc](\d+)")
    if hh[0].lower() == "o":
        return (int(hhnumre.findall(hh)[0]) - first) * 2
    elif hh[0].lower() == "c":
        return (int(hhnumre.findall(hh)[0]) - first) * 2 + 1
    else:
        raise Exception("room name different than o or c")


#This should always return even amount of contracts; None for things which were not in lin file
def get_contract_list(linfile):
    realresre = re.compile(r"rs\|([^\|]+)")
    contracts = realresre.findall(linfile)[0].split(",")
    #if contracts[-1] == contracts[-2] == "":
    #    contracts.pop()
    #assert (len(contracts) % 2) == 0, "Odd amount of contracts in linfile"
    return contracts


#It has to read both 3 and 4 hands distributions
def get_distrib(lintext):
    """Returns list of 4 elements which represents hands of
       S W N E respectively"""
    disre = re.compile(r"md\|\d([^\|]+)")
    dis = disre.findall(lintext)[0]
    dis = dis.strip(",")
    dis = dis.strip()
    if len(dis) >= 65:
        distre = re.compile(r'md\|\d([\d\w]+),([\d\w]+),([\d\w]+),([\d\w]+)')
        hands = distre.search(lintext)
        return (hands.group(1), hands.group(2), hands.group(3), hands.group(4))
    else:
        dens = ["A", "K", "Q", "J", "T", "9", "8", "7", "6", "5", "4", "3", "2"]
        suits = ["S", "H", "D", "C"]
        cards = []
        for s in suits:
            for d in dens:
                cards.append(s + d)
        for char in dis:
            if char in "SHDC":
                actualsuit = char
            if char in dens:
                cards.remove(actualsuit + char)
        missinghand = ""
        for s in suits:
            missinghand = missinghand + s
            for c in cards:
                if c[0] == s:
                    missinghand = missinghand + c[1]
        return (dis + "," + missinghand).split(",")



def get_pbn(lintext):
    """Returns distribution as string in PBN format"""
    dis = " ".join(get_distrib(lintext))
    dis = dis.replace("S", "")

    return sort_pbn(re.sub(r"H|D|C", ".", dis))


def card_value(card):
    """Returns 1-13 for 2, 3... K, A"""
    if card.lower() == "a": return 14
    elif card.lower() == "k": return 13
    elif card.lower() == "q": return 12
    elif card.lower() == "j": return 11
    elif card.lower() == "t": return 10
    else: return int(card)


#This is needed because sometimes ditribution in lin file is in reverse order
def sort_pbn(pbn):
    li = list(pbn)
    start = 0
    end = 0
    for i in li:
        if i in "23456789TJQKA":
            end = end + 1
        elif (i in ". " or end == len(li)):
            if start != end:
                li[start:end] = reversed(sorted(li[start:end], key = card_value))
            start = end + 1
            end = end + 1
    return "".join(li)


def extract_bidding(lintext):
    bidsre = re.compile(r"mb\|([^\|!]+)")
    return bidsre.findall(lintext)

#Add rdbls !!!!!
#This one takes the list with all the bids and returns the meat
def analyze_bidding(bidding, dealer):
    """Returns a tuple: (final contract, declarer, doubled);
    doubled is True or False"""
    if len(bidding) == 4 and len(set(bidding)) == 1:
        return ("passout", dealer, False)
    contract = "passout"
    try:
        for x in reversed(bidding):
            if len(x) == 2:
                contract = x
                break;
        trumps = contract[1]
        indexfinal = bidding.index(contract) % 2
        doubled = False
        for x in bidding[bidding.index(contract):]:
            if x.lower() == "d":
                doubled = True

        declarer = dealer
        for x in bidding:
            if len(x) == 2 and x[1] == trumps and (bidding.index(x) % 2) == indexfinal:
                declarer = (dealer + bidding.index(x)) % 4
                break;

        return (contract, declarer, doubled)
    except:
        return (None, None, None)


def get_dealer(lintext):
    """Returns 0123 for SWNE respectively"""
    dealerre = re.compile(r"md\|(\d)")
    try:
        return int(dealerre.findall(lintext)[0]) - 1
    except:
        raise Exception("Couldn't find dealer in {0}".format(lintext))
#This probably won't be needed as there are results for all the hands at the
#top of every lin file (fortunately...)
def get_tricks(lintext):
    """Returns amount of tricks taken by declarer"""
    pass


def get_oplead(lintext):
    """Returns the opening lead card"""
    opleadre = re.compile(r"pc\|(..)\|")
    try:
        return opleadre.findall(lintext)[0]
    except:
        return None

def get_vuln(lintext):
    """Returns one of the: BOTH, NS, WE, NONE strings"""
    vulre = re.compile(r"sv\|(.)\|")
    try:
        vul = vulre.findall(lintext)[0]
        if vul in ("N", "n", "S", "s"):
            return "NS"
        elif vul in ("E", "e", "W", "w"):
            return "WE"
        elif vul in ("o", "O", "0"):
            return "love"
        elif vul in ("B", "b"):
            return "WNES"
    except:
        raise Exception("Could not read vuln in {0}".format(lintext))



def get_bcalc(hand):
    """Returns list of 20 ints; which are tricks in C/D/H/S/NT for
    N S E W respectively"""
    su = subprocess.STARTUPINFO()
    su.dwFlags |= _subprocess.STARTF_USESHOWWINDOW
    su.wShowWindow = _subprocess.SW_HIDE
    p = subprocess.Popen([BCALCPATH, "-c", hand, "-t", "a", "-e", "e", "-q", "-d SWNE"], stdout = subprocess.PIPE, stderr = subprocess.STDOUT,
                         startupinfo = su)
    table = p.stdout.read().decode()
    numberre = re.compile(r"\d+")
    numbers = numberre.findall(table)
    return list(map(int, numbers))


#At the time of writing bcalc didn't have any API and this function just parses human readable
#output which wasn't easy task as some strange things happen there
def get_bcalc_tricks(hand, trumps, opleader):
    """Returns doubledummy results for given contract for every possible first card lead"""
    su = subprocess.STARTUPINFO()
    su.dwFlags |= _subprocess.STARTF_USESHOWWINDOW
    su.wShowWindow = _subprocess.SW_HIDE

    p = subprocess.Popen([BCALCPATH, "-c", hand, "-t", trumps, "-e", "e", "-q", "-d SWNE", "-l", opleader], stdout = subprocess.PIPE,
                         stderr = subprocess.STDOUT, startupinfo = su)
    table = p.stdout.read().decode()
    table = table.replace("\n", " ")
    table = table.replace("\r", " ")
    parts = [x for x in table.split("  ")]
    parts = [x.strip() for x in parts if not x in ("", " ")]
    hand = " " + hand + " "
    hand = hand.replace("....", ".-.-.-.")
    hand = hand.replace("...", ".-.-.")
    hand = hand.replace("..", ".-.")
    hand = hand.replace(". ", ".- ")
    hand = hand.replace(" .", " -. ")
    suits = hand.replace(".", " ").split(" ")
    suits = [x.strip() for x in suits if x!= ""]

    #print("suits: {0}".format(suits))
    #print("parts: {0}".format(parts))
    #print("pbn: {0}".format(hand))
    #print(trumps, opleader)
    #print("\n'n")
    assert len(suits) == 16
    assert 16 < len(parts) < 21, "error in hand{0}".format(hand)

    for x in suits:
        parts.remove(x)

    tricks = []
    numre = re.compile(r"\d+")
    for x in parts:
        for y in numre.findall(x):
            tricks.append(int(y))
    assert len(tricks) == 13
    return tricks


def optimal_result(hand, contract, doubled, declarer, vuln):
    """Returns result for given contract assuming dd play"""
    tricks = 13 - max(get_bcalc_tricks(hand, contract[1], PLAYERS[(REVPLAYERS[declarer] + 1) % 4]))
    if declarer in "WEwe":
        mult = -1
    else:
        mult = 1
    return mult*(calculate_score(contract, tricks, doubled, declarer in vuln))


#This takes 20 element list for possible tricks in C D H S N and NSEW players respectively
#Such list is returned by get_bcalc
#vuln is either "" or "WE" or "WNES" or "NS" as returned by get_vuln
def minimax(trickstable, vuln):
    NS = list(map(max, trickstable[0:5], trickstable[5:10]))
    WE = list(map(max, trickstable[10:15], trickstable[15:20]))

    NSscores = get_results_table(NS, "N" in vuln)
    WEscores = get_results_table(WE, "W" in vuln)

    actualbest = (0, None)
    for x in range(35):
        if NSscores[x][1] > actualbest[0]:
            actualbest = (NSscores[x][1], "NS")
        if -WEscores[x][1] < actualbest[0]:
            actualbest = (-WEscores[x][1], "WE")

    return actualbest


#vuln is True or False
def get_results_table(maxtricks, vuln):
    """Returns list of 35 value for all possible contracts; not makeable contracts are scored as doubled"""
    SUITS = {0:"C", 1:"D", 2:"H", 3:"S", 4:"N"}
    scores = []
    for x in range(7):
        for y in range(5):
            scores.append((str(x+1) + SUITS[y], calculate_score(str(x+1) + SUITS[y], maxtricks[y], maxtricks[y] < x + 7, vuln)))
    return scores

def normal_to_bcalc(x):
    if x == 0: return 1
    if x == 1: return 3
    if x == 2: return 0
    if x == 3: return 2


def sign(x):
    if x > 0: return 1
    if x < 0: return -1
    if x == 0: return 0


def IMPs(score):
    IMPtable = [0, 20, 50, 90, 130, 170, 220, 270, 320, 370, 430, 500, 600, 750, 900, 1100, 1300, 1500, 1750, 2000, 2250, 2500, 3000, 3500, 4000]
    return sign(score) * IMPtable.index([x for x in IMPtable if x <= abs(score)][-1])


def extract_hhs(linfile):
    return linfile.split(r"qx|")[1:]


#REMEMBER PASSOUTS !!!
def parse_lin_contract(s):
    """returns (contract, declarer, doubled, tricks)"""
    if s.lower() in ("p", "pass"):
        return ("passout", 0, False, 0)
    if not s:
        return None

    overtricksre = re.compile(r"[\+\-]\d")
    level = s[0]
    trumps = s[1]
    declarer = s[2]
    doubled = "x" in s
    overtricks = 0
    overtricksstr = overtricksre.findall(s)
    if overtricksstr:
        overtricks = int((overtricksstr)[0])

    tricks = int(level) + 6 + overtricks
    return(level + trumps, declarer, doubled, tricks)


#Returns (x, y) where x is room (o/c) and y is players position
def detect_player(linfile, name):
    namesre = re.compile(r"pn\|([^\|]+)")
    players = namesre.findall(linfile)[0].split(",")
    index = -1
    for x in players:
        if name.lower() in  x.lower():
            index = players.index(x)
    if index == -1:
        return False
    elif index > 3: room = "c"
    else : room = "o"
    return (room, PLAYERS[index % 4])


def get_files(path, ext = None):
    fils = []
    for root, dirs, files in os.walk(path):
        for name in files:
          if ext and (os.path.splitext(name))[1] == ext:
            fils.append(os.path.join(root,name))
    return fils


def BHminimax(bh):
    return minimax(get_bcalc(bh.pbn), bh.vuln)


#NSEW CDHSNT
def best_possible(contract, declarer, ttable, vuln):
    suit = contract[0][1]
    bcsuit = REVSUITS[suit]
    bcdeclarer = normal_to_bcalc(REVPLAYERS[declarer])
    tricks = ttable[bcdeclarer * 5 + bcsuit]
    mult = NSWEmult(declarer)
    return mult*(calculate_score(contract[0], tricks, contract[1], declarer in vuln))


def best_possible_tricks(contract, declarer, ttable, vuln):
    suit = contract[0][1]
    bcsuit = REVSUITS[suit]
    bcdeclarer = normal_to_bcalc(REVPLAYERS[declarer])
    tricks = ttable[bcdeclarer * 5 + bcsuit]
    mult = NSWEmult(declarer)
    return tricks



def NSWEmult(i):
    if i in "NSns":
        return 1
    elif i in "WEwe":
        return -1


#time to split it into various files...
def save_all_lins(linlist):
    cutre = re.compile(r".*chosen\\(.*)")
    for p in linlist:
        fread = open(p, 'rb')
        lin = fread.read()
        fread.close()
        outpath = os.path.join(fpath, cutre.findall(p)[0])
        try:
            os.makedirs(os.path.dirname(outpath))
        except OSError:
            pass
        output = open(outpath, "wb")
        output.write(lin)
        output.close()



#Lol.... :
#This still needs testing
#TO-DO: rdbl
def calculate_score(contract, tricks, doubled, vuln):
    under_vuln = [0, 200, 500, 800, 1100, 1400, 1700, 2000, 2300, 2600,
                  2900, 3200, 3500, 3800]
    under_not_vuln = [0, 100, 300, 500, 800, 1100, 1400, 1700, 2000,
                      2300, 2600, 2900, 3200, 3500]
    majorscores = [0, 30, 60, 90, 120, 150, 180, 210]
    minorscores = [0, 20, 40, 60, 80, 100, 120, 140]
    ntscores = [0, 40, 70, 100, 130, 160, 190, 220]

    if contract == "passout":
        return 0

    level = int(contract[0])
    overtricks = tricks - level - 6
    if overtricks < 0:
        if doubled and vuln:
            return -under_vuln[abs(overtricks)]
        elif doubled and not vuln:
            return -under_not_vuln[abs(overtricks)]
        elif not doubled and vuln:
            return 100 * overtricks
        elif not doubled and not vuln:
            return 50 * overtricks
    elif overtricks >= 0:
        if contract[1] in ('S', 'H'):
            base = majorscores[level]
        elif contract[1] in ('D', 'C'):
            base = minorscores[level]
        elif contract[1] in ('N', 'n'):
            base = ntscores[level]

    score = base
    if doubled and vuln:
        score = score * 2
    elif doubled and not vuln:
        score = score * 2

    #Game, partscore bonuses:
    if score >= 100 and vuln:
        score = score + 500
    elif score >= 100 and not vuln:
        score = score + 300
    else:
        score = score + 50

    #overtricks
    if doubled and vuln:
        score = score + overtricks * 200 + 50
    elif doubled and not vuln:
        score = score + overtricks * 100 + 50
    elif not doubled:
        if contract[1] in ('S', 'H', 'N', 'n'):
            score = score + overtricks * 30
        elif contract[1] in ('D', 'C'):
            score = score + overtricks * 20

    if int(contract[0]) == 6 and vuln:
        score = score + 750
    elif int(contract[0]) == 6 and not vuln:
        score = score + 500

    if int(contract[0]) == 7 and vuln:
        score = score + 1500
    elif int(contract[0]) == 7 and not vuln:
        score = score + 1000

    return score




def tricks_for_all(BHs):
    counter = 0
    errors = 0
    for hh in BHs:
        try:
            hh.minimax = get_bcalc_tricks(hh.pbn, hh.contract[0][1], hh.opleader)
            counter = counter + 1
            if counter % 50 == 0:
                print(counter)
        except:
            errors = errors + 1
            if errors % 10 == 0:
                print("ERROS: {0}".format(errors))
            continue
    print("ERRORS: {0}".format(errors))


def pos(card, pbn, opleader):
	hand = pbn.split(" ")[REVPLAYERS[opleader]]
	suits = {0: "s", 1: "h", 2: "d", 3: "c"}
	currsuit = 0
	pos = 0
	for c in hand:
		if c == ".":
			currsuit = (currsuit + 1) % 4
		elif card[0].lower() == suits[currsuit] and card[1] == c:
			return pos
		else:
			pos = pos + 1
	assert pos != 0, "Couldn't find a card of first lead"
	return -1


def rate_oplead(card, pbn, opleader, ttable):
    return ttable[pos(card, pbn, opleader)]


def concbcalc(BH):
    """Returns list of 20 ints; which are tricks in C/D/H/S/NT for
    N S E W respectively"""
    hand = BH.pbn
    su = subprocess.STARTUPINFO()
    su.dwFlags |= _subprocess.STARTF_USESHOWWINDOW
    su.wShowWindow = _subprocess.SW_HIDE
    p = subprocess.Popen([BCALCPATH, "-c", hand, "-t", "a", "-e", "e", "-q", "-d SWNE"], stdout = subprocess.PIPE, stderr = subprocess.STDOUT,
                         startupinfo = su)
    table = p.stdout.read().decode()
    numberre = re.compile(r"\d+")
    numbers = numberre.findall(table)
    return list(map(int, numbers))


#Filtering for bidding/shapes/points here
def bid_filter(hh, player, oppoints, respoints, sequence, opshape = [()], resshape = [()], weopen = True):
    bidding = extract_bidding(hh.hh)
    for x in range(len(bidding)):
        bidding[x] = bidding[x].lower()
    opener = get_dealer(hh.hh)
    for bid in bidding:
        if bid == 'p':
            opener = (opener + 1) % 4
        else:
            break
    heropos = None
    for pl in hh.players:
        if player.lower() in pl.lower():
            heropos = hh.players.index(pl)
    if heropos is None:
        return False
    if weopen:
        if opener != heropos and opener != (heropos + 2) % 4:
            return False
    else:
        if opener != (heropos + 1) % 4 and opener != (heropos + 3) % 4:
            return False

    passcount = 0
    for bid in bidding:
        if bid == 'p':
            passcount = passcount + 1
        else:
            break
    for i in range(passcount):
        bidding.remove('p')
    if len(bidding) >= len(sequence):
        for i in range(len(sequence)):
            if sequence[i].lower() == "np":
                if bidding[i].lower() == "p":
                    return False
                else:
                    continue

            if sequence[i].lower() == bidding[i].lower():
                pass
            else:
                return False
    else:
        return False
    hands = hh.pbn.split(" ")
    if not oppoints[0] <= point_count(hands[opener]) <= oppoints[1]:
        return False
    if not respoints[0] <= point_count(hands[(opener + 2) % 4]) <= respoints[1]:
        return False

    #shape here
    if not accshapes(hands[opener], opshape):
        return False
    if not accshapes(hands[(opener + 2) % 4], resshape):
        return False

    #print(hh.path)

    if weopen:
        return (hands[opener], hands[(opener + 2) % 4])
    else:
        return (hands[(opener+1) % 4], hands[(opener+3) % 4])

def accshape(pbnhand, shaperange = ()):
    if shaperange == ():
        return True
    pbnshape = shape(pbnhand)
    for x in range(4):
        if shaperange[0][0] <= pbnshape[0] <= shaperange[0][1] and \
        shaperange[1][0] <= pbnshape[1] <= shaperange[1][1] and \
        shaperange[2][0] <= pbnshape[2] <= shaperange[2][1] and \
        shaperange[3][0] <= pbnshape[3] <= shaperange[3][1]:
            return True
        else:
            return False

def accshapes(pbnhand, shapes):
    for shape in shapes:
        if accshape(pbnhand, shape):
            return True
    return False


def shape(pbnhand):
    count = 0
    suit = 0
    shape = [0,0,0,0]
    for x in pbnhand:
        if x != '.':
            shape[suit] = shape[suit]+1
        else:
            suit = suit + 1
            count = 0
    assert sum(shape) == 13, "12 cards !!"
    return shape


def point_count(pbnhand):
    pc = 0
    for x in pbnhand.lower():
        if x == 'a':
            pc = pc + 4
        elif x == 'k':
            pc = pc + 3
        elif x == 'q':
            pc = pc + 2
        elif x == 'j':
            pc = pc + 1
    return pc

def print_bid(bidding):
    bidlen = len(bidding)
    bids = []
    for b in bidding:
        bids.append(b)
    bids.extend(['p','p','p','p'])
    for x in range(0, bidlen, 4):
        print("{0:<4} {1:<4} {2:<4} {3:<4}".format(bids[x], bids[x+1], bids[x+2], bids[x+3]))

def onesided(bidding):
    even = False
    odd = False
    count = 0
    for b in bidding:
        if count == 0:
            if b != 'p':
                even = True
        if count == 1:
            if b != 'p':
                odd = True
        count = (count + 1) % 2
    return odd != even



def search_for_sequence(hhs, seqs, players, oppoints = (0,40), resppoints = (0,40), opshape =[()], resshape = [()], weopen = True):
    overall = []
    for pl in players:
        for seq in seqs:
            result = []
            for hh in hhs:
                res = bid_filter(hh, pl, oppoints, resppoints, seq, opshape, resshape, weopen)
                if res:
                    result.append(tuple([hh, res]))
            overall.extend(tuple(result))
    return overall


def display_sequencies(res):
    for r in res:
        print(r[0].players)
        print(r[1])
        print_bid(extract_bidding(r[0].hh))
        print("")


def lin_builder(hands, event, outputfile):
    """Builds a lin!"""
    header = "vg|{0},,P,1,{1},,,,|".format(event, len(hands))
    contracts = "" #contract list here in the future
    roomre = re.compile(r"([oc]\d+)[\|,]")
    plre = re.compile(r"pn\|[^\|]+\|")
    output = open(outputfile, "w")
    output.write(header + "\n")
    output.write(contracts)
    output.write("pw|,,|pg||")
    dealcount = 1
    for h in hands:
        hh  = roomre.sub("o{0}|".format(dealcount), h.hh, 1)
        hh = plre.sub("", hh)
        try:
            output.write("pn|{0},{1},{2},{3}|qx|".format(h.players[0], h.players[1], h.players[2], h.players[3]))
            output.write(hh)
            output.write("\n")
            dealcount = dealcount + 1
        except:
            pass
    output.close()

def pointsplit(hand):
	return sorted((point_count(hand.pbn.split(" ")[(REVPLAYERS[hand.declarer] + 2) % 4]) , (point_count(hand.pbn.split(" ")[REVPLAYERS[hand.declarer]]))))


def printpbn(pbn):
	pbns = list(pbn)
	symbols = ["!c", "!d", "!h"]
	for x in range(len(pbns)):
		if pbns[x] == ".":
			pbns[x] = symbols.pop()
	li = "".join(pbns)
	return ("!s" + li)

def printres(res):
	count = 0
	for x in res:
		count = count + 1
		print(str(count) + ". " + printpbn(x[1][1]).replace("!", "! "))


def prepare(hands, player, seqs):
	meckopens = []
	for hand in hands:
		for seq in seqs:
			if bid_filter(hand, player, (11,40), (0,40), seq):
				meckopens.append(hand)
				break
	bid = ultimate_bid(meckopens)
	cleannn(bid[0], 50)
	display_rating(bid[0])


def extract_player(hands, player):
    output = []
    for h in hands:
        for pl in h.players:
            if player.lower() in pl.lower():
                output.append(h)
                break
    return output


#creates 50hand .line files from lists as returned by search for sequence
def linify(gaz, path, name):
    handcount = len(gaz)
    i = 0
    while handcount > 0:
        hands = [x[0] for x in gaz[i*50:(i+1)*50]]
        lin_builder(hands, "", os.path.join(path, name + "part{0}.lin".format(i)))
        i = i + 1
        handcount = handcount - 50

def findswings(BHs, swingsize = 5):
    """Takes list of BridgeHand objects, returns dictionary with players/results"""
    results = {}
    output = []
    counter = 0
    for bh in BHs:
        try:
            score = IMPs(bh.score - minimax(bh.bcalctable, bh.vuln)[0])
            if abs(score) > swingsize:
                    output.append(bh)
        except:
            continue
        counter = counter + 1
        if counter % 1000 == 0:
            print("Hand no {0} processed".format(counter))
    return output

def lin_builder_forswings(hands, event, outputfile):
    """Builds a lin!"""
    header = "vg|{0},,P,1,{1},,,,|".format(event, len(hands))
    contracts = "" #contract list here in the future
    roomre = re.compile(r"([oc]\d+)[\|,]")
    plre = re.compile(r"pn\|[^\|]+\|")
    output = open(outputfile, "w")
    output.write(header + "\n")
    output.write(contracts)
    output.write("pw|,,|pg||")
    dealcount = 1
    for h in hands:
        hh  = roomre.sub("o{0}|".format(dealcount), h.hh, 1)
        hh = plre.sub("", hh)
        score = IMPs(h.score - minimax(h.bcalctable, h.vuln)[0])
        minimaxscore = minimax(h.bcalctable, h.vuln)[0]
        hh = hh.replace("|pg", "|nt|Swing: {0}\nMinimax: {1}\nScore: {2}|\npg".format(score, minimaxscore, h.score), 1)
        try:
            output.write("pn|{0},{1},{2},{3}|qx|".format(h.players[0], h.players[1], h.players[2], h.players[3]))
           
            #output.write("nt|Swing {0}|".format(score))
            output.write(hh)
            output.write("\n")
            dealcount = dealcount + 1
        except:
            pass
    output.close()

def get_opener(h):
    bidding = extract_bidding(h.hh)
    opener = get_dealer(h.hh)
    for bid in bidding:
        if bid.upper() == 'P':
            opener = (opener + 1) % 4
        else:
            break
    return opener















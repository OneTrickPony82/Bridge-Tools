#This file contains various tools for creating ratings like pair vs minimax,
#best declarer, best defenders etc etc. all based on some kind of comparison
#of actual play to double dummy play
#most interesting is probably assess_pair which is straightforward comparison
#of results to minimaxes as well as ultimate_bid and ultimate_cardplaye ones


from bridgetools.py import *

#cleaning for ratings
def clean(rat, player):
    score = 0
    hands = 0
    todel = []
    for key in rat:
        if player.lower() in key.lower():
            score = score + rat[key][0]
            hands = hands + rat[key][1]
            todel.append(key)
    for key in todel:
        del rat[key]
    if hands > 0:
            rat[player] = (score, hands)


def clean_all_names(rat):
    names = list(rat)
    names.sort(key = len)
    for n in names:
        if len(n.strip()) > 5:
            clean(rat, n)


def display_rating(rat):
    players = list(rat)
    players.sort(key = lambda x : rat[x][0] / rat[x][1])
    players = reversed(players)
    for pl in players:
        print("{0:<12} : {1:<6} , {2:<6} , avg: {3:.2f}".format(pl, rat[pl][0], rat[pl][1], rat[pl][0] / rat[pl][1]))


#there is a lot of code duplication assess_xxx funtcions but it was easier to copy paste than
#to think about some general solution
def assess_pair(BHs):
    """Takes list of BridgeHand objects, returns dictionary with players/results"""
    results = {}
    counter = 0
    for bh in BHs:
        try:
            score = IMPs(bh.score - minimax(bh.bcalctable, bh.vuln)[0])
            for pl in bh.players:
                    if pl in results:
                        results[pl] = (results[pl][0] + score * NSWEmult(PLAYERS[bh.players.index(pl)]), results[pl][1] + 1)
                        #print("Adding {0} for {1} contract {2}".format(score * NSWEmult(PLAYERS[bh.players.index(pl)]), pl, bh.contract[0]))
                    else:
                        results[pl] = ((score * NSWEmult(PLAYERS[bh.players.index(pl)])), 1)
                        #print("Adding {0} for {1} contract {2}".format(score * NSWEmult(PLAYERS[bh.players.index(pl)]), pl, bh.contract[0]))
        except:
            continue
        counter = counter + 1
        if counter % 1000 == 0:
            print("Hand no {0} processed".format(counter))
    return results


def assess_cardplay(BHs):
    """Takes list of BridgeHand objects, returns dictionary with players/results"""
    results = {}
    counter = 0
    for bh in BHs:
        try:
            realscore = calculate_score(bh.contract[0], bh.tricks, bh.contract[1], bh.declarer in bh.vuln)
            realscore = realscore * NSWEmult(bh.declarer)
            optimal = best_possible(bh.contract, bh.declarer, bh.bcalctable, bh.vuln)
            score = IMPs(realscore - optimal)
            #print(realscore, optimal, score)
            for pl in bh.players:
                if pl in results:
                    results[pl] = (results[pl][0] + score * NSWEmult(PLAYERS[bh.players.index(pl)]), results[pl][1] + 1)
                else:
                    results[pl] = ((score * NSWEmult(PLAYERS[bh.players.index(pl)])), 1)
        except:
            continue
        counter = counter + 1
        if counter % 10 == 0:
                    print(counter)
    return results
len


def assess_bidding(BHs):
    """Takes list of BridgeHand objects, returns dictionary with players/results"""
    results = {}
    counter = 0
    for bh in BHs:
        try:
            #ttable = get_bcalc(bh.pbn)
            ttable = bh.bcalctable
            minmax = minimax(ttable, bh.vuln)
            actual = best_possible(bh.contract, bh.declarer, bh.bcalctable, bh.vuln)
            score = IMPs(actual - minmax[0])
            #print(minmax, actual, score)
            for pl in bh.players:
                if pl in results:
                    results[pl] = (results[pl][0] + score * NSWEmult(PLAYERS[bh.players.index(pl)]), results[pl][1] + 1)
                    #print("Adding {0} for {1} contract {2}".format(score * NSWEmult(PLAYERS[bh.players.index(pl)]), pl, bh.contract[0]))
                else:
                    results[pl] = ((score * NSWEmult(PLAYERS[bh.players.index(pl)])), 1)
                    #print("Adding {0} for {1} contract {2}".format(score * NSWEmult(PLAYERS[bh.players.index(pl)]), pl, bh.contract[0]))
        except:
            continue
        counter = counter + 1
        if counter % 100 == 0:
            print(counter)
    return results


def assess_declarer(BHs):
    """Takes list of BridgeHand objects, returns dictionary with players/results"""
    results = {}
    counter = 0
    for bh in BHs:
        try:
            realscore = calculate_score(bh.contract[0], bh.tricks, bh.contract[1], bh.declarer in bh.vuln)
            realscore = realscore * NSWEmult(bh.declarer)
            optimal = best_possible(bh.contract, bh.declarer, bh.bcalctable, bh.vuln)
            score = IMPs(realscore - optimal)
            #print(realscore, optimal, score)
            for pl in bh.players:
                if bh.players.index(pl) == REVPLAYERS[bh.declarer]:
                    if pl in results:
                        results[pl] = (results[pl][0] + score * NSWEmult(PLAYERS[bh.players.index(pl)]), results[pl][1] + 1)
                    else:
                        results[pl] = ((score * NSWEmult(PLAYERS[bh.players.index(pl)])), 1)
        except:
            continue
        counter = counter + 1
        if counter % 10 == 0:
                    print(counter)
    return results


def assess_declarer_tricks(BHs):
    """Takes list of BridgeHand objects, returns dictionary with players/results"""
    results = {}
    counter = 0
    for bh in BHs:
        try:
            realscore = bh.tricks
            optimal = best_possible_tricks(bh.contract, bh.declarer, bh.bcalctable, bh.vuln)
            score = realscore - optimal
            #print(realscore, optimal, score)
            for pl in bh.players:
                if bh.players.index(pl) == REVPLAYERS[bh.declarer]:
                    if pl in results:
                        results[pl] = (results[pl][0] + score , results[pl][1] + 1)
                    else:
                        results[pl] = ((score, 1))
        except:
            continue
        counter = counter + 1
        if counter % 1000 == 0:
                    print(counter)
    return results


def assess_defence(BHs):
    """Takes list of BridgeHand objects, returns dictionary with players/results"""
    results = {}
    counter = 0
    for bh in BHs:
        try:
            realscore = calculate_score(bh.contract[0], bh.tricks, bh.contract[1], bh.declarer in bh.vuln)
            realscore = realscore * NSWEmult(bh.declarer)
            optimal = best_possible(bh.contract, bh.declarer, bh.bcalctable, bh.vuln)
            score = IMPs(realscore - optimal)
            #print(realscore, optimal, score)
            for pl in bh.players:
                if bh.players.index(pl) not in (REVPLAYERS[bh.declarer], (REVPLAYERS[bh.declarer] + 2 )% 4):
                    if pl in results:
                        results[pl] = (results[pl][0] + score * NSWEmult(PLAYERS[bh.players.index(pl)]), results[pl][1] + 1)
                    else:
                        results[pl] = ((score * NSWEmult(PLAYERS[bh.players.index(pl)])), 1)
        except:
            continue
        counter = counter + 1
        if counter % 1000 == 0:
                    print(counter)
    return results


#tool for assessing declarer's advantage
def assess_decadv(BHs):
    """Takes list of BridgeHand objects, returns dictionary with players/results"""
    results = [0, 0]
    counter = 0
    for bh in BHs:
        try:
            realscore = bh.tricks
            optimal = best_possible_tricks(bh.contract, bh.declarer, bh.bcalctable, bh.vuln)
            score = realscore - optimal
            #print(realscore, optimal, score)
            results[0] = results[0] + score
            results[1] = results[1] + 1

        except:
            continue
        counter = counter + 1
        if counter % 1000 == 0:
                    print(counter)
    return results


def assess_opleader(BHs):
    """Takes list of BridgeHand objects, returns dictionary with players/results"""
    results = {}
    counter = 0
    for bh in BHs:
        try:
            realtricks = 13 - rate_oplead(bh.oplead, bh.pbn, bh.opleader, bh.minimax)
            realscore = calculate_score(bh.contract[0], realtricks, bh.contract[1], bh.declarer in bh.vuln)
            realscore = realscore * NSWEmult(bh.declarer)
            optimal = best_possible(bh.contract, bh.declarer, bh.bcalctable, bh.vuln)
            score = IMPs(realscore - optimal)
            score = score * NSWEmult(bh.opleader)
            #print(realscore, optimal, score)
            for pl in bh.players:
                if bh.players.index(pl) == REVPLAYERS[bh.opleader]:
                    if pl in results:
                        results[pl] = (results[pl][0] + score , results[pl][1] + 1)
                        #print("Adding {0} for {1} contract {0}".format(score, pl, bh.contract[0]))
                    else:
                        results[pl] = ((score, 1))
                        #print("Adding {0} for {1} contract {0}".format(score, pl, bh.contract[0]))
        except:
            continue
        counter = counter + 1
        if counter % 1000 == 0:
                    print(counter)
    return results


def assess_decl_after_op_lead(BHs):
    """Takes list of BridgeHand objects, returns dictionary with players/results"""
    results = {}
    counter = 0
    errors = 0
    scores = []
    for bh in BHs:
        try:
            optimaltricks = 13 - rate_oplead(bh.oplead, bh.pbn, bh.opleader, bh.minimax)
            optimalscore = calculate_score(bh.contract[0], optimaltricks, bh.contract[1], bh.declarer in bh.vuln)
            optimalscore = optimalscore * NSWEmult(bh.declarer)
            realscore = calculate_score(bh.contract[0], bh.tricks, bh.contract[1], bh.declarer in bh.vuln)
            realscore = realscore * NSWEmult(bh.declarer)
            score = IMPs(realscore - optimalscore)
            score = score * NSWEmult(bh.declarer)
            scores.append(score)
            #print(realscore, optimal, score)
            for pl in bh.players:
                if bh.players.index(pl) == REVPLAYERS[bh.declarer]:
                    if pl in results:
                        results[pl] = (results[pl][0] + score , results[pl][1] + 1)
                        #print("Adding {0} for {1} contract {2}".format(score, pl, bh.contract[0]))
                    else:
                        results[pl] = ((score, 1))
                        #print("Adding {0} for {1} contract {2}".format(score, pl, bh.contract[0]))
        except:
            errors = errors + 1
            continue
        counter = counter + 1
        if counter % 1000 == 0:
                    print(counter)
    print("ERRORS: {0}".format(errors))
    return results, scores


def ultimate_bid(BHs):
    """Takes list of BridgeHand objects, returns dictionary with players/results"""
    results = {}
    counter = 0
    scores = []
    for bh in BHs:
        try:
            #ttable = get_bcalc(bh.pbn)
            ttable = bh.bcalctable
            minmax = minimax(ttable, bh.vuln)
            optimaltricks = 13 - rate_oplead(bh.oplead, bh.pbn, bh.opleader, bh.minimax)
            optimalscore = calculate_score(bh.contract[0], optimaltricks, bh.contract[1], bh.declarer in bh.vuln)
            actual = optimalscore * NSWEmult(bh.declarer)
            score = IMPs(actual - minmax[0])
            scores.append(score)
            #print(minmax, actual, score)
            for pl in bh.players:
                if pl in results:
                    results[pl] = (results[pl][0] + score * NSWEmult(PLAYERS[bh.players.index(pl)]), results[pl][1] + 1)
                    #print("Adding {0} for {1} contract {2}".format(score * NSWEmult(PLAYERS[bh.players.index(pl)]), pl, bh.contract[0]))
                else:
                    results[pl] = ((score * NSWEmult(PLAYERS[bh.players.index(pl)])), 1)
                    #print("Adding {0} for {1} contract {2}".format(score * NSWEmult(PLAYERS[bh.players.index(pl)]), pl, bh.contract[0]))
        except:
            continue
        counter = counter + 1
        if counter % 1000 == 0:
            print(counter)
    return results, scores


def handhog(BHs):
    """Takes list of BridgeHand objects, returns dictionary with players/results"""
    results = {}
    counter = 0
    for bh in BHs:
        for pl in bh.players:
            if not results.get(pl):
                results[pl] = (0,0)
            if bh.players[REVPLAYERS[bh.declarer]] == pl:
                results[pl] = (results[pl][0] + 1, results[pl][1] + 1)
            else:
                results[pl] = (results[pl][0], results[pl][1] + 1)


            counter = counter + 1
        if counter % 1000 == 0:
            print(counter)
    return results


def ultimate_def(BHs):
    """Takes list of BridgeHand objects, returns dictionary with players/results"""
    results = {}
    counter = 0
    errors = 0
    for bh in BHs:
        try:
            optimaltricks = 13 - rate_oplead(bh.oplead, bh.pbn, bh.opleader, bh.minimax)
            optimalscore = calculate_score(bh.contract[0], optimaltricks, bh.contract[1], bh.declarer in bh.vuln)
            optimalscore = optimalscore * NSWEmult(bh.declarer)
            realscore = calculate_score(bh.contract[0], bh.tricks, bh.contract[1], bh.declarer in bh.vuln)
            realscore = realscore * NSWEmult(bh.declarer)
            score = IMPs(realscore - optimalscore)
            score = score * NSWEmult(bh.opleader)
            #print(realscore, optimal, score)
            for pl in bh.players:
                if bh.players.index(pl) != REVPLAYERS[bh.declarer] and bh.players.index(pl) != (REVPLAYERS[bh.declarer] + 2) % 4:
                    if pl in results:
                        results[pl] = (results[pl][0] + score , results[pl][1] + 1)
                        #print("Adding {0} for {1} contract {2}".format(score, pl, bh.contract[0]))
                    else:
                        results[pl] = ((score, 1))
                        #print("Adding {0} for {1} contract {2}".format(score, pl, bh.contract[0]))
        except:
            errors = errors + 1
            continue
        counter = counter + 1
        if counter % 1000 == 0:
                    print(counter)
    print("ERRORS: {0}".format(errors))
    return results


def ultimate_cardplay(BHs):
    """Takes list of BridgeHand objects, returns dictionary with players/results"""
    results = {}
    counter = 0
    errors = 0
    scores = []
    for bh in BHs:
        try:
            optimaltricks = 13 - rate_oplead(bh.oplead, bh.pbn, bh.opleader, bh.minimax)
            optimalscore = calculate_score(bh.contract[0], optimaltricks, bh.contract[1], bh.declarer in bh.vuln)
            optimalscore = optimalscore * NSWEmult(bh.declarer)
            realscore = calculate_score(bh.contract[0], bh.tricks, bh.contract[1], bh.declarer in bh.vuln)
            realscore = realscore * NSWEmult(bh.declarer)
            score = IMPs(realscore - optimalscore)
            scores.append(score)

            #print(realscore, optimal, score)
            for pl in bh.players:
                if bh.players.index(pl) != bh.players.index(bh.players[(REVPLAYERS[bh.declarer] + 2) % 4]):
                    if pl in results:
                        results[pl] = (results[pl][0] + score * NSWEmult(PLAYERS[bh.players.index(pl)]), results[pl][1] + 1)
                        #print("Adding {0} for {1} contract {2}".format(score, pl, bh.contract[0]))
                    else:
                        results[pl] = ((score * NSWEmult(PLAYERS[bh.players.index(pl)]), 1))
                            #print("Adding {0} for {1} contract {2}".format(score, pl, bh.contract[0]))
        except:
            errors = errors + 1
            continue
        counter = counter + 1
        if counter % 1000 == 0:
                    print(counter)
    print("ERRORS: {0}".format(errors))
    return results, scores


def cleannn(rating, num):
    clean_all_names(rating)
    for name in ["Nunes", "Brink", "Levin", "Cohen", "Greco", "Moss", "Levy", "Wang", "Mari", "Brink", "zia", "grue", "Lall",
                 "Hurd", "Kamil", "Wold", "Katz", "Moss"]:
        clean(rating, name)
    todel = []
    for k in rating:
        if rating[k][1] < num:
            todel.append(k)
    for k in todel:
        del rating[k]

    #for name in ["Cronier", "Willard", "Armin", "Auken", ""]:
    #    try:
    #        del rating[name]
    #    except:
    #        continue


def display_bbo(rat):
    players = list(rat)
    players.sort(key = lambda x : rat[x][0] / rat[x][1])
    players = reversed(players)
    for pl in players:
        print(("{0:<12} : {1:<6} , {2:<6} , avg: {3:.2f}".
               format(pl, rat[pl][0], rat[pl][1],rat[pl][0] / rat[pl][1])).
              replace(" ", "[space]"))


def statsforgarden(hands, players, opening, seqs, opshapes, finalcontract):
    gaz = search_for_sequence(hands, opening, players)
    gaz1 = search_for_sequence(hands, opening, players, opshape = opshapes)
    gaz2 = search_for_sequence(hands, seqs, players, opshape = opshapes)

    h = [x[0] for x in gaz2]
    const = []
    for x in h:
        if onesided(extract_bidding(x.hh)):
            const.append(x)

    gard = []
    for x in const:
        if x.contract[0][0] == finalcontract:
            gard.append(x)

    print("All hands: {0}".format(len(hands)))
    print("1D opening: {0}".format(len(gaz)))
    print("1D in range: {0}".format(len(gaz1)))
    print("1D p 1H or 1D p 1S: {0}".format(len(gaz2)))
    print("Opponents passed: {0}".format(len(const)))
    print("Stopped at 2 level: {0}".format(len(gard)))

    return gard


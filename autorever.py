#for now only works for constructive bidding
#
#values in seqs dictionary: [list of hands, alerts]

from bridgetools import *
import re
import pickle
import pdb


def bss_builder(revsystem, filename):
    temp = {}
    for key in revsystem:
        if key[:3] == 'PPP' or key[:2] == 'PP':
            pre = '50'
        else:
            pre = '60'
        newkey = pre + key.lstrip('P')
        if newkey in temp:
            temp[newkey][0].extend(list(revsystem[key][0]))
            temp[newkey][1].extend(list(revsystem[key][1]))
        else:
            temp[newkey] = (list(revsystem[key][0]), list(revsystem[key][1]))

    records = []
    for key in temp:
        records.append([key, temp[key]])
    records = sorted(records, key = lambda x: x[0])
    with open(filename, "w") as f:
        for r in records:
            f.write(r[0] + "=NYYYYYY3")
            if r[0][-1:] != "N":
                f.write("28") #28 is just random number to satisfy FD specs
            if len(r[1][1]) > 0: #alerts not empty
                for al in r[1][1]:
                    f.write("{0}, ".format(al.replace("\n", "")))
            f.write("{0} hands             ".format(len(r[1][0])))
            for pbn in r[1][0][:15]:
                f.write(beautiful_pbnhand(pbn))
                f.write("  ")
            f.write("\n")

def point_range(pbnhands):
    li = []
    for h in pbnhands:
        li.append(point_count(h))
    return (min(li), max(li))
    
                
def beautiful_pbnhand(pbnhand):
    symbols = ["C", "D", "H"]
    li = list(pbnhand)
    for i in range(len(li)):
        if li[i] == '.':
            li[i] = "!" + symbols.pop()
    return "!S" + "".join(li)
    

def reverse_engineer(hands, players):
    """Returns a dict with sequences being keys and (hands, alerts) as values"""
    alertre = re.compile(r"mb\|([^\|!]+)[^\|]+\|an\|([^\|]+)") #to extract bids without ! sign but still accept them
    const = []
    for pl in players:
        const.extend(extract_constructive(hands, pl))
    const = list(set(const))
    seqs = {}
    for h in const:
        h.biddingstr = "".join(extract_bidding(h.hh))
        alerts = alertre.findall(h.hh)
        for seq in prefixes(h.biddingstr):
            hand = h.pbn.split(" ")[(h.opener + 2*evenbids(seq)) % 4]
            if seq in seqs:
                seqs[seq][0].append(hand)
            else:
                seqs[seq] = [[hand], []]
            for al in alerts:
                if al[0] == seq[-2:] and len(al[1]) > 2:
                    #print("alert added")
                    seqs[seq][1].append(al[1])
    return seqs
            

def extract_constructive(hands, player):
    output = []
    for h in hands:
        bidding = extract_bidding(h.hh)
        for i in range(len(bidding)):
            bidding[i] = bidding[i].lower()
        if onesided(bidding):
            opener = get_opener(h)
            heropos = None
            for pl in h.players:
                if player.lower() in pl.lower():
                    heropos = h.players.index(pl)   
            if heropos is None:
                continue
            if opener == heropos or opener == (heropos + 2) % 4:
                output.append(h)
    return output


def prefixes(bidsequence):
    bidsequence = bidsequence.upper()
    bidsequence = bidsequence.rstrip('P')
    bidsequence = bidsequence.lstrip('-')
    
    output = []
    while len(bidsequence) >= 2:
        output.append(bidsequence)
        bidsequence = bidsequence[:-2].rstrip('P')
    return output


def evenbids(prefix):
    prefix = prefix.upper()
    prefix = prefix.replace('P', '')
    return len(prefix) % 4 == 0


def add_alerts(revsystem, hands):
    alertre = re.compile(r"mb\|([^\|!]+)an\|([^\|]+)")
    alerts = alertre.findall(hh)


if __name__ == "__main__":
    with open(r"D:\warsztatbrydz\STARS\ItaliansALL\hands\ita.p", "rb") as f:
            laver = pickle.load(f)
    laverc = extract_constructive(laver, "versace")
    laverc = extract_constructive(laverc, "lauria")
    for x in laverc:
            x.opener = get_opener(x)

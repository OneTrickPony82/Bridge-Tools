#this doesn't handle the simplest of obstacles like random end of line characters :)
import sys, re, io
import os, os.path
import urllib.request
import datetime

class VuLink:
  def __init__(self, download_link = None, date = None, players = None, event = None, segment = None):
    self.download_link = download_link
    self.date = date
    self.players = players
    self.event = event
    self.segment = segment
  def __repr__(self):
    return "Date: {0}\nEvent: {1}\nSegment: {2}\nURL: {3}\n".format(self.date, self.event, self.segment, self.download_link)

def vu_filter(data, player):
  output = []
  for vulink in data:
    for pl in vulink.players:
      if player.lower() in pl.lower():
        output.append(vulink)
        break
  return output

def event_filter(data, event, date):
  output = []
  for vulink in data:
    if event.lower() in vulink.event.lower() and datetime.date(*date) < vulink.date:
      output.append(vulink)
  return output
    
    

def vu_downloader(links, outputfolder = None):
  flag = 0
  counter = 1
  for link in links:
    print(counter)
    counter = counter+1
    conn = urllib.request.urlopen(link.download_link)
    data = conn.read()
    print('Downloaded, code: ' + str(conn.getcode()))
    conn.close()
    #writing to proper dir/file:
    dirpath = os.path.join(outputfolder, link.event[:16].strip()).replace("/", "-")
    if not os.access(dirpath, os.F_OK):
      os.makedirs(dirpath)
    if not os.access(os.path.join(dirpath , link.segment.strip() + ".lin"), os.F_OK):
      output_file = open(os.path.join(dirpath, link.segment.strip() + ".lin").replace("/", "-"), 'wb')
    else:
      flag = flag + 1
      output_file = open(os.path.join(dirpath,link.segment.strip() + str(flag) + ".lin"), 'wb')
    output_file.write(data)
    output_file.close()


def mega_download(player, folder, start_date = '1900-01-01', end_date = '2050-12-30'):
  start = datetime.date(int(start_date[0:4]), int(start_date[5:7]), int(start_date[8:10]))
  end = datetime.date(int(end_date[0:4]), int(end_date[5:7]), int(end_date[8:10]))
  player_vus = vu_filter(output, player)
  to_download = []
  for vu in player_vus:
    if start < vu.date < end:
      to_download.append(vu)
  print('Preparing to download {0} files'.format(len(to_download)))
  vu_downloader(to_download, folder)

#strip comments and add pg tags to stop action
def lin_strip_comments(path, onlycomments = False):
  try:
    with open(path, encoding = "UTF") as f:
      data = f.read()
      enc = "UTF"
  except:
    with open(path, encoding = "cp037") as f:
      data = f.read()
      enc = "cp037"
 
  output = []
  input = io.StringIO(data)
  outfile = open(path, 'w', encoding = enc)
  for line in input:
    newline = re.sub(r"(nt\|[^\|]*\|)", "", line)
    if not onlycomments:
      newline = newline.replace('|pc|', '|pg||pc|')
      newline = newline.replace('|mb|', '|pg||mb|')
    output.append(newline)
  for line in output:
    if line != 'pg||\n':
      outfile.write(line)
  outfile.close()

#executes lin_strip_comments for all files in path dir and subdirs (recursively)
def strip_all_comments(path, onlycomments = False):
  files_to_strip = []
  for root, dirs, files in os.walk(path):
    for name in files:
      if (os.path.splitext(name))[1] == '.lin':
        files_to_strip.append(os.path.join(root,name))
  for file in files_to_strip:
    lin_strip_comments(file, onlycomments)
    print('OK: ' + str(file))
    


#Stuff to count hands in given folder
def how_many_hands(path, enc = "UTF"):
  lin = open(path, encoding = enc)
  countero = 0
  counterc = 0
  for line in lin:
    if "qx|o" in line:
      countero = countero + 1
    if "qx|c" in line:
      counterc = counterc + 1
  return max(countero, counterc)


def find_lins(path):
  lins = []
  for root, dirs, files in os.walk(path):
    for name in files:
      if (os.path.splitext(name))[1] == '.lin':
        lins.append(os.path.join(root,name))
  return lins


def count_hands(path, enc = "latin2"):
  hands = 0
  lin = find_lins(path)
  for fi in lin:
    hands = hands + how_many_hands(fi, enc)
  return hands

if __name__ == '__main__':
  pass

def main():
  path = r"C:\Python31\2011input.html"
  inputfi = open(path)
  linkre = re.compile(r"View.+(http.+)\"")
  tdre = re.compile(r"<td>(.*)</td>")
  playersre = re.compile(r"<i>(.*)</i><br>(.*)<br>(.*)</td>")
  output = []
  counter = 0

  for line in inputfi:
    try:
      counter = counter + 6
      if line[0:5] != '</tr>':
        print('ERROR')
      if line == '</tr></table></center></body>\n':
        break;

      download_link = (linkre.findall(line))[0]   
      newline = inputfi.readline()                    #line to read event date
      date_string = (tdre.findall(newline))[0]
      date = datetime.date(int(date_string[0:4]), int(date_string[5:7]), int(date_string[8:10]))
      newline = inputfi.readline()                    #line to read event name
      event = (tdre.findall(newline))[0]
      newline = inputfi.readline()                    #line to read segment
      segment = (tdre.findall(newline))[0]
      newline = inputfi.readline()                    #line to read team/players names
      names = playersre.search(newline)
      team1 = names.group(1)
      player1 = names.group(2)
      player2 = names.group(3)
      newline = inputfi.readline()                    #as above
      names = playersre.search(newline)
      team2 = names.group(1)
      player3 = names.group(2)
      player4 = names.group(3)
      output.append(VuLink(download_link, date, [player1, player2, player3, player4], event, segment))
    except:
      print(counter)
      print(newline)
      break
    

  return output
  

  
  
  
  
  
  


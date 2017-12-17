#!/usr/bin/python

import csv
from itertools import izip, cycle, imap
import sys
import random
import ConfigParser
import pickle
import os
import textwrap
from boto import ses

class User:
  def __init__(self, name, email):
    self.name = name
    self.email = email

  def __repr__(self):
    return "%s <%s>" % (self.name, self.email)

  def __str__(self):
    return self.__repr__()

  def __eq__(self, other):
    if isinstance(other, basestring):
      return other == self.name
    else:
      return self.name == other.name and self.email == other.email

  def __ne__(self, other):
    return not self.__eq__(other)


blacklisted = [
  ('James', 'Andrea'),
  ('Katie', 'Alex'),
  ('Kate', 'Laura'),
]

def is_valid_pairing(list1, list2):
  global blacklisted
  for (user1, user2) in zip(list1, list2):
    if user1 == user2:
      return False
    elif any([(b1 == user1 and b2 == user2) or (b1 == user2 and b2 == user1)
              for (b1, b2) in blacklisted]):
      return False
  return True

def make_pairing(users):
  while True:
    shuffled = users[:]
    random.shuffle(shuffled)
    if is_valid_pairing(users, shuffled):
      return zip(users, shuffled)

def print_pairing(pairing):
  for (user1, user2) in pairing:
    print "%s <-> %s" % (user1, user2)

FROM = 'wcauchois@gmail.com'

def send_emails():
  config = ConfigParser.RawConfigParser(allow_no_value=True)
  config.readfp(open(os.path.expanduser('~/.aws/config'), 'r'))
  conn = ses.connect_to_region('us-east-1',
    aws_access_key_id=config.get('default', 'aws_access_key_id'),
    aws_secret_access_key=config.get('default', 'aws_secret_access_key'))

  pairings = load_encrypted_pairings()
  for (u1, u2) in pairings:
    emailbody = textwrap.dedent("""\
    Hi %s,<br>
    <br>
    You have been assigned <strong>%s</strong> as your secret santa.<br>
    <br>
    Please get them a gift and bring it to friendmas!<br>
    <br>
    See you there,<br>
    Bill/Christmasbot<br>
    """ % (u1.name, u2.name))
    conn.send_email(
      source=FROM,
      subject="Friendmas Secret Santa Assignment",
      body=emailbody,
      format="html",
      to_addresses=u1.email,
    )
    print "sent email to %s" % u1.email

ENCRYPTION_KEY = "happy christmas"
def xor_cycle(s):
  "encrypt or decrypt a string"
  return ''.join(list(imap(lambda x: chr(ord(x[0]) ^ ord(x[1])), izip(s, cycle(ENCRYPTION_KEY)))))

def load_encrypted_pairings():
  with open('pairings.encrypted', 'rb') as infile:
    return pickle.loads(xor_cycle(infile.read()))

def gen_pairings():
  with open('names.txt', 'r') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    users = [User(name, email) for [name, email] in reader]
    pairing = make_pairing(users) # [(user, user)]
    pickled = pickle.dumps(pairing)
    with open('pairings.encrypted', 'wb') as outfile:
      outfile.write(xor_cycle(pickled))

def decrypt_and_print_pairings():
  pairings = load_encrypted_pairings()
  for (u1, u2) in pairings:
    print "%s -> %s" % (u1, u2)

def check_sure():
  return raw_input("are you sure? [y/n] ").lower() == "y"

if __name__ == '__main__':
  if len(sys.argv) < 2:
    print "requires an argument"
    sys.exit(1)

  if sys.argv[1] == 'gen':
    gen_pairings()
    print "generated pairings, wrote to pairings.encrypted"
  elif sys.argv[1] == 'display':
    if check_sure():
      decrypt_and_print_pairings()
  elif sys.argv[1] == 'email':
    if check_sure():
      send_emails()
  else:
    print "unrecognized argument"
    sys.exit(1)


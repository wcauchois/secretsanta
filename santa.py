#!/usr/bin/env python

import csv
from itertools import cycle
import sys
import random
import configparser
import pickle
import os
import textwrap
from boto import ses
import argparse

class User:
  def __init__(self, name, email):
    self.name = name
    self.email = email

  def __repr__(self):
    return "%s <%s>" % (self.name, self.email)

  def __str__(self):
    return self.__repr__()

  def __eq__(self, other):
    if isinstance(other, str):
      return other == self.name
    else:
      return self.name == other.name and self.email == other.email

  def __ne__(self, other):
    return not self.__eq__(other)

def is_valid_pairing(list1, list2, blacklist):
  for (user1, user2) in zip(list1, list2):
    if user1 == user2:
      return False
    elif any([(b1 == user1 and b2 == user2) or (b1 == user2 and b2 == user1)
              for (b1, b2) in blacklist]):
      return False
  return True

def load_blacklist(filename):
  if os.path.exists(filename):
    with open(filename, 'r') as fp:
      return list(map(tuple, csv.reader(fp)))
  else:
    return []

def make_pairing(users, blacklist):
  while True:
    shuffled = users[:]
    random.shuffle(shuffled)
    if is_valid_pairing(users, shuffled, blacklist):
      return list(zip(users, shuffled))

def send_emails_with_check(args):
  if args.sure or check_sure():
    send_emails(args)

def get_aws_credentials():
  if 'AWS_ACCESS_KEY_ID' in os.environ and 'AWS_SECRET_ACCESS_KEY' in os.environ:
    return (os.environ['AWS_ACCESS_KEY_ID'], os.environ['AWS_SECRET_ACCESS_KEY'])
  else:
    aws_config_path = os.path.expanduser('~/.aws/config')
    if not os.path.exists(aws_config_path):
      raise Exception('Could not locate AWS credentials via any method')
    config = configparser.RawConfigParser(allow_no_value=True)
    config.readfp(open(aws_config_path, 'r'))
    return (
      config.get('default', 'aws_access_key_id'),
      config.get('default', 'aws_secret_access_key')
    )

def send_emails(args):
  config = configparser.RawConfigParser(allow_no_value=True)
  config.readfp(open(aws_config_path, 'r'))
  (aws_access_key_id, aws_secret_access_key) = get_aws_credentials()
  conn = ses.connect_to_region('us-east-1',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key)

  pairings = load_encrypted_pairings(args.pairings_file)

  with open(args.email_template, 'r') as fp:
    template_string = fp.read()

  for (u1, u2) in pairings:
    emailbody = template_string.format(user_name=u1.name, target_name=u2.name)
    conn.send_email(
      source=args.from_email,
      subject=args.email_subject,
      body=emailbody,
      format="html",
      to_addresses=u1.email,
    )
    print("Sent email to {}".format(u1.email))

ENCRYPTION_KEY = "happy christmas"
def xor_cycle(b):
  "encrypt or decrypt a byte array"
  if not isinstance(b, bytes):
    raise ValueError('expected `bytes` instance')
  return bytes(map(lambda x: x[0] ^ ord(x[1]), zip(b, cycle(ENCRYPTION_KEY))))

def load_encrypted_pairings(filename):
  with open(filename, 'rb') as infile:
    return pickle.loads(xor_cycle(infile.read()))

def gen_pairings(args):
  with open(args.names_file, 'r') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    users = [User(name, email) for [name, email] in reader]
  blacklist = load_blacklist(args.blacklist_file)
  pairing = make_pairing(users, blacklist) # [(user, user)]
  pickled = pickle.dumps(pairing)
  with open(args.pairings_file, 'wb') as outfile:
    outfile.write(xor_cycle(pickled))
  print('Generated pairings for {} people, wrote to {}'.format(len(users), args.pairings_file))

def decrypt_and_print_pairings(args):
  if args.sure or check_sure():
    pairings = load_encrypted_pairings(args.pairings_file)
    for (u1, u2) in pairings:
      print("{} -> {}".format(u1, u2))

def check_sure():
  return input("are you sure? [y/n] ").lower() == "y"

if __name__ == '__main__':
  parser = argparse.ArgumentParser(
    description='Utilities for managing a Secret Santa event')

  parent_parser = argparse.ArgumentParser(add_help=False)
  parent_parser.add_argument('-p', '--pairings', dest='pairings_file', default='pairings.encrypted',
    help='Specify the file for the encrypted set of pairings (default: pairings.encrypted)')

  sure_parser = argparse.ArgumentParser(add_help=False)
  sure_parser.add_argument('-y', dest='sure', action='store_true', default=False,
    help='Yes, I am sure')

  subparsers = parser.add_subparsers(title='subcommands', dest='subcommand')
  subparsers.required = True

  gen_parser = subparsers.add_parser('gen', parents=[parent_parser],
    help='Generate a set of secret santa pairings and write them out encrypted')
  gen_parser.add_argument('-n', '--names', dest='names_file', default='names.txt',
    help='Specify the file for the list of names and emails (default: names.txt)')
  gen_parser.add_argument('-b', '--blacklist', dest='blacklist_file', default='blacklist.txt',
    help='Specify the file for the pairings blacklist (default: blacklist.txt, OK if not present)')
  gen_parser.set_defaults(func=gen_pairings)

  display_parser = subparsers.add_parser('display', parents=[parent_parser, sure_parser],
    help='Decrypt and display the pairings file (will ask for confirmation)')
  display_parser.set_defaults(func=decrypt_and_print_pairings)

  email_parser = subparsers.add_parser('email', parents=[parent_parser, sure_parser],
    help='Send out emails with secret santa assignments')
  email_parser.add_argument('-e', '--email-template', dest='email_template', default='email-template.txt',
    help='Use the specified email template (default: email-template.txt)')
  email_parser.add_argument('-s', '--subject', dest='email_subject', default='Secret Santa Assignment',
    help='Specify a subject for the email')
  email_parser.add_argument('-f', '--from', dest='from_email', default='wcauchois@gmail.com',
    help='Specify a from address for the email')
  email_parser.set_defaults(func=send_emails_with_check)

  args = parser.parse_args()
  args.func(args)


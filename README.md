## Secret Santa Utility

`santa.py` helps you run a secret santa for your friends. You can generate a set of secret santa assignments between people, and then email everyone (using Amazon SES) with their assignments.

```
$ ./santa.py -h
usage: santa.py [-h] {gen,display,email} ...

Utilities for managing a Secret Santa event

optional arguments:
  -h, --help           show this help message and exit

subcommands:
  {gen,display,email}
    gen                Generate a set of secret santa pairings and write them
                       out encrypted
    display            Decrypt and display the pairings file (will ask for
                       confirmation)
    email              Send out emails with secret santa assignments
```
### Steps to Use

1. Create a `names.txt` file with the names of everyone involved in the secret santa and optionally a `blacklist.txt` file (see "Files" below for more info).
1. Run `./santa.py gen` to generate a set of secret Santa assignments.
2. Run `./santa.py email` to email everyone with their assignments. You will need AWS creds set up and you may want to customize the content of the email, see "Emailing" below.

### Emailing

The emailing functionality uses [Amazon Simple Email Service](https://aws.amazon.com/ses/). The script attempts to locate your AWS credentials via two methods:

- Reading the `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` environment variables.
- Reading credentials from the `[default]` section of the `~/.aws/config` file (if you use the `aws` commandline tool, you probably have this file set up).

Run `./santa.py email -h` for options you can use to customize the email (at the very least you should provide the `-f` or `--from` parameter), and see `email-template.txt` for the default/example email template.

### Files

There are a few files involved in the process.

`names.txt` should be a CSV file where each row is `[name of person],[email of person]`. Example:

```
Bill,billsemail@example.com
James,jamesemail@example.com
```

---

`blacklist.txt` is an _optional_ file wherein you can blacklist certain assignments from being generated. This is useful for i.e. significant others. It should be a CSV file of `[name of person from names.txt],[name of person]`. Example:

```
Bill,James
```

This would prevent Bill and James from ever getting assigned to each other (both ways).

---

`pairings.encrypted` is the set of secret santa assignments generated by the `./santa.py gen` command. It's not very securely encrypted, it's just XORed with a key, the only reason it's obfuscated in this way is so that you don't accidentally `cat` it. Use `./santa.py display` to decrypt and show it, but it's recommended you keep everything secret.

The file names used here are the defaults, you can also use command-line arguments to override the names.

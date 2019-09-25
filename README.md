# handshook
## Introduction
Handshook is a Handshake applicator. It automatically applies to easy jobs on Handshake, i.e. jobs that require only resume and/or transcript.

## Dependencies
The script uses `requests` library.

## Usage
You need to provides this program three things:
* Your jobs search string
* Your cookies
* Your resume ID and transcript ID

You can obtain the job search string by just search normally for jobs, and copy the search url string. Please sort the jobs by latest first!

For cookies, follow the example in `conf.json`, copy the names and values from the domain `.joinhandshake.com` to that file.
The reason cookies are used because I don't have access to neither the CalCentral Login API nor Handshake API.

To get the resume ID and transcript ID just go to those documents and copy the number after `users/`.

Finally put those things in `config.json` and set `valid` to `true`. Run the script and enjoy!

## Note
This is still in development. I'll add features such as notification via email when your cookies don't work, and make it save work better so you can just set up it as a cron job and don't worry about applying anymore!
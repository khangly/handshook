# handshook
## Introduction
Handshook is a Handshake applicator. It automatically applies to easy jobs on Handshake, i.e. jobs that require only resume or cover letter or transcript.

## Dependencies
The script uses `requests` library.

## Usage
You need to provides this program three things:
* Your jobs search string
* Your cookies
* Your resume ID, cover letter ID, and transcript ID

You can obtain the job search string by just search normally for jobs, and copy the search url string. Please sort the jobs by "Date Posted"! The link looks like
```
https://berkeley.joinhandshake.com/postings?page=1&per_page=25&sort_direction=desc&sort_column=created_at&job.student_screen.disable_majors=true&job.student_screen.disable_school_years=true&job.student_screen.disable_graduation_date=true&job.student_screen.disable_work_auth=true&job.student_screen.disable_gpa=true&job.job_types%5B%5D=3&job.salary_types%5B%5D=1&qualified_only=false&majors%5B%5D=14484&majors%5B%5D=28
```

For cookies, follow the example in `conf.json`, copy the names and values from the domain `.joinhandshake.com` to that file. If you use Firefox, login to Handshake and go to developer mode by pressing <kbd>F12</kbd> or just by right clicking somewhere on the page and choose "Inspect Element". Then go to "Storage" tab, click on https://berkeley.joinhandshake.com and copy the cookies from there.
The reason I use cookies is because I don't have access to neither the CalCentral Login API nor Handshake API.

To get the resume ID, cover letter ID, and transcript ID go to those documents and copy the number after `documents#`. The link looks like
```
https://berkeley.joinhandshake.com/users/12345678/documents#12345678
```

Finally put those things in `config.json` and set `valid` to `true`. Run the script and enjoy!

## Note
Let me know if anything goes wrong!
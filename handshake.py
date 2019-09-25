import requests
import json
import datetime

CONF_FILE = "conf.json"
JOBS_FILE = "jobs.csv"
WAIT_FILE = "wait.json"
LEN_CSRF = 88
HOST = "berkeley.joinhandshake.com"
ACCEPT_GET = "application/json"
ACCEPT_POST = "application/json, text/javascript, */*; q=0.01"
CONTENT_TYPE = "application/json; charset=utf-8"
RESUME_TYPE_ID = 1
TRANSCRIPT_TYPE_ID = 3


def read_conf():
    """Read the configuration file and return Json Data, Valid, URL, Cookie, Date, Resume ID, Transcript ID"""
    with open(CONF_FILE, "r") as conf_file:
        data = json.load(conf_file)
        valid = data["valid"]
        URL = data["url"].replace("page=1&", '')
        cookies = data["cookies"]
        date = data["date"]
        resume = data["resume"]
        transcript = data["transcript"]
        return data, valid, URL, cookies, date, resume, transcript


def get_csrf_token(session):
    """Get the CSRF-Token, which is required when submitting an application"""
    page = session.get('https://berkeley.joinhandshake.com')
    index = page.text.find("<meta name=\"csrf-token\" content=\"") + len("<meta name=\"csrf-token\" content=\"")
    return page.text[index: index + LEN_CSRF]


class Job:

    def __init__(self, data):
        self.data = data
        self.start = data["apply_start"]
        self.date = data["updated_at"]
        self.id = data["job_id"]
        self.name = data["job_name"]
        self.employer = data["employer_name"]
        self.type = data["job"]["type"]
        self.apply_type = data["job"]["job_apply_setting"]["apply_type"]
        self.documents = [document_type["document_type_id"] for document_type in
                          data["job"]["required_job_document_types"]]

    @classmethod
    def set(cls, session, date, resume, transcript):
        """Set various attributes"""
        cls.session = session
        cls.date = date
        cls.resume = resume
        cls.transcript = transcript
        cls.csrf_token = get_csrf_token(session)
        cls.now = datetime.datetime.utcnow().isoformat()

    def apply(self):
        """Apply to this job, return 0 if succeed, return 1 if cookie errors, 2 if cover letter required,
            3 if not opened yet, 4 if the job requires applying externally"""
        if self.apply_type != "handshake":
            return 4
        if self.start > self.now:
            return 3
        if 2 in self.documents:
            return 2
        headers = {"Accept": ACCEPT_POST, "Host": HOST, "X-CSRF-Token": self.csrf_token, "Content-Type": CONTENT_TYPE}
        document_ids = list()
        for document in self.documents:
            if document == RESUME_TYPE_ID:
                document_ids.append(self.resume)
            else:
                document_ids.append(self.transcript)
        data = json.dumps(
            {"application": {"applicable_id": self.id, "applicable_type": self.type, "document_ids": document_ids},
             "work_authorization_status": None})
        result = self.session.post('https://berkeley.joinhandshake.com/jobs/' + str(self.id) + "/applications",
                                   headers=headers, data=data)
        if result.status_code != requests.codes.ok:
            print(result.text)
            return 1
        return 0

    def wait(self, waitlist):
        """Add to WAITLIST"""
        waitlist.append(self.data)

    def write(self, jobs_file):
        """Write job info to JOBS_FILE"""
        jobs_file.write(str(self.id) + ", \"" + self.name + "\", \"" + self.employer + "\", " + self.now + '\n')


def process():
    configs, valid, URL, cookie, date, resume, transcript = read_conf()
    cookie_error = False

    if not valid:
        print("Set the conf.json file or update your cookie")
        return

    session = requests.Session()
    session.cookies.update(cookie)

    Job.set(session, date, resume, transcript)
    with open(WAIT_FILE, "r") as wait_file:
        original_waitlist = json.load(wait_file)
    waitlist = list()
    jobs_file = open(JOBS_FILE, 'a')

    for job_data in original_waitlist:
        job = Job(job_data)
        ret = job.apply()
        if ret != 0:
            if ret == 3:
                job.wait(waitlist)
            elif ret == 1:
                cookie_error = True
                break
        else:
            job.write(jobs_file)

    page = 1
    while not cookie_error:
        jobs = session.get(URL + "&page=" + str(page), headers={"Host": HOST, "Accept": ACCEPT_GET}).json()
        for job_data in jobs["results"]:
            job = Job(job_data)
            if date > job.date:
                break
            ret = job.apply()
            if ret != 0:
                if ret == 3:
                    job.wait(waitlist)
                elif ret == 1:
                    cookie_error = True
                    break
            else:
                job.write(jobs_file)
        page += 1

    configs["valid"] = cookie_error
    configs["cookies"] = requests.utils.dict_from_cookiejar(session.cookies)
    with open(WAIT_FILE, 'w') as wait_file:
        json.dump(wait_file, waitlist)
    with open(CONF_FILE, 'w') as conf_file:
        json.dump(configs, conf_file)
    jobs_file.close()


process()

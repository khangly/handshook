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
COVER_TYPE_ID = 2
TRANSCRIPT_TYPE_ID = 3


def sanitize_url(url):
    left = url.find("page=")
    if left != -1:
        right = url.find('&', left)
        if right != -1:
            return url[:left] + url[right + 1:]
        return url[:left]
    return url


def read_conf():
    """Read the configuration file and return the dictionary representation of configs."""
    with open(CONF_FILE, "r") as conf_file:
        configs = json.load(conf_file)
        configs["url"] = sanitize_url(configs["url"])
        return configs


def read_wait_file():
    """Read the wait file that contains jobs which were not applied to in the previous run."""
    try:
        wait_file = open(WAIT_FILE, 'r')
        waited_jobs = json.load(wait_file)
        wait_file.close()
    except FileNotFoundError:
        waited_jobs = list()
    return waited_jobs


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
        self.document_type_ids = [document_type["document_type_id"] for document_type in
                                  data["job"]["required_job_document_types"]]

    @classmethod
    def set(cls, session, configs):
        """Set various attributes"""
        cls.session = session
        cls.date = configs["date"]
        cls.documents = {RESUME_TYPE_ID: configs["resume"], COVER_TYPE_ID: configs["cover"],
                         TRANSCRIPT_TYPE_ID: configs["transcript"]}
        cls.csrf_token = get_csrf_token(session)
        cls.now = datetime.datetime.utcnow().isoformat()

    def apply(self):
        """Apply to this job, return 0 if succeed, return 1 if cookie errors, 2 if not opened yet,
        3 if the job requires applying externally, 4 if the job required other documents"""
        if self.apply_type != "handshake":
            return 3
        if self.start and self.start > self.now:
            return 2
        headers = {"Accept": ACCEPT_POST, "Host": HOST, "X-CSRF-Token": self.csrf_token, "Content-Type": CONTENT_TYPE}
        document_ids = list()
        for document_type_id in self.document_type_ids:
            if document_type_id not in (RESUME_TYPE_ID, COVER_TYPE_ID, TRANSCRIPT_TYPE_ID):
                return 4
            document_ids.append(self.documents[document_type_id])
        data = json.dumps(
            {"application": {"applicable_id": self.id, "applicable_type": self.type, "document_ids": document_ids},
             "work_authorization_status": None})
        result = self.session.post('https://berkeley.joinhandshake.com/jobs/' + str(self.id) + "/applications",
                                   headers=headers, data=data)
        if result.status_code != requests.codes.ok:
            return 1
        print("Applied to %s successfully!" % self.name)
        return 0

    def wait(self, wait_list):
        """Add to WAIT_LIST"""
        wait_list.append(self.data)

    def write(self, jobs_file):
        """Write job info to JOBS_FILE"""
        jobs_file.write("%d, \"%s\", \"%s\", \"%s\"\n" % (self.id, self.name, self.employer, self.now))


def main():
    configs = read_conf()
    cookie_error = False
    if not configs["valid"]:
        print("RTFM!!!")
        exit(1)

    session = requests.Session()
    session.cookies.update(configs["cookies"])
    Job.set(session, configs)

    waited_list = read_wait_file()
    wait_list = list()
    jobs_file = open(JOBS_FILE, 'a+')
    for job_data in waited_list:
        job = Job(job_data)
        ret = job.apply()
        if ret != 0:
            if ret == 2:
                job.wait(wait_list)
            elif ret == 1:
                cookie_error = True
                break
        else:
            job.write(jobs_file)

    page = 1
    see_old_jobs = False
    date = datetime.datetime.utcnow().isoformat()
    while not cookie_error and not see_old_jobs:
        jobs = session.get(configs["url"] + "&page=" + str(page), headers={"Host": HOST, "Accept": ACCEPT_GET}).json()
        if "results" not in jobs:
            break
        for job_data in jobs["results"]:
            job = Job(job_data)
            if configs["date"] > job.date:
                see_old_jobs = True
                break
            ret = job.apply()
            if ret != 0:
                if ret == 2:
                    job.wait(wait_list)
                elif ret == 1:
                    cookie_error = True
                    break
            else:
                job.write(jobs_file)
        page += 1

    configs["valid"] = not cookie_error
    configs["cookies"] = requests.utils.dict_from_cookiejar(session.cookies)
    if cookie_error:
        print("Cookies are not valid, please provide new ones!!!")
    else:
        configs["date"] = date
        with open(WAIT_FILE, 'w') as wait_file:
            json.dump(wait_list, wait_file)
    with open(CONF_FILE, 'w') as conf_file:
        json.dump(configs, conf_file)
    jobs_file.close()


if __name__ == '__main__':
    main()

#!/usr/bin/python3
# BSD 3-Clause License
#
# Copyright (c) 2025, Geoffrey Argence <argence.geoffrey@gmail.com>
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import requests
import re
import sys
from typing import *

class RepositoryMetaData:

    organization:   str
    project:        str
    repositoryId:   str
    password:       Optional[str]
    headers:        Dict[str, str] # Dict[header, value]

    def __init__(self, organization: str, project: str, repositoryId: str, password: Optional[str] = None):
        self.organization = organization
        self.project = project
        self.repositoryId = repositoryId
        self.headers = {"Content-Type": "application/json"}
        if password:
            self.password = password
            self.headers["Authorization"] = f"Bearer {password}"
        else:
            password = None

    @staticmethod
    def from_url(url: str, password: Optional[str] = None) -> 'RepositoryMetaData':
        m = re.match("https://dev.azure.com/([^/]+)/([^/]+)/_git/([^/]+)", url)
        if m:
            return RepositoryMetaData(m.group(1), m.group(2), m.group(3), password)
        else:
            raise ValueError("URL is invalid, must be like http://dev.azure.com/{organization}/{project}/_git/{repositoryId}") # Not a format !



class PullRequestMetaData(RepositoryMetaData):

    organization:   str
    project:        str
    repositoryId:   str
    pullRequestId:  str
    password:       Optional[str]
    headers:        Dict[str, str] # Dict[header, value]

    def __init__(self, organization: str, project: str, repositoryId: str, pullRequestId: str, password: Optional[str] = None):
        self.organization = organization
        self.project = project
        self.repositoryId = repositoryId
        self.pullRequestId = pullRequestId
        self.headers = {"Content-Type": "application/json"}
        if password:
            self.password = password
            self.headers["Authorization"] = f"Bearer {password}"
        else:
            password = None

    @staticmethod
    def from_url(url: str, password: Optional[str] = None) -> 'PullRequestMetaData':
        m = re.match("https://dev.azure.com/([^/]+)/([^/]+)/_git/([^/]+)/pullrequest/([^/]+)", url)
        if m:
            return PullRequestMetaData(m.group(1), m.group(2), m.group(3), m.group(4), password)
        else:
            raise ValueError("URL is invalid, must be like http://dev.azure.com/{organization}/{project}/_git/{repositoryId}/pullrequest/{pullRequestId}") # Not a format !



class UserDataBase:

    users:          Dict[str, str] # Dict[uid, name]
    organization:   str
    headers:        Optional[Dict[str, str]] # Dict[header, value]

    def __init__(self, rmd: RepositoryMetaData):
        self.users = dict()
        self.organization = rmd.organization
        self.headers = rmd.headers

    def __getitem__(self, key: str) -> str:
        if key not in self.users.keys():
            try:
                url = f"https://vssps.dev.azure.com/{self.organization}/_apis/identities/{key}?api-version=7.1"
                r = requests.get(url, headers = self.headers)
                r.raise_for_status()
                if r.status_code != 200:
                    raise IOError(f"Invalid server response: {r.status_code}")
                j = r.json()
                self.users[key] = j["providerDisplayName"]
            except (requests.HTTPError, IOError):
                self.users[key] = f"<{key}>" # Keep original input but store it to avoid requesting it again
                print(f"Warning, did not success to retrieve user {key}", file = sys.stderr)

        return self.users[key]

    def __setitem__(self, key, value):
        raise AttributeError("UserDataBase: Manual data appending is not allowed")



class FileDataBase:

    files:  Dict[str, List[str]] # Dict[path, content]
    rmd:    RepositoryMetaData
    commit: str

    def __init__(self, rmd: RepositoryMetaData, commit: str):
        self.files = dict()
        self.rmd = rmd
        self.commit = commit

    def __getitem__(self, path: str) -> List[str]:
        if path not in self.files.keys():
            try:
                url = f"https://dev.azure.com/{self.rmd.organization}/{self.rmd.project}/_apis/git/repositories/{self.rmd.repositoryId}/items?path={path}&versionDescriptor.versionType=commit&versionDescriptor.version={self.commit}&api-version=7.1"
                r = requests.get(url, headers = self.rmd.headers)
                r.raise_for_status()
                if r.status_code != 200:
                    raise IOError(f"Invalid server response: {r.status_code}")
                self.files[path] = r.text.splitlines()
            except (requests.HTTPError, IOError):
                self.files[path] = ""
                print(f"Warning, did not success to retrieve file {path} from commit {self.commit}", file = sys.stderr)

        return self.files[path]

    def __setitem__(self, key, value):
        raise AttributeError("FileDataBase: Manual data appending is not allowed")



class VersionDataBase:

    versions:   Dict[str, FileDataBase] # Dict[commit, FileDataBase]
    rmd:        RepositoryMetaData

    def __init__(self, rmd: RepositoryMetaData):
        self.versions = dict()
        self.rmd = rmd

    def __getitem__(self, commit: str) -> FileDataBase:
        if commit not in self.versions.keys():
            self.versions[commit] = FileDataBase(self.rmd, commit)

        return self.versions[commit]

    def __setitem__(self, key, value):
        raise AttributeError("VersionDataBase: Manual data appending is not allowed")



# For typing information
class FilePosition(TypedDict):
    line:   int
    offset: int

# For typing information
class FileContext(TypedDict): # The context can be a file
    filePath:       str

# For typing information
class DetailedFileContext(FileContext): # Or the context can be a part of a file
    filePath:       str
    rightFileStart: FilePosition
    rightFileEnd:   FilePosition



class ThreadContextQuote:

    startLine:  int
    startOff:   int
    endLine:    int
    endOff:     int
    file:       List[str]

    def __init__(self, fc: DetailedFileContext, file: List[str]):
        rightFileStart = fc["rightFileStart"]
        rightFileEnd = fc["rightFileEnd"]

        self.startLine = int(rightFileStart["line"]) - 1
        self.startOff = int(rightFileStart["offset"]) - 1
        self.endLine = int(rightFileEnd["line"]) - 1
        self.endOff = int(rightFileEnd["offset"]) - 1

        self.file = file

    def getContext(self) -> List[str]:
        finalContent = list()
        if self.startLine == self.endLine:
            finalContent.append(self.file[self.startLine][self.startOff:self.endOff])
        else:
            finalContent.append(self.file[self.startLine][self.startOff:])
            for line in self.file[self.startLine + 1: self.endLine]:
                finalContent.append(line)
            finalContent.append(self.file[self.endLine][:self.endOff])

        return finalContent

    def getLinesBeforeContext(self, count: int = 2) -> List[str]:
        ret = list()
        for i in range(max(self.startLine - count, 0), self.startLine):
            ret.append(self.file[i])

        return ret

    def getCharsBeforeContext(self) -> str:
        return self.file[self.startLine][0:self.startOff]

    def getLinesAfterContext(self, count: int = 2) -> List[str]:
        ret = list()
        for i in range(self.endLine + 1, min(self.endLine + count + 1, len(self.file))):
            ret.append(self.file[i])

        return ret

    def getCharsAfterContext(self) -> str:
        return self.file[self.endLine][self.endOff:]

    def debug(self):

        print("file: ")

        for line in self.getLinesBeforeContext():
            print(line)

        context = self.getContext()
        if len(context) > 1:
            print(f"{self.getCharsBeforeContext()}>>>{context[0]}")
            for line in context[1:-1]:
                print(line)
            print(f"{context[-1]}<<<{self.getCharsAfterContext()}")
        else:
            assert(len(context) == 1), "Context should at least contain one empty line"
            print(f"{self.getCharsBeforeContext()}>>>{context[0]}<<<{self.getCharsAfterContext()}")

        for line in self.getLinesAfterContext():
            print(line)



class ThreadContext:

    filePath:   str
    commit:     str
    file:       List[str]
    quote:      Optional[ThreadContextQuote]

    def __init__(self, fc: FileContext, vdb: VersionDataBase, commit: str):
        self.filePath = fc["filePath"]
        self.commit = commit
        self.file = vdb[commit][self.filePath]

        try:
            self.quote = ThreadContextQuote(fc, self.file)
        except KeyError:
            self.quote = None

    def debug(self):
        print(f"On commit {self.commit}:")
        print(f"On file {self.filePath}:")
        if self.quote:
            self.quote.debug()



class Comment:

    author:     str
    pubDate:    str
    lstUpdDate: str
    content:    str

    def __init__(self, author: str, pubDate: str, lstUpdDate: str, content: str):
        self.author = author
        self.pubDate = pubDate
        self.lstUpdDate = lstUpdDate
        self.content = content

    def debug(self):
        print(f"{self.author} ({self.pubDate}/{self.lstUpdDate}):")
        print(self.content)



class CommentThread:

    commit:     str
    context:    Optional[ThreadContext]
    comments:   List[Comment]
    vdb:        VersionDataBase
    udb:        UserDataBase

    def __init__(self, thread: Dict, commit: str, vdb: VersionDataBase, udb: UserDataBase):
        self.commit = commit
        self.vdb = vdb
        self.udb = udb

        if "threadContext" in thread.keys() and thread["threadContext"]:
            self.context = ThreadContext(thread["threadContext"], vdb, commit)
        else:
            self.context = None

        if "comments" not in thread.keys() or len(thread["comments"]) < 1:
            raise ValueError()

        self.comments = list()

        for comment in thread["comments"]:

            if comment["author"]["uniqueName"] and comment["commentType"] == "text" and ("isDeleted" not in comment.keys() or not comment["isDeleted"]):

                def replace_user_mentions(text, udb: UserDataBase):
                    p = re.compile(r"(.*)@<([-a-zA-Z0-9]*)>(.*)")
                    didMatch = True
                    while didMatch:
                        didMatch = False
                        m = p.search(text)
                        if m:
                            text = f"{m.group(1)}@{udb[m.group(2)]}{m.group(3)}"
                            didMatch = True
                    return text

                if "content" not in comment.keys():
                    print("Warning: no content in comment")

                self.comments.append(Comment(comment["author"]["displayName"], comment["publishedDate"], comment["lastContentUpdatedDate"], replace_user_mentions(comment["content"], udb)))

    def debug(self):
        if self.context:
            self.context.debug()
        for comment in self.comments:
            comment.debug()
            print()



class PullRequest:

    prmd:   PullRequestMetaData
    vdb:    VersionDataBase
    udb:    UserDataBase

    def __init__(self, prmd: PullRequestMetaData, vdb: Optional[VersionDataBase] = None, udb: Optional[UserDataBase] = None):
        self.prmd = prmd
        self.vdb = vdb if vdb else VersionDataBase(self.prmd)
        self.udb = udb if udb else UserDataBase(self.prmd)

    def get(self) -> List[CommentThread]:

        prurl = f"https://dev.azure.com/{self.prmd.organization}/{self.prmd.project}/_apis/git/repositories/{self.prmd.repositoryId}/pullRequests/{self.prmd.pullRequestId}/iterations?api-version=7.1"
        threadsurl = f"https://dev.azure.com/{self.prmd.organization}/{self.prmd.project}/_apis/git/repositories/{self.prmd.repositoryId}/pullRequests/{self.prmd.pullRequestId}/threads?api-version=7.1"

        r = requests.get(prurl, headers = self.prmd.headers)
        r.raise_for_status()
        if r.status_code != 200:
            raise IOError(f"Invalid server response: {r.status_code}")
        j = r.json()
        if len(j["value"]) < 1:
            return list()

        commit = j["value"][0]["sourceRefCommit"]["commitId"]

        r = requests.get(threadsurl, headers = self.prmd.headers)
        r.raise_for_status()
        if r.status_code != 200:
            raise IOError(f"Invalid server response: {r.status_code}")

        j = r.json()

        thread_list = list()

        for thread in j["value"]:

            if "CodeReviewRefNewHeadCommit" in thread["properties"].keys():
                commit = thread["properties"]["CodeReviewRefNewHeadCommit"]["$value"]

            if thread["comments"] :
                for comment in thread["comments"]:
                    if comment["author"]["uniqueName"] and comment["commentType"] == "text" and ("isDeleted" not in comment.keys() or not comment["isDeleted"]):
                        thread_list.append(CommentThread(thread, commit, self.vdb, self.udb))
                        break

        return thread_list

    def debug(self):
        print(f"Pull Request {self.prmd.pullRequestId}")
        for thread in self.get():
            thread.debug()
            print("=" * 80)



class Repository:

    rmd:    RepositoryMetaData
    vdb:    VersionDataBase
    udb:    UserDataBase

    def __init__(self, rmd: RepositoryMetaData, vdb: Optional[VersionDataBase] = None, udb: Optional[UserDataBase] = None):
        self.rmd = rmd
        self.vdb = vdb if vdb else VersionDataBase(self.rmd)
        self.udb = udb if udb else UserDataBase(self.rmd)

    def get(self) -> List[PullRequest]:
        url = f"https://dev.azure.com/{self.rmd.organization}/{self.rmd.project}/_apis/git/repositories/{self.rmd.repositoryId}/pullrequests?searchCriteria.status=all&api-version=7.1"
        r = requests.get(url, headers = self.rmd.headers)
        r.raise_for_status()
        if r.status_code != 200:
            raise IOError(f"Invalid server response: {r.status_code}")
        pull_requests = r.json()
        pr_list = list()
        for pr in pull_requests["value"]:
            prmd = PullRequestMetaData(self.rmd.organization, self.rmd.project, self.rmd.repositoryId, pr["pullRequestId"], self.rmd.password)
            pr_list.append(PullRequest(prmd, self.vdb, self.udb))
        
        return pr_list

    def debug(self):
        print(f"Repository {self.rmd.repositoryId}")
        for pr in self.get():
            pr.debug()
            print("=" * 80)
            print("=" * 80)
            print("=" * 80)



if __name__ == "__main__":

    import argparse
    parser = argparse.ArgumentParser(description="Quick main to show data retrieved by the module.")
    parser.add_argument("url", type=str, help="Pull request or repository url")
    parser.add_argument("-p", "--password", type=str, help="Token API to use to access the server")
    args = parser.parse_args()

    if "pullrequest" in args.url:
        prmd = PullRequestMetaData.from_url(
            url = args.url,
            password = args.password
        )
        PullRequest(prmd).debug()
    else:
        rmd = RepositoryMetaData.from_url(
            url = args.url,
            password = args.password
        )
        Repository(rmd).debug()


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
"""
Module to fetch and treat Azure Devops pull requests and comments.
This module provides classes to interact with Azure Devops API and retrieve
pull requests and comments from a given repository.

Classes:
    RepositoryMetaData:
        Simple class holding all data needed to create a Repository object.
    PullRequestMetaData:
        Simple class holding all data needed to create a PullRequest object.
    UserDataBase:
        A cache/request API to get user name from id.
    FileDataBase:
        A cache/request API to get file content from the server for a given repository and commit id.
    VersionDataBase:
        A cache interface to store FileDataBase objects for different versions of a given repository.
    FilePosition:
        Class to represent a position in a file.
    FileContext:
        Class to represent a file context on the whole file.
    DetailedFileContext:
        Class to represent a file context on a file part.
    ThreadContextQuote:
        Delimits the part of the file quoted by the comment.
    ThreadContext:
        The file or file part concerned by the comment.
    Comment:
        Text of a comment and various metadata.
    CommentThread:
        Contains a comment along with its associated commit, context and replies.
    PullRequest:
        A request interface to fetch the pull requests associated with a repository.
    Repository:
        A request interface to fetch the pull requests associated with a repository.
"""

import requests
import re
import sys
from typing import *

class RepositoryMetaData:
    """
    Simple class holding all data needed to create a Repository object.

    Attributes:
        organization (str):
            Azure Devops organization name.
        project (str):
            Azure Devops project name.
        repositoryId (str):
            Azure Devops repositoryId.
        password (Optional[str]):
            Azure Devops API token.
        headers (Dict[str, str]):
            HTTP headers for requests.

    Methods:
        __init__(organization, project, repositoryId, password[optional]):
            Creates a RepositoryMetaData with provided values.
        from_url(url, password[optional]) [static]:
            Creates a RepositoryMetaData from the given url of an Azure Devops repository.
    """

    def __init__(self, organization: str, project: str, repositoryId: str, password: Optional[str] = None):
        """
        Creates a RepositoryMetaData with provided values.

        Args:
            organization (str):
                Azure Devops organization name.
            project (str):
                Azure Devops project name.
            repositoryId (str):
                Azure Devops repositoryId.
            password (Optional[str]):
                Azure Devops API token.
        """
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
        """
        Creates a RepositoryMetaData from the given url of an Azure Devops repository.

        Args:
            url (str):
                url of an Azure Devops repository.
            password (Optional[str]):
                Azure Devops API token.

        Returns:
            RepositoryMetaData:
                RepositoryMetaData object from the given url and password.

        Raises:
            ValueError:
                If the provided url is invalid.
        """
        m = re.match("https://dev.azure.com/([^/]+)/([^/]+)/_git/([^/]+)", url)
        if m:
            return RepositoryMetaData(m.group(1), m.group(2), m.group(3), password)
        else:
            raise ValueError("URL is invalid, must be like http://dev.azure.com/{organization}/{project}/_git/{repositoryId}") # Not a format !



class PullRequestMetaData(RepositoryMetaData):
    """
    Simple class holding all data needed to create a PullRequest object.
    Inherits from RepositoryMetaData.

    Attributes:
        organization (str):
            Azure Devops organization name.
        project (str):
            Azure Devops project name.
        repositoryId (str):
            Azure Devops repositoryId.
        pullRequestId (str):
            Azure Devops pullRequestId.
        password (Optional[str]):
            Azure Devops API token.
        headers (Dict[str, str]):
            HTTP headers for requests.

    Methods:
        __init__(organization, project, repositoryId, pullRequestId, password[optional]):
            Creates a PullRequestMetaData with provided values.
        from_url(url, password[optional]) [static]:
            Creates a PullRequestMetaData from the given url of an Azure Devops pull request.
    """

    def __init__(self, organization: str, project: str, repositoryId: str, pullRequestId: str, password: Optional[str] = None):
        """
        Creates a PullRequestMetaData with provided values.

        Args:
            organization (str):
                Azure Devops organization name.
            project (str):
                Azure Devops project name.
            repositoryId (str):
                Azure Devops repositoryId.
            pullRequestId (str):
                Azure Devops pullRequestId.
            password (Optional[str]):
                Azure Devops API token.
        """
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
        """
        Creates a PullRequestMetaData from the given url of an Azure Devops repository.

        Args:
            url (str):
                url of an Azure Devops pull request.
            password (Optional[str]):
                Azure Devops API token.

        Returns:
            PullRequestMetaData:
                PullRequestMetaData object from the given url and password.

        Raises:
            ValueError:
                If the provided url is invalid.
        """
        m = re.match("https://dev.azure.com/([^/]+)/([^/]+)/_git/([^/]+)/pullrequest/([^/]+)", url)
        if m:
            return PullRequestMetaData(m.group(1), m.group(2), m.group(3), m.group(4), password)
        else:
            raise ValueError("URL is invalid, must be like http://dev.azure.com/{organization}/{project}/_git/{repositoryId}/pullrequest/{pullRequestId}") # Not a format !



class UserDataBase:
    """
    A cache/request API to get user name from id.
    Behaves like a Dict[uid, name].

    Attributes:
        users (Dict[str, str]):
            Dictionary mapping user id to user name.
        organization (str):
            Azure Devops organization name.
        headers (Optional[Dict[str, str]]):
            HTTP headers for requests.

    Methods:
        __init__(rmd: RepositoryMetaData):
            Creates a UserDataBase for a given organization (taken from the RepositoryMetaData).
        __getitem__(key):
            Returns username of a given user id.
        __setitem__(key, value):
            Raises AttributeError, manual data appending is not allowed.
    """

    def __init__(self, rmd: RepositoryMetaData):
        """
        Creates a UserDataBase for a given organization (taken from the RepositoryMetaData).

        Args:
            rmd (RepositoryMetaData):
                Provides organization name and request headers.
        """
        self.users = dict()
        self.organization = rmd.organization
        self.headers = rmd.headers

    def __getitem__(self, key: str) -> str:
        """
        Returns username for a given user id.
        In case of error from the request, the uid is registered as the username and a warning is printed on the CLI.

        Args:
            key (str):
                Azure Devops user id.

        Returns:
            str:
                Azure Devops user name.
        """
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
                print(f"Warning, did not succeed to retrieve user {key}", file = sys.stderr)

        return self.users[key]

    def __setitem__(self, key, value):
        """
        Raises AttributeError, manual data appending is not allowed.

        Args:
            key:
                Ignored.
            value:
                Ignored.

        Raises:
            AttributeError:
                Manual data appending is not allowed.
        """
        raise AttributeError("UserDataBase: Manual data appending is not allowed")



class FileDataBase:
    """
    A cache/request interface to fetch file contents from the server for a given repository and commit id.
    Behaves like a Dict[path, content].

    Attributes:
        files (Dict[str, List[str]]):
            Dictionary mapping file path to file content.
        rmd (RepositoryMetaData):
            Associated repository metadata object.
        commit (str):
            Commit id.

    Methods:
        __init__(rmd: RepositoryMetaData, commit: str):
            Creates a FileDataBase tracking files of a given repository and commit id.
        __getitem__(path: str):
            Returns the content of a given file as a list of lines.
        __setitem__(key, value):
            Raises AttributeError, manual data appending is not allowed.
    """

    def __init__(self, rmd: RepositoryMetaData, commit: str):
        """
        Creates a FileDataBase tracking files of a given repository and commit id.

        Args:
            rmd (RepositoryMetaData):
                Repository information.
            commit (str):
                Commit id.
        """
        self.files = dict()
        self.rmd = rmd
        self.commit = commit

    def __getitem__(self, path: str) -> List[str]:
        """
        Returns the content of a given file as a list of lines.
        In case of error from the request, the file is registered as empty and a warning is printed on the CLI.

        Args:
            path (str):
                Path of the requested file.
        """
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
                print(f"Warning, did not succeed to retrieve file {path} from commit {self.commit}", file = sys.stderr)

        return self.files[path]

    def __setitem__(self, key, value):
        """
        Raises AttributeError, manual data appending is not allowed.

        Args:
            key:
                Ignored.
            value:
                Ignored.

        Raises:
            AttributeError:
                Manual data appending is not allowed.
        """
        raise AttributeError("FileDataBase: Manual data appending is not allowed")



class VersionDataBase:
    """
    A cache interface to store FileDataBase objects for different versions of a given repository.
    Behaves like a Dict[commit_id, FileDataBase].

    Attributes:
        versions (Dict[str, FileDataBase]):
            Dictionary mapping commit id to FileDataBase object.
        rmd (RepositoryMetaData):
            Associated repository metadata object.

    Methods:
        __init__(rmd: RepositoryMetaData):
            Creates a VersionDataBase tracking versions of a given repository.
        __getitem__(commit: str):
            Returns the FileDataBase for a given commit.
        __setitem__(key, value):
            Raises AttributeError, manual data appending is not allowed.
    """

    def __init__(self, rmd: RepositoryMetaData):
        """
        Creates a VersionDataBase tracking versions of a given repository.

        Args:
            rmd (RepositoryMetaData):
                Repository information.
        """
        self.versions = dict()
        self.rmd = rmd

    def __getitem__(self, commit: str) -> FileDataBase:
        """
        Returns the FileDataBase for a given commit.

        Args:
            commit (str):
                Commit id.

        Returns:
            FileDataBase:
                FileDataBase for the given commit.
        """
        if commit not in self.versions.keys():
            self.versions[commit] = FileDataBase(self.rmd, commit)

        return self.versions[commit]

    def __setitem__(self, key, value):
        """
        Raises AttributeError, manual data appending is not allowed.

        Args:
            key:
                Ignored.
            value:
                Ignored.

        Raises:
            AttributeError:
                Manual data appending is not allowed.
        """
        raise AttributeError("VersionDataBase: Manual data appending is not allowed")



# For typing information
class FilePosition(TypedDict):
    """
    Class to represent a position in a file.
    TypedDict of the part of an Azure Devops API response.

    Attributes:
        line (int):
            Line number in the file.
        offset (int):
            Offset in the line.
    """
    line:   int
    offset: int

# For typing information
class FileContext(TypedDict):
    """
    Class to represent a file context on the whole file.
    TypedDict of the part of an Azure Devops API response.

    Attributes:
        filePath (str):
            Path of the file.
    """
    filePath:       str

# For typing information
class DetailedFileContext(FileContext):
    """
    Class to represent a file context on a file part.
    TypedDict of the part of an Azure Devops API response.
    Inherits from FileContext

    Attributes:
        filePath (str):
            Path of the file.
        rightFileStart (FilePosition):
            Start position of the file part.
        rightFileEnd (FilePosition):
            End position of the file part.
    """
    filePath:       str
    rightFileStart: FilePosition
    rightFileEnd:   FilePosition



class ThreadContextQuote:
    """
    Delimits the part of the file quoted by the comment.

    Attributes:
        startLine (int):
            Start line index of the quoted part.
        startOff (int):
            Start offset of the quoted part in the line.
        endLine (int):
            End line index of the quoted part.
        endOff (int):
            End offset of the quoted part in the line.
        file (List[str]):
            File content, as a list of lines.

    Methods:
        __init__(fc: DetailedFileContext, file: List[str]):
            Creates a ThreadContextQuote object from the given file context and file content.
        getContext() -> List[str]:
            Get the quoted part as a list of lines.
        getLinesBeforeContext(count: int = 2) -> List[str]:
            Get count lines above the quoted part as a list of lines.
        getCharsBeforeContext() -> str:
            Get the characters preceding the quoted part on its first line.
        getLinesAfterContext(count: int = 2) -> List[str]:
            Get count lines under the quoted part as a list of lines.
        getCharsAfterContext() -> str:
            Get the characters following the quoted part on its last line.
        debug():
            Print the context quote and surrounding lines for debugging purposes.
    """

    def __init__(self, fc: DetailedFileContext, file: List[str]):
        """
        Creates a ThreadContextQuote object from the given file context and file content.

        Args:
            fc (DetailedFileContext):
                File context object.
            file (List[str]):
                File content, as a list of lines
        """
        rightFileStart = fc["rightFileStart"]
        rightFileEnd = fc["rightFileEnd"]

        self.startLine = int(rightFileStart["line"]) - 1
        self.startOff = int(rightFileStart["offset"]) - 1
        self.endLine = int(rightFileEnd["line"]) - 1
        self.endOff = int(rightFileEnd["offset"]) - 1

        self.file = file

    def getContext(self) -> List[str]:
        """
        Get the quoted part as a list of lines.

        Returns:
            List[str]:
                Quoted part of the file as a list of lines.
        """
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
        """
        Get count lines above the quoted part as a list of lines.

        Args:
            count (int):
                Desired number of lines.

        Returns:
            List[str]:
                Lines above the quoted part as a list of lines.
        """
        ret = list()
        for i in range(max(self.startLine - count, 0), self.startLine):
            ret.append(self.file[i])

        return ret

    def getCharsBeforeContext(self) -> str:
        """
        Get the characters preceding the quoted part on its first line.

        Returns:
            str:
                Characters preceding the quoted part on its first line.
        """
        return self.file[self.startLine][0:self.startOff]

    def getLinesAfterContext(self, count: int = 2) -> List[str]:
        """
        Get count lines under the quoted part as a list of lines.

        Args:
            count (int):
                Desired number of lines.

        Returns:
            List[str]:
                Lines under the quoted part as a list of lines.
        """
        ret = list()
        for i in range(self.endLine + 1, min(self.endLine + count + 1, len(self.file))):
            ret.append(self.file[i])

        return ret

    def getCharsAfterContext(self) -> str:
        """
        Get the characters following the quoted part on its last line.

        Returns:
            str:
                Characters following the quoted part on its last line.
        """
        return self.file[self.endLine][self.endOff:]

    def debug(self):
        """
        Prints the context quote and surrounding lines for debugging purposes.
        """
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
    """
    The file or file part concerned by the comment.

    Attributes:
        filePath (str):
            The path of the commented file.
        commit (str):
            The version commit of the commented file.
        file (List[str]):
            File content, as a list of lines.
        quote (Optional[ThreadContextQuote]):
            File part quoted by the comment.

    Methods:
        __init__(fc: FileContext, vdb: VersionDataBase, commit: str):
            Creates a ThreadContext object from a file context and a commit id.
        debug():
            Prints the thread context for debugging purposes.
    """

    def __init__(self, fc: FileContext, vdb: VersionDataBase, commit: str):
        """
        Creates a ThreadContext object from a file context and a commit id.

        Args:
            fc (FileContext):
                The file context.
            vdb (VersionDataBase):
                A VersionDataBase object to retrieve the file content.
            commit (str):
                The commit id.
        """
        self.filePath = fc["filePath"]
        self.commit = commit
        self.file = vdb[commit][self.filePath]

        try:
            self.quote = ThreadContextQuote(fc, self.file)
        except KeyError:
            self.quote = None

    def debug(self):
        """
        Prints the thread context for debugging purposes.
        """
        print(f"On commit {self.commit}:")
        print(f"On file {self.filePath}:")
        if self.quote:
            self.quote.debug()



class Comment:
    """
    Text of a comment and various metadata.

    Attributes:
        author (str):
            The author of the comment.
        pubDate (str):
            The date the comment was first published.
        lstUpdDate (str):
            The date the comment was last updated.
        content (str):
            The comment content.

    Methods:
        __init__(author, pubDate, lstUpdDate, content):
            Creates a Comment object from the given parameters.
        debug():
            Prints the comment information for debugging purposes.
    """

    def __init__(self, author: str, pubDate: str, lstUpdDate: str, content: str):
        """
        Creates a Comment object from the given parameters.

        Args:
            author (str):
                The author of the comment.
            pubDate (str):
                The date the comment was first published.
            lstUpdDate (str):
                The date the comment was last updated.
            content (str):
                The comment content.
        """
        self.author = author
        self.pubDate = pubDate
        self.lstUpdDate = lstUpdDate
        self.content = content

    def debug(self):
        """
        Prints the comment information for debugging purposes.
        """
        print(f"{self.author} ({self.pubDate}/{self.lstUpdDate}):")
        print(self.content)



class CommentThread:
    """
    Contains a comment along with its associated commit, context and replies.

    Attributes:
        commit (str):
            Commit id on which the first comment was made.
        context (Optional[ThreadContext]):
            Context of the comment (file/quote).
        comments (List[Comments]):
            Comment and replies.
        vdb (VersionDataBase):
            The VersionDataBase object used to retrieve the file content.
        udb (UserDataBase):
            The UserDataBase object used to retrieve user names.

    Methods:
        __init__(thread: Dict, commit: str, vdb: VersionDataBase, udb: UserDataBase):
            Creates a CommentThread object from a thread of Azure Devops API response.
        debug():
            Prints comment thread information and contained comments for debugging purposes.
    """

    def __init__(self, thread: Dict, commit: str, vdb: VersionDataBase, udb: UserDataBase):
        """
        Creates a CommentThread object from a thread of Azure Devops API response.
        Filters out deleted comments and non-text comments.
        Also replaces user mentions with their display names.

        Args:
            thread (Dict):
                The thread object from the Azure Devops API response.
            commit (str):
                The commit id.
            vdb (VersionDataBase):
                A VersionDataBase object to retrieve the file content.
            udb (UserDataBase):
                A UserDataBase object to retrieve user names.

        Raises:
            ValueError:
                If the thread does not contain any comments.
        """
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
                    """
                    Replaces user mentions in the text with their display names using the provided UserDataBase.
                    User mentions are in the format "@<userId>".

                    Args:
                        text (str):
                            The text containing user mentions.
                        udb (UserDataBase):
                            The UserDataBase object to retrieve user names.

                    Returns:
                        str:
                            The text with user mentions replaced by display names.
                    """
                    p = re.compile(r"(.*)@<([-a-zA-Z0-9]*)>(.*)")
                    didMatch = True
                    while didMatch:
                        didMatch = False
                        m = p.search(text)
                        if m:
                            text = f"{m.group(1)}@{udb[m.group(2)]}{m.group(3)}"
                            didMatch = True
                    return text

                self.comments.append(Comment(comment["author"]["displayName"], comment["publishedDate"], comment["lastContentUpdatedDate"], replace_user_mentions(comment["content"], udb)))

    def debug(self):
        """
        Prints comment thread information and containted comments for debugging purposes.
        """
        if self.context:
            self.context.debug()
        for comment in self.comments:
            comment.debug()
            print()



class PullRequest:
    """
    A request interface to fetch and treat all threads and comments of a pull request.

    Attributes:
        prmd (PullRequestMetaData):
            Pull request information.
        vdb (VersionDataBase):
            Version database.
        udb (UserDataBase):
            User database.

    Methods:
        __init__(prmd: PullRequestMetaData, vdb: Optional[VersionDataBase], udb: Optional[UserDataBase]):
            Creates a PullRequest object.
        get() -> List[CommentThread]:
            Fetches pull request threads from server, analyses them to track version commits and returns a list of threads containing comments.
        debug():
            Prints pull request information and contained threads for debugging purposes.
    """

    def __init__(self, prmd: PullRequestMetaData, vdb: Optional[VersionDataBase] = None, udb: Optional[UserDataBase] = None):
        """
        Creates a PullRequest object.

        Args:
            prmd (PullRequestMetaData):
                Pull request information.
            vdb (Optional[VersionDataBase]):
                Version database, a new one is created if None.
            udb (Optional[UserDataBase]):
                User database, a new one is created if None.
        """
        self.prmd = prmd
        self.vdb = vdb if vdb else VersionDataBase(self.prmd)
        self.udb = udb if udb else UserDataBase(self.prmd)

    def get(self) -> List[CommentThread]:

        """
        Fetches pull request threads from server, analyses them to track version commits and returns a list of threads containing comments.

        Returns:
            List[CommentThread]:
                List of CommentThread objects containing comments and their context.

        Raises:
            IOError:
                If the server response is invalid.
            HTTPError:
                If one occurs.
        """

        return thread_list

    def debug(self):
        """
        Prints pull request information and contained threads for debugging purposes.
        """
        print(f"Pull Request {self.prmd.pullRequestId}")
        for thread in self.get():
            thread.debug()
            print("=" * 80)



class Repository:
    """
    A request interface to fetch the pull requests associated with a repository.

    Attributes:
        rmd (RepositoryMetaData):
            Repository information.
        vdb (VersionDataBase):
            Version database.
        udb (UserDataBase):
            User database.

    Methods:
        __init__(rmd: RepositoryMetaData, vdb: Optional[VersionDataBase], udb: Optional[UserDataBase]):
            Creates a Repository object.
        get() -> List[PullRequest]:
            Fetches pull requests from server, constructs PullRequest objects and return them in a list.
        debug():
            Prints repository information and contained pull requests for debugging purposes.
    """

    def __init__(self, rmd: RepositoryMetaData, vdb: Optional[VersionDataBase] = None, udb: Optional[UserDataBase] = None):
        """
        Creates a Repository object.

        Args:
            rmd (RepositoryMetaData):
                Repository information.
            vdb (Optional[VersionDataBase]):
                Version database, a new one is created if None.
            udb (Optional[UserDataBase]):
                User database, a new one is created if None.
        """
        self.rmd = rmd
        self.vdb = vdb if vdb else VersionDataBase(self.rmd)
        self.udb = udb if udb else UserDataBase(self.rmd)

    def get(self) -> List[PullRequest]:
        """
        Fetches pull requests from server, constructs PullRequest objects and return them in a list.

        Returns:
            List[PullRequest]:
                List of PullRequest objects.

        Raises:
            IOError:
                If the server response is invalid.
            HTTPError:
                If one occurs.
        """
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
        """
        Prints repository information and contained pull requests for debugging purposes.
        """
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


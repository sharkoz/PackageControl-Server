from model.PackageSource.PackageSourceBase import PackageSourceBase
from config import LOGGER
import requests
import json
import dateutil.parser
import traceback


class Github(PackageSourceBase):
    description = "An entire repository on github.com dedicated to the package"

    def __init__(self, package):
        super().__init__(package)
        self.package.name = self.package.repo
        self.package.homepage = "https://github.com/{}/{}".format(self.package.owner, self.package.repo)

    def update(self):
        try:
            api_url = "https://api.github.com/repos/{}/{}".format(self.package.owner, self.package.repo)
            repo_info = json.loads(self.do_get_request(api_url))
            self.package.description = repo_info['description']

            request_url = "{}/releases".format(api_url)
            releases = json.loads(self.do_get_request(request_url))
            release_found = False
            for release in releases:
                release_date = dateutil.parser.parse(release['published_at'], ignoretz=True)
                if release['prerelease'] or self.package.date is not None and self.package.date > release_date:
                    continue
                self.package.date = release_date
                self.package.version = release['tag_name']
                for asset in release['assets']:
                    if asset['name'].endswith('.keypirinha-package'):
                        self.package.download_url = asset['browser_download_url']
                        self.package.filename = asset['name']
                        break
                release_found = True

            if not release_found:
                LOGGER.error("No release found in repo: %s: %s", self.package.owner, self.package.repo)
                return False
        except Exception as ex:
            LOGGER.error(ex, traceback.format_exc())
            return False

        return True

    def is_available(self):
        url = "https://github.com/{}/{}".format(self.package.owner, self.package.repo)
        req = requests.head(url)
        if req.status_code == 200:
            return True
        else:
            return False

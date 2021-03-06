from __future__ import absolute_import
import os
import logging
import lintreview.docker as docker
from lintreview.review import IssueComment
from lintreview.tools import Tool, process_quickfix, stringify

log = logging.getLogger(__name__)


class Mypy(Tool):

    name = 'mypy'

    def check_dependencies(self):
        """See if the python3 image exists
        """
        return docker.image_exists('python3')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.py'

    def process_files(self, files):
        """
        Run code checks with mypy.
        Only a single process is made for all files
        to save resources.
        """
        log.debug('Processing %s files with %s', files, self.name)

        command = ['mypy', '--no-error-summary', '--show-absolute-path']
        if 'config' in self.options:
            command += ['--config-file', stringify(self.options.get('config'))]
        command += files

        output = docker.run('python3', command, source_dir=self.base_path)
        if not output:
            log.debug('No mypy errors found.')
            return False
        output = output.strip().split("\n")
        if len(output) and output[-1].startswith('mypy: error:'):
            msg = (u'Your `mypy` configuration file caused `mypy` to fail with:'
                   '\n'
                   '```\n'
                   '{}\n'
                   '```\n'
                   'Please correct the error in your configuration file.')
            self.problems.add(IssueComment(msg.format(output[-1])))
            return

        process_quickfix(self.problems, output, docker.strip_base)

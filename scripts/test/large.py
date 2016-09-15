#http://www.apache.org/licenses/LICENSE-2.0.txt
#
#
#Copyright 2016 Intel Corporation
#
#Licensed under the Apache License, Version 2.0 (the "License");
#you may not use this file except in compliance with the License.
#You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#Unless required by applicable law or agreed to in writing, software
#distributed under the License is distributed on an "AS IS" BASIS,
#WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#See the License for the specific language governing permissions and
#limitations under the License.

import sys
import os
import unittest

from pytest import bins
from pytest import utils
from pytest.logger import log
from unittest import TextTestRunner


class PsutilCollectorLargeTest(unittest.TestCase):

    def setUp(self):
        plugins_dir = "/etc/snap/plugins"
        snap_dir = "/usr/local/bin"

        snapd_url = "http://snap.ci.snap-telemetry.io/snap/master/latest/snapd"
        snapctl_url = "http://snap.ci.snap-telemetry.io/snap/master/latest/snapctl"
        psutil_url = "http://snap.ci.snap-telemetry.io/plugins/snap-plugin-collector-psutil/latest/linux/x86_64/snap-plugin-collector-psutil"
        passthru_url = "http://snap.ci.snap-telemetry.io/snap/master/latest/snap-plugin-processor-passthru"
        mockfile_url = "http://snap.ci.snap-telemetry.io/snap/master/latest/snap-plugin-publisher-mock-file"

        # set and download required binaries (snapd, snapctl, plugins)
        self.binaries = bins.Binaries()
        self.binaries.snapd = bins.Snapd(snapd_url, snap_dir)
        self.binaries.snapctl = bins.Snapctl(snapctl_url, snap_dir)
        self.binaries.collector = bins.Plugin(psutil_url, plugins_dir, "collector", 6)
        self.binaries.processor = bins.Plugin(passthru_url, plugins_dir, "processor", -1)
        self.binaries.publisher = bins.Plugin(mockfile_url, plugins_dir, "publisher", -1)

        utils.download_binaries(self.binaries)

        self.task_file = "/snap-plugin-collector-psutil/examples/tasks/task-psutil.json"

        log.info("starting snapd")
        self.binaries.snapd.start()
        if not self.binaries.snapd.isAlive():
            self.fail("snapd thread died")

        log.debug("Waiting for snapd to finish starting")
        if not self.binaries.snapd.wait():
            log.error("snapd errors: {}".format(self.binaries.snapd.errors))
            self.binaries.snapd.kill()
            self.fail("snapd not ready, timeout!")

    def test_psutil_collector_plugin(self):
        # load plugins
        for plugin in self.binaries.get_all_plugins():
            log.info("snapctl plugin load {}".format(os.path.join(plugin.dir, plugin.name)))
            loaded = self.binaries.snapctl.load_plugin(plugin)
            self.assertTrue(loaded, "{} loaded".format(plugin.name))

        # check available metrics, plugins and tasks
        metrics = self.binaries.snapctl.list_metrics()
        plugins = self.binaries.snapctl.list_plugins()
        tasks = self.binaries.snapctl.list_tasks()
        self.assertGreater(len(metrics), 0, "Metrics available {} expected {}".format(len(metrics), 0))
        self.assertEqual(len(plugins), 3, "Plugins available {} expected {}".format(len(plugins), 3))
        self.assertEqual(len(tasks), 0, "Tasks available {} expected {}".format(len(tasks), 0))

        # check config policy for metric
        rules = self.binaries.snapctl.metric_get("/intel/psutil/vm/free")
        self.assertEqual(len(rules), 0, "Rules available {} expected {}".format(len(rules), 0))

        # create and list available task
        log.info("snapctl task create -t {}".format(self.task_file))
        task_id = self.binaries.snapctl.create_task(self.task_file)
        tasks = self.binaries.snapctl.list_tasks()
        self.assertEqual(len(tasks), 1, "Tasks available {} expected {}".format(len(tasks), 1))

        # check if task hits and fails
        hits = self.binaries.snapctl.task_hits_count(task_id)
        fails = self.binaries.snapctl.task_fails_count(task_id)
        self.assertGreater(hits, 0, "Task hits {} expected {}".format(hits, ">0"))
        self.assertEqual(fails, 0, "Task fails {} expected {}".format(fails, 0))

        # stop task and list available tasks
        log.info("snapctl task stop {}".format(task_id))
        stopped = self.binaries.snapctl.stop_task(task_id)
        self.assertTrue(stopped, "Task stopped")
        tasks = self.binaries.snapctl.list_tasks()
        self.assertEqual(len(tasks), 1, "Tasks available {} expected {}".format(len(tasks), 1))

        # unload plugin, list metrics and plugins
        log.info("snapctl plugin unload {}".format(self.binaries.collector))
        self.binaries.snapctl.unload_plugin(self.binaries.collector)
        metrics = self.binaries.snapctl.list_metrics()
        plugins = self.binaries.snapctl.list_plugins()
        self.assertEqual(len(metrics), 0, "Metrics available {} expected {}".format(len(metrics), 0))
        self.assertEqual(len(plugins), 2, "Plugins available {} expected {}".format(len(plugins), 2))

        # check for snapd errors
        self.assertEqual(len(self.binaries.snapd.errors), 0, "Errors found during snapd execution")

    def tearDown(self):
        log.info("stopping snapd")
        self.binaries.snapd.stop()
        if self.binaries.snapd.isAlive():
            log.warn("snapd thread did not died")

if __name__ == "__main__":
    test_suite = unittest.TestLoader().loadTestsFromTestCase(PsutilCollectorLargeTest)
    test_result = TextTestRunner().run(test_suite)
    # exit with return code equal to number of failures
    sys.exit(len(test_result.failures))


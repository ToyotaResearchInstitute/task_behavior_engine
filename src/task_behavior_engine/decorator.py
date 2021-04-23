# Copyright 2016 Toyota Research Institute

# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at

#   http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from __future__ import absolute_import
import logging

from .tree import Decorator
from .tree import NodeStatus

logger = logging.getLogger(__name__)


class Negate(Decorator):

    """ A Negate decorator reverses the status of the child node.
        If the child returns SUCCESS, this will return FAIL.
        If the child returns FAIL, this will return SUCCESS.
        All other statuses are passed through.
    """

    def __init__(self, name, *args, **kwargs):
        super(Negate, self).__init__(name=name,
                                     run_cb=self.run,
                                     *args, **kwargs)

    def run(self, nodedata):
        logger.debug("Negate.run() " + self._child._name)
        result = self.tick_child()
        if result == NodeStatus.SUCCESS:
            return NodeStatus(NodeStatus.FAIL, "Negating " + self._child._name)
        elif result == NodeStatus.FAIL:
            return NodeStatus(NodeStatus.SUCCESS, "Negating " + self._child._name)

        return result


class Repeat(Decorator):

    """ A Repeat decorator returns ACTIVE when result is either SUCCESS or FAIL.
        All other statuses are passed through.
    """

    def __init__(self, name, *args, **kwargs):
        super(Repeat, self).__init__(name=name,
                                     run_cb=self.run,
                                     *args, **kwargs)

    def run(self, nodedata):
        logger.debug("Repeat.run() " + self._child._name)
        result = self.tick_child()
        if result == NodeStatus.SUCCESS or result == NodeStatus.FAIL:
            return NodeStatus(NodeStatus.ACTIVE, "Repeating.. " + self._child._name)
        return result


class While(Decorator):

    """ A While decorator returns ACTIVE while the child returns SUCCESS.
        All other statuses are passed through.
    """

    def __init__(self, name, *args, **kwargs):
        super(While, self).__init__(name=name,
                                    run_cb=self.run,
                                    *args, **kwargs)

    def run(self, nodedata):
        logger.debug("While.run() " + self._child._name)
        result = self.tick_child()
        if result == NodeStatus.SUCCESS:
            return NodeStatus(NodeStatus.ACTIVE, "Continuing.. " + self._child._name)
        return result


class Until(Decorator):

    """ An Until decorator returns ACTIVE while the child returns FAIL.
        All other statuses are passed through.
    """

    def __init__(self, name, *args, **kwargs):
        super(Until, self).__init__(name=name,
                                    run_cb=self.run,
                                    *args, **kwargs)

    def run(self, nodedata):
        logger.debug("Until.run() " + self._child._name)
        result = self.tick_child()
        if result == NodeStatus.FAIL:
            return NodeStatus(NodeStatus.ACTIVE, "Trying again.. " + self._child._name)
        return result


class UntilCount(Decorator):
    """ An UntilCount returns ACTIVE while the child returns FAIL up to count.
        All other statuses are passed through.
    """

    def __init__(self, name, max_count, *args, **kwargs):
        super(UntilCount, self).__init__(
            name=name, configure_cb=self.config, run_cb=self.run, *args, **kwargs)

        self._max_count = max_count

    def config(self, nodedata):
        nodedata.count = 0
        nodedata.max_count = self._max_count

    def run(self, nodedata):
        logger.debug("UntilCount.run() " + self._child._name)
        result = self.tick_child()
        if result == NodeStatus.FAIL:
            nodedata.count += 1
            if nodedata.count < nodedata.max_count:
                return NodeStatus(NodeStatus.ACTIVE, "Trying again %s until %s..".format(nodedata.count, nodedata.max_count))
        return result


class Fail(Decorator):

    """ A Fail decorator returns FAIL if the child returns SUCCESS.
        All other statuses are passed through.

        A Fail will always return NodeStatus.FAIL on child completion,
        regardless of child SUCCESS/FAIL status.
    """

    def __init__(self, name, *args, **kwargs):
        super(Fail, self).__init__(name=name, run_cb=self.run, *args, **kwargs)

    def run(self, nodedata):
        logger.debug("Fail.run() " + self._child._name)
        result = self.tick_child()
        if result == NodeStatus.SUCCESS:
            return NodeStatus(NodeStatus.FAIL, "Failing " + self._child._name)
        return result


class Succeed(Decorator):

    """ A Succeed decorator returns SUCCESS if the child returns FAIL.
        All other statuses are passed through.

        A Success will always return NodeStatus.SUCCESS on child completion,
        regardless of child SUCCESS/FAIL status.
    """

    def __init__(self, name, *args, **kwargs):
        super(Succeed, self).__init__(name=name,
                                      run_cb=self.run,
                                      *args, **kwargs)

    def run(self, nodedata):
        logger.debug("Succeed.run() " + self._child._name)
        result = self.tick_child()
        if result == NodeStatus.FAIL:
            return NodeStatus(NodeStatus.SUCCESS, "Succeeding " + self._child._name)
        return result

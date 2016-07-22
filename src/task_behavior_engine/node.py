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


from task_behavior_engine.tree import Node
from task_behavior_engine.tree import NodeStatus


class Success(Node):

    """ A Success node always returns NodeStatus.SUCCESS. """

    def __init__(self, name, *args, **kwargs):
        super(Success, self).__init__(name, run_cb=self.run, *args, **kwargs)

    def run(self, nodedata):
        return NodeStatus(NodeStatus.SUCCESS)


class Fail(Node):

    """ A Fail node always returns NodeStatus.FAIL. """

    def __init__(self, name, *args, **kwargs):
        super(Fail, self).__init__(name, run_cb=self.run, *args, **kwargs)

    def run(self, nodedata):
        return NodeStatus(NodeStatus.FAIL)


class Continue(Node):

    """ A Continue node always returns NodeStatus.ACTIVE. """

    def __init__(self, name, *args, **kwargs):
        super(Continue, self).__init__(name, run_cb=self.run, *args, **kwargs)

    def run(self, nodedata):
        return NodeStatus(NodeStatus.ACTIVE)

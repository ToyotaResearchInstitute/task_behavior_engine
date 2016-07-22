#!/usr/bin/env python

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

import time

from task_behavior_engine.branch import Sequencer
from task_behavior_engine.decorator import Repeat
from task_behavior_engine.tree import Blackboard
from task_behavior_engine.tree import Node
from task_behavior_engine.tree import NodeStatus


class Count(Node):

    ''' The Count node starts at some number and counts up to a limit.
        It will return NodeStatus.ACTIVE until the count has reached the limit,
        then it will return NodeStatus.SUCCESS.

        As a node, this inherits from the base Node class.
    '''

    def __init__(self, name, *args, **kwargs):
        ''' User-facing initialization
            @param name [str] The human-readable name to aid in debugging
        '''
        super(Count, self).__init__(
            name,
            run_cb=self.run,
            configure_cb=self.configure,
            cleanup_cb=self.cleanup,
            *args, **kwargs)

    def configure(self, nodedata):
        ''' Initialize the start and limit values
            @param nodedata [NodeData] The shareable data associated with this node

            NodeData:
                start [int] The number the count should start on
                limit [int] The number the count sound end on
        '''
        self.start = nodedata.get_data('start', 0)
        self.limit = nodedata.get_data('limit', 5)
        nodedata.index = self.start

    def run(self, nodedata):
        ''' Update the count and return current status.
            @param nodedata [NodeData] The shareable data associated with this node

            NodeData:
                index [int] The current index of the count
        '''
        if nodedata.index < self.limit:
            nodedata.index += 1
            return NodeStatus(NodeStatus.ACTIVE, "Count " + str(nodedata.index))
        return NodeStatus(NodeStatus.SUCCESS, "Count finished at " + str(nodedata.index))

    def cleanup(self, nodedata):
        ''' Reset the count to start
            @param nodedata [NodeData]

            NodeData:
                index [int] The current index of the count
        '''
        nodedata.index = self.start

if __name__ == '__main__':

    print "Running example 1 -- using a node"

    count = Count(name="count_index")
    result = NodeStatus(NodeStatus.ACTIVE)

    while result == NodeStatus.ACTIVE:
        result = count.tick()
        print result
        time.sleep(0.1)

    print "Running example 2 (10 times) -- using a decorator"

    count = Count(name="count_index")
    repeat = Repeat(name="repeat_count", child=count)
    result = NodeStatus(NodeStatus.ACTIVE)

    for i in range(0, 10):
        result = repeat.tick()
        print result
        time.sleep(0.1)

    print "Running example 3 -- using a behavior"

    b = Blackboard()

    count1 = Count(name="count_1", blackboard=b)
    count2 = Count(name="count_2", blackboard=b)
    count3 = Count(name="count_3", blackboard=b)

    finish_counts = Sequencer("finish_counts", blackboard=b)
    finish_counts.add_child(count1)
    finish_counts.add_child(count2)
    finish_counts.add_child(count3)

    # change the limit for the count
    b.save("limit", 1, count1._id)
    b.save("limit", 2, count2._id)
    b.save("limit", 3, count3._id)

    result = NodeStatus(NodeStatus.ACTIVE)

    while result == NodeStatus.ACTIVE:
        result = finish_counts.tick()
        print result
        time.sleep(0.1)

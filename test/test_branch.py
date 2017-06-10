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

from nose.tools import assert_equal

from task_behavior_engine.branch import All
from task_behavior_engine.branch import Any
from task_behavior_engine.branch import First
from task_behavior_engine.branch import Majority
from task_behavior_engine.branch import Progressor
from task_behavior_engine.branch import Random
from task_behavior_engine.branch import Runner
from task_behavior_engine.branch import Selector
from task_behavior_engine.branch import Sequencer

from task_behavior_engine.node import Continue
from task_behavior_engine.node import Fail
from task_behavior_engine.node import Success

from task_behavior_engine.tree import Blackboard
from task_behavior_engine.tree import NodeStatus


class TestSelector(object):

    def setUp(self):
        self.blackboard = Blackboard()
        self.FAIL1 = Fail(name="FAIL1", blackboard=self.blackboard)
        self.FAIL2 = Fail(name="FAIL2", blackboard=self.blackboard)
        self.SUCCESS1 = Success(name="SUCCESS1", blackboard=self.blackboard)
        self.SUCCESS2 = Success(name="SUCCESS2", blackboard=self.blackboard)
        self.CONTINUE = Continue(name="CONTINUE", blackboard=self.blackboard)

        self.SELECT = Selector(name="SELECT")
        self.SELECT.set_blackboard(self.blackboard)
        self.nd = self.blackboard.get_memory(self.SELECT._id)

    def test_fail(self):
        self.SELECT.add_child(self.FAIL1)
        self.SELECT.add_child(self.FAIL2)

        result = self.SELECT.tick()
        assert_equal(result, NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.FAIL1._id),
                     NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.FAIL2._id),
                     NodeStatus.FAIL)

    def test_success(self):
        self.SELECT.add_child(self.FAIL1)
        self.SELECT.add_child(self.FAIL2)
        self.SELECT.add_child(self.SUCCESS1)
        self.SELECT.add_child(self.SUCCESS2)

        result = self.SELECT.tick()
        assert_equal(result, NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.FAIL1._id),
                     NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.FAIL2._id),
                     NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS1._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS2._id),
                     NodeStatus.PENDING)

    def test_active(self):
        self.SELECT.add_child(self.CONTINUE)
        self.SELECT.add_child(self.FAIL1)
        self.SELECT.add_child(self.FAIL2)
        self.SELECT.add_child(self.SUCCESS1)
        self.SELECT.add_child(self.SUCCESS2)

        result = self.SELECT.tick()
        assert_equal(result, NodeStatus.ACTIVE)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE._id),
                     NodeStatus.ACTIVE)
        assert_equal(self.blackboard.get_node_status(self.FAIL1._id),
                     NodeStatus.PENDING)
        assert_equal(self.blackboard.get_node_status(self.FAIL2._id),
                     NodeStatus.PENDING)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS1._id),
                     NodeStatus.PENDING)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS2._id),
                     NodeStatus.PENDING)

    def test_cancel(self):
        self.SELECT.add_child(self.CONTINUE)
        self.SELECT.add_child(self.FAIL1)
        self.SELECT.add_child(self.FAIL2)
        self.SELECT.add_child(self.SUCCESS1)
        self.SELECT.add_child(self.SUCCESS2)

        self.SELECT.tick()
        self.SELECT._cancel()
        result = self.SELECT.tick()
        assert_equal(result, NodeStatus.CANCEL)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE._id),
                     NodeStatus.CANCEL)
        assert_equal(self.blackboard.get_node_status(self.FAIL1._id),
                     NodeStatus.PENDING)
        assert_equal(self.blackboard.get_node_status(self.FAIL2._id),
                     NodeStatus.PENDING)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS1._id),
                     NodeStatus.PENDING)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS2._id),
                     NodeStatus.PENDING)

    def test_force_child(self):
        self.SELECT.add_child(self.CONTINUE)
        self.SELECT.add_child(self.FAIL1)
        self.SELECT.add_child(self.FAIL2)
        self.SELECT.add_child(self.SUCCESS1)
        self.SELECT.add_child(self.SUCCESS2)

        self.SELECT.tick()
        self.CONTINUE.force(NodeStatus.FAIL)
        result = self.SELECT.tick()
        assert_equal(result, NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE._id),
                     NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.FAIL1._id),
                     NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.FAIL2._id),
                     NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS1._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS2._id),
                     NodeStatus.PENDING)
        self.blackboard.clear_node_status()

    def test_force_behavior(self):
        self.SELECT.add_child(self.CONTINUE)
        self.SELECT.add_child(self.FAIL1)
        self.SELECT.add_child(self.FAIL2)
        self.SELECT.add_child(self.SUCCESS1)
        self.SELECT.add_child(self.SUCCESS2)

        self.SELECT.tick()
        self.SELECT.force(NodeStatus.FAIL)
        result = self.SELECT.tick()
        assert_equal(result, NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE._id),
                     NodeStatus.CANCEL)
        assert_equal(self.blackboard.get_node_status(self.FAIL1._id),
                     NodeStatus.PENDING)
        assert_equal(self.blackboard.get_node_status(self.FAIL2._id),
                     NodeStatus.PENDING)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS1._id),
                     NodeStatus.PENDING)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS2._id),
                     NodeStatus.PENDING)
        self.blackboard.clear_node_status()


class TestSequencer(object):

    def setUp(self):
        self.blackboard = Blackboard()
        self.FAIL1 = Fail(name="FAIL1", blackboard=self.blackboard)
        self.FAIL2 = Fail(name="FAIL2", blackboard=self.blackboard)
        self.SUCCESS1 = Success(name="SUCCESS1", blackboard=self.blackboard)
        self.SUCCESS2 = Success(name="SUCCESS2", blackboard=self.blackboard)
        self.CONTINUE = Continue(name="CONTINUE", blackboard=self.blackboard)

        self.SEQUENCE = Sequencer("SEQUENCE")
        self.SEQUENCE.set_blackboard(self.blackboard)
        self.nd = self.blackboard.get_memory(self.SEQUENCE._id)

    def test_success(self):
        self.SEQUENCE.add_child(self.SUCCESS1)
        self.SEQUENCE.add_child(self.SUCCESS2)

        result = self.SEQUENCE.tick()
        assert_equal(result, NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS1._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS2._id),
                     NodeStatus.SUCCESS)

    def test_fail(self):
        self.SEQUENCE.add_child(self.SUCCESS1)
        self.SEQUENCE.add_child(self.SUCCESS2)
        self.SEQUENCE.add_child(self.FAIL1)
        self.SEQUENCE.add_child(self.FAIL2)

        result = self.SEQUENCE.tick()
        assert_equal(result, NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS1._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS2._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.FAIL1._id),
                     NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.FAIL2._id),
                     NodeStatus.PENDING)

    def test_active(self):
        self.SEQUENCE.add_child(self.CONTINUE)
        self.SEQUENCE.add_child(self.SUCCESS1)
        self.SEQUENCE.add_child(self.SUCCESS2)
        self.SEQUENCE.add_child(self.FAIL1)
        self.SEQUENCE.add_child(self.FAIL2)

        result = self.SEQUENCE.tick()
        assert_equal(result, NodeStatus.ACTIVE)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE._id),
                     NodeStatus.ACTIVE)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS1._id),
                     NodeStatus.PENDING)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS2._id),
                     NodeStatus.PENDING)
        assert_equal(self.blackboard.get_node_status(self.FAIL1._id),
                     NodeStatus.PENDING)
        assert_equal(self.blackboard.get_node_status(self.FAIL2._id),
                     NodeStatus.PENDING)

    def test_cancel(self):
        self.SEQUENCE.add_child(self.CONTINUE)
        self.SEQUENCE.add_child(self.SUCCESS1)
        self.SEQUENCE.add_child(self.SUCCESS2)
        self.SEQUENCE.add_child(self.FAIL1)
        self.SEQUENCE.add_child(self.FAIL2)

        self.SEQUENCE.tick()
        self.SEQUENCE._cancel()
        result = self.SEQUENCE.tick()
        assert_equal(result, NodeStatus.CANCEL)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE._id),
                     NodeStatus.CANCEL)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS1._id),
                     NodeStatus.PENDING)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS2._id),
                     NodeStatus.PENDING)
        assert_equal(self.blackboard.get_node_status(self.FAIL1._id),
                     NodeStatus.PENDING)
        assert_equal(self.blackboard.get_node_status(self.FAIL2._id),
                     NodeStatus.PENDING)

    def test_force_child(self):
        self.SEQUENCE.add_child(self.CONTINUE)
        self.SEQUENCE.add_child(self.SUCCESS1)
        self.SEQUENCE.add_child(self.SUCCESS2)
        self.SEQUENCE.add_child(self.FAIL1)
        self.SEQUENCE.add_child(self.FAIL2)

        self.SEQUENCE.tick()
        self.CONTINUE.force(NodeStatus.SUCCESS)
        result = self.SEQUENCE.tick()
        assert_equal(result, NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS1._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS2._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.FAIL1._id),
                     NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.FAIL2._id),
                     NodeStatus.PENDING)

    def test_force_behavior(self):
        self.SEQUENCE.add_child(self.CONTINUE)
        self.SEQUENCE.add_child(self.SUCCESS1)
        self.SEQUENCE.add_child(self.SUCCESS2)
        self.SEQUENCE.add_child(self.FAIL1)
        self.SEQUENCE.add_child(self.FAIL2)

        self.SEQUENCE.tick()
        self.SEQUENCE.force(NodeStatus.SUCCESS)
        result = self.SEQUENCE.tick()
        assert_equal(result, NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE._id),
                     NodeStatus.CANCEL)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS1._id),
                     NodeStatus.PENDING)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS2._id),
                     NodeStatus.PENDING)
        assert_equal(self.blackboard.get_node_status(self.FAIL1._id),
                     NodeStatus.PENDING)
        assert_equal(self.blackboard.get_node_status(self.FAIL2._id),
                     NodeStatus.PENDING)


class TestRunner(object):

    def setUp(self):
        self.blackboard = Blackboard()
        self.FAIL1 = Fail(name="FAIL1", blackboard=self.blackboard)
        self.FAIL2 = Fail(name="FAIL2", blackboard=self.blackboard)
        self.SUCCESS1 = Success(name="SUCCESS1", blackboard=self.blackboard)
        self.SUCCESS2 = Success(name="SUCCESS2", blackboard=self.blackboard)
        self.CONTINUE = Continue(name="CONTINUE", blackboard=self.blackboard)

        self.RUNNER = Runner("RUNNER")
        self.RUNNER.set_blackboard(self.blackboard)
        self.nd = self.blackboard.get_memory(self.RUNNER._id)

    def test_success(self):
        self.RUNNER.add_child(self.SUCCESS1)
        self.RUNNER.add_child(self.FAIL1)
        self.RUNNER.add_child(self.SUCCESS2)
        self.RUNNER.add_child(self.FAIL2)

        result = self.RUNNER.tick()
        assert_equal(result, NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS1._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.FAIL1._id),
                     NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS2._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.FAIL2._id),
                     NodeStatus.FAIL)

    def test_active(self):
        self.RUNNER.add_child(self.SUCCESS1)
        self.RUNNER.add_child(self.FAIL1)
        self.RUNNER.add_child(self.CONTINUE)
        self.RUNNER.add_child(self.SUCCESS2)
        self.RUNNER.add_child(self.FAIL2)

        result = self.RUNNER.tick()
        assert_equal(result, NodeStatus.ACTIVE)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS1._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.FAIL1._id),
                     NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE._id),
                     NodeStatus.ACTIVE)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS2._id),
                     NodeStatus.PENDING)
        assert_equal(self.blackboard.get_node_status(self.FAIL2._id),
                     NodeStatus.PENDING)

    def test_cancel(self):
        self.RUNNER.add_child(self.SUCCESS1)
        self.RUNNER.add_child(self.FAIL1)
        self.RUNNER.add_child(self.CONTINUE)
        self.RUNNER.add_child(self.SUCCESS2)
        self.RUNNER.add_child(self.FAIL2)

        self.RUNNER.tick()
        self.RUNNER._cancel()
        result = self.RUNNER.tick()
        assert_equal(result, NodeStatus.CANCEL)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS1._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.FAIL1._id),
                     NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE._id),
                     NodeStatus.CANCEL)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS2._id),
                     NodeStatus.PENDING)
        assert_equal(self.blackboard.get_node_status(self.FAIL2._id),
                     NodeStatus.PENDING)

    def test_force_child(self):
        self.RUNNER.add_child(self.SUCCESS1)
        self.RUNNER.add_child(self.FAIL1)
        self.RUNNER.add_child(self.CONTINUE)
        self.RUNNER.add_child(self.SUCCESS2)
        self.RUNNER.add_child(self.FAIL2)

        self.RUNNER.tick()
        self.CONTINUE.force(NodeStatus.SUCCESS)
        result = self.RUNNER.tick()
        assert_equal(result, NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS1._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.FAIL1._id),
                     NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS2._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.FAIL2._id),
                     NodeStatus.FAIL)

    def test_force_behavior(self):
        self.RUNNER.add_child(self.SUCCESS1)
        self.RUNNER.add_child(self.FAIL1)
        self.RUNNER.add_child(self.CONTINUE)
        self.RUNNER.add_child(self.SUCCESS2)
        self.RUNNER.add_child(self.FAIL2)

        self.RUNNER.tick()
        self.RUNNER.force(NodeStatus.FAIL)
        result = self.RUNNER.tick()
        assert_equal(result, NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS1._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.FAIL1._id),
                     NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE._id),
                     NodeStatus.CANCEL)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS2._id),
                     NodeStatus.PENDING)
        assert_equal(self.blackboard.get_node_status(self.FAIL2._id),
                     NodeStatus.PENDING)


class TestAny(object):

    def setUp(self):
        self.blackboard = Blackboard()
        self.FAIL1 = Fail(name="FAIL1", blackboard=self.blackboard)
        self.FAIL2 = Fail(name="FAIL2", blackboard=self.blackboard)
        self.SUCCESS1 = Success(name="SUCCESS1", blackboard=self.blackboard)
        self.SUCCESS2 = Success(name="SUCCESS2", blackboard=self.blackboard)
        self.CONTINUE = Continue(name="CONTINUE", blackboard=self.blackboard)

        self.ANY = Any("ANY")
        self.ANY.set_blackboard(self.blackboard)
        self.nd = self.blackboard.get_memory(self.ANY._id)

    def test_fail(self):
        self.ANY.add_child(self.FAIL1)
        self.ANY.add_child(self.FAIL2)

        result = self.ANY.tick()
        assert_equal(result, NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.FAIL1._id),
                     NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.FAIL2._id),
                     NodeStatus.FAIL)

    def test_success(self):
        self.ANY.add_child(self.FAIL1)
        self.ANY.add_child(self.FAIL2)
        self.ANY.add_child(self.SUCCESS1)
        self.ANY.add_child(self.SUCCESS2)

        result = self.ANY.tick()
        assert_equal(result, NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.FAIL1._id),
                     NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.FAIL2._id),
                     NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS1._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS2._id),
                     NodeStatus.PENDING)

    def test_active(self):
        self.ANY.add_child(self.FAIL1)
        self.ANY.add_child(self.CONTINUE)
        self.ANY.add_child(self.FAIL2)

        result = self.ANY.tick()
        assert_equal(result, NodeStatus.ACTIVE)
        assert_equal(self.blackboard.get_node_status(self.FAIL1._id),
                     NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE._id),
                     NodeStatus.ACTIVE)
        assert_equal(self.blackboard.get_node_status(self.FAIL2._id),
                     NodeStatus.FAIL)

    def test_cancel(self):
        self.ANY.add_child(self.FAIL1)
        self.ANY.add_child(self.CONTINUE)
        self.ANY.add_child(self.FAIL2)

        self.ANY.tick()
        self.ANY._cancel()
        result = self.ANY.tick()
        assert_equal(result, NodeStatus.CANCEL)
        assert_equal(self.blackboard.get_node_status(self.FAIL1._id),
                     NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE._id),
                     NodeStatus.CANCEL)
        assert_equal(self.blackboard.get_node_status(self.FAIL2._id),
                     NodeStatus.FAIL)

    def test_force_child(self):
        self.ANY.add_child(self.FAIL1)
        self.ANY.add_child(self.CONTINUE)
        self.ANY.add_child(self.FAIL2)

        self.ANY.tick()
        self.CONTINUE.force(NodeStatus.SUCCESS)
        result = self.ANY.tick()
        assert_equal(result, NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.FAIL1._id),
                     NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.FAIL2._id),
                     NodeStatus.FAIL)

    def test_force_behavior(self):
        self.ANY.add_child(self.FAIL1)
        self.ANY.add_child(self.CONTINUE)
        self.ANY.add_child(self.FAIL2)

        self.ANY.tick()
        self.ANY.force(NodeStatus.FAIL)
        result = self.ANY.tick()
        assert_equal(result, NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.FAIL1._id),
                     NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE._id),
                     NodeStatus.CANCEL)
        assert_equal(self.blackboard.get_node_status(self.FAIL2._id),
                     NodeStatus.FAIL)


class TestAll(object):

    def setUp(self):
        self.blackboard = Blackboard()
        self.FAIL1 = Fail(name="FAIL1", blackboard=self.blackboard)
        self.FAIL2 = Fail(name="FAIL2", blackboard=self.blackboard)
        self.SUCCESS1 = Success(name="SUCCESS1", blackboard=self.blackboard)
        self.SUCCESS2 = Success(name="SUCCESS2", blackboard=self.blackboard)
        self.CONTINUE = Continue(name="CONTINUE", blackboard=self.blackboard)

        self.ALL = All("ALL")
        self.ALL.set_blackboard(self.blackboard)
        self.nd = self.blackboard.get_memory(self.ALL._id)

    def test_success(self):
        self.ALL.add_child(self.SUCCESS1)
        self.ALL.add_child(self.SUCCESS2)

        result = self.ALL.tick()
        assert_equal(result, NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS1._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS2._id),
                     NodeStatus.SUCCESS)

    def test_fail(self):
        self.ALL.add_child(self.SUCCESS1)
        self.ALL.add_child(self.SUCCESS2)
        self.ALL.add_child(self.FAIL1)
        self.ALL.add_child(self.FAIL2)

        result = self.ALL.tick()
        assert_equal(result, NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS1._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS2._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.FAIL1._id),
                     NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.FAIL2._id),
                     NodeStatus.PENDING)

    def test_active(self):
        self.ALL.add_child(self.SUCCESS1)
        self.ALL.add_child(self.CONTINUE)
        self.ALL.add_child(self.SUCCESS2)

        result = self.ALL.tick()
        assert_equal(result, NodeStatus.ACTIVE)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS1._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE._id),
                     NodeStatus.ACTIVE)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS2._id),
                     NodeStatus.SUCCESS)

    def test_cancel(self):
        self.ALL.add_child(self.SUCCESS1)
        self.ALL.add_child(self.CONTINUE)
        self.ALL.add_child(self.SUCCESS2)

        self.ALL.tick()
        self.ALL._cancel()
        result = self.ALL.tick()
        assert_equal(result, NodeStatus.CANCEL)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS1._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE._id),
                     NodeStatus.CANCEL)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS2._id),
                     NodeStatus.SUCCESS)

    def test_force_child(self):
        self.ALL.add_child(self.SUCCESS1)
        self.ALL.add_child(self.CONTINUE)
        self.ALL.add_child(self.SUCCESS2)

        self.ALL.tick()
        self.CONTINUE.force(NodeStatus.SUCCESS)
        result = self.ALL.tick()
        assert_equal(result, NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS1._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS2._id),
                     NodeStatus.SUCCESS)

    def test_force_behavior(self):
        self.ALL.add_child(self.SUCCESS1)
        self.ALL.add_child(self.CONTINUE)
        self.ALL.add_child(self.SUCCESS2)

        self.ALL.tick()
        self.ALL.force(NodeStatus.FAIL)
        result = self.ALL.tick()
        assert_equal(result, NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS1._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE._id),
                     NodeStatus.CANCEL)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS2._id),
                     NodeStatus.SUCCESS)
        self.blackboard.clear_node_status()


class TestRandom(object):

    def setUp(self):
        self.blackboard = Blackboard()
        self.FAIL1 = Fail(name="FAIL1", blackboard=self.blackboard)
        self.FAIL2 = Fail(name="FAIL2", blackboard=self.blackboard)
        self.SUCCESS1 = Success(name="SUCCESS1", blackboard=self.blackboard)
        self.SUCCESS2 = Success(name="SUCCESS2", blackboard=self.blackboard)
        self.CONTINUE = Continue(name="CONTINUE", blackboard=self.blackboard)

        self.RANDOM = Random("RANDOM")
        self.RANDOM.set_blackboard(self.blackboard)
        self.nd = self.blackboard.get_memory(self.RANDOM._id)

    def test_empty(self):
        # if empty, configuration should succeed but set child to None
        self.RANDOM._configure()
        assert_equal(self.RANDOM.child, None)

        # if ticked, random should report success if no children
        result = self.RANDOM.tick()
        assert_equal(self.RANDOM.child, None)
        assert_equal(result, NodeStatus.SUCCESS)

    def test_success(self):
        self.RANDOM.add_child(self.SUCCESS1)
        self.RANDOM.add_child(self.FAIL1)
        self.RANDOM.add_child(self.CONTINUE)

        self.RANDOM._configure()
        assert_equal(self.RANDOM.child in self.RANDOM._children, True)
        while (self.RANDOM.child != self.SUCCESS1):
            self.RANDOM._configure()

        result = self.RANDOM.tick()
        assert_equal(result, NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS1._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.FAIL1._id),
                     NodeStatus.PENDING)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE._id),
                     NodeStatus.PENDING)

    def test_fail(self):
        self.RANDOM.add_child(self.SUCCESS1)
        self.RANDOM.add_child(self.FAIL1)
        self.RANDOM.add_child(self.CONTINUE)

        self.RANDOM._configure()
        assert_equal(self.RANDOM.child in self.RANDOM._children, True)
        while (self.RANDOM.child != self.FAIL1):
            self.RANDOM._configure()

        result = self.RANDOM.tick()
        assert_equal(result, NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS1._id),
                     NodeStatus.PENDING)
        assert_equal(self.blackboard.get_node_status(self.FAIL1._id),
                     NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE._id),
                     NodeStatus.PENDING)

    def test_active(self):
        self.RANDOM.add_child(self.SUCCESS1)
        self.RANDOM.add_child(self.FAIL1)
        self.RANDOM.add_child(self.CONTINUE)

        self.RANDOM._configure()
        assert_equal(self.RANDOM.child in self.RANDOM._children, True)
        while (self.RANDOM.child != self.CONTINUE):
            self.RANDOM._configure()

        result = self.RANDOM.tick()
        assert_equal(result, NodeStatus.ACTIVE)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS1._id),
                     NodeStatus.PENDING)
        assert_equal(self.blackboard.get_node_status(self.FAIL1._id),
                     NodeStatus.PENDING)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE._id),
                     NodeStatus.ACTIVE)

    def test_cancel(self):
        self.RANDOM.add_child(self.SUCCESS1)
        self.RANDOM.add_child(self.FAIL1)
        self.RANDOM.add_child(self.CONTINUE)

        self.RANDOM._configure()
        assert_equal(self.RANDOM.child in self.RANDOM._children, True)
        while (self.RANDOM.child != self.CONTINUE):
            self.RANDOM._configure()

        self.RANDOM.tick()
        self.RANDOM._cancel()
        result = self.RANDOM.tick()
        assert_equal(result, NodeStatus.CANCEL)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS1._id),
                     NodeStatus.PENDING)
        assert_equal(self.blackboard.get_node_status(self.FAIL1._id),
                     NodeStatus.PENDING)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE._id),
                     NodeStatus.CANCEL)

    def test_force_child(self):
        self.RANDOM.add_child(self.SUCCESS1)
        self.RANDOM.add_child(self.FAIL1)
        self.RANDOM.add_child(self.CONTINUE)

        self.RANDOM._configure()
        self.RANDOM.child.force(NodeStatus.SUCCESS)
        result = self.RANDOM.tick()
        assert_equal(result, NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.RANDOM.child._id),
                     NodeStatus.SUCCESS)

    def test_force_behavior(self):
        self.RANDOM.add_child(self.SUCCESS1)
        self.RANDOM.add_child(self.FAIL1)
        self.RANDOM.add_child(self.CONTINUE)

        self.RANDOM._configure()
        self.RANDOM.force(NodeStatus.FAIL)
        result = self.RANDOM.tick()
        assert_equal(result, NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.RANDOM.child._id),
                     NodeStatus.PENDING)


class TestProgressor(object):

    def setUp(self):
        self.blackboard = Blackboard()
        self.FAIL1 = Fail(name="FAIL1", blackboard=self.blackboard)
        self.FAIL2 = Fail(name="FAIL2", blackboard=self.blackboard)
        self.SUCCESS1 = Success(name="SUCCESS1", blackboard=self.blackboard)
        self.SUCCESS2 = Success(name="SUCCESS2", blackboard=self.blackboard)
        self.CONTINUE = Continue(name="CONTINUE", blackboard=self.blackboard)
        self.CONTINUE2 = Continue(name="CONTINUE2", blackboard=self.blackboard)

        self.PROGRESS = Progressor("PROGRESS")
        self.PROGRESS.set_blackboard(self.blackboard)
        self.nd = self.blackboard.get_memory(self.PROGRESS._id)

    def test_success(self):
        self.PROGRESS.add_child(self.SUCCESS1)
        self.PROGRESS.add_child(self.SUCCESS2)

        result = self.PROGRESS.tick()
        assert_equal(result, NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS1._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS2._id),
                     NodeStatus.SUCCESS)

    def test_fail(self):
        self.PROGRESS.add_child(self.SUCCESS1)
        self.PROGRESS.add_child(self.SUCCESS2)
        self.PROGRESS.add_child(self.FAIL1)
        self.PROGRESS.add_child(self.FAIL2)

        result = self.PROGRESS.tick()
        assert_equal(result, NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS1._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS2._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.FAIL1._id),
                     NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.FAIL2._id),
                     NodeStatus.PENDING)

    def test_active(self):
        self.PROGRESS.add_child(self.SUCCESS1)
        self.PROGRESS.add_child(self.CONTINUE)
        self.PROGRESS.add_child(self.SUCCESS2)
        self.PROGRESS.add_child(self.FAIL1)
        self.PROGRESS.add_child(self.FAIL2)

        result = self.PROGRESS.tick()
        assert_equal(result, NodeStatus.ACTIVE)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS1._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE._id),
                     NodeStatus.ACTIVE)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS2._id),
                     NodeStatus.PENDING)
        assert_equal(self.blackboard.get_node_status(self.FAIL1._id),
                     NodeStatus.PENDING)
        assert_equal(self.blackboard.get_node_status(self.FAIL2._id),
                     NodeStatus.PENDING)

    def test_cancel(self):
        self.PROGRESS.add_child(self.SUCCESS1)
        self.PROGRESS.add_child(self.CONTINUE)
        self.PROGRESS.add_child(self.SUCCESS2)
        self.PROGRESS.add_child(self.FAIL1)
        self.PROGRESS.add_child(self.FAIL2)

        self.PROGRESS.tick()
        self.PROGRESS._cancel()
        result = self.PROGRESS.tick()
        assert_equal(result, NodeStatus.CANCEL)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS1._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE._id),
                     NodeStatus.CANCEL)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS2._id),
                     NodeStatus.PENDING)
        assert_equal(self.blackboard.get_node_status(self.FAIL1._id),
                     NodeStatus.PENDING)
        assert_equal(self.blackboard.get_node_status(self.FAIL2._id),
                     NodeStatus.PENDING)

    def test_force_child(self):
        self.PROGRESS.add_child(self.SUCCESS1)
        self.PROGRESS.add_child(self.CONTINUE)
        self.PROGRESS.add_child(self.CONTINUE2)
        self.PROGRESS.add_child(self.FAIL1)
        self.PROGRESS.add_child(self.FAIL2)

        self.PROGRESS.tick()
        self.CONTINUE.force(NodeStatus.SUCCESS)
        result = self.PROGRESS.tick()
        assert_equal(result, NodeStatus.ACTIVE)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS1._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE2._id),
                     NodeStatus.ACTIVE)
        assert_equal(self.blackboard.get_node_status(self.FAIL1._id),
                     NodeStatus.PENDING)
        assert_equal(self.blackboard.get_node_status(self.FAIL2._id),
                     NodeStatus.PENDING)

        self.CONTINUE2.force(NodeStatus.SUCCESS)
        result = self.PROGRESS.tick()
        assert_equal(result, NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS1._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE2._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.FAIL1._id),
                     NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.FAIL2._id),
                     NodeStatus.PENDING)

    def test_force_behavior(self):
        self.PROGRESS.add_child(self.SUCCESS1)
        self.PROGRESS.add_child(self.CONTINUE)
        self.PROGRESS.add_child(self.CONTINUE2)
        self.PROGRESS.add_child(self.FAIL1)
        self.PROGRESS.add_child(self.FAIL2)

        self.PROGRESS.tick()
        self.PROGRESS.force(NodeStatus.SUCCESS)
        result = self.PROGRESS.tick()
        assert_equal(result, NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS1._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE._id),
                     NodeStatus.CANCEL)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE2._id),
                     NodeStatus.PENDING)
        assert_equal(self.blackboard.get_node_status(self.FAIL1._id),
                     NodeStatus.PENDING)
        assert_equal(self.blackboard.get_node_status(self.FAIL2._id),
                     NodeStatus.PENDING)


class TestMajority(object):

    def setUp(self):
        self.blackboard = Blackboard()
        self.FAIL1 = Fail(name="FAIL1", blackboard=self.blackboard)
        self.FAIL2 = Fail(name="FAIL2", blackboard=self.blackboard)
        self.SUCCESS1 = Success(name="SUCCESS1", blackboard=self.blackboard)
        self.SUCCESS2 = Success(name="SUCCESS2", blackboard=self.blackboard)
        self.CONTINUE = Continue(name="CONTINUE", blackboard=self.blackboard)
        self.CONTINUE2 = Continue(name="CONTINUE2", blackboard=self.blackboard)

        self.MAJORITY = Majority("MAJORITY")
        self.MAJORITY.set_blackboard(self.blackboard)
        self.nd = self.blackboard.get_memory(self.MAJORITY._id)

    def test_success(self):
        self.MAJORITY.add_child(self.SUCCESS1)
        self.MAJORITY.add_child(self.SUCCESS2)

        result = self.MAJORITY.tick()
        assert_equal(result.status, NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS1._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS2._id),
                     NodeStatus.PENDING)

    def test_fail(self):
        self.MAJORITY.add_child(self.FAIL1)
        self.MAJORITY.add_child(self.FAIL2)

        result = self.MAJORITY.tick()
        assert_equal(result, NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.FAIL1._id),
                     NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.FAIL2._id),
                     NodeStatus.FAIL)

        self.MAJORITY.add_child(self.SUCCESS1)
        result = self.MAJORITY.tick()
        assert_equal(result, NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.FAIL1._id),
                     NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.FAIL2._id),
                     NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS1._id),
                     NodeStatus.PENDING)

    def test_active(self):
        self.MAJORITY.add_child(self.CONTINUE)
        self.MAJORITY.add_child(self.SUCCESS1)
        self.MAJORITY.add_child(self.SUCCESS2)
        self.MAJORITY.add_child(self.FAIL1)
        self.MAJORITY.add_child(self.FAIL2)

        result = self.MAJORITY.tick()
        assert_equal(result, NodeStatus.ACTIVE)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE._id),
                     NodeStatus.ACTIVE)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS1._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS2._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.FAIL1._id),
                     NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.FAIL2._id),
                     NodeStatus.FAIL)

    def test_cancel(self):
        self.MAJORITY.add_child(self.CONTINUE)
        self.MAJORITY.add_child(self.SUCCESS1)
        self.MAJORITY.add_child(self.SUCCESS2)
        self.MAJORITY.add_child(self.FAIL1)
        self.MAJORITY.add_child(self.FAIL2)

        self.MAJORITY.tick()
        self.MAJORITY._cancel()
        result = self.MAJORITY.tick()
        assert_equal(result, NodeStatus.CANCEL)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE._id),
                     NodeStatus.CANCEL)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS1._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS2._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.FAIL1._id),
                     NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.FAIL2._id),
                     NodeStatus.FAIL)

    def test_force_child(self):
        self.MAJORITY.add_child(self.CONTINUE)
        self.MAJORITY.add_child(self.SUCCESS1)
        self.MAJORITY.add_child(self.SUCCESS2)
        self.MAJORITY.add_child(self.FAIL1)
        self.MAJORITY.add_child(self.FAIL2)

        self.MAJORITY.tick()
        self.CONTINUE.force(NodeStatus.SUCCESS)
        result = self.MAJORITY.tick()
        assert_equal(result, NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS1._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS2._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.FAIL1._id),
                     NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.FAIL2._id),
                     NodeStatus.FAIL)

        self.CONTINUE.force(NodeStatus.FAIL)
        result = self.MAJORITY.tick()
        assert_equal(result, NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE._id),
                     NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS1._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS2._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.FAIL1._id),
                     NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.FAIL2._id),
                     NodeStatus.FAIL)

    def test_force_behavior(self):
        self.MAJORITY.add_child(self.CONTINUE)
        self.MAJORITY.add_child(self.SUCCESS1)
        self.MAJORITY.add_child(self.SUCCESS2)
        self.MAJORITY.add_child(self.FAIL1)
        self.MAJORITY.add_child(self.FAIL2)

        self.MAJORITY.tick()
        self.MAJORITY.force(NodeStatus.SUCCESS)
        result = self.MAJORITY.tick()
        assert_equal(result, NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE._id),
                     NodeStatus.CANCEL)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS1._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS2._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.FAIL1._id),
                     NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.FAIL2._id),
                     NodeStatus.FAIL)


class TestFirst(object):

    def setUp(self):
        self.blackboard = Blackboard()
        self.FAIL1 = Fail(name="FAIL1", blackboard=self.blackboard)
        self.FAIL2 = Fail(name="FAIL2", blackboard=self.blackboard)
        self.SUCCESS1 = Success(name="SUCCESS1", blackboard=self.blackboard)
        self.SUCCESS2 = Success(name="SUCCESS2", blackboard=self.blackboard)
        self.CONTINUE1 = Continue(name="CONTINUE1", blackboard=self.blackboard)
        self.CONTINUE2 = Continue(name="CONTINUE2", blackboard=self.blackboard)

        self.FIRST = First("FIRST")
        self.FIRST.set_blackboard(self.blackboard)
        self.nd = self.blackboard.get_memory(self.FIRST._id)

    def test_success(self):
        self.FIRST.add_child(self.SUCCESS1)
        self.FIRST.add_child(self.SUCCESS2)

        result = self.FIRST.tick()
        assert_equal(result.status, NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS1._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS2._id),
                     NodeStatus.PENDING)

    def test_fail(self):
        self.FIRST.add_child(self.FAIL1)
        self.FIRST.add_child(self.FAIL2)

        result = self.FIRST.tick()
        assert_equal(result, NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.FAIL1._id),
                     NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.FAIL2._id),
                     NodeStatus.PENDING)

    def test_active(self):
        self.FIRST.add_child(self.CONTINUE1)
        self.FIRST.add_child(self.CONTINUE2)

        result = self.FIRST.tick()
        assert_equal(result, NodeStatus.ACTIVE)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE1._id),
                     NodeStatus.ACTIVE)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE2._id),
                     NodeStatus.ACTIVE)

        self.FIRST.add_child(self.SUCCESS1)
        self.FIRST.add_child(self.SUCCESS2)
        self.FIRST.add_child(self.FAIL1)
        self.FIRST.add_child(self.FAIL2)

        result = self.FIRST.tick()
        assert_equal(result, NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE1._id),
                     NodeStatus.CANCEL)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE2._id),
                     NodeStatus.CANCEL)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS1._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS2._id),
                     NodeStatus.PENDING)
        assert_equal(self.blackboard.get_node_status(self.FAIL1._id),
                     NodeStatus.PENDING)
        assert_equal(self.blackboard.get_node_status(self.FAIL2._id),
                     NodeStatus.PENDING)

    def test_cancel(self):
        self.FIRST.add_child(self.CONTINUE1)
        self.FIRST.add_child(self.CONTINUE2)

        self.FIRST.tick()
        self.FIRST._cancel()
        result = self.FIRST.tick()
        assert_equal(result, NodeStatus.CANCEL)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE1._id),
                     NodeStatus.CANCEL)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE2._id),
                     NodeStatus.CANCEL)

    def test_force_child(self):
        self.FIRST.add_child(self.CONTINUE1)
        self.FIRST.add_child(self.CONTINUE2)

        self.FIRST.tick()
        self.CONTINUE1.force(NodeStatus.SUCCESS)
        result = self.FIRST.tick()
        assert_equal(result, NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE1._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE2._id),
                     NodeStatus.CANCEL)

        self.CONTINUE1.force(NodeStatus.FAIL)
        result = self.FIRST.tick()
        assert_equal(result, NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE1._id),
                     NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE2._id),
                     NodeStatus.CANCEL)

    def test_force_behavior(self):
        self.FIRST.add_child(self.CONTINUE1)
        self.FIRST.add_child(self.CONTINUE2)

        self.FIRST.tick()
        self.FIRST.force(NodeStatus.SUCCESS)
        result = self.FIRST.tick()
        assert_equal(result, NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE1._id),
                     NodeStatus.CANCEL)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE2._id),
                     NodeStatus.CANCEL)

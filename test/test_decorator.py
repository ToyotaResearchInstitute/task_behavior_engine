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

from task_behavior_engine.decorator import Fail
from task_behavior_engine.decorator import Negate
from task_behavior_engine.decorator import Repeat
from task_behavior_engine.decorator import Succeed
from task_behavior_engine.decorator import Until
from task_behavior_engine.decorator import While

from task_behavior_engine.node import Continue
from task_behavior_engine.node import Fail as Failure
from task_behavior_engine.node import Success

from task_behavior_engine.tree import Blackboard
from task_behavior_engine.tree import Node
from task_behavior_engine.tree import NodeStatus


class TestNegate(object):

    def setUp(self):
        self.blackboard = Blackboard()

        self.FAILURE = Failure(name="FAILURE", blackboard=self.blackboard)
        self.SUCCESS = Success(name="SUCCESS", blackboard=self.blackboard)
        self.CONTINUE = Continue(name="CONTINUE", blackboard=self.blackboard)

    def test_fail(self):
        NOT_FAIL = Negate(name="NOT_FAILURE",
                          blackboard=self.blackboard,
                          child=self.FAILURE)
        result = NOT_FAIL.tick()
        assert_equal(result, NodeStatus.SUCCESS)

    def test_success(self):
        NOT_SUCCESS = Negate(name="NOT_SUCCESS",
                             blackboard=self.blackboard,
                             child=self.SUCCESS)
        result = NOT_SUCCESS.tick()
        assert_equal(result, NodeStatus.FAIL)

    def test_active(self):
        ACTIVE = Negate(name="NOT_CONTINUE",
                        blackboard=self.blackboard,
                        child=self.CONTINUE)
        result = ACTIVE.tick()
        assert_equal(result, NodeStatus.ACTIVE)

    def test_cancel(self):
        ACTIVE = Negate(name="NOT_CONTINUE",
                        blackboard=self.blackboard,
                        child=self.CONTINUE)
        result = ACTIVE.tick()
        assert_equal(result, NodeStatus.ACTIVE)
        ACTIVE._cancel()
        assert_equal(ACTIVE.get_result(), NodeStatus.CANCEL)
        assert_equal(ACTIVE._child.get_result(), NodeStatus.CANCEL)
        result = ACTIVE.tick()
        assert_equal(result, NodeStatus.CANCEL)
        assert_equal(ACTIVE.get_result(), NodeStatus.PENDING)
        assert_equal(ACTIVE._child.get_result(), NodeStatus.PENDING)

    def test_force(self):
        NOT_SUCCESS = Negate(name="NOT_SUCCESS",
                             blackboard=self.blackboard,
                             child=self.SUCCESS)
        NOT_SUCCESS._child.force(NodeStatus.FAIL)
        result = NOT_SUCCESS.tick()
        assert_equal(result, NodeStatus.SUCCESS)

        # Test FORCE behavior
        NOT_FAIL = Negate(name="NOT_FAILURE",
                          blackboard=self.blackboard,
                          child=self.FAILURE)
        NOT_FAIL.force(NodeStatus.FAIL)
        result = NOT_FAIL.tick()
        assert_equal(result, NodeStatus.FAIL)


class TestRepeat(object):

    def setUp(self):
        self.blackboard = Blackboard()

        self.FAILURE = Failure(name="FAILURE", blackboard=self.blackboard)
        self.SUCCESS = Success(name="SUCCESS", blackboard=self.blackboard)
        self.CONTINUE = Continue(name="CONTINUE", blackboard=self.blackboard)

    def test_fail(self):
        REPEAT_FAIL = Repeat(name="REPEAT_FAILURE",
                             blackboard=self.blackboard,
                             child=self.FAILURE)
        result = REPEAT_FAIL.tick()
        assert_equal(result, NodeStatus.ACTIVE)
        assert_equal(self.blackboard.get_node_status(REPEAT_FAIL._id),
                     NodeStatus.ACTIVE)
        assert_equal(self.blackboard.get_node_status(self.FAILURE._id),
                     NodeStatus.FAIL)

    def test_success(self):
        REPEAT_SUCCESS = Repeat(name="REPEAT_SUCCESS",
                                blackboard=self.blackboard,
                                child=self.SUCCESS)
        result = REPEAT_SUCCESS.tick()
        assert_equal(result, NodeStatus.ACTIVE)
        assert_equal(self.blackboard.get_node_status(REPEAT_SUCCESS._id),
                     NodeStatus.ACTIVE)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS._id),
                     NodeStatus.SUCCESS)

    def test_active(self):
        ACTIVE = Repeat(name="REPEAT_CONTINUE",
                        blackboard=self.blackboard,
                        child=self.CONTINUE)
        result = ACTIVE.tick()
        assert_equal(result, NodeStatus.ACTIVE)
        assert_equal(self.blackboard.get_node_status(ACTIVE._id),
                     NodeStatus.ACTIVE)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE._id),
                     NodeStatus.ACTIVE)

    def test_cancel(self):
        ACTIVE = Repeat(name="REPEAT_CONTINUE",
                        blackboard=self.blackboard,
                        child=self.CONTINUE)
        result = ACTIVE.tick()
        ACTIVE._cancel()
        assert_equal(ACTIVE.get_result(), NodeStatus.CANCEL)
        assert_equal(ACTIVE._child.get_result(), NodeStatus.CANCEL)
        assert_equal(self.blackboard.get_node_status(ACTIVE._id),
                     NodeStatus.CANCEL)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE._id),
                     NodeStatus.CANCEL)
        result = ACTIVE.tick()
        assert_equal(result, NodeStatus.CANCEL)
        assert_equal(ACTIVE.get_result(), NodeStatus.PENDING)
        assert_equal(ACTIVE._child.get_result(), NodeStatus.PENDING)
        assert_equal(self.blackboard.get_node_status(ACTIVE._id),
                     NodeStatus.CANCEL)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE._id),
                     NodeStatus.CANCEL)

    def test_cancel_child(self):
        ACTIVE = Repeat(name="REPEAT_CONTINUE",
                        blackboard=self.blackboard,
                        child=self.CONTINUE)
        ACTIVE.tick()
        ACTIVE._child._cancel()
        assert_equal(ACTIVE.get_result(), NodeStatus.ACTIVE)
        assert_equal(ACTIVE._child.get_result(), NodeStatus.CANCEL)
        assert_equal(self.blackboard.get_node_status(ACTIVE._id),
                     NodeStatus.ACTIVE)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE._id),
                     NodeStatus.CANCEL)
        result = ACTIVE.tick()
        assert_equal(result.status, NodeStatus.CANCEL)
        assert_equal(ACTIVE.get_result(), NodeStatus.PENDING)
        assert_equal(ACTIVE._child.get_result(), NodeStatus.PENDING)
        assert_equal(self.blackboard.get_node_status(ACTIVE._id),
                     NodeStatus.CANCEL)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE._id),
                     NodeStatus.CANCEL)

    def test_force_child(self):
        NOT_SUCCESS = Repeat(name="NOT_SUCCESS",
                             blackboard=self.blackboard,
                             child=self.SUCCESS)
        NOT_SUCCESS._child.force(NodeStatus.FAIL)
        result = NOT_SUCCESS.tick()
        assert_equal(result, NodeStatus.ACTIVE)
        assert_equal(self.blackboard.get_node_status(NOT_SUCCESS._id),
                     NodeStatus.ACTIVE)
        assert_equal(self.blackboard.get_node_status(self.SUCCESS._id),
                     NodeStatus.FAIL)

    def test_force_behavior(self):
        NOT_FAIL = Repeat(name="NOT_FAILURE",
                          blackboard=self.blackboard,
                          child=self.FAILURE)
        result = NOT_FAIL.tick()
        NOT_FAIL.force(NodeStatus.SUCCESS)
        result = NOT_FAIL.tick()
        assert_equal(result, NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(NOT_FAIL._id),
                     NodeStatus.SUCCESS)
        assert_equal(self.blackboard.get_node_status(self.FAILURE._id),
                     NodeStatus.FAIL)

        NOT_CONTINUE = Repeat(name="NOT_CONTINUE",
                              blackboard=self.blackboard,
                              child=self.CONTINUE)
        result = NOT_CONTINUE.tick()
        NOT_CONTINUE.force(NodeStatus.FAIL)
        result = NOT_CONTINUE.tick()
        assert_equal(result, NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(NOT_CONTINUE._id),
                     NodeStatus.FAIL)
        assert_equal(self.blackboard.get_node_status(self.CONTINUE._id),
                     NodeStatus.CANCEL)


class TestWhile(object):

    def setUp(self):
        self.blackboard = Blackboard()

        self.FAILURE = Failure(name="FAILURE", blackboard=self.blackboard)
        self.SUCCESS = Success(name="SUCCESS", blackboard=self.blackboard)
        self.CONTINUE = Continue(name="CONTINUE", blackboard=self.blackboard)

    def test_fail(self):
        WHILE_FAIL = While(name="WHILE_FAILURE",
                           blackboard=self.blackboard,
                           child=self.FAILURE)
        result = WHILE_FAIL.tick()
        assert_equal(result, NodeStatus.FAIL)

    def test_success(self):
        WHILE_SUCCESS = While(name="WHILE_SUCCESS",
                              blackboard=self.blackboard,
                              child=self.SUCCESS)
        result = WHILE_SUCCESS.tick()
        assert_equal(result, NodeStatus.ACTIVE)

    def test_active(self):
        ACTIVE = While(name="WHILE_CONTINUE",
                       blackboard=self.blackboard,
                       child=self.CONTINUE)
        result = ACTIVE.tick()
        assert_equal(result, NodeStatus.ACTIVE)

    def test_cancel(self):
        ACTIVE = While(name="WHILE_CONTINUE",
                       blackboard=self.blackboard,
                       child=self.CONTINUE)
        result = ACTIVE.tick()
        ACTIVE._cancel()
        assert_equal(ACTIVE.get_result(), NodeStatus.CANCEL)
        assert_equal(ACTIVE._child.get_result(), NodeStatus.CANCEL)
        result = ACTIVE.tick()
        assert_equal(result, NodeStatus.CANCEL)
        assert_equal(ACTIVE.get_result(), NodeStatus.PENDING)
        assert_equal(ACTIVE._child.get_result(), NodeStatus.PENDING)

    def test_cancel_child(self):
        ACTIVE = While(name="WHILE_CONTINUE",
                       blackboard=self.blackboard,
                       child=self.CONTINUE)
        ACTIVE.tick()
        ACTIVE._child._cancel()
        assert_equal(ACTIVE.get_result(), NodeStatus.ACTIVE)
        assert_equal(ACTIVE._child.get_result(), NodeStatus.CANCEL)
        result = ACTIVE.tick()
        assert_equal(result.status, NodeStatus.CANCEL)
        assert_equal(ACTIVE.get_result(), NodeStatus.PENDING)
        assert_equal(ACTIVE._child.get_result(), NodeStatus.PENDING)

    def test_force_child(self):
        NOT_SUCCESS = While(name="NOT_SUCCESS",
                            blackboard=self.blackboard,
                            child=self.SUCCESS)
        NOT_SUCCESS._child.force(NodeStatus.FAIL)
        result = NOT_SUCCESS.tick()
        assert_equal(result, NodeStatus.FAIL)

    def test_force_behavior(self):
        NOT_FAIL = While(name="NOT_FAILURE",
                         blackboard=self.blackboard,
                         child=self.FAILURE)
        NOT_FAIL.force(NodeStatus.SUCCESS)
        result = NOT_FAIL.tick()
        assert_equal(result, NodeStatus.SUCCESS)


class TestUntil(object):

    def setUp(self):
        self.blackboard = Blackboard()

        self.FAILURE = Failure(name="FAILURE", blackboard=self.blackboard)
        self.SUCCESS = Success(name="SUCCESS", blackboard=self.blackboard)
        self.CONTINUE = Continue(name="CONTINUE", blackboard=self.blackboard)

    def test_fail(self):
        UNTIL_FAIL = Until(name="UNTIL_FAILURE",
                           blackboard=self.blackboard,
                           child=self.FAILURE)
        result = UNTIL_FAIL.tick()
        assert_equal(result, NodeStatus.ACTIVE)

    def test_success(self):
        UNTIL_SUCCESS = Until(name="UNTIL_SUCCESS",
                              blackboard=self.blackboard,
                              child=self.SUCCESS)
        result = UNTIL_SUCCESS.tick()
        assert_equal(result, NodeStatus.SUCCESS)

    def test_active(self):
        ACTIVE = Until(name="UNTIL_CONTINUE",
                       blackboard=self.blackboard,
                       child=self.CONTINUE)
        result = ACTIVE.tick()
        assert_equal(result, NodeStatus.ACTIVE)

    def test_cancel(self):
        ACTIVE = Until(name="UNTIL_CONTINUE",
                       blackboard=self.blackboard,
                       child=self.CONTINUE)
        result = ACTIVE.tick()
        ACTIVE._cancel()
        assert_equal(ACTIVE.get_result(), NodeStatus.CANCEL)
        assert_equal(ACTIVE._child.get_result(), NodeStatus.CANCEL)
        result = ACTIVE.tick()
        assert_equal(result, NodeStatus.CANCEL)
        assert_equal(ACTIVE.get_result(), NodeStatus.PENDING)
        assert_equal(ACTIVE._child.get_result(), NodeStatus.PENDING)

    def test_cancel_child(self):
        ACTIVE = Until(name="UNTIL_CONTINUE",
                       blackboard=self.blackboard,
                       child=self.CONTINUE)
        ACTIVE.tick()
        ACTIVE._child._cancel()
        assert_equal(ACTIVE.get_result(), NodeStatus.ACTIVE)
        assert_equal(ACTIVE._child.get_result(), NodeStatus.CANCEL)
        result = ACTIVE.tick()
        assert_equal(result.status, NodeStatus.CANCEL)
        assert_equal(ACTIVE.get_result(), NodeStatus.PENDING)
        assert_equal(ACTIVE._child.get_result(), NodeStatus.PENDING)

    def test_force_child(self):
        NOT_SUCCESS = Until(name="NOT_SUCCESS",
                            blackboard=self.blackboard,
                            child=self.SUCCESS)
        NOT_SUCCESS._child.force(NodeStatus.FAIL)
        result = NOT_SUCCESS.tick()
        assert_equal(result, NodeStatus.ACTIVE)

    def test_force_behavior(self):
        NOT_FAIL = Until(name="NOT_FAIL",
                         blackboard=self.blackboard,
                         child=self.FAILURE)
        NOT_FAIL.force(NodeStatus.SUCCESS)
        result = NOT_FAIL.tick()
        assert_equal(result, NodeStatus.SUCCESS)


class TestFail(object):

    def setUp(self):
        self.blackboard = Blackboard()

        self.FAILURE = Failure(name="FAILURE", blackboard=self.blackboard)
        self.SUCCESS = Success(name="SUCCESS", blackboard=self.blackboard)
        self.CONTINUE = Continue(name="CONTINUE", blackboard=self.blackboard)

    def test_fail(self):
        TEST = Fail(name="FAIL_FAILURE",
                    blackboard=self.blackboard,
                    child=self.FAILURE)
        result = TEST.tick()
        assert_equal(result, NodeStatus.FAIL)

    def test_success(self):
        TEST = Fail(name="FAIL_SUCCESS",
                    blackboard=self.blackboard,
                    child=self.SUCCESS)
        result = TEST.tick()
        assert_equal(result, NodeStatus.FAIL)

    def test_active(self):
        ACTIVE = Fail(name="FAIL_CONTINUE",
                      blackboard=self.blackboard,
                      child=self.CONTINUE)
        result = ACTIVE.tick()
        assert_equal(result, NodeStatus.ACTIVE)

    def test_cancel(self):
        ACTIVE = Fail(name="FAIL_CONTINUE",
                      blackboard=self.blackboard,
                      child=self.CONTINUE)
        result = ACTIVE.tick()
        ACTIVE._cancel()
        assert_equal(ACTIVE.get_result(), NodeStatus.CANCEL)
        assert_equal(ACTIVE._child.get_result(), NodeStatus.CANCEL)
        result = ACTIVE.tick()
        assert_equal(result, NodeStatus.CANCEL)
        assert_equal(ACTIVE.get_result(), NodeStatus.PENDING)
        assert_equal(ACTIVE._child.get_result(), NodeStatus.PENDING)

    def test_cancel_child(self):
        ACTIVE = Fail(name="FAIL_CONTINUE",
                      blackboard=self.blackboard,
                      child=self.CONTINUE)
        ACTIVE.tick()
        ACTIVE._child._cancel()
        assert_equal(ACTIVE.get_result(), NodeStatus.ACTIVE)
        assert_equal(ACTIVE._child.get_result(), NodeStatus.CANCEL)
        result = ACTIVE.tick()
        assert_equal(result.status, NodeStatus.CANCEL)
        assert_equal(ACTIVE.get_result(), NodeStatus.PENDING)
        assert_equal(ACTIVE._child.get_result(), NodeStatus.PENDING)

    def test_force_child(self):
        TEST = Fail(name="SUCCESS_CHILD",
                    blackboard=self.blackboard,
                    child=self.CONTINUE)
        TEST._child.force(NodeStatus.SUCCESS)
        result = TEST.tick()
        assert_equal(result, NodeStatus.FAIL)

    def test_force_behavior(self):
        TEST = Fail(name="FORCE_SUCCESS",
                    blackboard=self.blackboard,
                    child=self.CONTINUE)
        TEST.force(NodeStatus.SUCCESS)
        result = TEST.tick()
        assert_equal(result, NodeStatus.SUCCESS)


class TestSucceed(object):

    def setUp(self):
        self.blackboard = Blackboard()

        self.FAILURE = Failure(name="FAILURE", blackboard=self.blackboard)
        self.SUCCESS = Success(name="SUCCESS", blackboard=self.blackboard)
        self.CONTINUE = Continue(name="CONTINUE", blackboard=self.blackboard)

    def test_fail(self):
        TEST = Succeed(name="SUCCEED_FAILURE",
                       blackboard=self.blackboard,
                       child=self.FAILURE)
        result = TEST.tick()
        assert_equal(result, NodeStatus.SUCCESS)

    def test_success(self):
        TEST = Succeed(name="SUCCEED_SUCCESS",
                       blackboard=self.blackboard,
                       child=self.SUCCESS)
        result = TEST.tick()
        assert_equal(result, NodeStatus.SUCCESS)

    def test_active(self):
        ACTIVE = Succeed(name="SUCCEED_CONTINUE",
                         blackboard=self.blackboard,
                         child=self.CONTINUE)
        result = ACTIVE.tick()
        assert_equal(result, NodeStatus.ACTIVE)

    def test_cancel(self):
        ACTIVE = Succeed(name="SUCCEED_CONTINUE",
                         blackboard=self.blackboard,
                         child=self.CONTINUE)
        result = ACTIVE.tick()
        ACTIVE._cancel()
        assert_equal(ACTIVE.get_result(), NodeStatus.CANCEL)
        assert_equal(ACTIVE._child.get_result(), NodeStatus.CANCEL)
        result = ACTIVE.tick()
        assert_equal(result, NodeStatus.CANCEL)
        assert_equal(ACTIVE.get_result(), NodeStatus.PENDING)
        assert_equal(ACTIVE._child.get_result(), NodeStatus.PENDING)

    def test_cancel_child(self):
        ACTIVE = Succeed(name="SUCCEED_CONTINUE",
                         blackboard=self.blackboard,
                         child=self.CONTINUE)
        ACTIVE.tick()
        ACTIVE._child._cancel()
        assert_equal(ACTIVE.get_result(), NodeStatus.ACTIVE)
        assert_equal(ACTIVE._child.get_result(), NodeStatus.CANCEL)
        result = ACTIVE.tick()
        assert_equal(result.status, NodeStatus.CANCEL)
        assert_equal(ACTIVE.get_result(), NodeStatus.PENDING)
        assert_equal(ACTIVE._child.get_result(), NodeStatus.PENDING)

    def test_force_child(self):
        TEST = Succeed(name="SUCCESS_CHILD",
                       blackboard=self.blackboard,
                       child=self.CONTINUE)
        TEST._child.force(NodeStatus.FAIL)
        result = TEST.tick()
        assert_equal(result, NodeStatus.SUCCESS)

    def test_force_behavior(self):
        TEST = Succeed(name="FORCE_SUCCESS",
                       blackboard=self.blackboard,
                       child=self.CONTINUE)
        TEST.force(NodeStatus.FAIL)
        result = TEST.tick()
        assert_equal(result, NodeStatus.FAIL)

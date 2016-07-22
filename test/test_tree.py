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
from nose.tools import assert_not_equal
from nose.tools import assert_raises

from task_behavior_engine.tree import Behavior
from task_behavior_engine.tree import Blackboard
from task_behavior_engine.tree import Decorator
from task_behavior_engine.tree import Node
from task_behavior_engine.tree import NodeData
from task_behavior_engine.tree import NodeStatus


class TestNodeData(object):

    def test_init(self):
        nd = NodeData()
        assert_equal(nd._data, {})
        assert_equal(nd._locks, {})

    def test_assignment(self):
        nd = NodeData()
        # check variable assignment
        nd.test = "hello world"
        assert_equal(nd._data['test'], 'hello world')
        # check dictionary assignment
        nd['foo'] = "bar"
        assert_equal(nd._data['foo'], 'bar')
        # check set_data
        nd.set_data("universe", 47)
        assert_equal(nd._data['universe'], 47)

    def test_keys(self):
        nd = NodeData()
        nd.key1 = "first key"
        assert_equal(nd.keys(), ['key1'])
        nd.key2 = "second key"
        assert_equal(True, 'key2' in nd.keys())
        assert_equal(True, 'key1' in nd.keys())

    def test_get_data(self):
        nd = NodeData()
        # check retrieval from set
        nd.set_data("universe", 47)
        assert_equal(nd.get_data("universe"), 47)
        # check default operator
        assert_equal(nd.get_data("ros", "bag"), "bag")
        # check retrieval of non-existing data
        assert_equal(nd.get_data("none"), None)

    def test_contains(self):
        nd = NodeData()
        nd.test = "hello world"
        assert_equal(("test" in nd), True)
        assert_not_equal(("foo" in nd), True)


class TestNodeStatus(object):

    def test_init(self):
        s0 = NodeStatus()
        assert_equal(s0.status, NodeStatus.PENDING)
        assert_equal(s0.text, '')

        s1 = NodeStatus(NodeStatus.ACTIVE, 'testing init')
        assert_equal(s1.status, NodeStatus.ACTIVE)
        assert_equal(s1.text, 'testing init')

        s2 = NodeStatus(NodeStatus.SUCCESS)
        assert_equal(s2.status, NodeStatus.SUCCESS)
        assert_equal(s2.text, '')

    def test_str(self):
        s0 = NodeStatus(NodeStatus.PENDING, 'not started')
        assert_equal(str(s0), 'PENDING not started')

        s1 = NodeStatus(NodeStatus.ACTIVE, 'running')
        assert_equal(str(s1), 'ACTIVE running')

        s2 = NodeStatus(NodeStatus.SUCCESS, 'finished')
        assert_equal(str(s2), 'SUCCESS finished')

        s3 = NodeStatus(NodeStatus.FAIL, 'finished')
        assert_equal(str(s3), 'FAIL finished')

        s4 = NodeStatus(NodeStatus.CANCEL, 'canceled')
        assert_equal(str(s4), 'CANCEL canceled')

        s5 = NodeStatus(5, 'unknown')
        assert_equal(str(s5), '5 unknown')

    def test_eq(self):
        assert_equal(NodeStatus(NodeStatus.PENDING), NodeStatus.PENDING)
        assert_equal(NodeStatus(NodeStatus.ACTIVE), NodeStatus.ACTIVE)
        assert_equal(NodeStatus(NodeStatus.SUCCESS), NodeStatus.SUCCESS)
        assert_equal(NodeStatus(NodeStatus.FAIL), NodeStatus.FAIL)
        assert_equal(NodeStatus(NodeStatus.CANCEL), NodeStatus.CANCEL)

        assert_not_equal(NodeStatus(), NodeStatus(NodeStatus.ACTIVE))
        assert_not_equal(NodeStatus(NodeStatus.FAIL), NodeStatus.SUCCESS)


class TestBlackboard(object):

    def test_init(self):
        b = Blackboard()
        assert_equal(b._base_memory, {})
        assert_equal(b._node_memory, {})

    def test_base_memory(self):
        b = Blackboard()
        # test manually set memory
        b._base_memory["test"] = "hello world"
        assert_equal(b._get_memory(), {'test': 'hello world'})
        # test save
        b.save("foo", "bar")
        assert_equal(b._base_memory['foo'], 'bar')
        # test get
        assert_equal(b.get("foo"), 'bar')

    def test_node_memory(self):
        b = Blackboard()
        # test manually set memory
        b._node_memory["uuid"] = {}
        assert_equal(b._get_node_memory("uuid"), {})
        # test unknown uuid memory
        memory = b._get_node_memory("test_uuid")
        assert_equal(memory.keys(), ['node_data', 'remapping'])
        # test _get_node_memory
        memory['test_memory'] = 'test'
        memory = b._get_node_memory("test_uuid")
        assert_equal(memory['test_memory'], 'test')

    def test_memory(self):
        b = Blackboard()
        # test manually set memory
        node_memory = {'node_data': {'test_memory': 'test'}, 'remapping': {}}
        node_data = b._get_node_data(node_memory)
        assert_equal(node_data.keys(), ['test_memory'])
        # test non-existing memory
        assert_raises(KeyError, b.get, 'test', 'node_scope')
        # test save
        b.save('foo', 'bar', 'node_scope')
        value = b.get('foo', 'node_scope')
        assert_equal(value, 'bar')
        # test setting nodedata
        nd = b.get_memory('node_scope')
        nd.hello = "world"
        assert_equal(b.get('hello', 'node_scope'), 'world')

    def test_remapping(self):
        b = Blackboard()
        b.save('foo', 'bar', 'scope1')
        b.save('hello', 'world', 'scope2')
        b.add_remapping('scope1', 'foo', 'scope2', 'new_foo')
        scope1_nodedata = b.get_memory('scope2')
        assert_equal(scope1_nodedata['hello'], 'world')
        assert_equal(scope1_nodedata['new_foo'], 'bar')
        assert_equal(b.get('hello', 'scope2'), 'world')
        assert_equal(b.get('new_foo', 'scope2'), 'bar')
        # Test saving a value onto a remap gets over-written
        b.save('new_foo', 'test', 'scope2')
        assert_equal(b.get('foo', 'scope1'), 'bar')
        assert_equal(b.get('new_foo', 'scope2'), 'bar')
        # Test local changes get updated
        scope1_nodedata = b.get_memory('scope2')
        scope1_nodedata.new_foo = 'test'
        assert_equal(scope1_nodedata.new_foo, 'test')
        # Test updating a source remap, updates destination remap
        b.save('foo', 'new', 'scope1')
        assert_equal(b.get('foo', 'scope1'), 'new')
        assert_equal(b.get('new_foo', 'scope2'), 'new')
        # Test adding remapping to same value fails
        b.save('ping', 'pong', 'scope1')
        assert_raises(RuntimeError,
                      b.add_remapping, 'scope1', 'ping', 'scope2', 'new_foo')

    def test_node_status(self):
        b = Blackboard()
        assert_equal(b.get_node_status("blah"), NodeStatus.PENDING)

        b.set_node_status("scope1", NodeStatus.ACTIVE)
        assert_equal(b.get_node_status("scope1"), NodeStatus.ACTIVE)

        status = b.get_status()
        assert_equal(status["blah"], NodeStatus.PENDING)
        assert_equal(status['scope1'], NodeStatus.ACTIVE)

        b.clear_node_status()
        status = b.get_status()
        assert_equal(status, {})


class TestNode(object):

    def test_init(self):
        assert_raises(Exception, Node)
        n = Node('test')
        assert_equal(n._name, 'test')
        assert_equal(n._result, NodeStatus.PENDING)

    def test_blackboard(self):
        blackboard = Blackboard()
        n = Node('test', blackboard)
        assert_equal(n._blackboard, blackboard)

        n = Node('test')
        assert_not_equal(n._blackboard, blackboard)
        n.set_blackboard(blackboard)
        assert_equal(n._blackboard, blackboard)

    def test_configure(self):
        # test normal configure cb
        def configure_callback(nd):
            nd.cb_called = True
        n = Node('test', configure_cb=configure_callback)
        nd = n._blackboard.get_memory(n._id)
        assert_raises(KeyError, nd.__getitem__, 'cb_called')
        n._configure()
        assert_equal(nd.cb_called, True)
        assert_equal(n._result, NodeStatus.ACTIVE)
        # test no configure cb
        n = Node('test')
        nd = n._blackboard.get_memory(n._id)
        assert_raises(KeyError, nd.__getitem__, 'cb_called')
        n._configure()
        assert_raises(KeyError, nd.__getitem__, 'cb_called')
        assert_equal(n._result, NodeStatus.ACTIVE)
        # test register configure cb
        n = Node('test')
        n.register_configure_cb(configure_callback)
        nd = n._blackboard.get_memory(n._id)
        assert_raises(KeyError, nd.__getitem__, 'cb_called')
        n._configure()
        assert_equal(nd.cb_called, True)
        assert_equal(n._result, NodeStatus.ACTIVE)

    def test_cleanup(self):
        # test normal cleanup
        def cleanup_callback(nd):
            nd.cb_called = True
        n = Node('test', cleanup_cb=cleanup_callback)
        nd = n._blackboard.get_memory(n._id)
        assert_raises(KeyError, nd.__getitem__, 'cb_called')
        n._cleanup()
        assert_equal(nd.cb_called, True)
        assert_equal(n._result, NodeStatus.PENDING)
        # test no exit
        n = Node('test')
        nd = n._blackboard.get_memory(n._id)
        assert_raises(KeyError, nd.__getitem__, 'cb_called')
        n._cleanup()
        assert_raises(KeyError, nd.__getitem__, 'cb_called')
        assert_equal(n._result, NodeStatus.PENDING)
        # test register
        n = Node('test')
        nd = n._blackboard.get_memory(n._id)
        n.register_cleanup_cb(cleanup_callback)
        assert_raises(KeyError, nd.__getitem__, 'cb_called')
        n._cleanup()
        assert_equal(nd.cb_called, True)
        assert_equal(n._result, NodeStatus.PENDING)

    def test_run(self):
        # test normal evaluate
        def run_callback(nd):
            nd.cb_called = True
            return NodeStatus(NodeStatus.SUCCESS, 'complete')
        n = Node('test', run_cb=run_callback)
        nd = n._blackboard.get_memory(n._id)
        assert_raises(KeyError, nd.__getitem__, 'cb_called')
        r = n._run()
        assert_equal(nd.cb_called, True)
        assert_equal(r, NodeStatus.SUCCESS)
        # test no evaluate
        n = Node('test')
        nd = n._blackboard.get_memory(n._id)
        nd.cb_called = False
        assert_raises(NotImplementedError, n._run)
        # test register
        n = Node('test')
        nd = n._blackboard.get_memory(n._id)
        assert_raises(KeyError, nd.__getitem__, 'cb_called')
        n.register_run_cb(run_callback)
        assert_raises(KeyError, nd.__getitem__, 'cb_called')
        n._run()
        assert_equal(nd.cb_called, True)

        def wrong_callback(nd):
            nd.cb_called = True
            return ""

        n = Node('test')
        nd = n._blackboard.get_memory(n._id)
        n.register_run_cb(wrong_callback)
        assert_raises(KeyError, nd.__getitem__, 'cb_called')
        assert_raises(Exception, n._run)
        assert_equal(nd.cb_called, True)

    def test_cancel(self):
        # test normal cancel
        def cancel_callback(nd):
            nd.cb_called = True
        n = Node('test', cancel_cb=cancel_callback)
        nd = n._blackboard.get_memory(n._id)
        assert_raises(KeyError, nd.__getitem__, 'cb_called')
        n._cancel()
        assert_equal(nd.cb_called, True)
        # test no cancel callback
        n = Node('test')
        nd = n._blackboard.get_memory(n._id)
        assert_raises(KeyError, nd.__getitem__, 'cb_called')
        n._cancel()
        assert_raises(KeyError, nd.__getitem__, 'cb_called')
        # test register
        n = Node('test')
        nd = n._blackboard.get_memory(n._id)
        n.register_cancel_cb(cancel_callback)
        assert_raises(KeyError, nd.__getitem__, 'cb_called')
        n._cancel()
        assert_equal(nd.cb_called, True)

    def test_force(self):
        # test force
        def run_callback(nd):
            nd.cb_called = True
            return NodeStatus(NodeStatus.SUCCESS, 'complete')
        n = Node('test', run_cb=run_callback)
        nd = n._blackboard.get_memory(n._id)
        assert_raises(KeyError, nd.__getitem__, 'cb_called')
        r = n._run()
        assert_equal(r, NodeStatus.SUCCESS)
        assert_equal(nd.cb_called, True)
        n = Node('test', run_cb=run_callback)
        nd = n._blackboard.get_memory(n._id)
        assert_raises(KeyError, nd.__getitem__, 'cb_called')
        n.force(NodeStatus.FAIL)
        r = n._run()
        assert_equal(r, NodeStatus.FAIL)
        assert_raises(KeyError, nd.__getitem__, 'cb_called')
        n._cleanup()
        n._configure()
        r = n._run()
        assert_equal(r, NodeStatus.SUCCESS)
        assert_equal(nd.cb_called, True)

    def test_result(self):

        def run_callback(nd):
            nd.cb_called = True
            return NodeStatus(NodeStatus.SUCCESS, 'complete')
        n = Node('test', run_cb=run_callback)
        nd = n._blackboard.get_memory(n._id)
        assert_equal(n.get_result(), NodeStatus.PENDING)
        assert_raises(KeyError, nd.__getitem__, 'cb_called')
        n._configure()
        assert_equal(n.get_result(), NodeStatus.ACTIVE)
        assert_raises(KeyError, nd.__getitem__, 'cb_called')
        n._run()
        assert_equal(n.get_result(), NodeStatus.SUCCESS)
        assert_equal(nd.cb_called, True)
        n._cleanup()
        assert_equal(n.get_result(), NodeStatus.PENDING)
        assert_equal(nd.cb_called, True)

    def test_tick(self):
        def config_callback(nd):
            nd.config_called += 1

        def run_callback(nd):
            nd.run_called += 1
            return NodeStatus(NodeStatus.ACTIVE, 'running')

        def cancel_callback(nd):
            nd.cancel_called += 1

        n = Node('test', run_cb=run_callback,
                 configure_cb=config_callback, cancel_cb=cancel_callback)
        nd = n._blackboard.get_memory(n._id)
        nd.config_called = 0
        nd.run_called = 0
        nd.cancel_called = 0

        assert_equal(n.get_result().status, NodeStatus.PENDING)
        assert_equal(nd.config_called, 0)
        assert_equal(nd.run_called, 0)
        assert_equal(nd.cancel_called, 0)

        result = n.tick()
        assert_equal(n.get_result().status, NodeStatus.ACTIVE)
        assert_equal(result.status, NodeStatus.ACTIVE)
        assert_equal(nd.config_called, 1)
        assert_equal(nd.run_called, 1)
        assert_equal(nd.cancel_called, 0)

        result = n.tick()
        assert_equal(n.get_result().status, NodeStatus.ACTIVE)
        assert_equal(result.status, NodeStatus.ACTIVE)
        assert_equal(nd.config_called, 1)
        assert_equal(nd.run_called, 2)
        assert_equal(nd.cancel_called, 0)

        n.cancel()
        assert_equal(n.get_result().status, NodeStatus.CANCEL)
        assert_equal(nd.config_called, 1)
        assert_equal(nd.run_called, 2)
        assert_equal(nd.cancel_called, 1)

        result = n.tick()
        assert_equal(n.get_result().status, NodeStatus.PENDING)
        assert_equal(result.status, NodeStatus.CANCEL)
        assert_equal(nd.config_called, 1)
        assert_equal(nd.run_called, 2)
        assert_equal(nd.cancel_called, 1)


class TestDecorator(object):

    def test_init(self):
        def run_callback(nd):
            nd.cb_called = True
            return NodeStatus(NodeStatus.SUCCESS, 'complete')
        n = Node('test', run_cb=run_callback)
        d = Decorator('d_test', n)
        assert_equal(d._child, n)

    def test_configure(self):
        n1 = Node('node1')

        def success_cb(nd):
            nd.called += "run "
            return NodeStatus(NodeStatus.SUCCESS)

        def config_cb(nd):
            nd.called = nd.get_data("called", "")
            nd.called += "config "

        def cleanup_cb(nd):
            nd.called += "cleanup "

        n1.register_configure_cb(config_cb)
        n1.register_run_cb(success_cb)
        n1.register_cleanup_cb(cleanup_cb)

        d = Decorator('d_test', n1)
        d._configure()
        assert_equal(d.get_result(), NodeStatus.ACTIVE)
        assert_equal(d._child.get_result(), NodeStatus.ACTIVE)
        nd = n1._blackboard.get_memory(n1._id)
        assert_equal(nd.called, "config ")

    def test_cleanup(self):
        n1 = Node('node1')

        def success_cb(nd):
            nd.called += "run "
            return NodeStatus(NodeStatus.SUCCESS)

        def config_cb(nd):
            nd.called = nd.get_data("called", "")
            nd.called += "config "

        def cleanup_cb(nd):
            nd.called = nd.get_data("called", "")
            nd.called += "cleanup "

        n1.register_configure_cb(config_cb)
        n1.register_run_cb(success_cb)
        n1.register_cleanup_cb(cleanup_cb)

        d = Decorator('d_test', n1)
        d._cleanup()
        assert_equal(d.get_result(), NodeStatus.PENDING)
        assert_equal(d._child.get_result(), NodeStatus.PENDING)
        nd = n1._blackboard.get_memory(n1._id)
        assert_equal(nd.called, "cleanup ")

    def test_cancel(self):
        n1 = Node('node1')

        def success_cb(nd):
            nd.called += "run "
            return NodeStatus(NodeStatus.SUCCESS)

        def config_cb(nd):
            nd.called = nd.get_data("called", "")
            nd.called += "config "

        def cleanup_cb(nd):
            nd.called += "cleanup "

        n1.register_configure_cb(config_cb)
        n1.register_run_cb(success_cb)
        n1.register_cleanup_cb(cleanup_cb)

        d = Decorator('d_test', n1)
        d._cancel()
        assert_equal(d.get_result(), NodeStatus.CANCEL)
        assert_equal(d._child.get_result(), NodeStatus.CANCEL)


class TestBehavior(object):

    def test_init(self):
        b = Behavior('test')
        assert_equal(b._children, [])

    def test_children(self):
        b = Behavior('test')
        n1 = Node('node1')
        n2 = Node('node2')
        # Test adding children
        b.add_child(n1)
        assert_equal(b._children, [n1])
        b.add_child(n2)
        assert_equal(b._children, [n1, n2])
        # Test removing children
        b.remove_child(n2)
        assert_equal(b._children, [n1])
        # Test prepending child
        b.prepend_child(n2)
        assert_equal(b._children, [n2, n1])
        # Test inserting child
        n3 = Node('node3')
        b.insert_child(n3, 1)
        assert_equal(b._children, [n2, n3, n1])
        # Test insertring child with same name raises
        n4 = Node('node1')
        assert_raises(RuntimeError,
                      b.add_child, n4)

    def test_blackboard(self):
        blackboard = Blackboard()
        b = Behavior(name='test', blackboard=blackboard)
        assert_equal(b._blackboard, blackboard)

        b = Behavior(name='test')
        assert_not_equal(b._blackboard, blackboard)
        b.set_blackboard(blackboard)
        assert_equal(b._blackboard, blackboard)

    def test_tick_child(self):
        blackboard = Blackboard()
        n1 = Node(name='node1', blackboard=blackboard)

        def success_cb(nd):
            nd.called += "run "
            return NodeStatus(NodeStatus.SUCCESS)

        def config_cb(nd):
            nd.called = nd.get_data("called", "")
            nd.called += "config "

        def cleanup_cb(nd):
            nd.called += "cleanup "

        n1.register_configure_cb(config_cb)
        n1.register_run_cb(success_cb)
        n1.register_cleanup_cb(cleanup_cb)

        b = Behavior(name='test', blackboard=blackboard)
        b.add_child(n1)
        r = b.tick_child(n1)
        assert_equal(r, NodeStatus.SUCCESS)
        steps = b._blackboard.get('called', n1._id)
        assert_equal(steps, "config run cleanup ")

    def test_cancel(self):
        blackboard = Blackboard()
        n1 = Node(name='node1', blackboard=blackboard)

        def continue_cb(nd):
            nd.called += "run "
            return NodeStatus(NodeStatus.ACTIVE)

        def config_cb(nd):
            nd.called = nd.get_data("called", "")
            nd.called += "config "

        def cleanup_cb(nd):
            nd.called += "cleanup "

        def cancel_cb(nd):
            nd.called += "cancel "

        n1.register_configure_cb(config_cb)
        n1.register_run_cb(continue_cb)
        n1.register_cleanup_cb(cleanup_cb)
        n1.register_cancel_cb(cancel_cb)

        b = Behavior(name='test', blackboard=blackboard)
        b.add_child(n1)
        r = b.tick_child(n1)
        assert_equal(r, NodeStatus.ACTIVE)
        b._cancel()
        r = b.tick_child(n1)
        assert_equal(r, NodeStatus.CANCEL)
        steps = b._blackboard.get('called', n1._id)
        assert_equal(steps, "config run cancel cleanup ")

    def test_cleanup(self):
        blackboard = Blackboard()
        n1 = Node(name='node1', blackboard=blackboard)
        n2 = Node(name='node2', blackboard=blackboard)

        def success_cb(nd):
            nd.called += "success "
            return NodeStatus(NodeStatus.SUCCESS)

        def continue_cb(nd):
            nd.called += "run "
            return NodeStatus(NodeStatus.ACTIVE)

        def config_cb(nd):
            nd.called = nd.get_data("called", "")
            nd.called += "config "

        def cleanup_cb(nd):
            nd.called += "cleanup "

        def cancel_cb(nd):
            nd.called += "cancel "

        n1.register_configure_cb(config_cb)
        n1.register_run_cb(continue_cb)
        n1.register_cleanup_cb(cleanup_cb)
        n1.register_cancel_cb(cancel_cb)

        n2.register_configure_cb(config_cb)
        n2.register_run_cb(success_cb)
        n2.register_cleanup_cb(cleanup_cb)
        n2.register_cancel_cb(cancel_cb)

        b = Behavior(name='test', blackboard=blackboard)
        b.add_child(n1)
        b.add_child(n2)

        b._configure()
        r = b.tick_child(n1)
        assert_equal(r, NodeStatus.ACTIVE)
        r = b.tick_child(n2)
        assert_equal(r, NodeStatus.SUCCESS)

        assert_equal(n1.get_result().status, NodeStatus.ACTIVE)
        assert_equal(n2.get_result().status, NodeStatus.PENDING)
        assert_equal(b.get_result().status, NodeStatus.ACTIVE)

        b._cleanup()

        assert_equal(n1.get_result().status, NodeStatus.PENDING)
        assert_equal(n2.get_result().status, NodeStatus.PENDING)
        assert_equal(b.get_result().status, NodeStatus.PENDING)

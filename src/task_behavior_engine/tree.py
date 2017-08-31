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


import logging
import threading
import uuid

logger = logging.getLogger(__name__)


class NodeData(object):

    """ This object is a dictionary that holds all of the data for a node.
        You can access the members by standard dictionary calls (nodedata[name])
        or via attribute (nodedata.name)
    """

    def __init__(self):
        self._data = {}
        self._locks = {}

    def __contains__(self, key):
        return key in self._data.keys()

    def __getattr__(self, name):
        """ Override getattr to be thread safe. """
        if name[0] == '_':
            return object.__getattr__(self, name)
        if not name in self._locks.keys():
            self._locks[name] = threading.Lock()

        with self._locks[name]:
            temp = self._data[name]

        return temp

    def __setattr__(self, name, value):
        """ Override setattr to be thread safe. """
        if name[0] == '_':
            return object.__setattr__(self, name, value)

        if not name in self._locks.keys():
            self._locks[name] = threading.Lock()

        self._locks[name].acquire()
        self._data[name] = value
        self._locks[name].release()

    def __getitem__(self, key):
        return self.__getattr__(key)

    def __setitem__(self, key, item):
        self._data[key] = item

    def __str__(self):
        return str(self._data)

    def keys(self):
        """ Gets all of the keys
            @returns List A list of all of the keys
        """
        return list(self._data.keys())

    def get_data(self, key, default=None):
        """ Gets data from key.  If key does not exist, returns default value.
            @param key [string] The data key
            @param default (None) The default value
            @throws KeyError if key not found and default not set
        """
        if not key in self._data.keys():
            self._data[key] = default
        return self._data[key]

    def set_data(self, key, value):
        """ Sets data.
            @param key [string] The data key
            @param value [*] The data value
        """
        self._data[key] = value


class NodeStatus(object):

    """ A class for enumerating behavior status
        Available statuses:
            PENDING: Node hasn't is in pre-run state
            ACTIVE: Node is currently executing
            SUCCESS: Node has completed successfully
            FAIL: Node has completed with errors
            CANCEL: Node has been canceled
    """

    PENDING = 0
    ACTIVE = 1
    SUCCESS = 2
    FAIL = 3
    CANCEL = 4

    def __init__(self, status=PENDING, text=""):
        self.status = status
        self.text = text

    def _get_status_str(self):
        """ Gets the string of the current status enum"""
        status_str = {
            self.PENDING: "PENDING",
            self.ACTIVE: "ACTIVE",
            self.SUCCESS: "SUCCESS",
            self.FAIL: "FAIL",
            self.CANCEL: "CANCEL"
        }
        if self.status in status_str:
            return status_str[self.status]
        return str(self.status)

    def __str__(self):
        return str(self._get_status_str() + " " + self.text)

    def __eq__(self, other):
        return self.status == other

    def merge(self, status, text):
        """ Merges a NodeStatus together.
            If the merged status has a greater value than the current status,
            the merged status is used.
            If the merged status is the same or equal, the text is concatenated.
        """
        if status > self.status:
            self.status = status
            self.text = text

        if status == self.status:
            self.text = self.text + "; " + text


class Blackboard(object):

    """ A class to contain all (or related) nodedatas.  This class allows for
        specific node data parameters to be shared amoung nodes.
    """

    def __init__(self):
        self._base_memory = {}
        self._node_memory = {}
        self._node_status = {}

    def _get_node_memory(self, scope):
        """ Gets node memory
            If memory doesn't exist it will be assigned a default value.
            @param scope [uuid] The id of the node.
            @returns [dict] The memory.
        """
        if not scope in self._node_memory:
            self._node_memory[scope] = {'node_data': NodeData(),
                                        'remapping': {}}
        return self._node_memory[scope]

    def _get_node_data(self, node_memory):
        """ Gets node data with any remappings.
            If node data doesn't exist it will create an empty NodeData object.
            @param node_memory [dict] The memory of the node.
            @returns [NodeData] The node specific memory.
        """
        if not 'node_data' in node_memory:
            node_memory['node_data'] = NodeData()
        memory = node_memory['node_data']
        logger.debug("node_data: " + str(memory))
        remapping = node_memory['remapping']
        logger.debug("remapping: " + str(remapping))

        for key in remapping:
            (from_scope, from_key) = remapping[key]
            try:
                value = self.get(from_key, from_scope)
                memory[key] = value
            except:
                pass

        return memory

    def _get_memory(self, scope=None):
        """ Gets memory.
            If scope is none, it returns global memory
            else it returns node memory.
            @param scope [uuid] The uuid of the memory.
            @returns [dict] The memory.
        """
        memory = self._base_memory
        logger.debug("base_memory: " + str(memory))

        if(scope):
            memory = self._get_node_memory(scope)
            memory = self._get_node_data(memory)
            logger.debug(str(scope) + ".node_data: " + str(memory))

        return memory

    def save(self, key, value, scope=None):
        """ Saves a (key, value) pair onto tree_scope/node_scope.
            @param key [string] the key of the item.
            @param value [*] The value of the item.
            @param scope [uuid] (optional) The uuid of the tree.
        """
        memory = self._get_memory(scope)
        memory[key] = value

    def get(self, key, scope=None):
        """ Gets a (key, value) pair from tree_scope/node_scope.
            @param key [string] The key to retrieve.
            @param scope [uuid] (optional) The uuid of the tree.
            @returns The value of the key in the tree_scope/node_scope.
        """
        memory = self._get_memory(scope)
        return memory[key]

    def add_remapping(self, from_scope, from_key, to_scope, to_key):
        """ Add a remapping from one node->key to another node->key.
            @param from_scope [uuid] The id of the source node.
            @param from_key [string] The key of the source node.
            @param to_scope [uuid] The id of the destination node.
            @param to_key [string] The key of the destination node.
        """
        memory = self._get_node_memory(to_scope)
        remap = memory['remapping']
        if to_key in remap:
            raise RuntimeError("Can not map to same key twice")
        remap[to_key] = (from_scope, from_key)

    def get_memory(self, scope):
        """ Gets current nodedata with any remappings.
            @param scope [uuid] The id of the scope/node.
        """
        return self._get_memory(scope)

    def get_status(self):
        """ Gets all of the node status.
        """
        return self._node_status

    def get_node_status(self, scope):
        """ Gets the status of a specific node.
            @param scope [uuid] The id of the node to get.
            @returns [NodeStatus] The status of the node.
        """
        if not scope in self._node_status:
            self._node_status[scope] = NodeStatus()
        return self._node_status[scope]

    def set_node_status(self, scope, status):
        """ Sets the status of a specific node
            @param scope [uuid] The id of the node to set
            @param status [NodeStatus] The status to set the node
        """
        self._node_status[scope] = status

    def clear_node_status(self):
        """ Clears the node_status currently saved.
            This is mostly used for display purposes.
        """
        self._node_status = {}


class Node(object):

    """ Base class for nodes.
        This class defines the standard callbacks and data structures for Nodes.

        Callbacks follow a set state machine on each tick()

        PENDING -> configure() -> ACTIVE <-> run() -> CANCEL -> cancel()
                                               |                   |
                                               -> SUCCESS/FAIL - ---> cleanup()

        The data structure is provided by a Blackboard.  By default, each node
        creates its own Blackboard, however you may set the blackboard to a
        specific one as well so that nodes may share their data.
    """

    def __init__(self, name, blackboard=Blackboard(), run_cb=None,
                 configure_cb=None, cleanup_cb=None, cancel_cb=None,
                 *args, **kwargs):
        """ Node constructor.
            @param name [string] The name of this node.
            @param blackboard [Blackboard] The common nodedata container.
            @param run_cb [function] The function to call on run.
            @param config_cb [function] The function to call on enter.
            @param cleanup_cb [function] The function to call on exit.
            @param cancel_cb [function] The function to call when canceled.
        """
        self._id = uuid.uuid4()
        self._name = name
        self._force_state = None
        self._run_cb = run_cb
        self._configure_cb = configure_cb
        self._cleanup_cb = cleanup_cb
        self._cancel_cb = cancel_cb
        self._result = NodeStatus()
        self._blackboard = blackboard

    def _configure(self):
        """ Configuration performed once before run().
            This is usually used to set up internal variables.
        """
        logger.debug(
            self._name + "._configure() entering... " + str(self._result))
        if self._configure_cb:
            nodedata = self._blackboard.get_memory(self._id)
            self._configure_cb(nodedata)
        self._result = NodeStatus(
            NodeStatus.ACTIVE, "Configured " + self._name)
        logger.debug(
            self._name + "._configure() exiting.. " + str(self._result))

    def _cleanup(self):
        """ Cleanup performed once after run() returns a termination value.
            This is usually used to reset internal variables.
        """
        logger.debug(
            self._name + "._cleanup() entering... " + str(self._result))
        if self._result == NodeStatus.ACTIVE:
            self._cancel()
        if self._cleanup_cb:
            nodedata = self._blackboard.get_memory(self._id)
            self._cleanup_cb(nodedata)
        self._force_state = None
        self._result = NodeStatus(
            NodeStatus.PENDING, "Cleaned up " + self._name)
        logger.debug(self._name + "._cleanup() exiting.. " + str(self._result))

    def _run(self):
        """ Evaluates the current node.
            @returns [NodeStatus] Outcome status.
        """
        logger.info(self._name + "._run() entering... " + str(self._result))
        if self._force_state:
            self._result = self._force_state
        elif self._run_cb:
            nodedata = self._blackboard.get_memory(self._id)
            self._result = self._run_cb(nodedata)
        else:
            raise NotImplementedError('run_cb must be defined.')
        if not type(self._result) == NodeStatus:
            raise NotImplementedError(
                'Result of run_cb must be a task_behavior_engine.tree.NodeStatus type')
        logger.info(self._name + "._run() exiting.. " + str(self._result))
        self._blackboard.set_node_status(self._id, self._result)
        logger.info(self._name + " ::SET_NODE_STATUS:: " + str(self._result))
        return self._result

    def _cancel(self):
        """ Forces the current state to CANCEL
            and calls the cancel callback, if it exists.
        """
        logger.debug(
            self._name + "._cancel() entering... " + str(self._result))
        self._force_state = NodeStatus(
            NodeStatus.CANCEL, "Canceling " + self._name)
        nodedata = self._blackboard.get_memory(self._id)
        if self._cancel_cb:
            self._cancel_cb(nodedata)
        self._run()
        logger.debug(self._name + "._cancel() exiting.. " + str(self._result))

    def cancel(self, *args, **kwargs):
        """ By default a behavior should just call its internal
            cancel when requested.
        """
        self._cancel()

    def force(self, status):
        """ Forces an execution state.
            @param status [int] forced outcome state (must be NodeStatus enum).
        """
        logger.debug(
            self._name + ".force() entering... " + str(self._force_state))
        self._force_state = NodeStatus(status)
        self._force_state.text = "Forcing " + self._name + \
            " to " + self._force_state._get_status_str()
        logger.debug(
            self._name + ".force() exiting.. " + str(self._force_state))

    def get_nodedata(self):
        """ Return the NodeData of this behavior
            @returns [NodeData] The current NodeData
        """
        return self._blackboard.get_memory(self._id)

    def set_nodedata(self, key, value):
        """ Set a NodeData value for this behavior
        @param key [str] The name of the parameter
        @param value The value of the parameter
        """
        self._blackboard.save(key, value, self._id)

    def get_result(self):
        """ Return the result of this behavior.
            @returns [NodeStatus] The current result status.
        """
        return self._result

    def get_status(self):
        """ Get the status of this node.
            @returns [NodeStatus] The last completion status of the node.
        """
        return self._blackboard.get_node_status(self._id)

    def register_run_cb(self, cb):
        """ Register the run_cb.
            This will get called when ticked.
            @param cb [function] The function to call on run.
        """
        self._run_cb = cb

    def register_configure_cb(self, cb):
        """ Register the configure_cb.
            This will get called on configure.
            @param cb [function] The function to call on configure.
        """
        self._configure_cb = cb

    def register_cleanup_cb(self, cb):
        """ Register the cleanup callback.
            This will get called on cleanup.
            @param cb [function] The function to call on cleanup.
        """
        self._cleanup_cb = cb

    def register_cancel_cb(self, cb):
        """ Register the cancel callback.
            This will get called if task is canceled.
            @param cb [function] The function to call on cancel.
        """
        self._cancel_cb = cb

    def set_blackboard(self, blackboard):
        """Set the blackboard for this node.
        @param blackboard [Blackboard] The blackboard to assign to this node.
        """
        self._blackboard = blackboard

    def tick(self, *args, **kwargs):
        """Runs the node
        """
        logger.debug(self._name + ".tick() entering... " + str(self._result))
        if self._result == NodeStatus.PENDING:
            self._configure()
        result = self._run()
        logger.debug(self._name + ".tick() result: " + str(result))
        if not (self._result == NodeStatus.ACTIVE or self._result == NodeStatus.PENDING):
            self._cleanup()
        logger.debug(self._name + ".tick() exiting.. " + str(self._result))
        return result


class Decorator(Node):

    """ Decorators are nodes that contain one child.  Their purpose is to modify
        the output of the child node in order to fit into the task logic structure.
    """

    def __init__(self, name, child=None, *args, **kwargs):
        super(Decorator, self).__init__(name=name, *args, **kwargs)
        self._child = child

    def _configure(self):
        """ Configure the child node if this node is configured.
        """
        logger.debug(
            self._name + "._configure() entering... " + str(self._result))
        if self._child:
            self._child._configure()
        super(Decorator, self)._configure()
        logger.debug(
            self._name + "._configure() exiting.. " + str(self._result))

    def _cleanup(self):
        """ Cleanup the child node if this node is cleaned up.
        """
        logger.debug(
            self._name + "._cleanup() entering... " + str(self._result))
        if self._child:
            self._child._cleanup()
        super(Decorator, self)._cleanup()
        logger.debug(self._name + "._cleanup() exiting.. " + str(self._result))

    def _cancel(self):
        """ Cancel the child node if this node is canceled.
        """
        logger.debug(
            self._name + "._cancel() entering... " + str(self._result))
        if self._child:
            self._child._cancel()
        super(Decorator, self)._cancel()
        logger.debug(self._name + "._cancel() exiting.. " + str(self._result))

    def set_child(self, child):
        """ Assign the child node.  This can also be done at the constructor.
            @param child [Node] The child to add to this decorator
        """
        self._child = child

    def tick_child(self):
        """ Run the child node.
            If no child defined, return default status (PENDING)
        """
        if self._child:
            return self._child.tick()
        else:
            return NodeStatus()


class Behavior(Node):

    """ Behaviors are nodes that contain children.
    """

    def __init__(self, name, *args, **kwargs):
        super(Behavior, self).__init__(name=name, *args, **kwargs)

        self._children = []
        self._open_nodes = []

    def check_unique_child(self, name):
        return not name in [child._name for child in self._children]

    def add_child(self, node):
        """Add a node to the end behavior tree.
        @param node [Node] The node to add.
        @throws RuntimeError if the node name is not unique to this behavior.
        """
        if self.check_unique_child(node._name):
            self._children.append(node)
        else:
            raise RuntimeError(
                "Could not add node %s to %s. Name is not unique." % (node._name, self._name))

    def remove_child(self, node):
        """Remove a node from the behavior tree.
        @param node [Node] The node to remove.
        @throws ValueError if node not child of behavior.
        """
        self._children.remove(node)

    def prepend_child(self, node):
        """Add a node to the beginning of the behavior tree.
        @param node [Node] The node to prepend.
        """
        self._children.insert(0, node)

    def insert_child(self, node, i):
        """Insert node into position i of the behavior tree.
        @param node [Node] The node to add.
        @param i [int] The position of insertion.
        """
        self._children.insert(i, node)

    def tick_child(self, child):
        """Run a child node
        @param child [Node] The child to run
        """
        logger.info(child._name + ".tick_child()")
        result = child.tick()
        if result == NodeStatus.ACTIVE:
            if child._id not in self._open_nodes:
                logger.info("Adding child " + child._name + " to open_nodes")
                self._open_nodes.append(child._id)
        if child.get_result() == NodeStatus.PENDING:
            if child._id in self._open_nodes:
                logger.info(
                    "Removing child " + child._name + " from open_nodes")
                self._open_nodes.remove(child._id)
        return result

    def cancel_children(self):
        """ Cancel all children currently running
        """
        for child in self._children:
            self.cancel_child(child)

    def _cancel(self):
        """ If a behavior is canceled, cancel all running children.
        """
        self.cancel_children()
        super(Behavior, self)._cancel()

    def cleanup_children(self):
        """ Cleanup all active children
        """
        for child in self._children:
            if not child.get_result() == NodeStatus.PENDING:
                logger.info("Cleaning up child " + child._name)
                child._cleanup()
                if child._id in self._open_nodes:
                    logger.info(
                        "Removing child " + child._name + " from open_nodes")
                    self._open_nodes.remove(child._id)

    def _cleanup(self):
        """ If a behavior finishes, cancel all running children.
        """
        self.cancel_children()
        self.cleanup_children()
        super(Behavior, self)._cleanup()

    def reset_children_status(self):
        """ Reset the current node status for all children
        """
        for child in self._children:
            child._blackboard.set_node_status(child._id, NodeStatus())

    def cancel_child(self, child):
        """ Cancel a particular child.
            @param child [Node] The child to cancel
        """
        if not child.get_result() == NodeStatus.PENDING:
            logger.info("Canceling child " + child._name)
            child._cancel()

"""
Race Condition Detection

Based on: Race Condition Detection and Expression, US Patent US7017129B2 (Ouyang, 2006).

Implements static graph-based analysis for:
- Write–write races
- Read–write races  
- Trigger races
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from itertools import combinations
from collections import deque


# =============================================================================
# Node Identifier
# =============================================================================

NodeId = str


# =============================================================================
# Enums
# =============================================================================

class AssignmentKind(Enum):
    """Assignment kind: blocking (=), non-blocking (<=), or continuous."""
    BLOCKING = auto()
    NONBLOCKING = auto()
    CONTINUOUS = auto()


class RaceType(Enum):
    """Race condition kind detected."""
    WRITE_WRITE = auto()
    READ_WRITE = auto()
    TRIGGER = auto()


# =============================================================================
# IR Classes (Input Representation)
# =============================================================================

@dataclass
class IRSignal:
    """Intermediate representation of a signal."""
    name: str
    kind: str
    is_register: bool = False


@dataclass
class IRAssignment:
    """Intermediate representation of an assignment."""
    src_signals: list
    dst_signal: str
    kind: str
    condition_expr: object = None
    src_location: str = ""


@dataclass
class IRProcess:
    """Intermediate representation of a process."""
    name: str
    triggers: list
    trigger_kinds: list
    assignments: list
    src_location: str = ""


@dataclass
class IRDesign:
    """Intermediate representation of a design."""
    signals: list
    processes: list


# =============================================================================
# Graph Data Structures
# =============================================================================

@dataclass
class DataNode:
    """Represents a signal in the design graph."""
    id: NodeId
    name: str
    is_storage: bool = False
    writers: set = field(default_factory=set)
    readers: set = field(default_factory=set)


@dataclass
class ComputeNode:
    """Represents a process in the design graph."""
    id: NodeId
    name: str
    assignments: list = field(default_factory=list)
    triggers: list = field(default_factory=list)
    trigger_kinds: list = field(default_factory=list)
    src_location: str = ""


@dataclass
class Edge:
    """Edge in the design graph."""
    src: NodeId
    dst: NodeId
    kind: str
    assignment_kind: object = None
    condition_expr: object = None


@dataclass
class DesignGraph:
    """Complete design graph with data and compute nodes."""
    data_nodes: dict = field(default_factory=dict)
    compute_nodes: dict = field(default_factory=dict)
    edges_out: dict = field(default_factory=dict)
    edges_in: dict = field(default_factory=dict)

    def add_edge(self, edge):
        """Add an edge to both outgoing and incoming edge lists."""
        if edge.src not in self.edges_out:
            self.edges_out[edge.src] = []
        if edge.dst not in self.edges_in:
            self.edges_in[edge.dst] = []
        self.edges_out[edge.src].append(edge)
        self.edges_in[edge.dst].append(edge)


# =============================================================================
# Race Representation
# =============================================================================

@dataclass
class RacePath:
    """Represents a path in a race condition."""
    nodes: list
    edges: list
    conditions: list
    nb_steps: int
    start_id: NodeId
    end_id: NodeId


@dataclass
class RaceGraph:
    """Complete race condition with two paths."""
    race_type: RaceType
    source_id: NodeId
    target_id: NodeId
    anchor1_id: NodeId
    anchor2_id: NodeId
    path1: RacePath
    path2: RacePath


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class DetectionConfig:
    """Configuration for race detection."""
    require_storage_for_trigger_target: bool = True
    use_nonblocking_steps_filter: bool = True


# =============================================================================
# Helper Functions
# =============================================================================

def _parse_assignment_kind(kind_str):
    """Parse assignment kind string to enum."""
    kind_lower = kind_str.lower()
    if kind_lower == "blocking":
        return AssignmentKind.BLOCKING
    elif kind_lower == "nonblocking":
        return AssignmentKind.NONBLOCKING
    elif kind_lower == "continuous":
        return AssignmentKind.CONTINUOUS
    return AssignmentKind.BLOCKING


# =============================================================================
# Graph Building
# =============================================================================

def build_design_graph(ir_design):
    """Build a design graph from intermediate representation."""
    graph = DesignGraph()

    # Create data nodes for all signals
    for sig in ir_design.signals:
        node_id = f"d_{sig.name}"
        graph.data_nodes[node_id] = DataNode(
            id=node_id,
            name=sig.name,
            is_storage=sig.is_register,
        )

    # Create compute nodes for all processes
    for proc in ir_design.processes:
        node_id = f"c_{proc.name}"
        compute_node = ComputeNode(
            id=node_id,
            name=proc.name,
            assignments=proc.assignments,
            trigger_kinds=proc.trigger_kinds,
            src_location=proc.src_location,
        )
        graph.compute_nodes[node_id] = compute_node

        # Add trigger edges
        for trig_name, trig_kind in zip(proc.triggers, proc.trigger_kinds):
            data_id = f"d_{trig_name}"
            if data_id not in graph.data_nodes:
                graph.data_nodes[data_id] = DataNode(
                    id=data_id,
                    name=trig_name,
                    is_storage=False,
                )
            compute_node.triggers.append(data_id)
            graph.data_nodes[data_id].readers.add(node_id)
            edge = Edge(src=data_id, dst=node_id, kind="trigger")
            graph.add_edge(edge)

        # Add read/write edges for assignments
        for assign in proc.assignments:
            dst_id = f"d_{assign.dst_signal}"
            if dst_id not in graph.data_nodes:
                graph.data_nodes[dst_id] = DataNode(
                    id=dst_id,
                    name=assign.dst_signal,
                    is_storage=False,
                )
            
            graph.data_nodes[dst_id].writers.add(node_id)
            assign_kind = _parse_assignment_kind(assign.kind)
            edge = Edge(
                src=node_id,
                dst=dst_id,
                kind="write",
                assignment_kind=assign_kind,
                condition_expr=assign.condition_expr,
            )
            graph.add_edge(edge)

            # Read edges for source signals
            for src_sig in assign.src_signals:
                src_id = f"d_{src_sig}"
                if src_id not in graph.data_nodes:
                    graph.data_nodes[src_id] = DataNode(
                        id=src_id,
                        name=src_sig,
                        is_storage=False,
                    )
                
                graph.data_nodes[src_id].readers.add(node_id)
                edge = Edge(src=src_id, dst=node_id, kind="read")
                graph.add_edge(edge)

    return graph


# =============================================================================
# Race Detection - Core Algorithms
# =============================================================================

def detect_write_write_races(graph, config=None):
    """Detect write-write races: multiple processes writing to same signal."""
    if config is None:
        config = DetectionConfig()

    races = []
    
    for data_node in graph.data_nodes.values():
        if len(data_node.writers) >= 2:
            # Find all pairs of writers
            for writer1, writer2 in combinations(sorted(data_node.writers), 2):
                path1 = RacePath(
                    nodes=[writer1],
                    edges=[],
                    conditions=[],
                    nb_steps=0,
                    start_id=writer1,
                    end_id=data_node.id,
                )
                path2 = RacePath(
                    nodes=[writer2],
                    edges=[],
                    conditions=[],
                    nb_steps=0,
                    start_id=writer2,
                    end_id=data_node.id,
                )
                races.append(RaceGraph(
                    race_type=RaceType.WRITE_WRITE,
                    source_id=data_node.id,
                    target_id=data_node.id,
                    anchor1_id=writer1,
                    anchor2_id=writer2,
                    path1=path1,
                    path2=path2,
                ))

    return races


def detect_read_write_races(graph, config=None):
    """Detect read-write races: process reading while another writes."""
    if config is None:
        config = DetectionConfig()

    races = []
    
    for data_node in graph.data_nodes.values():
        # If multiple readers and writers exist
        if data_node.readers and data_node.writers:
            for reader in data_node.readers:
                for writer in data_node.writers:
                    if reader != writer:
                        path1 = RacePath(
                            nodes=[reader],
                            edges=[],
                            conditions=[],
                            nb_steps=0,
                            start_id=reader,
                            end_id=data_node.id,
                        )
                        path2 = RacePath(
                            nodes=[writer],
                            edges=[],
                            conditions=[],
                            nb_steps=0,
                            start_id=writer,
                            end_id=data_node.id,
                        )
                        races.append(RaceGraph(
                            race_type=RaceType.READ_WRITE,
                            source_id=data_node.id,
                            target_id=data_node.id,
                            anchor1_id=reader,
                            anchor2_id=writer,
                            path1=path1,
                            path2=path2,
                        ))

    return races


def detect_trigger_races(graph, config=None):
    """Detect trigger races: concurrent processes triggered same way."""
    if config is None:
        config = DetectionConfig()

    races = []
    
    # Group processes by their triggers
    trigger_to_procs = {}
    
    for compute_node in graph.compute_nodes.values():
        trigger_key = tuple(sorted(compute_node.triggers))
        if trigger_key:
            if trigger_key not in trigger_to_procs:
                trigger_to_procs[trigger_key] = []
            trigger_to_procs[trigger_key].append(compute_node.id)

    # Find processes triggered by same signals
    for trigger_key, procs in trigger_to_procs.items():
        if len(procs) >= 2:
            # Check if they write to overlapping signals
            for proc1, proc2 in combinations(sorted(procs), 2):
                node1 = graph.compute_nodes[proc1]
                node2 = graph.compute_nodes[proc2]
                
                # Get written signals
                writes1 = {a.dst_signal for a in node1.assignments}
                writes2 = {a.dst_signal for a in node2.assignments}
                
                # Check for overlap
                overlaps = writes1 & writes2
                for sig in overlaps:
                    sig_id = f"d_{sig}"
                    path1 = RacePath(
                        nodes=[proc1],
                        edges=[],
                        conditions=[],
                        nb_steps=0,
                        start_id=proc1,
                        end_id=sig_id,
                    )
                    path2 = RacePath(
                        nodes=[proc2],
                        edges=[],
                        conditions=[],
                        nb_steps=0,
                        start_id=proc2,
                        end_id=sig_id,
                    )
                    races.append(RaceGraph(
                        race_type=RaceType.TRIGGER,
                        source_id=sig_id,
                        target_id=proc1,
                        anchor1_id=proc1,
                        anchor2_id=proc2,
                        path1=path1,
                        path2=path2,
                    ))

    return races


def detect_all_races(graph, enabled_types=None, config=None):
    """Detect all race conditions in the design."""
    if enabled_types is None:
        enabled_types = {RaceType.WRITE_WRITE, RaceType.READ_WRITE, RaceType.TRIGGER}
    if config is None:
        config = DetectionConfig()

    all_races = []

    if RaceType.WRITE_WRITE in enabled_types:
        all_races.extend(detect_write_write_races(graph, config))

    if RaceType.READ_WRITE in enabled_types:
        all_races.extend(detect_read_write_races(graph, config))

    if RaceType.TRIGGER in enabled_types:
        all_races.extend(detect_trigger_races(graph, config))

    return all_races

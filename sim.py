import netsquid as ns
from netsquid.components import QuantumMemory, ClassicalChannel, QuantumChannel
from netsquid.components.models.delaymodels import FixedDelayModel
from netsquid.nodes import Node, Network
from netsquid.qubits import qubitapi
from netsquid.protocols import Protocol
import random
import numpy as np
from netsquid.qubits.operators import H, X, SWAP, CNOT

#Simulation's costants
T_coherence = 5.0
threshold_fidelity = 0.9
multi_party_enabled = True  # Attiva la distribuzione multi-party (GHZ, W, cluster)

# Global pool for entanglement recycling
entanglement_pool = []


#########################################################################
# Error Correction (3 qubits bit-flip code)
#########################################################################
def error_correct(qubit, error_probability=0.05):
    # Step 0: "Measure" the original qubit to extract its classical value
    # (in a real circuit you shouldn't measure it, but here we use it to simulate)
    outcome, _ = qubitapi.measure(qubit)
    original_bit = outcome  # 0 o 1

    # Step 1: Encode in 3 qubits
    # Create two qubits in |0> and "copy" the value of the original qubit
    encoded_bits = [original_bit, original_bit, original_bit]

    # Step 2: Introducing errors: for each qubit, with probability error_probability,
    # the value is inverted (simulates a bit-flip)
    for i in range(3):
        if random.random() < error_probability:
            encoded_bits[i] = 1 - encoded_bits[i]

    # Step 3: Syndrome measurement
    # Compare the pairs to find the error:
    # - If encoded_bits[0] != encoded_bits[1] then the first comparison gives 1, otherwise 0.
    # - If encoded_bits[1] != encoded_bits[2] then the second comparison gives 1, otherwise 0.
    syndrome1 = 1 if encoded_bits[0] != encoded_bits[1] else 0
    syndrome2 = 1 if encoded_bits[1] != encoded_bits[2] else 0

    # Step 4: Syndrome correction:
    # - Syndrome (1,0): error on the first qubit
    # - Syndrome (1,1): error on the second qubit
    # - Syndrome (0,1): error on the third qubit
    if (syndrome1, syndrome2) == (1, 0):
        encoded_bits[0] = 1 - encoded_bits[0]
    elif (syndrome1, syndrome2) == (1, 1):
        encoded_bits[1] = 1 - encoded_bits[1]
    elif (syndrome1, syndrome2) == (0, 1):
        encoded_bits[2] = 1 - encoded_bits[2]
    # If the syndrome is (0,0), no correction is made.

    # Step 5: Decoding: Majority vote on the three qubits
    majority_bit = 1 if sum(encoded_bits) > 1 else 0

    # Prepare a new qubit in the correct state
    corrected = qubitapi.create_qubits(1)[0]
    if majority_bit == 1:
        qubitapi.operate(corrected, X)
    return corrected


#############################################
# 1. Quantum Router Network Creation
#############################################
def create_mdi_network():
    network = Network("MDI-QKD-Network")

    # Creating main nodes
    alice = Node("Alice", port_names=["portQA", "portCA", "portSA"])
    bob = Node("Bob", port_names=["portQB", "portCB", "portSB"])
    charlie = Node("Charlie", port_names=["portQC1", "portQC2", "portCC1", "portCC2", "portCC_Router"])
    sifter = Node("Sifter", port_names=["portSA_sift", "portSB_sift"])

    # Quantum memory router with multiple communication ports
    router = Node("Router",
                  port_names=["portR1", "portR2", "portRC1", "portRC2", "portCR1", "portCR2", "portCR_Classical"])
    router.add_subcomponent(QuantumMemory("RouterMemory", num_positions=2))

    network.add_nodes([alice, bob, charlie, sifter, router])

    # Quantum channels with distinct ports
    # We absolutely cannot connect multiple outputs to the same port
    qchannel1 = QuantumChannel("QChan_Alice_to_Router", length=10, models={"delay_model": FixedDelayModel(delay=1e-3)})
    qchannel2 = QuantumChannel("QChan_Bob_to_Router", length=10, models={"delay_model": FixedDelayModel(delay=1e-3)})
    qchannel3 = QuantumChannel("QChan_Router_to_Charlie1", length=10,
                               models={"delay_model": FixedDelayModel(delay=1e-3)})
    qchannel4 = QuantumChannel("QChan_Router_to_Charlie2", length=10,
                               models={"delay_model": FixedDelayModel(delay=1e-3)})

    network.add_connection(alice, router, channel_to=qchannel1, label="quantum_Alice_Router",
                           port_name_node1="portQA", port_name_node2="portR1")
    network.add_connection(bob, router, channel_to=qchannel2, label="quantum_Bob_Router",
                           port_name_node1="portQB", port_name_node2="portR2")
    network.add_connection(router, charlie, channel_to=qchannel3, label="quantum_Router_Charlie1",
                           port_name_node1="portRC1", port_name_node2="portQC1")
    network.add_connection(router, charlie, channel_to=qchannel4, label="quantum_Router_Charlie2",
                           port_name_node1="portRC2", port_name_node2="portQC2")

    # Classic channels with separate ports to avoid conflicts
    cchannel1 = ClassicalChannel("CChan_Charlie_to_Alice", models={"delay_model": FixedDelayModel(delay=1e-3)})
    cchannel2 = ClassicalChannel("CChan_Charlie_to_Bob", models={"delay_model": FixedDelayModel(delay=1e-3)})
    cchannel3 = ClassicalChannel("CChan_Router_to_Charlie", models={"delay_model": FixedDelayModel(delay=1e-3)})

    network.add_connection(charlie, alice, channel_to=cchannel1, label="classical_Charlie_Alice",
                           port_name_node1="portCC1", port_name_node2="portCA")
    network.add_connection(charlie, bob, channel_to=cchannel2, label="classical_Charlie_Bob",
                           port_name_node1="portCC2", port_name_node2="portCB")
    network.add_connection(router, charlie, channel_to=cchannel3, label="classical_Router_Charlie",
                           port_name_node1="portCR_Classical", port_name_node2="portCC_Router")

    return network


#############################################
#Routing protocol with error correction
#############################################
class QuantumRouter(Protocol):
    def __init__(self, node, error_probability=0.05):
        super().__init__()
        self.node = node
        self.error_probability = error_probability
        self.memory = node.subcomponents["RouterMemory"]

    def run(self):
        while True:
            # Receiving the first input qubit from portR1
            yield self.await_port_input(self.node.ports["portR1"])
            q1 = self.node.ports["portR1"].rx_input().items[0]
            # Apply the  error correction procedure on the first qubit
            q1_corrected = error_correct(q1, self.error_probability)

            # Receiving the second input qubit from portR2
            yield self.await_port_input(self.node.ports["portR2"])
            q2 = self.node.ports["portR2"].rx_input().items[0]
            q2_corrected = error_correct(q2, self.error_probability)

            # Performs a Controlled-SWAP on the correct qubits
            control_qubit = qubitapi.create_qubits(1)[0]
            # The control qubit is in a superposition state
            qubitapi.operate(control_qubit, H)
            qubitapi.operate([control_qubit, q1_corrected, q2_corrected], SWAP)  # Controlled-SWAP
            print("[Router] Quantum Routing Performed (After Correction) with Controlled-SWAP")

            self.node.ports["portCR_Classical"].tx_output("Routing completed")


#############################################
# Adaptive Key Management
#############################################
class AdaptiveKeyManagement(Protocol):
    def __init__(self, node, target_key_length=128):
        super().__init__()
        self.node = node
        self.target_key_length = target_key_length
        self.key_pool = []
        self.current_key = None

    def run(self):
        while len(self.key_pool) < self.target_key_length:
            yield self.await_timer(0.01)
            # Simulating a new random key
            new_key = random.randint(0, 1)
            self.key_pool.append(new_key)
            print(f"[{self.node.name}] Generated New Key: {new_key}")

            # Every 10 keys, re-keying possible
            if len(self.key_pool) % 10 == 0:
                self.current_key = self.key_pool[-10:]
                print(f"[{self.node.name}] Re-keying: New Active Key {self.current_key}")

            # Simulate compromise and revocation
            if random.random() < 0.05:
                print(f"[{self.node.name}] WARNING: Compromised detected, initiating revocation!")
                self.key_pool = self.key_pool[-20:]


#############################################
# Multi-party distribution with Entanglement Recycling
#############################################
class MultiPartyQKD(Protocol):
    def __init__(self, node):
        super().__init__()
        self.node = node

    def run(self):
        global entanglement_pool
        while True:
            yield self.await_timer(0.02)
            if multi_party_enabled:
                # Check if there is a recycled GHZ state available
                if entanglement_pool:
                    ghz_state = entanglement_pool.pop(0)
                    print(f"[{self.node.name}] Usage GHZ state recycled from pool")
                else:
                    # Generate a new GHZ state
                    q1, q2, q3 = qubitapi.create_qubits(3)
                    qubitapi.operate(q1, H)
                    qubitapi.operate([q1, q2], CNOT)
                    qubitapi.operate([q1, q3], CNOT)
                    ghz_state = (q1, q2, q3)
                    print(f"[{self.node.name}] New GHZ state generated")

                # Simulates state loyalty check
                fidelity = random.uniform(0.85, 1.0)
                if fidelity >= threshold_fidelity:
                    entanglement_pool.append(ghz_state)
                    print(f"[{self.node.name}] GHZ state with fidelity {fidelity:.2f} recycled into the pool")
                else:
                    print(f"[{self.node.name}] GHZ state with fidelity {fidelity:.2f} NOT recycled")

                print(f"[{self.node.name}] GHZ state distributed between 3 nodes")


#############################################
# Simulation
#############################################
def run_simulation():
    # Set how NetSquid should represent and simulate quantum states of qubits.
    # KET is used to precisely represent pure quantum states as state vectors,
    # useful in small-scale simulations without complex decoherence.

    ns.set_qstate_formalism(ns.QFormalism.KET)
    network = create_mdi_network()

    # Declaring objects representing protocols and starting them
    router = QuantumRouter(node=network.nodes["Router"], error_probability=0.05)
    alice = AdaptiveKeyManagement(node=network.nodes["Alice"])
    bob = AdaptiveKeyManagement(node=network.nodes["Bob"])
    multi_party = MultiPartyQKD(node=network.nodes["Charlie"])

    router.start()
    alice.start()
    bob.start()
    multi_party.start()

    # Simulation start with timed execution
    ns.sim_run(end_time=10)


run_simulation()
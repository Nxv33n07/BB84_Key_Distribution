import matplotlib
matplotlib.use("Agg")
import qiskit
import qiskit_aer
print(f"DEBUG: Qiskit version: {qiskit.__version__}")
print(f"DEBUG: Qiskit Aer version: {qiskit_aer.__version__}")
from fastapi import FastAPI,Query
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from qiskit import QuantumCircuit, transpile,QuantumRegister, ClassicalRegister
from qiskit_aer import Aer
import random
import matplotlib.pyplot as plt
from qiskit.visualization import plot_bloch_vector, circuit_drawer, plot_state_city
from qiskit.quantum_info import Statevector
import io
import base64
from fastapi.responses import JSONResponse
from qiskit.quantum_info import Pauli
app = FastAPI(title="BB84 Quantum Key Distribution API (Qiskit)", root_path="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow frontend requests
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# Data Models
# ---------------------------
class Qubit(BaseModel):
    bit: int          # 0 or 1
    basis: str        # "+" (rectilinear) or "x" (diagonal)

class BobMeasure(BaseModel):
    basis: str        # Bob’s chosen basis


# ---------------------------
# In-Memory State
# ---------------------------
qubits_sent = []      # Store Alice’s qubits
qubits_eve = []       # Eve’s intercepted results
qubits_bob = []       # Bob’s measurements


# ---------------------------
# Helper: Prepare qubit state with Qiskit
# ---------------------------
def fig_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return encoded

def prepare_qubit(bit: int, basis: str):
    qc = QuantumCircuit(1, 1)

    # Encode classical bit
    if bit == 1:
        qc.x(0)

    # Apply diagonal basis (Hadamard)
    if basis == "x":
        qc.h(0)

    return qc

def measure_qubit(qc: QuantumCircuit, basis: str) -> int:
    # Apply measurement basis
    if basis == "x":
        qc.h(0)  # switch to diagonal basis

    qc.measure(0, 0)

    # New Qiskit API: transpile + run
    simulator = Aer.get_backend("aer_simulator")
    compiled_circuit = transpile(qc, simulator)
    result = simulator.run(compiled_circuit, shots=1).result()

    counts = result.get_counts()
    measured_bit = int(max(counts, key=counts.get))
    return measured_bit



def build_alice_circuit():
    n = len(qubits_sent)
    qr = QuantumRegister(n, "q")
    qc = QuantumCircuit(qr)

    for i, q in enumerate(qubits_sent):
        if q["bit"] == 1:
            qc.x(qr[i])
        if q["basis"] == "x":
            qc.h(qr[i])

    return qc

def build_eve_circuit():
    n = len(qubits_sent)
    qr = QuantumRegister(n, "q")
    cr = ClassicalRegister(n, "c")
    qc = QuantumCircuit(qr, cr)

    for i in range(n):
        if i < len(qubits_eve) and qubits_eve[i]:  # Eve acted
            eve_basis = qubits_eve[i]["basis"]
            if eve_basis == "x":
                qc.h(qr[i])
            qc.measure(qr[i], cr[i])
            qc.reset(qr[i])
            if qubits_eve[i]["measured"] == 1:
                qc.x(qr[i])
            if eve_basis == "x":
                qc.h(qr[i])

    return qc

def build_bob_circuit():
    n = len(qubits_sent)
    qr = QuantumRegister(n, "q")
    cr = ClassicalRegister(n, "c")
    qc = QuantumCircuit(qr, cr)

    for i in range(n):
        if i < len(qubits_bob) and qubits_bob[i]:
            bob_basis = qubits_bob[i]["basis"]
            if bob_basis == "x":
                qc.h(qr[i])
            qc.measure(qr[i], cr[i])

    return qc
# ---------------------------
# API Endpoints
# ---------------------------

@app.get("/")
def welcome():
    return {"message":"Welcome to api"}

@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/alice/send")
def alice_send(q: Qubit):
    """Alice prepares a qubit and stores it."""
    qc = prepare_qubit(q.bit, q.basis)
    qubits_sent.append({"bit": q.bit, "basis": q.basis, "qc": qc})
    return {"msg": "Alice sent a qubit", "qubit": q}

@app.get("/eve/intercept/{index}")
def eve_intercept(index: int):
    if index >= len(qubits_sent):
        return {"error": "Invalid qubit index"}

    q = qubits_sent[index]
    eve_basis = random.choice(["+", "x"])
    qc = q["qc"].copy()
    measured = measure_qubit(qc, eve_basis)

    # Save Eve’s collapsed qc internally
    eve_qc = prepare_qubit(measured, eve_basis)
    eve_result = {"basis": eve_basis, "measured": measured}

    if len(qubits_eve) <= index:
        qubits_eve.extend([None] * (index - len(qubits_eve) + 1))
    qubits_eve[index] = {"basis": eve_basis, "measured": measured, "qc": eve_qc}

    return {"msg": "Eve intercepted", "index": index, "eve_result": eve_result}
@app.post("/bob/measure/{index}")
def bob_measure(index: int, b: BobMeasure):
    if index >= len(qubits_sent):
        return {"error": "Invalid qubit index"}

    q = qubits_sent[index]

    # If Eve intercepted, state collapsed
    if len(qubits_eve) > index and qubits_eve[index]:
        eve_info = qubits_eve[index]
        qc = prepare_qubit(eve_info["measured"], eve_info["basis"])
    else:
        qc = q["qc"].copy()

    measured = measure_qubit(qc, b.basis)

    # Keep Bob's QC in memory only
    bob_qc = prepare_qubit(measured, b.basis)
    bob_result = {"basis": b.basis, "measured": measured}

    if len(qubits_bob) <= index:
        qubits_bob.extend([None] * (index - len(qubits_bob) + 1))
    qubits_bob[index] = {"basis": b.basis, "measured": measured, "qc": bob_qc}  # ✅ keep qc in memory

    # Return only JSON-safe data
    return {"msg": "Bob measured", "index": index, "bob_result": bob_result}
# @app.get("/eve/intercept/{index}")
# def eve_intercept(index: int):
#     """Eve intercepts qubit and measures it with random basis."""
#     if index >= len(qubits_sent):
#         return {"error": "Invalid qubit index"}

#     q = qubits_sent[index]
#     eve_basis = random.choice(["+", "x"])

#     qc = q["qc"].copy()
#     measured = measure_qubit(qc, eve_basis)

#     eve_result = {"basis": eve_basis, "measured": measured}
#     if len(qubits_eve) <= index:
#         qubits_eve.extend([None] * (index - len(qubits_eve) + 1))
#     qubits_eve[index] = eve_result

#     return {"msg": "Eve intercepted", "index": index, "eve_result": eve_result}


# @app.post("/bob/measure/{index}")
# def bob_measure(index: int, b: BobMeasure):
#     """Bob measures qubit at position `index` with his basis."""
#     if index >= len(qubits_sent):
#         return {"error": "Invalid qubit index"}

#     q = qubits_sent[index]

#     # If Eve already measured, collapse happened
#     if len(qubits_eve) > index and qubits_eve[index]:
#         eve_info = qubits_eve[index]
#         qc = prepare_qubit(eve_info["measured"], eve_info["basis"])
#     else:
#         qc = q["qc"].copy()

#     measured = measure_qubit(qc, b.basis)

#     bob_result = {"basis": b.basis, "measured": measured}
#     if len(qubits_bob) <= index:
#         qubits_bob.extend([None] * (index - len(qubits_bob) + 1))
#     qubits_bob[index] = bob_result

#     return {"msg": "Bob measured", "index": index, "bob_result": bob_result}


@app.get("/compare-bases")
def compare_bases():
    """Alice and Bob publicly compare bases, keep only matching ones."""
    if not qubits_sent or not qubits_bob:
        return {"error": "No qubits to compare"}
    
    # print("Alice");
    # for i in range(len(qubits_sent)):
    #     print({"bit":qubits_sent[i]["bit"], "basis":qubits_sent[i]["basis"]})
    # print("Eve");
    # for i in range(len(qubits_eve)):
    #     print({"bit":qubits_eve[i]["measured"], "basis":qubits_eve[i]["basis"]})
    # print("Bob");
    # for i in range(len(qubits_bob)):
    #     print({"bit":qubits_bob[i]["measured"], "basis":qubits_bob[i]["basis"]})

    matching_indices = []
    alice_key = []
    bob_key = []

    for i in range(min(len(qubits_sent), len(qubits_bob))):
        if not qubits_bob[i]:
            continue
        if qubits_sent[i]["basis"] == qubits_bob[i]["basis"]:
            matching_indices.append(i)
            alice_key.append(qubits_sent[i]["bit"])
            bob_key.append(qubits_bob[i]["measured"])

    # print({
    #     "matching_indices": matching_indices,
    #     "alice_key": alice_key,
    #     "bob_key": bob_key
    # })

    return {
        "matching_indices": matching_indices,
        "alice_key": alice_key,
        "bob_key": bob_key
    }


@app.get("/error-correction")
def error_correction(block_size: int = Query(3)):
    """
    Parity-based block error correction on the sifted key.
    Divides the sifted key into blocks, compares parities between Alice and Bob,
    and binary-searches within mismatched blocks to find and fix errors.
    Updates qubits_bob in-memory so /final-key reflects corrected data.
    """
    comp = compare_bases()
    if "error" in comp:
        return comp

    alice_key = comp["alice_key"]
    bob_key = list(comp["bob_key"])
    matching_indices = comp["matching_indices"]

    if not alice_key:
        return {"error": "No sifted key to correct"}

    blocks = []
    corrected_positions = []  # positions within sifted key that were flipped

    n = len(alice_key)
    block_num = 0
    i = 0
    while i < n:
        block_end = min(i + block_size, n)
        a_block = alice_key[i:block_end]
        b_block = bob_key[i:block_end]

        a_parity = sum(a_block) % 2
        b_parity = sum(b_block) % 2

        block_info = {
            "block": block_num,
            "start": i,
            "end": block_end,
            "alice_parity": a_parity,
            "bob_parity": b_parity,
            "corrected": False,
            "corrected_index": None,
        }

        if a_parity != b_parity:
            # Binary search within block to locate the single erroneous bit
            lo, hi = i, block_end
            while hi - lo > 1:
                mid = (lo + hi) // 2
                if sum(alice_key[lo:mid]) % 2 != sum(bob_key[lo:mid]) % 2:
                    hi = mid
                else:
                    lo = mid
            # lo is the sifted-key index of the erroneous bit
            bob_key[lo] ^= 1
            corrected_positions.append(lo)
            block_info["corrected"] = True
            block_info["corrected_index"] = lo

            # Persist correction into qubits_bob so /final-key reads updated data
            original_idx = matching_indices[lo]
            if original_idx < len(qubits_bob) and qubits_bob[original_idx]:
                qubits_bob[original_idx]["measured"] = bob_key[lo]

        blocks.append(block_info)
        i = block_end
        block_num += 1

    return {
        "alice_key": alice_key,
        "corrected_bob_key": bob_key,
        "corrected_indices": corrected_positions,
        "errors_corrected": len(corrected_positions),
        "total_blocks": len(blocks),
        "blocks_with_errors": sum(1 for b in blocks if b["corrected"]),
        "block_size": block_size,
        "blocks": blocks,
    }


@app.get("/final-key")
def final_key():
    """Compute final shared key and error rate."""
    comp = compare_bases()
    if "error" in comp:
        return comp

    alice_key = comp["alice_key"]
    bob_key = comp["bob_key"]

    if not alice_key:
        return {"error": "No matching bases → no key"}

    errors = sum(1 for i in range(len(alice_key)) if alice_key[i] != bob_key[i])
    error_rate = (errors / len(alice_key)) * 100

    return {
        "shared_key": "".join(map(str, alice_key)),
        "alice_key": alice_key,
        "bob_key": bob_key,
        "error_rate": error_rate,
        "has_eavesdropper": error_rate >= 20,
    }


@app.post("/reset")
def reset():
    """Reset all stored data (for new simulation)."""
    global qubits_sent, qubits_eve, qubits_bob
    qubits_sent = []
    qubits_eve = []
    qubits_bob = []
    return {"msg": "State reset"}


@app.get("/visualize/overall-circuit")
def visualize_overall(eve: str = Query("false")):
    """
    Build and return the entire BB84 protocol as one big circuit diagram.
    eve: "true"/"false"/"1"/"0"/etc as query param.
    """
    # Normalize string → bool
    eve_normalized = str(eve).lower() in ["true", "1", "yes", "on"]

    n = len(qubits_sent)
    if n == 0:
        return {"error": "No qubits yet, run simulation first."}

    qr = QuantumRegister(n, "q")
    cr = ClassicalRegister(n, "c")
    qc = QuantumCircuit(qr, cr)

    alice_bits = [q["bit"] for q in qubits_sent]
    alice_bases = [q["basis"] for q in qubits_sent]
    bob_bases = [b["basis"] if b else "+" for b in qubits_bob]

    for i in range(n):
        # Alice encodes
        if alice_bits[i] == 1:
            qc.x(qr[i])
        if alice_bases[i] == "x":
            qc.h(qr[i])

        # Optional Eve
        if eve_normalized and i < len(qubits_eve) and qubits_eve[i]:
            eve_basis = qubits_eve[i]["basis"]
            if eve_basis == "x":
                qc.h(qr[i])
            qc.measure(qr[i], cr[i])
            qc.reset(qr[i])
            if qubits_eve[i]["measured"] == 1:
                qc.x(qr[i])
            if eve_basis == "x":
                qc.h(qr[i])

        # Bob
        if i < len(bob_bases) and bob_bases[i] == "x":
            qc.h(qr[i])
        qc.measure(qr[i], cr[i])

    fig = qc.draw("mpl")
    encoded = fig_to_base64(fig)
    return {"img_base64": encoded}

@app.get("/visualize/overall/alice")
def visualize_overall_alice():
    if not qubits_sent:
        return {"error": "No qubits prepared yet."}
    qc = build_alice_circuit()
    fig = qc.draw("mpl")
    return {"img_base64": fig_to_base64(fig)}

@app.get("/visualize/overall/eve")
def visualize_overall_eve():
    if not qubits_eve:
        return {"error": "Eve has not intercepted any qubits."}
    qc = build_eve_circuit()
    fig = qc.draw("mpl")
    return {"img_base64": fig_to_base64(fig)}

@app.get("/visualize/overall/bob")
def visualize_overall_bob():
    if not qubits_bob:
        return {"error": "Bob has not measured any qubits yet."}
    qc = build_bob_circuit()
    fig = qc.draw("mpl")
    return {"img_base64": fig_to_base64(fig)}


@app.get("/visualize/circuit/{index}")
def visualize_circuit(index: int):
    """Return a base64-encoded circuit diagram for qubit at index."""
    if index >= len(qubits_sent):
        return {"error": "Invalid qubit index"}

    qc = qubits_sent[index]["qc"]
    fig = circuit_drawer(qc, output="mpl")
    encoded = fig_to_base64(fig)
    return {"img_base64": encoded}


@app.get("/visualize/bloch/{index}")
def visualize_bloch(index: int):
    """Return a Bloch sphere for qubit state at index."""
    if index >= len(qubits_sent):
        return {"error": "Invalid qubit index"}

    qc = qubits_sent[index]["qc"]
    state = Statevector.from_instruction(qc)

    bloch_vector = [
        state.expectation_value(Pauli("X")).real,
        state.expectation_value(Pauli("Y")).real,
        state.expectation_value(Pauli("Z")).real,
    ]

    fig = plot_bloch_vector(bloch_vector)
    encoded = fig_to_base64(fig)
    return {"img_base64": encoded}


@app.get("/visualize/{who}/{index}")
def visualize_participant_qubit(who: str, index: int):
    """
    Visualize qubit state for Alice, Eve, or Bob.
    who = 'alice' | 'eve' | 'bob'
    """
    qsource = None
    if who == "alice" and index < len(qubits_sent):
        qsource = qubits_sent[index]["qc"]
    elif who == "eve" and index < len(qubits_eve) and qubits_eve[index]:
        qsource = qubits_eve[index]["qc"]
    elif who == "bob" and index < len(qubits_bob) and qubits_bob[index]:
        qsource = qubits_bob[index]["qc"]
    else:
        return {"error": "No data for this participant/index"}

    fig_circuit = circuit_drawer(qsource, output="mpl")
    circuit_base64 = fig_to_base64(fig_circuit)

    state = Statevector.from_instruction(qsource)
    bloch_vector = [
        state.expectation_value(Pauli("X")).real,
        state.expectation_value(Pauli("Y")).real,
        state.expectation_value(Pauli("Z")).real,
    ]
    fig_bloch = plot_bloch_vector(bloch_vector)
    bloch_base64 = fig_to_base64(fig_bloch)

    return {"circuit": circuit_base64, "bloch": bloch_base64}


@app.get("/visualize/{index}")
def visualize_qubit_alice(index: int):
    """Return both circuit diagram and Bloch sphere for Alice's qubit at index."""
    if index >= len(qubits_sent):
        return {"error": "Invalid qubit index"}

    qc = qubits_sent[index]["qc"]
    state = Statevector.from_instruction(qc)

    fig_circuit = circuit_drawer(qc, output="mpl")
    circuit_base64 = fig_to_base64(fig_circuit)

    bloch_vector = [
        state.expectation_value(Pauli("X")).real,
        state.expectation_value(Pauli("Y")).real,
        state.expectation_value(Pauli("Z")).real,
    ]
    fig_bloch = plot_bloch_vector(bloch_vector)
    bloch_base64 = fig_to_base64(fig_bloch)

    return {"circuit": circuit_base64, "bloch": bloch_base64}

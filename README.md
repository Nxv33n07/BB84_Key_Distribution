# BB84 Quantum Key Distribution Simulator

An interactive full-stack simulator of the **BB84 quantum key distribution protocol** — the first and most widely studied quantum cryptography protocol. Watch Alice and Bob establish a secure shared key using quantum mechanics, observe Eve's eavesdropping attempts, and see how parity-based error correction reconciles key disagreements.

---

## What is BB84?

BB84 (Bennett & Brassard, 1984) is a quantum key distribution protocol that uses the principles of quantum mechanics to allow two parties (Alice and Bob) to generate a provably secure shared secret key. Any eavesdropping attempt by a third party (Eve) introduces measurable disturbances in the quantum channel, making it detectable.

---

## Features

- **Interactive step-by-step simulation** of the full BB84 protocol
- **Two modes** — Secure Channel (no Eve) and Eve Intercepts
- **Adjustable parameters** — qubit count (4–60), simulation speed, Eve interception rate
- **Real quantum simulation** via Qiskit Aer (not a mock — actual quantum circuits)
- **Quantum circuit diagrams** and **Bloch sphere visualizations** for every qubit
- **Overall circuit view** combining Alice, Eve, and Bob's operations
- **Bit-by-bit key comparison** — mismatches highlighted in red after key generation
- **Parity-based error correction** (simplified Cascade) — fixes errors and shows corrected bits in green
- **QBER tracking** with live error rate chart across simulation runs
- **Chat log** narrating every protocol step from Alice, Bob, Eve, and System

---

## Protocol Flow

```
1. Prepare Qubits     — Alice generates random bits and bases
2. Send Qubits        — Qubits transmitted; Eve may intercept with random basis
3. Compare Bases      — Alice & Bob publicly compare bases, discard mismatches (sifting)
4. Generate Key       — Raw sifted key shown; mismatches between Alice & Bob highlighted
5. Fix Errors         — Parity reconciliation corrects Bob's key; corrected bits shown in green
```

---

## Tech Stack

### Backend

| Technology | Role                                     |
| ---------- | ---------------------------------------- |
| Python 3.9 | Runtime                                  |
| FastAPI    | REST API                                 |
| Qiskit 2.x | Quantum circuit simulation               |
| Qiskit Aer | Aer simulator backend                    |
| Matplotlib | Circuit diagram & Bloch sphere rendering |
| Uvicorn    | ASGI server                              |

### Frontend

| Technology               | Role                 |
| ------------------------ | -------------------- |
| React 18 + TypeScript    | UI framework         |
| Vite                     | Build tool           |
| Tailwind CSS + shadcn/ui | Styling & components |
| Framer Motion            | Animations           |
| TanStack Query           | API state management |
| Axios                    | HTTP client          |
| Recharts                 | Error rate chart     |

---

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js 18+
- npm

### Backend

```bash
cd bb84_backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

API docs available at `http://localhost:8000/docs`

### Frontend

```bash
cd bb84-frontend
npm install
npm run dev
```

Open `http://localhost:5173`

> By default the frontend points to the deployed backend. For local development, update `API_BASE_URL` in `bb84-frontend/src/services/bb84Api.ts` to `http://localhost:8000`.

---

## API Endpoints

| Method | Endpoint                     | Description                                   |
| ------ | ---------------------------- | --------------------------------------------- |
| `POST` | `/alice/send`                | Alice prepares and sends a qubit              |
| `GET`  | `/eve/intercept/{index}`     | Eve intercepts qubit with random basis        |
| `POST` | `/bob/measure/{index}`       | Bob measures qubit with chosen basis          |
| `GET`  | `/compare-bases`             | Sift key — keep only matching basis positions |
| `GET`  | `/final-key`                 | Generate raw key with QBER                    |
| `GET`  | `/error-correction`          | Parity-based error correction on sifted key   |
| `POST` | `/reset`                     | Clear all in-memory state                     |
| `GET`  | `/visualize/circuit/{index}` | Circuit diagram for qubit at index            |
| `GET`  | `/visualize/bloch/{index}`   | Bloch sphere for qubit at index               |
| `GET`  | `/visualize/{who}/{index}`   | Circuit + Bloch for alice/eve/bob at index    |
| `GET`  | `/visualize/overall-circuit` | Full protocol circuit diagram                 |
| `GET`  | `/visualize/overall/alice`   | Alice's full encoding circuit                 |
| `GET`  | `/visualize/overall/eve`     | Eve's interception circuit                    |
| `GET`  | `/visualize/overall/bob`     | Bob's measurement circuit                     |
| `GET`  | `/health`                    | Health check                                  |

---

## Error Correction

The simulator implements a **single-pass parity-based reconciliation** (simplified Cascade):

1. The sifted key is divided into blocks of 3 bits
2. Alice broadcasts the parity of each block publicly
3. For any block where parities differ, a binary search locates the exact erroneous bit
4. Bob flips the incorrect bit — both keys now agree

This is shown visually in the Results panel:

- **After Generate Key** — Alice vs Bob bit comparison with red/green indicators
- **After Fix Errors** — All bits turn green, correction summary shown

---

## Project Structure

```
BB84_Key_Distribution/
├── bb84_backend/
│   ├── app.py              # FastAPI app — all endpoints and quantum logic
│   └── requirements.txt
└── bb84-frontend/
    └── src/
        ├── components/
        │   ├── BB84Simulator.tsx    # Main simulation orchestrator
        │   ├── AlicePanel.tsx       # Alice's qubit display
        │   ├── BobPanel.tsx         # Bob's measurement display
        │   ├── EvePanel.tsx         # Eve's interception panel
        │   ├── ControlPanel.tsx     # Protocol step buttons
        │   ├── ResultsCard.tsx      # Key results + error correction view
        │   ├── ChatLog.tsx          # Protocol narration
        │   ├── QuantumChannel.tsx   # Photon animation
        │   └── OverallCircuit.tsx   # Full circuit visualization
        ├── services/
        │   └── bb84Api.ts           # All API calls
        └── types/
            └── bb84.ts              # TypeScript types for the protocol
```

---

## Author

**Naveen** — [github.com/Nxv33n07](https://github.com/Nxv33n07)

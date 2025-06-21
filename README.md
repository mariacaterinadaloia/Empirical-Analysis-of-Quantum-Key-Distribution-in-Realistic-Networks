# An Empirical Analysis of Quantum Key Distribution in Realistic Networks

>Abstract—Quantum technologies promise to boost ICT further
by extending its limits, even by promising more effective and
secure communications due to the benefits of quantum physics.
This leads to Quantum Key Distribution (QKD), a cryptographic
primitive for securely exchanging a secret key between distant
endpoints, leveraging an insecure communication channel due
to potential eavesdroppers. The literature on QKD started with
the BB84 protocol proposed in 1984 and continued with other
protocols, each with its pros and cons. Still, they have been
chiefly designed for static scenarios and do not consider the
needs of dynamic networks. This paper presents a QKD solution
for dynamic networks combining adaptive key management
techniques and fault-tolerant routing, ensuring high security and
efficiency even in variable network topologies. Using MDI-QKD
(Measurement Device Independent QKD) and simulations with
NetSquid, we provide a preliminary assessment of this solution’s
robustness against dynamic attacks and the improvement in
quantum resource management. The work also compares the
protocol’s effectiveness with existing solutions, highlighting the
advantages and potential practical applications.


This repository contains the code of the simulation we proposed. 
The main script `sim.py` demonstrates how to simulate quantum communication protocols, channel noise, entanglement, and measurements between quantum nodes using realistic network components.

---

## Getting Started

Follow these steps to install and run the simulation:

---

### 1.  Register for NetSquid Access

NetSquid is **free**, but requires registration to use.

👉 Register at: [https://forum.netsquid.org](https://forum.netsquid.org)

You’ll need your forum credentials (username and password) to install the package.

---

### 2. Install NetSquid

Use `pip` with the custom NetSquid package index. Run:

```bash
  pip3 install --extra-index-url https://pypi.netsquid.org netsquid
```
This command will prompt you for your forum credentials.

---

### 3. Install Python Dependencies

After installing NetSquid, install the remaining dependencies:

```bash
pip install -r requirements.txt
```
⚠️ Make sure the requirements.txt file is in the root folder and lists all additional packages used in your project (e.g., matplotlib, numpy, etc.).

---

### 4. ▶ Run the Simulation

Run the simulation script with:

```bash
python3 sim.py
```

---

### Project Structure

.

├── sim.py                # Main simulation script using NetSquid

├── requirements.txt      # Additional Python dependencies

└── README.md             # This file

---

## 📄 Scientific Paper

This simulation is based on the following research paper:

**Title:** *An Empirical Analysis of Quantum Key Distribution in Realistic Networks*  
**Authors:** Maria Caterina D’Aloia, Christian Esposito  
**Institution:** University of Salerno  

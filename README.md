# DeceVo: Decentralized Voting System Utilizing Blockchain and Homomorphic Encryption

DeceVo is voting system designed to leverage the security and transparency of blockchain technology, along with the privacy-preserving characteristics of homomorphic encryption. This project aims to provide a framework for conducting secure, anonymous, and verifiable online elections.

## Features

- **Blockchain Integration**: Ensures tamper-proof record keeping of votes.
- **Homomorphic Encryption**: Allows for the votes to be counted without being decrypted, maintaining voter privacy.
- **Decentralization**: Removes the need for a central authority, reducing the risk of fraud or interference.
- **Transparency**: All operations on the blockchain are visible for verification, ensuring fair elections.


# Projcet Structure (The Directory Tree)

```
.
├── Paillier.py # Homomorphic encryption implementation
├── README.md # Project documentation
├── blockchain.py # Core blockchain functionality
├── primes-to-100k.txt # Prime numbers list for encryption purposes
├── templates # HTML templates for the web interface
│ ├── add_node.html # Add a new node to the network
│ ├── blocks.html # Display blockchain blocks
│ ├── d.gitkeep # Git placeholder for directory structure
│ ├── index.html # Main landing page
│ ├── mined_blocks.html # Show mined blocks in the system
│ ├── new_transaction.html # Create a new transaction (vote)
│ ├── node_totals.html # Display node total counts
│ ├── sync_nodes.html # Interface for node synchronization
│ └── vote_page.html # Voting interface for users
└── tree.txt # Directory tree for reference
```

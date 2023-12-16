import hashlib
import json
from time import time
from uuid import uuid4
from flask import Flask, jsonify, request, render_template
import requests
from urllib.parse import urlparse
from datetime import datetime
from threading import Lock
import sys
from Paillier import *
import math


class Blockchain(object):
    difficulty_target = "000"

    def hash_block(self, block):
        block_encoded = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_encoded).hexdigest()

    def __init__(self):

        self.chain = []
        self.current_transactions = []
        self.nodes = set()
        self.lock = Lock()
        self.create_genesis_block()
        self.crpyt = Paillier()
        self.voted_ports = set()
        self.starter_difficulity = "00"
        self.blocks_number = 1
        self.difficulty_target = "00"

    
    def create_genesis_block(self):
        genesis_transaction = {
            'sender': "0",
            'recipient': "creator_address",  # Replace with your address
            'amount': 1000,
        }
        self.current_transactions.append(genesis_transaction)
        genesis_hash = self.hash_block("genesis_block")
        self.append_block(hash_of_previous_block=genesis_hash,
                          nonce=self.proof_of_work(0, genesis_hash, [genesis_transaction]))


    def increase_difficulty(self, blocks_number, starter_difficulity):
        threshold_blocks = 10  # Adjust this threshold as needed

        # Calculate the floating-point number based on the number of mined blocks
        floating_point_number = blocks_number / threshold_blocks
        print(floating_point_number)
        # Round up the floating-point number
        rounded_number = math.floor(floating_point_number)

        # Generate the new new_difficulty with a number of leading zeros equal to the rounded number
        new_difficulty = '0' * rounded_number + starter_difficulity
        return new_difficulty


    def proof_of_work(self, index, hash_of_previous_block, transactions):
        nonce = 0
        while self.valid_proof(index, hash_of_previous_block, transactions, nonce) is False:
            nonce += 1
        return nonce

    def valid_proof(self, index, hash_of_previous_block, transactions, nonce):
        content = f'{index}{hash_of_previous_block}{transactions}{nonce}'.encode()
        content_hash = hashlib.sha256(content).hexdigest()
        return content_hash[:len(self.difficulty_target)] == self.difficulty_target

    def append_block(self, nonce, hash_of_previous_block):
        block = {
            'index': len(self.chain),
            'timestamp': time(),
            'transactions': self.current_transactions,
            'nonce': nonce,
            'hash_of_previous_block': hash_of_previous_block
        }
        self.current_transactions = []
        self.chain.append(block)
        return block

    def calculate_balances(self):
        balances = {}
        for block in self.chain:
            for tx in block['transactions']:
                sender = tx['sender']
                recipient = tx['recipient']
                amount = tx['amount']
                balances[sender] = balances.get(sender, 0) - amount
                balances[recipient] = balances.get(recipient, 0) + amount
        return balances

    def add_transaction(self, sender, recipient, amount):
        with self.lock:
            balances = self.calculate_balances()
            print(balances)
            for block in self.chain:
                for tx in block['transactions']:
                    if tx['sender'] == sender and tx['sender'] != '0':
                        raise ValueError('The coin has already been spent')
            if balances.get(sender, 0) < amount and sender != '0':
                if int(balances.get(sender, 0)) < int(amount) and sender != '0':
                    raise ValueError('Insufficient balance')
            self.current_transactions.append({
                'sender': sender,
                'recipient': recipient,
                'amount': amount,
            })
            return self.last_block['index'] + 1

    def decrypt_candidate_totals(self):
        decrypted_totals = {}
        neighbours = self.nodes
        candidate_ports = [node[0] for node in neighbours if node[1] == 'C']
        for candidate_port, encrypted_total in self.candidates.items():
            # Decrypt each candidate's total
            decrypted_total = self.crpyt.decrypt(encrypted_total)
            decrypted_totals[candidate_port] = decrypted_total

        return decrypted_totals

    @property
    def last_block(self):
        return self.chain[-1]

    def add_node(self, address):
        parsed_url = urlparse(address[0])
        self.nodes.add((parsed_url.netloc, address[1]))

    def valid_chain(self, chain):
        last_block = chain[0]
        current_index = 1
        while current_index < len(chain):
            block = chain[current_index]
            if block['hash_of_previous_block'] != self.hash_block(last_block):
                return False
            last_block = block
            current_index += 1
        return True

    def update_blockchain(self):
        # get the nodes around us that has been registered
        neighbours = self.nodes
        ports_only = [ports[0] for ports in neighbours]
        new_chain = None
        # for simplicity, look for chains longer than ours
        max_length = len(self.chain)
        # grab and verify the chains from all the nodes in our
        # network
        for node in ports_only:
            # get the blockchain from the other nodes
            response = requests.get(f'http://{node}/blockchain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

            # check if the length is longer and the chain
            # is valid
            if length > max_length and self.valid_chain(chain):
                max_length = length
                new_chain = chain
            # replace our chain if we discovered a new, valid
            # chain longer than ours
        if new_chain:
            self.chain = new_chain
            print("blockchain updated")
        print("blockchain already up-to-date")


app = Flask(__name__, template_folder='templates')
node_identifier = str(uuid4()).replace('_', "")
blockchain = Blockchain()
blockchain.add_transaction(sender="0", recipient=node_identifier, amount=blockchain.crpyt.encrypt(1))
blockchain.add_node(("http://127.0.0.1:10000", "C"))
blockchain.add_node(("http://127.0.0.1:20000", "C"))
for nodeNum in range(1, 6):
    if int(f"500{nodeNum}") == int(sys.argv[1]):
        continue
    node_address = f"http://127.0.0.1:500{nodeNum}"
    blockchain.add_node((node_address, "V"))


@app.route('/')
def home():
    blockchain.update_blockchain()
    return render_template('index.html')


@app.route('/transactions/new', methods=['GET', 'POST'])
def new_transaction():
    if request.method == 'POST':
        values = request.get_json()
        required_fields = ['sender', 'recipient', 'amount']
        if not all(k in values for k in required_fields):
            return ('Missing fields', 400)
        try:
            index = blockchain.add_transaction(
                values['sender'], values['recipient'], values['amount'])
        except ValueError as e:
            return jsonify({'message': str(e)}), 400
        response = {'message': f'Transaction will be added to Block {index}'}
        return (jsonify(response), 201)
    else:
        return render_template('new_transaction.html')


@app.route('/blockchain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


@app.route('/mine', methods=['GET'])
def mine_block_page():
    blockchain.add_transaction(sender="0", recipient=node_identifier, amount=blockchain.crpyt.encrypt(0))
    last_block_hash = blockchain.hash_block(blockchain.last_block)
    index = len(blockchain.chain)
    nonce = blockchain.proof_of_work(
        index, last_block_hash, blockchain.current_transactions)
    block = blockchain.append_block(nonce, last_block_hash)
     # Increment blocks mined
    blockchain.blocks_number += 1
    
    # adjust difficulty target
    blockchain.difficulty_target = blockchain.increase_difficulty(blockchain.blocks_number, blockchain.starter_difficulity)
    response = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'message': "New Block Mined",
        'index': block['index'],
        'hash_of_previous_block': block['hash_of_previous_block'],
        'nonce': block['nonce'],
        'transactions': block['transactions'],
    }
    return render_template('mined_blocks.html', block=response)


@app.route('/blocks', methods=['GET'])
def show_blocks():
    return render_template('blocks.html', blocks=blockchain.chain)


@app.route('/nodes/add_node', methods=['GET', 'POST'])
def add_node():
    if request.method == 'POST':
        port = request.form.get('port')
        role = request.form.get('role')

        if not port or not role:
            return "Error: Missing port or role information", 400

        node_address = f"http://127.0.0.1:{port}"
        # Add the new node to the blockchain network
        blockchain.add_node((node_address, role))
        
        return render_template('index.html')

    return render_template('add_node.html')


@app.route('/nodes/node_totals', methods=['GET'])
def node_totals():
    node_votes = {}

    for block in blockchain.chain:
        for tx in block['transactions']:
            recipient = tx['recipient']
            amount = tx['amount']
            if recipient.startswith("127.0.0.1:"):
                if recipient not in node_votes:
                    node_votes[recipient] = blockchain.crpyt.encrypt(0)
                node_votes[recipient] = node_votes[recipient] * \
                    amount  # Accumulate votes for each node

    decrypted_totals = {}
    for node, encrypted_amount in node_votes.items():
        decrypted_amount = blockchain.crpyt.decrypt(encrypted_amount)
        # Decrypt and store node-wise totals
        decrypted_totals[node] = decrypted_amount

    return render_template('node_totals.html', node_totals=decrypted_totals)


# replace the route...
@app.route('/vote', methods=['GET', 'POST'])
def vote():
    if request.method == 'POST':
        candidate_port = f"127.0.0.1:{request.form.get('candidate_port')}"
        # Sending 0 coins to all candidates except the chosen one (sending 1)
        # From node initialization each node must keep a list of candidate's ports and its own port
        # get the nodes around us that have been registered
        if sys.argv[1] in blockchain.voted_ports:
            response = {'message': 'Already voted'}
            return jsonify(response), 400
        neighbours = blockchain.nodes
        candidate_ports = [node[0] for node in neighbours if node[1] == 'C']
        for port in candidate_ports:
            amount = 0 if port != candidate_port else 1
            blockchain.add_transaction(
                sender='0', recipient=port, amount=blockchain.crpyt.encrypt(amount))
            print(port)
            print(candidate_port)
            blockchain.voted_ports.add(sys.argv[1])
        response = {'message': 'Vote recorded'}
        return render_template('index.html')
    elif request.method == "GET":
        neighbours = blockchain.nodes
        candidate_ports = [node[0].split(":")[1] for node in neighbours if node[1] == 'C']
        return render_template('vote_page.html', candidates=candidate_ports)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(sys.argv[1]))

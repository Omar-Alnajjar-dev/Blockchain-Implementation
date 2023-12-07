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
from RSA import *

class Blockchain(object):
    difficulty_target = "00000" 

    def hash_block(self, block):
        block_encoded = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_encoded).hexdigest()

    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()
        self.lock = Lock()
        self.create_genesis_block()

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

    def add_transaction(self, sender, recipient, amount, fee):
        with self.lock:
            balances = self.calculate_balances()
            print(balances)
            for block in self.chain:
                for tx in block['transactions']:
                    if tx['sender'] == sender and tx['sender'] != '0':
                        raise ValueError('The coin has already been spent')
            # if balances.get(sender, 0) < amount + fee:
            #     raise ValueError('Insufficient balance including fee')
            self.current_transactions.append({
                'sender': sender,
                'recipient': recipient,
                'amount': amount,
            })
            # Fee transaction
            self.current_transactions.append({
                'sender': sender,
                'recipient': 'miner_address',  # Replace with miner's address
                'amount': fee,
            })
            return self.last_block['index'] + 1

    def decrypt_candidate_totals(self):
        decrypted_totals = {}
        for candidate_port, encrypted_total in self.candidates.items():
            # Decrypt each candidate's total
            decrypted_total = DecryptionFunction(encrypted_total)
            decrypted_totals[candidate_port] = decrypted_total

        return decrypted_totals

    def find_winner(self):
        decrypted_totals = self.decrypt_candidate_totals()

        # Find the candidate's port with the highest total
        winner = max(decrypted_totals, key=decrypted_totals.get)
        return winner


    @property
    def last_block(self):
        return self.chain[-1]

    def add_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def valid_chain(self, chain):
        last_block = chain[0]
        current_index = 1
        while current_index < len(chain):
            block = chain[current_index]
            if block['hash_of_previous_block'] != self.hash_block(last_block):
                return False
            if not self.valid_proof(current_index, block['hash_of_previous_block'], block['transactions'], block['nonce']):
                return False
            last_block = block
            current_index += 1
        return True

    def update_blockchain(self):
        neighbours = self.nodes
        new_chain = None
        max_length = len(self.chain)
        for node in neighbours:
            response = requests.get(f'http://{node}/blockchain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain
        if new_chain:
            self.chain = new_chain
            return True
        return False
    
    # # create afunction that genrates a public and private key
    # def generate_keys(self):
    #     r_private_key , r_public_key = rsa_genKeys()
    #     return r_private_key, r_public_key

app = Flask(__name__, template_folder='templates')
node_identifier_list = []
node_identifier_list.append(str(uuid4()).replace('_', ""))
# node_coins = []
blockchain = Blockchain()
# node_coins.append(blockchain.generate_keys())

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/transactions/new', methods=['GET', 'POST'])
def new_transaction():
    if request.method == 'POST':
        values = request.get_json()
        required_fields = ['sender', 'recipient', 'amount', 'fee']
        if not all(k in values for k in required_fields):
            return ('Missing fields', 400)
        try:
            index = blockchain.add_transaction(values['sender'], values['recipient'], values['amount'], values['fee'])
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
    # node_coins.append(blockchain.generate_keys())
    # coin_address = rsa_encrypt(node_coins[-1][1], int(node_identifier.replace('-', ''), 16))
    node_identifier_list.append(str(uuid4()).replace('_', ""))
    blockchain.add_transaction(sender="0", recipient=node_identifier_list[-2], amount=1, fee=0)
    last_block_hash = blockchain.hash_block(blockchain.last_block)
    index = len(blockchain.chain)
    nonce = blockchain.proof_of_work(index, last_block_hash, blockchain.current_transactions)
    block = blockchain.append_block(nonce, last_block_hash)
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


# Voting process

@app.route('/vote', methods=['POST'])
def vote():
    values = request.get_json()

    # Assuming 'candidate_port' is provided in the JSON
    candidate_port = values.get('candidate_port')

    # Sending 0 coins to all candidates except the chosen one (sending 1)
    # From node initialization each node must keep a list of candidate's ports and it's own port
    for port in all_candidate_ports:
        amount = 0 if port != candidate_port else 1
        blockchain.add_transaction(sender=my_port, recipient=port, amount=EncryptionFunction(amount))

    response = {'message': 'Vote recorded'}
    return jsonify(response), 200


# Determining the winner
@app.route('/result', methods=['GET'])
def get_winner():
    winner_port = blockchain.find_winner()
    response = {'winner_port': winner_port}
    return jsonify(response), 200


@app.route('/nodes/add_nodes', methods=['POST'])
def add_nodes():
    nodes = request.get_json().get('nodes')
    if nodes is None or not isinstance(nodes, list):
        return jsonify({'message': 'Invalid or missing nodes data'}), 400
    for node in nodes:
        blockchain.add_node(node)
    node_list = list(blockchain.nodes)
    return render_template('nodes_added.html', nodes=node_list)

@app.route('/nodes/sync', methods=['GET'])
def sync():
    updated = blockchain.update_blockchain()
    if updated:
        updated_message = 'The blockchain has been updated to the latest'
    else:
        updated_message = 'Our blockchain is the latest'
    return render_template('sync_nodes.html', message=updated_message, blockchain=blockchain.chain)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(sys.argv[1]))

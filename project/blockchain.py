import hashlib
import json
from time import time
from certificate import Certificate

class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_certificates = []
        
        # Create the genesis block
        self.create_block(previous_hash='1', proof=100)
    
    def create_block(self, proof, previous_hash):
        """
        Create a new block in the blockchain
        """
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'certificates': self.current_certificates,
            'proof': proof,
            'previous_hash': previous_hash
        }
        
        # Reset the current list of certificates
        self.current_certificates = []
        
        # Calculate hash for this block
        block['hash'] = self.hash_block(block)
        
        # Add block to the chain
        self.chain.append(block)
        return block
    
    def get_last_block(self):
        """
        Returns the last block in the chain
        """
        return self.chain[-1]
    
    def proof_of_work(self, previous_proof):
        """
        Simple Proof of Work Algorithm:
        - Find a number p' such that hash(p * p') contains 4 leading zeroes
        - p is the previous proof, p' is the new proof
        """
        new_proof = 1
        check_proof = False
        
        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
        
        return new_proof
    
    def hash_block(self, block):
        """
        Creates a SHA-256 hash of a block
        """
        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()
    
    def is_chain_valid(self, chain):
        """
        Check if the blockchain is valid
        """
        previous_block = chain[0]
        block_index = 1
        
        while block_index < len(chain):
            block = chain[block_index]
            
            # Check if the previous hash matches
            if block['previous_hash'] != self.hash_block(previous_block):
                return False
            
            # Check if the Proof of Work is correct
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
            
            if hash_operation[:4] != '0000':
                return False
            
            previous_block = block
            block_index += 1
        
        return True
    
    def add_certificate(self, certificate):
        """
        Add a new certificate to the list of certificates
        """
        self.current_certificates.append(certificate.to_dict())
        
        # Get the last block
        previous_block = self.get_last_block()
        previous_proof = previous_block['proof']
        
        # Find the proof for the new block
        proof = self.proof_of_work(previous_proof)
        
        # Get the hash of the previous block
        previous_hash = self.hash_block(previous_block)
        
        # Create the new block
        block = self.create_block(proof, previous_hash)
        
        return block['index']
    
    def find_certificate(self, certificate_id):
        """
        Find a certificate in the blockchain by its ID
        """
        for block in self.chain:
            for cert in block['certificates']:
                if cert['certificate_id'] == certificate_id:
                    return cert, block
        return None, None
    
    def verify_certificate(self, certificate_id, block_hash):
        """
        Verify if a certificate exists in the blockchain and is valid
        """
        cert, block = self.find_certificate(certificate_id)
        
        if cert and block:
            # Verify the block hash
            if block['hash'] == block_hash:
                return True
        
        return False
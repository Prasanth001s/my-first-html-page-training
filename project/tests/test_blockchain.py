import unittest
import sys
import os

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from blockchain import Blockchain
from certificate import Certificate

class TestBlockchain(unittest.TestCase):
    def setUp(self):
        self.blockchain = Blockchain()
        self.test_certificate_data = {
            'recipient_name': 'John Doe',
            'recipient_id': '12345',
            'issuer_name': 'Test University',
            'course_name': 'Blockchain 101',
            'description': 'Introduction to Blockchain Technology'
        }
        self.certificate = Certificate(self.test_certificate_data)
    
    def test_create_block(self):
        # Get the initial length of the chain
        initial_length = len(self.blockchain.chain)
        
        # Create a new block
        proof = self.blockchain.proof_of_work(100)
        previous_hash = self.blockchain.hash_block(self.blockchain.chain[-1])
        block = self.blockchain.create_block(proof, previous_hash)
        
        # Check if the chain length increased by 1
        self.assertEqual(len(self.blockchain.chain), initial_length + 1)
        
        # Check if the block has the correct structure
        self.assertIn('index', block)
        self.assertIn('timestamp', block)
        self.assertIn('certificates', block)
        self.assertIn('proof', block)
        self.assertIn('previous_hash', block)
        self.assertIn('hash', block)
    
    def test_proof_of_work(self):
        previous_proof = 100
        proof = self.blockchain.proof_of_work(previous_proof)
        
        # Check if the proof is valid
        hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
        self.assertTrue(hash_operation[:4] == '0000')
    
    def test_hash_block(self):
        # Get the last block
        block = self.blockchain.chain[-1]
        
        # Calculate the hash
        hash_value = self.blockchain.hash_block(block)
        
        # Check if the hash is a string of length 64 (SHA-256 produces 64 hex characters)
        self.assertEqual(len(hash_value), 64)
        self.assertTrue(all(c in '0123456789abcdef' for c in hash_value))
    
    def test_is_chain_valid(self):
        # The initial chain should be valid
        self.assertTrue(self.blockchain.is_chain_valid(self.blockchain.chain))
        
        # Tamper with the chain
        self.blockchain.chain[1]['proof'] = 1
        
        # The chain should now be invalid
        self.assertFalse(self.blockchain.is_chain_valid(self.blockchain.chain))
    
    def test_add_certificate(self):
        # Add a certificate to the blockchain
        block_index = self.blockchain.add_certificate(self.certificate)
        
        # Check if the certificate was added to the blockchain
        cert, block = self.blockchain.find_certificate(self.certificate.certificate_id)
        
        self.assertIsNotNone(cert)
        self.assertIsNotNone(block)
        self.assertEqual(cert['certificate_id'], self.certificate.certificate_id)
    
    def test_verify_certificate(self):
        # Add a certificate to the blockchain
        block_index = self.blockchain.add_certificate(self.certificate)
        
        # Get the block hash
        block_hash = self.blockchain.chain[block_index]['hash']
        
        # Verify the certificate
        is_valid = self.blockchain.verify_certificate(self.certificate.certificate_id, block_hash)
        self.assertTrue(is_valid)
        
        # Verify with incorrect hash
        is_valid = self.blockchain.verify_certificate(self.certificate.certificate_id, 'incorrect_hash')
        self.assertFalse(is_valid)
        
        # Verify non-existent certificate
        is_valid = self.blockchain.verify_certificate('non_existent_id', block_hash)
        self.assertFalse(is_valid)

if __name__ == '__main__':
    unittest.main()
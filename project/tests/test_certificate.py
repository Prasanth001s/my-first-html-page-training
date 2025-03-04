import unittest
import sys
import os

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from certificate import Certificate

class TestCertificate(unittest.TestCase):
    def setUp(self):
        self.test_certificate_data = {
            'recipient_name': 'John Doe',
            'recipient_id': '12345',
            'issuer_name': 'Test University',
            'course_name': 'Blockchain 101',
            'description': 'Introduction to Blockchain Technology'
        }
    
    def test_certificate_creation(self):
        certificate = Certificate(self.test_certificate_data)
        
        # Check if all attributes are set correctly
        self.assertEqual(certificate.recipient_name, self.test_certificate_data['recipient_name'])
        self.assertEqual(certificate.recipient_id, self.test_certificate_data['recipient_id'])
        self.assertEqual(certificate.issuer_name, self.test_certificate_data['issuer_name'])
        self.assertEqual(certificate.course_name, self.test_certificate_data['course_name'])
        self.assertEqual(certificate.description, self.test_certificate_data['description'])
        
        # Check if certificate_id and hash are generated
        self.assertIsNotNone(certificate.certificate_id)
        self.assertIsNotNone(certificate.hash)
    
    def test_to_dict(self):
        certificate = Certificate(self.test_certificate_data)
        cert_dict = certificate.to_dict()
        
        # Check if all keys are present in the dictionary
        self.assertIn('certificate_id', cert_dict)
        self.assertIn('recipient_name', cert_dict)
        self.assertIn('recipient_id', cert_dict)
        self.assertIn('issuer_name', cert_dict)
        self.assertIn('issue_date', cert_dict)
        self.assertIn('course_name', cert_dict)
        self.assertIn('description', cert_dict)
        self.assertIn('hash', cert_dict)
        
        # Check if values are correct
        self.assertEqual(cert_dict['recipient_name'], self.test_certificate_data['recipient_name'])
        self.assertEqual(cert_dict['recipient_id'], self.test_certificate_data['recipient_id'])
        self.assertEqual(cert_dict['issuer_name'], self.test_certificate_data['issuer_name'])
        self.assertEqual(cert_dict['course_name'], self.test_certificate_data['course_name'])
        self.assertEqual(cert_dict['description'], self.test_certificate_data['description'])
    
    def test_from_dict(self):
        # Create a certificate
        original_cert = Certificate(self.test_certificate_data)
        
        # Convert to dictionary
        cert_dict = original_cert.to_dict()
        
        # Create a new certificate from the dictionary
        new_cert = Certificate.from_dict(cert_dict)
        
        # Check if all attributes are the same
        self.assertEqual(new_cert.certificate_id, original_cert.certificate_id)
        self.assertEqual(new_cert.recipient_name, original_cert.recipient_name)
        self.assertEqual(new_cert.recipient_id, original_cert.recipient_id)
        self.assertEqual(new_cert.issuer_name, original_cert.issuer_name)
        self.assertEqual(new_cert.issue_date, original_cert.issue_date)
        self.assertEqual(new_cert.course_name, original_cert.course_name)
        self.assertEqual(new_cert.description, original_cert.description)
        self.assertEqual(new_cert.hash, original_cert.hash)
    
    def test_hash_generation(self):
        certificate1 = Certificate(self.test_certificate_data)
        
        # Create a second certificate with the same data
        certificate2 = Certificate(self.test_certificate_data)
        
        # The hashes should be different because the certificate_ids are different
        self.assertNotEqual(certificate1.hash, certificate2.hash)
        
        # Create a certificate with different data
        different_data = self.test_certificate_data.copy()
        different_data['course_name'] = 'Different Course'
        certificate3 = Certificate(different_data)
        
        # The hash should be different
        self.assertNotEqual(certificate1.hash, certificate3.hash)

if __name__ == '__main__':
    unittest.main()
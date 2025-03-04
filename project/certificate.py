import hashlib
import uuid
from datetime import datetime

class Certificate:
    def __init__(self, data):
        """
        Initialize a new certificate
        
        Args:
            data (dict): Certificate data including recipient_name, recipient_id, 
                         issuer_name, course_name, and optional description
        """
        self.certificate_id = str(uuid.uuid4())
        self.recipient_name = data['recipient_name']
        self.recipient_id = data['recipient_id']
        self.issuer_name = data['issuer_name']
        self.issue_date = data.get('issue_date', datetime.utcnow().isoformat())
        self.course_name = data['course_name']
        self.description = data.get('description', '')
        
        # Generate hash of the certificate data
        self.hash = self._generate_hash()
    
    def _generate_hash(self):
        """
        Generate a hash of the certificate data
        """
        certificate_string = (
            f"{self.certificate_id}{self.recipient_name}{self.recipient_id}"
            f"{self.issuer_name}{self.issue_date}{self.course_name}{self.description}"
        )
        return hashlib.sha256(certificate_string.encode()).hexdigest()
    
    def to_dict(self):
        """
        Convert certificate to dictionary
        """
        return {
            'certificate_id': self.certificate_id,
            'recipient_name': self.recipient_name,
            'recipient_id': self.recipient_id,
            'issuer_name': self.issuer_name,
            'issue_date': self.issue_date,
            'course_name': self.course_name,
            'description': self.description,
            'hash': self.hash
        }
    
    @classmethod
    def from_dict(cls, data):
        """
        Create a certificate from dictionary data
        """
        certificate = cls({
            'recipient_name': data['recipient_name'],
            'recipient_id': data['recipient_id'],
            'issuer_name': data['issuer_name'],
            'course_name': data['course_name'],
            'description': data.get('description', '')
        })
        certificate.certificate_id = data['certificate_id']
        certificate.issue_date = data['issue_date']
        certificate.hash = data['hash']
        return certificate
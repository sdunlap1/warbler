"""Message model tests."""

import os
from unittest import TestCase
from models import db, User, Message

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app

db.create_all()

class MessageModelTestCase(TestCase):
    """Test model for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="HASHED_PASSWORD",
                                    image_url=None)

        self.testuser_id = 12345
        self.testuser.id = self.testuser_id

        db.session.commit()

    def tearDown(self):
        """Clean up fouled transactions."""
        db.session.rollback()

    def test_message_model(self):
        """Does the basic model work?"""
        msg = Message(text="Test message", user_id=self.testuser_id)

        db.session.add(msg)
        db.session.commit()

        self.assertEqual(len(self.testuser.messages), 1)
        self.assertEqual(self.testuser.messages[0].text, "Test message")

import os
from unittest import TestCase
from models import db, User

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app, CURR_USER_KEY

db.create_all()

class UserViewsTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()

    def tearDown(self):
        """Clean up fouled transactions."""
        db.session.rollback()

    def test_login(self):
        """Test login functionality."""

        with self.client as c:
            resp = c.post("/login", data={"username": "testuser", "password": "testuser"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Hello, testuser!", str(resp.data))

    def test_logout(self):
        """Test logout functionality."""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get("/logout", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("You have successfully logged out.", str(resp.data))

    # Add more tests following the same structure

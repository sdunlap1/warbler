"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py

import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False

class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        self.testuser_id = 12345
        self.testuser.id = self.testuser_id

        self.u1 = User.signup("abc", "test1@test.com", "password", None)
        self.u1_id = 67890
        self.u1.id = self.u1_id

        self.u2 = User.signup("efg", "test2@test.com", "password", None)
        self.u2_id = 22222
        self.u2.id = self.u2_id

        self.u3 = User.signup("hij", "test3@test.com", "password", None)
        self.u4 = User.signup("testing", "test4@test.com", "password", None)

        db.session.commit()

    def tearDown(self):
        """Clean up fouled transactions."""
        db.session.rollback()

    def test_add_message(self):
        """Can user add a message?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/messages/new", data={"text": "Hello"})

            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    def test_add_no_session(self):
        """Can user add a message without a session?"""

        with self.client as c:
            resp = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"Access unauthorized", resp.data)

    def test_add_invalid_user(self):
        """Can user add a message as another user?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 88888  # This user does not exist

            resp = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"Access unauthorized", resp.data)

    def test_message_show(self):
        """Can user view a message?"""

        m = Message(
            id=1234,
            text="a test message",
            user_id=self.testuser.id
        )

        db.session.add(m)
        db.session.commit()

        with self.client as c:
            resp = c.get(f'/messages/{m.id}')
            self.assertEqual(resp.status_code, 200)
            self.assertIn(m.text, str(resp.data))

    def test_invalid_message_show(self):
        """Can user view a non-existent message?"""

        with self.client as c:
            resp = c.get('/messages/99999999')
            self.assertEqual(resp.status_code, 404)

    def test_message_delete(self):
        """Can user delete their own message?"""

        m = Message(
            id=1234,
            text="a test message",
            user_id=self.testuser.id
        )
        db.session.add(m)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/messages/1234/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            m = Message.query.get(1234)
            self.assertIsNone(m)

    def test_unauthorized_message_delete(self):
        """Can user delete another user's message?"""

        u = User.signup(username="unauthorized",
                        email="unauthorized@test.com",
                        password="password",
                        image_url=None)
        db.session.commit()

        m = Message(
            id=1234,
            text="a test message",
            user_id=self.testuser.id
        )
        db.session.add(m)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = u.id

            resp = c.post("/messages/1234/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"Access unauthorized", resp.data)

            m = Message.query.get(1234)
            self.assertIsNotNone(m)

    def test_message_delete_no_auth(self):
        """Can user delete a message without authentication?"""

        m = Message(
            id=1234,
            text="a test message",
            user_id=self.testuser.id
        )
        db.session.add(m)
        db.session.commit()

        with self.client as c:
            resp = c.post("/messages/1234/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"Access unauthorized", resp.data)

            m = Message.query.get(1234)
            self.assertIsNotNone(m)

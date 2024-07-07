"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy.exc import IntegrityError

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

    def tearDown(self):
        """Clean up any fouled transaction."""
        db.session.rollback()

    def test_user_model(self):
        """Does basic model work?"""
        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    def test_repr(self):
        """Does the repr method work as expected?"""
        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        self.assertEqual(repr(u), f"<User #{u.id}: testuser, test@test.com>")

    def test_is_following(self):
        """Does is_following successfully detect when user1 is following user2?"""
        u1 = User.signup("user1", "user1@test.com", "password", None)
        u2 = User.signup("user2", "user2@test.com", "password", None)

        db.session.commit()

        u1.following.append(u2)
        db.session.commit()

        self.assertTrue(u1.is_following(u2))
        self.assertFalse(u2.is_following(u1))

    def test_is_followed_by(self):
        """Does is_followed_by successfully detect when user1 is followed by user2?"""
        u1 = User.signup("user1", "user1@test.com", "password", None)
        u2 = User.signup("user2", "user2@test.com", "password", None)

        db.session.commit()

        u1.followers.append(u2)
        db.session.commit()

        self.assertTrue(u1.is_followed_by(u2))
        self.assertFalse(u2.is_followed_by(u1))

    def test_valid_signup(self):
        """Does User.signup successfully create a new user given valid credentials?"""
        u = User.signup("validuser", "valid@test.com", "password", None)
        uid = 99999
        u.id = uid
        db.session.commit()

        u_test = User.query.get(uid)
        self.assertIsNotNone(u_test)
        self.assertEqual(u_test.username, "validuser")
        self.assertEqual(u_test.email, "valid@test.com")
        self.assertNotEqual(u_test.password, "password")
        # Bcrypt strings should start with $2b$
        self.assertTrue(u_test.password.startswith("$2b$"))

    def test_invalid_signup(self):
        """Does User.signup fail to create a new user if any of the validations (e.g. uniqueness, non-nullable fields) fail?"""
        invalid = User.signup(None, "test@test.com", "password", None)
        uid = 99999
        invalid.id = uid

        db.session.add(invalid)
        
        try:
            db.session.commit()
            self.fail("IntegrityError not raised")
        except IntegrityError as e:
            self.assertIn("null value in column \"username\"", str(e.orig))

    def test_authenticate(self):
        """Does User.authenticate successfully return a user when given a valid username and password?"""
        u = User.signup("validuser", "valid@test.com", "password", None)
        db.session.commit()

        auth_user = User.authenticate("validuser", "password")
        self.assertIsNotNone(auth_user)
        self.assertEqual(auth_user.username, "validuser")

    def test_invalid_username(self):
        """Does User.authenticate fail to return a user when the username is invalid?"""
        u = User.signup("validuser", "valid@test.com", "password", None)
        db.session.commit()

        self.assertFalse(User.authenticate("invaliduser", "password"))

    def test_wrong_password(self):
        """Does User.authenticate fail to return a user when the password is invalid?"""
        u = User.signup("validuser", "valid@test.com", "password", None)
        db.session.commit()

        self.assertFalse(User.authenticate("validuser", "wrongpassword"))

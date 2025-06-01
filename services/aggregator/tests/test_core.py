# from unittest.mock import MagicMock
#
# import pytest
#
# from tg_aggregator_src.core.registry import UserRegistry, FeedsRegistry
# from tg_aggregator_src.core.user import User
#
#
# @pytest.fixture
# def clear_registries():
#     """Fixture to clear registry data before each test"""
#     UserRegistry._users = {}
#     FeedsRegistry._feeds = {}
#     FeedsRegistry._feeds_users_count = {}
#
#
# class TestUserRegistry:
#     def test_register_user(self, clear_registries):
#         """Test that a user can be registered properly"""
#         user = User(1)
#         assert 1 in UserRegistry._users
#         assert UserRegistry._users[1] == user
#
#     def test_register_duplicate_user(self, clear_registries):
#         """Test that registering a duplicate user raises an error"""
#         User(1)  # First registration
#         with pytest.raises(ValueError):
#             User(1)  # Should raise ValueError for duplicate
#
#     def test_get_user(self, clear_registries):
#         """Test retrieving a user from the registry"""
#         user = User(1)
#         retrieved_user = UserRegistry.get_user(1)
#         assert user == retrieved_user
#
#     def test_get_nonexistent_user(self, clear_registries):
#         """Test that getting a non-existent user raises KeyError"""
#         with pytest.raises(KeyError):
#             UserRegistry.get_user(999)
#
#     def test_delete_user(self, clear_registries):
#         """Test that a user can be deleted from the registry"""
#         User(1)
#         UserRegistry.delete_user(1)
#         assert 1 not in UserRegistry._users
#
#     def test_delete_user_unsubscribes_feeds(self, clear_registries):
#         """Test that deleting a user unsubscribes them from all feeds"""
#         user = User(1)
#         user.subscribe("CNN")
#         user.subscribe("BBC")
#
#         # Verify feeds exist before deletion
#         assert "CNN" in FeedsRegistry._feeds
#         assert "BBC" in FeedsRegistry._feeds
#
#         UserRegistry.delete_user(1)
#
#         # Both feeds should be removed as no other users are subscribed
#         assert "CNN" not in FeedsRegistry._feeds
#         assert "BBC" not in FeedsRegistry._feeds
#
#
# class TestFeedsRegistry:
#     def test_create_feed(self, clear_registries):
#         """Test creating a new feed"""
#         feed = FeedsRegistry.create_or_get_feed("CNN")
#         assert "CNN" in FeedsRegistry._feeds
#         assert FeedsRegistry._feeds["CNN"] == feed
#         assert FeedsRegistry._feeds_users_count["CNN"] == 1
#
#     def test_get_existing_feed(self, clear_registries):
#         """Test getting an existing feed increments count"""
#         feed1 = FeedsRegistry.create_or_get_feed("CNN")
#         feed2 = FeedsRegistry.create_or_get_feed("CNN")
#         assert feed1 is feed2  # Same object returned
#         assert FeedsRegistry._feeds_users_count["CNN"] == 2
#
#     def test_release_feed(self, clear_registries):
#         """Test releasing a feed decrements count"""
#         FeedsRegistry.create_or_get_feed("CNN")
#         FeedsRegistry.create_or_get_feed("CNN")  # Count should be 2
#
#         FeedsRegistry.release_feed("CNN")
#         assert FeedsRegistry._feeds_users_count["CNN"] == 1
#         assert "CNN" in FeedsRegistry._feeds  # Feed still exists
#
#     def test_release_last_feed_reference(self, clear_registries):
#         """Test releasing the last reference removes the feed"""
#         FeedsRegistry.create_or_get_feed("CNN")
#         FeedsRegistry.release_feed("CNN")
#         assert "CNN" not in FeedsRegistry._feeds
#         assert "CNN" not in FeedsRegistry._feeds_users_count
#
#     def test_update_feed(self, clear_registries, monkeypatch):
#         """Test that updating a feed calls the update method"""
#         mock_update = MagicMock()
#         monkeypatch.setattr('tg_aggregator_src.core.feed.Feed.update', mock_update)
#
#         FeedsRegistry.create_or_get_feed("CNN")
#         FeedsRegistry.update_feed("CNN")
#         assert mock_update.call_count == 1
#
#     def test_update_all_feeds(self, clear_registries, monkeypatch):
#         """Test that updating all feeds calls update on each feed"""
#         mock_update = MagicMock()
#         monkeypatch.setattr('tg_aggregator_src.core.feed.Feed.update', mock_update)
#
#         FeedsRegistry.create_or_get_feed("CNN")
#         FeedsRegistry.create_or_get_feed("BBC")
#         FeedsRegistry.update_all_feeds()
#         assert mock_update.call_count == 2
#
#
# class TestUser:
#     def test_user_creation(self, clear_registries):
#         """Test user is created with correct ID"""
#         user = User(42)
#         assert user.id == 42
#         assert len(user._user_feeds) == 0
#
#     def test_subscribe(self, clear_registries):
#         """Test user can subscribe to a feed"""
#         user = User(1)
#         user.subscribe("CNN")
#         assert "CNN" in user._user_feeds
#         assert user._user_feeds["CNN"] == FeedsRegistry._feeds["CNN"]
#
#     def test_unsubscribe(self, clear_registries):
#         """Test user can unsubscribe from a feed"""
#         user = User(1)
#         user.subscribe("CNN")
#         user.unsubscribe("CNN")
#         assert "CNN" not in user._user_feeds
#
#     def test_unsubscribe_nonexistent(self, clear_registries):
#         """Test unsubscribing from a non-existent feed doesn't error"""
#         user = User(1)
#         # Should not raise any exception
#         user.unsubscribe("NonExistentFeed")
#
#     def test_get_user_feeds(self, clear_registries):
#         """Test retrieving user feeds"""
#         user = User(1)
#         user.subscribe("CNN")
#         user.subscribe("BBC")
#
#         feeds = user.get_users_feeds()
#         assert len(feeds) == 2
#         assert "CNN" in feeds
#         assert "BBC" in feeds
#
#
# class TestFeedSharing:
#     """Integration tests for interactions between users and feeds"""
#
#     def test_shared_feed_between_users(self, clear_registries):
#         """Test that multiple users can share the same feed object"""
#         user1 = User(1)
#         user2 = User(2)
#
#         user1.subscribe("CNN")
#         user2.subscribe("CNN")
#
#         # Both users should have the exact same feed object
#         assert user1._user_feeds["CNN"] is user2._user_feeds["CNN"]
#         assert FeedsRegistry._feeds_users_count["CNN"] == 2
#
#     def test_feed_only_removed_when_all_unsubscribe(self, clear_registries):
#         """Test that a feed is only removed when all users unsubscribe"""
#         user1 = User(1)
#         user2 = User(2)
#
#         user1.subscribe("CNN")
#         user2.subscribe("CNN")
#
#         user1.unsubscribe("CNN")
#         assert "CNN" in FeedsRegistry._feeds  # Feed should still exist
#
#         user2.unsubscribe("CNN")
#         assert "CNN" not in FeedsRegistry._feeds  # Feed should be gone

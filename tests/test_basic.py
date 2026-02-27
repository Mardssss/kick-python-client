# tests/test_basic.py

import pytest
from kick import KickClient, KickAuthenticationError


def test_client_can_be_instantiated():
    """Smoke test: can we even create the client object?"""
    client = KickClient(
        client_id="fake-id",
        client_secret="fake-secret",
        token_file="fake_tokens.json",
    )
    assert isinstance(client, KickClient)


def test_missing_token_raises_error():
    """
    If no token and no auth flow, accessing API should raise proper exception.
    (This is a partial test — real auth flow needs mocking/browser)
    """
    client = KickClient(
        client_id="fake",
        client_secret="fake",
        token_file="non_existing_file.json",
    )
    # Simulate no token and no refresh possible
    client.access_token = None
    client.refresh_token = None

    with pytest.raises(KickAuthenticationError):
        client.get_access_token(force_new=False)

def test_force_new_starts_flow():
    """
    When force_new=True, full OAuth flow should be attempted.
    (We mock webbrowser.open so it doesn't actually open browser during test)
    """
    import webbrowser
    original_open = webbrowser.open
    webbrowser.open = lambda url: None  # mock – do nothing

    try:
        client = KickClient("fake", "fake")
        client.access_token = None
        client.refresh_token = None

        # This should now go to _full_oauth_flow
        with pytest.raises(KickAuthenticationError):  # because fake creds → exchange fails
            client.get_access_token(scopes="user:read", force_new=True)

    finally:
        webbrowser.open = original_open  # restore
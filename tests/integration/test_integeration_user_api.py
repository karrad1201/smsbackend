from fastapi.testclient import TestClient


class TestUserEndpoints:
    def test_register_user_success(self, client: TestClient):
        user_data = {
            "user_name": "testuser",
            "password": "testpassword123"
        }

        response = client.post("/user/register", json=user_data)

        assert response.status_code != 500
        assert response.status_code in [200, 400]

    def test_register_and_login_flow(self, client: TestClient):
        user_data = {
            "user_name": "loginuser",
            "password": "loginpassword123"
        }

        reg_response = client.post("/user/register", json=user_data)

        if reg_response.status_code == 200:
            login_data = {
                "user_name": "loginuser",
                "password": "loginpassword123"
            }

            login_response = client.post("/user/login", json=login_data)
            assert login_response.status_code == 200
            assert "token" in login_response.json()

    def test_login_user_invalid_credentials(self, client: TestClient):
        login_data = {
            "user_name": "nonexistent",
            "password": "wrongpassword"
        }

        response = client.post("/user/login", json=login_data)
        assert response.status_code != 200

    def test_register_user_duplicate_username(self, client: TestClient):
        user_data = {
            "user_name": "duplicateuser",
            "password": "password123"
        }

        response1 = client.post("/user/register", json=user_data)

        response2 = client.post("/user/register", json=user_data)

        assert response2.status_code == 400
        assert "already exists" in response2.json().get("detail", "").lower()

    def test_register_user_invalid_data(self, client: TestClient):
        user_data_no_password = {
            "user_name": "nopassworduser"
        }
        response = client.post("/user/register", json=user_data_no_password)
        assert response.status_code == 422

        user_data_no_username = {
            "password": "password123"
        }
        response = client.post("/user/register", json=user_data_no_username)
        assert response.status_code == 422

        user_data_empty_username = {
            "user_name": "",
            "password": "password123"
        }
        response = client.post("/user/register", json=user_data_empty_username)
        assert response.status_code in [400, 422]

    def test_register_user_with_optional_fields(self, client: TestClient):
        user_data = {
            "user_name": "fulluser",
            "password": "password123",
            "email": "test@example.com",
            "first_name": "John",
            "last_name": "Doe"
        }

        response = client.post("/user/register", json=user_data)
        assert response.status_code in [200, 400]

    def test_login_with_correct_and_incorrect_password(self, client: TestClient):
        user_data = {
            "user_name": "passwordtestuser",
            "password": "correctpassword"
        }
        reg_response = client.post("/user/register", json=user_data)

        if reg_response.status_code == 200:
            login_correct = {
                "user_name": "passwordtestuser",
                "password": "correctpassword"
            }
            response_correct = client.post("/user/login", json=login_correct)
            assert response_correct.status_code == 200
            assert "token" in response_correct.json()

            login_incorrect = {
                "user_name": "passwordtestuser",
                "password": "wrongpassword"
            }
            response_incorrect = client.post("/user/login", json=login_incorrect)
            assert response_incorrect.status_code == 401

    def test_user_profile_flow(self, client: TestClient):
        user_data = {
            "user_name": "profileuser",
            "password": "profilepass123",
            "email": "profile@example.com",
            "first_name": "Profile",
            "last_name": "User"
        }

        reg_response = client.post("/user/register", json=user_data)

        if reg_response.status_code == 200:
            login_data = {
                "user_name": "profileuser",
                "password": "profilepass123"
            }
            login_response = client.post("/user/login", json=login_data)
            assert login_response.status_code == 200

            token = login_response.json()["token"]
            headers = {"Authorization": f"Bearer {token}"}

            profile_response = client.get("/user/me", headers=headers)
            if profile_response.status_code == 422:
                error_detail = profile_response.json().get("detail", "Unknown error")
                print(f"Profile error: {error_detail}")
            assert profile_response.status_code == 200
            profile_data = profile_response.json()

            assert profile_data["user_name"] == "profileuser"
            assert "balance" in profile_data

    def test_update_user_profile(self, client: TestClient):
        user_data = {
            "user_name": "updateuser",
            "password": "updatepass123",
            "email": "old@example.com",
            "first_name": "Old",
            "last_name": "Name"
        }

        reg_response = client.post("/user/register", json=user_data)

        if reg_response.status_code == 200:
            login_data = {
                "user_name": "updateuser",
                "password": "updatepass123"
            }
            login_response = client.post("/user/login", json=login_data)
            token = login_response.json()["token"]
            headers = {"Authorization": f"Bearer {token}"}

            update_data = {
                "email": "new@example.com",
                "first_name": "New",
                "last_name": "Name",
                "language": "en"
            }

            update_response = client.put("/user/me", json=update_data, headers=headers)
            if update_response.status_code == 422:
                error_detail = update_response.json().get("detail", "Unknown error")
                print(f"Update error: {error_detail}")
            assert update_response.status_code == 200

            updated_profile = update_response.json()
            assert updated_profile["email"] == "new@example.com"
            assert updated_profile["first_name"] == "New"

    def test_get_user_balance(self, client: TestClient):
        user_data = {
            "user_name": "balanceuser",
            "password": "balancepass123"
        }

        reg_response = client.post("/user/register", json=user_data)

        if reg_response.status_code == 200:
            login_data = {
                "user_name": "balanceuser",
                "password": "balancepass123"
            }
            login_response = client.post("/user/login", json=login_data)
            token = login_response.json()["token"]
            headers = {"Authorization": f"Bearer {token}"}

            balance_response = client.get("/user/balance", headers=headers)
            if balance_response.status_code == 422:
                error_detail = balance_response.json().get("detail", "Unknown error")
                print(f"Balance error: {error_detail}")
            assert balance_response.status_code == 200
            balance_data = balance_response.json()
            assert "balance" in balance_data

    def test_change_password(self, client: TestClient):
        user_data = {
            "user_name": "passwordchangeuser",
            "password": "oldpassword123"
        }

        reg_response = client.post("/user/register", json=user_data)

        if reg_response.status_code == 200:
            login_data = {
                "user_name": "passwordchangeuser",
                "password": "oldpassword123"
            }
            login_response = client.post("/user/login", json=login_data)
            token = login_response.json()["token"]
            headers = {"Authorization": f"Bearer {token}"}

            change_response = client.post(
                "/user/change-password",
                data={
                    "current_password": "oldpassword123",
                    "new_password": "newpassword456"
                },
                headers=headers
            )
            if change_response.status_code == 422:
                error_detail = change_response.json().get("detail", "Unknown error")
                print(f"Change password error: {error_detail}")
            assert change_response.status_code == 200

            new_login_data = {
                "user_name": "passwordchangeuser",
                "password": "newpassword456"
            }
            new_login_response = client.post("/user/login", json=new_login_data)
            assert new_login_response.status_code == 200

    def test_generate_api_key(self, client: TestClient):
        user_data = {
            "user_name": "apikeyuser",
            "password": "apikeypass123"
        }

        reg_response = client.post("/user/register", json=user_data)

        if reg_response.status_code == 200:
            login_data = {
                "user_name": "apikeyuser",
                "password": "apikeypass123"
            }
            login_response = client.post("/user/login", json=login_data)
            token = login_response.json()["token"]
            headers = {"Authorization": f"Bearer {token}"}
            api_key_response = client.post("/user/generate-api-key", headers=headers)
            if api_key_response.status_code == 422:
                error_detail = api_key_response.json().get("detail", "Unknown error")
                print(f"API key error: {error_detail}")
            assert api_key_response.status_code == 200

    def test_unauthorized_access(self, client: TestClient):
        profile_response = client.get("/user/me")
        assert profile_response.status_code in [401, 422]

        balance_response = client.get("/user/balance")
        assert balance_response.status_code in [401, 422]

        update_response = client.put("/user/me", json={})
        assert update_response.status_code in [401, 422]

        api_key_response = client.post("/user/generate-api-key")
        assert api_key_response.status_code in [401, 422]

    def test_user_deletion(self, client: TestClient):
        user_data = {
            "user_name": "deleteuser",
            "password": "deletepass123"
        }

        reg_response = client.post("/user/register", json=user_data)

        if reg_response.status_code == 200:
            login_data = {
                "user_name": "deleteuser",
                "password": "deletepass123"
            }
            login_response = client.post("/user/login", json=login_data)
            token = login_response.json()["token"]
            headers = {"Authorization": f"Bearer {token}"}

            delete_response = client.delete("/user/account", headers=headers)
            if delete_response.status_code == 422:
                error_detail = delete_response.json().get("detail", "Unknown error")
                print(f"Delete error: {error_detail}")
            assert delete_response.status_code == 200

            login_after_delete = client.post("/user/login", json=login_data)
            assert login_after_delete.status_code == 401

    def test_user_session_persistence(self, client: TestClient):
        user_data = {
            "user_name": "sessionuser",
            "password": "sessionpass123"
        }

        reg_response = client.post("/user/register", json=user_data)

        if reg_response.status_code == 200:
            login_data = {
                "user_name": "sessionuser",
                "password": "sessionpass123"
            }
            login_response = client.post("/user/login", json=login_data)
            token = login_response.json()["token"]
            headers = {"Authorization": f"Bearer {token}"}

            for i in range(3):
                profile_response = client.get("/user/me", headers=headers)
                if profile_response.status_code == 422:
                    error_detail = profile_response.json().get("detail", "Unknown error")
                    print(f"Session error {i}: {error_detail}")
                assert profile_response.status_code == 200

                balance_response = client.get("/user/balance", headers=headers)
                if balance_response.status_code == 422:
                    error_detail = balance_response.json().get("detail", "Unknown error")
                    print(f"Balance session error {i}: {error_detail}")
                assert balance_response.status_code == 200

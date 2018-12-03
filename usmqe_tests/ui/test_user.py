import pytest
from usmqe.base.application.implementations.web_ui import ViaWebUI
#LOGGER = pytest.get_logger('ui_user_testing', module=True)
import time
import copy
import json

from usmqe.api.tendrlapi import user as tendrlapi_user
from usmqe.api.tendrlapi.common import login, logout
from usmqe.base.application import Application


@pytest.mark.parametrize("role", ["normal", "limited"])
def test_user_crud(application, role, valid_session_credentials):
    user = application.collections.users.create(
        user_id="{}_user_auto".format(role),
        name="{} user".format(role),
        email="{}user@tendrl.org".format(role),
        notifications_on=False,
        password="1234567890",
        role=role
    )
    # assert user.exists
    test = tendrlapi_user.ApiUser(auth=valid_session_credentials)
    user_data = {
        "name": user.user_id,
        "username": user.name,
        "email": user.email,
        "role": user.role,
        "password": user.password,
        "email_notifications": user.notifications_on}

    # test.check_user(user_data)

    user.edit({
              "user_id": user.user_id,
              "users_name": user.name,
              "email": "edited_email_for_{}@tendrl.org".format(role),
              "password": user.password,
              "confirm_password": user.password,
              })
    assert not user.exists
    user.email = "edited_email_for_{}@tendrl.org".format(role)
    assert user.exists
    user.delete()
    assert not user.exists


def test_user_creation_password_invalid(application, valid_session_credentials, 
                                        valid_normal_user_data, invalid_password):
    user = application.collections.users.create(
        user_id=valid_normal_user_data["username"],
        name=valid_normal_user_data["name"],
        email=valid_normal_user_data["email"],
        notifications_on=valid_normal_user_data["email_notifications"],
        password=invalid_password,
        role=valid_normal_user_data["role"]
    )
    assert not user.exists
    test = tendrlapi_user.ApiUser(auth=valid_session_credentials)

    user_data_password_invalid = copy.deepcopy(valid_normal_user_data)
    user_data_password_invalid["username"] = invalid_password
    asserts = {
        "ok": False,
        "reason": 'Not Found',
        "status": 404}
    not_found = test.get_user(user_data_password_invalid["username"], asserts_in=asserts)
    assert "Not found" in str(not_found)


def test_edit_email_password(valid_new_normal_user, valid_normal_user_data):
    #new_data = {"email": "new_user_email@ya.ru"}
    #application_normal_user.collections.users.edit_logged_in_user(valid_normal_user_data[username], new_data)
    app1 = Application(hostname="ebondare-usm1-server.usmqe.lab.eng.brq.redhat.com",
                           scheme="http",
                           username=valid_normal_user_data["username"],
                           password=valid_normal_user_data["password"])
    view = ViaWebUI.navigate_to(app1.web_ui, "LoggedIn")
    new_data = {"email": "new_user_email@ya.ru", 
                "password": valid_normal_user_data["password"],
                "password_confirmation": valid_normal_user_data["password"] } 
    app1.collections.users.edit_logged_in_user(valid_normal_user_data["username"], new_data)
    app1.web_ui.browser_manager.quit()
    app2 = Application(hostname="ebondare-usm1-server.usmqe.lab.eng.brq.redhat.com",
                           scheme="http",
                           username=valid_normal_user_data["username"],
                           password=valid_normal_user_data["password"])
    view = ViaWebUI.navigate_to(app2.web_ui, "LoggedIn")
    app2.web_ui.browser_manager.quit()


def test_edit_email_only(valid_new_normal_user, valid_normal_user_data):
    #new_data = {"email": "new_user_email@ya.ru"}
    #application_normal_user.collections.users.edit_logged_in_user(valid_normal_user_data[username], new_data)
    app1 = Application(hostname="ebondare-usm1-server.usmqe.lab.eng.brq.redhat.com",
                           scheme="http",
                           username=valid_normal_user_data["username"],
                           password=valid_normal_user_data["password"])
    view = ViaWebUI.navigate_to(app1.web_ui, "LoggedIn")
    new_data = {"email": "new_user_email@ya.ru"}
    app1.collections.users.edit_logged_in_user(valid_normal_user_data["username"], new_data)
    app1.web_ui.browser_manager.quit()
    app2 = Application(hostname="ebondare-usm1-server.usmqe.lab.eng.brq.redhat.com",
                           scheme="http",
                           username=valid_normal_user_data["username"],
                           password=valid_normal_user_data["password"])
    try:
        view = ViaWebUI.navigate_to(app2.web_ui, "LoggedIn")
        app2.web_ui.browser_manager.quit()
    except:
        pytest.check(False,
                     issue='https://bugzilla.redhat.com/show_bug.cgi?id=1654623')

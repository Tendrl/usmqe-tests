import attr
from navmazing import NavigateToAttribute
from wait_for import wait_for

from usmqe.base.application.entities import BaseCollection, BaseEntity
from usmqe.base.application.views.user import UsersView
from usmqe.base.application.views.adduser import AddUserView
from usmqe.base.application.implementations.web_ui import TendrlNavigateStep, ViaWebUI


@attr.s
class User(BaseEntity):
    pass


@attr.s
class UsersCollection(BaseCollection):
    ENTITY = User

    def adduser(self, user_id, name, email, notifications_on, password, role):
        view = ViaWebUI.navigate_to(self, "All")
        wait_for(lambda: view.is_displayed, timeout=5)
        view.adduser.click()
        view = self.application.web_ui.create_view(AddUserView)
        changed = view.fill({"user_id": user_id,
                             "users_name": name,
                             "email": email,
                             "notifications_on": notifications_on,
                             "password": password,
                             "confirm_password": password,
                             "role": role})
        if changed:
            view.save_button.click()


@ViaWebUI.register_destination_for(UsersCollection, "All")
class UsersAll(TendrlNavigateStep):
    VIEW = UsersView
    prerequisite = NavigateToAttribute("application.web_ui", "LoggedIn")

    def step(self):
        self.parent.navbar.usermanagement.select_item("Users")

from tendrlui.entities.base import BaseEntity
from tendrlui.navigation import NavigateStep, navigator
from tendrlui.views.login import LoginView


class LoginEntity(BaseEntity):

    def login(self, values):
        view = self.navigate_to(self, 'NavigateToLogin')
        view.fill(values)
        view.submit.click()

    def logout(self):
        # fixme: not implemented
        pass


@navigator.register(LoginEntity)
class NavigateToLogin(NavigateStep):
    VIEW = LoginView

    def step(self, *args, **kwargs):
        # fixme: logout() if logged_in
        pass

    def am_i_here(self, *args, **kwargs):
        return self.view.is_displayed

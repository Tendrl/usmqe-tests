from widgetastic.widget import Text, TextInput
from widgetastic_patternfly import BreadCrumb

from tendrlui.views.common import BaseLoggedInView, SearchableViewMixin
from tendrlui.widgets import ActionsDropdown, SatTable


class ComputeProfilesView(BaseLoggedInView, SearchableViewMixin):
    title = Text("//h1[text()='Compute Profiles']")
    new = Text("//a[contains(@href, '/compute_profiles/new')]")
    table = SatTable(
        './/table',
        column_widgets={
            'Name': Text('./a'),
            'Actions': ActionsDropdown("./div[contains(@class, 'btn-group')]"),
        }
    )

    @property
    def is_displayed(self):
        return self.browser.wait_for_element(
            self.title, exception=False) is not None


class ComputeProfileCreateView(BaseLoggedInView):
    breadcrumb = BreadCrumb()
    name = TextInput(locator=".//input[@id='compute_profile_name']")
    submit = Text('//input[@name="commit"]')

    @property
    def is_displayed(self):
        breadcrumb_loaded = self.browser.wait_for_element(
            self.breadcrumb, exception=False)
        return (
                breadcrumb_loaded
                and self.breadcrumb.locations[0] == 'Compute Profiles'
                and self.breadcrumb.read() == 'Create Compute Profile'
        )


class ComputeProfileRenameView(ComputeProfileCreateView):

    @property
    def is_displayed(self):
        breadcrumb_loaded = self.browser.wait_for_element(
            self.breadcrumb, exception=False)
        return (
                breadcrumb_loaded
                and self.breadcrumb.locations[0] == 'Compute profiles'
                and self.breadcrumb.read() == 'Edit Compute profile'
        )

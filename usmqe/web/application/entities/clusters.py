import attr
import time
from navmazing import NavigateToAttribute, NavigateToSibling
from wait_for import wait_for
import pytest
from selenium.common.exceptions import NoSuchElementException

from usmqe.web.application.entities import BaseCollection, BaseEntity
from usmqe.web.application.views.cluster import ClustersView, UnmanageConfirmationView
from usmqe.web.application.views.cluster import UnmanageTaskSubmittedView, ExpandConfirmationView
from usmqe.web.application.views.host import ClusterHostsView
from usmqe.web.application.views.volume import ClusterVolumesView
from usmqe.web.application.views.task import ClusterTasksView, MainTaskEventsView
from usmqe.web.application.views.event import ClusterEventsView
from usmqe.web.application.views.importcluster import ImportClusterView, ImportTaskSubmittedView
from usmqe.web.application.implementations.web_ui import TendrlNavigateStep, ViaWebUI
from usmqe.web.application.entities.hosts import HostsCollection
from usmqe.web.application.entities.volumes import VolumesCollection
from usmqe.web.application.entities.tasks import TasksCollection
from usmqe.web.application.entities.events import EventsCollection
from usmqe.web.application.views.grafana import GrafanaClusterDashboard
from usmqe.web import tools


LOGGER = pytest.get_logger('clusters', module=True)


@attr.s
class Cluster(BaseEntity):
    """
    Each Cluster object has its own collections of hosts, volumes, tasks and events.
    """
    cluster_id = attr.ib()
    name = attr.ib()
    health = attr.ib()
    version = attr.ib()
    managed = attr.ib()
    hosts_number = attr.ib()
    status = attr.ib()
    # attributes below are not defined until cluster is imported
    volumes_number = attr.ib()
    alerts = attr.ib()
    profiling = attr.ib()

    _collections = {'hosts': HostsCollection,
                    'volumes': VolumesCollection,
                    'tasks': TasksCollection,
                    'events': EventsCollection}

    @property
    def hosts(self):
        return self.collections.hosts

    @property
    def volumes(self):
        return self.collections.volumes

    @property
    def tasks(self):
        return self.collections.tasks

    @property
    def events(self):
        return self.collections.events

    def update(self):
        """
        Update the cluster's attributes by reading them from Clusters list.
        """
        view = self.application.web_ui.create_view(ClustersView)
        wait_for(lambda: view.is_displayed,
                 timeout=300,
                 delay=2,
                 message="ClustersView wasn't displayed in time.\n" +
                 "Visible text: {}".format(view.browser.elements("*")[0].text))
        self.version = view.clusters(self.name).cluster_version.text
        self.managed = view.clusters(self.name).managed.text
        self.hosts_number = view.clusters(self.name).hosts.text
        self.status = view.clusters(self.name).status.text
        self.health = view.clusters(self.name).health
        if self.managed == "Yes":
            self.volumes_number = view.clusters(self.name).volumes.text
            self.alerts = view.clusters(self.name).alerts.text
            self.profiling = view.clusters(self.name).profiling.text
        else:
            self.volumes_number = None
            self.alerts = None
            self.profiling = None
        return (self.version,
                self.managed,
                self.hosts_number,
                self.status,
                self.health,
                self.volumes_number,
                self.alerts,
                self.profiling)

    def cluster_import(self, cluster_name=None, profiling="enable", view_progress=False):
        """
        Import the cluster and wait until it is listed as Ready to Use in the clusters list.
        Valid cluster name contains only alphanumeric and underscore characters.
        Possible profiling values are "enable", "disable" or "leaveAsIs".
        If import fails, save the screenshot of import log to ``screenshots`` directory.
        """
        view = ViaWebUI.navigate_to(self, "Import")
        wait_for(lambda: view.is_displayed,
                 timeout=30,
                 delay=2,
                 message="ClusterImport view wasn't displayed in time.\n" +
                 "Visible text: {}".format(view.browser.elements("*")[0].text))
        if cluster_name is not None:
            view.fill({"cluster_name": cluster_name,
                       "profiling": profiling})
            self.name = cluster_name
        else:
            view.fill({"profiling": profiling})
        view.confirm_import.click()
        view = self.application.web_ui.create_view(ImportTaskSubmittedView)
        wait_for(lambda: view.is_displayed,
                 timeout=30,
                 delay=2,
                 message="ImportTaskSubmittedView wasn't displayed in time.\n" +
                 "Visible text: {}".format(view.browser.elements("*")[0].text))
        if view_progress:
            view.view_progress.click()
            view = self.application.web_ui.create_view(MainTaskEventsView)
            wait_for(lambda: view.is_displayed,
                     timeout=100,
                     message="MainTaskEventsView wasn't displayed in time.\n" +
                     "Visible text: {}".format(view.browser.elements("*")[0].text))
            wait_for(lambda: view.import_status.text in {"Completed", "Failed"},
                     timeout=700,
                     message="Cluster import couldn't reach Comleted or Failed state in 700 " +
                     "seconds. Current status is {}".format(view.import_status.text))
            if view.import_status.text == "Completed":
                LOGGER.debug("Import task was completed")
                view.cluster_details.click()
                view = self.application.web_ui.create_view(ClusterHostsView)
                wait_for(lambda: view.is_displayed,
                         timeout=30,
                         delay=2,
                         message="ClusterHostsView wasn't displayed in time.\n" +
                         "Visible text: {}".format(view.browser.elements("*")[0].text))
                view.navbar.clusters.select_by_visible_text("All Clusters")
                view = self.application.web_ui.create_view(ClustersView)
                wait_for(lambda: view.is_displayed,
                         timeout=30,
                         delay=2,
                         message="ClustersView wasn't displayed in time\n" +
                         "Visible text: {}".format(view.browser.elements("*")[0].text))
            else:
                LOGGER.debug("Cluster import failed")
                tools.get_errors_from_log(self, view, "import", go_to_details=False)
                return False
        else:
            view.close_button.click()
        view = self.application.web_ui.create_view(ClustersView)
        wait_for(lambda: view.is_displayed,
                 timeout=30,
                 delay=2,
                 message="ClustersView wasn't displayed in time\n" +
                 "Visible text: {}".format(view.browser.elements("*")[0].text))
        wait_for(lambda: view.clusters(self.name).status.is_displayed,
                 timeout=40,
                 delay=2,
                 message="Cluster's status wasn't displayed in time\n" +
                 "Visible text: {}".format(view.browser.elements("*")[0].text))
        LOGGER.debug("Self.name: {}".format(self.name))
        wait_for(lambda: self.update()[3] in {"Ready to Use",
                                              "Import Failed. View Details"},
                 timeout=600,
                 delay=2,
                 message="Cluster import couldn't reach Comleted or Failed state in time\n" +
                 "Visible text: {}".format(view.browser.elements("*")[0].text))
        if self.status == "Import Failed. View Details":
            LOGGER.debug("Cluster import failed")
            tools.get_errors_from_log(self, view, "import", go_to_details=True)
            return False
        wait_for(lambda: self.update()[1] == "Yes",
                 timeout=200,
                 delay=3,
                 message="Cluster's Managed attribute couldn't reach ``Yes`` in time\n" +
                 "Visible text: {}".format(view.browser.elements("*")[0].text))
        LOGGER.debug("Cluster was updated")
        LOGGER.debug("Cluster status: {}".format(self.status))
        pytest.check(self.status == "Ready to Use",
                     "Cluster status: {}. Should be ``Ready to use``".format(self.status))
        return True

    def unmanage(self, cancel=False, original_id=None, view_progress=False):
        """
        Unmanage the cluster and wait until it's listed as Ready to Import in the clusters list.
        If the cluster has custom name, its original id is need it to find it in the clusters list
        after the unmanage.
        If unmanage fails, save the screenshot of unmanage log to ``screenshots`` directory.
        """
        if original_id is not None:
            self.cluster_id = original_id
        view = self.application.web_ui.create_view(ClustersView)
        wait_for(lambda: view.is_displayed,
                 timeout=50,
                 delay=2,
                 message="ClustersView wasn't displayed in time\n" +
                 "Visible text: {}".format(view.browser.elements("*")[0].text))
        hosts_number = self.hosts_number
        wait_for(lambda: view.clusters(self.name).actions.is_displayed,
                 timeout=5,
                 delay=2,
                 message="Cluster's Actions kebab wasn't displayed in time\n" +
                 "Visible text: {}".format(view.browser.elements("*")[0].text))
        view.clusters(self.name).actions.select("Unmanage")
        view = self.application.web_ui.create_view(UnmanageConfirmationView)
        wait_for(lambda: view.is_displayed,
                 timeout=50,
                 message="UnmanageConfirmationView wasn't displayed in time\n" +
                 "Visible text: {}".format(view.browser.elements("*")[0].text))
        view.unmanage.click()
        view = self.application.web_ui.create_view(UnmanageTaskSubmittedView)
        wait_for(lambda: view.is_displayed,
                 timeout=200,
                 message="UnmanageTaskSubmittedView wasn't displayed in time\n" +
                 "Visible text: {}".format(view.browser.elements("*")[0].text))
        if original_id is not None:
            self.name = original_id
        if view_progress:
            view.view_progress.click()
            view = self.application.web_ui.create_view(MainTaskEventsView)
            wait_for(lambda: view.is_displayed,
                     timeout=200,
                     delay=2,
                     message="Task progress view wasn't displayed in time\n" +
                     "Visible text: {}".format(view.browser.elements("*")[0].text))
            wait_for(lambda: view.import_status.text in {"Completed", "Failed"},
                     timeout=500,
                     message="Import task couldn't reach Completed or Failed state in time\n" +
                     "Visible text: {}".format(view.browser.elements("*")[0].text))
            if view.import_status.text == "Completed":
                view.navbar.clusters.select_by_visible_text("All Clusters")
                view = self.application.web_ui.create_view(ClustersView)
                wait_for(lambda: view.is_displayed,
                         timeout=100,
                         delay=2,
                         message="ClustersView wasn't displayed in time\n" +
                         "Visible text: {}".format(view.browser.elements("*")[0].text))
            else:
                LOGGER.debug("Cluster unmanage failed")
                tools.get_errors_from_log(self, view, "unmanage", go_to_details=False)
                return False
        else:
            view.close()
        view = self.application.web_ui.create_view(ClustersView)
        LOGGER.debug("Unmanage task was submitted")
        wait_for(lambda: view.is_displayed,
                 timeout=30,
                 delay=2,
                 message="ClustersView wasn't displayed in time\n" +
                 "Visible text: {}".format(view.browser.elements("*")[0].text))
        for _ in range(80):
            try:
                self.update()
                if (self.managed == "No" and
                        self.status == "Ready to Import"
                        and self.hosts_number == hosts_number):
                    break
                elif self.status == "Unmanage Failed. View Details":
                    LOGGER.debug("Cluster unmanage failed")
                    tools.get_errors_from_log(self, view, "unmanage", go_to_details=True)
                    return False
                else:
                    time.sleep(5)
            except NoSuchElementException:
                if self.cluster_id != self.name:
                    self.name = self.cluster_id
                time.sleep(5)
        LOGGER.debug("Cluster is managed: {}".format(self.managed))
        pytest.check(self.managed == "No",
                     "Managed attribute: {}. Should be 'No'".format(self.managed))
        LOGGER.debug("Cluster status: {}".format(self.status))
        pytest.check(self.status == "Ready to Import",
                     "Cluster's status: {}. Should be ``Ready to Import``".format(self.status))
        return True

    def enable_profiling(self, cancel=False):
        """
        Enable profiling for all volumes of the cluster and wait until cluster's Volume Profiling
        attribute changes to Enabled.
        """
        view = self.application.web_ui.create_view(ClustersView)
        wait_for(lambda: view.is_displayed,
                 timeout=30,
                 message="ClustersView wasn't displayed in time\n" +
                 "Visible text: {}".format(view.browser.elements("*")[0].text))
        view.clusters(self.name).actions.select("Enable Profiling")
        wait_for(lambda: self.update()[7] == "Enabled",
                 timeout=300,
                 delay=2,
                 message="Profiling hasn't changed to Enabled in 300 seconds\n" +
                 "Visible text: {}".format(view.browser.elements("*")[0].text))
        # profiling enabling process might not be over by this time
        time.sleep(5)

    def disable_profiling(self, cancel=False):
        """
        Disable profiling for all volumes of the cluster and wait until cluster's Volume Profiling
        attribute changes to Disabled.
        """
        view = self.application.web_ui.create_view(ClustersView)
        wait_for(lambda: view.is_displayed, timeout=30,
                 message="ClustersView wasn't displayed in time\n" +
                 "Visible text: {}".format(view.browser.elements("*")[0].text))
        view.clusters(self.name).actions.select("Disable Profiling")
        wait_for(lambda: self.update()[7] == "Disabled",
                 timeout=300,
                 delay=2,
                 message="Profiling hasn't changed to Disabled in 300 seconds\n" +
                 "Visible text: {}".format(view.browser.elements("*")[0].text))
        # profiling enabling process might not be over by this time
        time.sleep(5)

    def get_values_from_dashboard(self):
        """
        Click Dashboard button, read the selected data from Grafana dashboard,
        close the window with Grafana dashboard and return to main UI
        """
        view = ViaWebUI.navigate_to(self, "Dashboard")
        wait_for(lambda: view.is_displayed,
                 timeout=300,
                 delay=2,
                 message="Cluster Dashboard wasn't displayed in time\n" +
                 "Visible text: {}".format(view.browser.elements("*")[0].text))
        dashboard_values = {
            "cluster_name": view.cluster_name.text,
            "host_count": view.hosts_total.text.split(" ")[-1],
            "volume_count": view.volumes_total.text.split(" ")[-1],
            "cluster_health": view.cluster_health.text}
        while len(view.browser.selenium.window_handles) > 1:
            view.browser.selenium.close()
            view.browser.selenium.switch_to.window(view.browser.selenium.window_handles[-1])
        return dashboard_values

    def expand(self, cancel=False):
        """
        Expand cluster and wait until expansion process is complete.
        """
        view = self.application.web_ui.create_view(ClustersView)
        view.clusters(self.name).actions.select("Expand")
        view = self.application.web_ui.create_view(ExpandConfirmationView)
        wait_for(lambda: view.is_displayed,
                 timeout=3,
                 message="ExpandConfirmationView wasn't displayed in time\n" +
                 "Visible text: {}".format(view.browser.elements("*")[0].text))
        view.expand.click()
        time.sleep(20)
        for _ in range(40):
            self.update()
            if self.status == "Ready to Use":
                break
            else:
                time.sleep(5)
        pytest.check(self.status == "Ready to Use",
                     "Cluster's status: {}. Should be ``Ready to Use``".format(self.status))


@attr.s
class ClustersCollection(BaseCollection):
    ENTITY = Cluster

    def get_clusters(self):
        """
        Return the list of instantiated Cluster objects, their attributes read from Clusters page.
        If a cluster hasn't been imported, its volumes count, alerts count and profiling
        attributes are set to None.
        """
        view = ViaWebUI.navigate_to(self, "All")
        wait_for(lambda: view.is_displayed,
                 timeout=30,
                 message="ClustersView wasn't displayed in time\n" +
                 "Visible text: {}".format(view.browser.elements("*")[0].text))
        clusters_list = []
        for cluster_id in view.all_ids:
            if view.clusters(cluster_id).managed.text == "No":
                cluster = self.instantiate(
                    cluster_id,
                    cluster_id,
                    view.clusters(cluster_id).health,
                    view.clusters(cluster_id).cluster_version.text,
                    view.clusters(cluster_id).managed.text,
                    view.clusters(cluster_id).hosts.text,
                    view.clusters(cluster_id).status.text,
                    None,
                    None,
                    None)
                clusters_list.append(cluster)
            else:
                cluster = self.instantiate(
                    cluster_id,
                    cluster_id,
                    view.clusters(cluster_id).health,
                    view.clusters(cluster_id).cluster_version.text,
                    view.clusters(cluster_id).managed.text,
                    view.clusters(cluster_id).hosts.text,
                    view.clusters(cluster_id).status.text,
                    view.clusters(cluster_id).volumes.text,
                    view.clusters(cluster_id).alerts.text,
                    view.clusters(cluster_id).profiling.text)
                clusters_list.append(cluster)
        return clusters_list


@ViaWebUI.register_destination_for(ClustersCollection, "All")
class ClustersAll(TendrlNavigateStep):
    """
    Navigate to the list of clusters by choosing 'All clusters' in the context selector.
    """
    VIEW = ClustersView
    prerequisite = NavigateToAttribute("application.web_ui", "LoggedIn")

    def step(self):
        self.parent.navbar.clusters.select_by_visible_text("All Clusters")


@ViaWebUI.register_destination_for(Cluster, "Import")
class ClusterImport(TendrlNavigateStep):
    """
    Navigate to Cluster Import page by choosing Import option of the Clusters's kebab.
    """
    VIEW = ImportClusterView
    prerequisite = NavigateToAttribute("parent", "All")

    def step(self):
        self.parent.clusters(self.obj.name).import_button.click()


@ViaWebUI.register_destination_for(Cluster, "Hosts")
class ClusterHosts(TendrlNavigateStep):
    """
    Navigate to Cluster's Host page by clicking on Cluster's name/id in the context selector.
    """
    VIEW = ClusterHostsView
    prerequisite = NavigateToAttribute("parent", "All")

    def step(self):
        self.parent.navbar.clusters.select_by_visible_text(self.obj.name)


@ViaWebUI.register_destination_for(Cluster, "Volumes")
class ClusterVolumes(TendrlNavigateStep):
    """
    Navigate to Cluster's Volumes page by clicking Volumes in the vertical navigation bar.
    """
    VIEW = ClusterVolumesView
    prerequisite = NavigateToSibling("Hosts")

    def step(self):
        self.parent.vertical_navbar.volumes.click()


@ViaWebUI.register_destination_for(Cluster, "Tasks")
class ClusterTasks(TendrlNavigateStep):
    """
    Navigate to Cluster's Tasks page by clicking Tasks in the vertical navigation bar.
    """
    VIEW = ClusterTasksView
    prerequisite = NavigateToSibling("Hosts")

    def step(self):
        self.parent.vertical_navbar.tasks.click()


@ViaWebUI.register_destination_for(Cluster, "Events")
class ClusterEvents(TendrlNavigateStep):
    """
    Navigate to Cluster's Events page by clicking Events in the vertical navigation bar.
    """
    VIEW = ClusterEventsView
    prerequisite = NavigateToSibling("Hosts")

    def step(self):
        self.parent.vertical_navbar.events.click()


@ViaWebUI.register_destination_for(Cluster, "Dashboard")
class ClusterDashboard(TendrlNavigateStep):
    """
    Navigate to Cluster's grafana dashboard by clicking Dashboard button.
    """
    VIEW = GrafanaClusterDashboard
    prerequisite = NavigateToAttribute("parent", "All")

    def step(self):
        self.parent.clusters(self.obj.name).dashboard_button.click()
        self.view.browser.selenium.switch_to.window(self.view.browser.selenium.window_handles[1])

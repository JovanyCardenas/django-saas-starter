from django.test.runner import DiscoverRunner


class AppsTestRunner(DiscoverRunner):
    test_apps = [
        "apps.tenants.tests",
        "apps.rbac.tests",
        "apps.settings_panel.tests",
        "apps.files.tests",
    ]

    def build_suite(self, test_labels=None, extra_tests=None, **kwargs):
        if not test_labels:
            test_labels = self.test_apps
        return super().build_suite(test_labels, extra_tests=extra_tests, **kwargs)
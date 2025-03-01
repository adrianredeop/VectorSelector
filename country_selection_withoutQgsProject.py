from qgis.PyQt.QtWidgets import QAction, QWidget, QVBoxLayout, QDockWidget, QLabel, QScrollArea, QCheckBox, QInputDialog
from qgis.PyQt.QtGui import QIcon
from qgis.utils import iface
from qgis.PyQt.QtCore import Qt
import os

class CountrySelectionPlugin:
    def __init__(self, iface):
        """Initializes the plugin and prepares the icon."""
        self.iface = iface
        self.action = None
        self.dock_widget = None

    def initGui(self):
        """Adds an icon to the toolbar."""
        icon_path = os.path.join(os.path.dirname(__file__), "icon.png")
        self.action = QAction(QIcon(icon_path), "Start Selection", self.iface.mainWindow())
        self.action.triggered.connect(self.show_country_selection)

        # Add action to the toolbar and menu
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("&Selection", self.action)

    def unload(self):
        """Removes the icon and menu when the plugin is deactivated."""
        if self.action:
            self.iface.removePluginMenu("&Selection", self.action)
            self.iface.removeToolBarIcon(self.action)
        if self.dock_widget:
            self.iface.removeDockWidget(self.dock_widget)
            self.dock_widget.deleteLater()

    def show_country_selection(self):
        """Displays the selection dock widget."""
        layer, attribute_field = self.get_user_input()
        if not layer or not attribute_field:
            self.iface.messageBar().pushWarning("Error", "No valid selection made.")
            return

        attribute_values = sorted(set(
            feature[attribute_field] for feature in layer.getFeatures() if feature[attribute_field]
        ))

        if not attribute_values:
            self.iface.messageBar().pushWarning("Error", f"No values found in '{attribute_field}'!")
            return

        # Remove previous dock widgets
        existing_dock = self.iface.mainWindow().findChild(QDockWidget, "Selection")
        if existing_dock:
            self.iface.removeDockWidget(existing_dock)
            existing_dock.deleteLater()

        # Create a new dock widget
        self.dock_widget = QDockWidget("Selection", self.iface.mainWindow())
        self.dock_widget.setObjectName("Selection")
        country_widget = CountrySelectionWidget(layer, attribute_field, attribute_values)
        self.dock_widget.setWidget(country_widget)
        self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dock_widget)

    def get_user_input(self):
        """Prompts the user to select a layer and an attribute field."""
        layers = self.iface.mapCanvas().layers()
        if not layers:
            self.iface.messageBar().pushWarning("Error", "No layers in the project.")
            return None, None

        layer_names = [layer.name() for layer in layers]
        layer_name, ok = QInputDialog.getItem(None, "Select Layer", "Layer:", layer_names, 0, False)
        if not ok:
            return None, None

        selected_layer = next(layer for layer in layers if layer.name() == layer_name)
        field_names = [field.name() for field in selected_layer.fields()]
        field_name, ok = QInputDialog.getItem(None, "Select Field", "Field:", field_names, 0, False)
        if not ok:
            return None, None

        return selected_layer, field_name


class CountrySelectionWidget(QWidget):
    def __init__(self, layer, attribute_field, values, parent=None):
        """Creates a widget for selecting fields."""
        super().__init__(parent)
        self.layer = layer
        self.attribute_field = attribute_field
        self.values = values
        self.checkboxes = {}

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Select one or more fields:"))

        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()

        for value in self.values:
            checkbox = QCheckBox(str(value))
            checkbox.stateChanged.connect(self.update_selection)
            scroll_layout.addWidget(checkbox)
            self.checkboxes[value] = checkbox

        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
        self.setLayout(layout)

    def update_selection(self):
        """Updates the selection based on the checked boxes."""
        selected_values = [
            value for value, checkbox in self.checkboxes.items() if checkbox.isChecked()
        ]

        self.layer.removeSelection()

        if not selected_values:
            iface.messageBar().pushMessage("Info", "No fields selected.", level=0)
            return

        # Get the field type (QVariant types)
        field_index = self.layer.fields().indexOf(self.attribute_field)
        field_type = self.layer.fields().field(field_index).typeName().lower()

        # Check if the field is numeric
        is_numeric = field_type in ["int", "integer", "real", "double", "decimal", "float"]

        # Build the expression based on the field type
        if is_numeric:
            value_list = ', '.join(str(val) for val in selected_values)
        else:
            value_list = ', '.join(f"'{val}'" for val in selected_values)

        expression = f'"{self.attribute_field}" IN ({value_list})'

        # Select features and zoom
        self.layer.selectByExpression(expression)
        iface.mapCanvas().zoomToSelected(self.layer)
        iface.messageBar().pushSuccess("Selection", f"{len(selected_values)} fields selected and highlighted.")

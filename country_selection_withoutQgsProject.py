from qgis.PyQt.QtWidgets import QWidget, QVBoxLayout, QDockWidget, QLabel, QScrollArea, QCheckBox, QInputDialog
from qgis.utils import iface

# Function to get user input for layer and column
def get_user_input():
    # Get list of all layers
    layers = iface.mapCanvas().layers()
    layer_names = [layer.name() for layer in layers]
    
    # Ask user to select a layer
    layer_name, ok = QInputDialog.getItem(None, "Select Layer", "Layer:", layer_names, 0, False)
    if not ok or not layer_name:
        iface.messageBar().pushWarning("Fehler", "Keine Ebene ausgewählt!")
        exit()
    
    # Get the selected layer
    selected_layer = next(layer for layer in layers if layer.name() == layer_name)
    
    # Get list of all fields in the selected layer
    field_names = [field.name() for field in selected_layer.fields()]
    
    # Ask user to select a field
    field_name, ok = QInputDialog.getItem(None, "Select Field", "Field:", field_names, 0, False)
    if not ok or not field_name:
        iface.messageBar().pushWarning("Fehler", "Keine Spalte ausgewählt!")
        exit()
    
    return selected_layer, field_name

# Get user input
layer, ATTRIBUTE_FIELD = get_user_input()

# Länder aus der Spalte 'selected' sammeln
attribute_values = sorted(set(
    feature[ATTRIBUTE_FIELD] for feature in layer.getFeatures() if feature[ATTRIBUTE_FIELD]
))
if not attribute_values:
    iface.messageBar().pushWarning("Fehler", f"Keine Werte in '{ATTRIBUTE_FIELD}' gefunden!")
    exit()

# Widget mit Kontrollkästchen erstellen
class CountrySelectionWidget(QWidget):
    def __init__(self, layer, attribute_field, values, parent=None):
        super().__init__(parent)
        self.layer = layer
        self.attribute_field = attribute_field
        self.values = values
        self.checkboxes = {}
        
        # Layout & Widgets
        layout = QVBoxLayout()
        label = QLabel("Wähle ein oder mehrere Länder:")
        layout.addWidget(label)
        
        # Scroll-Bereich für viele Einträge
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        
        # Kontrollkästchen erstellen
        for value in self.values:
            checkbox = QCheckBox(value)
            checkbox.stateChanged.connect(self.update_selection)
            scroll_layout.addWidget(checkbox)
            self.checkboxes[value] = checkbox
        
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
        self.setLayout(layout)
        
    def update_selection(self):
        selected_values = [
            value for value, checkbox in self.checkboxes.items() if checkbox.isChecked()
        ]
        
        # Vorherige Auswahl entfernen
        self.layer.removeSelection()
        
        if not selected_values:
            iface.messageBar().pushMessage("Info", "Keine Länder ausgewählt.", level=0)
            return
        
        # Ausdruck für die Auswahl
        value_list = ', '.join(f"'{val}'" for val in selected_values)
        expression = f'"{self.attribute_field}" IN ({value_list})'
        
        # Features auswählen & Karte zoomen
        self.layer.selectByExpression(expression)
        iface.mapCanvas().zoomToSelected(self.layer)
        iface.messageBar().pushSuccess("Auswahl", f"{len(selected_values)} Länder ausgewählt und markiert.")

# Vorheriges DockWidget entfernen, falls vorhanden
existing_dock = iface.mainWindow().findChild(QDockWidget, "Länder-Auswahl")
if existing_dock:
    iface.removeDockWidget(existing_dock)
    existing_dock.deleteLater()

# DockWidget erstellen & hinzufügen
dock_widget = QDockWidget("Länder-Auswahl", iface.mainWindow())
dock_widget.setObjectName("Länder-Auswahl")
country_widget = CountrySelectionWidget(layer, ATTRIBUTE_FIELD, attribute_values)
dock_widget.setWidget(country_widget)
iface.addDockWidget(Qt.LeftDockWidgetArea, dock_widget)
import QtQuick 2.5
import QtQuick.Controls 1.4

// Defaulting to normal, non-underlined text, provide a state that allows the label's text
// to be bold and underlined.

Label {
    id: framLabelHighlightCapable
    states: [
        State { // Unnecessary because state = "" sets to default, but this might be clearer:
            name: "default"
            PropertyChanges { target: framLabelHighlightCapable; font.underline: "false"; font.bold: "false" }
        },
        State {
            name: "highlighted"
            PropertyChanges { target: framLabelHighlightCapable; font.underline: "true"; font.bold: "true" }
        }
    ]

    function highlight(enable) {
        state = enable ? "highlighted" : "default";
    }
}

import QtQuick 2.2

ListModel {
    ListElement {
        category: "Weights"
        validation: "Mixes all add up"
        status: "Success"
    }
    ListElement {
        category: "Weights"
        validation: "Mixes contain at least one weight"
        status: "Success"
    }
    ListElement {
        category: "Sampling"
        validation: "Barcodes are unique"
        status: "Fail"
    }
    ListElement {
        category: "Sampling"
        validation: "Species-specific length ranges"
        status: "Resolved"
    }
}
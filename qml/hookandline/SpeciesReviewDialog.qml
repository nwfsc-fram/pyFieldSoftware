import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Controls.Private 1.0
import QtQuick.Layouts 1.2
import QtQml.Models 2.2
import QtQuick.Dialogs 1.2
import QtQuick.Window 2.0

import "../common"

Dialog {
    id: dlg
    width: 1280
    height: 900
    title: "Review Species"

    modality: Qt.NonModal

    property int id: -1
    property int spacing: 20;
    property int speciesWidth: 120;
    property int tableWidth: 403;  // dlg.width/3 - 20;

    // Used for keep tracking if the best species is being changed by the user or not
    property bool aBestSpeciesClicked: false
    property bool bBestSpeciesClicked: false
    property bool cBestSpeciesClicked: false

    // Color Row Changing Flag for the three tables
    property bool aRowChanged: false
    property bool bRowChanged: false
    property bool cRowChanged: false

    property variant setId: null

    Component.onCompleted: {
        console.info((new Date()) + " - SpeciesReviewDialog.qml completed");
    }

    onVisibleChanged: {
        // If the dialog is closed, set the bestSpeciesClicked items to false
        if (!visible) {
            aBestSpeciesClicked = false;
            bBestSpeciesClicked = false;
            cBestSpeciesClicked = false;
        }
    }


    onRejected: {  }
    onAccepted: {  }

    Connections {
        target: speciesReview.anglerASpeciesModel
        onResetBestSpecies: bestSpeciesReset(speciesReview.anglerASpeciesModel);
    } // anglerASpeciesModel.onResetBestSpecies
    Connections {
        target: speciesReview.anglerBSpeciesModel
        onResetBestSpecies: bestSpeciesReset(speciesReview.anglerBSpeciesModel);
    } // anglerBSpeciesModel.onResetBestSpecies
    Connections {
        target: speciesReview.anglerCSpeciesModel
        onResetBestSpecies: bestSpeciesReset(speciesReview.anglerCSpeciesModel);
    } // anglerCSpeciesModel.onResetBestSpecies

    Connections {
        target: speciesReview.anglerASpeciesModel
        onRowColorUpdated: updateRowColor(model, row);
    } // anglerASpeciesModel.onRowColorUpdated
    Connections {
        target: speciesReview.anglerBSpeciesModel
        onRowColorUpdated: updateRowColor(model, row);
    } // anglerBSpeciesModel.onRowColorUpdated
    Connections {
        target: speciesReview.anglerCSpeciesModel
        onRowColorUpdated: updateRowColor(model, row);
    } // anglerCSpeciesModel.onRowColorUpdated

    function updateRowColor(model, row) {
        switch (model) {
            case "A":
                tvAnglerA.updateRow = !tvAnglerA.updateRow;
                break;
            case "B":
                tvAnglerB.updateRow = !tvAnglerB.updateRow;
                break;
            case "C":
                tvAnglerC.updateRow = !tvAnglerC.updateRow;
                break;
        }
    }

//    Connections {
//        target: speciesReview.anglerASpeciesModel
//        onBestSpeciesChanged: updateRowBestSpecies(model, row);
//    } // speciesReview.anglerASpeciesModel.onBestSpeciesChanged
//    Connections {
//        target: speciesReview.anglerBSpeciesModel
//        onBestSpeciesChanged: updateRowBestSpecies(model, row);
//    } // speciesReview.anglerBSpeciesModel.onBestSpeciesChanged
//    Connections {
//        target: speciesReview.anglerCSpeciesModel
//        onBestSpeciesChanged: updateRowBestSpecies(model, row);
//    } // speciesReview..anglerCSpeciesModel.onBestSpeciesChanged
//
//    function updateRowBestSpecies(model, row) {
//        var index = getRowBestSpecies(model, row);
//        var tvc;
//        switch (model) {
//            case "A":
////                tvAnglerA.toggleBestSpecies = !tvAnglerA.toggleBestSpecies;
//                tvc = tvAnglerA.tvcBestSpecies;
//                console.info('tvc = ' + tvc);
//                break;
//            case "B":
//                tvAnglerB.toggleBestSpecies = !tvAnglerB.toggleBestSpecies;
//                break;
//            case "C":
//                tvAnglerC.toggleBestSpecies = !tvAnglerC.toggleBestSpecies;
//                break;
//        }
//        if (tvc !== undefined) tvc.currentIndex = index;
//    }

    function bestSpeciesReset(model) {
        for (var i=0; i < model.count; i++) {
            model.setProperty(i, "bestSpecies", model.species[0]);
        }
    }

    function getTableModel(table) {
        var model;
        switch (table) {
            case "A":
                model = speciesReview.anglerASpeciesModel;
                break;
            case "B":
                model = speciesReview.anglerBSpeciesModel;
                break;
            case "C":
                model = speciesReview.anglerCSpeciesModel;
                break;
        }
        return model;
    }

    function getRowBestSpecies(table, row) {  // changed) {
//        logging.info('getting the best species: table=' + table + ', row=' + row + ', changed=' + changed);

        if (row === -1) return 0;
        var model = getTableModel(table);
        var rowData = model.get(row);
        var hmSpecies = rowData.hookMatrixSpecies;
        var csSpecies = rowData.cutterSpecies;
        var bestSpecies = rowData.bestSpecies;

        if (bestSpecies !== undefined) {

            return model.species.findIndex(function(e, i, a) {return e.text === bestSpecies});

        } else if ((hmSpecies === csSpecies) && (csSpecies !== undefined)) {

            return model.species.findIndex(function(e, i, a) {return e.text === csSpecies});
        }
        return 0;
    }

    function getRowColor(table, row, selected, alternate, changed) {

//        console.info(new Date() + " - getRowColor, table=" + table + ", row=" + row);

        // If no row, then return a default color
        if ((row === -1) || (row === undefined)) {
            return selected ? "skyblue" : (alternate ? "#eee" : "#fff")
        }

        var model = getTableModel(table);
        var rowData = model.get(row);

        // If the rowData does not exist for some reason, return a default color
        if (rowData === undefined) {
            return selected ? "skyblue" : (alternate ? "#eee" : "#fff")
        }

        // If rowColor exists, return it
        var rowColor = rowData.rowColor;
        if (rowColor) return rowColor;

        // If all else fails, return the default
        return selected ? "skyblue" : (alternate ? "#eee" : "#fff")
    }

    contentItem: Rectangle {
        color: SystemPaletteSingleton.window(true)
        RowLayout {
            id: rlOperations
            anchors.top: parent.top
            anchors.topMargin: 10
            anchors.left: parent.left
            anchors.leftMargin: 10
            Label {
                text: "Select Operation"
            }
            ComboBox {
                id: cbSetId
                width: parent.width
                anchors.verticalCenter: parent.verticalCenter
                model: speciesReview.operationsModel
                currentIndex: 0
                onCurrentIndexChanged: {
                    if (currentIndex >= 0) {
                        console.info('loadOperation called...')
                        setId = this.currentText;
                        speciesReview.loadOperation(setId);
                        aBestSpeciesClicked = false;
                        bBestSpeciesClicked = false;
                        cBestSpeciesClicked = false;

                        console.info((new Date()) + ' - loadOperation finished');
                    }
                }
            }
            Label { Layout.preferredWidth: 20; }
            Button {
                id: btnReloadSite
                text: "Reload Operation"
                onClicked: {
                    speciesReview.loadOperation(cbSetId.currentText);
                    aBestSpeciesClicked = false;
                    bBestSpeciesClicked = false;
                    cBestSpeciesClicked = false;
                }
            }
        }
        Label { height: 20 }
        RowLayout {
            id: rlTables
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: rlOperations.bottom
            anchors.topMargin: 10
            Layout.preferredHeight: dlg.height - rlOperations.height - 40
            width: dlg.width
            spacing: 20
            ColumnLayout {
                Label {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: "Angler A"
                    font.pixelSize: 24
                }
                TableView {
                    id: tvAnglerA
                    Layout.preferredHeight: dlg.height - rlOperations.height - 70
                    Layout.preferredWidth: tableWidth; //dlg.width/3 - 20;
                    model: speciesReview.anglerASpeciesModel
                    property bool updateRow: false
                    property bool toggleBestSpecies: false;
                    style: TableViewStyle {
                        headerDelegate: Rectangle {
                            height: 30
                            width: textItem.implicitWidth
                    //            color: "lightsteelblue"
                            gradient: Gradient {
                                GradientStop { position: 0.0; color: "white" }
                                GradientStop { position: 1.0; color: "lightgray" }
                            }
                            border.color: "gray"
                            border.width: 1
                            Text {
                                id: textItem
                                anchors.fill: parent
                                verticalAlignment: Text.AlignVCenter
                    //                    horizontalAlignment: styleData.textAlignment
                                horizontalAlignment: Text.AlignHCenter
                                anchors.leftMargin: 12
                                text: styleData.value
                                elide: Text.ElideRight
                                color: textColor
                                renderType: Text.NativeRendering
                                font.pixelSize: 11
                            }
                            Rectangle {
                                anchors.right: parent.right
                                anchors.top: parent.top
                                anchors.bottom: parent.bottom
                                anchors.bottomMargin: 1
                                anchors.topMargin: 1
                                width: 1
                    //                color: "#ccc"
                                gradient: Gradient {
                                    GradientStop { position: 0.0; color: "white" }
                                    GradientStop { position: 1.0; color: "#eee" }
                    //                    GradientStop { position: 1.0; color: "lightgray" }
                                }
                            }
                        }
                        rowDelegate: Rectangle {
                            height: 30
                            color: getRowColor("A", styleData.row, styleData.selected, styleData.alternate, tvAnglerA.updateRow);
                        }
                    }
                    TableViewColumn {
                        role: "adh"
                        title: "ADH"
                        width: 40
                    } // adh
                    TableViewColumn {
                        role: "hookMatrixSpecies"
                        title: "Hook Matrix"
                        width: speciesWidth
                    } // hookMatrixSpecies
                    TableViewColumn {
                        role: "cutterSpecies"
                        title: "Cutter"
                        width: speciesWidth
                    } // cutterSpecies
                    TableViewColumn {
                        id: tvcBestSpecies
                        role: "bestSpecies"
                        title: "Best"
                        width: speciesWidth
                        delegate: Item {
                            ComboBox {
                                width: parent.width
                                anchors.verticalCenter: parent.verticalCenter
                                model: speciesReview.anglerASpeciesModel.species
//                                currentIndex: getRowBestSpecies("A", styleData.row)
                                currentIndex: ((styleData.row >= 0) &&
                                    (speciesReview.anglerASpeciesModel.get(styleData.row).bestSpeciesIndex !== undefined)) ?
                                    speciesReview.anglerASpeciesModel.get(styleData.row).bestSpeciesIndex : 0;
                                onCurrentIndexChanged: {

//                                    console.info(new Date() + " - A index changed");

                                    if (cbSetId.currentText === "Set ID") {
                                        currentIndex = 0;
                                        return;
                                    }

                                    if ((aBestSpeciesClicked) && (currentIndex >=0)) {
                                        if (styleData.row >= 0) {
                                            var rowData = speciesReview.anglerASpeciesModel.get(styleData.row);
                                            speciesReview.anglerASpeciesModel.updateBestSpecies(setId, rowData.adh,
                                                    speciesReview.anglerASpeciesModel.species[currentIndex].text);
                                            aBestSpeciesClicked = false;
                                        }
                                    }
                                }
                                MouseArea {
                                    anchors.fill: parent
                                    onWheel: {
                                        // do nothing
                                    }
                                    onPressed: {
                                        // propogate to ComboBox
                                        mouse.accepted = false;
                                        aBestSpeciesClicked = true;
                                    }
                                    onReleased: {
                                        // propogate to ComboBox
                                        mouse.accepted = false;
                                        console.info('firing onReleased - does not ever appear to fire');
                                        aBestSpeciesClicked = false;
                                    }
                                }  // Needed to disable onWheel mouse events
                            }
                        }
                    } // bestSpecies
                } // tvAnglerA
            } // Angler A
            ColumnLayout {
                Label {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: "Angler B"
                    font.pixelSize: 24
                }
                TableView {
                    id: tvAnglerB
                    Layout.preferredHeight: dlg.height - rlOperations.height - 70
                    Layout.preferredWidth: tableWidth; //dlg.width/3 - 20;
                    model: speciesReview.anglerBSpeciesModel
                    property bool updateRow: false
                    property bool toggleBestSpecies: false;
                    style: TableViewStyle {
                        headerDelegate: Rectangle {
                            height: 30
                            width: textItem.implicitWidth
                    //            color: "lightsteelblue"
                            gradient: Gradient {
                                GradientStop { position: 0.0; color: "white" }
                                GradientStop { position: 1.0; color: "lightgray" }
                            }
                            border.color: "gray"
                            border.width: 1
                            Text {
                                id: textItem
                                anchors.fill: parent
                                verticalAlignment: Text.AlignVCenter
                    //                    horizontalAlignment: styleData.textAlignment
                                horizontalAlignment: Text.AlignHCenter
                                anchors.leftMargin: 12
                                text: styleData.value
                                elide: Text.ElideRight
                                color: textColor
                                renderType: Text.NativeRendering
                                font.pixelSize: 11
                            }
                            Rectangle {
                                anchors.right: parent.right
                                anchors.top: parent.top
                                anchors.bottom: parent.bottom
                                anchors.bottomMargin: 1
                                anchors.topMargin: 1
                                width: 1
                    //                color: "#ccc"
                                gradient: Gradient {
                                    GradientStop { position: 0.0; color: "white" }
                                    GradientStop { position: 1.0; color: "#eee" }
                    //                    GradientStop { position: 1.0; color: "lightgray" }
                                }
                            }
                        }
                        rowDelegate: Rectangle {
                            height: 30
                            color: getRowColor("B", styleData.row, styleData.selected, styleData.alternate, tvAnglerB.updateRow);
                        }
                    }
                    TableViewColumn {
                        role: "adh"
                        title: "ADH"
                        width: 40
                    } // adh
                    TableViewColumn {
                        role: "hookMatrixSpecies"
                        title: "Hook Matrix"
                        width: speciesWidth
                    } // hookMatrixSpecies
                    TableViewColumn {
                        role: "cutterSpecies"
                        title: "Cutter"
                        width: speciesWidth
                    } // cutterSpecies
                    TableViewColumn {
                        role: "bestSpecies"
                        title: "Best"
                        width: speciesWidth
                        delegate: Item {
                            ComboBox {
                                width: parent.width
                                anchors.verticalCenter: parent.verticalCenter
                                model: speciesReview.anglerBSpeciesModel.species
//                                currentIndex: getRowBestSpecies("B", styleData.row);
                                currentIndex: (styleData.row >= 0) ?
                                    speciesReview.anglerBSpeciesModel.get(styleData.row).bestSpeciesIndex : 0;
                                onCurrentIndexChanged: {
                                    if (cbSetId.currentText === "Set ID") {
                                        currentIndex = 0;
                                        return;
                                    }
                                    if ((bBestSpeciesClicked) && (currentIndex >=0)) {
                                        if (styleData.row >= 0) {
                                            var rowData = speciesReview.anglerBSpeciesModel.get(styleData.row);
                                            speciesReview.anglerBSpeciesModel.updateBestSpecies(setId, rowData.adh,
                                                    speciesReview.anglerBSpeciesModel.species[currentIndex].text);
                                            bBestSpeciesClicked = false;
                                        }
                                    }
                                }
                                MouseArea {
                                    anchors.fill: parent
                                    onWheel: {
                                        // do nothing
                                    }
                                    onPressed: {
                                        // propogate to ComboBox
                                        mouse.accepted = false;
                                        bBestSpeciesClicked = true;
                                    }
                                    onReleased: {
                                        // propogate to ComboBox
                                        mouse.accepted = false;
                                        bBestSpeciesClicked = false;
                                    }
                                }  // Needed to disable onWheel mouse events
                            } // ComboBox
                        } // Item delegate
                    } // bestSpecies
                } // tvAnglerB
            } // Angler B
            ColumnLayout {
                Label {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: "Angler C"
                    font.pixelSize: 24
                }
                TableView {
                    id: tvAnglerC
                    Layout.preferredHeight: dlg.height - rlOperations.height - 70
                    Layout.preferredWidth: tableWidth;
                    model: speciesReview.anglerCSpeciesModel
                    property bool updateRow: false
                    property bool toggleBestSpecies: false;
                    style: TableViewStyle {
                        headerDelegate: Rectangle {
                            height: 30
                            width: textItem.implicitWidth
                    //            color: "lightsteelblue"
                            gradient: Gradient {
                                GradientStop { position: 0.0; color: "white" }
                                GradientStop { position: 1.0; color: "lightgray" }
                            }
                            border.color: "gray"
                            border.width: 1
                            Text {
                                id: textItem
                                anchors.fill: parent
                                verticalAlignment: Text.AlignVCenter
                    //                    horizontalAlignment: styleData.textAlignment
                                horizontalAlignment: Text.AlignHCenter
                                anchors.leftMargin: 12
                                text: styleData.value
                                elide: Text.ElideRight
                                color: textColor
                                renderType: Text.NativeRendering
                                font.pixelSize: 11
                            }
                            Rectangle {
                                anchors.right: parent.right
                                anchors.top: parent.top
                                anchors.bottom: parent.bottom
                                anchors.bottomMargin: 1
                                anchors.topMargin: 1
                                width: 1
                    //                color: "#ccc"
                                gradient: Gradient {
                                    GradientStop { position: 0.0; color: "white" }
                                    GradientStop { position: 1.0; color: "#eee" }
                    //                    GradientStop { position: 1.0; color: "lightgray" }
                                }
                            }
                        }
                        rowDelegate: Rectangle {
                            height: 30
                            color: getRowColor("C", styleData.row, styleData.selected, styleData.alternate, tvAnglerC.updateRow);
                        }
                    }
                    TableViewColumn {
                        role: "adh"
                        title: "ADH"
                        width: 40
                    } // adh
                    TableViewColumn {
                        role: "hookMatrixSpecies"
                        title: "Hook Matrix"
                        width: speciesWidth
                    } // hookMatrixSpecies
                    TableViewColumn {
                        role: "cutterSpecies"
                        title: "Cutter"
                        width: speciesWidth
                    } // cutterSpecies
                    TableViewColumn {
                        role: "bestSpecies"
                        title: "Best"
                        width: speciesWidth
                        delegate: Item {
                            ComboBox {
                                width: parent.width
                                anchors.verticalCenter: parent.verticalCenter
                                model: speciesReview.anglerCSpeciesModel.species
//                                currentIndex: getRowBestSpecies("C", styleData.row);
                                currentIndex: (styleData.row >= 0) ?
                                    speciesReview.anglerCSpeciesModel.get(styleData.row).bestSpeciesIndex : 0;
                                onCurrentIndexChanged: {
                                    if (cbSetId.currentText === "Set ID") {
                                        currentIndex = 0;
                                        return;
                                    }
                                    if ((cBestSpeciesClicked) && (currentIndex >=0)) {
                                        if (styleData.row >= 0) {
                                            var rowData = speciesReview.anglerCSpeciesModel.get(styleData.row);
                                            speciesReview.anglerCSpeciesModel.updateBestSpecies(setId, rowData.adh,
                                                    speciesReview.anglerCSpeciesModel.species[currentIndex].text);
                                            cBestSpeciesClicked = false;
                                        }
                                    }
                                }
                                MouseArea {
                                    anchors.fill: parent
                                    onWheel: {
                                        // do nothing
                                    }
                                    onPressed: {
                                        // propogate to ComboBox
                                        mouse.accepted = false;
                                        cBestSpeciesClicked = true;
                                    }
                                    onReleased: {
                                        // propogate to ComboBox
                                        mouse.accepted = false;
                                        cBestSpeciesClicked = false;
                                    }
                                }  // Needed to disable onWheel mouse events
                            } // ComboBox
                        } // Item delegate
                    } // bestSpecies
                } // tvAnglerC
            } // Angler C
        }
        Keys.onEnterPressed: dlg.accept()
        Keys.onReturnPressed: dlg.accept()
        Keys.onEscapePressed: dlg.reject()
        Keys.onBackPressed: dlg.reject()
    }
}

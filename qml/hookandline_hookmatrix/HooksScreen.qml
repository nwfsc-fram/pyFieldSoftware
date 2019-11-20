import QtQuick 2.7
//import QtQuick.Controls 1.3
import QtQuick.Controls 2.2
import QtQuick.Layouts 1.1
import QtQuick.Controls.Styles 1.2
import QtQuick.Controls.Private 1.0

Item {
    property double aStartSeconds;
    property double bStartSeconds;
    property double cStartSeconds;
    property variant currentHook: hook5;
    property int buttonWidth: 160
    property int buttonHeight: 80

    property alias hook5: hook5;
    property alias hook4: hook4;
    property alias hook3: hook3;
    property alias hook2: hook2;
    property alias hook1: hook1;

    property string clickedColor: "yellow"

    property variant hooksMap:
        {5: hook5.tfHook, 4: hook4.tfHook, 3: hook3.tfHook, 2: hook2.tfHook,
            1: hook1.tfHook}

    state: "short species list"

    Connections {
        target: labelPrinter
        onPrinterStatusReceived: receivedPrinterStatus(comport, success, message)
    }
    function receivedPrinterStatus(comport, success, message) {
        var result = success ? "success" : "failed"
        dlgOkay.message = "Print job to " + comport + " status: " + result;
        if (result === "failed") {
            dlgOkay.action = "Please try again";
        } else {
            dlgOkay.action = "Well done, continue on matey";
        }
        dlgOkay.open();
    }

    Connections {
        target: hook5
        onCurrentHookChanged: changeCurrentHook(hookNumber);
    } // onCurrentHookChanged
    Connections {
        target: hook4
        onCurrentHookChanged: changeCurrentHook(hookNumber);
    } // onCurrentHookChanged
    Connections {
        target: hook3
        onCurrentHookChanged: changeCurrentHook(hookNumber);
    } // onCurrentHookChanged
    Connections {
        target: hook2
        onCurrentHookChanged: changeCurrentHook(hookNumber);
    } // onCurrentHookChanged
    Connections {
        target: hook1
        onCurrentHookChanged: changeCurrentHook(hookNumber);
    } // onCurrentHookChanged
    Connections {
        target: hooks
        onHooksSelected: populateHooks(results)
    } // hooks.onHooksSelected
    function populateHooks(results) {
        console.info('popuplateHooks: ' + JSON.stringify(results));
        var key;
        var item;
        for (key in results) {
            item = hooksMap[key];
            item.text = results[key] ? results[key] : "";
        }
        for (key in hooksMap) {
            hooksMap[key].cursorPosition = 0;
        }
        hook5.tfHook.color = "yellow";
        hook5.tfHook.forceActiveFocus();
        stateMachine.hook = "5";
    }

    Connections {
        target: framFooter
        onClickedSpeciesList: switchSpeciesList(speciesList)
    } // framFoot.onClickedSpeciesList
    function switchSpeciesList(speciesList) {
        switch (speciesList) {
            case "Full List":
                state = "full species list";
                break;
            case "Short List":
                state = "short species list";
                break;
        }
    }
    function padZeros(value) { return (value < 10) ? "0" + value : value; }
    function formatTime(value) {
        var minutes = padZeros(Math.floor(value/60))
        var seconds = padZeros(Math.round(value%60))
        return minutes + ":" + seconds;
    }
    function changeCurrentHook(value) {
        switch (value) {
            case "5":
                currentHook = hook5;
                break;
            case "4":
                currentHook = hook4;
                break;
            case "3":
                currentHook = hook3;
                break;
            case "2":
                currentHook = hook2;
                break;
            case "1":
                currentHook = hook1;
                break;
        }
        stateMachine.hook = value;
    }
    function populateHook(species) {

    //    if (currentHook == "") return;
        if (currentHook === null) return;

        hooks.saveHook(currentHook.hookNumber, species);
        switch (currentHook) {
            case hook5:
                hook5.tfHook.text = species;
                hook5.tfHook.cursorPosition = 0;

                hook4.tfHook.focus = true;
                hook4.tfHook.cursorPosition = 0;
                hook4.tfHook.color = clickedColor;

                currentHook = hook4;
                break;
            case hook4:
                hook4.tfHook.text = species;
                hook4.tfHook.cursorPosition = 0;

                hook3.tfHook.focus = true;
                hook3.tfHook.cursorPosition = 0;
                hook3.tfHook.color = clickedColor;
                currentHook = hook3;
                break;
            case hook3:
                hook3.tfHook.text = species;
                hook3.tfHook.cursorPosition = 0;

                hook2.tfHook.focus = true;
                hook2.tfHook.cursorPosition = 0;
                hook2.tfHook.color = clickedColor;
                currentHook = hook2;
                break;
            case hook2:
                hook2.tfHook.text = species;
                hook2.tfHook.cursorPosition = 0;
                hook1.tfHook.focus = true;
//                hook1.tfHook.selectAll();
                hook1.tfHook.cursorPosition = 0;
                hook1.tfHook.color = clickedColor;
                currentHook = hook1;
                break;
            case hook1:
                hook1.tfHook.text = species;
                hook1.tfHook.cursorPosition = 0;
                hook1.tfHook.color = clickedColor;
                break;
        }
    }
    function getModelSubset(index) {
        console.info('index: ' + index);
        var model = hooks.fullSpeciesListModel.getSubset(index);
        console.info(JSON.stringify(model));
        return model;
    }
    function getSwipeViewComponent(textStr) {
        console.info(textStr);
        if (textStr === "") {
            return cpLabel;
        } else {
            return cpButton;
        }
    }
    Component {
        id: cpLabel
        Label {}
    }
    Component {
        id: cpButton
        BackdeckButton {
            property string textStr: ""
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            text: textStr.length > 13 ?
                    textStr.replace(" ", "\n") :
                    textStr;
            onClicked: {
                populateHook(text.replace('\n', ' '));
            }
        }
    }

    Header {
        id: framHeader
        title: "Drop " + stateMachine.drop + " - Angler " + stateMachine.angler + " - " +
                        stateMachine.anglerName + " - Hooks"
        height: 50
    }
    ColumnLayout {
        id: clHooks
        spacing: 20
        anchors.left: parent.left
        anchors.leftMargin: 10
        anchors.verticalCenter: parent.verticalCenter
        HookItem {
            id: hook5;
            hookNumber: "5"
        } // hook 5
        HookItem {
            id: hook4;
            hookNumber: "4"
        } // hook 4
        HookItem {
            id: hook3;
            hookNumber: "3"
        } // hook 3
        HookItem {
            id: hook2;
            hookNumber: "2"
        } // hook 2
        HookItem {
            id: hook1;
            hookNumber: "1"
        } // hook 1
    } // clHooks
    GridLayout {
        id: glShortSpeciesList
        rows: 7
        columns: 4
        rowSpacing: 10
        columnSpacing: 10
        flow: GridLayout.TopToBottom
        anchors.left: clHooks.right
        anchors.leftMargin: 20
        anchors.top: clHooks.top

        // column 1
        BackdeckButton {
            id: btnBoc
            text: qsTr("Bocaccio")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            onClicked: {
                populateHook(text);
            }
        } // btnBOC
        BackdeckButton {
            id: btnVermilion
            text: qsTr("Vermilion")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            onClicked: {
                populateHook(text);
            }
        } // btnVermilion
        BackdeckButton {
            id: btnBaitBack
            text: qsTr("Bait Back")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            onClicked: {
                populateHook(text);
            }
        } // btnBaitBack
        BackdeckButton {
            id: btnNoBait
            text: qsTr("No Bait")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            onClicked: {
                populateHook(text);
            }
        } // btnNoBait
        BackdeckButton {
            id: btnNoHook
            text: qsTr("No Hook")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            onClicked: {
                populateHook(text);
            }
        } // btnNoHook
        BackdeckButton {
            id: btnMultipleHook
            text: qsTr("Multiple Hook")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            onClicked: {
                populateHook(text);
            }
        } // btnMultipleHook
        BackdeckButton {
            id: btnUndeployed
            text: qsTr("Undeployed")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            onClicked: {
                populateHook(text);
            }
        } // btnMultipleHook

        // Column 2
        BackdeckButton {
            id: btnBank
            text: qsTr("Bank")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            onClicked: {
                populateHook(text);
            }
        } // btnBank
        BackdeckButton {
            id: btnBlue
            text: qsTr("Blue")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            onClicked: {
                populateHook(text);
            }
        } // btnBlue
        BackdeckButton {
            id: btnCanary
            text: qsTr("Canary")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            onClicked: {
                populateHook(text);
            }
        } // btnCanary
        BackdeckButton {
            id: btnChilipepper
            text: qsTr("Chilipepper")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            onClicked: {
                populateHook(text);
            }
        } // btnChilipepper
        BackdeckButton {
            id: btnCopper
            text: qsTr("Copper")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            onClicked: {
                populateHook(text);
            }
        } // btnCopper
        BackdeckButton {
            id: btnCowcod
            text: qsTr("Cowcod")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            onClicked: {
                populateHook(text);
            }
        } // btnCowcod
        BackdeckButton {
            id: btnGreenblotched
            text: qsTr("Greenblotched")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            onClicked: {
                populateHook(text);
            }
        } // btnGreenblotched

        // Column 3
        BackdeckButton {
            id: btnGreenSpot
            text: qsTr("GSpot")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            onClicked: {
                populateHook(text);
            }
        } // btnGreenSpot
        BackdeckButton {
            id: btnGreenstriped
            text: qsTr("Greenstriped")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            onClicked: {
                populateHook(text);
            }
        } // btnGreenstriped
        BackdeckButton {
            id: btnHalfbanded
            text: qsTr("Halfbanded")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            onClicked: {
                populateHook(text);
            }
        } // btnHalfbanded
        BackdeckButton {
            id: btnLingcod
            text: qsTr("Lingcod")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            onClicked: {
                populateHook(text);
            }
        } // btnLingcod
        BackdeckButton {
            id: btnOceanWhitefish
            text: qsTr("Ocean\nWhitefish")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            onClicked: {
                populateHook(text);
            }
        } // btnOceanWhitefish
        BackdeckButton {
            id: btnOliveRockfish
            text: qsTr("Olive\nRockfish")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            onClicked: {
                populateHook(text);
            }
        } // btnOliveRockfish
        BackdeckButton {
            id: btnRosyRockfish
            text: qsTr("Rosy\nRockfish")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            onClicked: {
                populateHook(text);
            }
        } // btnRosyRockfish

        // Column 4
        BackdeckButton {
            id: btnSanddab
            text: qsTr("Sanddab")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            onClicked: {
                populateHook(text);
            }
        } // btnSanddab
        BackdeckButton {
            id: btnSpeckled
            text: qsTr("Speckled")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            onClicked: {
                populateHook(text);
            }
        } // btnSpeckled
        BackdeckButton {
            id: btnSquarespot
            text: qsTr("Squarespot")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            onClicked: {
                populateHook(text);
            }
        } // btnSquarespot
        BackdeckButton {
            id: btnStarry
            text: qsTr("Starry")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            onClicked: {
                populateHook(text);
            }
        } // btnStarry
        BackdeckButton {
            id: btnSwordspine
            text: qsTr("Swordspine")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            onClicked: {
                populateHook(text);
            }
        } // btnSwordspine
        BackdeckButton {
            id: btnWidow
            text: qsTr("Widow")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            onClicked: {
                populateHook(text);
            }
        } // btnWidow
        BackdeckButton {
            id: btnYellowtail
            text: qsTr("Yellowtail")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            onClicked: {
                populateHook(text);
            }
        } // btnYellowtail
    } // glShortSpeciesList
//    SwipeView {
    Item {
        id: svFullSpeciesList
//        currentIndex: 0
        property int currentIndex: 0
        property int count: 3
        anchors.left: clHooks.right
        anchors.leftMargin: 20
        anchors.top: clHooks.top

        property alias sl1: sl1
        property alias sl2: sl2
        property alias sl3: sl3

        HooksFullSpeciesList {
            id: sl1
            repeaterIndex: 0
            visible: true
        } // sl1
        HooksFullSpeciesList {
            id: sl2
            repeaterIndex: 1
            visible: false
        } // sl2
        HooksFullSpeciesList {
            id: sl3
            repeaterIndex: 2
            visible: false
        } // sl3



//        Repeater {
//            model: 3
//            Page {
//                width: svFullSpeciesList.width
//                height: svFullSpeciesList.height
//                GridLayout {
//                    rows: 6
//                    columns: 4
//                    rowSpacing: 10
//                    columnSpacing: 10
//                    Repeater {
////                        model: hooks.fullSpeciesListModel.getSubset(index);
//                        model: getModelSubset(index);
////                        Loader {
////                            sourceComponent: getSwipeViewComponent(modelData.text);
////                        }
//                        BackdeckButton {
//                            Layout.preferredWidth: buttonWidth
//                            Layout.preferredHeight: buttonHeight
//                            text: modelData.text.length > 13 ?
//                                    modelData.text.replace(" ", "\n") :
//                                    modelData.text;
//                            onClicked: {
//                                populateHook(text.replace('\n', ' '));
//                            }
//                        }
//                    }
//                }
//            }
//        }

//        Repeater {
//            model: 3
//            Loader {
//                sourceComponent: GridLayout {
//                    rows: 6
//                    columns: 4
//                    rowSpacing: 10
//                    columnSpacing: 10
//                    Repeater {
//                        model: hooks.fullSpeciesListModel.getSubset(index);
//                        BackdeckButton {
//                            Layout.preferredWidth: buttonWidth
//                            Layout.preferredHeight: buttonHeight
//                            text: modelData.text.length > 13 ?
//                                    modelData.text.replace(" ", "\n") :
//                                    modelData.text;
//                            onClicked: {
//                                populateHook(text.replace('\n', ' '));
//                            }
//                        }
//                    }
//
//                }
//            }
//        }
    }
    PageIndicator {
        id: piIndicator

        count: svFullSpeciesList.count
        currentIndex: svFullSpeciesList.currentIndex
        anchors.bottom: framFooter.top
        anchors.bottomMargin: -10
        anchors.horizontalCenter: glShortSpeciesList.horizontalCenter

        delegate: Rectangle {
            implicitWidth: 80
            implicitHeight: 80

            property variant alphaIndex: {0: "A-G", 1: "G-S", 2: "S-Y"}
            radius: width
            color: "white"
            border.color: "black"
            border.width: 5

            opacity: index === svFullSpeciesList.currentIndex ? 0.95 : pressed ? 0.5 : 0.3

            Behavior on opacity {
                OpacityAnimator {
                    duration: 100
                }
            }
            MouseArea {
                anchors.fill: parent
                onClicked: {
                    if(index !== svFullSpeciesList.currentIndex) {
                        svFullSpeciesList.currentIndex = index;
                        svFullSpeciesList.sl1.visible = false;
                        svFullSpeciesList.sl2.visible = false;
                        svFullSpeciesList.sl3.visible = false;
                        switch (index) {
                            case 0:
                                svFullSpeciesList.sl1.visible = true;
                                break;
                            case 1:
                                svFullSpeciesList.sl2.visible = true;
                                break;

                            case 2:
                                svFullSpeciesList.sl3.visible = true;
                                break;
                        }

//                        svFullSpeciesList.setCurrentIndex(index);
//                        console.info('new index: ' + index);
                    }
                }
            }
            Text {
                text: alphaIndex[index]
                color: "black"
                font.pixelSize: 24
                font.bold: true
                anchors.fill: parent
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
        }
    }

    Footer {
        id: framFooter
        height: 50
        state: "hooks"
    }
    OkayDialog { id: dlgOkay }

    states: [
        State {
            name: "full species list"
            PropertyChanges { target: glShortSpeciesList; visible: false; }
            PropertyChanges { target: svFullSpeciesList; visible: true; }
            PropertyChanges { target: framFooter.lblSpeciesList; text: "Short List"; }
            PropertyChanges { target: piIndicator; visible: true; }
        }, // full species list
        State {
            name: "short species list"
            PropertyChanges {target: glShortSpeciesList; visible: true; }
            PropertyChanges { target: svFullSpeciesList; visible: false; }
            PropertyChanges { target: framFooter.lblSpeciesList; text: "Full List"; }
            PropertyChanges { target: piIndicator; visible: false; }
        } // short species list
    ]
}

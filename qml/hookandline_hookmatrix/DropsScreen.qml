import QtQuick 2.5
import QtQuick.Controls 1.3
import QtQuick.Layouts 1.2
import QtQuick.Controls.Styles 1.2
import QtQuick.Controls.Private 1.0

Item {

    property variant siteResults: null
    property variant currentDrop: tbDrop1
    property variant dropTabMap:  {
        "1": tbDrop1, "2": tbDrop2, "3": tbDrop3, "4": tbDrop4, "5": tbDrop5
    }

    Connections {
        target: drops
        onExceptionEncountered: showException(message, action)
    } // drops.onExceptionEncountered
    function showException(message, action) {
        dlgOkay.message = message;
        dlgOkay.action = action;
        dlgOkay.open();
    }

    Connections {
        target: drops
        onSelectionResultsObtained: populateDropInfo(results);
    } // drops.onSelectionResultsObtained
    function populateDropInfo(results) {

        console.info("siteResults: " + JSON.stringify(results));

        siteResults = results;

        var tab;
        var anglerItem;
        var anglerResult;

        // Clear out the stateMachine variables:
        stateMachine.anglerAOpId = null;
        stateMachine.anglerBOpId = null;
        stateMachine.anglerCOpId = null;

        for (var drop in results) {
            for (var i = 0; i < tvDrops.count; i++) {
                var tab = tvDrops.getTab(i);
                if (tab.title == drop) {

                    // Drop the Drop-level information (id, sinkerWeight, etc.)
                    var dropKeyValue;
                    for (var dropKey in results[drop]) {
                        if (dropKey !== "Anglers") {
//                            console.info('dropKey: ' + dropKey);
                            switch (dropKey) {
                                case "id":
                                    stateMachine.dropOpId = results[drop][dropKey];
                                    break;
                                case "Sinker Weight":
                                    dropKeyValue = results[drop][dropKey] ? results[drop][dropKey] : ""
                                    tab.item.dtDrop.sinkerWeight = "Sinker\n" + dropKeyValue + " lb";
                                    break;
                                case "Recorder Name":
                                    tab.item.dtDrop.recorder = results[drop][dropKey] ? results[drop][dropKey] : "";
                                    break;
                            }
                        }
                    }

                    // Populate the Angler-level information (id, times, etc.)
                    for (var angler in results[drop]["Anglers"]) {

                        // Get the Angler Item QML element
                        switch (angler) {
                            case "Angler A":
                                anglerItem = tab.item.dtDrop.anglerA;
                                break;
                            case "Angler B":
                                anglerItem = tab.item.dtDrop.anglerB;
                                break;
                            case "Angler C":
                                anglerItem = tab.item.dtDrop.anglerC;
                                break
                        }

                        // Get the JSON angler elements, used to populate the various QML widgets
                        anglerResult = results[drop]["Anglers"][angler];
                        for (var value in anglerResult) {
                            switch (value) {
                                case "Angler Time Start":
                                    anglerItem.btnStart.text = "Start\n" + anglerResult[value];
                                    var hour, min, sec;
                                    var timeSplit = anglerResult[value].split(":");
                                    hour = timeSplit[0];
                                    min = timeSplit[1];
                                    sec = timeSplit[2];
                                    var d = new Date();
                                    d.setHours(hour);
                                    d.setMinutes(min);
                                    d.setSeconds(sec);
                                    anglerItem.startSeconds = d.getTime();

                                    break;
                                case "Angler Time Begin Fishing":
                                    anglerItem.btnBeginFishing.text = "Begin Fishing\n" + anglerResult[value];
                                    break;
                                case "Angler Time First Bite":
                                    anglerItem.btnFirstBite.text = "First Bite\n" + anglerResult[value];
                                    break;
                                case "Angler Time Retrieval":
                                    anglerItem.btnRetrieval.text = "Retrieval\n" + anglerResult[value];
                                    break;
                                case "Angler Time At Surface":
                                    anglerItem.btnAtSurface.text = "At Surface\n" + anglerResult[value];
                                    break;
                                case "Angler Attribute Angler Name":
                                    anglerItem.anglerName = anglerResult[value];
                                    break;
                                case "id":
                                    switch (anglerItem) {
                                        case tab.item.dtDrop.anglerA:
                                            stateMachine.anglerAOpId = anglerResult[value];
                                            drops.selectAnglerGpLabels(stateMachine.dropOpId, "A")  // updates gp label
                                            break;
                                        case tab.item.dtDrop.anglerB:
                                            stateMachine.anglerBOpId = anglerResult[value];
                                            drops.selectAnglerGpLabels(stateMachine.dropOpId, "B")  // updates gp label
                                            break;
                                        case tab.item.dtDrop.anglerC:
                                            stateMachine.anglerCOpId = anglerResult[value];
                                            drops.selectAnglerGpLabels(stateMachine.dropOpId, "C")  // updates gp label
                                            break;
                                    }
                                    break;
                            }
                        }

                        // Start the timer if btnStart is populated and btnAtSurface is not
                        if ((anglerItem.btnStart.text !== "Start\n") & (anglerItem.btnAtSurface.text === "At Surface\n")) {
                            anglerItem.isRunning = true;
                            anglerItem.startTimer();
                        }
                        if (anglerItem.btnAtSurface.text !== "At Surface\n") {
                            anglerItem.lblElapsedTime.text = anglerItem.btnAtSurface.text.replace("At Surface\n", "");
                        }

                        anglerItem.btnStart.enabled = false
                        anglerItem.btnBeginFishing.enabled = false;
                        anglerItem.btnFirstBite.enabled = false;
                        anglerItem.btnRetrieval.enabled = false;
                        anglerItem.btnAtSurface.enabled = false;

                        if (anglerItem.btnAtSurface.text !== "At Surface\n") {
                            anglerItem.btnAtSurface.enabled = true;
                            anglerItem.rtHooks.enabled = true;
                        } else if ((anglerItem.btnRetrieval.text !== "Retrieval\n") &
                            (anglerItem.btnAtSurface.text === "At Surface\n")) {
                            anglerItem.btnBeginFishing.enabled = false;
                            anglerItem.btnFirstBite.enabled = false;

                            anglerItem.btnRetrieval.enabled = true;
                            anglerItem.btnAtSurface.enabled = true;
                        } else if ((anglerItem.btnFirstBite.text !== "First Bite\n") &
                            (anglerItem.btnRetrieval.text === "Retrieval\n")) {
                            anglerItem.btnBeginFishing.enabled = false;
                            anglerItem.btnFirstBite.enabled = true;
                            anglerItem.btnRetrieval.enabled = true;
                        } else if ((anglerItem.btnBeginFishing.text !== "Begin Fishing\n") &
                            (anglerItem.btnFirstBite.text === "First Bite\n")) {
                            anglerItem.btnBeginFishing.enabled = true;
                            anglerItem.btnFirstBite.enabled = true;
                            anglerItem.btnRetrieval.enabled = true;
                        } else if ((anglerItem.btnStart.text !== "Start\n") &
                            (anglerItem.btnBeginFishing.text === "Begin Fishing\n")) {
                            anglerItem.btnStart.enabled = true;
                            anglerItem.btnBeginFishing.enabled = true;
                            anglerItem.btnFirstBite.enabled = true;
                            anglerItem.btnRetrieval.enabled = true;
                        } else if (anglerItem.btnStart.text === "Start\n") {
                            anglerItem.btnStart.enabled = true;
                        }
                        anglerItem.previousButtonsState = {
                            "Start": anglerItem.btnStart.enabled, "Begin Fishing": anglerItem.btnBeginFishing.enabled,
                            "First Bite": anglerItem.btnFirstBite.enabled, "Retrieval": anglerItem.btnRetrieval.enabled,
                            "At Surface": anglerItem.btnAtSurface.enabled
                        }
                    }
                    break;
                }
            }
        }
    }

    // Next five connections all pick up newly added drop JSON and add these back to the siteResults JSON
    Connections {
        target: drops
        onNewDropAdded: addNewDropData(dropJson);
    } // drops.onNewDropAdded
    Connections {
        target: tbDrop1.item.dtDrop
        onNewDropAdded: addNewDropData(dropJson);
    } // tbDrop1.onNewDropAdded
    Connections {
        target: tbDrop2.item.dtDrop
        onNewDropAdded: addNewDropData(dropJson);
    } // tbDrop2.onNewDropAdded
    Connections {
        target: tbDrop3.item.dtDrop
        onNewDropAdded: addNewDropData(dropJson);
    } // tbDrop3.onNewDropAdded
    Connections {
        target: tbDrop4.item.dtDrop
        onNewDropAdded: addNewDropData(dropJson);
    } // tbDrop4.onNewDropAdded
    Connections {
        target: tbDrop5.item.dtDrop
        onNewDropAdded: addNewDropData(dropJson);
    } // tbDrop5.onNewDropAdded
    function addNewDropData(dropJson) {
        console.info('siteResults before: ' + JSON.stringify(siteResults))
        console.info("in DropScreen: " + JSON.stringify(dropJson));
        var keys = Object.keys(dropJson);
        var dropKey = keys[0];
        if (!(dropKey in siteResults)) {
            siteResults[dropKey] = dropJson[dropKey];
        }
        console.info('siteResults after: ' + JSON.stringify(siteResults));
    }
    function changeDrop(drop) {
        stateMachine.drop = drop;
        var dropResults;
        if (siteResults !== null) {
            if ("Drop " + drop in siteResults) {
                dropResults = siteResults["Drop " + drop];
                stateMachine.dropOpId = dropResults["id"];
                stateMachine.anglerAOpId = dropResults["Anglers"]["Angler A"]["id"];
                stateMachine.anglerBOpId = dropResults["Anglers"]["Angler B"]["id"];
                stateMachine.anglerCOpId = dropResults["Anglers"]["Angler C"]["id"];
                currentDrop = dropTabMap[drop];
            } else {
                stateMachine.dropOpId = null;
                stateMachine.anglerAOpId = null;
                stateMachine.anglerBOpId = null;
                stateMachine.anglerCOpId = null
            }
        }
        console.info('input drop: ' + drop +
            ' >>> stateMachine items, drop: ' + stateMachine.drop +
            ', dropOpId: ' + stateMachine.dropOpId +
            ', anglerAOpId: ' + stateMachine.anglerAOpId +
            ', anglerBOpId: ' + stateMachine.anglerBOpId +
            ', anglerCOpId: ' + stateMachine.anglerCOpId)
    }
    function updateSinkerWeights(result) {
        var text_str = qsTr("Sinker\n" + result + " lb");
        tbDrop2.item.dtDrop.sinkerWeight = text_str;
        tbDrop3.item.dtDrop.sinkerWeight = text_str;
        tbDrop4.item.dtDrop.sinkerWeight = text_str;
        tbDrop5.item.dtDrop.sinkerWeight = text_str;
        var operationId;

        console.info('siteResults: ' + JSON.stringify(siteResults));

        for (var i=2; i<6; i++) {
            i = i.toString();
            operationId = null;
            if ("Drop " + i in siteResults) {
                operationId = siteResults["Drop " + i]["id"];
//            } else {
//                drops.insertOperations(i);
//                operationId = stateMachine.dropOpId;
            }
            console.info('Drop operationId: ' + operationId);
            stateMachine.drop = i;
            drops.upsertOperationAttribute(operationId, "Drop Attribute", "Sinker Weight", "numeric",
                                            parseInt(result), "Drop " + i);

        }
        console.info('currentDrop title: ' + currentDrop.title);

        // Reset the stateMachine drop/angler IDs back to the current Drop + three anglers
        stateMachine.drop = "1";
        stateMachine.dropOpId = siteResults[currentDrop.title]["id"];
        stateMachine.anglerAOpId = siteResults[currentDrop.title]["Anglers"]["Angler A"]["id"];
        stateMachine.anglerBOpId = siteResults[currentDrop.title]["Anglers"]["Angler B"]["id"];
        stateMachine.anglerCOpId = siteResults[currentDrop.title]["Anglers"]["Angler C"]["id"];

        console.info('stateMachine values:  drop=' + stateMachine.drop + ', ' +
                        'drop Op Id=' + stateMachine.dropOpId + ', ' +
                        'angler A Op ID=' + stateMachine.anglerAOpId + ', ' +
                        'angler B Op ID=' + stateMachine.anglerBOpId + ', ' +
                        'angler C Op ID=' + stateMachine.anglerCOpId)

    }
    function padZeros(value) { return (value < 10) ? "0" + value : value; }
    function formatTime(value) {
        var minutes = padZeros(Math.floor(value/60))
        var seconds = padZeros(Math.round(value%60))
        return minutes + ":" + seconds;
    }
    function getHeaderTitle() {
        var site = (stateMachine.site !== undefined) ? stateMachine.site : ""
        var area = (stateMachine.area !== undefined) ? stateMachine.area : ""
        var str = stateMachine.setId + " - " + site + " - " +
                    area + " - " + stateMachine.siteDateTime +
                    " - Drop " + stateMachine.drop;
        return str;
    }
    Header {
        id: framHeader
        title: getHeaderTitle();
        height: 50
    }
    TabView {
        id: tvDrops
        anchors.top: framHeader.bottom
        anchors.topMargin: 20
        anchors.bottom: framFooter.top
        anchors.bottomMargin: 20
        anchors.left: parent.left
        anchors.right: parent.right

        Tab {
            id: tbDrop1
            title: "Drop 1"
            active: true
            Item {
                property alias dtDrop: dtDrop
                DropTab {
                    id: dtDrop;
                    dropNumber: "1";
                    onSinkerWeightsUpdated: {
                        updateSinkerWeights(result);
                    }
                 }
            }
            onVisibleChanged: {
                if (this.visible) {
                    console.log('changeDrop to 1');
                    changeDrop("1");
                }//stateMachine.drop = "1"
            }
        } // tbDrop1
        Tab {
            id: tbDrop2
            title: "Drop 2"
            active: true
            onVisibleChanged: {
                console.info('inside 2 visibility changing');
                if (this.visible) {
                    changeDrop("2");
                } //stateMachine.drop = "2"
            }
            Item {
                property alias dtDrop: dtDrop
                DropTab { id: dtDrop; dropNumber: "2"; }
            }
        } // tbDrop2
        Tab {
            id: tbDrop3
            title: "Drop 3"
            active: true
            Item {
                property alias dtDrop: dtDrop
                DropTab { id: dtDrop; dropNumber: "3"; }
            }
            onVisibleChanged: {
                if (this.visible) changeDrop("3"); //stateMachine.drop = "3"
            }
        } // tbDrop3
        Tab {
            id: tbDrop4
            title: "Drop 4"
            active: true
            Item {
                property alias dtDrop: dtDrop
                DropTab { id: dtDrop; dropNumber: "4"; }
            }
            onVisibleChanged: {
                if (this.visible) changeDrop("4"); //stateMachine.drop = "4"
            }
        } // tbDrop4
        Tab {
            id: tbDrop5
            title: "Drop 5"
            active: true
            Item {
                property alias dtDrop: dtDrop
                DropTab { id: dtDrop; dropNumber: "5"; }
            }
            onVisibleChanged: {
                if (this.visible) changeDrop("5");  //stateMachine.drop = "5"
            }
        } // tbDrop5
        style: TabViewStyle {
            frameOverlap: 1
            tab: Rectangle {
                color: styleData.selected ? "white": "lightgray"
//                color: styleData.selected ? "steelblue" :"lightsteelblue"
//                border.color:  "steelblue"
                border.color: "black"
//                implicitWidth: Math.max(text.width + 4, 80)
                implicitWidth: 140
                implicitHeight: 70
                radius: 3
                Text {
                    id: text
                    font.pixelSize: 24
                    anchors.centerIn: parent
                    text: styleData.title
                    font.weight: styleData.selected ? Font.Bold : Font.Normal
//                    color: styleData.selected ? "white" : "black"
                }
            }
//            frame: Rectangle { color: "#EEE" }
        }
    }
    BackdeckButton {
        id: btnFinished
        text: qsTr("Finished &\nValidate")
        anchors.top: framHeader.bottom
//        anchors.topMargin: 10
        anchors.right: parent.right
        anchors.rightMargin: 10
        width: 140
        height: 80
        onClicked: {
            smHookMatrix.to_sites_state();
            sites.finishedAndValidate();
        }
    }
    Footer {
        id: framFooter
        height: 50
        state: "drops"
    }
    OkayDialog {
        id: dlgOkay
    }
}

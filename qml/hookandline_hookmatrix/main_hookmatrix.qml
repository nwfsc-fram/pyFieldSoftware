import QtQuick 2.7
import QtQuick.Controls 1.2
import QtQuick.Layouts 1.2
import QtQuick.Window 2.2
import QtQuick.Dialogs 1.2

//import "../common"

ApplicationWindow {
    id: main
    title: qsTr("HookMatrix " + stateMachine.swVersion)
    width: 1920 // 1024 // 1008 //1024     // 1040 with borders - 16 > 1008
    height: 1200 // 768 // 730 //768     // 806 with titlebar+borders - 38 > 730
    visible: true
    property alias screens: screens

    onClosing: {
        serialPortManager.stop_all_threads()
//        soundPlayer.stop_thread()
    }

    Connections {
        target: rpc
        onExceptionEncountered: showException(message, action)
    } // rpc.onExceptionEncountered
    function showException(message, action) {
        dlgMainOkay.message = message;
        dlgMainOkay.action = action;
        if (!dlgMainOkay.visible) {
            dlgMainOkay.open()
        }
    }

    HookMatrixStateMachine {
        id: smHookMatrix
    }

    StackView {
        id: screens
        anchors.fill: parent
        initialItem: SitesScreen {
            width: parent.width
            height: parent.height
        }
    }
    OkayDialog {
        id: dlgMainOkay
    }
}

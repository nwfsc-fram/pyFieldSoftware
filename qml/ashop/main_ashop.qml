import QtQuick 2.5
import QtQuick.Controls 1.2
import QtQuick.Layouts 1.2
import QtQuick.Window 2.2
import QtQuick.Dialogs 1.2

//import py.trawl.WindowFrameSize 1.0
import "../common"
import "."

ApplicationWindow {
    id: main
    title: qsTr("ASHOP")
    width: 1008 //1024     // 1040 with borders - 16 > 1008
    height: 730 //768     // 806 with titlebar+borders - 38 > 730
    visible: true
    property alias screens: screens
    property alias dlgMessage: dlgMessage

    property string windowLabel: ""

    BackdeckStateMachine {
        id: bdSM
    }

    Component.onCompleted: {
//        wfs.set_window(main)
//        var rect = wfs.get_frame_size()   // pyqtSlot technique = method
//        var rect = wfs.frame_size           // pyqtProperty technique = property
//        console.log(rect.width)
 //       msg.show("Width: " + rect.width + "\nHeight: " + rect.height)

    }

    onClosing: {
//        serialPortManager.stop_all_threads()
//        soundPlayer.stop_thread()
//        close.accepted = true;
    }


    function maximizeWindow() {
        // Tablet rotated
        main.x = 0
        main.y = 0
        main.width = Screen.width
        main.height = Screen.height
    }

//    Screen.onPrimaryOrientationChanged: {
//        maximizeWindow()
//    }

//    Connections {
//        target: settings
//        onPingStatusReceived: pingTestMsg.show(message, success)
//    }

    StackView {
        id: screens
        anchors.fill: parent
        initialItem: HomeScreen {
            width: parent.width
            height: parent.height
        }


        Component.onCompleted: {
            // Ping the wheelhouse, access_point, Moxa
//            var response = settings.ping_test();
//            var success = true;
//            if (response.indexOf("FAIL") != -1) {
//                success = false;
//            }
//            if (response != "")
//                pingTestMsg.show(response, success);
        }
    }


//    TrawlConfirmDialog {
//        id: pingTestMsg
//        property int speciesNumber: -1
//        action: ""
//        title: "Ping Test Result "
//        function show(caption, success) {
//            if(!success) {
//                btnOkay.text = "Okay"
//                title += " FAILED"
//            } else {
//                title += " PASSED"
//            }
//            btnCancel.visible = false;
//            message = caption;
//            open();
//        }
//    }
    MessageDialog {
        id: dlgMessage
        width: 600
        height: 800
        objectName: "dlgUnhandledException"
        title: qsTr("Unhandled Exception Occurred")
        icon: StandardIcon.Critical
        function show(caption) {
            messageDialog.text = caption;
            messageDialog.open();
        }
        onAccepted: {
            mainWindow.close();
        }
    }


//    MessageDialog {
//        id: msg
//        title: qsTr("May I have your attention, please?")
//        function show(caption) {
//            msg.text = caption;
//            msg.open();
//        }
//    }

}

/**
 * HelperFunctions.js Created by James.Stearns on 15-Jun-2017.
 * Purpose: hold "code-behind" JavaScript utilities that can be imported by, and shared by, QML scripts.
 * See "Defining JavaScript Resources in QML" at http://doc.qt.io/qt-5/qtqml-javascript-resources.html
 */
// Mark as library so that these stateless functions can be shared.
// See article above for stateful non-library functions.
.pragma library

function dateTodayString() {
    // Use the ISO convention of year-month-day hour:min without the extra T: "yyyy-mm-dd hh:mm"
    var today = new Date();
    var today_date = today.toISOString().slice(0,10);
    var hh = today.getHours() < 10 ? "0" + today.getHours() : today.getHours();
    var min = today.getMinutes() < 10 ? "0" + today.getMinutes() : today.getMinutes();
    return "".concat(today_date).concat(" ").concat(hh).concat(":").concat(min);
}

function openDialog(dlgUrl, openParm, parentWindow) {
    // Instantiate a dialog window and call its open() method with the supplied parameter.
    // dlgUrl: URL (filename, here in OPTECS)
    // openParm: parameter to pass into open() call
    // parentWindow: parent of this dialog. Dialog will be centered over parent. Can be null.
    var component = Qt.createComponent(dlgUrl);
    if (component == null) {
        console.error("Problem creating dialog window component. Is URL correct?");
    } else {
        var dialogWindow = component.createObject(parentWindow);
        if (dialogWindow == null) {
            console.error("Problem instantiating dialog window." + component.errorString());
        } else {
            console.log("Dialog window instantiated.");
            dialogWindow.open(openParm);
        }
    }
}

function openUnusualConditionDialog(message, parentWindow) {
    // Open the ObserverUnusualConditionDialog (supply the URL to its QML file to openDialog(), above).
    var urlDlgUnusualCondition = "qrc:/qml/observer/ObserverUnusualConditionDialog.qml";
    openDialog(urlDlgUnusualCondition, message, parentWindow)
}
